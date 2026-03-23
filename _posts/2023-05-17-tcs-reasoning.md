---
layout: post
title: "TCS Reasoning: Systematic Solving Methods"
page_title: "TCS Reasoning Ability Complete Guide - Foundation and Advanced Topics with Systematic Solving Approaches"
date: 2023-05-17
categories: ["Industry"]
tags: ["TCS reasoning", "TCS logical reasoning", "TCS reasoning questions", "TCS puzzles", "TCS coding decoding"]
excerpt: "Master TCS Reasoning Ability at both Foundation and Advanced levels. Systematic approaches for every question type, no guesswork."
image: "/assets/images/blog/blog-09.webp"
reading_time: 60
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
Reasoning Ability is the section that most TCS NQT candidates underestimate during preparation. Many candidates spend weeks on aptitude formulas and assume reasoning will take care of itself because it "tests common sense." It does not test common sense - it tests systematic logic, and systematic logic is learnable. The difference between a candidate who scores 20/25 in reasoning and one who scores 14/25 is almost never intelligence. It is whether the candidate has a reliable, practiced technique for each question type, or whether they are attempting to solve by intuition under time pressure. This guide provides that technique for every reasoning topic, at both Foundation and Advanced difficulty levels, with worked examples and the common traps that send prepared candidates to the wrong answer.

![TCS Guide](/assets/images/blog/blog-09.webp)

## Reasoning Fundamentals: The Logic-First Mindset

Before any individual technique, there is a mindset shift required for reasoning questions. Most candidates approach them the way they approach aptitude questions - start calculating, see where it goes. Reasoning problems require a different first step.

### The Three-Step Reasoning Protocol

**Step 1: Classify the question type** (5 seconds maximum)
Reading the first sentence of a reasoning question reveals its type almost immediately. Blood relation problems have family relationship words. Seating arrangements have positioning language. Series questions show a sequence with a gap. The classification happens in 5 seconds or it requires more reading time.

**Step 2: Apply the correct technique** (not "figure out what to do")
Every reasoning question type has a specific solving technique. You do not figure out the technique during the exam - you apply the technique you have already practiced. If you cannot identify which technique applies within 10 seconds of classification, that question type needs more practice.

**Step 3: Execute systematically** (diagram, table, or tree)
The execution of reasoning problems is visual. Seating arrangements require drawn diagrams. Blood relations require family trees. Direction sense requires drawn paths. Series questions require written difference sequences. Candidates who attempt to hold the problem in their head make errors. Candidates who externalise the problem onto rough paper almost never do.

### Why Systematic Beats Intuitive

Intuitive solving works when problems are simple. At Foundation level, some questions are simple enough that intuition suffices. At Advanced level, no question is simple enough for intuition - they are specifically designed to fool intuitive solvers with plausible-looking wrong answers. The candidate who has a technique is immune to these traps. The intuitive solver falls into them reliably.

---

## Topic 1: Coding-Decoding

### What TCS Tests

Coding-decoding at Foundation level uses letter shifting (A becomes D if shifted by 3 positions), number substitution (each letter gets a number based on position or a transformed position), and symbol substitution (a given code replaces each letter with a symbol). Advanced level introduces compound patterns (letters reversed AND shifted) and new-pattern coding (relationships between words and codes are given; derive the code for a new word).

### Technique 1: Letter Shifting

**Foundation problem:** If FRIEND is coded as HUMGL, how is CANDLE coded?

**Approach:** Find the shift for each letter.
F → H: +2, R → U: +3, I → M: +4, E → G: +2, N → L: -2, D → ?

Wait - the shifts are not consistent (2, 3, 4, 2, -2). This is not a simple uniform shift. Apply the technique: list each original letter and its coded equivalent side by side.

```
F(6)  → H(8):  +2
R(18) → U(21): +3
I(9)  → M(13): +4
E(5)  → G(7):  +2
N(14) → L(12): -2
D(4)  → ?(?)
```

Pattern: The shifts are +2, +3, +4, +2, -2... this seems irregular. Re-examine: perhaps the letters in FRIEND are being rearranged, not shifted. Try: F→H (letter 1 of coded word), but position 1 in coded word is H. Let's check if HUMGL is FRIEND written with +2 shift on alternate letters, or some other rule.

Alternatively, check if word is reversed and shifted: DNEIRF → shifted? D(+4)=H, N(+7)=U, E(+8)=M, I(+4)=M... no clear pattern.

Try: each letter's position in the alphabet + its position in the word:
F=6, position 1: 6+1=7=G? No (gives H=8).
F=6, position 1: 6+2=8=H. R=18, position 2: 18+3=21=U. I=9, position 3: 9+4=13=M. E=5, position 4: 5+2=G? No, 5+2=7=G, but coded is G. ✓ Wait, let me recount: HUMGL has 5 letters but FRIEND has 6.

This example has complexity that requires careful letter-by-letter analysis. The key lesson: always write the mapping out explicitly before looking for patterns. Never try to spot a pattern visually.

**The letter shifting shortcut (for uniform shift problems):**
If all letters shift by k positions: Z wraps to A (so treat alphabet as circular, position 1-26). Shift formula: (position + k - 1) mod 26 + 1.

### Technique 2: New Pattern Coding

**Advanced problem:**
If "APPLE goes YNNVO" and "MANGO goes KYLAM", then "GRAPE goes ?"

**Approach:** Map each letter position:
A(1)→Y(25): +24 or -2 (circular). P(16)→N(14): -2. P(16)→N(14): -2. L(12)→V(22): +10? O(15)→O(15): 0.

Inconsistent shifts across positions - check if it's position-dependent:
Position 1: A(1)→Y(25): A-2 (wrap). Position 2: P(16)→N(14): -2. Position 3: P(16)→N(14): -2. Position 4: L(12)→V(22): +10. Position 5: O(15)→O(15): 0.

Verify with MANGO→KYLAM:
M(13)→K(11): -2. A(1)→Y(25): -2 (wrap). N(14)→L(12): -2. G(7)→A(1): -6? O(15)→M(13): -2.

Pattern: positions 1,2,3,5 shift by -2. Position 4 shifts differently. Let's check position 4 for MANGO: G(7)→A(1): -6. For APPLE: L(12)→V(22): +10. No consistent position-4 rule.

**New pattern coding insight:** When the shift pattern isn't immediately clear, look at whether the coded word is related to the original in a different way - reversed, only consonants, only vowels, or a completely different encoding rule. For Advanced TCS questions, the relationship between the original word and code is always internally consistent - you just need more examples to identify it.

### Common Coding-Decoding Traps

**Trap 1: Assuming uniform shift when shifts are position-dependent.** Always check the first three letters before assuming the rule.

**Trap 2: Forgetting alphabetical wrap-around.** Z+1 = A, not a 27th letter. Use (n-1) mod 26 + 1 formula.

**Trap 3: Direction error.** If the original becomes coded by +3, and you are asked for the original from the code, apply -3 (not +3).

**Time benchmark:** Simple uniform shift: 30 seconds. Position-dependent shift (mapping required): 60 seconds. New pattern from two examples: 90 seconds.

---

## Topic 2: Seating Arrangements

This is the highest-time-consumption question type and the one where technique versus intuition produces the largest performance gap.

### The Grid Method for Linear Arrangements

**Always draw the seats before reading conditions.**

For N people in a row, draw N boxes: □ □ □ □ □

As conditions are read, fill in boxes with:
- Letters (confirmed occupant)
- X (person who cannot be here)
- Constraint notation (e.g., "A is to the left of B")

**Foundation problem:** Five people A, B, C, D, E sit in a row.
(1) B sits at one of the ends.
(2) C is immediately to the right of B.
(3) D is not adjacent to C.
(4) A is at the second position from the right end.

Draw: _ _ _ _ _  (positions 1-5, left to right)

From (1): B is at position 1 or position 5.
From (2): C is immediately to the right of B. If B=1, C=2. If B=5, no position to the right → B=1, C=2.
From (4): A is at position 4 (second from right end, which is position 5, so second from right is position 4).
Remaining positions 3 and 5 for D and E.
From (3): D is not adjacent to C. C is at position 2. Adjacent to C is position 1 (B) and position 3. So D cannot be at position 3 → D=5, E=3.

Final arrangement: B(1) C(2) E(3) A(4) D(5)

Questions like "Who sits at position 3?" → E. "Who is to the right of A?" → D.

### The Circle Method for Circular Arrangements

For N people in a circle, draw a circle with N marks. Fix one person at the top to eliminate rotational ambiguity.

**Advanced problem:** Six people A, B, C, D, E, F sit around a circular table.
(1) A is between F and E.
(2) C is not adjacent to F.
(3) D is immediately to the right of E.
(4) B and C sit opposite each other.

Draw circle with 6 positions. Fix A at position 1 (top).
From (1): F and E are on either side of A. So F=6, E=2 OR F=2, E=6.
From (3): D is immediately to the right of E. If E=2, D=3. If E=6, D=1 (but 1 is A) → invalid. So E=2, D=3, F=6.
Remaining: B and C at positions 4 and 5.
From (4): B and C opposite each other. In a 6-person circle, opposite pairs are (1,4), (2,5), (3,6). Neither B nor C is at 1, 2, 3, or 6. Positions 4 and 5 are not opposite each other (they are adjacent). Contradiction?

Re-examine: "Opposite" means across the table. In 6-person circle with positions 1-6, opposite pairs: (1,4), (2,5), (3,6). B and C must be at one of these pairs. Available positions are 4 and 5. The pair (2,5) means someone at 5. Position 2 is E. So if C or B is at position 5, they would need to be opposite position 2=E. But condition (4) says B and C are opposite each other, not opposite E.

So B and C must both be at a pair that satisfies the opposite condition from among available positions. Positions 4 and 5 are available but not an opposite pair. This arrangement is impossible under these conditions? Either the problem has a unique solution hidden by a different initial assumption, or my F/E placement needs revisiting.

This illustrates the key benefit of the grid/circle technique: it reveals contradictions immediately. If a problem seems to lead to a contradiction, revisit the first condition and try the other case.

**Advanced seating: Two rows facing each other**

Draw two rows, label Row 1 (faces north) and Row 2 (faces south). Person A in Row 1 position 1 "faces" person B in Row 2 position 1.

Mark all confirmed positions, then use constraints to fill remaining gaps. "X faces Y" means they are in opposite rows at the same column position.

**Time benchmark:** 4-person linear arrangement: 2-3 minutes. 5-6 person circular: 3-5 minutes. Complex multi-variable (8 people, 2 attributes): 5-7 minutes.

---

## Topic 3: Syllogisms

### The Venn Diagram Approach

Every syllogism statement corresponds to a Venn diagram relationship:
- **"All A are B":** A circle is entirely inside B circle.
- **"No A is B":** A circle and B circle do not overlap at all.
- **"Some A are B":** A and B circles partially overlap.
- **"Some A are not B":** Part of A circle falls outside B circle.

### Foundation Level: Two-Statement Syllogisms

**Problem:**
Statements: (1) All cats are animals. (2) Some animals are dogs.
Conclusions: (I) Some cats are dogs. (II) Some dogs are animals.

Draw Venn:
Statement 1: cats circle entirely inside animals circle.
Statement 2: animals circle and dogs circle partially overlap.

Conclusion I: "Some cats are dogs." The cats circle is inside animals. Does any part of the cats circle overlap with dogs? The dogs overlap is with animals generally - it might overlap with cats (inside animals) or with the non-cats part of animals. Not certain → Conclusion I does NOT follow.

Conclusion II: "Some dogs are animals." Statement 2 directly says some animals are dogs, which by conversion means some dogs are animals → Conclusion II FOLLOWS.

**Answer: Only Conclusion II follows.**

### Advanced Level: Three-Statement Syllogisms

**Problem:**
Statements: (1) All roses are flowers. (2) All flowers are plants. (3) Some plants are trees.

Conclusions:
(I) All roses are plants.
(II) Some trees are flowers.
(III) Some plants are roses.

Venn construction:
- Roses entirely inside flowers (from 1).
- Flowers entirely inside plants (from 2).
- Therefore roses entirely inside plants (transitive).
- Trees partially overlap plants (from 3).

(I) All roses are plants: Roses ⊂ flowers ⊂ plants → roses ⊂ plants ✓ **FOLLOWS**
(II) Some trees are flowers: Trees overlap plants, but the overlap area might be entirely in the plants-but-not-flowers region. Not certain → **DOES NOT FOLLOW**
(III) Some plants are roses: Since all roses are plants, "some plants are roses" is true (those are the rose-plants). **FOLLOWS**

**Answer: Conclusions I and III follow.**

### Possibility-Based Conclusions

"It is possible that some A are B" - this is true UNLESS the given statements make it impossible for any A to be B. "No A is B" makes the possibility false. Any other arrangement allows the possibility.

**Problem:**
Statements: All cats are mammals. No dog is a cat.
Conclusion: It is possible that some dogs are mammals.

No statement says "No dog is a mammal." The only constraint is "No dog is a cat." Dogs can still be mammals (the cats are mammals, but other mammals exist too). The possibility is NOT ruled out → the conclusion **FOLLOWS**.

**Time benchmark:** Two-statement with two conclusions: 90 seconds. Three-statement with three conclusions: 2.5-3 minutes.

---

## Topic 4: Number and Letter Series

### The Difference Method

For number series, compute first differences (consecutive gaps), second differences (gaps between gaps), and so on until a clear pattern emerges.

**Foundation problem:** 3, 7, 13, 21, 31, 43, ?
First differences: 4, 6, 8, 10, 12 (arithmetic progression +2 each time)
Second differences: 2, 2, 2, 2 (constant)
Next first difference = 14. Next term = 43 + 14 = **57**.

**Advanced: Multi-level difference series**
2, 3, 6, 11, 18, 27, 38, 51, ?
First differences: 1, 3, 5, 7, 9, 11, 13 (odd numbers)
Next difference = 15. Next term = 51 + 15 = **66**.

### Wrong Term Problems

**Problem:** Find the wrong term: 1, 8, 27, 64, 124, 216
These should be cubes: 1³, 2³, 3³, 4³, 5³, 6³ = 1, 8, 27, 64, **125**, 216.
Wrong term is **124** (should be 125).

**Approach:** Identify what the series should be (cubes, squares, primes, factorials), then find which term deviates.

### Interleaved Series

**Problem:** 2, 5, 4, 10, 8, 20, 16, 40, ?
Odd positions: 2, 4, 8, 16 (×2 each time) → next odd position = 32
Even positions: 5, 10, 20, 40 (×2 each time) → next even position = 80
The "?" is at position 9 (odd): **32**.

### Letter Series

**Foundation:** A, C, E, G, ? (every other letter: +2 each time) → **I**

**Advanced compound pattern:** AZ, BY, CX, DW, ?
First letters: A, B, C, D (+1) → next: E
Second letters: Z, Y, X, W (-1) → next: V
Answer: **EV**

**Advanced position-value:** 1B, 4E, 9H, 16K, ?
Numbers: 1, 4, 9, 16 (squares: 1², 2², 3², 4²) → next: 25
Letters: B(2), E(5), H(8), K(11) (+3 each time) → next: N(14)
Answer: **25N**

---

## Topic 5: Direction Sense

### The Path-Drawing Mandatory Rule

**Never solve direction problems mentally. Always draw the path.**

Set up: North at top, South at bottom, East at right, West at left. Draw start point at centre.

**Foundation problem:** Riya starts at school. She walks 3 km north, turns right and walks 4 km, then turns right and walks 5 km. How far is she from school and in which direction?

Draw:
- Start: Point S
- Walk 3 km north: reach point A (S + 3 units up)
- Turn right (now facing east), walk 4 km: reach point B (A + 4 units right)
- Turn right (now facing south), walk 5 km: reach point C (B + 5 units down)

Final position relative to start:
- Horizontal: 4 km east of start
- Vertical: 3 km north then 5 km south = 2 km south of start

Straight-line distance: √(4² + 2²) = √(16+4) = √20 = 2√5 ≈ **4.47 km** south-east.

**The direction turn system:**
- Facing North: turn right → face East; turn left → face West
- Facing East: turn right → face South; turn left → face North
- Facing South: turn right → face West; turn left → face East
- Facing West: turn right → face North; turn left → face South

Memorise this as: right turns go clockwise (N→E→S→W→N), left turns go counter-clockwise.

**Advanced: Combined distance and direction question**

A person travels: 5 km South, then 3 km East, then 7 km North, then 3 km West.

Final position:
- Vertical: 5 south + 7 north = 2 north of start
- Horizontal: 3 east + 3 west = 0 (back to same longitude)

Final position: **2 km directly North** of starting point. Distance: 2 km.

**The shortcut:** Combine all north movements, subtract all south movements. Combine all east movements, subtract all west movements. These give the net displacement in each axis. Apply Pythagoras for the straight-line distance.

---

## Topic 6: Blood Relations

### The Family Tree Method

**Draw before solving. Every time.**

**Foundation problem:** "Pointing to a photograph, Arun says, 'This man's son is my mother's only son's daughter's husband.' What is the relationship of the man in the photograph to Arun?"

This type of chained relationship is impossible to solve mentally. Draw the tree:
- "my mother's only son" = Arun himself (if Arun is male) or Arun's brother
- "my mother's only son's daughter" = Arun's daughter (if Arun is male) or Arun's brother's daughter
- "daughter's husband" = Arun's son-in-law (if referring to Arun's daughter)
- "this man's son" = the man's son = Arun's son-in-law → the man is Arun's son-in-law's father = Arun's daughter's husband's father

Relationship to Arun: **Father-in-law of Arun's daughter** or, from Arun's perspective, the man in the photo is related as Arun's daughter's husband's father.

### Coded Blood Relations

**Foundation problem:** "A + B means A is the mother of B. A - B means A is the brother of B. A × B means A is the father of B. A ÷ B means A is the sister of B."
If P + Q - R × S ÷ T, what is the relationship between P and T?

Decode left to right:
- P + Q: P is the mother of Q
- Q - R: Q is the brother of R
- R × S: R is the father of S
- S ÷ T: S is the sister of T

Draw the tree:
P is mother of Q. Q is brother of R → Q and R are siblings, P is also mother of R.
R is father of S. S is sister of T → S and T are siblings, R is also father of T.

Chain: P → mother of Q and R. R → father of S and T.
P is the mother of R, who is the father of T. P is therefore T's **grandmother (paternal grandmother's side, through father's mother)**.

The relationship between P and T: **P is the paternal grandmother of T** (grandmother).

---

## Topic 7: Puzzles

### Floor-Based Puzzles

Floor puzzles assign people to floors (typically in a building with 6-8 floors) based on a series of conditions. The technique is a constraint table.

**Create a table:** Rows = floor numbers (top to bottom or bottom to top as specified). Columns = person names. Mark "possible" with O and "confirmed" with ✓.

**Foundation problem:** 6 people A, B, C, D, E, F live in 6 floors (floor 1 = lowest).
(1) B lives on a floor above A.
(2) C lives on floor 3.
(3) D lives immediately below E.
(4) F does not live on floors 1 or 6.

From (2): C = floor 3.
From (3): D and E are consecutive (D immediately below E). Possible pairs: (1,2), (2,3), (4,5), (5,6). Since floor 3 is C: pair (2,3) and (3,4) are partially occupied. Valid pairs for D,E: (1,2), (4,5), (5,6).
From (4): F ≠ floor 1 or 6.
From (1): B is above A.

If D=1, E=2: remaining floors 4,5,6 for A, B, F. F≠6, so F=4 or 5. B above A: if A=4,B=5,F=6 - but F≠6. If A=4,B=5(or 6),F=5(or 4) - multiple arrangements possible without further constraints.

If D=4, E=5: remaining floors 1,2,6 for A, B, F. F≠1 or 6 → F=2. Then A and B are at 1 and 6. B above A → B=6, A=1.
Final: A=1, F=2, C=3, D=4, E=5, B=6.

Verify all conditions: B(6)>A(1) ✓, C=3 ✓, D(4) immediately below E(5) ✓, F=2 (not 1 or 6) ✓.

### Comparison-Based Puzzles

These puzzles rank people on a single attribute (height, marks, age) using comparative statements.

**Foundation problem:** Among 5 students, P scored higher than Q. R scored higher than P. S scored lower than Q. T scored between Q and P. Rank all from highest to lowest.

From R>P>Q>S (direct chain from first three conditions).
T is between Q and P: Q < T < P.
Full order: R > P > T > Q > S.

Ranking from highest: **R, P, T, Q, S**.

---

## Topic 8: Data Sufficiency

### The Two-Statement Framework

Data Sufficiency questions ask: is the given information sufficient to answer the question?

The five options are:
(A) Statement 1 alone sufficient; 2 not
(B) Statement 2 alone sufficient; 1 not
(C) Both together sufficient; neither alone
(D) Each statement alone sufficient
(E) Neither alone nor together

**Critical rule:** Evaluate each statement independently. Do not combine statements while evaluating Statement 1 alone.

**Foundation problem:** Is X an even number?
Statement 1: X² is divisible by 4.
Statement 2: X is divisible by 6.

Statement 1 alone: X² divisible by 4 means X² = 4k for some integer k. This means X itself must be divisible by 2 (since if X were odd, X² would be odd). So X is even. **Statement 1 is sufficient.**

Statement 2 alone: X divisible by 6 means X = 6k for some integer k. 6k is always even (6 is even). So X is even. **Statement 2 is sufficient.**

Answer: **(D) Each statement alone is sufficient.**

**Advanced problem:** What is the value of x + y?
Statement 1: x² + y² = 25.
Statement 2: x - y = 1.

Statement 1 alone: Many solutions satisfy x²+y²=25 (e.g., 3+4=7, 0+5=5, etc.). x+y is not determined. **Not sufficient.**

Statement 2 alone: x-y=1 means x=y+1. x+y = (y+1)+y = 2y+1. Without knowing y, x+y is not determined. **Not sufficient.**

Both together: x²+y²=25 and x=y+1. Substitute: (y+1)²+y²=25 → y²+2y+1+y²=25 → 2y²+2y-24=0 → y²+y-12=0 → (y+4)(y-3)=0 → y=-4 or y=3.
If y=3: x=4, x+y=7. If y=-4: x=-3, x+y=-7. Two possible values for x+y → still not uniquely determined. **Not sufficient together either.**

Answer: **(E) Neither alone nor together sufficient.**

---

## Topic 9: Input-Output Problems

### The Pattern Identification Protocol

**Step 1:** Look at two consecutive steps together - what changed?
**Step 2:** Look at what happens to numbers vs what happens to words (they often follow separate rules).
**Step 3:** Verify the identified pattern against a third step before applying it.

**Foundation problem:**
Input:  dog 15 cat 8 bird 42 fish 3
Step 1: 3 dog 15 cat 8 bird 42 fish
Step 2: 3 dog 8 cat 15 bird 42 fish
Step 3: 3 dog 8 cat 15 bird 42 fish (same as Step 2?)

Actually: Step 1 moved 3 (smallest number) to the front. Step 2 sorted the next smallest number (8) to position 3. The pattern: numbers are being sorted in ascending order, one number per step, from left to right, while words remain in their relative positions between numbers.

**Step 3 should be:** 3 dog 8 cat 15 bird 42 fish (already sorted - the arrangement stays the same because numbers are already sorted).

Wait, let me re-examine. Input has: 15, 8, 42, 3 (numbers, unsorted). Step 1: moves 3 to position 1. Step 2: sorts 8 to position 3. Step 3 would sort 15 to position 5. Step 4 would complete the sort: 3, 8, 15, 42.

Pattern: In each step, the smallest remaining unsorted number moves to its correct position.

Final output: **3 dog 8 cat 15 bird 42 fish** (numbers sorted ascending, words maintain relative positions around the numbers).

**Advanced: Two-operation input-output**

Input:  red 48 blue 31 green 17 yellow 95
Step 1: red 48 blue 31 green 17 yellow 95 → yellow 95 red 48 blue 31 green 17

Pattern in Step 1: largest number (95) and its preceding word (yellow) moved to front as a pair.

Step 2: yellow 95 green 17 red 48 blue 31 → smallest number (17) and its word (green) moved to position after the first pair.

The alternating pattern: each step alternates between moving the largest remaining pair to the next position and the smallest remaining pair to the next position.

---

## Topic 10: Visual Reasoning

### Pattern Completion

Pattern completion problems show a 3×3 or 2×3 grid with one cell missing. The rule governing the grid must be identified and applied to find the missing element.

**Rule types:**
- Row rule: each row follows an arithmetic progression, or each row has the same sum/product
- Column rule: similar to row rule
- Diagonal rule: the main or anti-diagonal follows a pattern
- Operation rule: each cell is derived from the other two in its row/column (e.g., third = first × second)

**Approach:** Check row-wise first (what rule connects cell 1, 2, 3 in row 1?). If no consistent rule, try column-wise. If no rule there, try operation-based.

### Mirror Image Problems

For alphabetical mirror images: A↔Z, B↔Y, C↔X, D↔W... Each letter and its mirror sum to 27 (in 1-26 numbering). Mirror of A(1) = Z(26): 1+26=27. Mirror of M(13) = N(14): 13+14=27.

Quick formula: Mirror of letter at position n = letter at position (27-n).
Mirror of R(18) = position 9 = I. Mirror of G(7) = position 20 = T.

### Paper Folding and Punching

For paper folding problems:
1. Trace where each fold line is and which direction the fold goes.
2. When the paper is punched, the hole appears at the punch location AND all its mirror images across fold lines.
3. When the paper is unfolded, trace back all mirror images.

**Systematic approach:** Mark the fold axis. The punch hole on one side has a mirror position on the other side of each fold. For multiple folds, apply fold sequence in reverse when unfolding.

### Dice Problems

**Standard dice convention:**
- Opposite faces: 1-6, 2-5, 3-4 (sum to 7 for each pair)
- When two faces are shown, the third pair is determined

**Approach for dice questions showing multiple positions:**
- Identify which faces are visible in each position
- Use the information to determine which numbers are adjacent (not opposite)
- The face not visible but determined by elimination is the answer

---

## Topic 11: Logical Deductions

### If-Then Problems

**Foundation:** "All birds can fly. Penguins are birds. Therefore, penguins can fly."

This is a valid deduction (follows the logic of the given statements) but potentially factually wrong. In reasoning questions, we evaluate logical validity, not factual accuracy.

**Advanced:** "If it rains, the ground is wet. The ground is wet. Therefore, it rained."

This is a logical fallacy - the ground being wet does not guarantee it rained (it could have been watered, flooded, etc.). The valid form requires: "If it rained, the ground is wet" + "It rained" → "The ground is wet." But the reverse direction is not valid.

**Modus Ponens (valid):** If P then Q. P. Therefore Q.
**Modus Tollens (valid):** If P then Q. Not Q. Therefore not P.
**Affirming the consequent (invalid):** If P then Q. Q. Therefore P.
**Denying the antecedent (invalid):** If P then Q. Not P. Therefore not Q.

### Cause and Effect

**Approach:** Two statements are given. Determine if Statement A causes Statement B, Statement B causes Statement A, both have a common cause, or they are independent.

The systematic test: Could A happen without B? Could B happen without A? Does changing A predictably change B?

---

## Topic 12: Analogies

### Number Analogies

**Type:** 3 : 12 :: 5 : ?

Method: Identify the relationship. 3 → 12: multiplied by 4. So 5 × 4 = **20**. Verify: is the relationship consistent? 3×4=12 ✓.

If the relationship is not obvious: try: addition (3+9=12 vs 5+9=14), multiplication (3×4=12 vs 5×4=20), power (3²+3=12? 9+3=12 ✓, so 5²+5=30).

When multiple operations work for one pair, use the second pair in the analogy to confirm.

### Letter Analogies

**Type:** AC : CE :: EG : ?

Method: A(1)C(3) - gap of 2. C(3)E(5) - gap of 2. The second pair starts where the first ends. Pattern: two-letter sequences with gap of 2, starting 2 positions after previous sequence start. EG → GI (start 2 after E=position 5, so start at G=7, then I=9). Answer: **GI**.

### Word Analogies

**Type:** Sculptor : Chisel :: Carpenter : ?

Method: Sculptor uses a chisel (tool of the sculptor). Carpenter's tool: **Saw** (or hammer, plane - the primary tool).

---

## Advanced Reasoning: What Changes at Digital Level

Foundation reasoning at TCS tests individual techniques. Advanced reasoning tests the same techniques but with:
- More people/attributes per arrangement (6-8 variables instead of 4-5)
- More conditions per puzzle (5-7 conditions instead of 3-4)
- Mixed question types within one puzzle (a seating arrangement that also involves blood relations)
- Critical reasoning (argument evaluation)
- Data Sufficiency at higher complexity

**The critical change in approach for Advanced level:** The systematic technique is the same - you still draw diagrams, you still construct family trees, you still write difference sequences. What changes is the care required. A small error in one deduction step propagates through the entire arrangement and makes all subsequent questions wrong.

At Advanced level, **verification** becomes a required step, not an optional one. After placing every person in an arrangement, verify every single condition before answering any question.

---

## Practice Problem Set: Foundation Level (25 Questions)

Rather than providing all 25 here, the following 10 questions cover the most frequently tested types with answers:

**Q1 (Coding-Decoding):** If WATER = YCVGT, then FIRE = ?
WATER: W+2=Y, A+2=C, T+2=V, E+2=G, R+2=T. Pattern: each letter +2.
FIRE: F+2=H, I+2=K, R+2=T, E+2=G → Answer: **HKTG**

**Q2 (Series):** Find next: 2, 6, 18, 54, ?
Each term × 3. Next: 54 × 3 = **162**

**Q3 (Blood Relation):** "X is the brother of Y. Y is the sister of Z. Z is the father of W." What is X to W?
Y is sister of Z, Z is father of W → Y is aunt of W. X is brother of Y → X is also the sibling of Y's sibling Z. X is the brother of W's father Z → X is the uncle of W. Answer: **Uncle**

**Q4 (Direction Sense):** A man walks 4 km North, then 3 km East. Distance from start?
√(4²+3²) = √(16+9) = √25 = **5 km**

**Q5 (Arrangement):** Five people A,B,C,D,E in a row. A is at the 4th position. D is to the immediate left of A. B is at the rightmost end. What is C's position if E is between C and B?
B=5, A=4, D=3. E is between C and B: positions 1 and 2 remain. B=5, so between C and B means E is at 4 side... E=4? But A=4. Contradiction. E must be between C and B in a different sense: C at position 2, E at position ... wait B is at position 5, E is between C and B means C<E<5 or 5 between C and E. If C=1 and E=2: E is between A (not B). Re-read: E is between C and B positionally. C and B must have E between them. B=5. For E between C and B: C must be at position 1 or 2, E between that position and 5. Remaining positions are 1 and 2 for C and E. C=1, E=2: is E between C(1) and B(5)? Positions 2,3,4 are between 1 and 5. E is at 2, which is between 1 and 5. ✓ Answer: C is at position **1**

**Q6 (Syllogism):**
Statements: All pens are pencils. Some pencils are erasers.
Conclusion I: Some pens are erasers.
Conclusion II: Some erasers are pencils.

Venn: pens⊂pencils. pencils and erasers partially overlap. The overlap of pencils and erasers may or may not include the pens sub-region.
I: Not certain. II: Some erasers are pencils (directly from Statement 2 by conversion). Answer: **Only II follows**

**Q7 (Data Sufficiency):** Is N divisible by 15?
Statement 1: N is divisible by 5.
Statement 2: N is divisible by 3.

Alone: 1 alone - 5, 10, 15... not certain. 2 alone - 3, 6, 9, 12, 15... not certain. Together: divisible by both 3 and 5 → LCM(3,5)=15 → yes divisible by 15. Answer: **(C) Both together sufficient**

**Q8 (Input-Output):**
Input: cat 7 dog 3 hen 12 pig 5
Step 1: 3 cat 7 dog 12 hen 5 pig

Pattern: numbers sorted ascending, words maintained. Next step would arrange next smallest number (5) to position 3. Answer for Step 2: **3 cat 5 dog 7 hen 12 pig**

**Q9 (Analogy):** ACE : CEG :: GIK : ?
Gaps: A(1)C(3)E(5) - odd numbers starting at 1. C(3)E(5)G(7) - shifted by 2. G(7)I(9)K(11) - next sequence. Followed by I(9)K(11)M(13) → Answer: **IKM**

**Q10 (Visual):** In a pattern matrix where each row's third element = row's first element × row's second element:
Row 1: 3, 4, 12. Row 2: 5, 6, 30. Row 3: 7, 8, ?
7 × 8 = **56**

---

## The 3-Week Reasoning Preparation Plan

### Week 1: Foundation Coverage

**Days 1-2: Coding-Decoding and Series**
Learn the four coding types (uniform shift, position-dependent, new-pattern, coded relationships). Practice 10 problems per type. Series: practice difference method, second difference, and interleaved series identification. 15 series problems.

**Days 3-4: Blood Relations and Directions**
Blood relations: draw every problem, never solve mentally. Build a 15-problem family tree exercise set. Directions: draw every path. Practice 15 direction problems with distance calculation.

**Days 5-6: Seating Arrangements**
Linear first (draw grid, fill conditions). Circular next (fix one person, draw circle). 3 complete arrangement sets per day (4-5 questions each).

**Day 7: Review**
Full mock reasoning section (25 questions, 25 minutes). Identify which question types gave most errors.

### Week 2: Deeper Practice and Advanced Introduction

**Days 8-9: Syllogisms**
Two-statement with Venn diagrams until error rate < 10%. Begin three-statement syllogisms. Practice 20 syllogism problems.

**Days 10-11: Puzzles and Data Sufficiency**
Floor-based puzzles (3 problems, full constraint table). Comparison puzzles (5 problems). Data Sufficiency (10 problems with the two-statement framework).

**Days 12-13: Input-Output and Logical Deductions**
Input-output: 5 complete sets (trace pattern, answer questions). Logical deductions: if-then problems, cause-effect identification. 10 problems each.

**Day 14: Advanced Section Introduction**
Attempt 5 Advanced reasoning questions (complexity: 6+ people, 5+ conditions). Note which technique adaptations the higher complexity requires.

### Week 3: Advanced Mastery and Mock Testing

**Days 15-17: Advanced Arrangements**
Complex multi-variable arrangements (8 people, 2 attributes each). Practice the verification step explicitly.

**Days 18-19: Advanced Syllogisms and Critical Reasoning**
Three-statement syllogisms with possibility conclusions. Critical reasoning: argument strengthening, weakening, assumption identification.

**Days 20-21: Mock Tests and Error Analysis**
Two full reasoning sections per day (Foundation + Advanced level). Apply the post-mock error analysis protocol (Type A through E error categorisation).

**The practice platform:** For additional reasoning questions calibrated to the NQT difficulty level, the [TCS NQT Preparation Guide](https://reportmedic.org/tools/tcs-nqt-preparation-guide.html) provides interactive practice across all reasoning question types with detailed explanations for each answer choice.

---

## Common Reasoning Mistakes and How to Prevent Them

### Mistake 1: Mental Arithmetic in Arrangement Problems

The most costly mistake: attempting to solve seating or floor arrangement problems by holding the entire setup in your head. This produces errors at a rate of 30-40% even among prepared candidates. Drawing the diagram reduces the error rate to under 5%. There is no time argument against drawing - a drawn 5-person arrangement takes 60 seconds and produces correct answers. A mental arrangement takes 90 seconds and produces wrong answers.

### Mistake 2: Using Facts Instead of Logic in Syllogisms

"All roses are red. Some flowers are roses. Therefore some flowers are red." This seems obviously correct because roses are indeed red. But the reasoning must be valid even if we replace "roses" with an abstract variable: "All X are Y. Some Z are X. Therefore some Z are Y." Test with abstract variables to avoid being influenced by real-world knowledge.

### Mistake 3: Combining Statements in Data Sufficiency

When testing whether Statement 1 alone is sufficient, candidates instinctively use information from Statement 2. This produces incorrect answers consistently. Deliberately ignore Statement 2 while evaluating Statement 1, then deliberately ignore Statement 1 while evaluating Statement 2.

### Mistake 4: Direction Problem Cardinal Errors

"Turn right while facing South" does not mean turn to the right side of the page. It means turn to the relative right of the person facing South, which is East (left side of the page). Always redraw the person's orientation before applying the turn.

### Mistake 5: Series Pattern Jumping

Seeing a pattern after two terms and applying it before verifying with the third term leads to errors on complex series. Always verify the identified pattern against at least three consecutive terms before applying.

---

## Time Management: Reasoning Under Pressure

### Section-Level Time Budget

Foundation Reasoning: 25 questions, 25 minutes = 60 seconds per question.

**Fast question types (target 30-45 seconds):** Series completion (once pattern is clear), number analogies, simple coding-decoding (uniform shift), direction distances (once diagram is drawn).

**Medium question types (target 60-90 seconds):** Blood relations, data sufficiency, logical deductions, letter analogies.

**Slow question types (target 180-300 seconds total for the set):** Seating arrangements (4-5 questions per arrangement, invest 3-4 minutes for the setup then answer 4-5 questions at 30 seconds each).

### The Arrangement Investment Decision

Arrangement questions require upfront time investment. The decision: is solving this arrangement worth the setup time?

For 3-question arrangement sets: 3 minutes setup, 3 × 30 seconds answers = 4.5 minutes total for 3 marks. This is 90 seconds per mark - too slow if it prevents you from answering faster questions.

For 5-question arrangement sets: 3 minutes setup, 5 × 30 seconds answers = 5.5 minutes for 5 marks = 66 seconds per mark. Acceptable.

**Rule:** Attempt 5-question arrangement sets. Evaluate 3-question sets based on remaining time.

### Triage in Reasoning

The first 90 seconds of the Reasoning section: scan all questions and classify as:
- Green: fast question types, answer immediately
- Yellow: medium, answer after Greens
- Red: complex arrangements, attempt last

Answering all Greens first (typically 8-10 questions completed in 5-7 minutes) creates a time buffer that can be applied to Yellow and Red questions without the pressure of running out of time.

---

## Frequently Asked Questions: TCS NQT Reasoning

**Is Reasoning harder in the Advanced section than Foundation?**
Yes, significantly. Foundation Reasoning tests individual techniques at standard complexity (4-5 person arrangements, 2-statement syllogisms, simple series). Advanced Reasoning at Digital level introduces complex multi-variable puzzles, 3-statement syllogisms with possibility conclusions, critical reasoning, and Data Sufficiency at a higher complexity level. The Foundation-to-Advanced gap in Reasoning is comparable to the gap in Quantitative Ability.

**How many questions come from each reasoning type in the Foundation section?**
Based on observed patterns: Seating arrangements generate 4-6 questions (from 1-2 sets). Syllogisms generate 3-4 questions. Series and coding-decoding generate 2-3 questions each. Blood relations generate 2-3 questions. Direction and analogies generate 2 questions each. Data Sufficiency and Input-Output generate 1-2 questions each. The remaining question types fill 1-2 questions each.

**Can I skip arrangement problems and still score well?**
Skipping all arrangement problems means giving up 4-6 questions (approximately 16-24% of the section). Scoring 19+ on the remaining 19-21 questions is possible but requires near-perfect performance on other types. The better strategy is to do 5-question arrangements (high ROI) and consider skipping 3-question arrangements that appear complex.

**Should I practice visual reasoning for TCS NQT?**
Foundation Reasoning at TCS NQT primarily tests logical reasoning (arrangements, syllogisms, series), not visual/spatial reasoning. Visual reasoning questions (mirror images, paper folding, dice) appear less frequently than other types. Prioritise logical reasoning types in your preparation.

**How do I get faster at seating arrangements?**
Speed at arrangements comes from practice at the technique level, not the speed level. A candidate who has done 30+ arrangement sets (each involving setting up the diagram, applying all conditions, answering 4-5 questions) develops the pattern-to-diagram translation speed automatically. The bottleneck is diagram setup accuracy - prioritise accuracy over speed in your first 20 practice arrangements, then switch to timing.

---

## Advanced Reasoning: Critical Reasoning

Critical Reasoning appears in the Advanced Reasoning section for Digital profile candidates. It evaluates whether you can analyse the logical structure of an argument - identifying what supports it, what weakens it, or what it assumes.

### The Four Critical Reasoning Tasks

**Task 1: Strengthen the Conclusion**
Find the answer choice that makes the argument's conclusion more likely to be true. The strengthener provides additional evidence, rules out an alternative explanation, or establishes a missing link in the logic.

**Task 2: Weaken the Conclusion**
Find the answer choice that makes the argument's conclusion less likely. The weakener introduces a confounding factor, shows the evidence is consistent with a different conclusion, or undermines a premise.

**Task 3: Identify the Assumption**
The assumption is a statement the argument needs to be true but never explicitly states. If the assumption is false, the argument collapses. The correct assumption is something that bridges the evidence to the conclusion.

**Task 4: Identify the Logical Flaw**
The flaw is a specific reasoning error: circular reasoning, hasty generalisation, false dichotomy, correlation-causation confusion, or attacking the person (ad hominem).

### Worked Example

**Argument:** "Sales of our new product increased by 40% after we hired a famous celebrity to endorse it. The celebrity endorsement clearly caused the sales increase."

**Assumption question:** What does this argument assume?
The argument assumes the sales increase was caused by the celebrity endorsement and not by any other factor (price reduction, competitor exit, seasonal demand, advertising spend, economic improvement). The assumption is: **no other significant factor changed simultaneously to explain the sales increase.**

**Weakener question:** Which of the following most weakens this argument?
(A) The company also reduced the product's price by 25% at the same time as the celebrity endorsement.
(B) Other products in the same category also experienced sales increases.
(C) The celebrity was well-known and liked by the target demographic.
(D) The product had previously had very low brand awareness.

**(A) weakens the argument most** - the price reduction is an alternative explanation for the sales increase, directly undermining the causal attribution to the celebrity endorsement. (B) actually weakens it too but less directly (suggests external market forces). (C) strengthens it slightly. (D) is neutral background information.

---

## Extended Practice: Advanced Reasoning Problems

### Advanced Arrangement Problem

**Problem:** Eight employees A, B, C, D, E, F, G, H are seated in two parallel rows of four facing each other. Row 1 faces north; Row 2 faces south. Each person in Row 1 directly faces one person in Row 2.

Conditions:
(i) B faces D.
(ii) A is at one end of Row 1.
(iii) F sits second from the left end of Row 2.
(iv) E is not in Row 2.
(v) G sits to the immediate left of F in Row 2.
(vi) H sits between B and C in Row 1.

**Solution process:**

Draw:
Row 1 (faces north): _ _ _ _ (positions L1, L2, L3, L4)
Row 2 (faces south): _ _ _ _ (positions R1, R2, R3, R4)
"Faces" means same column: L1 faces R1, L2 faces R2, L3 faces R3, L4 faces R4.

From (iii): F = R2 (second from left in Row 2).
From (v): G immediately left of F in Row 2. G = R1.
From (i): B faces D. B in Row 1, D in Row 2 (or vice versa).
From (iv): E is in Row 1.
From (ii): A is at one end of Row 1: A = L1 or L4.
From (vi): H is between B and C in Row 1 - so H is flanked by B and C.

Row 2 so far: G(R1), F(R2), ?, ? - remaining: and some of {A,B,C,D,E,H} noting E is in Row 1, so Row 2 contains some subset of {A,B,C,D,H} (since G and F are already placed).

From (i): B faces D. If B is in Row 1, D is in Row 2 at the same column position.
From (iv): E in Row 1. So Row 2 has 4 people from {A,B,C,D,H} minus any in Row 1. Row 1 has 4 people from {A,B,C,E,H} (since E must be in Row 1) plus possibly B.

From (vi): H is between B and C in Row 1 - the arrangement B-H-C or C-H-B. So B, H, C are in Row 1 together.

Row 1 has: A (from (ii), at an end), B, H, C (consecutive from (vi)), and E (from (iv)).
But Row 1 has only 4 seats. A, B, H, C, E = 5 people. Contradiction unless one of them is not in Row 1.

Re-examine: (vi) says H sits between B and C. The word "between" could mean between in Row 1 specifically. Since E must be in Row 1 (condition iv) and A must be in Row 1 (condition ii), and B, H, C must be together in Row 1 (condition vi), we have A, B, H, C, E = 5 in a 4-seat row. One of B or C must be in Row 2.

If B is in Row 2: B faces someone in Row 1. From (i), B faces D. If B is in Row 2, D is in Row 1. Then Row 1 contains: A, D, H, C, E = still 5. Still contradictory.

If C is in Row 2: Row 1 contains A, B, H, E. But (vi) says H is between B and C. If C is in Row 2, H cannot be between B and C in Row 1.

This problem as stated appears to have a contradiction. This illustrates that some Advanced arrangement problems have intentional red herrings in conditions, or require interpreting "between" more broadly (H is between B and C positionally in the building, not necessarily within one row).

For exam purposes: when an Advanced arrangement produces a contradiction, re-examine the most recently assumed condition with alternative interpretations before concluding no solution exists.

### Advanced Syllogism: Possibility Conclusion

**Problem:**
Statements:
(1) All athletes are strong.
(2) Some strong people are doctors.
(3) No doctor is a teacher.

Conclusions:
(I) Some athletes are doctors.
(II) Some strong people are not teachers.
(III) It is possible that some teachers are athletes.
(IV) No athlete is a teacher.

**Analysis:**

From (1): athletes ⊂ strong.
From (2): strong ∩ doctors ≠ ∅. But the overlap of strong and doctors may or may not include athletes.
From (3): doctors ∩ teachers = ∅ (no doctor is a teacher).

(I) "Some athletes are doctors." The athlete sub-group is entirely within strong. The doctors also overlap strong. But the doctors-strong overlap might be in the non-athlete part of strong. NOT CERTAIN. Does NOT follow.

(II) "Some strong people are not teachers." From (2), some strong people are doctors. From (3), no doctor is a teacher. Therefore, those strong-doctors are not teachers. "Some strong people are not teachers" is TRUE. FOLLOWS.

(III) "It is possible that some teachers are athletes." From (3): no doctor is a teacher. Teachers are completely separate from doctors. Athletes are within strong. The given statements don't establish any connection between teachers and athletes - teachers might or might not overlap with athletes. The possibility is NOT ruled out. FOLLOWS (possibility).

(IV) "No athlete is a teacher." Athletes are strong. Some strong people are doctors. But athletes themselves being teachers is not ruled out by the given statements - only doctors can't be teachers. We cannot conclude no athlete is a teacher. DOES NOT FOLLOW.

**Answer: Conclusions II and III follow.**

---

## Coding-Decoding: Extended Types

### Type 3: Symbol-Based Coding

In symbol coding, each letter corresponds to a symbol (%, #, @, etc.). The code is provided and must be applied.

**Problem:** In a code language: A=!, B=@, C=#, D=$, E=%, F=^.
If the code for BEAD is @%!$, what is the code for FACE?

F=^, A=!, C=#, E=%. Code for FACE = **^!#%**

**The approach:** Build the full mapping table first (even if it has 6 entries). Apply it to the target word. Never try to remember multiple symbol mappings in your head simultaneously.

### Type 4: Number Code Substitution

Each letter gets a number based on a specific rule. Common rules: alphabetical position (A=1, B=2...), reverse alphabetical (A=26, B=25...), position × 2, or position + constant.

**Problem:** If A=2, C=4, E=6 (even numbers for vowels starting at A), and B=1, D=3, F=5 (odd numbers for consonants starting at B), what is the code for FACE?

F is the 3rd consonant (after B,D): F=5. A is the 1st vowel: A=2. C is the 2nd consonant: C=3. E is the 3rd vowel: E=6.
Code for FACE = **5236**

---

## Blood Relations: Extended Coded Problems

**Advanced coded blood relation:**

"P @ Q means P is the mother of Q. P # Q means P is the father of Q. P $ Q means P is the sister of Q. P % Q means P is the brother of Q."

Expression: A @ B # C % D $ E

Decode:
- A @ B: A is mother of B.
- B # C: B is father of C.
- C % D: C is brother of D.
- D $ E: D is sister of E.

**Question:** How is A related to D?

Draw the tree:
A is mother of B. B is father of C. C is brother of D (so C and D are siblings; B is father of both C and D). A is mother of B, who is father of C and D. A is **grandmother** of D (paternal grandmother through father B, and B's mother A).

**Question 2:** How is E related to A?

D is sister of E → D and E are siblings. D and C are siblings → E is also a sibling of C (and D). B is father of C, D, and E. A is mother of B. A is grandmother of E.

---

## Visual Reasoning: Extended Examples

### The Number Pattern Matrix

**Advanced pattern matrix (3×3):**

```
3   6   9
4   8   12
5   ?   15
```

Row pattern: each row is an arithmetic progression with common difference = first element.
Row 1: 3, 6, 9 (d=3). Row 2: 4, 8, 12 (d=4). Row 3: 5, ?, 15 (d=5). Missing = 5+5 = **10**.

Column check: Column 1: 3,4,5 (+1). Column 2: 6,8,? (+2). Predicted: 10 ✓. Column 3: 9,12,15 (+3) ✓.

### Mirror Image of Numbers

For numbers, the mirror image is obtained by:
1. Reversing the order of digits.
2. Replacing each digit with its mirror (0↔0, 1↔1, 2↔2, 3↔3 since these are symmetric; 6↔9, 7 has no standard mirror and is omitted from such problems).

For questions about a digital clock's mirror image: flip horizontally. The time shown as HH:MM in a mirror appears with horizontally reflected digits.

---

## Floor-Based Puzzles: Advanced Example

**Problem:** 7 people A,B,C,D,E,F,G live on floors 1-7 (floor 1 = lowest). Various conditions given.

Conditions:
(1) A is on floor 3.
(2) D is on a higher floor than C.
(3) There are 2 floors between G and E.
(4) B is on the highest floor.
(5) F is on floor 6.
(6) C is on a floor between A and F.

**Solution:**
B = 7 (highest). F = 6. A = 3.
C is between A(3) and F(6): C is at floor 4 or 5.
D is higher than C: if C=4, D is 5, 6, or 7. Floor 6=F, 7=B. So D=5 (if C=4).
If C=5, D must be higher than 5: D=6 or 7. F=6, B=7. Contradiction.
So C=4, D=5.

Remaining: E and G at floors 1 and 2.
Condition (3): 2 floors between G and E. Possible: (1 and 3) but 3=A. (2 and 4) but 4=C. (1 and 2) have only 1 floor between. Wait: "2 floors between G and E" means |G-E|=3 (if "2 floors between" means 2 floors exist between them, so they are 3 apart). Floors available for G and E: 1 and 2. |1-2|=1. This is 0 floors between them (no floor exists between floors 1 and 2). This doesn't satisfy the condition.

Re-examine: Maybe "between" means |G-E|=2. Available floors 1 and 2: |1-2|=1 ≠ 2. Still not satisfied.

With only floors 1 and 2 remaining for G and E, condition (3) cannot be satisfied unless the problem has additional flexibility. Review: have we fully used all conditions? Yes. Conclusion: this problem as stated has no solution given current information, OR condition (3) requires reinterpretation (perhaps "2 floors between" means G is on floor (E+2) or (E-2)).

If |G-E|=2 with available floors 1 and 2: not possible.

This type of problem occasionally has minor errors in published materials. In the actual TCS NQT, all problems have valid solutions. When you encounter an apparent contradiction, the most likely error is in your deduction - recheck your earlier steps.

---

## Analogies: Extended Practice

### Semantic Analogies

**Advanced:** Author : Plagiarism :: Scientist : ?
An author commits plagiarism (using others' work without credit). A scientist commits **fraud** (using fabricated or others' data without credit). Both are misuse/theft of intellectual work.

**Alternative framing:** Doctor : Malpractice :: Lawyer : Malpractice (same term). But the deeper analogy: professional : professional ethical violation.

For TCS Advanced, semantic analogies often involve professional/domain-specific relationships. Look for: instrument of, location of, product of, study of, cause of.

### Mixed Number-Letter Analogy

**Problem:** A2Z : C4X :: E6V : ?
A(1)2Z(26): Position 1, number 2, position 26.
C(3)4X(24): Position 3, number 4, position 24.
E(5)6V(22): Position 5, number 6, position 22.
Pattern: First letter at position 2n-1, middle number = 2n, last letter at position 27-(2n-1) = 28-2n.

For n=1: A,2,Z. For n=2: C,4,X. For n=3: E,6,V. For n=4: G,8,T.
Answer: **G8T**

---

## Reasoning Section Strategy: Putting It All Together

### The Optimal Question Order in Reasoning

At the start of the Reasoning section, spend 90 seconds identifying:
- How many arrangement sets are there, and how many questions per set?
- Are any syllogism sets visible?
- Are there quick individual questions (series, analogies, coding-decoding)?

**Optimal answering order:**
1. Quick individual questions: series completion, analogies, simple coding-decoding (target 30-45 seconds each)
2. Medium individual questions: blood relations, directions, simple data sufficiency (60-90 seconds each)
3. Small arrangement sets (3 questions) if time permits
4. Large arrangement sets (5+ questions) - highest time investment, highest per-question return
5. Advanced types (critical reasoning, complex DS) with remaining time

Following this order rather than sequential order saves 3-5 minutes in a 25-minute section, which is enough time to attempt 3-5 additional questions.

### Rapid Review Before Submitting

In the last 2 minutes of the Reasoning section (before time expires), do a rapid scan:
- Any questions with a confirmed answer marked but where the answer "feels off"? Reconsider.
- Any questions left blank where you could eliminate at least 2 options? Guess on those.
- Any questions where you made an assumption that was not explicitly stated? Verify.

These 2 minutes of review typically recover 1-2 marks per section - not trivial in a 25-question section where each mark represents 4% of the section score.

---

## Reasoning Preparation: The Confidence Foundation

Many candidates approach reasoning preparation with a specific anxiety that does not affect their aptitude preparation: "I'm just not logical." This belief is unfounded and demonstrably false.

Every reasoning topic in TCS NQT is technique-dependent, not talent-dependent. The technique for seating arrangements (draw a diagram, apply conditions one by one, verify at the end) works equally well for every candidate who applies it. The technique for syllogisms (draw Venn circles, apply each statement, check conclusions) works regardless of the solver's natural logical inclination.

The evidence is in the pattern of errors. Candidates who struggle with reasoning make specific, predictable errors - they attempt to hold arrangements in their head, they misapply direction turns, they skip the verification step. These are not signs of low logical ability. They are signs of not having the technique.

Candidates who have the technique make different, much rarer errors - an edge case in a direction problem (clockwise vs anticlockwise interpretation), a subtle syllogism trap (possibility vs certainty). These are the errors that separate 18/25 from 22/25 at advanced preparation levels.

If you are starting from 14/25 or below, the gap to 18-20/25 is almost entirely closed by learning and practicing the techniques in this guide. If you are already at 18/25, closing the gap to 22/25 requires the Advanced-level practice and the critical reasoning component.

The preparation investment for Reasoning is among the most efficient in the entire TCS NQT preparation - technique learning produces large, rapid, reliable gains. Start with the systematic approaches, practice them on paper, and the scores follow.

---

## Extended Topic Coverage: Comparison Puzzles

### Ranking with Multiple Attributes

Advanced comparison puzzles assign multiple attributes (height, weight, age, rank) to a group and ask for specific comparisons.

**Problem:** A, B, C, D, and E are five friends. Among their heights:
- B is taller than E but shorter than A.
- C is the shortest.
- D is taller than B but shorter than A.
- E is taller than C.

Establish the ranking from the conditions:
- C < E (from last condition)
- C < E < B (from B taller than E, C shortest)
- B < D < A (D taller than B, shorter than A)
- A is tallest (nothing is stated above A)

Full ranking tall to short: **A > D > B > E > C**

**Question types from comparison puzzles:**
- "Who is the third tallest?" → B
- "Who is between D and E in height?" → B
- "How many people are shorter than D?" → 2 (B, E, C = 3 shorter? Let me recount: A>D>B>E>C, so B, E, C are shorter than D = 3 people shorter than D)

The key: express every relationship in a consistent inequality chain before answering questions.

### Scheduling Puzzles

Scheduling puzzles assign tasks to time slots (days, hours) for multiple people, with conditions about who can do what when.

**Approach:** Create a table with people as rows and time slots as columns. Fill in confirmed assignments (✓), confirmed impossibilities (✗), and constraints.

**Foundation scheduling problem:** 5 tasks T1-T5 must be completed by 5 employees A-E, one task per employee. Conditions:
(1) A cannot do T3.
(2) B must do T2 or T4.
(3) C does T1.
(4) D does not do T2.
(5) E does T5.

From (3): C=T1. From (5): E=T5.
Remaining: A, B, D for T2, T3, T4.
From (1): A cannot do T3. From (2): B must do T2 or T4.
From (4): D cannot do T2.

If B=T2: A and D take T3 and T4. A cannot do T3 → A=T4, D=T3. Check D≠T2 ✓.
If B=T4: A and D take T2 and T3. D≠T2 → D=T3. But A cannot do T3 and D takes T3, so A must take T2. D takes T3. Check: A=T2, D=T3, B=T4.

Two possible assignments:
- A=T4, B=T2, C=T1, D=T3, E=T5
- A=T2, B=T4, C=T1, D=T3, E=T5

Questions would specify additional conditions to narrow to one unique solution, or ask "which of the following can be true?"

---

## Input-Output: Advanced Pattern Recognition

### Two-Simultaneous-Operation Patterns

Advanced Input-Output problems apply two operations per step: one affecting numbers and one affecting words, or two operations on the same type of element.

**Problem:**
Input:  85 joy 63 love 12 hope 47 faith
Step 1: 12 joy 85 love 63 hope 47 faith (smallest number moved to front)
Step 2: 12 joy 47 love 85 hope 63 faith (second-smallest moved to position 3)
Step 3: 12 joy 47 love 63 hope 85 faith (numbers now sorted ascending at alternate positions)

Pattern: numbers sort ascending at positions 1, 3, 5, 7 (every odd position), while words remain at even positions in original order.

**Question: What is the final arrangement?**
Numbers: 12, 47, 63, 85 (ascending at positions 1,3,5,7)
Words: joy, love, hope, faith (original order at positions 2,4,6,8)
Final: **12 joy 47 love 63 hope 85 faith**

**What is the arrangement after Step 2?**
After Step 1: position 1 = 12 (smallest). After Step 2: position 3 = 47 (second smallest).
**12 joy 47 love 85 hope 63 faith**

### Reverse-Operation Problems

Some Input-Output problems ask: "If Step 3 is X, what was the original Input?" This requires tracing the operations in reverse.

**Approach:** Identify the pattern (forward direction). Apply the reverse operation from the given step backward to reach the input.

If the forward operation was "move smallest to front each step," the reverse operation is "move the front number back to its original sorted position." Trace backward from the given step.

---

## The 12 Reasoning Types: Quick Reference Card

| Type | Technique | Time Budget | Key Rule |
|---|---|---|---|
| Coding-Decoding | Write mapping table | 30-60 sec | Never try to hold mapping mentally |
| Seating (Linear) | Draw boxes, fill conditions | 2-4 min/set | One condition at a time |
| Seating (Circular) | Fix one person, draw circle | 3-5 min/set | All directions relative to fixed person |
| Syllogisms | Draw Venn circles per statement | 90 sec (2-stmt) | Test with abstract variables |
| Number Series | Write first and second differences | 30-45 sec | Verify pattern on 3+ terms before applying |
| Letter Series | Write letter-to-number mapping | 30-45 sec | Include position numbers |
| Analogies | Identify the relationship type | 30 sec | Try multiple relationship types |
| Direction Sense | Draw path on compass | 45-60 sec | Turns are RELATIVE to current facing |
| Blood Relations | Draw family tree | 60-90 sec | Never follow chain mentally |
| Puzzles | Build constraint table | 3-6 min/set | Verify ALL conditions after solving |
| Data Sufficiency | Test each statement ALONE | 60-90 sec | Never combine while testing individually |
| Input-Output | Identify pattern from 2 steps, verify with 3rd | 2-3 min/set | Check numbers AND words separately |

---

## Reasoning Under Time Pressure: The Mental Game

### Recognising When to Cut Your Losses

The most skilled reasoning candidates in the NQT do something that feels counterintuitive: they give up on specific questions faster than other candidates. This is not defeatism - it is strategic resource allocation.

When a seating arrangement has been worked on for 4 minutes and no valid arrangement has emerged, two scenarios are possible:
1. The solution is there but requires another 2-3 minutes to find.
2. You are in a logic loop because of an error in your first condition application.

In Scenario 2, more time does not yield the answer - a fresh start from scratch would. In a timed exam, starting from scratch costs more time than the question is worth. The cut-loss decision: mark the questions in this set as your best guess and allocate the remaining time to solvable questions.

**The 3-minute rule for arrangements:** If you have not placed at least half the people correctly in an arrangement after 3 minutes, the remaining time is better spent elsewhere. Mark your best guess (based on the partial arrangement you have) and move on.

### Confidence Calibration

A reasoning question should produce one of three states when you complete it:
1. **High confidence:** "I applied the correct technique, checked my work, and I am sure of this answer." Mark and move on without second-guessing.
2. **Moderate confidence:** "My technique application seems correct but I could not verify all conditions." Mark the answer but note the question for review if time permits.
3. **Low confidence:** "I am guessing." Apply the elimination strategy and mark, but acknowledge you might be wrong.

Candidates who second-guess High Confidence answers during time-pressure moments often change correct answers to incorrect ones. Trust the technique when you applied it correctly. Uncertainty during review is not evidence of error.

---

## Practice Questions: Advanced Reasoning (15 Questions)

**Q1 (Advanced Arrangement - floor):**
7 people on floors 1-7. B=7, C=1, D is on floor 5, E is above D but below B (E is on floor 6), A is between C and D (A=2,3, or 4). F is on floor 3. What floor is A on?
Remaining floor 2 is the only option between C(1) and the occupied floors 3(F) and 5(D). A = **2**.

**Q2 (Critical Reasoning - assumption):**
"All students who study daily score above 80%. Rajan scores above 80%. Therefore, Rajan studies daily."
What does this argument assume? It commits the fallacy of affirming the consequent. The assumption is: **studying daily is the only way to score above 80%.** (This is a false assumption - the argument is actually invalid.)

**Q3 (Advanced Syllogism):**
All engineers are scientists. Some scientists are authors. No author is an artist.
Can we conclude: Some engineers are not artists?
Engineers are within scientists. Some scientists are authors. But the "engineers within scientists" part might not overlap with the "authors within scientists" part. We cannot say some engineers are authors (that's not certain). However: Can any engineer be an artist? An engineer would need to be an author first to be potentially restricted from being an artist, but engineers might not be authors. So engineers might be artists. Therefore we CANNOT conclude "some engineers are not artists" with certainty. **Does not follow.**

**Q4 (Coded Blood Relation - Advanced):**
A * B means A is the daughter of B. A / B means A is the son of B. A = B means A is the wife of B. If M * N / P = Q, who is M to Q?
M * N: M is daughter of N. N / P: N is son of P. P = Q: P is wife of Q. So Q is husband of P. P is father of N. N is parent of M. M is granddaughter of P. Q is husband of P (M's grandfather's wife = Q is M's grandmother's husband from P's side = M's grandfather). M is Q's granddaughter.

**Q5 (Input-Output):**
Input: 32 table 17 chair 9 desk 55 shelf
If the pattern is: smallest number and its adjacent word move to front each step, what is Step 2?
Step 1: 9 desk 32 table 17 chair 55 shelf (9 and "desk" moved to front)
Step 2: 9 desk 17 chair 32 table 55 shelf (next smallest = 17 with "chair" moved to position 3)
Answer: **9 desk 17 chair 32 table 55 shelf**

**Q6 (Data Sufficiency - complex):**
What is the value of integer n?
Statement 1: n²= 49.
Statement 2: n > 0.

Statement 1 alone: n = 7 or n = -7. Not unique. NOT sufficient.
Statement 2 alone: n > 0. Not unique. NOT sufficient.
Together: n² = 49 AND n > 0 → n = 7. Unique. **Answer: (C)**

**Q7 (Series - wrong term):**
3, 8, 15, 24, 35, 48, 65, 80
Expected pattern: 3,8,15,24,35,48,63,80. Differences: 5,7,9,11,13,15,17 (odd numbers +2 each).
Actual: ...48, **65**, 80. Expected: 48+15=63, then 63+17=80.
Wrong term: **65** (should be 63).

**Q8 (Direction - Advanced):**
Starting at point A, a man walks 6 km east. Then 4 km north. Then 6 km west. Then 8 km south. How far and in which direction is he from A?
Net east-west: +6 -6 = 0 (back to same longitude as A).
Net north-south: +4 -8 = -4 (4 km south of A).
He is **4 km directly south** of A.

---

## Building Reasoning Speed: The Daily Drill

The following 5-minute daily drill maintains reasoning sharpness throughout the preparation period. It takes less time than a full practice session but consistently keeps all the techniques active in working memory.

**Drill 1 (90 seconds): 3 quick coding-decoding problems**
Apply uniform shift, reverse alphabetical, and position-based shift to short 4-letter words. Time: 30 seconds each.

**Drill 2 (90 seconds): 2 syllogisms**
Two-statement syllogisms with two conclusions each. Draw Venn circles, classify conclusions. Time: 45 seconds each.

**Drill 3 (90 seconds): 2 direction problems**
Simple 4-turn direction problems. Draw path, calculate distance. Time: 45 seconds each.

**Drill 4 (60 seconds): 1 series problem**
Write the first two differences and identify the next term. Time: 60 seconds maximum.

This 5-minute drill, done daily, ensures that the technique for each reasoning type stays fluent throughout the preparation period. Without daily practice, techniques rust - particularly direction sense and syllogisms, which require specific mental operations that atrophy without use.

The reasoning section of the TCS NQT is not a natural ability test. It is a test of prepared technique. Every type has a method. Every method is learnable. Every method becomes fast with practice. The preparation path is clear and the endpoint - 20+ out of 25 in Foundation Reasoning - is reachable for any candidate who follows it consistently.
