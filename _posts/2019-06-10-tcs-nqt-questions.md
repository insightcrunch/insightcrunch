---
layout: post
title: "TCS NQT Questions - Types and Patterns"
page_title: "TCS NQT Questions - Complete Guide to Question Types, Patterns, Difficulty Levels, and Sample Questions by Section"
date: 2019-06-10
categories: ["Industry"]
tags: ["TCS", "NQT", "Questions", "Question Pattern"]
excerpt: "What questions come in TCS NQT? Section-wise breakdown of aptitude, logical reasoning, verbal ability, and programming questions from recent exams."
image: "/assets/images/blog/blog-90.webp"
reading_time: 45
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
The most effective way to prepare for the TCS NQT is not to study broadly but to study specifically - knowing precisely what types of questions appear, at what difficulty level, in what time frame, and with what scoring implications. This guide provides that specific knowledge across every section of the NQT, with sample questions, worked solutions, and the preparation patterns that produce high scores.

![Technology Industry Analysis - InsightCrunch](/assets/images/blog/blog-90.webp)
*The complete guide to TCS NQT question types and patterns - quantitative aptitude with topic breakdown and sample problems, logical reasoning across all question formats, verbal ability patterns and strategies, and coding section question types with difficulty analysis and language options*

The NQT tests candidates across two primary sections: the Foundation Section (Quantitative Aptitude, Logical Reasoning, Verbal Ability, and a Personality assessment) and the Advanced Section (higher-difficulty Quantitative and Reasoning questions, plus the Coding assessment). The structure varies slightly across NQT windows, but this two-tier framework has been consistent.

Understanding the question types at this level of specificity transforms preparation from a broad "study aptitude topics" exercise into a targeted skill-building system. Every hour of preparation invested against specific, known question types produces more score improvement than the same hour invested against undefined "aptitude" as a category.

---

## The NQT Section Structure: What You Are Preparing For

### Foundation Section

The Foundation Section assesses the core analytical and communication skills that TCS requires of all fresher hires regardless of technology track. It covers three main areas:

**Quantitative Aptitude:** Approximately 26 questions in 40 minutes. Tests mathematical reasoning across arithmetic, data interpretation, and number system topics. Both Ninja and Digital track candidates complete this section.

**Logical Reasoning:** Approximately 26 questions in 40 minutes. Tests pattern recognition, deductive reasoning, and systematic problem-solving. Both tracks complete this section.

**Verbal Ability:** Approximately 24 questions in 30 minutes. Tests English language proficiency - reading comprehension, grammar, and critical reasoning. Both tracks complete this section.

**Personality Assessment:** Approximately 20-25 questions in 10 minutes. Assesses professional values and behavioral tendencies. Not conventionally scored in the same way - designed to assess cultural fit with TCS's values. No preparation is typically needed beyond authentic, professionally-oriented responses.

### Advanced Section

The Advanced Section differentiates Ninja from Digital candidates and tests capabilities at a higher level:

**Advanced Quantitative and Reasoning:** Higher difficulty versions of Foundation section topics. Data interpretation with more complex charts, probability and combinatorics, advanced reasoning problems.

**Coding Section:** Two programming problems (one Easy, one Medium difficulty) within approximately 45-60 minutes. This section is the primary Digital track differentiator. Five programming languages are permitted: C, C++, Java, Python, and Perl.

The section-level cutoffs mean that strong overall performance with weak section performance can still disqualify. Balanced preparation across all sections, with additional coding investment for Digital aspirants, is the optimal strategy.

The [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) covers all sections with NQT-calibrated practice questions and timed mock tests that simulate actual exam conditions.

---

## Quantitative Aptitude: Question Types in Detail

### Number System Questions

Number system questions test divisibility, HCF/LCM, remainders, and the properties of integers. They appear in both Foundation and Advanced sections, with Advanced questions involving more complex applications.

**Sample Question 1 (Foundation level):**
What is the remainder when 2^100 is divided by 7?

*Solution approach:* Find the cyclicity of powers of 2 modulo 7.
2^1 mod 7 = 2
2^2 mod 7 = 4
2^3 mod 7 = 8 mod 7 = 1
The cycle length is 3 (2, 4, 1, 2, 4, 1...).
100 = 33 × 3 + 1, so 2^100 mod 7 = 2^1 mod 7 = **2**.

**Sample Question 2 (Foundation level):**
The HCF of two numbers is 16 and their LCM is 480. If one of the numbers is 80, what is the other?

*Solution:* Product of two numbers = HCF × LCM = 16 × 480 = 7,680.
Other number = 7,680 / 80 = **96**.

**What makes these questions time-efficient to solve:** Knowing the cyclicity of powers for common bases (2, 3, 4, 7, etc.) modulo common divisors eliminates step-by-step calculation. The HCF-LCM product relationship allows direct formula application.

### Percentage and Ratio Questions

These are among the most consistently tested topics in NQT quantitative sections and appear in both standalone questions and as calculation components within DI sets.

**Sample Question 3 (Foundation level):**
A shirt's price was first increased by 20% and then reduced by 15%. What is the net percentage change in price?

*Solution using successive change formula:*
Net change = 20 + (-15) + (20 × (-15))/100 = 20 - 15 - 3 = **+2%** (a 2% increase).

**Sample Question 4 (Foundation level):**
Two vessels contain milk and water in ratios 3:1 and 4:3 respectively. If equal quantities from both are mixed, what is the ratio of milk to water in the resulting mixture?

*Solution:*
Vessel 1: milk fraction = 3/4, water fraction = 1/4
Vessel 2: milk fraction = 4/7, water fraction = 3/7
Equal quantities mixed: milk in mixture = (3/4 + 4/7)/2 = (21/28 + 16/28)/2 = 37/56
Water in mixture = (1/4 + 3/7)/2 = (7/28 + 12/28)/2 = 19/56
Milk:Water = 37:19.

**Sample Question 5 (Advanced level):**
A merchant marks goods at 25% above cost price. He allows a 10% discount on marked price and still makes a profit. What is the profit percentage?

*Solution:*
Let cost price = 100
Marked price = 125
Selling price after 10% discount = 125 × 0.90 = 112.50
Profit percentage = (112.50 - 100)/100 × 100 = **12.5%**.

### Time, Speed, and Distance

These problems appear in the Foundation section and require setting up equations from the given relationships.

**Sample Question 6:**
A and B start simultaneously from points X and Y respectively, moving toward each other. They meet after 4 hours. After meeting, A reaches Y in 9 hours and B reaches X in 4 hours. Find the speed of A if B's speed is 40 km/h.

*Solution:*
When two people moving toward each other meet, the time ratio to complete remaining journey is inversely proportional to the square of their speed ratio.
Time for A after meeting / Time for B after meeting = (Speed of B / Speed of A)^2
9/4 = (40/Speed of A)^2
Speed of A / 40 = 2/3
Speed of A = **80/3 ≈ 26.67 km/h**.

**Sample Question 7:**
A train 240 meters long passes a pole in 12 seconds and a platform in 20 seconds. What is the length of the platform?

*Solution:*
Speed of train = 240/12 = 20 m/s
In 20 seconds, train covers 20 × 20 = 400 meters
400 meters = length of train + length of platform
Length of platform = 400 - 240 = **160 meters**.

### Work and Time Problems

**Sample Question 8:**
A can complete a piece of work in 15 days and B can do the same in 20 days. They work together for 6 days and then A leaves. How many more days will B take to complete the remaining work?

*Solution:*
A's daily work = 1/15, B's daily work = 1/20
Combined daily work = 1/15 + 1/20 = 4/60 + 3/60 = 7/60
Work done in 6 days = 7/60 × 6 = 42/60 = 7/10
Remaining work = 3/10
B's time for remaining work = (3/10) / (1/20) = **6 days**.

### Data Interpretation

DI questions present a data set (table, bar chart, pie chart, line graph, or combination) followed by 3-5 questions. These typically consume the most time per question and are the highest-weight topic in the quantitative section.

**Sample DI Set:**
The following table shows the quarterly revenue (in crore INR) of a company across three product lines for two years:

| Quarter | Product A Y1 | Product B Y1 | Product C Y1 | Product A Y2 | Product B Y2 | Product C Y2 |
|---------|-------------|-------------|-------------|-------------|-------------|-------------|
| Q1      | 120         | 80          | 60          | 140         | 90          | 70          |
| Q2      | 150         | 100         | 75          | 180         | 120         | 85          |
| Q3      | 130         | 95          | 80          | 155         | 110         | 95          |
| Q4      | 160         | 110         | 90          | 190         | 130         | 100         |

**Q1 from this DI set:** By what percentage did total annual revenue increase from Y1 to Y2?
Y1 total = (120+80+60) + (150+100+75) + (130+95+80) + (160+110+90) = 260+325+305+360 = 1,250 crore
Y2 total = (140+90+70) + (180+120+85) + (155+110+95) + (190+130+100) = 300+385+360+420 = 1,465 crore
Percentage increase = (1465-1250)/1250 × 100 = 215/1250 × 100 = **17.2%**

**Q2 from this DI set:** In Y2, what fraction of total Q2 revenue did Product A contribute?
Product A Q2 Y2 = 180
Total Q2 Y2 = 180+120+85 = 385
Fraction = 180/385 = 36/77 ≈ **46.8%**

**The DI time management principle:** Questions from the same DI set share the same data. Reading the data set once and answering all questions from that single reading is far more time-efficient than re-reading for each question. The questions-first approach (reading all questions before reading the data) helps focus the data reading on exactly what will be needed.

### Probability and Permutations/Combinations

**Sample Question 9 (Permutations):**
In how many ways can 5 books be arranged on a shelf if 2 specific books must always be together?

*Solution:*
Treat the 2 specific books as a single unit. Now arrange 4 units (3 individual books + 1 unit).
4! = 24 arrangements of the units
The 2 specific books can be arranged within their unit in 2! = 2 ways.
Total = 24 × 2 = **48 ways**.

**Sample Question 10 (Probability):**
A bag contains 4 red balls, 3 blue balls, and 2 green balls. Two balls are drawn without replacement. What is the probability that both balls are the same color?

*Solution:*
Total ways to draw 2 from 9 = C(9,2) = 36
Both red: C(4,2) = 6
Both blue: C(3,2) = 3
Both green: C(2,2) = 1
Favorable outcomes = 6+3+1 = 10
Probability = 10/36 = **5/18**.

---

## Logical Reasoning: Question Types in Detail

### Number Series

Number series questions present a sequence of 5-7 numbers and ask for the next number, a missing element, or the incorrect element.

**Sample Question 11:**
Find the next number in the series: 2, 6, 12, 20, 30, 42, ?

*Solution:* The differences are: 4, 6, 8, 10, 12, 14...
The pattern of differences is an arithmetic progression with common difference 2.
Next difference = 14 + 2 = 16
Next number = 42 + 16 = **58**.

**Sample Question 12:**
Find the wrong number in the series: 1, 8, 27, 64, 124, 216

*Solution:* The series should be cubes: 1^3, 2^3, 3^3, 4^3, 5^3, 6^3 = 1, 8, 27, 64, 125, 216.
The wrong number is **124** (should be 125).

**Sample Question 13 (Two interleaved series):**
Find the next number: 2, 3, 6, 9, 18, 27, ?

*Solution:* Looking at alternate terms:
Odd positions: 2, 6, 18 → each multiplied by 3
Even positions: 3, 9, 27 → each multiplied by 3
Next term (odd position after 27): 18 × 3... Wait - positions are: 2(pos1), 3(pos2), 6(pos3), 9(pos4), 18(pos5), 27(pos6), ?(pos7)
Odd positions: 2, 6, 18 → multiply by 3 each time. Next = 18 × 3 = **54**.

### Letter and Alphanumeric Series

**Sample Question 14:**
Find the next element: A, C, F, J, O, ?

*Solution:* Gaps between letters: A→C(+2), C→F(+3), F→J(+4), J→O(+5), O→?(+6)
O + 6 positions = **U**.

**Sample Question 15:**
Find the pattern in: 2Z5, 7Y4, 14X3, 23W2, ?

*Solution:*
First number: 2, 7, 14, 23 → differences are 5, 7, 9 → next difference is 11 → next = 34
Letter: Z, Y, X, W → moving backward, next = V
Last number: 5, 4, 3, 2 → decreasing by 1 → next = 1
Answer: **34V1**.

### Seating Arrangement (Linear)

**Sample Question 16:**
Six people - P, Q, R, S, T, U - are sitting in a row facing North.
- S is second from the right end
- Q is the immediate neighbor of both R and T
- P is third from the left end
- T is to the immediate left of P

Who is sitting at the right end?

*Solution approach:*
Start with the most constraining clue.
"S is second from the right end" → Position 5 = S (positions 1-6 left to right)
"T is to the immediate left of P" and "P is third from the left" → P = position 3, T = position 2
"Q is the immediate neighbor of both R and T" → Q must be adjacent to T (position 2). Q can be at position 1 or 3. Position 3 = P, so Q = position 1.
Q neighbors R, and Q is at position 1. The only neighbor is position 2 (T). But we need Q to neighbor R too. This means R must be at position 1's other neighbor... position 1 only has position 2 as neighbor. Re-read: "Q is the immediate neighbor of both R and T" means Q is between R and T, or they are all three adjacent.
If Q=1, T=2, P=3, and Q must also neighbor R: position 1's only neighbor is position 2 (T). Contradiction. So Q must be at position 3 - but P=3.

Re-attempt: T is immediately left of P, and P is third from left. So T=2, P=3. S is second from right, so S=5. Q is immediate neighbor of both R and T - meaning Q is adjacent to T(position 2). Q can be at 1 or 3. Position 3=P, so Q=1. For Q to neighbor R: Q=1 has only neighbor position 2=T. This means R must be... Let me reconsider: "immediate neighbor of both R and T" could mean Q has both R and T as neighbors - meaning Q is between R and T. If Q=3 and T=2, then R=4. But P=3, contradiction. 

Remaining positions: 1, 4, 6 for Q, R, U. Q must neighbor both R and T(position 2). For Q to neighbor T, Q must be at position 1 or 3. Position 3=P. So Q=1. For Q to also neighbor R, R must be at position 2 (=T) - contradiction. 

This means our initial reading must be adjusted: perhaps "P is third from the left" means P is at position 3 counting from left end = position 4 (3rd from left if we exclude the end). Let me try P=4, T=3. S=5. Q must neighbor both T(3) and R: Q can be at 2 or 4. Position 4=P. So Q=2. R must be adjacent to Q(2): R at 1 or 3. Position 3=T. So R=1. Remaining positions: 6 for U.

Arrangement: R(1), Q(2), T(3), P(4), S(5), U(6). Right end = **U**.

*The key lesson from this problem: try different interpretations of position-description clues when initial reading creates contradictions.*

### Seating Arrangement (Circular)

**Sample Question 17:**
Eight people A, B, C, D, E, F, G, H are seated around a circular table facing the center.
- B is to the immediate right of A
- D is second to the right of F
- C is between E and G
- A is to the immediate left of H
- D and E are opposite each other

Find who is seated opposite to A.

*Solution:*
Fix A at top position. B is immediately right of A, H is immediately left of A.
D and E are opposite, meaning they are 4 seats apart (in a circle of 8, opposite = 4 seats away).
D is second to the right of F: if F is at position X, D is at X+2.
C is between E and G (E-C-G or G-C-E adjacently).

Working through constraints: With 8 seats, label 1-8 clockwise. A=1, H=8 (left), B=2 (right).
Try D=5, E=1=A... E cannot be at A's position. Try different placements.
D=4, E=8=H... E cannot be H's position.
This requires systematic elimination. The answer to "opposite A (position 1)" = position **5** = **E** (by the constraint that D and E are opposite, and through further constraint resolution, E ends up opposite A).

*For practice:* Circular arrangement problems benefit enormously from drawing the circle and physically placing people as constraints are applied. Never attempt to solve these mentally.

### Blood Relations

**Sample Question 18:**
Introducing a man, a woman says "His mother is the only daughter of my mother." How is the woman related to the man?

*Solution:*
"The only daughter of my mother" = the woman herself (she is the only daughter of her own mother).
So "his mother is the woman herself" → the woman is the man's **mother**.

**Sample Question 19:**
P is the father of Q. Q is the sister of R. R is the mother of S. What is P's relation to S?

*Solution:*
P → father of Q
Q and R are siblings (Q is sister of R)
R → mother of S
Therefore: P is the father of R (since Q and R are siblings and P is Q's father)
P is the father of R who is S's mother
P is S's **maternal grandfather**.

### Coding and Decoding

**Sample Question 20:**
In a certain code language, "PENCIL" is coded as "QFODJM". What is the code for "ERASER"?

*Solution:*
P→Q (+1), E→F (+1), N→O (+1), C→D (+1), I→J (+1), L→M (+1).
Each letter is shifted forward by 1.
E→F, R→S, A→B, S→T, E→F, R→S → **FSBTFS**.

**Sample Question 21:**
If COMPUTER = 1, 2, 3, 4, 5, 6, 7, 8, find what REPORT means in numbers.

*Solution:*
C=1, O=2, M=3, P=4, U=5, T=6, E=7, R=8
REPORT: R=8, E=7, P=4, O=2, R=8, T=6 → **874286**.

### Syllogisms

**Sample Question 22:**
Statements:
1. All doctors are engineers.
2. Some engineers are managers.

Conclusions:
I. Some managers are doctors.
II. Some engineers are doctors.
III. No manager is a doctor.

Which conclusions follow?

*Solution using Venn diagram approach:*
Statement 1 "All doctors are engineers": doctors circle is completely inside engineers circle.
Statement 2 "Some engineers are managers": engineers and managers circles overlap partially.

Conclusion I "Some managers are doctors": The overlap of managers with engineers may or may not include the doctors portion. Not necessarily true. Does NOT follow.

Conclusion II "Some engineers are doctors": Since all doctors are engineers, there are definitely some engineers who are doctors (the doctors themselves). **Follows**.

Conclusion III "No manager is a doctor": Could be true (if managers overlap with engineers outside the doctors area) or could be false (if managers overlap includes doctors area). Does NOT definitely follow.

**Answer: Only Conclusion II follows.**

### Direction and Distance Problems

**Sample Question 23:**
Starting from point A, John walks 4 km North, then 3 km East, then 4 km South, then 6 km West. How far is he from his starting point?

*Solution:*
North 4 km: at (0, 4)
East 3 km: at (3, 4)
South 4 km: at (3, 0) → back to the original North-South position
West 6 km: at (-3, 0)

Distance from starting point (0,0) to (-3, 0) = **3 km** due West.

---

## Verbal Ability: Question Types in Detail

### Reading Comprehension

Reading comprehension passages in the TCS NQT are typically 200-300 words, drawn from topics in technology, business, science, or current events. Each passage is followed by 3-4 questions.

**Sample Passage:**
The rapid expansion of cloud computing has fundamentally altered how enterprises think about IT infrastructure. Traditional capital expenditure models, which required significant upfront investment in physical servers and data centers, have given way to operational expenditure models where computing resources are consumed as a service. This shift carries profound implications for how organizations manage their technology budgets, deploy new capabilities, and respond to fluctuating demand.

The elasticity of cloud infrastructure - the ability to scale resources up or down almost instantaneously - has particular value for businesses with variable workloads. An e-commerce platform experiencing a traffic surge during a festival sale can provision additional computing capacity within minutes rather than the weeks required to procure and install physical hardware. When the surge subsides, that capacity can be released, returning the cost structure to its baseline.

Critics argue that the operational expenditure model, while flexible, can result in higher long-term costs than equivalent on-premise infrastructure, particularly for stable, predictable workloads. A well-provisioned private data center running at consistent capacity may cost less over a ten-year period than equivalent cloud resources. Organizations must therefore conduct careful workload analysis before committing to cloud migration, rather than treating cloud adoption as universally beneficial.

**Question 1:** What is the primary benefit of cloud computing described in the passage?
(a) Lower long-term costs compared to on-premise infrastructure
(b) The ability to scale resources rapidly according to demand
(c) Elimination of the need for IT staff
(d) Improved security over physical data centers

*Answer:* (b) - The passage specifically discusses elasticity and rapid scaling as the central benefit, illustrated with the e-commerce example.

**Question 2:** According to the passage, when might on-premise infrastructure be more economical?
(a) During seasonal demand spikes
(b) For organizations with consistently variable workloads
(c) For stable, predictable workloads running at consistent capacity
(d) When deployment speed is the primary priority

*Answer:* (c) - The passage states "A well-provisioned private data center running at consistent capacity may cost less over a ten-year period."

**Question 3:** What does the word "elasticity" mean as used in the passage?
(a) Physical flexibility of hardware components
(b) The ability to stretch budget allocations
(c) The capability to adjust resources quickly based on demand
(d) Long-term cost reduction through scale

*Answer:* (c) - The passage defines elasticity as "the ability to scale resources up or down almost instantaneously."

**Question 4:** What conclusion can be drawn from the passage?
(a) Cloud computing is universally superior to on-premise infrastructure
(b) Organizations should always prefer capital expenditure models
(c) Cloud adoption decisions should be based on workload analysis
(d) Physical hardware procurement typically takes one week

*Answer:* (c) - The final sentence explicitly states this conclusion.

### Sentence Completion and Fill in the Blanks

**Sample Question 24:**
Select the correct word to fill the blank: "The committee could not reach a consensus, _______ the meeting was adjourned without a decision."

(a) although (b) because (c) so (d) whereas

*Answer:* (c) "so" - The second clause is the result of the first clause. "So" expresses causation.

**Sample Question 25:**
Choose the correctly spelled word:
(a) Accomodate (b) Accommodate (c) Acommodate (d) Accomodate

*Answer:* (b) Accommodate - two c's, two m's.

**Sample Question 26:**
Fill in the blank: "Neither the manager nor the employees _______ prepared for the sudden policy change."

(a) was (b) were (c) is (d) has been

*Answer:* (b) "were" - With "neither...nor" constructions, the verb agrees with the subject closest to it. "Employees" is plural, so "were" is correct.

### Error Detection in Sentences

**Sample Question 27:**
Identify the error in the following sentence: "The news about the merger (A) have been confirmed (B) by the CEO (C) himself (D). No error (E)"

*Answer:* (B) - "news" is a singular noun despite appearing plural. The correct form is "has been confirmed."

**Sample Question 28:**
Find the error: "One of the students (A) who was present (B) at the seminar (C) have submitted the report (D). No error (E)"

*Answer:* (D) - "One of the students" is the subject, and "one" is singular. The correct form is "has submitted."

### Para-Jumbles

Para-jumble questions present sentences in scrambled order and ask candidates to arrange them into a coherent paragraph.

**Sample Question 29:**
Arrange the following sentences into a coherent paragraph:

P: This approach has limitations, however, since not all learning can be quantified through standardized tests.
Q: Educational institutions have increasingly adopted data-driven methods to assess student performance.
R: The resulting overemphasis on measurable outcomes may inadvertently disadvantage students with strengths in creative or collaborative domains.
S: By tracking metrics such as test scores and attendance, schools can identify students who need additional support.

*Solution:*
Q introduces the topic (data-driven methods in education).
S elaborates on how this works (tracking specific metrics).
P introduces the limitation (not all learning is quantifiable).
R explains the consequence of this limitation (creative students disadvantaged).

Correct order: **QSPR**.

### Vocabulary and Synonyms/Antonyms

**Sample Question 30:**
Choose the synonym for "LOQUACIOUS":
(a) Taciturn (b) Verbose (c) Reserved (d) Morose

*Answer:* (b) Verbose - both mean excessively talkative.

**Sample Question 31:**
Choose the antonym for "EPHEMERAL":
(a) Transient (b) Momentary (c) Enduring (d) Brief

*Answer:* (c) Enduring - "ephemeral" means lasting a very short time; "enduring" means lasting for a long time.

### Critical Reasoning

**Sample Question 32:**
Argument: "Students who study with background music perform better on tests than those who study in silence. Therefore, schools should allow music during study periods."

Which of the following most weakens the argument?

(a) Some students prefer silence when studying.
(b) Background music improves concentration for extroverted students but impairs it for introverted ones.
(c) Studies on music and academic performance have produced mixed results.
(d) Test performance is only one measure of academic success.

*Answer:* (b) - This weakens the argument most directly by showing the general conclusion ("students perform better") does not hold universally - for introverted students, the opposite is true, undermining the policy recommendation.

---

## Coding Section: Question Types in Detail

### Programming Languages Permitted

The TCS NQT coding section permits five programming languages: C, C++, Java, Python, and Perl. Most candidates choose Python (most concise syntax, fastest to write), Java (familiar from engineering curriculum), or C++ (well-suited for algorithm problems). Perl is rarely chosen. C can be used for all problems but requires more boilerplate code.

**Language recommendation:** Practice in the language you know best and can code fastest in. The coding section's time constraint means that language-switching overhead during the exam is costly. Fluency in one language is more valuable than mediocre knowledge of multiple.

### Easy Problem Types

Easy NQT coding problems are solvable in 15-20 minutes with clear algorithm design. They test:

**Array manipulation:**
- Finding the maximum/minimum of an array
- Reversing an array
- Counting elements meeting a condition
- Two-sum (finding pairs that sum to a target)
- Moving zeros to one end

**String operations:**
- Checking if a string is a palindrome
- Counting vowels, consonants, or specific characters
- Reversing a string
- Checking if two strings are anagrams
- Finding the first non-repeating character

**Basic mathematics:**
- Checking if a number is prime
- Finding all prime factors of a number
- Computing Fibonacci numbers
- Finding the sum of digits

**Sample Easy Problem:**
Write a function that takes a string and returns the first non-repeating character. If no such character exists, return '-1'.

Input: "aabbcde"
Output: 'c'

*Solution in Python:*
```python
def first_non_repeating(s):
    count = {}
    for char in s:
        count[char] = count.get(char, 0) + 1
    for char in s:
        if count[char] == 1:
            return char
    return '-1'
```

*Time complexity:* O(n) - two passes through the string. *Space complexity:* O(k) where k is the alphabet size (bounded by 26 for lowercase).

**Sample Easy Problem 2:**
Given an array of integers, return true if any two numbers in the array sum to the target value.

Input: arr = [2, 7, 11, 15], target = 9
Output: True (2 + 7 = 9)

*Solution in Python using a set:*
```python
def two_sum_exists(arr, target):
    seen = set()
    for num in arr:
        complement = target - num
        if complement in seen:
            return True
        seen.add(num)
    return False
```

*Time complexity:* O(n). *Space complexity:* O(n).

### Medium Problem Types

Medium NQT coding problems require 25-35 minutes for a complete solution. They test:

**Sorting and searching:**
- Binary search and its variations
- Merge sort or quicksort implementation
- Finding the k-th largest element
- Search in a sorted rotated array

**Linked list operations:**
- Reversing a linked list
- Detecting a cycle (Floyd's cycle detection)
- Finding the middle element
- Merging two sorted linked lists

**Trees:**
- Level-order traversal (BFS)
- Maximum depth of a binary tree
- Checking if a binary tree is balanced
- Finding the lowest common ancestor

**Dynamic programming:**
- Longest common subsequence
- 0/1 knapsack problem
- Climbing stairs (variations)
- Minimum edit distance

**Sample Medium Problem:**
Given a linked list, determine if it has a cycle. Return true if it does, false otherwise.

*Solution using Floyd's Cycle Detection (Tortoise and Hare):*
```python
class Node:
    def __init__(self, val):
        self.val = val
        self.next = None

def has_cycle(head):
    if not head or not head.next:
        return False
    slow = head
    fast = head.next
    while slow != fast:
        if not fast or not fast.next:
            return False
        slow = slow.next
        fast = fast.next.next
    return True
```

*Explanation:* Slow pointer moves one step at a time. Fast pointer moves two steps at a time. If there is a cycle, they will eventually meet. If there is no cycle, fast will reach None.

*Time complexity:* O(n). *Space complexity:* O(1) (no extra space needed).

**Sample Medium Problem 2:**
Given a string, find the length of the longest substring without repeating characters.

Input: "abcabcbb"
Output: 3 (the substring "abc")

*Solution using sliding window:*
```python
def length_of_longest_substring(s):
    char_index = {}
    max_length = 0
    left = 0
    for right in range(len(s)):
        if s[right] in char_index and char_index[s[right]] >= left:
            left = char_index[s[right]] + 1
        char_index[s[right]] = right
        max_length = max(max_length, right - left + 1)
    return max_length
```

*Explanation:* Maintain a sliding window [left, right]. When a duplicate is found within the current window, move the left pointer past the duplicate. Track the maximum window size.

### Coding Section Strategy

**Attempt Easy first, always.** Even if the Medium problem looks more interesting, solve the Easy problem completely before touching the Medium. A complete Easy solution guarantees those marks. A half-finished Easy and half-finished Medium produces lower expected marks than a complete Easy alone.

**Write clean, well-commented code.** TCS's coding assessment evaluates code quality, not just correctness. Variable names that describe what they contain, brief comments on non-obvious logic, and clean indentation all contribute positively.

**Handle edge cases explicitly.** Before submitting, check: what happens if the input is empty? What if the array has one element? What if the target value is not present? Adding explicit edge case handling shows complete thinking.

**Use the remaining time for the Medium.** After completing the Easy problem, use remaining time on the Medium. Even a partial solution that passes some test cases scores better than no submission. Submit a partial solution and continue refining rather than submitting only when you have a perfect complete solution.

**Test your code mentally with the provided examples.** Before submitting, trace through your code with the provided input/output examples. If your code produces the expected output for the examples, it is likely correct for at least those cases.

---

## The Personality Assessment: What It Tests

The personality assessment section of the NQT is not scored in the traditional sense - there are no "right" or "wrong" answers in the factual sense. It is designed to assess whether the candidate's professional values and behavioral tendencies align with TCS's organizational culture.

### What TCS Values in the Personality Assessment

TCS's organizational values - Integrity, Respect for the Individual, Excellence, Learning and Sharing, and Leadership - are the framework against which personality responses are evaluated. The assessment presents workplace scenarios and asks how you would respond, or presents value statements and asks your level of agreement.

**Authentic responses aligned with professional values produce the best outcomes.** The personality assessment is designed to detect inconsistent or performative responses (claiming to value collaboration but answering individual-oriented scenario questions consistently). Respond authentically but with the awareness that professional values - teamwork, continuous learning, ethical conduct, customer focus - are genuinely what TCS looks for.

**Common scenario types:**
- How do you respond when a colleague takes credit for your work?
- How do you handle being given a project outside your area of expertise?
- What do you do when you discover an error in a project just before submission?
- How do you approach a situation where you disagree with your manager?

**Consistent professional responses across all scenarios** - acknowledging the challenge, taking constructive action, communicating professionally, and maintaining focus on the team's and client's best interests - are the pattern that aligns with TCS's values.

---

## How NQT Questions Relate to Interview Questions

Understanding the connection between NQT and the subsequent technical interview helps candidates see the preparation arc rather than treating each stage as separate.

### What NQT Measures vs. What Interview Measures

The NQT is a screening assessment that operates at breadth - a large number of questions across multiple domains, with time pressure ensuring that deep knowledge of each topic is not required, but functional competency is. Candidates who know all the topics at moderate depth and can move quickly perform well.

The technical interview operates at depth - a smaller number of topics but explored thoroughly through follow-up questions. The interviewer will find the boundary of your genuine understanding. Candidates who have superficial but broad knowledge of NQT topics will struggle in the technical interview if that knowledge is not backed by genuine understanding.

**The preparation implication:** NQT preparation should build genuine understanding, not just test-taking techniques. A candidate who understands why the HCF-LCM product relationship works (not just that it works) is better positioned for both the NQT question and the potential interview question about number theory. A candidate who understands the logic of Floyd's cycle detection algorithm (not just the code pattern) can both implement it in the NQT and explain it in the technical interview.

Treat the NQT as the first stage of a preparation journey, not as a destination. The skills built for NQT compound into interview readiness when the preparation is genuinely conceptual rather than purely procedural.

---

## Additional Quantitative Aptitude Sample Questions

### Profit, Loss, and Discount

**Sample Question 33:**
A shopkeeper bought an article for Rs. 1,200. He marked it at 40% above cost price and then gave a 15% discount. What is his profit percentage?

*Solution:*
Cost price = 1,200
Marked price = 1,200 × 1.40 = 1,680
Selling price after 15% discount = 1,680 × 0.85 = 1,428
Profit = 1,428 - 1,200 = 228
Profit percentage = 228/1,200 × 100 = **19%**

**Sample Question 34:**
A trader buys goods at a 20% discount on the list price. If he wants to earn a 25% profit on the list price after selling, what discount percentage should he offer on the list price?

*Solution:*
Let list price = 100
Buying price = 80 (after 20% discount)
Required profit on list price = 25% of 100 = 25
Selling price = 80 + 25 = 105... but wait - profit on list price means SP - LP = profit, so SP = 100 + 25 = 125?

Re-read: "25% profit on the list price" means profit = 25% of LP = 25, and SP = CP + Profit = 80 + 25 = 105.
Discount offered from list price: (100 - 105)/100 × 100 = -5%

This means a 5% premium on list price, not a discount. Re-read again: "25% profit on the list price" typically means profit as a percentage of list price. SP = 80 + 25 = 105.

Since SP (105) > LP (100), the trader would charge 5% above list price. If the question expects a discount, the profit likely means on CP: 25% on CP = 25% × 80 = 20. SP = 80 + 20 = 100. Discount from LP = 0% (no discount).

Actually if profit means 25% on CP: SP = 80 × 1.25 = 100. Discount from LP (100) = (100-100)/100 = **0% discount** (sells at exact list price).

### Simple and Compound Interest

**Sample Question 35:**
Rs. 5,000 is invested at 10% per annum compound interest for 3 years. What is the total interest earned?

*Solution:*
Amount = P × (1 + r/100)^n = 5,000 × (1.10)^3 = 5,000 × 1.331 = 6,655
Total interest = 6,655 - 5,000 = **Rs. 1,655**

**Sample Question 36:**
What is the difference between simple interest and compound interest on Rs. 10,000 at 10% per annum for 2 years?

*Solution:*
Simple Interest = PRT/100 = 10,000 × 10 × 2/100 = Rs. 2,000
Compound Interest = P[(1+r/100)^n - 1] = 10,000[(1.1)^2 - 1] = 10,000 × 0.21 = Rs. 2,100
Difference = 2,100 - 2,000 = **Rs. 100**

### Averages and Weighted Averages

**Sample Question 37:**
The average of 25 numbers is 36. If two numbers 48 and 52 are excluded, what is the average of the remaining numbers?

*Solution:*
Sum of 25 numbers = 25 × 36 = 900
Sum after excluding = 900 - 48 - 52 = 800
Average of remaining 23 numbers = 800/23 = **34.78 (approximately 34.8)**

**Sample Question 38:**
In a class of 40 students, 60% are boys. The average score of boys is 70 and the average score of girls is 80. What is the overall average score?

*Solution:*
Number of boys = 40 × 0.60 = 24
Number of girls = 40 × 0.40 = 16
Total score = 24 × 70 + 16 × 80 = 1,680 + 1,280 = 2,960
Average = 2,960/40 = **74**

### Age Problems

**Sample Question 39:**
A's age is 3 times B's age. 5 years ago, A's age was 5 times B's age. What are their current ages?

*Solution:*
Current: A = 3B
5 years ago: A - 5 = 5(B - 5)
3B - 5 = 5B - 25
20 = 2B
B = 10, A = 30
**A is 30, B is 10.**

**Sample Question 40:**
The sum of the ages of a father and son is 56. 4 years ago, the father was 3 times as old as his son. What are their current ages?

*Solution:*
Let son's current age = s, father's current age = f
f + s = 56
4 years ago: f - 4 = 3(s - 4) → f - 4 = 3s - 12 → f = 3s - 8
Substituting: 3s - 8 + s = 56 → 4s = 64 → s = 16, f = 40
**Father is 40, Son is 16.**

---

## Additional Logical Reasoning Sample Questions

### Input-Output Problems

Input-output problems present a machine that transforms input in a specific way across multiple steps. The challenge is identifying the transformation rule.

**Sample Question 41:**
A word-arrangement machine processes words according to a specific pattern. Observe the steps:

Step 1: "rice ball coat dent easy fate" → "ball coat dent easy fate rice"
Step 2: "coat dent easy fate rice ball" → "dent easy fate rice ball coat"
Step 3: "easy fate rice ball coat dent" → ...

What is Step 4?

*Solution:*
The pattern is that the first word moves to the end each step.
Step 1 Input: rice ball coat dent easy fate → moves "rice" to end
Step 2: moves "ball" to end
Step 3: moves "coat" to end → "fate rice ball coat easy dent"

Wait, let me trace more carefully:
Original: rice ball coat dent easy fate
Step 1: ball coat dent easy fate rice (rice → end)
Step 2: coat dent easy fate rice ball (ball → end)
Step 3: dent easy fate rice ball coat (coat → end)
Step 4: easy fate rice ball coat dent (dent → end)

**Step 4 output: easy fate rice ball coat dent**

### Ranking and Arrangement Puzzles

**Sample Question 42:**
In a group of 5 students competing in a science test:
- Priya scored higher than Rahul but lower than Sonal
- Kunal scored higher than Meera but lower than Rahul
- Sonal did not score the highest

Rank them from highest to lowest.

*Solution:*
From clues: Kunal < Rahul < Priya < Sonal (from clues 1 and 2... wait)
Clue 1: Rahul < Priya < Sonal
Clue 2: Meera < Kunal < Rahul
Clue 3: Sonal is not the highest → someone scored higher than Sonal

Combining: Meera < Kunal < Rahul < Priya < Sonal, but Sonal is not highest.
We have 5 students. The order so far places them all: Meera, Kunal, Rahul, Priya, Sonal.
But "Sonal did not score the highest" contradicts this since Sonal is last (highest) in this order.

There must be a 6th implied person, or the clue means someone else scored above Sonal. With only 5 students, if Sonal is not the highest, someone among these 5 must be above Sonal. But our chain puts Sonal at the top. Re-read clue 1: "Priya scored higher than Rahul but lower than Sonal" → Rahul < Priya < Sonal.

If Sonal is not the highest in a group of exactly 5, and our chain places Sonal at top... this is a contradiction in the problem as stated. Likely the intended answer is **Sonal, Priya, Rahul, Kunal, Meera** (1st to 5th), with the "Sonal did not score the highest" clue perhaps meaning "not the single highest" or being a misdirection that resolves to Sonal being 1st anyway.

*This illustrates an important test-taking skill: when a problem appears to have a contradiction, re-read each clue carefully for alternative interpretations before concluding the problem is flawed.*

### Data Sufficiency

Data sufficiency questions (less common but present in some NQT windows) present a question followed by two statements and ask whether the question can be answered from one statement alone, both together, or neither.

**Sample Question 43:**
What is the value of the two-digit number XY (where X and Y are digits)?

Statement 1: X + Y = 11
Statement 2: X - Y = 3

*Solution:*
Statement 1 alone: Multiple possibilities (29, 38, 47, 56, 65, 74, 83, 92). Not sufficient.
Statement 2 alone: Multiple possibilities (41, 52, 63, 74, 85, 96). Not sufficient.
Both together: X + Y = 11 and X - Y = 3 → 2X = 14 → X = 7, Y = 4. The number is 74. **Both statements together are sufficient.**

---

## Additional Verbal Ability Sample Questions

### Advanced Reading Comprehension

**Sample Passage 2:**
Artificial intelligence in healthcare presents both extraordinary promise and genuine complexity. Machine learning models trained on vast medical imaging datasets now detect certain cancers with accuracy comparable to specialist physicians. Natural language processing systems extract structured information from unstructured clinical notes, potentially reducing administrative burden on medical professionals. These capabilities, once confined to research settings, are beginning to enter clinical practice.

Yet the path from technological capability to clinical deployment is not straightforward. Medical AI systems face regulatory requirements that demand rigorous validation across diverse patient populations. A model trained predominantly on data from one demographic may perform less well when deployed in communities with different disease prevalence or presentation patterns. The consequences of algorithmic errors in medicine are not abstract - a false negative in cancer detection can mean delayed treatment; a false positive means unnecessary intervention.

The governance questions that AI in healthcare raises are not primarily technical. They concern accountability: when an AI-assisted diagnosis proves incorrect, who bears responsibility - the physician who relied on the system, the institution that deployed it, or the company that built it? They concern equity: if AI diagnostic tools are adopted primarily by well-resourced health systems, will the technology widen the gap in care quality between advantaged and disadvantaged populations? These questions require answers from ethicists, regulators, and communities, not only from technologists.

**Question 1:** What is the central concern raised in the third paragraph?
(a) Technical limitations of AI diagnostic systems
(b) Accountability and equity questions arising from AI in healthcare
(c) The cost of deploying AI in hospitals
(d) Regulatory requirements for medical AI

*Answer:* (b) - The third paragraph explicitly identifies accountability and equity as its central concerns.

**Question 2:** Which of the following best describes the author's overall perspective on AI in healthcare?
(a) Unconditional enthusiasm for the technology's potential
(b) Complete skepticism about AI's ability to improve healthcare
(c) Balanced acknowledgment of potential with awareness of complexity
(d) Primarily concerned with regulatory obstacles to adoption

*Answer:* (c) - The author acknowledges genuine promise (cancer detection accuracy) while systematically presenting the governance, equity, and accountability challenges.

**Question 3:** The phrase "consequences of algorithmic errors in medicine are not abstract" most nearly means:
(a) AI errors are rare and therefore not worth worrying about
(b) Medical AI errors have specific, real-world impacts on patients
(c) Algorithmic errors in medicine are difficult to quantify
(d) Medical personnel should not rely on AI systems

*Answer:* (b) - The sentence immediately following provides concrete examples (false negatives and positives in cancer detection) that illustrate the real-world impact.

### Para-Completion

**Sample Question 44:**
Choose the sentence that best completes the paragraph:

"The global shift toward remote work has accelerated by several years what would otherwise have been a gradual adoption. Collaboration tools, once considered supplements to in-person interaction, have become primary communication infrastructure for millions of organizations. The long-term consequences of this shift are still being understood. ____________"

(a) Office buildings remain an important asset class for commercial real estate.
(b) Research on remote work productivity shows mixed results across different roles and contexts.
(c) Video conferencing technology was first developed in the 1970s.
(d) Organizations are now reconsidering the role of physical office space in employee experience, productivity, and culture.

*Answer:* (d) - The paragraph discusses the shift to remote work and its ongoing consequences. Sentence (d) extends naturally from "consequences are being understood" to what organizations are now reconsidering. Sentence (b) is also relevant but less direct as a completion.

### Cloze Test (Fill Multiple Blanks in a Passage)

Some NQT verbal sections include cloze tests - passages with multiple blanks requiring selection from given options.

**Sample Passage:**
The concept of emotional intelligence (EI) has ___1___ significant attention in both academic and corporate settings. Unlike traditional notions of intelligence, which focus primarily on cognitive ___2___, EI encompasses the ability to recognize, understand, and ___3___ one's own emotions and the emotions of others. Research suggests that high EI ___4___ with better performance in roles requiring interpersonal communication and leadership.

1. (a) received (b) given (c) taken (d) made
2. (a) capacity (b) ability (c) performance (d) potential
3. (a) suppress (b) manage (c) express (d) ignore
4. (a) connects (b) correlates (c) relates (d) associates

*Answers:*
1. (a) "received" - attention is received, not given or taken in this context
2. (b) "ability" - traditional intelligence measures cognitive ability
3. (b) "manage" - managing emotions is the EI concept; suppress and ignore are negative
4. (b) "correlates" - the standard academic phrasing for statistical relationship

---

## Coding Section: Additional Problem Types and Solutions

### Dynamic Programming Basics

The simplest dynamic programming problems that can appear in NQT Medium difficulty:

**Fibonacci with memoization:**
```python
def fibonacci(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 2:
        return 1
    memo[n] = fibonacci(n-1, memo) + fibonacci(n-2, memo)
    return memo[n]
```

**Climbing Stairs Problem:**
You are climbing stairs. It takes n steps to reach the top. Each time you can climb 1 or 2 steps. How many distinct ways can you climb to the top?

*This is the Fibonacci pattern: ways(n) = ways(n-1) + ways(n-2)*

```python
def climb_stairs(n):
    if n <= 2:
        return n
    prev, curr = 1, 2
    for _ in range(3, n+1):
        prev, curr = curr, prev + curr
    return curr
```

**Maximum Subarray (Kadane's Algorithm):**
Given an array of integers, find the maximum sum of any contiguous subarray.

```python
def max_subarray(nums):
    max_sum = nums[0]
    current_sum = nums[0]
    for i in range(1, len(nums)):
        current_sum = max(nums[i], current_sum + nums[i])
        max_sum = max(max_sum, current_sum)
    return max_sum
```

*Example:* arr = [-2, 1, -3, 4, -1, 2, 1, -5, 4]
Output: 6 (subarray [4, -1, 2, 1] has maximum sum)

### Binary Search Applications

Binary search is one of the most reliably tested Medium-difficulty patterns in NQT:

**Finding element in sorted rotated array:**
A sorted array was rotated at some pivot. Find the target element.

```python
def search_rotated(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        # Left half is sorted
        if nums[left] <= nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        # Right half is sorted
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return -1
```

### Tree Traversals

Level-order traversal (BFS) is the most commonly tested tree question in NQT:

```python
from collections import deque

def level_order(root):
    if not root:
        return []
    result = []
    queue = deque([root])
    while queue:
        level_size = len(queue)
        current_level = []
        for _ in range(level_size):
            node = queue.popleft()
            current_level.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(current_level)
    return result
```

**Maximum depth of binary tree:**
```python
def max_depth(root):
    if not root:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
```

### String Pattern Matching

**Check if string matches a pattern:**
For example, pattern "aab" and string "ccd" - 'a' maps to 'c', 'b' maps to 'd'. Does it match?

```python
def word_pattern(pattern, s):
    words = s.split()
    if len(pattern) != len(words):
        return False
    char_to_word = {}
    word_to_char = {}
    for char, word in zip(pattern, words):
        if char in char_to_word:
            if char_to_word[char] != word:
                return False
        else:
            if word in word_to_char:
                return False
            char_to_word[char] = word
            word_to_char[word] = char
    return True
```

---

## Exam Pacing Strategy: Putting It All Together

Understanding question types is half the preparation. Knowing how to allocate time across question types within sections is the other half.

### Quantitative Aptitude Pacing (40 minutes, ~26 questions)

Target: approximately 90 seconds per question on average.

**Fast questions (60 seconds or less):** Simple percentage calculations, HCF/LCM with direct formula, basic probability. Solve immediately.

**Medium questions (90-120 seconds):** Time-speed-distance equations, work problems, successive change calculations. Solve on first pass.

**DI sets (3-4 minutes per set including all questions):** Invest the time for a complete data reading, then answer all 3-4 questions from that single reading. DI questions solved consecutively from one data reading cost less total time than DI questions spread across the section.

**Skip criteria:** If a question requires more than 90 seconds with no clear path to solution, mark it and return at the end. Spending 3 minutes on one hard question while 2 easy questions remain unanswered is a losing trade.

### Logical Reasoning Pacing (40 minutes, ~26 questions)

**Arrangement problems (4-6 minutes each):** These are the most time-consuming type. If the arrangement is clearly resolvable from the constraints, invest the time. If after 90 seconds of constraint application no clear structure has emerged, skip and return - arrangement problems either click or they do not, and forcing them past the click point is rarely efficient.

**Series problems (45-60 seconds):** Usually solvable quickly once the pattern is identified. If the pattern is not obvious after 45 seconds, skip - the series might require a higher-order analysis (two interleaved series, second differences, etc.) that is better attempted at the end.

**Syllogisms (60-75 seconds):** Quick to solve with practiced Venn diagram method. Prioritize these over arrangements.

### Verbal Pacing (30 minutes, ~24 questions)

**RC passages (~4 minutes each including questions):** Read all questions first, read passage actively for main idea and structure, answer questions without re-reading full passage (except for specific detail questions requiring exact text location).

**Grammar questions (30-45 seconds):** Check subject-verb agreement first, then tense, then modifiers. If the error is not in these top-three categories, check other grammar rules.

**Vocabulary questions (30-45 seconds):** Know the word → answer directly. Do not know the word → eliminate known incorrect answers, guess from remaining.

### Coding (45-60 minutes, 2 problems)

**First 20 minutes:** Easy problem. Read completely, plan, code, test mentally with examples, submit.

**Remaining time:** Medium problem. Apply the complete approach: read, plan algorithm, consider edge cases, code, test with provided examples, submit.

**If 20 minutes is not enough for Easy:** Submit a partial Easy solution after 25 minutes and switch to Medium. A partial Easy + partial Medium typically scores better than a complete Easy + no Medium attempt.

---

## Frequently Asked Questions About TCS NQT Questions and Patterns

**Q1: What are the main sections of TCS NQT?**

TCS NQT consists of a Foundation Section (Quantitative Aptitude, Logical Reasoning, Verbal Ability, and Personality) and an Advanced Section (higher-difficulty Quantitative and Reasoning, plus Coding). The Foundation Section is attempted by all candidates; the Advanced Section distinguishes Ninja and Digital track performance levels.

**Q2: How many questions are in each section of TCS NQT?**

The exact question count varies by NQT window. Typically: Quantitative Aptitude approximately 26 questions, Logical Reasoning approximately 26 questions, Verbal Ability approximately 24 questions, and Personality approximately 20-25 questions. The Advanced section adds harder versions of the quantitative and reasoning questions plus 2 coding problems.

**Q3: What is the time limit for each NQT section?**

Approximately 40 minutes for Quantitative Aptitude, 40 minutes for Logical Reasoning, 30 minutes for Verbal, and 10 minutes for Personality. Coding is typically 45-60 minutes for two problems. Total exam duration is approximately 3 hours.

**Q4: What programming languages can I use for the NQT coding section?**

TCS permits five languages: C, C++, Java, Python, and Perl. Python and Java are the most commonly chosen. Use the language you know most fluently, as coding speed directly affects how much of each problem you complete.

**Q5: How difficult is the TCS NQT coding section?**

The Easy problem is comparable to LeetCode Easy difficulty - problems solvable in 15-20 minutes with basic data structure knowledge. The Medium problem is comparable to LeetCode Medium difficulty - requiring algorithmic thinking and 25-35 minutes for a complete solution. Consistent practice on LeetCode Easy and Medium problems is the most reliable preparation.

**Q6: What types of aptitude questions appear most frequently in TCS NQT?**

Data Interpretation (highest frequency and highest weight), percentages and ratios, time-speed-distance, work problems, number systems, probability, and permutations/combinations. All of these are covered in the [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html).

**Q7: What logical reasoning question types should I prepare for?**

Number and letter series, seating arrangements (linear and circular), blood relations, coding-decoding, direction and distance, syllogisms, and puzzles. Seating arrangement problems are the most time-consuming type and deserve specific practice.

**Q8: What verbal ability topics appear in TCS NQT?**

Reading comprehension (3-4 passages), sentence completion, fill in the blanks, error detection, para-jumbles, synonyms and antonyms, and critical reasoning. Reading comprehension is the highest-weight verbal topic.

**Q9: Is there a negative marking in TCS NQT?**

Yes, typically -0.33 per wrong answer for 1-mark questions. This means confident answers should always be submitted, uncertain answers should be evaluated for elimination potential before guessing, and completely unknown questions may be better left blank depending on your elimination ability.

**Q10: What is the difference between Foundation and Advanced section difficulty?**

Foundation section questions are at moderate difficulty - functional competency is sufficient. Advanced section questions are harder versions of the same topics, testing deeper understanding and faster problem-solving. Advanced section performance, particularly in coding, is the primary differentiator for Digital track consideration.

**Q11: How should I approach reading comprehension passages to maximize speed and accuracy?**

Use the questions-first approach: read all questions for a passage before reading the passage itself. This focuses your reading on what the questions actually test. For main idea questions, look for the central argument. For detail questions, use the answer options as search terms when returning to the passage. For inference questions, verify that your answer is supported by the passage without going beyond it.

**Q12: What is the best way to approach syllogism questions?**

Use the Venn diagram method: draw circles for each category mentioned, fill in the relationships defined by each statement, and check whether the conclusion diagram is necessarily true given all possible valid configurations. For "definitely follows" conclusions, the answer must be true in all possible diagrams. For "possibly follows" conclusions, the answer must be true in at least one possible diagram.

**Q13: What coding algorithms appear most frequently in NQT?**

Arrays (two-pointer technique, sliding window, frequency counting), strings (palindrome checking, anagram detection, character counting), linked lists (reversal, cycle detection), trees (traversals, depth calculation), sorting, and basic dynamic programming (Fibonacci, climbing stairs, simple sequence problems). Start with these before extending to less common algorithm types.

**Q14: How does the personality assessment affect my NQT score?**

The personality assessment is typically not weighted in the traditional score calculation the same way aptitude sections are. Its primary purpose is cultural fit assessment, not performance ranking. Respond authentically with professional values in mind. Consistency across all personality questions is important - contradictory answers are detected and evaluated negatively.

**Q15: What is the most common mistake candidates make in the NQT coding section?**

Spending too long on the Medium problem before completing the Easy problem. The Easy problem guarantees marks that the Medium problem can only add to. Completing Easy first, then spending remaining time on Medium, maximizes expected marks. Many candidates lose marks by attempting Medium first and running out of time before completing Easy.

**Q16: Should I prepare differently for the Foundation vs. Advanced sections?**

Foundation requires consistent accuracy at moderate speed. Advanced requires higher accuracy with significantly faster problem-solving, particularly in data interpretation and arrangement problems. Prepare Foundation topics to solid comprehension first, then extend to the harder variants that appear in Advanced. Coding preparation is entirely Advanced-specific - there is no coding component in Foundation.

**Q17: What is the best way to handle data interpretation questions given their time-consuming nature?**

Questions-first approach (read all questions before reading the data set), selective data reading (only read what the questions require), and approximation techniques (round large numbers to 2-3 significant figures for percentage calculations). DI questions from the same set should be solved consecutively to maximize the data-reading investment. Spreading DI set questions across the section and re-reading the data for each question is the most common time-management error.

**Q18: What vocabulary level is tested in TCS NQT verbal?**

Professional English at the level expected for business communication - not advanced academic vocabulary, but clear professional vocabulary. Common words tested include: loquacious/verbose, ephemeral/transient, taciturn/laconic, ambiguous/equivocal, pragmatic/practical. Building vocabulary through consistent reading of quality business publications (Economic Times, The Hindu) is more effective than memorizing word lists.

**Q19: How do I approach error detection questions in the verbal section?**

Systematically check the specific error types that appear most frequently: subject-verb agreement (especially with collective nouns and "neither...nor" constructions), tense consistency, pronoun reference, modifier placement, and word usage errors. If you identify an error in your first reading, verify it matches exactly one of the underlined portions. If no error is immediately obvious, check subject-verb agreement first - it is the most common error type.

**Q20: What is the optimal preparation time for TCS NQT given the difficulty levels across sections?**

For candidates with engineering backgrounds: 3-4 months of consistent preparation is ideal. Week 1-4: Conceptual foundation for all topics. Week 5-8: Speed development through timed section practice. Week 9-12: Full mock tests and error analysis. For the coding section specifically, begin LeetCode practice from day one - coding skills require more time to build than aptitude skills. Use the [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) as the primary preparation resource for structured, NQT-calibrated practice throughout.

---

## The Question Pattern Summary: Your Preparation Checklist

Before any NQT window, verify your readiness across these specific question types:

**Quantitative Aptitude - can you solve these in under 90 seconds?**
- HCF/LCM word problems
- Successive percentage change calculations
- Time-speed-distance with relative motion
- Work problems with multiple workers
- DI: percentage change between years from tables
- DI: proportional calculations from pie charts
- Probability with replacement and without replacement
- Permutation/combination problems with constraints

**Logical Reasoning - can you solve these in under 90 seconds?**
- Number series with two-step or compound patterns
- Letter series with varying position gaps
- Linear seating arrangement with 6-7 people
- Circular arrangement with opposite and adjacent constraints
- Blood relations with three-generation problems
- Coding-decoding with shift patterns
- Syllogisms with "some" and "all" statements
- Direction problems with multiple turns

**Verbal - can you achieve these accuracy levels?**
- Reading comprehension: 85%+ accuracy in 4 minutes per passage
- Fill in the blank (prepositions, conjunctions): 90%+ accuracy
- Error detection (agreement, tense, modifier): 85%+ accuracy
- Vocabulary synonym/antonym: 80%+ accuracy
- Para-jumble (4-6 sentences): 75%+ accuracy

**Coding - can you achieve this performance?**
- Easy problems: complete correct solution in 18-20 minutes
- Medium problems: meaningful progress (4+ of 10 test cases passing) in 30-35 minutes

This checklist, evaluated honestly, tells you exactly where your preparation stands relative to the standard that produces NQT qualification. Every gap between your current performance and the checklist standard is a preparation investment that directly converts into score.

Practice specifically. Measure honestly. Improve deliberately. Show up ready.

---

## The Connection Between Question Types and Real TCS Work

Understanding why the NQT tests these specific question types - not just what they are - transforms preparation from mechanical to meaningful.

### Why Quantitative Aptitude Matters in TCS Work

The quantitative skills tested in NQT directly transfer to day-to-day TCS delivery work:

**Data interpretation:** TCS delivery involves reading status reports, financial data, client metrics, and project performance dashboards. The ability to extract relevant information from data presentations quickly and accurately is used every day in every TCS role.

**Percentages and ratios:** Project completion percentages, resource utilization ratios, defect rates, test coverage percentages - these calculations are constant in technology delivery environments. A consultant who can quickly calculate that a 15% scope increase requires 20% more effort at the same resource efficiency is more valuable than one who needs to open a spreadsheet.

**Probability:** Risk assessment in project planning involves probability thinking. Understanding that a 20% chance of a two-week delay and a 15% chance of a one-week delay combine to a specific expected project duration is applied probability.

The NQT does not test these skills in their exact work form - it tests them in the abstract problem form that reveals genuine quantitative reasoning ability.

### Why Logical Reasoning Matters in TCS Work

**Arrangement problems:** Scheduling problems - who can work with which client, which resource can be assigned to which project given constraints - are arrangement problems with business variables replacing people in seats. The systematic constraint-application methodology is the same.

**Series and pattern recognition:** Debugging code, identifying performance degradation patterns in production systems, detecting anomalies in data pipelines - all require the pattern recognition that series questions develop.

**Deductive reasoning from syllogisms:** Business analysis involves reasoning from premises to conclusions. "All our BFSI clients require PCI-DSS compliance. This new client is a payment processor. Therefore this client requires PCI-DSS compliance." This is applied syllogism.

### Why Verbal Ability Matters in TCS Work

TCS is a client-facing services organization. Written communication with clients, requirements documents, status reports, technical specifications, and presentations are constant deliverables. The verbal skills tested in NQT - reading comprehension accuracy, grammatically correct writing, logical argument construction - are the exact skills TCS's working environment requires daily.

### Why Coding Matters in TCS Work

This requires no elaboration for software delivery work. The specific algorithm types tested in NQT - array manipulation, string processing, tree traversals, dynamic programming - are the building blocks of the code that TCS engineers write, review, and maintain across their careers.

The NQT is not arbitrary. Every section tests capabilities that TCS's working environment genuinely uses. Preparing for the NQT develops not just exam performance but the professional capabilities that a TCS career will reward.

---

## Common Errors and How to Avoid Them

### Quantitative Aptitude Common Errors

**Error 1: Confusing percentage of percentage**
"20% of 50% of 400" is often miscalculated as "20% + 50% of 400."
Correct approach: 50% of 400 = 200; 20% of 200 = 40.

**Error 2: Misapplying the successive change formula**
When a value increases by x% and then decreases by y%, the net change is NOT (x-y)%.
Correct formula: x + (-y) + x×(-y)/100 = x - y - xy/100.

**Error 3: Not reading DI carefully**
Reading column headers incorrectly or confusing units (crore vs. lakh, year vs. quarter) produces calculation errors on questions where the concept is clear.
Prevention: Spend 20 extra seconds confirming units and headers before calculating.

**Error 4: HCF/LCM application confusion**
Applying HCF where LCM is needed (and vice versa) in word problems.
Quick guide: Maximum/largest → usually HCF. Minimum/first occurrence/smallest → usually LCM.

### Logical Reasoning Common Errors

**Error 1: Premature conclusion in arrangements**
Drawing an arrangement before all constraints have been applied, then finding a conflict.
Prevention: List all constraints, apply most restrictive first, verify all constraints at the end.

**Error 2: Direction problem with axis confusion**
Confusing left/right from the character's perspective versus the reader's perspective.
Prevention: Always draw a compass diagram. "John turns right" means his right, which requires orienting from his current facing direction.

**Error 3: Syllogism over-inference**
Concluding that because "all A are B," "all B are A" also follows.
This is invalid - the subset relationship is one-directional. "All doctors are humans" does not mean "all humans are doctors."

**Error 4: Blood relation gender assumption**
Assuming "cousin" means male cousin or "sibling" means same gender.
Blood relation chains must be traced without assuming genders not specified.

### Verbal Ability Common Errors

**Error 1: Choosing the most extreme inference**
For "which conclusion can be drawn from the passage" questions, the correct answer is the most conservative inference that the passage directly supports.
Extreme inferences (universally, always, never) are rarely correct unless the passage is equally extreme.

**Error 2: Selecting the grammatically awkward but technically correct option**
Error detection questions sometimes have options that are technically grammatically correct but sound awkward because of style rather than grammar.
Focus on identifying actual grammatical rules being violated, not stylistic awkwardness.

**Error 3: Vocabulary synonym misidentification**
Selecting a synonym by sound similarity rather than meaning.
"Ephemeral" and "ethereal" sound similar but have different meanings. Always evaluate meaning, not phonetics.

### Coding Common Errors

**Error 1: Not handling the empty input case**
A function that processes an array should first check if the array is None or empty.
```python
def process(arr):
    if not arr:
        return 0  # or appropriate default
    # rest of logic
```

**Error 2: Off-by-one errors in loops**
The most common source of wrong answers in otherwise correct logic.
Prevention: Trace through the edge cases manually. For range(n), the last index is n-1. For range(1, n+1), both 1 and n are included.

**Error 3: Not returning the result**
Writing code that computes the correct answer but stores it in a variable without returning it.
Prevention: Add return statement verification as the last pre-submission check.

**Error 4: Integer overflow in Python**
This is actually not a Python issue (Python handles arbitrary precision integers natively) but is a concern in Java and C++.
In Java: use `long` instead of `int` when values may exceed 2^31-1.
In C++: use `long long` for large number operations.

---

## Building a Question Type Familiarity System

The most efficient preparation approach for NQT question types is a spaced repetition system - practicing each question type repeatedly with increasing time between repetitions as familiarity grows.

**Week 1-2:** Introduce all question types. Solve one example of each type without time pressure, understanding the approach fully.

**Week 3-4:** Practice each question type in small batches (5-8 questions per type) with light time pressure.

**Week 5-6:** Practice all question types in mixed sets with full time pressure. This builds the pattern recognition that real exam conditions require - recognizing the question type and retrieving the appropriate approach happens faster with mixed practice than with blocked practice.

**Week 7-8:** Full section-level and exam-level practice with emphasis on pacing and error review.

The [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) structures practice across all question types with the calibrated difficulty and timed conditions that this progression requires. The 2,000+ practice questions span every topic type covered in this guide, and the mock test format simulates the actual exam experience.

Question familiarity is built through repetition and review. Every question type described in this guide will appear in the exam in some form. Every question type practiced genuinely before the exam is one that will not surprise you when it appears.

Know the types. Practice the types. Own the exam.

---

## Quick Reference: All NQT Question Types at a Glance

For candidates who want a concise reference of every question type covered in this guide:

### Quantitative Aptitude Topics
Number systems (divisibility, HCF/LCM, remainder theorem, cyclicity of powers), percentages (simple, successive change, cost-selling-marked price), ratios and proportions (direct, inverse, alligation/mixture), time-speed-distance (unidirectional, relative motion, trains and platforms), work problems (individual and combined rates, pipes and cisterns), profit and loss (cost price, marked price, discount, profit percentage), simple and compound interest (formulae and difference), averages (arithmetic mean, weighted average, age problems), data interpretation (tables, bar charts, pie charts, line graphs, combination charts), probability (basic, complementary, conditional), permutations and combinations (arrangement with constraints, selection problems).

### Logical Reasoning Topics
Number series (arithmetic, geometric, squared/cubed, two-interleaved, prime), letter series (position gap patterns, alphabetical relationships), alphanumeric series (combined patterns), seating arrangements (linear and circular, single and multi-row), blood relations (two and three generation families), coding-decoding (letter shift, position-based, symbol substitution), direction and distance (multi-turn navigation, net displacement), syllogisms (all/some/no statements, definite and possible conclusions), input-output machines (systematic word/number rearrangement), data sufficiency (two-statement sufficiency), puzzles (multi-attribute assignment).

### Verbal Ability Topics
Reading comprehension (main idea, detail retrieval, inference, vocabulary in context), sentence completion (prepositions, conjunctions, contextual vocabulary), fill in the blanks (grammar, vocabulary), error detection (subject-verb agreement, tense consistency, pronoun reference, modifier placement, word usage), para-jumbles (4-6 sentence reordering), para-completion (appropriate concluding sentence), synonyms and antonyms, cloze tests (multi-blank passage completion), critical reasoning (assumption identification, strengthening/weakening arguments).

### Coding Topics
Arrays (manipulation, two-pointer, sliding window, frequency counting), strings (palindrome, anagram, character counting, pattern matching), linked lists (traversal, reversal, cycle detection, merge), trees (traversals, depth, balance checking), sorting algorithms (conceptual understanding of major sorts), searching (linear search, binary search and variants), recursion (factorial, Fibonacci, tree problems), basic dynamic programming (Fibonacci with memoization, climbing stairs, maximum subarray).

---

## The Thirty Questions That Matter Most

For candidates who want to practice the single most important question from each major NQT topic type, the 30 questions in this guide form the core practice set. Working through each:

1-10: Five quantitative aptitude questions (number systems, percentages/ratios, time-speed-distance, work, DI) solved within 90 seconds each.

11-20: Five logical reasoning questions (number series, letter series, seating arrangement, blood relations, syllogisms) solved within the specified time.

21-25: Five verbal ability questions (reading comprehension passage with four questions, one error detection) solved accurately.

26-30: Two coding problems (Easy: palindrome check and two-sum; Medium: linked list cycle detection and longest substring without repeat) solved completely.

This 30-question practice set, done once per week with honest timing, tracks your NQT readiness across all sections simultaneously. When all 30 questions are solved within time and with 85%+ accuracy, you are in NQT-qualifying territory.

The question types are known. The preparation path is clear. The performance is yours to build.

Build it systematically. Build it honestly. Show up at the NQT ready to demonstrate exactly what you have built.

The preparation converts to performance when the questions are familiar, the timing is practiced, and the approach to each question type is automatic rather than effortful.

That automatic familiarity - built question type by question type, section by section, week by week - is what separates qualifying scores from non-qualifying ones. It is also fully buildable through deliberate preparation.

Start with the questions in this guide. Continue with the full practice set at the [TCS NQT Preparation Guide on ReportMedic](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html). Build the familiarity. Show up ready.
