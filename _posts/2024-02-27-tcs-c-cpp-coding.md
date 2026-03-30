---
layout: post
title: "TCS C/C++ Coding: Complete Solutions Set"
page_title: "TCS Coding Questions Using C and C++ - Command Line Programming, Solutions, and Compiler-Specific Guide"
date: 2024-02-27
categories: ["Industry"]
tags: ["TCS C coding", "TCS C++ coding", "TCS C programming", "TCS command line", "TCS coding solutions C"]
excerpt: "Master TCS coding with C and C++. Command line programming explained, compiler quirks covered, and full solution set provided."
image: "/assets/images/blog/blog-59.webp"
reading_time: 60
author: "Insight Crunch Team"
last_updated: 2026-03-30
---
C and C++ have historically been the most widely used languages in TCS coding rounds, and they remain the dominant choice for experienced competitive programmers sitting the NQT. The TCS iON platform runs a GCC-type compiler, which means standard C99/C11 and C++14/C++17 code compiles cleanly. But there is one aspect of TCS coding that catches unprepared candidates completely off guard: command line argument input. While most candidates have practised programs that use `scanf` or `cin` for input, TCS problems frequently pass input through command line arguments - a different reading method that requires knowing `argc`, `argv`, and `atoi`. This guide covers everything: the compiler environment, the command line input method explained from first principles, and a structured set of problems with complete solutions in both C and C++.

![TCS Guide](/assets/images/blog/blog-59.webp)

## The TCS iON Compiler Environment

### Compiler Type and Language Versions

TCS iON uses a GCC-based compiler. For C, this means C99 and C11 standards are supported. For C++, C++14 and C++17 are available. Practically speaking:

**In C:** You can use `//` single-line comments (C99 feature), variable-length arrays in some contexts, and the standard library headers (`stdio.h`, `stdlib.h`, `string.h`, `math.h`).

**In C++:** You can use the full STL (vectors, maps, sets, queues, stacks, algorithms), `auto` keyword, range-based for loops, lambda functions, and structured bindings (C++17). The `bits/stdc++.h` mega-header that includes all standard headers is available and widely used by competitive programmers.

### C vs C++ on TCS Platform: When to Use Which

**Use C when:**
- You want to demonstrate foundational programming knowledge in a Ninja interview context
- The problem is simple arithmetic, loops, and conditionals with no complex data structures
- You are more comfortable with C from your academic background

**Use C++ when:**
- The problem involves sorting (use `std::sort` instead of writing bubble sort)
- You need dynamic arrays (`vector<int>` instead of manual malloc)
- String operations are complex (C++ `string` class vs C character arrays)
- The problem has multiple test cases or complex input (STL containers simplify management)

**The practical recommendation:** If you are comfortable with C++, use it exclusively. The STL saves significant lines of code and reduces bugs. If you only know C, use C - a correct C solution is always better than a buggy C++ solution.

### Output Formatting: The Critical Rule

TCS iON evaluates output by exact string matching against expected output. Every character matters.

**Rules to follow:**
- Print exactly what the problem asks for. If the problem says "print the result", print the number and nothing else.
- Use `\n` for newlines (not `endl` in tight loops - `endl` flushes the buffer and is slower, though for TCS problems this rarely matters)
- No trailing spaces after the last value on a line
- No extra blank lines unless the problem specifies them
- If the problem shows sample output with a specific format, match it exactly

**Common output error:** Adding a descriptive label ("The answer is: 42") when the expected output is just "42". This causes a wrong answer even though the calculation is correct.

---

## The Most Important TCS-Specific Concept: Command Line Arguments

### Why Command Line Input Is Used

TCS's iON platform frequently passes test case inputs via command line arguments rather than standard input (keyboard/pipe). This design allows the platform to run automated test cases efficiently. A candidate who only knows `scanf` or `cin` will produce programs that compile but receive no input - causing wrong answers on all test cases.

### What Are Command Line Arguments?

When you run a program, you can pass values after the executable name:
```
./program 5 10 hello
```
Here `5`, `10`, and `hello` are command line arguments. Inside the program, these are accessible through the `main` function parameters `argc` and `argv`.

### The main() Signature with argc and argv

```c
int main(int argc, char *argv[]) {
    // argc = argument count (number of arguments including the program name)
    // argv = argument vector (array of strings)
    // argv[0] = program name
    // argv[1] = first argument
    // argv[2] = second argument
    // ...
}
```

**Critical facts:**
- `argc` always includes the program name itself. If you run `./program 5 10`, then `argc = 3` (program, 5, 10) and `argv[0] = "./program"`, `argv[1] = "5"`, `argv[2] = "10"`.
- All arguments arrive as **strings** (`char *`). The number `5` arrives as the string `"5"`. To use it as an integer, you must convert it.
- `argv` is an array of `char *` pointers - each element is a C string (null-terminated character array).

### The atoi() Function: String to Integer Conversion

`atoi` (ASCII to Integer) converts a C string to an integer:

```c
#include <stdlib.h>

int n = atoi(argv[1]);  // converts "42" to the integer 42
```

**How atoi works:** It reads digits from the string until it encounters a non-digit character. Leading whitespace is skipped. `atoi("42")` = 42. `atoi("-17")` = -17. `atoi("0")` = 0. `atoi("abc")` = 0 (no digits found).

**For floating point:** Use `atof()` (string to double). `atof("3.14")` = 3.14.

**For long integers:** Use `atol()` or `strtol()` for more precise control.

### Complete Command Line Input Example

```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    // Check that we received the expected number of arguments
    if (argc < 3) {
        printf("Usage: %s num1 num2\n", argv[0]);
        return 1;
    }

    int a = atoi(argv[1]);  // first argument as integer
    int b = atoi(argv[2]);  // second argument as integer

    printf("%d\n", a + b);
    return 0;
}
```

Running: `./program 15 27` → Output: `42`

### Reading Multiple Numbers from a Single Argument

Some TCS problems pass all numbers as space-separated values in a single argument wrapped in quotes, or as separate arguments. The pattern depends on the specific problem statement.

**Multiple separate arguments (most common):**
```
./program 3 7 2 8 5
```
Access: `argv[1]` = "3", `argv[2]` = "7", etc. Loop from `argv[1]` to `argv[argc-1]`.

**Array input as separate arguments:**
```c
int arr[100];
int n = argc - 1;  // number of integers
for (int i = 0; i < n; i++) {
    arr[i] = atoi(argv[i + 1]);
}
```

### When to Use scanf/cin vs Command Line Arguments

**Read the problem statement carefully.** If the problem says:
- "The input is given as command line arguments" → use `argc`/`argv`/`atoi`
- "Read from standard input" or shows a sample input below → use `scanf`/`cin`
- No explicit instruction → use command line arguments (safer default for TCS)

---

## Part 1: Command Line Programming Fundamentals

### Problem CL-1: Sum of Two Numbers

**Problem statement:** Write a program that accepts two integers as command line arguments and prints their sum.

**Input:** Two integers passed as command line arguments.
**Output:** Their sum on a single line.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int a = atoi(argv[1]);
    int b = atoi(argv[2]);
    printf("%d\n", a + b);
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int a = atoi(argv[1]);
    int b = atoi(argv[2]);
    cout << a + b << "\n";
    return 0;
}
```

**Common error:** Using `printf("%s\n", argv[1] + argv[2])` - you cannot add C strings with `+`. Convert to integers first.

### Problem CL-2: Sum of N Numbers

**Problem statement:** The first command line argument is N (count of numbers). The next N arguments are the numbers. Print their sum.

**Input:** `./program 5 3 7 2 8 5` (N=5, numbers are 3,7,2,8,5)
**Output:** `25`

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    int sum = 0;
    for (int i = 2; i <= n + 1; i++) {
        sum += atoi(argv[i]);
    }
    printf("%d\n", sum);
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    int sum = 0;
    for (int i = 2; i <= n + 1; i++) {
        sum += atoi(argv[i]);
    }
    cout << sum << "\n";
    return 0;
}
```

**Explanation:** `argv[1]` is N (the count), so the actual numbers start at `argv[2]` through `argv[n+1]`.

### Problem CL-3: Processing a String Argument

**Problem statement:** Accept a string as a command line argument. Print the string in reverse and its length.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char *s = argv[1];
    int len = strlen(s);

    // Print in reverse
    for (int i = len - 1; i >= 0; i--) {
        printf("%c", s[i]);
    }
    printf("\n%d\n", len);
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <string>
using namespace std;

int main(int argc, char *argv[]) {
    string s = argv[1];  // convert char* to C++ string
    int len = s.length();

    // Reverse using built-in
    string rev = string(s.rbegin(), s.rend());
    cout << rev << "\n" << len << "\n";
    return 0;
}
```

---

## Part 2: Basic Programs

### Problem B-1: Prime Number Check

**Problem statement:** Given a positive integer N, determine if it is prime. Print "Prime" or "Not Prime".

**C Solution (command line input):**
```c
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

int isPrime(int n) {
    if (n <= 1) return 0;
    if (n == 2) return 1;
    if (n % 2 == 0) return 0;
    for (int i = 3; i <= (int)sqrt((double)n); i += 2) {
        if (n % i == 0) return 0;
    }
    return 1;
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    printf("%s\n", isPrime(n) ? "Prime" : "Not Prime");
    return 0;
}
```

**Compile note for C:** When using `math.h`, compile with `-lm` flag: `gcc program.c -o program -lm`. TCS iON handles this automatically.

**C++ Solution:**
```cpp
#include <iostream>
#include <cmath>
#include <cstdlib>
using namespace std;

bool isPrime(int n) {
    if (n <= 1) return false;
    if (n == 2) return true;
    if (n % 2 == 0) return false;
    for (int i = 3; i <= (int)sqrt((double)n); i += 2) {
        if (n % i == 0) return false;
    }
    return true;
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    cout << (isPrime(n) ? "Prime" : "Not Prime") << "\n";
    return 0;
}
```

**Why sqrt(n) as the loop bound:** If N has a factor greater than sqrt(N), it must have a corresponding factor smaller than sqrt(N). So checking up to sqrt(N) is sufficient to find all factors.

**Edge cases:** 0 and 1 are not prime. 2 is the only even prime. Negative numbers are not prime.

### Problem B-2: Palindrome Number

**Problem statement:** Check if a given integer is a palindrome (reads the same forwards and backwards). Print "Palindrome" or "Not Palindrome".

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int isPalindrome(int n) {
    if (n < 0) return 0;  // negative numbers are not palindromes
    int original = n;
    int reversed = 0;

    while (n > 0) {
        int digit = n % 10;      // extract last digit
        reversed = reversed * 10 + digit;  // build reversed number
        n /= 10;                 // remove last digit
    }
    return original == reversed;
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    printf("%s\n", isPalindrome(n) ? "Palindrome" : "Not Palindrome");
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <cstdlib>
using namespace std;

bool isPalindrome(int n) {
    if (n < 0) return false;
    int original = n, reversed = 0;
    while (n > 0) {
        reversed = reversed * 10 + n % 10;
        n /= 10;
    }
    return original == reversed;
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    cout << (isPalindrome(n) ? "Palindrome" : "Not Palindrome") << "\n";
    return 0;
}
```

**Alternative C++ approach using strings:**
```cpp
#include <iostream>
#include <string>
#include <algorithm>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    string s = argv[1];
    string rev = s;
    reverse(rev.begin(), rev.end());
    cout << (s == rev ? "Palindrome" : "Not Palindrome") << "\n";
    return 0;
}
```

### Problem B-3: Fibonacci Series

**Problem statement:** Print the first N terms of the Fibonacci series.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);

    if (n <= 0) { printf("Invalid input\n"); return 1; }

    long long a = 0, b = 1;
    for (int i = 0; i < n; i++) {
        printf("%lld", a);
        if (i < n - 1) printf(" ");
        long long next = a + b;
        a = b;
        b = next;
    }
    printf("\n");
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    long long a = 0, b = 1;
    for (int i = 0; i < n; i++) {
        cout << a;
        if (i < n - 1) cout << " ";
        long long next = a + b;
        a = b;
        b = next;
    }
    cout << "\n";
    return 0;
}
```

**Why long long:** Fibonacci numbers grow exponentially. `int` overflows around F(46). `long long` handles up to approximately F(92).

### Problem B-4: Armstrong Number

**Problem statement:** Check if a number is an Armstrong number (sum of each digit raised to the power of the number of digits equals the number itself). Example: 153 = 1^3 + 5^3 + 3^3.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

int isArmstrong(int n) {
    int original = n;
    int digits = 0;
    int temp = n;

    // Count digits
    while (temp > 0) { digits++; temp /= 10; }

    // Sum of digits^(digit_count)
    int sum = 0;
    temp = n;
    while (temp > 0) {
        int d = temp % 10;
        sum += (int)pow((double)d, digits);
        temp /= 10;
    }
    return sum == original;
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    printf("%s\n", isArmstrong(n) ? "Armstrong" : "Not Armstrong");
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <cmath>
#include <cstdlib>
using namespace std;

bool isArmstrong(int n) {
    int original = n, digits = 0, temp = n;
    while (temp > 0) { digits++; temp /= 10; }
    int sum = 0;
    temp = n;
    while (temp > 0) {
        int d = temp % 10;
        sum += (int)pow((double)d, digits);
        temp /= 10;
    }
    return sum == original;
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    cout << (isArmstrong(n) ? "Armstrong" : "Not Armstrong") << "\n";
    return 0;
}
```

### Problem B-5: Factorial

**Problem statement:** Compute the factorial of N.

**C Solution (iterative):**
```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    unsigned long long fact = 1;
    for (int i = 2; i <= n; i++) {
        fact *= i;
    }
    printf("%llu\n", fact);
    return 0;
}
```

**C Solution (recursive):**
```c
#include <stdio.h>
#include <stdlib.h>

unsigned long long factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    printf("%llu\n", factorial(n));
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    unsigned long long fact = 1;
    for (int i = 2; i <= n; i++) fact *= i;
    cout << fact << "\n";
    return 0;
}
```

**Overflow note:** `unsigned long long` holds 20! = 2,432,902,008,176,640,000. For N > 20, you need big integer arithmetic (not available natively in C/C++).

### Problem B-6: Digit Sum and Digit Reversal

**Problem statement:** Given a number, print its digit sum and its reversed form.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    int original = n;
    int sum = 0, reversed = 0;

    while (n > 0) {
        int d = n % 10;
        sum += d;
        reversed = reversed * 10 + d;
        n /= 10;
    }
    printf("Digit sum: %d\nReversed: %d\n", sum, reversed);
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    int sum = 0, reversed = 0;
    int temp = n;
    while (temp > 0) {
        int d = temp % 10;
        sum += d;
        reversed = reversed * 10 + d;
        temp /= 10;
    }
    cout << "Digit sum: " << sum << "\nReversed: " << reversed << "\n";
    return 0;
}
```

---

## Part 3: String Programs

### Problem S-1: String Reversal

**Problem statement:** Reverse a given string.

**C Solution:**
```c
#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char *s = argv[1];
    int len = strlen(s);
    // In-place reversal
    for (int i = 0; i < len / 2; i++) {
        char temp = s[i];
        s[i] = s[len - 1 - i];
        s[len - 1 - i] = temp;
    }
    printf("%s\n", s);
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <string>
#include <algorithm>
using namespace std;

int main(int argc, char *argv[]) {
    string s = argv[1];
    reverse(s.begin(), s.end());
    cout << s << "\n";
    return 0;
}
```

### Problem S-2: Vowel and Consonant Count

**Problem statement:** Count the number of vowels and consonants in a string.

**C Solution:**
```c
#include <stdio.h>
#include <ctype.h>

int isVowel(char c) {
    c = tolower(c);
    return (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u');
}

int main(int argc, char *argv[]) {
    char *s = argv[1];
    int vowels = 0, consonants = 0;
    for (int i = 0; s[i] != '\0'; i++) {
        if (isalpha(s[i])) {
            if (isVowel(s[i])) vowels++;
            else consonants++;
        }
    }
    printf("Vowels: %d\nConsonants: %d\n", vowels, consonants);
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <string>
#include <cctype>
using namespace std;

int main(int argc, char *argv[]) {
    string s = argv[1];
    string vowelSet = "aeiouAEIOU";
    int vowels = 0, consonants = 0;
    for (char c : s) {
        if (isalpha(c)) {
            if (vowelSet.find(c) != string::npos) vowels++;
            else consonants++;
        }
    }
    cout << "Vowels: " << vowels << "\nConsonants: " << consonants << "\n";
    return 0;
}
```

### Problem S-3: Character Frequency

**Problem statement:** Find the frequency of each character in a string.

**C Solution:**
```c
#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char *s = argv[1];
    int freq[256] = {0};  // ASCII character array

    for (int i = 0; s[i] != '\0'; i++) {
        freq[(unsigned char)s[i]]++;
    }

    for (int i = 0; i < 256; i++) {
        if (freq[i] > 0) {
            printf("%c: %d\n", (char)i, freq[i]);
        }
    }
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <map>
#include <string>
using namespace std;

int main(int argc, char *argv[]) {
    string s = argv[1];
    map<char, int> freq;
    for (char c : s) freq[c]++;
    for (auto &p : freq) {
        cout << p.first << ": " << p.second << "\n";
    }
    return 0;
}
```

**C++ note:** Using `map<char, int>` automatically sorts output by character. The C version uses an array indexed by ASCII value, which also produces sorted output (ASCII order).

### Problem S-4: String Palindrome Check (Without Library)

**Problem statement:** Check if a string is a palindrome without using reverse() or similar library functions.

**C Solution:**
```c
#include <stdio.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char *s = argv[1];
    int len = strlen(s);
    int isPalin = 1;

    for (int i = 0; i < len / 2; i++) {
        if (s[i] != s[len - 1 - i]) {
            isPalin = 0;
            break;
        }
    }
    printf("%s\n", isPalin ? "Palindrome" : "Not Palindrome");
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <string>
using namespace std;

int main(int argc, char *argv[]) {
    string s = argv[1];
    int left = 0, right = (int)s.length() - 1;
    bool isPalin = true;
    while (left < right) {
        if (s[left] != s[right]) { isPalin = false; break; }
        left++; right--;
    }
    cout << (isPalin ? "Palindrome" : "Not Palindrome") << "\n";
    return 0;
}
```

---

## Part 4: Array Programs

### Problem A-1: Sort an Array

**Problem statement:** Given N numbers, sort them in ascending order.

**C Solution (Bubble Sort - for demonstration):**
```c
#include <stdio.h>
#include <stdlib.h>

void bubbleSort(int arr[], int n) {
    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            }
        }
    }
}

int compare(const void *a, const void *b) {
    return (*(int*)a - *(int*)b);
}

int main(int argc, char *argv[]) {
    int n = argc - 1;
    int arr[100];
    for (int i = 0; i < n; i++) arr[i] = atoi(argv[i + 1]);

    // Use qsort (stdlib.h) for efficiency - O(N log N)
    qsort(arr, n, sizeof(int), compare);

    for (int i = 0; i < n; i++) {
        printf("%d", arr[i]);
        if (i < n - 1) printf(" ");
    }
    printf("\n");
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <vector>
#include <algorithm>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int n = argc - 1;
    vector<int> arr(n);
    for (int i = 0; i < n; i++) arr[i] = atoi(argv[i + 1]);

    sort(arr.begin(), arr.end());

    for (int i = 0; i < n; i++) {
        cout << arr[i];
        if (i < n - 1) cout << " ";
    }
    cout << "\n";
    return 0;
}
```

**When to use which sort in C:**
- `qsort` (from `stdlib.h`): general purpose, O(N log N) average, requires a comparator function
- Manual bubble sort: only for very small arrays (N < 10) or when the problem explicitly asks for bubble sort

### Problem A-2: Find Maximum and Minimum

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

int main(int argc, char *argv[]) {
    int n = argc - 1;
    int maxVal = INT_MIN, minVal = INT_MAX;

    for (int i = 1; i < argc; i++) {
        int val = atoi(argv[i]);
        if (val > maxVal) maxVal = val;
        if (val < minVal) minVal = val;
    }
    printf("Max: %d\nMin: %d\n", maxVal, minVal);
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <vector>
#include <algorithm>
#include <cstdlib>
#include <climits>
using namespace std;

int main(int argc, char *argv[]) {
    vector<int> arr;
    for (int i = 1; i < argc; i++) arr.push_back(atoi(argv[i]));

    cout << "Max: " << *max_element(arr.begin(), arr.end()) << "\n";
    cout << "Min: " << *min_element(arr.begin(), arr.end()) << "\n";
    return 0;
}
```

### Problem A-3: Array Rotation

**Problem statement:** Rotate an array of N elements left by K positions.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

void rotateLeft(int arr[], int n, int k) {
    k = k % n;  // handle k >= n
    // Reverse first k elements
    for (int i = 0, j = k - 1; i < j; i++, j--) {
        int temp = arr[i]; arr[i] = arr[j]; arr[j] = temp;
    }
    // Reverse remaining n-k elements
    for (int i = k, j = n - 1; i < j; i++, j--) {
        int temp = arr[i]; arr[i] = arr[j]; arr[j] = temp;
    }
    // Reverse entire array
    for (int i = 0, j = n - 1; i < j; i++, j--) {
        int temp = arr[i]; arr[i] = arr[j]; arr[j] = temp;
    }
}

int main(int argc, char *argv[]) {
    // First argument is k, remaining are array elements
    int k = atoi(argv[1]);
    int n = argc - 2;
    int arr[100];
    for (int i = 0; i < n; i++) arr[i] = atoi(argv[i + 2]);

    rotateLeft(arr, n, k);

    for (int i = 0; i < n; i++) {
        printf("%d", arr[i]);
        if (i < n - 1) printf(" ");
    }
    printf("\n");
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <vector>
#include <algorithm>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int k = atoi(argv[1]);
    vector<int> arr;
    for (int i = 2; i < argc; i++) arr.push_back(atoi(argv[i]));
    int n = arr.size();
    k = k % n;
    rotate(arr.begin(), arr.begin() + k, arr.end());
    for (int i = 0; i < n; i++) {
        cout << arr[i];
        if (i < n - 1) cout << " ";
    }
    cout << "\n";
    return 0;
}
```

---

## Part 5: Pattern Programs

Pattern printing uses nested loops. TCS occasionally tests these to verify basic loop control.

### Problem P-1: Number Triangle

**Problem statement:** Print a number triangle of N rows.
```
1
1 2
1 2 3
1 2 3 4
```

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    for (int i = 1; i <= n; i++) {
        for (int j = 1; j <= i; j++) {
            printf("%d", j);
            if (j < i) printf(" ");
        }
        printf("\n");
    }
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    for (int i = 1; i <= n; i++) {
        for (int j = 1; j <= i; j++) {
            cout << j;
            if (j < i) cout << " ";
        }
        cout << "\n";
    }
    return 0;
}
```

### Problem P-2: Star Pyramid

**Problem statement:** Print a star pyramid of N rows.
```
    *
   ***
  *****
 *******
*********
```

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    for (int i = 1; i <= n; i++) {
        // Print spaces
        for (int j = 1; j <= n - i; j++) printf(" ");
        // Print stars (2*i - 1 stars)
        for (int j = 1; j <= 2 * i - 1; j++) printf("*");
        printf("\n");
    }
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <string>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    for (int i = 1; i <= n; i++) {
        cout << string(n - i, ' ') << string(2 * i - 1, '*') << "\n";
    }
    return 0;
}
```

---

## Part 6: Mathematical Programs

### Problem M-1: GCD and LCM

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int gcd(int a, int b) {
    while (b != 0) {
        int temp = b;
        b = a % b;
        a = temp;
    }
    return a;
}

int main(int argc, char *argv[]) {
    int a = atoi(argv[1]);
    int b = atoi(argv[2]);
    int g = gcd(a, b);
    int l = (a / g) * b;  // a/g first to reduce overflow risk
    printf("GCD: %d\nLCM: %d\n", g, l);
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <numeric>  // for std::gcd in C++17
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int a = atoi(argv[1]), b = atoi(argv[2]);
    int g = __gcd(a, b);  // C++ built-in (or std::gcd in C++17)
    int l = (a / g) * b;
    cout << "GCD: " << g << "\nLCM: " << l << "\n";
    return 0;
}
```

### Problem M-2: Binary Conversion

**Problem statement:** Convert a decimal number to binary.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    if (n == 0) { printf("0\n"); return 0; }

    char binary[64];
    int pos = 0;

    while (n > 0) {
        binary[pos++] = '0' + (n % 2);
        n /= 2;
    }
    // Reverse the binary string
    for (int i = 0; i < pos / 2; i++) {
        char temp = binary[i];
        binary[i] = binary[pos - 1 - i];
        binary[pos - 1 - i] = temp;
    }
    binary[pos] = '\0';
    printf("%s\n", binary);
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <bitset>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    // Using bitset for clean binary conversion
    cout << bitset<32>(n).to_string().substr(bitset<32>(n).to_string().find('1')) << "\n";
    return 0;
}
```

Or the manual approach in C++:
```cpp
string toBinary(int n) {
    if (n == 0) return "0";
    string result = "";
    while (n > 0) { result = char('0' + n % 2) + result; n /= 2; }
    return result;
}
```

### Problem M-3: Matrix Addition

**Problem statement:** Add two 2x2 matrices. Input: 8 numbers (row-major order for each matrix).

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int a[2][2], b[2][2], c[2][2];
    // Read first matrix
    for (int i = 0; i < 2; i++)
        for (int j = 0; j < 2; j++)
            a[i][j] = atoi(argv[1 + i * 2 + j]);
    // Read second matrix
    for (int i = 0; i < 2; i++)
        for (int j = 0; j < 2; j++)
            b[i][j] = atoi(argv[5 + i * 2 + j]);
    // Add
    for (int i = 0; i < 2; i++)
        for (int j = 0; j < 2; j++)
            c[i][j] = a[i][j] + b[i][j];
    // Print
    for (int i = 0; i < 2; i++) {
        for (int j = 0; j < 2; j++) {
            printf("%d", c[i][j]);
            if (j < 1) printf(" ");
        }
        printf("\n");
    }
    return 0;
}
```

---

## Part 7: Advanced Programs

### Problem ADV-1: Recursive Sum of Digits

**Problem statement:** Find the digital root of a number (recursively sum digits until single digit).

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int digitSum(int n) {
    if (n < 10) return n;
    int sum = 0;
    while (n > 0) { sum += n % 10; n /= 10; }
    return digitSum(sum);
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    printf("%d\n", digitSum(n));
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <cstdlib>
using namespace std;

int digitRoot(int n) {
    if (n < 10) return n;
    int sum = 0;
    while (n > 0) { sum += n % 10; n /= 10; }
    return digitRoot(sum);
}

int main(int argc, char *argv[]) {
    cout << digitRoot(atoi(argv[1])) << "\n";
    return 0;
}
```

**Mathematical shortcut:** The digital root of N is: 0 if N=0, 9 if N%9==0, else N%9. This O(1) formula replaces the recursive approach for large inputs.

### Problem ADV-2: Two Array Intersection

**Problem statement:** Find common elements between two arrays.

**C++ Solution (using sets):**
```cpp
#include <iostream>
#include <set>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    // First arg: N (size of first array), next N args: first array
    // Then M (size of second array), next M args: second array
    int n = atoi(argv[1]);
    set<int> setA;
    for (int i = 2; i <= n + 1; i++) setA.insert(atoi(argv[i]));

    int m = atoi(argv[n + 2]);
    bool first = true;
    for (int i = n + 3; i <= n + 2 + m; i++) {
        int val = atoi(argv[i]);
        if (setA.count(val)) {
            if (!first) cout << " ";
            cout << val;
            first = false;
            setA.erase(val);  // prevent duplicates in output
        }
    }
    cout << "\n";
    return 0;
}
```

### Problem ADV-3: Bit Manipulation - Count Set Bits

**Problem statement:** Count the number of 1-bits in the binary representation of N.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int countBits(int n) {
    int count = 0;
    while (n) {
        count += n & 1;  // check last bit
        n >>= 1;          // shift right
    }
    return count;
}

// Alternatively: Brian Kernighan's algorithm (faster)
int countBitsFast(int n) {
    int count = 0;
    while (n) {
        n &= (n - 1);  // clears the lowest set bit
        count++;
    }
    return count;
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    printf("%d\n", countBitsFast(n));
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <bitset>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    cout << __builtin_popcount(n) << "\n";  // GCC built-in
    return 0;
}
```

`__builtin_popcount` is a GCC compiler intrinsic that counts set bits. Since TCS uses GCC, this is available and is the fastest option.

---

## C/C++ Quick Reference for TCS iON

### C Standard Library Headers

| Header | Key functions |
|---|---|
| `stdio.h` | printf, scanf, fprintf, fgets |
| `stdlib.h` | atoi, atof, atol, malloc, free, qsort, abs |
| `string.h` | strlen, strcpy, strcat, strcmp, strchr, strstr, memset |
| `math.h` | sqrt, pow, abs, floor, ceil, log, sin, cos |
| `ctype.h` | isalpha, isdigit, isupper, islower, toupper, tolower |
| `limits.h` | INT_MAX, INT_MIN, LLONG_MAX, LLONG_MIN |

### C++ STL Quick Reference

```cpp
// Vector (dynamic array)
vector<int> v;
v.push_back(5);     // add to back
v.pop_back();       // remove from back
v.size();           // number of elements
v[i];               // access by index
sort(v.begin(), v.end());  // sort ascending
sort(v.begin(), v.end(), greater<int>());  // sort descending

// String
string s = "hello";
s.length();                    // length
s.find("ell");                 // find substring (npos if not found)
s.substr(1, 3);                // substring starting at 1, length 3 = "ell"
s.replace(1, 3, "xyz");        // replace
s += " world";                 // concatenate
transform(s.begin(), s.end(), s.begin(), toupper);  // uppercase

// Map
map<string, int> m;
m["key"] = 5;
m.count("key");     // 1 if exists, 0 if not
m.find("key");      // iterator, m.end() if not found
for (auto &p : m) { cout << p.first << " " << p.second; }

// Set
set<int> s;
s.insert(5);
s.count(5);        // 1 if present, 0 if not
s.erase(5);

// Queue
queue<int> q;
q.push(5);         // enqueue
q.front();         // peek front
q.pop();           // dequeue

// Stack
stack<int> st;
st.push(5);        // push
st.top();          // peek top
st.pop();          // pop
```

### Common TCS Coding Mistakes

**Mistake 1: Off-by-one in command line argument indexing**
`argv[0]` is the program name. Your first data argument is `argv[1]`, not `argv[0]`.

**Mistake 2: Not handling negative numbers**
`atoi("-5")` correctly returns -5, but programs that assume inputs are always positive will fail. Check the problem statement for the input range.

**Mistake 3: Integer overflow**
For problems involving products or sums of large numbers, use `long long` instead of `int`. Declare with `long long var = 0LL;` and use `%lld` in printf.

**Mistake 4: Forgetting string null terminator**
C strings end with `\0`. A char array of size N can hold N-1 characters plus the terminator. Always ensure your string buffer is large enough.

**Mistake 5: endl vs "\n" in loops**
`cout << endl` flushes the buffer AND prints a newline. In output-intensive loops, use `"\n"` which only prints a newline without flushing.

**Mistake 6: Array size underestimation**
When reading N elements from command line arguments, ensure your array is declared with size at least N. A safe practice: `int arr[1000]` covers most TCS problem constraints.

**Mistake 7: Missing return statement**
`main` must return 0 on success. Some compilers warn but do not error; the TCS compiler may accept or reject missing returns depending on the standard used. Always include `return 0;`.

---

## Test Strategy for C/C++ on TCS iON

### Before Writing Code

1. Read the problem twice. Identify: input format (command line or stdin?), data types needed (int, long long, float?), output format (exact string match required).

2. Write pseudocode on rough paper. Identify the algorithm before writing actual code.

3. Check the constraints. If N can be up to 10^6, an O(N²) algorithm will time out.

### While Writing Code

1. Use descriptive variable names even in competitive settings. `n` for count, `arr` for array, `result` for the final answer are readable and error-reducing.

2. Handle edge cases explicitly at the top of your function: n=0, n=1, negative numbers, empty strings.

3. Test mentally with the sample input before submitting. Trace through your code line by line with the given input and verify the output matches.

### After Writing Code

Verify:
- All arguments read from `argv`, not from `scanf` if the problem specifies command line input
- Output matches expected format exactly (no extra spaces, correct newlines)
- No unused variables that might cause compiler warnings
- `return 0;` at the end of `main`

Submit the brute-force solution first if you have one that works on the sample test cases. Then optimise if time permits. A partially-correct solution is always better than a perfectly-written solution that is never submitted.

The C and C++ language combination, mastered to the level demonstrated in this guide, provides complete coverage for TCS NQT Foundation and Ninja coding requirements. For Digital Advanced coding, the same foundations extend naturally into more complex algorithms - but the input handling, output formatting, and structural patterns remain identical.

---

## Part 8: Extended Problem Collection

### Problem E-1: Number of Occurrences of Each Digit

**Problem statement:** Given a number, print how many times each digit (0-9) appears in it.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char *s = argv[1];
    int freq[10] = {0};

    // Handle negative numbers: skip the minus sign
    int start = (s[0] == '-') ? 1 : 0;

    for (int i = start; s[i] != '\0'; i++) {
        if (s[i] >= '0' && s[i] <= '9') {
            freq[s[i] - '0']++;
        }
    }

    for (int i = 0; i <= 9; i++) {
        if (freq[i] > 0) {
            printf("%d appears %d time(s)\n", i, freq[i]);
        }
    }
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <map>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    string s = argv[1];
    map<char, int> freq;
    for (char c : s) {
        if (c >= '0' && c <= '9') freq[c]++;
    }
    for (auto &p : freq) {
        cout << (p.first - '0') << " appears " << p.second << " time(s)\n";
    }
    return 0;
}
```

### Problem E-2: Power Without Built-in Function

**Problem statement:** Compute base^exp using only multiplication (no `pow()`).

**C Solution (iterative):**
```c
#include <stdio.h>
#include <stdlib.h>

long long power(long long base, int exp) {
    long long result = 1;
    while (exp > 0) {
        if (exp % 2 == 1) result *= base;
        base *= base;
        exp /= 2;
    }
    return result;
}

int main(int argc, char *argv[]) {
    long long base = atol(argv[1]);
    int exp = atoi(argv[2]);
    printf("%lld\n", power(base, exp));
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <cstdlib>
using namespace std;

long long power(long long base, int exp) {
    long long result = 1;
    while (exp > 0) {
        if (exp & 1) result *= base;  // same as exp % 2 == 1
        base *= base;
        exp >>= 1;                     // same as exp /= 2
    }
    return result;
}

int main(int argc, char *argv[]) {
    long long base = atol(argv[1]);
    int exp = atoi(argv[2]);
    cout << power(base, exp) << "\n";
    return 0;
}
```

**Why this approach (binary exponentiation):** Naive repeated multiplication takes O(exp) multiplications. Binary exponentiation exploits the fact that base^8 = (base^4)^2 = ((base^2)^2)^2, reducing to O(log exp) multiplications.

### Problem E-3: Check Perfect Number

**Problem statement:** A perfect number equals the sum of its proper divisors (divisors excluding itself). Is N perfect?

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

int isPerfect(int n) {
    if (n <= 1) return 0;
    int sum = 1;  // 1 is always a proper divisor (for n > 1)
    for (int i = 2; i <= (int)sqrt((double)n); i++) {
        if (n % i == 0) {
            sum += i;
            if (i != n / i) sum += n / i;  // add both divisors
        }
    }
    return sum == n;
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    printf("%s\n", isPerfect(n) ? "Perfect" : "Not Perfect");
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <cmath>
#include <cstdlib>
using namespace std;

bool isPerfect(int n) {
    if (n <= 1) return false;
    int sum = 1;
    for (int i = 2; i <= (int)sqrt((double)n); i++) {
        if (n % i == 0) {
            sum += i;
            if (i != n / i) sum += n / i;
        }
    }
    return sum == n;
}

int main(int argc, char *argv[]) {
    cout << (isPerfect(atoi(argv[1])) ? "Perfect" : "Not Perfect") << "\n";
    return 0;
}
```

**Well-known perfect numbers:** 6 (1+2+3=6), 28 (1+2+4+7+14=28), 496, 8128.

### Problem E-4: Sum of Prime Numbers up to N

**Problem statement:** Find the sum of all prime numbers from 2 to N using the Sieve of Eratosthenes.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    char *sieve = (char *)calloc(n + 1, sizeof(char));  // 0 = prime, 1 = composite
    // calloc initialises to 0

    sieve[0] = 1; sieve[1] = 1;  // 0 and 1 are not prime

    for (int i = 2; (long long)i * i <= n; i++) {
        if (!sieve[i]) {
            for (int j = i * i; j <= n; j += i) {
                sieve[j] = 1;
            }
        }
    }

    long long sum = 0;
    for (int i = 2; i <= n; i++) {
        if (!sieve[i]) sum += i;
    }
    printf("%lld\n", sum);
    free(sieve);
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <vector>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    vector<bool> sieve(n + 1, true);
    sieve[0] = sieve[1] = false;

    for (int i = 2; (long long)i * i <= n; i++) {
        if (sieve[i]) {
            for (int j = i * i; j <= n; j += i)
                sieve[j] = false;
        }
    }

    long long sum = 0;
    for (int i = 2; i <= n; i++)
        if (sieve[i]) sum += i;

    cout << sum << "\n";
    return 0;
}
```

**Sieve efficiency:** The Sieve of Eratosthenes generates all primes up to N in O(N log log N) time, far faster than checking each number individually.

### Problem E-5: Second Largest in Array

**Problem statement:** Find the second largest element in an array. All elements are distinct.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

int main(int argc, char *argv[]) {
    int n = argc - 1;
    int largest = INT_MIN, second = INT_MIN;

    for (int i = 1; i < argc; i++) {
        int val = atoi(argv[i]);
        if (val > largest) {
            second = largest;
            largest = val;
        } else if (val > second) {
            second = val;
        }
    }

    if (second == INT_MIN) {
        printf("No second largest\n");
    } else {
        printf("%d\n", second);
    }
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <vector>
#include <algorithm>
#include <cstdlib>
#include <climits>
using namespace std;

int main(int argc, char *argv[]) {
    vector<int> arr;
    for (int i = 1; i < argc; i++) arr.push_back(atoi(argv[i]));
    sort(arr.begin(), arr.end(), greater<int>());
    cout << arr[1] << "\n";  // second element after descending sort
    return 0;
}
```

**Note:** The C solution is O(N) - single pass. The C++ solution using sort is O(N log N). For TCS problem constraints, both work, but the O(N) approach is worth knowing.

### Problem E-6: Count Pairs with Given Sum

**Problem statement:** Count pairs of elements in an array whose sum equals a target value K.

**C Solution (O(N²)):**
```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int k = atoi(argv[1]);
    int n = argc - 2;
    int arr[100];
    for (int i = 0; i < n; i++) arr[i] = atoi(argv[i + 2]);

    int count = 0;
    for (int i = 0; i < n - 1; i++) {
        for (int j = i + 1; j < n; j++) {
            if (arr[i] + arr[j] == k) count++;
        }
    }
    printf("%d\n", count);
    return 0;
}
```

**C++ Solution (O(N) using map):**
```cpp
#include <iostream>
#include <unordered_map>
#include <cstdlib>
using namespace std;

int main(int argc, char *argv[]) {
    int k = atoi(argv[1]);
    unordered_map<int, int> freq;
    int count = 0;

    for (int i = 2; i < argc; i++) {
        int val = atoi(argv[i]);
        int complement = k - val;
        if (freq.count(complement)) {
            count += freq[complement];
        }
        freq[val]++;
    }
    cout << count << "\n";
    return 0;
}
```

**Algorithm:** For each element, check if (k - element) has been seen before. If yes, all previous occurrences of (k - element) form valid pairs with the current element.

---

## Part 9: Using Standard Input (scanf/cin) When Required

While TCS often uses command line arguments, some problems specify standard input. The key patterns:

### Reading Multiple Lines with scanf

```c
#include <stdio.h>

int main() {
    int n;
    scanf("%d", &n);  // read count
    int arr[100];
    for (int i = 0; i < n; i++) {
        scanf("%d", &arr[i]);  // read each element
    }
    // process...
    return 0;
}
```

### Reading Multiple Lines with cin

```cpp
#include <iostream>
#include <vector>
using namespace std;

int main() {
    int n;
    cin >> n;
    vector<int> arr(n);
    for (int i = 0; i < n; i++) cin >> arr[i];
    // process...
    return 0;
}
```

### Reading a String with Spaces

```c
// Reading a line with spaces in C
char line[1000];
fgets(line, sizeof(line), stdin);
// fgets includes the newline - strip it if needed
line[strcspn(line, "\n")] = '\0';
```

```cpp
// Reading a line with spaces in C++
string line;
getline(cin, line);
```

**Important:** `scanf("%s", str)` reads only up to the first whitespace. Use `fgets` or `getline` for strings with spaces.

---

## Handling Multiple Test Cases

Some TCS problems provide multiple test cases in a single run. Two common formats:

### Format 1: Count then Cases

```
3          <- number of test cases
5          <- test case 1 input
12         <- test case 2 input
7          <- test case 3 input
```

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int solve(int n) {
    // your logic here
    return n * n;  // example: return square
}

int main(int argc, char *argv[]) {
    // If using command line: first arg is count, rest are test cases
    int t = atoi(argv[1]);
    for (int i = 0; i < t; i++) {
        int n = atoi(argv[i + 2]);
        printf("%d\n", solve(n));
    }
    return 0;
}
```

### Format 2: Read Until End of Input (scanf returns EOF)

```c
#include <stdio.h>

int main() {
    int n;
    while (scanf("%d", &n) != EOF) {
        printf("%d\n", n * n);  // process each input
    }
    return 0;
}
```

```cpp
#include <iostream>
using namespace std;

int main() {
    int n;
    while (cin >> n) {
        cout << n * n << "\n";
    }
    return 0;
}
```

---

## Debugging Common Compile Errors on TCS iON

### "implicit declaration of function"

Occurs when a function is used before being declared. Either declare the function before `main` or add a forward declaration (prototype):

```c
// Add prototype before main:
int isPrime(int n);

int main(int argc, char *argv[]) {
    // can now call isPrime
}

int isPrime(int n) { ... }
```

### "undefined reference to sqrt/pow"

The math functions require explicit linking with `-lm`. TCS iON handles this automatically, but if you see this error in your local testing: `gcc program.c -o program -lm`.

### Segmentation Fault (Runtime Error)

Most common causes:
1. Array access out of bounds (arr[-1] or arr[n] when valid is arr[0] to arr[n-1])
2. Dereferencing a null pointer
3. Stack overflow from infinite recursion

**Debugging locally:**
```bash
gcc -g program.c -o program   # compile with debug info
./program args                 # run and see where it crashes
```

Or add print statements before and after the suspected crash point to locate it.

### "format '%d' expects argument of type 'int*' but argument is of type 'long long*'"

This is a common mismatch. Use `%lld` for `long long`, `%d` for `int`, `%f` for `float`, `%lf` for `double`.

---

## Complete Program Template: C and C++

### C Template (Command Line Input)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ctype.h>
#include <limits.h>

/* Helper functions go here */

int main(int argc, char *argv[]) {
    /* Read inputs */
    int n = atoi(argv[1]);  // adjust based on problem

    /* Process */

    /* Output */
    printf("%d\n", n);  // adjust based on expected output

    return 0;
}
```

### C++ Template (Command Line Input)

```cpp
#include <bits/stdc++.h>
using namespace std;
typedef long long ll;

int main(int argc, char *argv[]) {
    ios_base::sync_with_stdio(false);
    cin.tie(NULL);

    /* Read inputs from command line */
    int n = atoi(argv[1]);  // adjust as needed

    /* Process */

    /* Output */
    cout << n << "\n";

    return 0;
}
```

**Note on ios_base::sync_with_stdio(false):** This speed optimisation is useful when mixing cin/cout with scanf/printf (which you should not do). For programs using only cout, it provides a minor speedup. Leave it in as standard competitive programming practice.

---

## Practice Problem Set: 10 Challenge Problems

Work through each of these under timed conditions (25 minutes each). These represent the range of problems you will encounter in TCS NQT Foundation and Ninja coding sections.

**Challenge 1:** Accept N integers as command line arguments. Print the sum of squares of even numbers and the sum of squares of odd numbers separately.

**Challenge 2:** Accept a string. Print the string with every word reversed individually, but the word order preserved. Example: "hello world" → "olleh dlrow".

**Challenge 3:** Accept two arrays (size M and N, all sizes and elements as command line arguments). Merge them into a single sorted array without using any sort function - only the merge step from merge sort.

**Challenge 4:** Accept N and check if N is a perfect square. If yes, print its square root. If not, print "Not a perfect square". Do not use sqrt().

**Challenge 5:** Accept a string. Print all non-repeating characters in the order they appear in the string.

**Challenge 6:** Accept an array of N integers. Find the maximum sum subarray and print both the sum and the starting and ending indices.

**Challenge 7:** Accept a positive integer N. Print all prime factors of N in ascending order (with repetition). Example: 12 → 2 2 3.

**Challenge 8:** Accept a string. Check if it is an anagram of its own reverse. (This is always true - think about it and explain why.)

**Challenge 9:** Accept N integers. Partition them into two groups: elements at even indices and elements at odd indices. Print each group sorted in ascending order.

**Challenge 10:** Accept a number. Print the next prime number greater than or equal to that number.

These problems cover the full range of Foundation coding skills. Solving all 10 correctly from scratch, with command line input handling, in under 25 minutes each, means you are fully prepared for the TCS NQT Ninja Coding section.

---

## The Language Decision: When to Switch Mid-Preparation

Many candidates ask: "I've been practising in Python, should I switch to C/C++ for TCS?"

The answer depends on where you are in your preparation:

**If you have 3+ weeks:** Learning C/C++ input/output patterns is feasible and worth doing. The efficiency of C++ STL makes many problems cleaner to solve.

**If you have 1-2 weeks:** Stick with what you know. A correct Python solution beats an incomplete C++ solution. Spend time on problem-solving, not language switching.

**The specific case for C/C++:** If your primary language is Java or Python, the command line argument pattern (`argc`/`argv`/`atoi`) requires the same learning investment regardless of which of C/C++ you choose. The 3 programs in Part 1 of this guide cover that learning in under 2 hours of focused practice.

**The practical recommendation:** Know at least one of C or C++ well enough to handle command line input. Then solve problems primarily in your preferred language. The language does not determine your Foundation coding score - solving the problem correctly does.

C and C++ provide one genuine advantage: speed. If the TCS iON judge times out your Python or Java solution on a large test case, C/C++ will pass. For Foundation-level problems, this rarely matters. For Digital-level competitive problems, it can be the difference between full marks and partial marks.

---

## Part 10: String Programs Extended

### Problem ES-1: String Without Using String Library Functions

TCS sometimes tests whether you can work with strings at the character level, without relying on `strlen`, `strcpy`, or similar functions.

**Implement strlen manually:**
```c
int myStrlen(char *s) {
    int count = 0;
    while (s[count] != '\0') count++;
    return count;
}
```

**Implement strcmp manually:**
```c
int myStrcmp(char *s1, char *s2) {
    int i = 0;
    while (s1[i] != '\0' && s2[i] != '\0') {
        if (s1[i] != s2[i]) return s1[i] - s2[i];
        i++;
    }
    return s1[i] - s2[i];  // 0 if both ended, positive/negative if one ended first
}
```

**Implement strcpy manually:**
```c
void myStrcpy(char *dest, char *src) {
    int i = 0;
    while (src[i] != '\0') {
        dest[i] = src[i];
        i++;
    }
    dest[i] = '\0';  // null-terminate the destination
}
```

### Problem ES-2: Count Words in a String

**Problem statement:** Count the number of words in a sentence (words separated by single spaces).

**C Solution:**
```c
#include <stdio.h>
#include <ctype.h>

int main(int argc, char *argv[]) {
    char *s = argv[1];
    int wordCount = 0;
    int inWord = 0;

    for (int i = 0; s[i] != '\0'; i++) {
        if (!isspace(s[i]) && !inWord) {
            wordCount++;
            inWord = 1;
        } else if (isspace(s[i])) {
            inWord = 0;
        }
    }
    printf("%d\n", wordCount);
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <sstream>
#include <string>
using namespace std;

int main(int argc, char *argv[]) {
    string s = argv[1];
    istringstream iss(s);
    string word;
    int count = 0;
    while (iss >> word) count++;
    cout << count << "\n";
    return 0;
}
```

**Note on the C++ approach:** `istringstream` with `>>` automatically handles multiple spaces and trims leading/trailing whitespace.

### Problem ES-3: Check if Two Strings Are Anagrams

**Problem statement:** Two strings are anagrams if they contain the same characters with the same frequencies.

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[]) {
    char *s1 = argv[1];
    char *s2 = argv[2];

    int freq[256] = {0};

    // Increment for s1
    for (int i = 0; s1[i] != '\0'; i++) freq[(unsigned char)s1[i]]++;
    // Decrement for s2
    for (int i = 0; s2[i] != '\0'; i++) freq[(unsigned char)s2[i]]--;

    // If any frequency is non-zero, not anagrams
    for (int i = 0; i < 256; i++) {
        if (freq[i] != 0) {
            printf("Not Anagram\n");
            return 0;
        }
    }
    printf("Anagram\n");
    return 0;
}
```

**C++ Solution:**
```cpp
#include <iostream>
#include <algorithm>
#include <string>
using namespace std;

int main(int argc, char *argv[]) {
    string s1 = argv[1], s2 = argv[2];
    sort(s1.begin(), s1.end());
    sort(s2.begin(), s2.end());
    cout << (s1 == s2 ? "Anagram" : "Not Anagram") << "\n";
    return 0;
}
```

**Two approaches:** The C solution uses O(1) space (fixed-size frequency array) and O(N) time. The C++ sort solution uses O(N log N) time but is simpler to write.

---

## Part 11: Advanced Data Structure Programs

### Problem ADS-1: Implement a Stack in C

**Problem statement:** Implement push, pop, and peek operations for a stack. Process a sequence of operations.

**C Solution (array-based stack):**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_SIZE 100

int stack[MAX_SIZE];
int top = -1;

int isEmpty() { return top == -1; }
int isFull() { return top == MAX_SIZE - 1; }

void push(int val) {
    if (isFull()) { printf("Stack overflow\n"); return; }
    stack[++top] = val;
}

int pop() {
    if (isEmpty()) { printf("Stack underflow\n"); return -1; }
    return stack[top--];
}

int peek() {
    if (isEmpty()) { printf("Stack empty\n"); return -1; }
    return stack[top];
}

int main(int argc, char *argv[]) {
    // Process operations from command line:
    // argv[1] = operation (push/pop/peek), argv[2] = value if push
    for (int i = 1; i < argc; ) {
        if (strcmp(argv[i], "push") == 0 && i + 1 < argc) {
            push(atoi(argv[i + 1]));
            i += 2;
        } else if (strcmp(argv[i], "pop") == 0) {
            printf("%d\n", pop());
            i++;
        } else if (strcmp(argv[i], "peek") == 0) {
            printf("%d\n", peek());
            i++;
        } else {
            i++;
        }
    }
    return 0;
}
```

### Problem ADS-2: Queue Using Circular Array

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_SIZE 100

int queue[MAX_SIZE];
int front = 0, rear = 0, count = 0;

void enqueue(int val) {
    if (count == MAX_SIZE) { printf("Queue full\n"); return; }
    queue[rear] = val;
    rear = (rear + 1) % MAX_SIZE;
    count++;
}

int dequeue() {
    if (count == 0) { printf("Queue empty\n"); return -1; }
    int val = queue[front];
    front = (front + 1) % MAX_SIZE;
    count--;
    return val;
}

int main(int argc, char *argv[]) {
    for (int i = 1; i < argc; ) {
        if (strcmp(argv[i], "enqueue") == 0 && i + 1 < argc) {
            enqueue(atoi(argv[i + 1]));
            i += 2;
        } else if (strcmp(argv[i], "dequeue") == 0) {
            printf("%d\n", dequeue());
            i++;
        } else { i++; }
    }
    return 0;
}
```

### Problem ADS-3: Linked List Operations

**Problem statement:** Build a singly linked list from N values, then print the list in reverse order without reversing the list itself (use recursion).

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *next;
};

struct Node *createNode(int val) {
    struct Node *node = (struct Node *)malloc(sizeof(struct Node));
    node->data = val;
    node->next = NULL;
    return node;
}

void printReverse(struct Node *head) {
    if (head == NULL) return;
    printReverse(head->next);  // recurse to end first
    printf("%d", head->data);
    if (head->next != NULL) printf(" ");  // avoid trailing space at start
}

int main(int argc, char *argv[]) {
    struct Node *head = NULL, *tail = NULL;
    int n = argc - 1;

    for (int i = 1; i < argc; i++) {
        struct Node *node = createNode(atoi(argv[i]));
        if (head == NULL) { head = tail = node; }
        else { tail->next = node; tail = node; }
    }

    printReverse(head);
    printf("\n");

    // Free memory (good practice)
    struct Node *curr = head;
    while (curr) {
        struct Node *next = curr->next;
        free(curr);
        curr = next;
    }
    return 0;
}
```

---

## Part 12: Bit Manipulation Programs

### Problem BM-1: Check if N is a Power of 2

**C Solution:**
```c
#include <stdio.h>
#include <stdlib.h>

int isPowerOfTwo(int n) {
    if (n <= 0) return 0;
    return (n & (n - 1)) == 0;
}

int main(int argc, char *argv[]) {
    int n = atoi(argv[1]);
    printf("%s\n", isPowerOfTwo(n) ? "Power of 2" : "Not Power of 2");
    return 0;
}
```

**Why this works:** Powers of 2 in binary are 1, 10, 100, 1000, etc. (exactly one 1-bit). Subtracting 1 from a power of 2 gives 0, 01, 011, 0111 (all the lower bits become 1). AND-ing N with N-1 for a power of 2 gives 0; for any non-power it gives a non-zero result.

### Problem BM-2: Swap Two Numbers Without Temporary Variable

**C Solution (using XOR):**
```c
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    int a = atoi(argv[1]);
    int b = atoi(argv[2]);

    printf("Before: a=%d b=%d\n", a, b);

    // XOR swap
    a ^= b;  // a = a XOR b
    b ^= a;  // b = b XOR (a XOR b) = a
    a ^= b;  // a = (a XOR b) XOR a = b

    printf("After: a=%d b=%d\n", a, b);
    return 0;
}
```

**C solution (using arithmetic):**
```c
a = a + b;
b = a - b;  // b = (a+b) - b = a
a = a - b;  // a = (a+b) - a = b
```

**Note:** The XOR method has one pitfall: if a and b point to the same memory location, XOR swap incorrectly sets both to 0. The arithmetic method avoids this but can overflow for large values. In practice, always use a temporary variable in production code - these techniques are exam curiosities.

---

## Additional C vs C++ Comparison: When C Wins

Despite C++ being the recommended language for most TCS problems, C has specific advantages worth knowing:

**C is simpler for character-level string work.** Manipulating `char *` arrays with pointer arithmetic is faster to write for experienced C programmers than managing `std::string` objects for some specific patterns.

**C is more explicit about memory.** For problems where you need to understand exactly what is happening (memory addresses, pointer arithmetic, struct layouts), C forces clarity that C++ can obscure with abstractions.

**C is what is taught in most Indian engineering curricula.** If you learned programming in C and are more fluent in it than C++, use C for TCS. A correct, clean C solution beats a buggy C++ solution.

**When C clearly loses:**
- Sorting: C requires writing or calling `qsort` with a comparator; C++ has `std::sort` which is cleaner.
- Collections: C has no built-in hash map or dynamic array; C++ STL provides them.
- String operations: C++ `std::string` has `find`, `substr`, `replace` built in; C requires manual loops or careful library use.

The practical guidance: if you know both at similar levels, C++ is more efficient for problem-solving. If you are stronger in C, the core command line programming and logic patterns in this guide are fully expressible in C.

---

## The Output Validation Mindset

The single biggest source of wrong answers in TCS coding, given correct logic, is output format mismatch. This is fully preventable with one habit: before submitting, compare your output to the sample output character by character.

**The checklist:**
- Is your output on the same number of lines as the expected output?
- Are numbers separated by exactly the spacing shown (space, comma, newline)?
- Are there any leading or trailing spaces you didn't intend?
- If the output is a single number, is it on its own line (`\n` at the end)?
- If the output is "Yes"/"No" or "True"/"False", does the capitalisation match exactly?

**A practical technique:** Print your output to a file and use `diff` locally against the expected output file. `diff actual.txt expected.txt` shows any differences including invisible characters. In a TCS exam context, this is done mentally by tracing through your code's print statements.

The extra 60 seconds spent verifying output format is among the highest-return time investments in any coding exam. Logic errors require redesign; format errors require a single character change.

Mastering C and C++ input/output specifically for TCS, through the programs in this guide, means arriving at the TCS coding section with zero uncertainty about the mechanical aspects of submission. The only challenge remaining is the algorithm itself.

---

## Complete Problem Category Summary with Complexity Reference

| Problem | C Approach | C++ Approach | Time Complexity |
|---|---|---|---|
| Sum of N numbers | atoi loop | atoi + vector | O(N) |
| Prime check | sqrt(n) loop | sqrt(n) loop | O(sqrt N) |
| All primes to N | Sieve with calloc | Sieve with vector<bool> | O(N log log N) |
| Palindrome number | Reverse by digits | Same or string compare | O(log N) |
| Palindrome string | Two-pointer | Two-pointer or reverse | O(N) |
| Fibonacci N terms | Two-variable loop | Same | O(N) |
| Armstrong check | Count digits, sum powers | Same | O(log N) |
| Factorial | Iterative product | Same | O(N) |
| Sort array | qsort() | std::sort | O(N log N) |
| Array max/min | Linear scan | max/min_element | O(N) |
| Array rotation | Reversal algorithm | std::rotate | O(N) |
| String reversal | In-place swap | std::reverse or rbegin | O(N) |
| Char frequency | freq[256] array | map<char,int> | O(N) |
| Anagram check | Frequency difference | Sort both, compare | O(N) or O(N log N) |
| GCD | Euclidean algorithm | __gcd() | O(log(min(a,b))) |
| Binary conversion | Extract bit by bit | bitset or manual | O(log N) |
| Power | Binary exponentiation | Same | O(log exp) |
| Perfect number | Sum divisors up to sqrt | Same | O(sqrt N) |
| Count set bits | Loop or __builtin_popcount | __builtin_popcount | O(log N) or O(1) |
| Second largest | Single pass | Sort descending | O(N) |

---

## Frequently Asked Questions: C/C++ on TCS Platform

**"Should I include `#include <bits/stdc++.h>` or individual headers?"**
For C++, `#include <bits/stdc++.h>` is the competitive programmer's convention and is supported on TCS iON (GCC compiler). It includes everything. For C, there is no equivalent - you must include individual headers. If you are writing C, include only what you use: `stdio.h`, `stdlib.h`, `string.h`, `math.h` as needed.

**"What data type should I use for large numbers?"**
For counts, indices, and most intermediate values: `int` (up to ~2.1 billion).
For sums that might overflow int: `long long` (up to ~9.2 × 10^18).
For products that might overflow long long: use intermediate modular arithmetic (`(a * b) % MOD` at each step) or Python.
For very large numbers (> 10^18): no native type in C/C++ - use strings or Python.

**"Can I use global variables in TCS coding?"**
Yes. Global variables are perfectly acceptable. For programs with multiple helper functions, global arrays can simplify data passing. This is a common competitive programming practice.

**"The problem says 'print without newline at the end'. How do I do that?"**
Simply omit the `\n` at the end of your last printf/cout statement. The line `printf("%d", result);` prints the integer with no newline.

**"Can I use multiple source files?"**
TCS iON is a single-file submission environment. All code must be in one file. Functions, structs, and global variables all go in the same `.c` or `.cpp` file.

**"What happens if my program takes too long?"**
The judge will return a TLE (Time Limit Exceeded) verdict. The test case is scored as incorrect. Partial credit for other test cases that completed within the time limit is still awarded. If TLE affects only large test cases, your logic is correct but your algorithm is too slow - submit the current solution for partial credit, then optimise.

**"My code compiles locally but gets a compilation error on TCS iON. Why?"**
Common causes:
1. You used a C++-specific feature in a file submitted as C (e.g., `//` comments in older C89 mode)
2. You used a non-standard extension that GCC accepts but the TCS compiler version rejects
3. Missing header (something included transitively by `bits/stdc++.h` locally but not on the platform)

Fix: Add explicit `#include` for every header you use. Avoid compiler-specific extensions that are not in the C99/C11 or C++14 standards.

**"How do I read a string with spaces using command line arguments?"**
Pass the string in quotes at the shell level: `./program "hello world"`. Inside the program, `argv[1]` will be `"hello world"` as a single string. The shell processes the quotes and passes everything within them as one argument.

---

## The atoi Edge Cases: What Every TCS Candidate Should Know

`atoi` is simple but has specific behaviour at edge cases that can cause bugs:

**`atoi("0")` returns 0** - correct.
**`atoi("-5")` returns -5** - handles negative correctly.
**`atoi("  42  ")` returns 42** - skips leading whitespace.
**`atoi("42abc")` returns 42** - stops at first non-digit.
**`atoi("abc")` returns 0** - no digits found, returns 0.
**`atoi("9999999999")` is undefined behaviour** - value exceeds int range. Use `atol()` (returns long) or `strtol()` (returns long with error checking) for large numbers.

**The safe alternative for large numbers:**
```c
long long val = strtoll(argv[1], NULL, 10);
```
`strtoll` converts to `long long` and the `10` specifies base 10. This handles numbers up to ~9.2 × 10^18 correctly.

**The full version with error checking:**
```c
char *endptr;
long long val = strtoll(argv[1], &endptr, 10);
if (*endptr != '\0') {
    printf("Invalid number: %s\n", argv[1]);
    return 1;
}
```
`endptr` points to the first character that was not part of the number. If it is `'\0'`, the entire string was a valid number.

---

## Connecting C/C++ Practice to the Broader TCS Preparation

The command line argument pattern (`argc`, `argv`, `atoi`) is specific to TCS's coding environment. Every other aspect of C/C++ programming - the logic, the algorithms, the data structures - is universal across competitive programming platforms.

This means your practice on external platforms (LeetCode, HackerRank, CodeChef) using C++ is fully transferable to TCS. The only adaptation needed is replacing `cin` input with `atoi(argv[N])` input. A candidate who has solved 50 problems on HackerRank using C++ needs only 2-3 hours of practice with the command line pattern to be fully prepared for TCS's input format.

Conversely, if you have practised all the programs in this guide with command line input but not practised general algorithmic problem-solving, you will handle the input correctly but struggle with harder problems. Both aspects - the TCS-specific input format and the general algorithmic preparation - are necessary.

The programs in this guide cover the TCS NQT Foundation and Ninja coding range completely. The Digital Advanced coding articles in this series cover the algorithms needed for Digital-level problems. Together, they provide the complete C/C++ preparation framework for TCS coding at every level.
