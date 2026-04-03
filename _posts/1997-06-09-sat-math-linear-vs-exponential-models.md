---
layout: post
title: "SAT Math: Linear vs Exponential Models and When to Use Each"
page_title: "SAT Math Linear vs Exponential Models: Complete Guide to Choosing, Interpreting and Applying Models for the Digital SAT"
date: 1997-06-09
categories: ["Industry"]
tags: ["SAT", "SAT Math", "Modeling", "Linear", "Exponential"]
excerpt: "Master the diagnostic test for linear vs exponential data, translate real-world scenarios, interpret growth and decay, and answer every modeling question on the Digital SAT."
image: "/assets/images/blog/blog-51.webp"
reading_time: 61
author: "katherine-blake"
last_updated: 1997-06-09
---

Linear and exponential model questions appear two to three times on every Digital SAT administration, spanning both the Problem Solving and Data Analysis domain and the Advanced Math domain. They are among the most conceptually rich questions on the test because they require both mathematical skill (identifying and applying the right function form) and interpretive skill (translating a real-world scenario into a model and reading results in context). A student who can automatically distinguish between a constant rate of change (linear) and a constant multiplicative factor (exponential) will resolve every linear-vs-exponential question on the Digital SAT correctly.

The single most powerful diagnostic tool for these questions is the two-test: compute both the differences between consecutive y-values AND the ratios between consecutive y-values from a data table. If the differences are constant, the model is linear. If the ratios are constant, the model is exponential. This two-calculation test resolves every data-table model identification question in under 60 seconds.

This guide covers the complete Digital SAT treatment of linear and exponential models: the structure of each model and what makes it linear or exponential, the two-test for identifying the correct model from a data table, translating real-world scenarios into linear or exponential form, the key interpretive vocabulary (initial value, rate of change, growth factor, decay factor, doubling time), piecewise linear models, the inevitable dominance of exponential over linear at large values, and the "approximately linear or exponential" question type where real data fits one model better than the other. For the linear equation and slope-intercept concepts that underlie the linear model, the companion [SAT Math algebra guide](/2021/04/24/sat-algebra-domain-complete-guide/) provides the full linear equation framework. For the exponential function notation and transformations that connect to the exponential model, the [SAT Math functions and transformations guide](/1997/08/02/sat-math-functions-transformations/) provides that foundation. For timed practice, the [free SAT Math practice questions](https://reportmedic.org/tools/sat-math-practice-questions.html) on ReportMedic provide Digital SAT-format problems at every difficulty level.

![SAT Math Linear vs Exponential Models](/assets/images/blog/blog-51.webp)

## The Structure of Linear Models

A linear model describes a quantity that changes by the same amount for each equal increase in the input variable. The defining feature: a constant rate of change (constant slope).

The general form of a linear model: y = mx + b, where m is the rate of change (slope) and b is the initial value (y-intercept, the value of y when x = 0).

What "constant rate of change" means: for every 1-unit increase in x, y changes by exactly m units. If m = 5 and the model represents daily earnings, the person earns $5 more for each additional day worked, regardless of how many days have already been worked.

In a data table, a linear model produces equal DIFFERENCES between consecutive y-values when the x-values are equally spaced. If x increases by 1 each row and y increases by 3 each row (constant difference of 3), the model is linear with slope m = 3.

The four components of a linear model statement: initial value b (the starting amount when x = 0), rate of change m (the constant change per unit of x), the independent variable x (often time), and the dependent variable y (the quantity being modeled).

Real-world linear scenarios: salary with a fixed annual raise of $2,000 per year (linear because the SAME dollar amount is added each year). A car traveling at constant speed of 60 mph (linear because the SAME distance is covered each hour). A tank draining at a constant rate of 10 gallons per minute (linear because the SAME volume leaves each minute). Renting a bicycle at $8 per hour (linear because the SAME charge applies to each additional hour).

The key word signal for linear models: "per" (constant amount per unit), "each" (same amount each time), "added," "increased by a fixed amount," "$X more per unit." These phrases signal constant addition, which is the defining property of linear growth.

## The Structure of Exponential Models

An exponential model describes a quantity that changes by the same MULTIPLICATIVE FACTOR for each equal increase in the input variable. The defining feature: a constant ratio between consecutive values (a constant growth or decay factor).

The general form of an exponential model: y = a times b to the power x, where a is the initial value (the value when x = 0) and b is the growth or decay factor (the ratio between consecutive y-values when x increases by 1).

What "constant multiplicative factor" means: for every 1-unit increase in x, y is multiplied by b. If b = 1.08 and the model represents annual savings, the savings multiply by 1.08 each year, meaning the savings grow by 8 percent of the CURRENT amount (which increases each year).

In a data table, an exponential model produces equal RATIOS between consecutive y-values when the x-values are equally spaced. If x increases by 1 each row and y values are 10, 20, 40, 80 (each twice the previous), the ratio is constant at 2, indicating an exponential model with growth factor b = 2.

The four components of an exponential model statement: initial value a (the starting amount when x = 0), growth or decay factor b (the constant multiplier per unit of x), the independent variable x (often time), and the dependent variable y.

Real-world exponential scenarios: a 5 percent annual interest rate on an investment (exponential because the SAME percentage of the current balance is added each year, so the dollar amount grows each year). Bacterial population doubling every 3 hours (exponential because the population is multiplied by 2 every 3 hours). A radioactive substance losing 10 percent of its mass each year (exponential decay because the SAME percentage of the current mass is removed each year). A viral video being shared at a rate where views multiply by 3 each hour (exponential).

The key word signal for exponential models: "percent increase/decrease," "grows by X%," "doubles," "triples," "halves," "multiplied by a factor of." These phrases signal constant multiplication (or division), which is the defining property of exponential growth or decay.

## The Two-Test: The Fastest Way to Identify the Correct Model

The two-test is the most reliable and most time-efficient method for identifying whether a given data table represents a linear or exponential model.

Step one: compute the differences between consecutive y-values (first differences). If these differences are all equal (constant), the model is LINEAR.

Step two: compute the ratios between consecutive y-values (divide each y-value by the previous). If these ratios are all equal (constant), the model is EXPONENTIAL.

If neither the differences nor the ratios are constant, the data does not fit a simple linear or exponential model.

Worked example: the table shows x = 0, 1, 2, 3, 4 and corresponding y = 3, 6, 12, 24, 48.

Differences: 6 minus 3 = 3, 12 minus 6 = 6, 24 minus 12 = 12, 48 minus 24 = 24. The differences are 3, 6, 12, 24. NOT constant. Not linear.

Ratios: 6/3 = 2, 12/6 = 2, 24/12 = 2, 48/24 = 2. The ratios are all 2. CONSTANT. Exponential with growth factor 2 and initial value 3.

Model: y = 3 times 2 to the power x.

Worked example: the table shows x = 0, 1, 2, 3, 4 and y = 5, 8, 11, 14, 17.

Differences: 8 minus 5 = 3, 11 minus 8 = 3, 14 minus 11 = 3, 17 minus 14 = 3. Constant difference of 3. LINEAR with slope m = 3 and initial value b = 5.

Ratios: 8/5 = 1.6, 11/8 = 1.375, 14/11 = 1.27, 17/14 = 1.21. NOT constant. Not exponential.

Model: y = 3x + 5.

Worked example (harder): the table shows x = 0, 2, 4, 6 and y = 100, 50, 25, 12.5.

The x-values increase by 2, not 1. Adjust: for equally spaced x-values with spacing 2, the ratio test still applies: 50/100 = 0.5, 25/50 = 0.5, 12.5/25 = 0.5. Constant ratio. Exponential.

But this ratio (0.5) is the factor for every 2 units of x, not 1 unit. The per-unit factor b is 0.5 to the power (1/2) = root(0.5) = 1/root(2). Or equivalently, write the model as y = 100 times 0.5 to the power (x/2).

The two-test applies to any equally-spaced x-values by comparing consecutive y-values in the table, regardless of the spacing of x.

## Translating Real-World Scenarios Into Models

The translation skill is the application layer of linear-vs-exponential classification: given a verbal description, identify the model type and write the equation.

Linear translation: "A company starts with 200 employees and hires 15 new employees each month." Starting value = 200 (b = 200). Rate of change = 15 per month (m = 15). Model: E(t) = 200 + 15t, where t is months.

Exponential translation: "A company starts with 200 employees and its workforce grows 8 percent per month." Starting value = 200 (a = 200). Growth factor = 1.08 per month (b = 1.08; the 1 represents keeping 100 percent plus adding 8 percent). Model: E(t) = 200 times (1.08) to the power t.

The contrast: in the linear model, 15 employees are added per month regardless of the current count. In the exponential model, 8 percent of the CURRENT count are added per month. At month 1: linear adds 15, exponential adds 0.08 times 200 = 16. By month 10: linear still adds 15, but exponential adds 0.08 times 200(1.08) to the 9th = much more than 15.

Decay scenarios:

Linear decay: "A tank contains 500 gallons and drains at 30 gallons per hour." W(t) = 500 minus 30t.

Exponential decay: "A radioactive substance has a mass of 500 grams and loses 12 percent of its mass each year." M(t) = 500 times (0.88) to the power t. (Keeping 88 percent each year = multiplying by 0.88.)

The growth factor b and decay factor:
For a percent increase of r percent: b = 1 + r/100.
For a percent decrease of r percent: b = 1 minus r/100.

For an 8 percent annual increase: b = 1.08.
For a 15 percent annual decrease: b = 0.85.
For doubling each period: b = 2.
For halving each period: b = 0.5.
For tripling each period: b = 3.

## Growth Factor, Decay Factor, and the Initial Value

The parameters a and b in the exponential model y = a times b to the power x have specific interpretations that the Digital SAT tests in context.

The initial value a: the value of y when x = 0. In context, this is the starting amount before any growth or decay has occurred. For "a population of 1000 bacteria doubles every hour," a = 1000.

The growth factor b (when b is greater than 1): the multiplier applied to y for each one-unit increase in x. For b = 1.05, y increases by 5 percent per unit. For b = 2, y doubles per unit. The growth RATE as a percent is (b minus 1) times 100 percent.

The decay factor b (when 0 is less than b is less than 1): the multiplier applied to y for each one-unit increase in x. For b = 0.90, y decreases by 10 percent per unit (retains 90 percent). For b = 0.5, y halves per unit. The decay RATE as a percent is (1 minus b) times 100 percent.

A common Digital SAT question: "The function P(t) = 4200 times (0.94) to the power t models the population of a city, where t is years since 2010. What is the annual percent decrease in the population?"

The decay factor is 0.94, meaning the population retains 94 percent each year. The annual decrease = 1 minus 0.94 = 0.06 = 6 percent. The population decreases by 6 percent per year.

A harder question: "The function V(t) = 8000 times (1.035) to the power (4t) models the value of an investment after t years, where each period is a quarter (three months). What is the approximate annual growth factor?"

The quarterly growth factor is 1.035, and there are 4 quarters per year. The annual growth factor = (1.035) to the power 4 approximately 1.1475. The annual growth rate is approximately 14.75 percent.

## The Diagnostic Test for Real-World Scenarios

Beyond data tables, the two-test logic applies to verbal descriptions: is the scenario describing constant addition (linear) or constant multiplication (exponential)?

Scenario test: ask "what happens to the change as the quantity grows?"

If the change stays the same (constant dollar amount, constant rate per time), it is LINEAR.
If the change grows proportionally (same percentage, same factor), it is EXPONENTIAL.

Practical examples:

"A savings account earns $50 interest per year" - constant $50 added regardless of balance. LINEAR.

"A savings account earns 5 percent interest per year" - the interest dollar amount grows as the balance grows. EXPONENTIAL.

"A drug leaves the body at a rate of 10 mg per hour" - constant 10 mg removed per hour. LINEAR decay.

"A drug leaves the body at a rate of 30 percent per hour" - 30 percent of the CURRENT amount is removed each hour, so the actual amount removed decreases as the drug level falls. EXPONENTIAL decay.

"A city grows by 3,000 residents per year" - constant 3,000 added. LINEAR.

"A city grows by 3 percent per year" - the actual number added depends on the current population. EXPONENTIAL.

The decision rule: dollar amount / rate = linear. Percentage / factor = exponential.

## Exponential Always Eventually Dominates Linear

One of the most conceptually important facts about exponential vs linear growth is that an exponential function with any growth factor greater than 1 will always eventually exceed any linear function, regardless of how large the linear function's slope is or how large a head start it has.

This fact appears on the Digital SAT in questions about comparing two models or identifying which model predicts a larger value for large x.

The formal statement: for any exponential function a times b to the power x with b greater than 1 and any linear function mx + c, there exists some threshold x-value X beyond which the exponential function is always larger. For large enough x, the exponential dominates.

Why this happens: the linear function adds the same amount each period (m), while the exponential function multiplies by b each period. Multiplication eventually outpaces addition regardless of the constants involved.

Example comparison: linear function y = 1000x and exponential function y = 2 to the power x.

At x = 1: linear = 1000, exponential = 2. Linear leads massively.
At x = 10: linear = 10,000, exponential = 1024. Linear still leads.
At x = 15: linear = 15,000, exponential = 32,768. Exponential has overtaken linear.

Even with a massive initial linear lead and a slope of 1000, the exponential function y = 2 to the power x eventually dominates. The crossover happens around x = 13 to 14.

Digital SAT application: "For large values of t, which model predicts a greater population: P(t) = 5000t + 100 or P(t) = 10 times 1.2 to the power t?" The answer is always the exponential model for large enough t, regardless of the initial linear lead. For the specific values here, the exponential starts tiny (10 at t = 0) compared to the linear (100 at t = 0) but eventually dominates because 1.2 to the power t grows without bound.

## Piecewise Linear Models: When the Rate Changes

A piecewise linear model has different rates of change over different intervals of the independent variable. Each piece is linear (constant rate within its interval), but the rate differs between pieces.

The defining feature: a graph of a piecewise linear function is a connected series of line segments, each with its own slope. The slope changes at specific breakpoints (transition points between pieces).

A common real-world piecewise linear scenario: utility pricing with tiered rates. "A utility charges $0.12 per kilowatt-hour for the first 500 kWh and $0.18 per kilowatt-hour for usage above 500 kWh." For usage from 0 to 500 kWh: cost increases linearly at $0.12/kWh. For usage above 500 kWh: cost increases linearly at $0.18/kWh (steeper slope). The transition at 500 kWh is the breakpoint.

Reading piecewise linear models from graphs: each line segment's slope represents the rate of change for that interval. A steeper slope means a higher rate. A flat segment means zero rate of change. A segment with negative slope means the quantity is decreasing.

A specific Digital SAT piecewise linear question type: "The graph shows the distance traveled by a cyclist over 4 hours. During which hour did the cyclist travel the fastest?" The cyclist travels fastest during the hour with the steepest slope (greatest distance per hour). Compare the slopes of each hourly segment; the steepest is the fastest.

Writing piecewise linear models:

Example: a worker earns $15/hour for the first 40 hours and $22.50/hour (1.5 times $15, overtime rate) for hours beyond 40. Model:

E(h) = 15h for 0 less than or equal to h less than or equal to 40.
E(h) = 15(40) + 22.50(h minus 40) = 600 + 22.50(h minus 40) for h greater than 40.

At h = 40: E(40) = 600. Continuity: 600 + 22.50(40 minus 40) = 600. Continuous at the breakpoint.

## The "Approximately Linear or Exponential" Question Type

The Digital SAT sometimes presents real data that does not perfectly fit either a linear or exponential model but fits one significantly better than the other. The question asks which model type better represents the data.

The analysis method: apply the two-test (compute differences AND ratios). If the differences are approximately constant (with small variation) but the ratios vary significantly, the linear model is better. If the ratios are approximately constant but the differences vary significantly, the exponential model is better.

Example: the table shows x = 0, 1, 2, 3, 4 and y = 10, 21, 33, 46, 60.

Differences: 11, 12, 13, 14. Nearly constant but increasing slightly. Approximately linear.

Ratios: 21/10 = 2.1, 33/21 = 1.57, 46/33 = 1.39, 60/46 = 1.30. Decreasing significantly. Not approximately exponential.

Conclusion: the linear model better represents this data (the differences are nearly constant, while the ratios are not).

Example: the table shows x = 0, 1, 2, 3, 4 and y = 10, 15, 22, 33, 48.

Differences: 5, 7, 11, 15. Increasing significantly. Not approximately linear.

Ratios: 15/10 = 1.5, 22/15 = 1.47, 33/22 = 1.50, 48/33 = 1.45. Approximately constant near 1.5. Approximately exponential.

Conclusion: the exponential model better represents this data.

## Ten Worked Examples Across All Question Types

### Example 1: Identify Model From Table (Easy)

Table: x = 0, 1, 2, 3; y = 4, 7, 10, 13.

Differences: 3, 3, 3. Constant. Linear model. Slope = 3, initial value = 4.

Model: y = 3x + 4.

Principle: constant differences = linear.

### Example 2: Identify Model From Table - Exponential (Easy)

Table: x = 0, 1, 2, 3; y = 2, 6, 18, 54.

Differences: 4, 12, 36. Not constant.
Ratios: 3, 3, 3. Constant. Exponential with factor 3 and initial value 2.

Model: y = 2 times 3 to the power x.

Principle: constant ratios = exponential.

### Example 3: Translate Scenario to Linear Model (Easy-Medium)

"A plant is 5 cm tall and grows 2 cm per week. Write a function for the height H after t weeks."

Constant addition of 2 cm per week = linear. H(t) = 5 + 2t.

At t = 0: H = 5 (initial height). Rate of change = 2 cm/week.

Principle: "grows X cm per week" signals linear (constant addition).

### Example 4: Translate Scenario to Exponential Model (Easy-Medium)

"An investment of $1,200 grows at 6 percent annually. Write a function for the value V after t years."

Constant percentage growth = exponential. Growth factor = 1 + 0.06 = 1.06. V(t) = 1200 times (1.06) to the power t.

Principle: "grows X percent annually" signals exponential (constant multiplication by 1.06).

### Example 5: Interpret Exponential Model Parameters (Medium)

The function P(t) = 8,000 times (0.97) to the power t models the population of a town. What does 0.97 represent?

0.97 is the annual decay factor: the population retains 97 percent each year, decreasing by 3 percent annually.

Principle: in exponential decay models, the base b = 1 minus (decay rate). Here b = 0.97 means 3 percent annual decline.

### Example 6: Two-Test on Irregular Data (Medium)

Table: x = 0, 2, 4, 6; y = 100, 110, 121, 133.1.

Differences: 10, 11, 12.1. Not constant.
Ratios: 110/100 = 1.1, 121/110 = 1.1, 133.1/121 = 1.1. Constant at 1.1.

Exponential: factor 1.1 for every 2 units of x. Per-unit factor = (1.1) to the power (1/2) approximately 1.0488.

Model: y = 100 times (1.1) to the power (x/2), or y = 100 times (1.0488) to the power x.

Principle: apply the two-test even with non-unit x-spacing. Constant ratios still confirm exponential.

### Example 7: Which Model for Large Values (Hard)

For large values of t, which model predicts a greater value: A(t) = 5t + 1000 or B(t) = 5 times 1.1 to the power t?

For small t, A is much larger (at t = 0: A = 1000, B = 5). But B is exponential: it eventually overtakes A.

Find approximate crossover: 5 times 1.1 to the power t = 5t + 1000. Testing t = 70: B = 5 times (1.1) to the 70 approximately 5 times 789 = 3945. A = 5(70) + 1000 = 1350. B is larger.

For large t, B(t) = 5 times 1.1 to the power t is greater.

Principle: exponential always dominates linear for sufficiently large x.

### Example 8: Piecewise Linear Model (Hard)

A phone plan charges $0.05 per minute for the first 200 minutes and $0.02 per minute for usage beyond 200 minutes. Write the cost function C(m) for any usage m.

C(m) = 0.05m for 0 less than or equal to m less than or equal to 200.
C(m) = 0.05(200) + 0.02(m minus 200) = 10 + 0.02(m minus 200) for m greater than 200.

At m = 200: C = 10. Continuous.

Principle: write separate formulas for each piece; ensure continuity at the breakpoint.

### Example 9: Find Initial Value and Rate from Context (Hard)

"The temperature of a cooling object is modeled by T(t) = a times b to the power t, where t is minutes. At t = 0, the temperature is 90 degrees. After 5 minutes, the temperature is 60 degrees. Find a and b."

At t = 0: T(0) = a = 90. So a = 90.

At t = 5: 60 = 90 times b to the power 5. b to the power 5 = 60/90 = 2/3. b = (2/3) to the power (1/5) = (2/3) to the 0.2 approximately 0.896.

Model: T(t) = 90 times (0.896) to the power t.

Principle: use given data points to set up and solve for the parameters a and b.

### Example 10: Distinguish Linear and Exponential Salary Raises (Hard Module 2)

"Employee A receives a $3,000 annual raise. Employee B receives a 4 percent annual raise. Both start at a salary of $50,000. After how many years does Employee B's salary first exceed Employee A's?"

A(t) = 50,000 + 3,000t. B(t) = 50,000 times (1.04) to the power t.

At t = 0: both = 50,000. At t = 10: A = 80,000; B = 50,000 times (1.04) to the 10 = 50,000 times 1.480 = 74,000. A still leads.

At t = 20: A = 110,000; B = 50,000 times (1.04) to the 20 = 50,000 times 2.191 = 109,550. Nearly equal.

At t = 21: A = 113,000; B = 50,000 times (1.04) to the 21 approximately 113,931. B first exceeds A.

Answer: after approximately 21 years, Employee B's salary first exceeds Employee A's.

Principle: set up both functions, test values to find the crossover point. Use Desmos for efficiency.

## How the College Board Structures Linear vs Exponential Questions

Easy questions present a data table with obvious constant differences or ratios and ask which type of model fits. The two-test applied quickly identifies the answer.

Medium questions require either translating a verbal scenario into the correct model type (identifying whether a percent or a fixed amount is being added), interpreting the parameters of a given model (what does 0.85 represent in f(t) = 200 times 0.85 to the t?), or applying the model to predict a value at a specific x.

Hard questions compare two models for large values, require finding model parameters from data points (using a system of equations or algebraic substitution), ask about piecewise linear models with breakpoints, or present data that approximately fits one model type and ask for the better-fitting model with justification.

The hardest questions combine model identification with model application: given a verbal scenario, write the model, identify its type, find a specific value, and interpret what that value represents in context.

## Key Vocabulary for Model Interpretation Questions

The Digital SAT tests model interpretation in a specific and predictable vocabulary. Mastering these terms allows instant interpretation of any given function.

For linear functions y = mx + b:
"m is the slope" = the constant rate of change = how much y changes for each 1-unit increase in x.
"b is the y-intercept" = the initial value = the value of y when x = 0.
"The rate of change" = the slope m.
"The starting value" = b.

For exponential functions y = a times b to the power x:
"a is the initial value" = the value of y when x = 0.
"b is the growth factor" (b greater than 1) = the multiplier applied per period. The growth RATE is (b minus 1) expressed as a percent.
"b is the decay factor" (0 less than b less than 1) = the multiplier applied per period. The decay RATE is (1 minus b) expressed as a percent.
"Doubling time" = the time T such that b to the power T = 2. For b = 1.05: T = log(2)/log(1.05) approximately 14.2 periods.
"Half-life" = the time T such that b to the power T = 0.5. For b = 0.87: T = log(0.5)/log(0.87) approximately 5 periods.

The Digital SAT tests interpretation in questions like: "In the function V(t) = 2,500 times (1.07) to the power t, what does 2,500 represent?" Answer: the initial value (the value at t = 0). "What does 1.07 represent?" Answer: the annual growth factor, indicating 7 percent annual growth.

## Desmos for Linear vs Exponential Questions

Desmos is particularly useful for linear-vs-exponential questions in two specific ways.

First: graphing both models to see which fits the data better. If the question provides a data table and asks which model fits, plot the data points in Desmos (by entering them as a table), then graph both a linear function and an exponential function with approximately matching parameters. The model whose curve passes through or near all data points is the better fit.

Second: finding the crossover point for two models. Graph both functions and identify where they intersect. The intersection point is the crossover where one model transitions from predicting a higher value to predicting a lower value than the other.

For example 10 (salary comparison): graph A(t) = 50,000 + 3,000t and B(t) = 50,000 times 1.04 to the t in Desmos. The intersection visually identifies the year when B exceeds A, confirming the algebraic estimate of year 21.

The Desmos regression feature (available in the Bluebook app during the Digital SAT) can also fit a linear or exponential curve to a dataset, though this feature requires knowing which model type to try first.

## Connecting Linear and Exponential Models to the Broader Curriculum

Linear models connect to the linear equation and systems of equations content in the Algebra domain. Recognizing a linear model as y = mx + b and solving for parameters using given data points is identical to solving a linear equation or system. The slope formula (m = (y2 minus y1) / (x2 minus x1)) applies directly when two data points are given for a linear model.

Exponential models connect to the exponential function content in the Advanced Math domain. The growth and decay function y = a times b to the power x is the same as the general exponential function studied in the [SAT Math functions guide](/1997/08/02/sat-math-functions-transformations/), and the domain, range, and transformation properties of exponential functions all apply to exponential models.

The statistical interpretation of model fit connects to the Problem Solving and Data Analysis domain. When the Digital SAT presents data that is "approximately" linear or exponential, the selection of the better-fitting model requires the same data-analysis reasoning used in scatter plot and regression questions (covered in the [SAT Math scatter plots guide](/1997/08/11/sat-math-scatter-plots-regression/)).

## Score Range Strategy for Linear vs Exponential Questions

For students targeting 550-620, the priority is the data-table two-test: identify constant differences (linear) vs constant ratios (exponential). These appear at easy difficulty and are the foundational skill for all model questions.

For students targeting 620-700, add the translation skill (percent increase/decrease signals exponential, fixed amount signals linear), interpretation of model parameters (initial value, growth factor, decay rate), and simple model application (find y at a given x from a model). These appear at medium difficulty.

For students targeting 700-760, add piecewise linear models, the crossover question type (which model dominates for large x), finding model parameters from data points, and approximately-fits questions. These appear at hard difficulty.

For students targeting 760-800, add compound growth and decay (quarterly compounding, different time units than the exponent), complex piecewise models, and questions requiring both model identification and multi-step application in a single problem.

## Conclusion

Linear and exponential model questions reward the student who understands the fundamental distinction between addition and multiplication as the core of growth. A constant addition produces a linear relationship (straight-line graph, equal first differences in a table). A constant multiplicative factor produces an exponential relationship (curved graph, equal ratios in a table).

The two-test (compute differences AND ratios from a data table) is the most reliable identification tool and takes under 60 seconds for any data table the Digital SAT can present. The translation vocabulary (fixed amount = linear, percentage = exponential) resolves every verbal-scenario model question. The interpretation vocabulary (initial value, growth factor, decay rate) resolves every model parameter question.

Together, these tools form a complete framework for every linear vs exponential question on the Digital SAT. The two-to-three questions per administration that test this framework are among the most efficiently prepared questions on the test, because the identification and interpretation rules are small in number, precise in application, and consistent across every format the College Board uses.

The distinguishing insight: the fundamental difference between linear and exponential is the difference between adding and multiplying. Every real-world scenario involving a constant dollar amount, a constant rate per unit, or a constant absolute change is linear. Every scenario involving a constant percent, a constant multiplicative factor, or a compounding mechanism is exponential. Mastering this one distinction at a deep level produces fluency across every format these questions can take.

## How the Digital SAT Tests Model Identification at Each Difficulty Level

Easy model questions present a clean data table with whole-number entries and ask directly whether the relationship is linear or exponential. The differences or ratios are exact integers, requiring only one round of arithmetic. These resolve in under 60 seconds using the two-test.

Medium model questions wrap the identification in a context: "A population of bacteria is recorded each hour. Which type of function best models the data?" The student must apply the two-test to the given table AND recognize how the answer connects to real-world meaning (bacteria doubling = exponential, bacteria growing by a fixed count = linear). Alternatively, medium questions give a function in algebraic form and ask for the interpretation of a specific parameter.

Hard model questions combine identification, translation, and application in a single problem. A harder question might: present a verbal scenario, require the student to identify the model type, write the function, evaluate it at a specific input, and interpret the result in context. Or it might compare two models and ask which gives a larger prediction for a given range of values, requiring both model evaluation and the "exponential dominates linear for large x" understanding.

The hardest questions may involve non-standard time units (quarterly compounding vs annual, half-lives in hours vs years), or require finding a parameter from two given data points using the ratio method (dividing two equations to eliminate the initial value a, then solving for the growth factor b).

## The Slope-Intercept Form of a Linear Model: A Deep Dive

The linear model y = mx + b is the most fundamental algebraic form in all of Digital SAT Math. For the modeling context specifically, each component has a clear real-world interpretation that the Digital SAT tests through context questions.

The slope m: the constant rate of change. Dimensionally, m has units of "y-units per x-unit." If y is dollars and x is months, m has units of dollars per month. If y is kilometers and x is hours, m has units of km/h. The slope tells you: for every one more unit of x, y increases (or decreases if m is negative) by m units.

The y-intercept b: the value of y when x = 0. In context, this is always the starting value before any change has occurred. If x is time in years since 2020, then b is the value in 2020. If x is the number of items purchased, then b is the fixed cost before any items are purchased (a setup fee, membership fee, or base charge).

Practical questions using slope and intercept:

"A plumber charges a $75 flat fee plus $60 per hour. What does the y-intercept represent?" The y-intercept is 75, representing the flat fee charged regardless of hours worked.

"The function C(t) = 450 + 35t models a phone plan's total cost after t months. After how many months will the total cost exceed $1,000?" 450 + 35t is greater than 1000 gives 35t greater than 550, t greater than 15.7, so after month 16 (t = 16).

"The graph of a linear model passes through (0, 120) and (5, 70). What is the rate of change?" Slope = (70 minus 120) / (5 minus 0) = minus 50/5 = minus 10. The quantity decreases by 10 units per 1-unit increase in x.

## The Standard Exponential Form: Writing and Reading

The exponential model y = a times b to the power x appears in the Digital SAT in several algebraic forms that look different but represent the same function.

Standard form: y = a times b to the power x.
Alternative form with base e: y = a times e to the power (kx), where k = ln(b). The Digital SAT rarely uses this form but it appears in physics and finance contexts.
Alternative form with explicit rate: y = a times (1 + r) to the power x for growth, or y = a times (1 minus r) to the power x for decay, where r is the per-period rate as a decimal.

Converting between forms: a times b to the power x = a times (1 + r) to the power x means b = 1 + r, so r = b minus 1. For b = 1.06: r = 0.06 = 6 percent growth. For b = 0.92: r = minus 0.08, meaning an 8 percent decay per period (usually stated as "8 percent decay" not "minus 8 percent growth").

The Digital SAT tests this conversion in questions like: "The function V(t) = 3,500 times (1.04) to the power t models the value of a car, where t is years. What is the annual percent increase?" Answer: 4 percent (since b = 1.04 means 1 + 0.04).

A subtler question: "An account has a balance of $1,000. After 3 years, the balance is $1,157.63. What is the annual growth rate assuming exponential growth?"

a = 1000, t = 3, y = 1157.63. Using y = a times b to the t: 1157.63 = 1000 times b cubed. b cubed = 1.15763. b = (1.15763) to the (1/3) approximately 1.05. Annual growth rate approximately 5 percent.

## Negative Exponential: Decay Models in Depth

Exponential decay is as important as exponential growth on the Digital SAT, and it has a few specific features worth detailed coverage.

The structure: for decay, b is between 0 and 1. The model y = a times b to the power x produces a quantity that decreases but never reaches zero (it approaches zero asymptotically). This is a key distinction from linear decay, where the quantity can reach zero (and even become negative if the model is extended beyond the physical situation).

Real-world decay contexts:

Radioactive decay: a substance loses a fixed percentage of its mass per unit time. "Carbon-14 has a half-life of approximately 5,730 years." The half-life is the time for the quantity to halve, so b to the power (5730) = 0.5, giving b = 0.5 to the power (1/5730) approximately 0.99988.

Depreciation: a car loses 15 percent of its value each year. V(t) = initial value times (0.85) to the power t. After 10 years: V(10) = initial value times (0.85) to the 10 approximately 0.197 times initial value. The car retains about 19.7 percent of its original value.

Drug concentration: a medication is eliminated from the bloodstream at 30 percent per hour. C(t) = initial concentration times (0.70) to the power t. After 5 hours: C(5) = initial times (0.70) to the 5 approximately 0.168 times initial. About 16.8 percent remains.

The half-life: the time T at which a decaying quantity reaches half its initial value. Setting a times b to the T = a/2 gives b to the T = 0.5. Solving: T = log(0.5) / log(b) = ln(0.5) / ln(b). For b = 0.85 (15 percent annual decay): T = ln(0.5) / ln(0.85) approximately 4.27 years.

The Digital SAT tests half-life in questions like: "A substance decays according to M(t) = 200 times (0.75) to the power t. Approximately how many years does it take for the mass to reach 100 grams?" 100 = 200 times (0.75) to the t. (0.75) to the t = 0.5. t = ln(0.5) / ln(0.75) approximately 2.41 years.

## Graphical Interpretation of Linear and Exponential Models

The Digital SAT tests linear vs exponential model identification not only from tables and verbal descriptions but also from graphs. Being able to look at a graph and immediately classify the function type is a high-value visual skill.

Linear model graph: a straight line. Constant slope throughout. Can be increasing (positive slope), decreasing (negative slope), or flat (zero slope). The y-intercept is where the line crosses the y-axis.

Exponential growth graph: a curve that starts nearly flat and becomes increasingly steep as x increases. The curve is always concave up (opening upward). The y-intercept is at x = 0 (y = a). The curve approaches the x-axis but never reaches it for negative x (as the function approaches zero asymptotically from above).

Exponential decay graph: a curve that starts steep and flattens as x increases. Always concave up. Approaches the x-axis asymptotically without touching it. For y = a times b to the power x with 0 less than b less than 1: y starts at a (when x = 0) and decreases toward zero.

The visual distinction: if the graph is a straight line, linear. If the graph curves and the curve is concave up, exponential. If the data points on a scatter plot fall close to a straight line, linear model is appropriate. If the data points follow an upward or downward curve that is consistent with concave-up curvature, exponential model is appropriate.

A specific Digital SAT question type: "Which of the following graphs could represent an exponential decay function?" Identify the graph that shows a decreasing, concave-up curve that approaches but never touches the horizontal axis.

## The Relationship Between Linear and Exponential in Tables: Side-by-Side Analysis

Understanding both models simultaneously helps in questions that present a table and ask students to choose between them. A side-by-side comparison reinforces why the two-test is so effective.

For x = 0, 1, 2, 3, 4:

Linear example (y = 5x + 10): y = 10, 15, 20, 25, 30.
First differences: 5, 5, 5, 5. Constant. Linear confirmed.
Ratios: 15/10 = 1.5, 20/15 = 1.33, 25/20 = 1.25, 30/25 = 1.20. Decreasing. Not exponential.

Exponential example (y = 10 times 1.5 to the power x): y = 10, 15, 22.5, 33.75, 50.625.
First differences: 5, 7.5, 11.25, 16.875. Increasing. Not linear.
Ratios: 15/10 = 1.5, 22.5/15 = 1.5, 33.75/22.5 = 1.5, 50.625/33.75 = 1.5. Constant at 1.5. Exponential confirmed.

Note that at x = 0 and x = 1, both models give y = 10 and y = 15. After this first step, they diverge: the linear model adds 5 each time, while the exponential model multiplies by 1.5 each time, producing larger and larger increases.

This side-by-side comparison reveals why two data points alone cannot distinguish a linear from an exponential model: any two points are consistent with infinitely many functions. At least three points are needed to begin distinguishing, and four or more give a clearer pattern.

## Writing Exponential Models From Context: A Step-by-Step Protocol

Many Digital SAT questions present a verbal scenario and ask for the exponential model. A four-step protocol handles all variants.

Step one: identify the initial value a. This is the value of y when x = 0, usually stated as the "starting" or "initial" amount.

Step two: identify the growth or decay factor b. If a percent rate is given: b = 1 + r for growth (where r is the rate as a decimal) or b = 1 minus r for decay.

Step three: identify the independent variable x and its unit. Usually time (years, months, hours).

Step four: write y = a times b to the power x, labeling what y and x represent.

Example: "A population of 2,500 fish increases by 12 percent every 3 months. Write an exponential function P(t) for the population after t months."

Step one: a = 2,500 (initial population).
Step two: 12 percent increase every 3 months means b = 1.12 for every 3-month period. For the exponent in terms of months: the exponent becomes t/3 (so that when t = 3, the exponent is 1, giving one growth period).
Step three: x = t in months.
Step four: P(t) = 2,500 times (1.12) to the power (t/3).

Alternatively: find the monthly factor. The factor per month = (1.12) to the power (1/3) approximately 1.0385. Then P(t) = 2,500 times (1.0385) to the power t.

Both forms are equivalent. The form P(t) = 2,500 times (1.12) to the power (t/3) is more transparent in showing the 12 percent per 3-month relationship.

## The Doubling Time and Its Relationship to the Growth Factor

Doubling time is the most commonly tested special value for exponential growth models. It connects the growth factor b to a specific observable quantity (the time to double).

Definition: the doubling time T is the value of x such that y doubles: a times b to the T = 2a, which simplifies to b to the T = 2. Solving: T = ln(2) / ln(b) = log(2) / log(b).

For common growth rates:
b = 1.05 (5 percent per period): T = ln(2)/ln(1.05) approximately 14.2 periods.
b = 1.10 (10 percent per period): T = ln(2)/ln(1.10) approximately 7.27 periods.
b = 1.20 (20 percent per period): T = ln(2)/ln(1.20) approximately 3.80 periods.
b = 2 (doubles each period): T = 1 period (trivially).

The Rule of 70 approximation: for small growth rates r (as a percent), the doubling time approximately equals 70 / r. For 5 percent annual growth: doubling time approximately 70/5 = 14 years (close to the exact 14.2). For 10 percent: approximately 70/10 = 7 years (close to 7.27). This approximation is useful for quick estimation.

The Digital SAT tests doubling time in questions like: "A population model is given by P(t) = 500 times (1.08) to the power t. Approximately how many years does it take for the population to double?" Using the Rule of 70: approximately 70/8 = 8.75 years. Exact: ln(2)/ln(1.08) approximately 9.0 years.

## When the Independent Variable Is Not Time

Linear and exponential models appear with a variety of independent variables, not only time. The same rules apply regardless of what x represents.

Area-based models: "The production cost per item decreases by $0.50 for every additional unit produced." This is a linear model in x = number of units produced.

Distance-based models: "The pressure of the atmosphere decreases by 12 percent for each kilometer of altitude gained." This is an exponential decay model in x = altitude in km.

Count-based models: "Each additional employee generates $3,000 in revenue per year for the company." This is a linear model in x = number of employees.

Biological models: "A species of plant produces 50 percent more seeds than the previous generation for each year of adaptation." This is an exponential growth model in x = generations.

On the Digital SAT, these non-time contexts do not change the underlying mathematics. The two-test, the translation vocabulary, and the model form (y = mx + b or y = a times b to the power x) all apply identically regardless of what x represents physically. The only adjustment: the interpretation of the slope or growth factor must use the correct units from the context.

## Real Data and Model Choice: The Statistical Perspective

In real-world applications, data rarely fits either model perfectly. The Digital SAT acknowledges this through "approximately linear" or "approximately exponential" questions. Understanding the statistical perspective helps in these questions.

For a scatter plot of real data, the appropriate model type is chosen by looking at the overall shape of the data points:

If the scatter plot appears to follow a straight-line trend (with random variation around a line), a linear model is appropriate.

If the scatter plot appears to follow a curved trend that is consistent with a concave-up curve (similar to an exponential curve), an exponential model is appropriate.

The tightness of fit (how closely the data clusters around the model) determines how well the model works. A high correlation (data close to the model) means the model is a good fit. A low correlation (data scattered widely around the model) means the model is a poor fit.

For the Digital SAT, "which model best fits the data?" is answered by comparing the differences (for linear) and ratios (for exponential) and identifying which is more nearly constant. The model with more nearly constant values is the better fit.

## Extended Examples: Parameter Finding From Data Points

The hardest linear-vs-exponential questions on the Digital SAT require finding the model parameters from two or more given data points. This appears more often for exponential models (where the algebra is less familiar) than for linear models.

Finding linear model parameters from two points: slope m = (y2 minus y1) / (x2 minus x1), then b = y1 minus m times x1. This is standard slope-intercept calculation.

Finding exponential model parameters from two points: the ratio method eliminates a.

Given (x1, y1) and (x2, y2) on y = a times b to the power x:
y1 = a times b to the x1.
y2 = a times b to the x2.
Dividing: y2 / y1 = b to the power (x2 minus x1).
Solve for b: b = (y2/y1) to the power (1/(x2 minus x1)).
Then find a from y1 = a times b to the x1: a = y1 / (b to the x1).

Example: an exponential function passes through (2, 12) and (5, 96).

y2/y1 = 96/12 = 8. x2 minus x1 = 5 minus 2 = 3. b = 8 to the power (1/3) = 2.
a = 12 / (2 to the 2) = 12 / 4 = 3.
Model: y = 3 times 2 to the power x.

Verify: at x = 2: y = 3 times 4 = 12. At x = 5: y = 3 times 32 = 96. Correct.

This ratio method is the standard approach for finding exponential model parameters from data and appears in both the SAT Math section directly and as a component of harder modeling problems.

## Continuous vs Discrete Exponential Growth

The Digital SAT tests the distinction between discrete exponential models (where growth happens in distinct steps, like annually) and continuous growth (where growth happens at every instant, like bacterial population growth in ideal conditions).

Discrete model: y = a times b to the power t, where t takes integer values (years, months, etc.) and b is the per-period multiplier.

Continuous model: y = a times e to the power (rt), where r is the continuous growth rate and e is Euler's number (approximately 2.718). This form appears less frequently on the Digital SAT but is worth recognizing.

Converting between forms: a times e to the power (rt) = a times (e to the r) to the power t. So the effective per-period growth factor is b = e to the r. For r = 0.05 (5 percent continuous rate): b = e to the 0.05 approximately 1.0513. This is slightly more than 1.05 (the discrete 5 percent annual rate) because continuous compounding compounds at every instant.

For the Digital SAT, most exponential model questions use the discrete form y = a times b to the power t. The continuous form appears primarily in physics or finance contexts that are labeled as such.

## Connecting Exponential Models to the Function Notation

On the Digital SAT, exponential models are frequently presented using function notation: P(t) = ..., V(t) = ..., C(x) = .... The function notation emphasizes that the model is a specific rule relating input and output.

Function evaluation: P(5) means the value of P when t = 5. For P(t) = 800 times (1.06) to the t: P(5) = 800 times (1.06) to the 5 = 800 times 1.338 = 1070.4.

Function interpretation: "What does P(10) represent in context?" means asking what the output means when t = 10 (the population/value/quantity 10 periods after the starting point).

Function equation solving: "For what value of t does P(t) = 1600?" Set 800 times (1.06) to the t = 1600. (1.06) to the t = 2. t = ln(2) / ln(1.06) approximately 11.9 periods. The quantity doubles in approximately 11.9 periods.

Composition with linear functions: sometimes the Digital SAT presents a model like V(t) = 5000 times (0.80) to the power (t minus 2) for t greater than or equal to 2. This is an exponential model shifted horizontally: the decay starts at t = 2 rather than t = 0. The value at t = 2 is V(2) = 5000 times (0.80) to the 0 = 5000 (the starting value of the decay).

## Preparing for Model Questions: A Systematic Drill Protocol

The most efficient preparation for linear-vs-exponential model questions follows a three-stage drill protocol that builds each skill layer before combining them.

Stage one: two-test drills. Practice applying the two-test (differences AND ratios) to ten data tables per session. The goal is to compute both tests automatically and identify the model type in under 30 seconds per table. Include tables where neither test gives a constant (to practice recognizing non-standard data).

Stage two: translation drills. Take ten verbal scenarios and write the model equation for each without solving any specific question. Focus on identifying whether "per" or "percent" language signals linear vs exponential, and correctly computing b from a given percentage rate. Verify each model by checking that it produces correct values at t = 0 and t = 1.

Stage three: parameter interpretation drills. Take ten given model equations (mix of linear and exponential) and write a two-sentence interpretation for each parameter in context. For y = 350 times (0.92) to the t: "The initial value is 350, representing the starting amount. The decay factor is 0.92, meaning the quantity decreases by 8 percent per period." This drill builds the interpretive vocabulary needed for context-based questions.

Combining stages: after mastering each stage, practice complete model problems that require all three skills: identify the model type, write the equation, interpret the parameters. Ten complete problems per session bring all the skills together under realistic time pressure.

## The Broader Role of Linear vs Exponential in SAT Data Analysis

Linear and exponential model questions are a subset of the broader data analysis and modeling content that appears throughout the Digital SAT. Understanding where these questions fit helps prioritize preparation.

Within the Problem Solving and Data Analysis domain: linear and exponential models appear alongside scatter plots (the model line or curve fitted to data), two-way tables (categorical data, not directly related to linear/exponential), and summary statistics (mean, median, standard deviation). The model identification skill transfers to scatter plot questions that show a curved vs straight line of best fit.

Within the Advanced Math domain: linear and exponential models appear alongside function analysis questions. The exponential function y = a times b to the power x is a specific case of the general function studied in the functions domain, and model questions in this context may ask about domain, range, transformations, or algebraic properties of the model.

The connection to the algebra domain: finding model parameters from data points is an algebraic skill (setting up and solving equations). The slope calculation for linear models is the same as the slope-formula skill. The ratio method for exponential parameters is an application of exponent rules.

Mastering linear-vs-exponential models as a self-contained unit reinforces skills across three domains simultaneously: data analysis (reading and interpreting data tables), algebra (finding parameters from given values), and advanced math (function notation and exponential function properties).

## The Eight Most Common Digital SAT Model Question Formats

Digital SAT linear and exponential model questions appear in eight specific formats. Recognizing each format immediately routes thinking to the correct approach.

Format one: "Which function type best represents the data?" Given a table, apply the two-test. Constant differences = linear, constant ratios = exponential.

Format two: "What is the value of f(5)?" Given a model function, substitute x = 5 and compute. This is pure function evaluation with no modeling judgment needed.

Format three: "What does the value 1.08 represent in f(t) = 200 times 1.08 to the t?" This is a parameter interpretation question. Answer: 1.08 is the annual growth factor, meaning the quantity increases by 8 percent per year.

Format four: "Write a function that models this scenario." Identify the model type from the verbal description, find a (initial value) and b (growth/decay factor or slope), and write the function.

Format five: "For what value of t does the population reach 500?" Set the function equal to 500 and solve. For linear: straightforward algebra. For exponential: requires logarithms (or a Desmos intersection), which the Digital SAT handles by providing answer choices that can be verified by substitution.

Format six: "Which model predicts a greater value when t = 100?" Evaluate both models at t = 100 and compare. For exponential vs linear, use the "exponential dominates for large t" principle to identify the answer without necessarily computing exact values.

Format seven: "A graph shows data. Which equation could model the data?" Identify the graph's shape (straight line = linear, concave-up curve = exponential growth, concave-down curve = exponential decay) and match to the equation form.

Format eight: "Given that f(2) = 16 and f(5) = 128, find f(0)." Use the ratio method to find b (128/16 = 8 = b to the 3, so b = 2), then find a from f(2) = a times 2 squared = 16, so a = 4. Check: f(0) = 4 times 1 = 4.

These eight formats cover every linear-vs-exponential question type that has appeared on Digital SAT administrations. Preparing a specific response protocol for each format eliminates uncertainty about what to do when the question is encountered.

## A Complete Pre-Test Reference for Linear and Exponential Models

For a concise pre-test review, here is every fact and formula needed for linear-vs-exponential model questions.

IDENTIFICATION: Constant differences in a table = linear. Constant ratios in a table = exponential. Fixed amount per period = linear. Percentage per period = exponential.

LINEAR MODEL: y = mx + b. m is the rate of change (slope, units per x-unit). b is the initial value (value when x = 0).

EXPONENTIAL MODEL: y = a times b to the power x. a is the initial value (value when x = 0). b is the growth factor (b greater than 1) or decay factor (0 less than b less than 1). Growth rate = (b minus 1) times 100 percent. Decay rate = (1 minus b) times 100 percent.

PARAMETER FINDING FROM TWO POINTS - LINEAR: slope m = (y2 minus y1) / (x2 minus x1). Initial value b = y1 minus m times x1.

PARAMETER FINDING FROM TWO POINTS - EXPONENTIAL: growth factor b = (y2/y1) to the power (1/(x2 minus x1)). Initial value a = y1 / (b to the x1).

DOMINANCE: exponential always exceeds linear for large enough x when b is greater than 1.

PIECEWISE LINEAR: constant rate on each interval, continuity at breakpoints.

DECAY HALF-LIFE: T = ln(0.5) / ln(b) where b is the decay factor.

COMPOUNDING: y = a times (1 + r/n) to the power (nt) for nominal rate r compounded n times per year.

This ten-item reference covers every concept tested in linear-vs-exponential model questions. Reviewing it for five minutes before the test activates all relevant memory and reduces setup time on the first model question encountered.

## Why Linear vs Exponential Is Among the Most Productive Preparation Topics

The linear vs exponential distinction produces a high return on preparation time for three reasons.

First, the question type is predictable. The two-test, the translation vocabulary, and the parameter interpretation rules appear consistently across administrations. A student who has mastered these tools will encounter no surprises in this question category.

Second, the tools transfer widely. The two-test applies to scatter plot questions, the slope interpretation applies to all linear function questions, and the growth factor interpretation applies to all exponential function questions. Preparing linear vs exponential models simultaneously prepares adjacent question types.

Third, the preparation is efficient. The complete toolkit can be learned and internalized in two focused study hours. For two to three questions per administration, this investment produces a highly favorable payoff-per-hour ratio compared to harder topics that require much longer preparation for similar question counts.

Students who have not previously distinguished clearly between addition-based and multiplication-based growth will find that this distinction, once internalized, immediately clarifies a wide range of real-world reasoning situations beyond the SAT. The concept that percentage growth is fundamentally different from dollar-amount growth is one of the most practically important mathematical ideas in personal finance, public health, and population biology. The SAT is measuring a genuinely important skill, and preparing for it produces understanding that extends well beyond test day.

## Summary: The Core Framework for Linear vs Exponential Model Mastery

The complete linear-vs-exponential framework has five elements, each building on the previous.

Element one: the distinction. Addition = linear. Multiplication = exponential. This is the conceptual foundation.

Element two: the two-test. Differences = linear. Ratios = exponential. This is the table identification tool.

Element three: the model forms. y = mx + b for linear (m is rate, b is initial). y = a times b to the power x for exponential (a is initial, b is factor). These are the algebraic representations.

Element four: the translation vocabulary. Fixed amount signals linear. Percentage or factor signals exponential. This is the verbal identification tool.

Element five: the interpretation vocabulary. For linear: "m dollars per unit," "b is the initial amount." For exponential: "b = 1.08 means 8 percent growth per period," "a is the starting value." This is the context-reading skill.

All five elements work together as a unified system. Every linear-vs-exponential question on the Digital SAT can be resolved by combining the appropriate elements from this framework: identify the model type (elements one and two), write the model (element three), or interpret the model's parameters (elements four and five).

## Modeling With Technology: Using Desmos Effectively for Model Questions

The Digital SAT's built-in Desmos calculator is especially powerful for linear vs exponential model questions because it can graph functions, evaluate them at specific points, find intersections, and visually confirm which model type fits a dataset.

Plotting data points: Desmos allows entering data as a table. Type "x, y" in the first row, then enter each data point. The data points appear as dots on the graph. This visual allows instant comparison of whether the points follow a straight line (linear) or a curve (exponential).

Graphing candidate models: after plotting the data, graph a candidate linear function (y = mx + b) and adjust m and b using sliders until the line passes through the data points. Repeat for an exponential function (y = a times b to the power x) with sliders for a and b. The model that fits the data points better is the appropriate model type.

Finding intersections: to find where two model functions give the same value, graph both functions and click on the intersection point. Desmos displays the coordinates of the intersection, giving the x-value where the two models agree and allowing determination of which model is greater beyond that point.

Function evaluation: to find f(5) for any model function, type the function in Desmos and evaluate at x = 5 either by tracing the graph or by entering the expression f(5) directly.

Regression features: Desmos can fit a linear regression line (type "y1 ~ mx1 + b" in the expression window, where y1 and x1 are data column labels) or an exponential regression curve (type "y1 ~ a times b to the x1"). Desmos outputs the best-fit values of m and b (or a and b) and displays the R-squared value, which indicates how well the model fits the data.

For Digital SAT purposes, the most efficient use of Desmos for model questions: plot the data (if a table is given), graph both a linear and exponential model, and identify which fits better visually. This visual approach is often faster than computing the two-test by hand, though knowing the two-test remains valuable for non-calculator contexts and for understanding why one model fits better.

## Worked Examples Extended: Five More Practice Problems

The following five additional problems cover question formats and difficulty levels not fully addressed in the initial worked examples.

Practice problem one (medium): "A savings account has a balance of $500. It earns $25 interest per month. Write a linear function B(t) for the balance after t months and find the balance after 18 months."

Initial value a = 500, monthly addition m = 25. B(t) = 500 + 25t. At t = 18: B(18) = 500 + 25(18) = 500 + 450 = $950.

Practice problem two (medium): "A colony of 800 bacteria triples every 4 hours. Write an exponential function P(t) for the population after t hours."

Initial value = 800. Tripling every 4 hours means growth factor = 3 for every 4 hours. Exponent = t/4. P(t) = 800 times 3 to the power (t/4).

At t = 4: P(4) = 800 times 3 = 2,400. At t = 8: P(8) = 800 times 9 = 7,200. Confirmed.

Practice problem three (hard): "The table below shows the value of an investment over time. Determine whether the relationship is linear or exponential and find the function that models the data."

x = 0, 1, 2, 3; y = 1600, 1200, 900, 675.

Differences: 1200 minus 1600 = minus 400, 900 minus 1200 = minus 300, 675 minus 900 = minus 225. Not constant. Not linear.

Ratios: 1200/1600 = 0.75, 900/1200 = 0.75, 675/900 = 0.75. Constant at 0.75. Exponential with decay factor 0.75 and initial value 1600.

Function: y = 1600 times (0.75) to the power x. This represents 25 percent annual depreciation (since 1 minus 0.75 = 0.25).

Practice problem four (hard): "Employee A's salary starts at $60,000 and increases by $4,000 per year. Employee B's salary starts at $45,000 and increases by 6 percent per year. After how many years (approximately) will Employee B's salary first exceed Employee A's?"

A(t) = 60,000 + 4,000t. B(t) = 45,000 times (1.06) to the t.

Testing: t = 10: A = 100,000; B = 45,000 times (1.06) to the 10 = 45,000 times 1.791 = 80,595. A leads.
t = 20: A = 140,000; B = 45,000 times (1.06) to the 20 = 45,000 times 3.207 = 144,315. B leads.
t = 19: A = 136,000; B = 45,000 times (1.06) to the 19 approximately 136,240. B barely exceeds A.

Answer: after approximately 19 years, Employee B's salary first exceeds Employee A's.

Practice problem five (hard module 2): "The function P(t) = 3000 times (1 + r) to the t models a population, where t is years. If the population is 3630 after 2 years, find r and use it to determine the population after 5 years."

At t = 2: 3630 = 3000 times (1 + r) squared. (1 + r) squared = 3630/3000 = 1.21. 1 + r = root(1.21) = 1.1. r = 0.1 = 10 percent.

Model: P(t) = 3000 times (1.1) to the t. At t = 5: P(5) = 3000 times (1.1) to the 5 = 3000 times 1.61051 approximately 4,832 people.

These five practice problems span every major format: writing a linear model, writing an exponential model with non-unit time periods, identifying and writing an exponential decay model from a table, finding a crossover point between linear and exponential, and finding a parameter from given data then evaluating the model.

---

## Frequently Asked Questions

**Q1: What is the key difference between a linear and an exponential model?**

A linear model has a constant rate of change: the same amount is added to y for each unit increase in x. An exponential model has a constant multiplicative factor: y is multiplied by the same value for each unit increase in x. In a data table, constant first differences (y2 minus y1 = y3 minus y2) signal linear; constant ratios (y2/y1 = y3/y2) signal exponential. The conceptual distinction: linear models describe situations where the same quantity is added each period regardless of the current total (a $500 monthly payment on a debt). Exponential models describe situations where the change is proportional to the current total (a 5 percent monthly interest charge that grows as the debt grows). This proportionality is the defining feature that separates exponential from linear. A powerful memory aid: linear comes from "line," and a linear model has a straight-line graph. Exponential comes from "exponent," and an exponential model has x as an exponent in the formula. These two naming conventions reflect the core structural distinction between the two model types.

**Q2: What is the two-test for identifying model type from a data table?**

Compute both the first differences (subtract consecutive y-values) and the ratios (divide consecutive y-values). If the differences are constant, the model is linear. If the ratios are constant, the model is exponential. If neither is constant, the data does not fit a simple linear or exponential model. Always compute both before deciding. A systematic approach: label your work. Write "Differences:" and compute each one, then write "Ratios:" and compute each one. Looking at one set without the other risks missing the pattern. Computing both takes under 30 seconds for a four-row table and provides definitive evidence for the model type.

**Q3: What are the formulas for linear and exponential models?**

Linear: y = mx + b, where m is the slope (rate of change) and b is the y-intercept (initial value). Exponential: y = a times b to the power x, where a is the initial value (value when x = 0) and b is the growth or decay factor. Two derived formulas worth knowing: for exponential growth, y = a times (1 + r) to the power x where r is the per-period rate as a decimal. For exponential decay, y = a times (1 minus r) to the power x. The growth factor b is (1 + r) and the decay factor is (1 minus r). Keeping this connection between b and the percent rate r explicit prevents the common error of using r directly as b (forgetting the "1 +"). A practical comparison of the two forms: y = 1000 times 0.85 to the power t and y = 1000 times (1 minus 0.15) to the power t are identical (since b = 0.85 = 1 minus 0.15 = 1 minus r with r = 0.15). The first form (using b directly) is more compact; the second form (using 1 minus r) makes the decay rate of 15 percent explicit. On the Digital SAT, both forms appear and both must be readable.

**Q4: How do I identify a linear vs exponential scenario from a word problem?**

Linear signals: "increases by $X per year," "adds X units per period," "constant rate," "per unit." The change is a fixed amount regardless of the current value. Exponential signals: "increases by X percent per year," "doubles every period," "grows by a factor of," "percent interest." The change is proportional to the current value. A diagnostic question to ask about any scenario: "Does the amount of change stay the same or grow over time?" If it stays the same (same dollars added each year), linear. If it grows (more dollars added each year as the balance grows), exponential. This question reliably distinguishes the two model types even when the verbal phrasing does not use obvious signal words. Tricky phrasings to watch for: "earns 3 percent on top of the original investment" sounds exponential (percent) but is actually linear if "original investment" means the percent always applies to the same fixed starting amount, not the current value. Always identify whether the percentage applies to the original amount (linear) or the current amount (exponential).

**Q5: What does the growth factor b represent in an exponential model?**

The growth factor b is the multiplier applied to y for each one-unit increase in x. If b is greater than 1, the model grows (b = 1.08 means 8 percent growth per period). If b is between 0 and 1, the model decays (b = 0.85 means 15 percent decay per period, since 1 minus 0.85 = 0.15). A quick parameter reading guide: b = 1.0X means X percent growth. b = 0.9X means (1 minus 0.9X) = (10 minus X) percent decay. For b = 0.97: 3 percent decay. For b = 1.15: 15 percent growth. For b = 0.80: 20 percent decay. Practicing this instant conversion from b to percent rate (and back) builds the interpretive fluency needed for parameter questions.

**Q6: How do I find the growth or decay rate from the growth factor?**

For growth (b greater than 1): growth rate = (b minus 1) times 100 percent. For b = 1.07: growth rate = 7 percent. For decay (b between 0 and 1): decay rate = (1 minus b) times 100 percent. For b = 0.93: decay rate = 7 percent. The reverse direction: given a growth rate of r percent, the growth factor is b = 1 + r/100. Given a decay rate of r percent, the decay factor is b = 1 minus r/100. Both conversions are single-step arithmetic. Practice until these conversions are instantaneous: "8 percent growth means b = 1.08," "15 percent decay means b = 0.85."

**Q7: For large values of x, which always dominates: linear or exponential?**

For any exponential function with growth factor b greater than 1 and any linear function, the exponential function will eventually be greater for large enough x, regardless of the initial values or slope. Exponential growth always eventually dominates linear growth because multiplication outpaces addition at large scales. The rate of eventual overtaking depends on b: a large growth factor (b = 3) will overtake a linear function sooner than a small growth factor (b = 1.01), but both will eventually dominate. For Digital SAT questions asking "for large values of t, which model predicts a greater value?", the exponential model is always the answer when its base is greater than 1, without needing to compute a specific crossover point.

**Q8: What is a piecewise linear model?**

A piecewise linear model has different constant rates of change over different intervals of the input variable. Each piece is a separate linear function with its own slope. The graph is a series of connected line segments. Real-world examples: utility pricing with tiered rates, overtime pay rates, shipping costs that change above certain weight thresholds. The key requirement: continuity at each breakpoint. The formula for the first piece, evaluated at the breakpoint, must equal the starting value of the second piece, evaluated at the breakpoint. If there is a jump discontinuity at the breakpoint (the two pieces give different values at that x), the model has an error.

**Q9: How do I write a piecewise linear model?**

Identify the breakpoints (where the rate changes) and the rate for each interval. Write a separate linear formula for each interval: f(x) = formula1 for x in [a, b], f(x) = formula2 for x in [b, c], etc. Ensure continuity at each breakpoint: the formula before the breakpoint and the formula after should give the same value at the breakpoint x. For the second and later pieces, always write the formula as (accumulated total from prior pieces) + (new rate) times (x minus breakpoint). This structure automatically ensures continuity. For example, if the first piece gives 150 at the breakpoint and the second piece has a rate of 20: second piece = 150 + 20(x minus breakpoint).

**Q10: If a data table doesn't perfectly fit either model, how do I choose?**

Compute both differences and ratios. Whichever is more nearly constant indicates the better-fitting model. If differences have small variation but ratios vary widely, linear is better. If ratios are approximately constant but differences vary widely, exponential is better. The model with the more stable values from the two-test is the better fit. A quantitative approach when both are nearly constant: compute the range (max minus min) of the differences and the range of the ratios. Compare these ranges proportionally. If the ratios vary by 0.01 around a value of 1.5 (a variation of about 0.7 percent) while the differences vary by 5 around a value of 20 (a variation of 25 percent), the ratios are far more stable, indicating an exponential model.

**Q11: How do I interpret the initial value in a model?**

The initial value is the value of the dependent variable when the independent variable equals zero. In y = 3x + 7: the initial value is 7 (the value when x = 0). In y = 500 times (0.95) to the power t: the initial value is 500 (the starting amount before any decay). Always specify what the independent variable represents (usually time) and what the initial value means in context (the amount at time zero). A common interpretation question: "What does the value 500 represent in P(t) = 500 times (0.95) to the power t?" A complete answer states both the numerical value (500) and its contextual meaning ("the initial population of 500 at time t = 0" or "the population at the start of the study"). Both parts are needed for a correct interpretation.

**Q12: What is the difference between linear growth of X per year and exponential growth of X percent per year?**

Linear growth of X per year adds the same dollar (or unit) amount X to the total each year, regardless of the current total. Exponential growth of X percent per year adds X percent of the CURRENT total each year, so the actual amount added increases as the total grows. In the long run, even a small percentage exponential rate will far outpace any fixed-amount linear rate. A numerical comparison: a $100 annual increase on a $1,000 starting balance (linear, 10 percent of original) vs a 10 percent annual compounded growth on the same $1,000. In year one, both add $100. In year two, linear adds $100 (same as before), while exponential adds 10 percent of $1,100 = $110. By year 10, linear has added a total of $1,000; exponential has grown to $1,000 times (1.10) to the 10 = $2,594, adding $1,594.

**Q13: How do I find the parameters of an exponential model from two data points?**

Write the exponential model y = a times b to the power x. Substitute each data point to get two equations in two unknowns (a and b). Divide the two equations to eliminate a: y2/y1 = b to the power (x2 minus x1). Solve for b: b = (y2/y1) to the power (1/(x2 minus x1)). Then find a from one of the original equations. Common error: using the wrong base for the power. The exponent in the formula for b is 1/(x2 minus x1), not 1/(x2). Always use the DIFFERENCE of the x-values as the denominator. Verification: substitute both original data points into the final model equation and confirm they are satisfied exactly.

**Q14: How does compounding affect exponential models?**

Compounding at different frequencies changes the effective growth factor per year. For a nominal annual rate r compounded n times per year over t years: final value = a times (1 + r/n) to the power (nt). Monthly compounding (n = 12) gives a slightly higher effective rate than annual compounding (n = 1) because interest earns interest within the year. The formula (1 + r/n) to the power n gives the effective annual growth factor. For the Digital SAT, compounding questions typically specify the frequency explicitly. A question might give a quarterly rate and ask for the value after a certain number of years, requiring the student to correctly set up the exponent as 4t (four quarters per year times t years) rather than t.

**Q15: What does it mean when the Digital SAT asks for the "percent increase per year" from an exponential model?**

The percent increase per year is the growth rate expressed as a percentage. For the model y = a times b to the power t: percent increase per year = (b minus 1) times 100 percent. For V(t) = 1000 times (1.06) to the power t: percent increase per year = (1.06 minus 1) times 100 = 6 percent per year. A harder variant: "What is the percent increase per quarter if the model is V(t) = 1000 times (1.06) to the power t where t is years?" The quarterly factor is (1.06) to the power (1/4) approximately 1.01467. Percent increase per quarter approximately 1.47 percent. This requires understanding that the annual factor raised to the 1/4 power gives the quarterly factor.

**Q16: How does the graph of a linear model differ from the graph of an exponential model?**

A linear model graphs as a straight line with constant slope. An exponential growth model graphs as an upward-curving curve that increases faster and faster. An exponential decay model graphs as a downward-curving curve that decreases but never reaches zero. The key visual distinction: if the graph is a straight line, the model is linear. If the graph curves (concave up for growth, concave down for decay), the model is exponential. Note that on a logarithmic scale (where the y-axis shows log(y) rather than y), an exponential function graphs as a straight line. This log-linear relationship is a mathematical property of exponential functions that can appear in graph-interpretation questions on the Digital SAT.

**Q17: How do I find when two models give the same value?**

Set the two model equations equal to each other and solve for x. For two linear models: mx + b = cx + d gives x = (d minus b) / (m minus c). For one linear and one exponential: set them equal and solve numerically or using Desmos, since there is no simple algebraic formula for the intersection of a line and an exponential curve. Desmos approach: graph both functions and look for the intersection point. The x-coordinate of the intersection is where both models give the same value. Use the Desmos click-on-graph feature to read the coordinates of the intersection point precisely. For Digital SAT questions asking "after how many years does model B exceed model A?", identify the intersection and determine which model is greater beyond that point.

**Q18: What does "the model is appropriate for values between x = 0 and x = 10" mean?**

This indicates the domain restriction of the model: the model only accurately represents the quantity for x-values in [0, 10]. Outside this range, the model may not be valid (the underlying relationship may change, or the data the model was based on does not extend beyond this range). Always apply the model only within its stated domain. A practical consequence: if the question asks for the predicted value at x = 15 and the model is stated to be appropriate only for x from 0 to 10, the model cannot reliably predict the value at x = 15. The Digital SAT sometimes asks about predictions outside the stated domain to test whether students understand this domain restriction.

**Q19: How do I handle an exponential model where the time unit and the exponent's unit differ?**

Adjust the exponent to match the model's unit. If a model doubles every 3 years and you want the formula in terms of years: the exponent should be t/3 (so the quantity doubles when t = 3). V(t) = a times 2 to the power (t/3). Alternatively, find the annual growth factor: 2 to the power (1/3) is the annual multiplier. V(t) = a times (2 to the 1/3) to the power t. Both forms are algebraically equivalent. The choice depends on which form is most natural for the given question. If the question asks about values at t = 3, 6, 9 years, the form with t/3 makes the calculation transparent (exponent becomes 1, 2, 3). If the question asks about annual values at t = 1, 2, 3, the per-year factor form is more direct.

**Q20: How many linear vs exponential model questions appear per Digital SAT and what is the most efficient preparation strategy?**

Linear vs exponential questions appear two to three times per administration, across both PSDA and Advanced Math. The most efficient preparation strategy: first, master the two-test (differences for linear, ratios for exponential) for data tables. Second, learn the translation dictionary (percent/factor signals exponential; fixed amount signals linear). Third, practice interpreting a and b in y = a times b to the power x in various real-world contexts. These three elements cover the complete linear-vs-exponential curriculum in approximately two focused study hours. The questions are highly predictable in structure, making this category one of the most efficiently prepared for the score impact it produces. For students who already understand the distinction conceptually but make errors on interpretive questions, targeted practice on the "what does 0.92 represent in this model?" question type builds the vocabulary precision that prevents interpretation errors on test day.
