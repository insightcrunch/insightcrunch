---
layout: post
title: "Infosys Technical Interview Questions for Freshers"
page_title: "Infosys Technical Interview Questions and Answers for Freshers: OOP, Java, DBMS, OS, and Networking with Detailed Explanations"
date: 2021-08-22
categories: ["Industry"]
tags: ["Infosys Technical Interview Questions", "Infosys Interview Questions for Freshers", "Infosys Technical Round", "Infosys Java Interview Questions", "Infosys DBMS Questions", "Infosys OOP Questions", "Infosys OS Questions", "Infosys Interview Preparation"]
excerpt: "200+ Infosys technical interview questions with detailed answers covering OOP, Java, DBMS, OS, and networking for freshers with preparation strategy."
image: "/assets/images/blog/blog-87.webp"
reading_time: 60
author: "shruti-agarwal"
last_updated: 2026-03-29
---
The Infosys technical interview for freshers is a genuine evaluation, not a formality that follows the online assessment. Candidates who walk in expecting it to be easy because they have memorized a list of definitions get caught out immediately. Infosys technical interviewers, who are experienced engineers or senior developers, know the difference between a candidate who understands a concept and one who has memorized an explanation. The follow-up question is the tell: "Can you give me an example from your project?" or "What would happen if I changed this condition?" separates the two kinds of preparation within seconds.

![Infosys Technical Interview Questions for Freshers](/assets/images/blog/blog-87.webp)

This guide is built for genuine understanding, not surface coverage. For every topic that appears in the Infosys technical interview, questions are presented with complete, accurate answers, followed by the most common follow-up question the interviewer uses to probe depth, and the trap answer that reveals insufficient preparation. The topics covered are the ones that actually appear: OOP concepts, Java fundamentals, database management and SQL, operating systems, computer networks, and project-based technical questions.

The guide also covers the meta-skills of technical interviewing: how to handle questions you do not know the answer to, how to communicate while you think, how to present your project confidently, and how to recover when a line of reasoning hits a dead end. These skills determine the difference between a technically qualified candidate who impresses the interviewer and one who does not.

---

## Table of Contents

1. [What the Infosys Technical Interview Actually Evaluates](#what-the-infosys-technical-interview-actually-evaluates)
2. [OOP Concepts: Questions and Answers](#oop-concepts-questions-and-answers)
3. [Java Fundamentals: Questions and Answers](#java-fundamentals-questions-and-answers)
4. [Database Management System: Questions and Answers](#database-management-system-questions-and-answers)
5. [SQL Queries: Practical Questions and Solutions](#sql-queries-practical-questions-and-solutions)
6. [Operating Systems: Questions and Answers](#operating-systems-questions-and-answers)
7. [Computer Networks: Questions and Answers](#computer-networks-questions-and-answers)
8. [Data Structures: Questions and Answers](#data-structures-questions-and-answers)
9. [Project-Based Technical Questions](#project-based-technical-questions)
10. [Coding Questions Asked in Infosys Technical Rounds](#coding-questions-asked-in-infosys-technical-rounds)
11. [How to Handle Questions You Do Not Know](#how-to-handle-questions-you-do-not-know)
12. [The Technical Interview: Format and Flow](#the-technical-interview-format-and-flow)
13. [Frequently Asked Questions](#frequently-asked-questions)

---

## What the Infosys Technical Interview Actually Evaluates

Before diving into questions, understanding what interviewers are actually measuring helps calibrate preparation.

**Conceptual Clarity Over Memorization:**

The Infosys technical interview is designed to reveal whether a candidate genuinely understands the concepts they claim to know, or whether they have surface-level familiarity. The distinction appears in follow-up questions. If you say "polymorphism allows the same method to behave differently based on the object type," the follow-up is "can you show me this in code?" or "what would happen at runtime if I call this method on a parent class reference pointing to a child object?" A candidate who understands polymorphism answers these immediately. One who memorized the definition cannot.

**Problem-Solving Approach:**

When given a technical problem or a coding challenge, interviewers watch the process more than the answer. A candidate who articulates the problem, explores approaches, identifies edge cases, and works toward a solution methodically is evaluated more favorably than one who sits in silence and then either produces an answer or does not. Speaking through the thinking process is not just acceptable; it is expected and valued.

**Communication Quality:**

The interview is also a proxy for how the candidate will communicate in a professional technical environment. Can they explain a technical concept clearly? Can they answer a question concisely without padding? Can they acknowledge uncertainty without pretending to know things they do not? These communication qualities are evaluated alongside technical accuracy.

**Academic Project Depth:**

The final year project is the one area where every candidate should have absolute confidence, because it is their own work. Interviewers consistently probe the project for technical depth. A candidate who cannot explain the technology choices made in their own project, or who cannot answer "what would happen if you changed this component?" raises serious credibility concerns.

---

## OOP Concepts: Questions and Answers

Object-oriented programming is the most consistently tested topic in Infosys technical interviews for freshers. The four pillars (encapsulation, inheritance, polymorphism, abstraction) are the baseline, but interviewers typically go significantly deeper.

---

**Q1: What is Object-Oriented Programming? How does it differ from procedural programming?**

**Answer:**
Object-Oriented Programming (OOP) is a programming paradigm that organizes software design around data (objects) rather than functions and logic. An object is an instance of a class that bundles data (attributes) and behavior (methods) together.

In procedural programming, the program is structured as a sequence of procedures (functions) that operate on data. The data and the functions that operate on it are separate. In OOP, they are encapsulated together within objects.

The key advantages OOP provides over procedural programming are: better data security through encapsulation (data is hidden within objects), better code reusability through inheritance, better flexibility through polymorphism, and better maintainability through separation of concerns.

**Common Follow-up:** "Can you give me a real-world example where OOP is clearly better than procedural programming?"

**Strong Answer:** "Consider a banking system. In procedural programming, account data and transaction functions are separate; any function can access and modify account data directly, creating security risks. In OOP, each account is an object that exposes only specific methods for depositing, withdrawing, and querying balance. The internal balance is private; only the account's own methods can modify it. This encapsulation prevents accidental or unauthorized modification of account data."

---

**Q2: Explain the four pillars of OOP with examples.**

**Answer:**

**Encapsulation:** Bundling data and methods that operate on that data within a single unit (class) and restricting direct access to internal state. Example: a BankAccount class with a private `balance` field and public `deposit()`, `withdraw()`, and `getBalance()` methods. External code cannot directly modify `balance`; it must use the provided methods.

**Inheritance:** A mechanism where a new class (child/subclass) acquires properties and behaviors from an existing class (parent/superclass). Example: a `Vehicle` class with `speed` and `fuel` attributes. `Car` and `Motorcycle` classes extend `Vehicle`, inheriting these attributes while adding their own specific ones (`numberOfDoors` for Car, `hasSidecar` for Motorcycle).

**Polymorphism:** The ability of different objects to respond to the same message (method call) in different ways. Example: a `Shape` class with an `area()` method. `Circle`, `Rectangle`, and `Triangle` classes override `area()` with their own implementations. Calling `shape.area()` on a `Shape` reference produces different results depending on the actual object type at runtime.

**Abstraction:** Hiding complex implementation details and exposing only the essential features. Example: a `DatabaseConnection` class that exposes `connect()`, `query()`, and `disconnect()` methods without revealing the underlying connection pooling, authentication handling, or protocol specifics.

**Common Follow-up:** "What is the difference between abstraction and encapsulation?"

**Strong Answer:** "Encapsulation is about hiding data by making fields private and providing controlled access through public methods. Abstraction is about hiding complexity by presenting only what is necessary to the user of a class or interface. Encapsulation is the mechanism; abstraction is the design principle. A car dashboard is an abstraction: it exposes a steering wheel, pedals, and dials while hiding the engine mechanics. Encapsulation ensures each of those components is self-contained and controlled."

---

**Q3: What is the difference between method overloading and method overriding?**

**Answer:**

**Method Overloading (Compile-time Polymorphism):**
- Occurs within the same class.
- Two or more methods with the same name but different parameter lists (different number, type, or order of parameters).
- Resolved at compile time based on the method signature.
- Return type alone cannot differentiate overloaded methods.

```java
class Calculator {
    int add(int a, int b) { return a + b; }
    double add(double a, double b) { return a + b; }
    int add(int a, int b, int c) { return a + b + c; }
}
```

**Method Overriding (Runtime Polymorphism):**
- Occurs between a parent class and a child class.
- The child class provides its own implementation of a method that already exists in the parent class, with the same name and parameter list.
- Resolved at runtime based on the actual object type.
- The `@Override` annotation is recommended to make intent explicit.

```java
class Animal {
    void sound() { System.out.println("Some sound"); }
}
class Dog extends Animal {
    @Override
    void sound() { System.out.println("Bark"); }
}
```

**Common Follow-up:** "Can we override a static method in Java?"

**Strong Answer:** "No. Static methods belong to the class, not to any instance. When you define a method with the same signature as a parent's static method in a child class, this is called method hiding, not overriding. The method that gets called is determined by the reference type at compile time, not the object type at runtime. This is a fundamental distinction: polymorphism (runtime dispatch) does not apply to static methods."

---

**Q4: What is the difference between an abstract class and an interface in Java?**

**Answer:**

| Feature | Abstract Class | Interface |
|---------|---------------|-----------|
| Instantiation | Cannot be instantiated | Cannot be instantiated |
| Methods | Can have abstract and concrete methods | All methods abstract by default (Java 8+ allows default and static methods) |
| Variables | Can have instance variables of any type | Only public static final (constants) |
| Constructor | Can have constructors | Cannot have constructors |
| Inheritance | A class can extend only one abstract class | A class can implement multiple interfaces |
| Access modifiers | Methods can have any access modifier | Methods are implicitly public |
| When to use | When classes share common state AND behavior | When you want to define a contract without implementation |

**Common Follow-up:** "If a class implements two interfaces with the same default method, what happens?"

**Strong Answer:** "In Java 8 and above, this creates a compilation error. The implementing class must override the conflicting default method to resolve the ambiguity. The class can also explicitly invoke the desired interface's default method using the syntax InterfaceName.super.methodName(). This is the diamond problem for interfaces in Java, and the language forces the programmer to resolve it explicitly."

---

**Q5: What is a constructor? How is it different from a method?**

**Answer:**
A constructor is a special member of a class that is automatically called when an object of that class is created. Its purpose is to initialize the object's state.

**Key differences from a method:**
- A constructor has the same name as the class; a method can have any name.
- A constructor has no return type, not even void; methods always have a return type.
- A constructor is called automatically during object creation with `new`; methods are called explicitly on objects.
- If no constructor is defined, the compiler provides a default no-argument constructor; no such default exists for methods.
- Constructors cannot be inherited; they can only be invoked through the `super()` call from a child class constructor.

**Constructor types:**
- Default constructor: no parameters, initializes fields to default values.
- Parameterized constructor: takes parameters to initialize fields with specific values.
- Copy constructor: takes an object of the same class as a parameter and creates a new object with the same state.

**Common Follow-up:** "What is constructor chaining?"

**Strong Answer:** "Constructor chaining is the process of calling one constructor from another within the same class or from a parent class. Within the same class, `this()` is used to call another constructor of the same class. From a child class, `super()` is used to call a constructor of the parent class. The `this()` or `super()` call must be the first statement in the constructor body. Constructor chaining ensures that when any constructor is called, all necessary initialization in the class hierarchy happens in the correct order."

---

**Q6: What is the difference between IS-A and HAS-A relationships?**

**Answer:**

**IS-A relationship (Inheritance):** Represents a type hierarchy. If class B extends class A, then B IS-A A. Every instance of B is also an instance of A. Example: "A Dog IS-A Animal."

**HAS-A relationship (Composition):** Represents a part-whole or ownership relationship. If class A has an attribute of type B, then A HAS-A B. Example: "A Car HAS-A Engine."

The distinction is critical for good OOP design. Use inheritance (IS-A) when the subclass is genuinely a specialization of the parent class and substitutability makes sense. Use composition (HAS-A) when one class uses another class's functionality without being a type of it.

**Common Follow-up:** "Why is composition often preferred over inheritance?"

**Strong Answer:** "Composition is preferred because it avoids the tight coupling that inheritance creates. With inheritance, changes to the parent class can break child classes unexpectedly (the fragile base class problem). Composition allows the behavior to be changed at runtime by swapping the composed object. It also avoids the limitations of single inheritance in Java. The design principle 'favor composition over inheritance' encourages using composition when the IS-A relationship is not a genuine type relationship but merely a convenience for code reuse."

---

**Q7: Explain the concept of static in Java. What can be declared static?**

**Answer:**
The `static` keyword in Java indicates that a member belongs to the class itself rather than to any specific instance. Static members are shared across all instances of the class.

**What can be static:**

**Static variables (class variables):** Shared across all instances. One copy exists regardless of how many objects are created. Example: a counter tracking how many objects of a class have been created.

**Static methods:** Can be called on the class name directly without creating an object. Cannot access instance variables or instance methods directly (because there is no instance context). The `main()` method is static so the JVM can call it without creating an object.

**Static blocks:** Executed once when the class is loaded by the JVM, before any object is created. Used for complex static variable initialization.

**Static nested classes:** A nested class that does not require an instance of the outer class to be instantiated.

**Common Follow-up:** "Can we override a static method? Can we access a non-static variable from a static method?"

**Strong Answer:** "Static methods cannot be overridden (as explained in the polymorphism question). Regarding accessing non-static variables: no, a static method cannot access instance variables or call instance methods directly. This is because static methods run in a class context, and instance variables only exist in the context of a specific object instance. There is no implicit 'this' reference in a static method. To access instance data from a static method, you must pass an object reference as a parameter and access the data through that reference."

---

**Q8b: What is the Java memory model? Explain the heap and stack.**

**Answer:**
The Java runtime memory is divided into several regions. The two most important for freshers to understand are the heap and the stack.

**Stack Memory:**
- Stores method frames: local variables, method parameters, and return addresses.
- Each thread has its own stack; they do not share stack memory.
- Memory is allocated when a method is called and deallocated when the method returns (LIFO).
- Stores references to heap objects, and primitive values (int, boolean, char, etc.) directly.
- Fixed size (configured by JVM flags); stack overflow occurs when it is exceeded (typically through deep recursion).
- Faster to allocate and deallocate than heap memory.

**Heap Memory:**
- Stores all objects created with the `new` keyword and all instance variables.
- Shared across all threads.
- Managed by the Garbage Collector (GC), which automatically reclaims memory from objects that are no longer reachable.
- Larger than the stack but slower to allocate.
- Divided into generations for GC efficiency: Young Generation (Eden space + Survivor spaces) for newly created objects, Old Generation (Tenured space) for long-lived objects, and Metaspace (formerly PermGen) for class metadata.

**Common Follow-up:** "What is the difference between stack and heap allocation in terms of performance?"

**Strong Answer:** "Stack allocation is faster because it is simply a pointer increment or decrement (LIFO discipline). There is no need for garbage collection because memory is automatically freed when the method returns. Heap allocation requires the JVM to find a free block of the appropriate size, which takes more time. However, heap allocation allows objects to survive beyond the method that created them, which stack allocation cannot. This is why long-lived objects (like objects stored in a data structure or passed between methods) must go on the heap. The GC overhead is the main heap performance concern: 'stop-the-world' GC pauses can affect latency-sensitive applications, which is why GC tuning is an important topic in production Java systems."

---

**Q8c: What is the final keyword in Java? What can be declared final?**

**Answer:**
The `final` keyword in Java prevents modification. What it means depends on what it is applied to:

**Final variable:** The variable can be assigned only once. For primitive variables, the value cannot change. For object references, the reference cannot point to a different object, but the object itself can still be modified (its fields can change). A final field must be initialized either at declaration or in the constructor.

```java
final int MAX = 100; // MAX can never change
final List<String> list = new ArrayList<>(); // list can't point elsewhere
list.add("item"); // But this IS allowed: the list's contents can change
```

**Final method:** The method cannot be overridden in a subclass. Used to prevent subclasses from changing the behavior of a specific method while still allowing inheritance of the class.

**Final class:** The class cannot be subclassed. The String class in Java is final, which is why you cannot extend String. This guarantees the immutability and security properties of String across the entire codebase.

**Common Follow-up:** "How does the final keyword relate to immutability?"

**Strong Answer:** "A class is truly immutable when: it is declared final (preventing subclasses from adding mutable state or overriding methods), all fields are private and final, no setter methods exist, and the class returns defensive copies of any mutable objects it contains (not references to internal mutable state). Java's String class exemplifies this: it is final, stores characters in a private final array, and all methods that appear to modify the String return new String objects. Immutability is valuable for thread safety (immutable objects can be safely shared between threads without synchronization), caching (you can safely cache and reuse immutable objects), and reliability (a method cannot unintentionally modify an immutable parameter)."

---

**Q8: What is the difference between == and .equals() in Java?**

**Answer:**

**== operator:** Compares references (memory addresses) for objects, not content. For primitive types, it compares values. `String a = new String("hello"); String b = new String("hello"); a == b` is `false` because `a` and `b` point to different objects in memory.

**.equals() method:** Compares the content of objects. By default (from Object class), it is the same as `==`. However, classes like `String`, `Integer`, and other wrapper classes override `equals()` to compare content. `a.equals(b)` for the strings above returns `true` because both contain "hello".

**Important caveat:** String literals in Java are stored in the String pool. `String a = "hello"; String b = "hello"; a == b` is `true` because both point to the same object in the pool. This is a source of confusion; the safe practice is always to use `.equals()` for content comparison of objects.

**Common Follow-up:** "What is the contract between equals() and hashCode()?"

**Strong Answer:** "Java's contract states: if two objects are equal according to equals(), they must return the same hashCode(). However, two objects with the same hashCode() are not required to be equal (hash collisions are allowed). This contract matters for correct behavior in hash-based collections like HashMap and HashSet. If you override equals() without overriding hashCode(), objects that are 'equal' by your equals() definition may have different hash codes, causing them to be placed in different buckets in a HashMap, and the collection will fail to find objects that should be considered the same key."

---

## Java Fundamentals: Questions and Answers

---

**Q9: What is the difference between ArrayList and LinkedList in Java?**

**Answer:**

**ArrayList:**
- Backed by a dynamic array.
- Random access is O(1) (get by index is fast).
- Insertion/deletion at arbitrary positions is O(n) because elements must be shifted.
- Better memory locality (contiguous memory), which helps CPU cache performance.
- Use when: frequent reading by index, infrequent insertion/deletion in the middle.

**LinkedList:**
- Backed by a doubly linked list.
- Sequential access; random access is O(n) because the list must be traversed.
- Insertion/deletion at known positions is O(1) (just update pointers).
- Higher memory overhead (each node stores two extra references: next and previous).
- Use when: frequent insertion/deletion at the beginning or end, rare random access.
- Implements both List and Deque interfaces, so it can be used as a queue or stack.

**Common Follow-up:** "In practice, when should you actually use LinkedList over ArrayList?"

**Strong Answer:** "Honestly, ArrayList outperforms LinkedList in most real-world scenarios because of better cache performance and lower memory overhead. The O(1) insertion of LinkedList sounds appealing, but in practice finding the position to insert at still takes O(n) traversal. The primary use case where LinkedList genuinely wins is when you need to use it as a queue or deque, frequently adding and removing from both ends. For most list operations, ArrayList is the correct default choice."

---

**Q10: What are Java exceptions? Explain checked vs unchecked exceptions.**

**Answer:**
An exception is an event that disrupts the normal flow of a program's execution. Java's exception handling mechanism (try-catch-finally) allows programs to respond to exceptional conditions gracefully rather than crashing.

**Checked Exceptions:**
- Subclasses of Exception (but not RuntimeException).
- The compiler requires that these be either caught (try-catch) or declared (throws clause).
- Represent conditions that a reasonable program might want to recover from.
- Examples: IOException, SQLException, ClassNotFoundException.
- The programmer must explicitly handle them or declare them, making the code explicitly aware of potential failure modes.

**Unchecked Exceptions:**
- Subclasses of RuntimeException (or Error).
- The compiler does not require them to be caught or declared.
- Represent programming errors that are either unrecoverable (Errors like OutOfMemoryError) or indicate bugs in the code (RuntimeException subclasses).
- Examples: NullPointerException, ArrayIndexOutOfBoundsException, IllegalArgumentException, ClassCastException.

**Common Follow-up:** "Should you catch RuntimeException in your application code?"

**Strong Answer:** "Generally no, for two reasons. First, RuntimeExceptions typically indicate programming bugs (null dereferences, array out of bounds), and catching them hides bugs rather than fixing them. The correct response to a NullPointerException is to fix the null handling in your code, not to catch the exception. Second, catching broad RuntimeException creates code that silently absorbs errors, making debugging extremely difficult. The acceptable use case for catching RuntimeException is at the application boundary (like a web request handler) to prevent crashes from unhandled exceptions reaching the user, while logging the full stack trace for debugging."

---

**Q11: What is the difference between String, StringBuilder, and StringBuffer in Java?**

**Answer:**

**String:**
- Immutable: once created, cannot be changed. Any operation that appears to modify a String actually creates a new String object.
- Thread-safe due to immutability.
- Stored in the String pool; string literals with the same content share the same object.
- Repeated concatenation in a loop is very inefficient because it creates a new String object at each step.

**StringBuilder:**
- Mutable: modification methods (append, insert, delete, reverse) modify the same object in place.
- Not thread-safe: should not be shared between threads without external synchronization.
- Preferred for string manipulation within a single thread (the typical use case).
- Much more efficient than String for repeated concatenation.

**StringBuffer:**
- Mutable, like StringBuilder.
- Thread-safe: all methods are synchronized.
- Slower than StringBuilder due to synchronization overhead.
- Use only when the string object is being modified by multiple threads simultaneously.

**Common Follow-up:** "What does the Java compiler do with String concatenation using the + operator?"

**Strong Answer:** "In Java, the compiler converts String concatenation with + into StringBuilder operations during compilation. `String s = 'Hello' + ' ' + 'World'` becomes `new StringBuilder('Hello').append(' ').append('World').toString()`. However, this optimization happens statement by statement. In a loop, `s = s + element` creates a new StringBuilder object at each iteration, which is inefficient. The explicit use of a single StringBuilder outside the loop, with append() calls inside, is the correct practice for loop-based string construction."

---

**Q12: What is the Java Collections Framework? Name its key interfaces.**

**Answer:**
The Java Collections Framework (JCF) is a unified architecture for representing and manipulating collections of objects. It provides ready-to-use data structures and algorithms through a set of interfaces and their implementations.

**Key Interfaces:**

**Collection:** Root interface of the framework. Represents a group of objects.

**List:** Ordered collection allowing duplicates. Key implementations:
- ArrayList: resizable array
- LinkedList: doubly linked list
- Vector: synchronized ArrayList (legacy)

**Set:** Unordered collection, no duplicates. Key implementations:
- HashSet: hash table, O(1) operations, no order guarantee
- LinkedHashSet: maintains insertion order
- TreeSet: sorted order, O(log n) operations

**Queue:** Ordered collection for FIFO (First-In-First-Out) operations. Key implementations:
- LinkedList
- PriorityQueue: priority-based ordering

**Map:** Key-value pairs, no duplicate keys. Note: Map does NOT extend Collection. Key implementations:
- HashMap: O(1) operations, no order guarantee
- LinkedHashMap: maintains insertion order
- TreeMap: sorted by key, O(log n) operations
- Hashtable: synchronized HashMap (legacy)

**Common Follow-up:** "What is the difference between a Set and a List? When would you use each?"

**Strong Answer:** "A List maintains insertion order and allows duplicate elements. A Set does not guarantee order (except LinkedHashSet and TreeSet) and does not allow duplicates. Use a List when order matters and duplicates are expected or acceptable, such as a list of transactions or a log of events. Use a Set when you need to track unique items and duplicates should be eliminated, such as tracking which users have visited a page, or collecting unique words in a document. The Set's contains() operation is typically O(1) for HashSet versus O(n) for ArrayList, making Set the clear choice when frequent membership checking is required."

---

**Q13: What is a HashMap in Java? How does it work internally?**

**Answer:**
A HashMap is a hash-table-based implementation of the Map interface. It stores key-value pairs and allows null keys and null values. It does not maintain insertion order and is not synchronized.

**Internal Working:**

1. **Hashing:** When a key-value pair is put into the HashMap, Java calls `hashCode()` on the key to compute a hash code.

2. **Index Calculation:** The hash code is processed (using bit manipulation) to compute an index in an internal array of "buckets."

3. **Bucket:** Each bucket holds a linked list (or a red-black tree in Java 8+ when the list grows beyond a threshold of 8 entries) of entries that hash to the same index.

4. **Collision Handling:** When two keys hash to the same bucket (collision), the new entry is added to the bucket's linked list. When retrieving, Java traverses the list and uses `equals()` to find the exact key.

5. **Load Factor and Resizing:** The default load factor is 0.75. When the number of entries exceeds (capacity × load factor), the HashMap resizes (doubles the array) and rehashes all entries. Resizing is expensive, so choosing an appropriate initial capacity can improve performance.

**Common Follow-up:** "Why must an object used as a HashMap key correctly override both equals() and hashCode()?"

**Strong Answer:** "Because HashMap uses hashCode() to find the bucket and equals() to find the exact key within the bucket. If equals() is overridden without hashCode(): two objects that are 'equal' by your equals() definition may have different hash codes, so they end up in different buckets. The HashMap cannot find the second object by looking up the first, even though they are 'equal.' Conversely, if hashCode() is overridden without equals(): objects with the same hash code collide in the same bucket, but since equals() still compares references, the HashMap treats them as different keys. Both methods must be consistent for correct HashMap behavior."

---

## Database Management System: Questions and Answers

---

**Q14: What is normalization? Explain the normal forms.**

**Answer:**
Normalization is the process of organizing a relational database schema to reduce data redundancy and improve data integrity. It involves decomposing tables into smaller, more focused tables while defining relationships between them.

**First Normal Form (1NF):**
- Each column contains atomic (indivisible) values.
- No repeating groups or arrays in a single column.
- Each row is unique (there is a primary key).
- Violation example: a column "phone_numbers" containing "9876543210, 9123456789."
- Fix: separate phone numbers into their own table with a foreign key.

**Second Normal Form (2NF):**
- Must be in 1NF.
- No partial dependency: non-key attributes must depend on the entire primary key, not just part of it.
- Applies only when the primary key is composite.
- Violation example: In a table (StudentID, CourseID, StudentName, CourseName), StudentName depends only on StudentID (partial dependency), and CourseName depends only on CourseID.
- Fix: Separate into Students(StudentID, StudentName) and Courses(CourseID, CourseName) and Enrollments(StudentID, CourseID).

**Third Normal Form (3NF):**
- Must be in 2NF.
- No transitive dependency: non-key attributes must not depend on other non-key attributes.
- Violation example: In a table (EmployeeID, DepartmentID, DepartmentName), DepartmentName depends on DepartmentID (non-key), not directly on EmployeeID.
- Fix: Separate into Employees(EmployeeID, DepartmentID) and Departments(DepartmentID, DepartmentName).

**Boyce-Codd Normal Form (BCNF):**
- A stricter version of 3NF.
- Every determinant must be a candidate key.
- Addresses anomalies that 3NF misses in tables with multiple overlapping candidate keys.

**Common Follow-up:** "Is it always desirable to normalize to the highest normal form?"

**Strong Answer:** "No. Normalization improves data integrity and reduces redundancy, but it comes at the cost of query complexity and sometimes performance. Highly normalized schemas require many joins to retrieve related data, which can slow read-heavy applications. Denormalization, intentionally introducing redundancy, is a common technique in data warehouses and analytical systems where read performance is prioritized over write efficiency and data integrity is managed at the application level. The right level of normalization depends on the use case: transactional systems (OLTP) typically normalize to 3NF or BCNF; analytical systems (OLAP) often use star or snowflake schemas that are intentionally denormalized."

---

**Q15: What are the ACID properties of a database transaction?**

**Answer:**

**Atomicity:** A transaction is treated as a single unit. Either all operations in the transaction succeed and are committed, or none of them are applied and the database is rolled back to its state before the transaction started. Example: A bank transfer debiting one account and crediting another must either complete entirely or not at all.

**Consistency:** A transaction takes the database from one valid state to another valid state. All defined rules (constraints, cascades, triggers) must be satisfied after the transaction. A transaction that would violate a NOT NULL constraint or a foreign key constraint is rejected.

**Isolation:** Concurrent transactions execute as if they were serial (sequential). The intermediate state of a transaction is not visible to other transactions. The degree of isolation is controlled by isolation levels (Read Uncommitted, Read Committed, Repeatable Read, Serializable).

**Durability:** Once a transaction is committed, it remains committed even if the system subsequently fails. Changes are persisted to non-volatile storage. This is typically achieved through write-ahead logging (WAL).

**Common Follow-up:** "What are the concurrency problems that isolation is meant to prevent?"

**Strong Answer:** "There are three classic concurrency problems. A dirty read occurs when Transaction A reads data that Transaction B has modified but not yet committed; if B rolls back, A has read data that never actually existed. A non-repeatable read occurs when Transaction A reads the same row twice during its execution and gets different results because Transaction B committed a change between the two reads. A phantom read occurs when Transaction A executes a range query twice and gets different sets of rows because Transaction B inserted or deleted rows matching the range condition between the two queries. Each isolation level prevents a different subset of these problems, with Serializable preventing all three at the cost of the most concurrency restriction."

---

**Q16: What are indexes in a database? What are the trade-offs?**

**Answer:**
An index is a data structure (typically a B-tree or hash table) that the database maintains to allow faster retrieval of rows from a table based on the values in one or more columns. Without an index, a query on a non-key column requires a full table scan.

**How indexes work:** An index on a column stores the values of that column in sorted order, along with pointers to the actual table rows. A query on that column can use a binary search on the index instead of a sequential scan of the table.

**Types:**
- **Clustered index:** The table's physical data rows are sorted and stored according to the index key. There can be only one per table (typically the primary key). Reading by the clustered index key is fastest because the data is at the index itself.
- **Non-clustered index:** A separate structure from the table data, containing the index key and a pointer to the actual row. A table can have multiple non-clustered indexes.
- **Composite index:** An index on multiple columns, useful for queries that filter or sort on multiple columns.

**Trade-offs:**
- **Faster reads:** The primary benefit. Indexed columns can be searched in O(log n) instead of O(n).
- **Slower writes:** Every INSERT, UPDATE, or DELETE must also update the index structure. Tables with many indexes are significantly slower for write operations.
- **Storage overhead:** Each index requires additional disk space proportional to the size of the indexed data.
- **Over-indexing:** More indexes does not always mean faster queries; the query optimizer may choose an index suboptimally, or index maintenance overhead may dominate for write-heavy tables.

**Common Follow-up:** "How does a query optimizer decide whether to use an index?"

**Strong Answer:** "The query optimizer estimates the cost of different execution plans and chooses the cheapest. For an index, the key factor is selectivity: how many rows are expected to match the query condition. If a query has high selectivity (few matching rows, like filtering on a unique ID), using the index is much faster than a full scan. If selectivity is low (like filtering on a boolean column where half the rows match), a full scan may be cheaper because following many index pointers to scattered rows (random I/O) is slower than sequentially reading the entire table. The optimizer uses statistics (collected by ANALYZE or equivalent) to estimate selectivity."

---

**Q16b: What are SQL joins? Explain each type with an example.**

**Answer:**
A JOIN combines rows from two or more tables based on a related column.

**INNER JOIN:** Returns only rows where the join condition is met in both tables. Rows without a match in either table are excluded.

```sql
-- Returns only employees who have a department
SELECT e.Name, d.DeptName
FROM Employees e
INNER JOIN Departments d ON e.DeptID = d.DeptID;
```

**LEFT OUTER JOIN (LEFT JOIN):** Returns all rows from the left table, plus matching rows from the right table. Where there is no match, right table columns return NULL.

```sql
-- Returns ALL employees, with NULL DeptName for employees with no department
SELECT e.Name, d.DeptName
FROM Employees e
LEFT JOIN Departments d ON e.DeptID = d.DeptID;
```

**RIGHT OUTER JOIN (RIGHT JOIN):** Returns all rows from the right table, plus matching rows from the left table. Less commonly used; can always be rewritten as a LEFT JOIN by swapping the tables.

**FULL OUTER JOIN:** Returns all rows from both tables. Where there is no match on either side, the missing columns return NULL.

```sql
-- Returns all employees and all departments, with NULLs where there is no match
SELECT e.Name, d.DeptName
FROM Employees e
FULL OUTER JOIN Departments d ON e.DeptID = d.DeptID;
```

**CROSS JOIN:** Returns the Cartesian product: every row from the left table paired with every row from the right table. No join condition. Rarely used directly; can be useful for generating combinations.

**SELF JOIN:** Joining a table with itself. Uses table aliases to treat the same table as two different tables.

```sql
-- Find employees and their managers
SELECT e.Name AS Employee, m.Name AS Manager
FROM Employees e
LEFT JOIN Employees m ON e.ManagerID = m.EmpID;
```

---

**Q16c: What is a view in SQL? What are its benefits?**

**Answer:**
A view is a virtual table defined by a SQL SELECT query. It does not store data itself; it presents data from one or more underlying tables. When you query a view, the database executes the defining query and returns the results.

**Benefits:**

**Simplification:** Complex joins or subqueries can be encapsulated in a view, allowing simple SELECT queries on the view. Instead of writing a complex 5-table join every time, users query the view with a simple SELECT.

**Security:** Views can expose only specific columns or rows to users, hiding sensitive data. A view on the Employees table might exclude the Salary column for users without HR privileges.

**Data independence:** If the underlying table structure changes, the view can be updated to maintain the same interface for applications that use it, avoiding breaking changes to application queries.

**Reusability:** Frequently used complex queries are defined once and reused across many applications.

**Limitations:** Most databases do not allow INSERT, UPDATE, or DELETE on complex views (views with joins, aggregations, or DISTINCT). Simple views on a single table can often be updated. Materialized views (some databases) store the query results and must be periodically refreshed, trading currency for performance.

---

**Q16d: What is a stored procedure? How does it differ from a function?**

**Answer:**
A stored procedure is a precompiled set of SQL statements stored in the database that can be called by name. It can perform DML operations (INSERT, UPDATE, DELETE) and may or may not return a value.

A function is similar but is designed to compute and return a single value (or a table in table-valued functions). Functions can be used in SQL expressions and SELECT statements; procedures cannot. Functions must return a value; procedures may or may not return values (via OUT parameters).

**Stored procedure advantages:**
- Reduced network traffic: multiple SQL operations execute server-side in one call instead of many round trips.
- Precompiled: the execution plan is cached, improving performance for repeated calls.
- Security: users can be granted EXECUTE permission on a procedure without direct table access.
- Encapsulation: business logic is centralized in the database rather than duplicated across multiple application layers.

**Common Follow-up:** "When would you use a stored procedure versus writing the SQL in application code?"

**Strong Answer:** "Stored procedures are best when the logic is primarily data-manipulation that operates on large data sets that are better processed at the database server than by pulling data into the application layer. They are also appropriate when consistent data access rules must be enforced regardless of which application accesses the database. However, stored procedures have drawbacks: they are harder to version control, test, and debug than application code; they create tight coupling between the application and the database; and they make it harder to migrate to a different database. The modern trend is to handle business logic in the application layer and use the database primarily for data storage, keeping SQL in the application code where it can be version-controlled, unit-tested, and maintained like any other code."

---

## SQL Queries: Practical Questions and Solutions

SQL query questions are a guaranteed part of the Infosys technical interview. These are not just definitional but require writing actual queries.

**Schema used in the following questions:**

```sql
Employees (EmpID, Name, DeptID, Salary, ManagerID, JoiningDate)
Departments (DeptID, DeptName, Location)
```

---

**Q17: Write a query to find the second highest salary from the Employees table.**

**Answer:**
```sql
-- Method 1: Using subquery
SELECT MAX(Salary)
FROM Employees
WHERE Salary < (SELECT MAX(Salary) FROM Employees);

-- Method 2: Using LIMIT/OFFSET (MySQL/PostgreSQL)
SELECT DISTINCT Salary
FROM Employees
ORDER BY Salary DESC
LIMIT 1 OFFSET 1;

-- Method 3: Using DENSE_RANK (works for nth highest)
SELECT Salary
FROM (
    SELECT Salary, DENSE_RANK() OVER (ORDER BY Salary DESC) AS rnk
    FROM Employees
) ranked
WHERE rnk = 2;
```

**When to use each:** Method 1 works in all SQL dialects but only for second highest. Method 2 is clean but LIMIT syntax varies by database. Method 3 is the most generalizable and can be modified to find any nth highest salary.

**Common Follow-up:** "What happens if there are multiple employees with the same highest salary?"

**Strong Answer:** "Method 1 correctly handles this because MAX() returns the highest value regardless of how many rows have it, and the WHERE clause excludes all rows at that maximum, then finds the next MAX. DENSE_RANK() also handles it correctly because all ties at the same salary get the same rank number. ROW_NUMBER() would NOT handle it correctly because it assigns unique row numbers, so some tied employees would be ranked 2nd and others 3rd arbitrarily."

---

**Q18: Write a query to find all employees who earn more than the average salary in their department.**

**Answer:**
```sql
SELECT e.EmpID, e.Name, e.Salary, e.DeptID
FROM Employees e
WHERE e.Salary > (
    SELECT AVG(Salary)
    FROM Employees
    WHERE DeptID = e.DeptID
);
```

This is a correlated subquery because the subquery references the outer query's row (e.DeptID). The subquery executes once for each row in the outer query.

**Alternative using JOIN:**
```sql
SELECT e.EmpID, e.Name, e.Salary, e.DeptID
FROM Employees e
JOIN (
    SELECT DeptID, AVG(Salary) AS AvgSalary
    FROM Employees
    GROUP BY DeptID
) dept_avg ON e.DeptID = dept_avg.DeptID
WHERE e.Salary > dept_avg.AvgSalary;
```

The JOIN approach computes department averages once and is generally more efficient than the correlated subquery, which recomputes the average for each row.

---

**Q19: Write a query to display each department name along with the number of employees in it, including departments with no employees.**

**Answer:**
```sql
SELECT d.DeptName, COUNT(e.EmpID) AS EmployeeCount
FROM Departments d
LEFT JOIN Employees e ON d.DeptID = e.DeptID
GROUP BY d.DeptID, d.DeptName
ORDER BY EmployeeCount DESC;
```

**Key points:** LEFT JOIN is essential here. If INNER JOIN were used, departments with no employees would be excluded from the result. With LEFT JOIN, departments with no employees appear with NULL for all Employee columns, and COUNT(e.EmpID) returns 0 for those (because COUNT on a column ignores NULLs).

**Common Follow-up:** "What is the difference between COUNT(*) and COUNT(column_name)?"

**Strong Answer:** "COUNT(*) counts all rows including those with NULL values in any column. COUNT(column_name) counts only the rows where that specific column is NOT NULL. This distinction is critical in LEFT JOIN results: COUNT(e.EmpID) correctly returns 0 for departments with no employees, while COUNT(*) would return 1 for every row in the result, including the NULL-EmpID rows from departments with no employees, giving an incorrect count of 1 instead of 0."

---

**Q20: Write a query to find employees who are managers (appear as ManagerID of someone else).**

**Answer:**
```sql
-- Method 1: Using IN
SELECT EmpID, Name
FROM Employees
WHERE EmpID IN (
    SELECT DISTINCT ManagerID
    FROM Employees
    WHERE ManagerID IS NOT NULL
);

-- Method 2: Using EXISTS
SELECT e.EmpID, e.Name
FROM Employees e
WHERE EXISTS (
    SELECT 1
    FROM Employees
    WHERE ManagerID = e.EmpID
);

-- Method 3: Self JOIN
SELECT DISTINCT m.EmpID, m.Name
FROM Employees e
JOIN Employees m ON e.ManagerID = m.EmpID;
```

**Common Follow-up:** "Which is more efficient: IN or EXISTS?"

**Strong Answer:** "The performance depends on the specific database engine and the relative sizes of the tables. EXISTS short-circuits: it stops as soon as it finds one matching row, making it efficient when the subquery result is large but each individual check is likely to find a match early. IN evaluates the entire subquery first and then checks membership. For modern query optimizers, the difference is often negligible because the optimizer can rewrite one as the other internally. However, EXISTS is generally preferred when the subquery contains NULLs, because IN with a subquery containing NULLs can produce unexpected results: if any NULL exists in the subquery result, `value NOT IN (subquery with NULL)` returns NULL (which is treated as false), potentially excluding rows incorrectly."

---

**Q21: Write a query to find all employees along with their manager's name. Employees who have no manager should also be shown.**

**Answer:**
```sql
SELECT 
    e.EmpID,
    e.Name AS EmployeeName,
    m.Name AS ManagerName
FROM Employees e
LEFT JOIN Employees m ON e.ManagerID = m.EmpID;
```

This is a self-join using a LEFT JOIN. The Employees table is joined to itself, treating the first instance as employee records and the second as manager records. LEFT JOIN ensures employees with no manager (ManagerID IS NULL) are included with NULL in the ManagerName column.

---

**Q22: Write a query to find the department(s) with the highest total salary bill.**

**Answer:**
```sql
SELECT d.DeptName, SUM(e.Salary) AS TotalSalary
FROM Departments d
JOIN Employees e ON d.DeptID = e.DeptID
GROUP BY d.DeptID, d.DeptName
HAVING SUM(e.Salary) = (
    SELECT MAX(TotalSalary)
    FROM (
        SELECT SUM(Salary) AS TotalSalary
        FROM Employees
        GROUP BY DeptID
    ) dept_totals
);
```

**HAVING vs WHERE explanation:** WHERE filters individual rows before grouping. HAVING filters the aggregated groups after GROUP BY. HAVING is used here because we need to filter based on the aggregate function SUM(e.Salary), which cannot appear in a WHERE clause.

---

## Operating Systems: Questions and Answers

---

**Q23: What is a process? How is it different from a program and a thread?**

**Answer:**

**Program:** A static set of instructions stored on disk. It is passive: just a file until executed.

**Process:** An active instance of a program in execution. When a program is loaded into memory and execution begins, it becomes a process. A process has its own: memory space (code, data, heap, stack), process control block (PCB) containing its state, CPU registers, process ID (PID), and file descriptors. Multiple processes run in isolation from each other by default.

**Thread:** The smallest unit of execution within a process. Multiple threads within the same process share: the process's memory space (code, data, heap), file descriptors, and other resources. Each thread has its own stack and CPU register state. Threads within a process can communicate and share data directly (no IPC mechanisms needed), but this shared memory requires synchronization to prevent race conditions.

**Key differences:**
- Process: heavyweight, separate memory, slow context switching, isolated.
- Thread: lightweight, shared memory within process, fast context switching, must synchronize shared data access.

**Common Follow-up:** "What is a context switch? Why is it expensive?"

**Strong Answer:** "A context switch is when the CPU stops executing one process (or thread) and starts executing another. For processes, this involves saving the full state of the current process (all CPU registers, program counter, memory mapping) to its PCB, loading the state of the next process from its PCB, and potentially flushing the CPU's translation lookaside buffer (TLB) because the memory mapping changes. This overhead is why context switching is expensive: not just the state save/restore, but the cache invalidation that follows. After a context switch, the new process starts with a cold cache, causing cache misses on data it accesses. Thread context switches are lighter because the memory mapping stays the same, but they still involve register save/restore."

---

**Q24: What is deadlock? What are its necessary conditions?**

**Answer:**
A deadlock is a state in which a group of processes are each waiting for a resource held by another process in the group, resulting in a circular wait where none can proceed.

**The four necessary conditions (Coffman's conditions):**

**Mutual Exclusion:** At least one resource must be held in a non-shareable mode; only one process can use it at a time. If another process requests it, the requesting process must wait.

**Hold and Wait:** A process holding at least one resource is waiting to acquire additional resources that are currently held by other processes.

**No Preemption:** Resources cannot be forcibly taken from a process; they must be released voluntarily by the process holding them.

**Circular Wait:** A set of processes {P1, P2, ..., Pn} must exist such that P1 is waiting for a resource held by P2, P2 is waiting for P3, ..., Pn is waiting for P1.

All four conditions must hold simultaneously for a deadlock to occur. Deadlock prevention strategies eliminate one or more of these conditions.

**Common Follow-up:** "How do operating systems handle deadlock?"

**Strong Answer:** "There are four strategies. Deadlock prevention eliminates one of the necessary conditions by design (for example, requiring processes to request all resources they need at once eliminates hold-and-wait). Deadlock avoidance uses algorithms like Banker's Algorithm to check before granting resource requests whether the grant keeps the system in a 'safe state' where completion of all processes is guaranteed. Deadlock detection allows deadlocks to occur and periodically runs a detection algorithm on the resource allocation graph, then resolves detected deadlocks by terminating processes or preempting resources. Finally, deadlock ignorance is used when the cost of detection and prevention outweighs the rarity of deadlocks; this is the approach taken by most modern operating systems including Windows and Unix for certain resource types."

---

**Q25: What is the difference between paging and segmentation in memory management?**

**Answer:**

**Paging:**
- Physical memory is divided into fixed-size frames; logical memory is divided into equal-size pages.
- A page table maps logical pages to physical frames.
- The process's logical address space is divided into pages of the same size as frames.
- Pages may not correspond to any logical division in the program; they are a purely physical convenience.
- Eliminates external fragmentation (all frames are the same size).
- Still has internal fragmentation (the last page of a process may not be fully used).
- Virtual memory is easily implemented by swapping individual pages.

**Segmentation:**
- Memory is divided into variable-size segments that correspond to logical divisions of the program: code segment, data segment, stack segment, and so on.
- A segment table maps (segment number, offset) logical addresses to physical addresses.
- Segments can grow and shrink independently.
- No internal fragmentation (each segment is exactly as large as needed).
- External fragmentation occurs over time as segments are allocated and deallocated, leaving gaps.
- Supports sharing of code segments between processes.

**Modern systems typically use both:** logical segmentation at the user level is implemented on top of physical paging.

---

**Q26: What are the CPU scheduling algorithms? Compare them.**

**Answer:**

**First Come First Serve (FCFS):**
- Processes are executed in the order they arrive.
- Simple to implement.
- Non-preemptive.
- Can cause convoy effect: a long process at the front delays all shorter processes.
- Average waiting time is generally high.

**Shortest Job First (SJF):**
- Executes the process with the smallest expected burst time next.
- Optimal for minimizing average waiting time.
- Practical challenge: requires knowing the burst time in advance (estimated or predicted).
- Non-preemptive version: FCFS for ties.
- Preemptive version (SRTF - Shortest Remaining Time First): if a new shorter process arrives, it preempts the current one.

**Round Robin:**
- Each process gets a small unit of CPU time (time quantum), typically 10-100ms.
- After the time quantum expires, the process is preempted and added to the end of the ready queue.
- Designed for time-sharing systems.
- No process waits more than (n-1) × time_quantum.
- Performance depends heavily on time quantum: too small increases context switch overhead; too large degrades to FCFS.

**Priority Scheduling:**
- Each process is assigned a priority; higher priority processes execute first.
- Can be preemptive or non-preemptive.
- Problem: starvation (low-priority processes may never execute if high-priority processes keep arriving).
- Solution: aging (gradually increasing priority of waiting processes).

**Multilevel Queue Scheduling:**
- Multiple queues for different categories of processes (interactive, system, batch), each with its own scheduling algorithm.

---

## Computer Networks: Questions and Answers

---

**Q27: What is the OSI model? Explain each layer.**

**Answer:**
The OSI (Open Systems Interconnection) model is a conceptual framework that describes how different network protocols interact in a layered architecture. It has 7 layers:

**Layer 7 - Application:** The interface between the application and the network. Protocols: HTTP, HTTPS, FTP, SMTP, DNS, SSH. Provides services directly to user applications.

**Layer 6 - Presentation:** Translates data formats (encoding, encryption, compression). Ensures data from the application layer of one system can be read by the application layer of another. Examples: SSL/TLS (encryption), JPEG/MPEG (compression).

**Layer 5 - Session:** Manages sessions (connections) between applications. Establishes, maintains, and terminates dialogues. Handles session recovery after network failures.

**Layer 4 - Transport:** End-to-end communication, error recovery, flow control. Key protocols: TCP (reliable, connection-oriented) and UDP (unreliable, connectionless). Handles port numbers to multiplex multiple applications.

**Layer 3 - Network:** Logical addressing and routing. Determines how data is routed from source to destination across multiple networks. Key protocol: IP (Internet Protocol). Devices: routers.

**Layer 2 - Data Link:** Physical addressing (MAC addresses), frame synchronization, error detection on a single network link. Divided into LLC (Logical Link Control) and MAC (Media Access Control) sublayers. Devices: switches, bridges.

**Layer 1 - Physical:** Transmission of raw bits over a physical medium. Defines electrical signals, cable types, connectors, and transmission rates. Devices: hubs, repeaters, cables.

**Memory trick:** "All People Seem To Need Data Processing" (Application, Presentation, Session, Transport, Network, Data Link, Physical).

**Common Follow-up:** "Why does the TCP/IP model have fewer layers than OSI?"

**Strong Answer:** "The TCP/IP model (also called the Internet model) was developed from practical implementation experience rather than from a theoretical design exercise. It has four layers: Application (combining OSI's Application, Presentation, and Session), Transport, Internet (equivalent to OSI's Network), and Network Access (combining OSI's Data Link and Physical). The OSI model's Presentation and Session layers are rarely distinct in practice; most application protocols handle their own encoding and session management within the application layer itself. The TCP/IP model is more practical and maps directly to how the internet actually works, while OSI is more useful as a conceptual framework for understanding protocol relationships."

---

**Q28: What is the difference between TCP and UDP?**

**Answer:**

| Feature | TCP | UDP |
|---------|-----|-----|
| Connection | Connection-oriented (3-way handshake) | Connectionless |
| Reliability | Reliable: guarantees delivery, ordering, and error checking | Unreliable: no delivery guarantee |
| Speed | Slower due to overhead | Faster, lower latency |
| Flow Control | Yes | No |
| Congestion Control | Yes | No |
| Header Size | 20-60 bytes | 8 bytes |
| Use Cases | Web browsing, file transfer, email | Video streaming, online gaming, DNS, VoIP |

**TCP's three-way handshake:**
1. Client sends SYN (synchronize) to server.
2. Server responds with SYN-ACK (synchronize-acknowledge).
3. Client sends ACK (acknowledge). Connection established.

**When UDP is preferred:** When speed matters more than reliability and the application can tolerate some packet loss. DNS uses UDP because queries are short and a lost query simply times out and retries. Video streaming uses UDP because retransmitting a delayed video frame is pointless; it is better to skip it and continue.

---

**Q29: What happens when you type a URL in a browser? Explain the full process.**

**Answer:**
This is a system design question disguised as a networking question. The complete flow:

1. **DNS Resolution:** The browser checks its DNS cache. If not found, it asks the OS, which checks its hosts file and then asks the configured DNS resolver (typically the ISP or Google's 8.8.8.8). The DNS resolver recursively queries root nameservers, TLD nameservers, and authoritative nameservers to resolve the domain to an IP address.

2. **TCP Connection:** The browser establishes a TCP connection to the server's IP address on port 80 (HTTP) or 443 (HTTPS) using the three-way handshake.

3. **TLS Handshake (for HTTPS):** After TCP connection, the TLS handshake establishes an encrypted channel. This involves exchanging certificates, verifying the server's identity, and negotiating encryption algorithms and session keys.

4. **HTTP Request:** The browser sends an HTTP GET request for the URL resource, including headers (Accept, User-Agent, Cookie, etc.).

5. **Server Processing:** The server processes the request, querying databases, applying application logic, generating the response.

6. **HTTP Response:** The server sends back an HTTP response with status code, headers (Content-Type, Cache-Control, Set-Cookie, etc.), and the response body (HTML, JSON, etc.).

7. **Browser Rendering:** The browser parses the HTML, builds the DOM tree, fetches referenced resources (CSS, JavaScript, images), executes JavaScript, and renders the page.

---

## Data Structures: Questions and Answers

---

**Q30: What is a linked list? What are its advantages and disadvantages over arrays?**

**Answer:**
A linked list is a linear data structure where elements (nodes) are stored at non-contiguous memory locations. Each node contains data and a reference (pointer) to the next node.

**Advantages over arrays:**
- Dynamic size: grows and shrinks at runtime without reallocation.
- Efficient insertion/deletion at the beginning: O(1) (just update a pointer) versus O(n) for arrays (shift elements).
- No wasted space: each node is allocated as needed, unlike arrays where capacity may exceed current size.

**Disadvantages over arrays:**
- No random access: accessing the nth element requires traversing from the head, O(n) versus O(1) for arrays.
- Extra memory: each node stores a pointer in addition to data.
- Poor cache performance: nodes are scattered in memory, causing frequent cache misses; arrays benefit from spatial locality.
- No backward traversal in singly linked lists.

**Types:**
- Singly linked list: each node has one pointer (to next).
- Doubly linked list: each node has two pointers (to next and previous), allowing bidirectional traversal.
- Circular linked list: the last node points back to the head.

---

**Q31: What is a binary search tree? What are its properties?**

**Answer:**
A Binary Search Tree (BST) is a binary tree with the following property: for each node, all values in the left subtree are less than the node's value, and all values in the right subtree are greater.

**Operations and time complexities:**
- Search: O(log n) average, O(n) worst case (degenerate tree).
- Insert: O(log n) average, O(n) worst case.
- Delete: O(log n) average, O(n) worst case.
- Inorder traversal: O(n), produces sorted output.

**The worst case** occurs when elements are inserted in sorted order, creating a linear chain (the tree degenerates to a linked list).

**Balanced BSTs** (AVL trees, Red-Black trees) maintain balance after insertions and deletions, guaranteeing O(log n) performance. Java's TreeMap is implemented as a Red-Black tree.

**Common Follow-up:** "What is the difference between a complete binary tree and a full binary tree?"

**Strong Answer:** "A full binary tree has every node with either 0 or 2 children; no node has exactly 1 child. A complete binary tree has all levels fully filled except possibly the last level, which is filled from left to right. A perfect binary tree is both full and complete: all interior nodes have exactly 2 children and all leaves are at the same level. These distinctions matter for heap data structures: a heap is a complete binary tree, which allows it to be efficiently represented as an array (left child of node i is at 2i+1, right child at 2i+2)."

---

**Q32: What is a stack? What are its applications?**

**Answer:**
A stack is a linear data structure following the LIFO (Last In, First Out) principle. Elements are inserted and removed from the same end (called the top).

**Core operations:**
- Push: add an element to the top, O(1).
- Pop: remove and return the top element, O(1).
- Peek/Top: return the top element without removing it, O(1).
- isEmpty: check if the stack is empty, O(1).

**Applications:**

**Function call stack:** The runtime call stack uses a stack to manage function invocations. When a function is called, a stack frame containing local variables, parameters, and return address is pushed. When the function returns, the frame is popped. Stack overflow occurs when too many nested calls exhaust stack memory.

**Expression evaluation:** Converting infix expressions to postfix (Reverse Polish Notation) and evaluating postfix expressions use stacks.

**Balanced parentheses checking:** Push opening brackets onto the stack; when a closing bracket is encountered, verify it matches the top of the stack and pop.

**Undo functionality:** Applications maintain a stack of previous states; undo pops the most recent state.

**Browser back button:** A stack of visited URLs, with the current page on top.

**DFS (Depth-First Search):** Graph traversal uses a stack (explicit or the implicit function call stack for recursive implementations).

---

## Project-Based Technical Questions

The project discussion is the section of the technical interview where most freshers are either at their strongest or completely unprepared. There is no excuse for being unprepared: your own project is the one area where you have complete authority to speak from genuine experience.

**How Interviewers Probe the Project:**

The standard project question sequence is:

1. "Tell me about your project." (Open-ended; tests ability to explain coherently)
2. "What technology did you use for X, and why did you choose it over alternatives?" (Tests deliberateness of technology choices)
3. "How did you handle Y?" (Probes specific implementation details)
4. "What was the most challenging part? How did you solve it?" (Probes problem-solving approach)
5. "If you had to do this again, what would you do differently?" (Tests reflection and learning)

**Preparing Your Project Story:**

Write out a two-minute verbal explanation of your project that covers: what problem it solves, who the intended users are, what technology stack was used, what your specific contribution was, and what the outcome was. Practice this until it is fluent and natural.

For every technology in your project, be ready to answer: what it is, what specific feature of it you used, and why you chose it over at least one alternative. If you used MySQL, know why you chose MySQL over MongoDB (or vice versa). If you used REST APIs, know what REST is and what alternatives exist (GraphQL, SOAP).

**Sample Project Explanation:**

"My final year project is a web-based attendance management system for colleges. Students scan a QR code on their phone, and the system records their attendance in real time. We built it using Spring Boot for the backend, MySQL for the database, and React for the frontend. My specific contribution was designing the QR code generation and validation module. The QR code encodes the session ID and a timestamp and is valid for only 3 minutes to prevent sharing. I stored active sessions in memory using a HashMap with the session ID as the key and the expiry time as the value. This reduced database queries for validation by about 80% compared to our initial design that queried the database for every scan."

This explanation is specific, includes measurable details, identifies the candidate's specific ownership, and demonstrates genuine technical thought.

---

## Coding Questions Asked in Infosys Technical Rounds

Some Infosys technical interview variants, particularly for [DSE and PP](https://insightcrunch.com/2021/10/25/infosys-power-programmer-dse/) tracks, include a live coding component. The following are representative problems at the appropriate difficulty level.

---

**Coding Q1: Write a program to reverse a string without using built-in reverse functions.**

```java
public String reverseString(String s) {
    char[] chars = s.toCharArray();
    int left = 0, right = chars.length - 1;
    while (left < right) {
        char temp = chars[left];
        chars[left] = chars[right];
        chars[right] = temp;
        left++;
        right--;
    }
    return new String(chars);
}
```

**Explanation:** Two-pointer approach. Start with pointers at both ends, swap characters, and move both pointers toward the center. Time: O(n), Space: O(n) for the char array.

**Edge cases to mention:** Empty string, single character, string with spaces, palindrome input (should return the same string).

---

**Coding Q2: Check if a string is a palindrome.**

```java
public boolean isPalindrome(String s) {
    int left = 0, right = s.length() - 1;
    while (left < right) {
        if (s.charAt(left) != s.charAt(right)) {
            return false;
        }
        left++;
        right--;
    }
    return true;
}
```

**Edge cases:** Empty string (return true), single character (return true), case sensitivity (should the comparison be case-insensitive? Ask the interviewer).

---

**Coding Q3: Find the factorial of a number using both iterative and recursive approaches.**

```java
// Iterative
public long factorialIterative(int n) {
    if (n < 0) throw new IllegalArgumentException("Factorial undefined for negative numbers");
    long result = 1;
    for (int i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

// Recursive
public long factorialRecursive(int n) {
    if (n < 0) throw new IllegalArgumentException("Factorial undefined for negative numbers");
    if (n == 0 || n == 1) return 1;
    return n * factorialRecursive(n - 1);
}
```

**When to use recursive:** When the recursive structure matches the problem naturally and the call stack depth is manageable. Factorial is a classic recursion problem but the iterative version is preferred in production because deep recursion for large n causes stack overflow.

---

**Coding Q4: Write a program to find all duplicates in an array.**

```java
public List<Integer> findDuplicates(int[] nums) {
    List<Integer> duplicates = new ArrayList<>();
    Map<Integer, Integer> frequency = new HashMap<>();
    
    for (int num : nums) {
        frequency.put(num, frequency.getOrDefault(num, 0) + 1);
    }
    
    for (Map.Entry<Integer, Integer> entry : frequency.entrySet()) {
        if (entry.getValue() > 1) {
            duplicates.add(entry.getKey());
        }
    }
    return duplicates;
}
```

**Time:** O(n), **Space:** O(n). Discuss alternatives: sorting + linear scan is O(n log n) time and O(1) extra space. The hash map approach is better for time; the sorting approach is better for space.

---

**Coding Q5: Implement a stack using an array.**

```java
class Stack {
    private int[] data;
    private int top;
    private int capacity;
    
    public Stack(int capacity) {
        this.capacity = capacity;
        data = new int[capacity];
        top = -1;
    }
    
    public void push(int val) {
        if (top == capacity - 1) throw new RuntimeException("Stack overflow");
        data[++top] = val;
    }
    
    public int pop() {
        if (isEmpty()) throw new RuntimeException("Stack underflow");
        return data[top--];
    }
    
    public int peek() {
        if (isEmpty()) throw new RuntimeException("Stack is empty");
        return data[top];
    }
    
    public boolean isEmpty() { return top == -1; }
    public int size() { return top + 1; }
}
```

**What the interviewer is evaluating:** Correct implementation of all operations, proper boundary condition handling (overflow and underflow), clean code structure.

---

## How to Handle Questions You Do Not Know

A significant portion of the technical interview evaluation is about how candidates handle uncertainty. This is not a peripheral skill: it directly represents professional maturity.

**The Wrong Responses:**

Pretending to know: Making up an answer or confidently stating something incorrect. This is the worst possible response. An experienced interviewer identifies incorrect answers immediately, and the loss of credibility from being caught making things up is severe and irreversible.

Complete silence: Saying nothing and waiting for the interviewer to move on. This signals low confidence and poor communication.

**The Right Response:**

Acknowledge the limit honestly, engage intellectually with what you do know, and reason toward what the answer might be.

Example: "I am not fully certain about the specific implementation of Tarjan's algorithm for finding SCCs. But I know that finding strongly connected components involves exploring the graph using DFS and identifying nodes that can reach each other. Based on what I know about DFS and stack usage, my intuition is that the algorithm probably uses a stack to track which nodes are in the current DFS path. Is that in the right direction?"

This response shows:
- Honesty about the knowledge gap.
- Genuine engagement with the question rather than withdrawal.
- Application of what is known to reason about what is not known.
- An invitation for the interviewer to confirm, correct, or extend.

Interviewers respond positively to this kind of intellectual honesty and engagement. It is a demonstration of how you would actually behave on a project when encountering an unfamiliar technical problem.

---

## The Technical Interview: Format and Flow

Understanding the typical structure of the Infosys technical interview helps in both preparation and performance.

**Duration:** 30 to 45 minutes for the standard SE technical interview. DSE and PP track interviews may run 45 to 60 minutes.

**Typical Flow:**

Opening (5 minutes): The interviewer introduces themselves, asks the candidate to introduce themselves briefly, and sets the context for the session. The candidate's self-introduction should be a concise professional summary: name, college, degree, brief mention of technical interests and the project.

Project Discussion (10-15 minutes): The interviewer asks about the final year project. This is where many interviews are effectively won or lost. Thorough project preparation is non-negotiable.

Core Technical Questions (15-20 minutes): The interviewer selects topics based on the candidate's responses and stated knowledge. Common sequences include: OOP followed by Java specifics, or DBMS followed by SQL. The interviewer typically goes deeper on topics where the candidate shows confidence.

Coding Problem (5-10 minutes, if included): A basic to medium coding problem, usually on paper or a whiteboard. The emphasis is on problem-solving approach and code correctness.

Closing (2-3 minutes): The interviewer asks if the candidate has questions. Always have one thoughtful question prepared.

**What to Do During the Interview:**

Think out loud. Do not code or answer in silence. Verbalize the reasoning process.

Ask clarifying questions before answering complex questions. "Just to make sure I understand: when you ask about polymorphism, are you interested in the conceptual definition, or would you like me to demonstrate with a code example?"

Connect answers to real examples from your project wherever possible. Abstract knowledge paired with concrete application is more impressive than definitions alone.

---

## Frequently Asked Questions

**1. What topics are most important for the Infosys technical interview?**

OOP concepts (the four pillars, plus overloading vs overriding, abstract class vs interface, static keyword) and DBMS/SQL (normalization, ACID properties, joins, and writing queries) are the most consistently tested. Java fundamentals (collections, exception handling, String vs StringBuilder) appear frequently for candidates who list Java as a primary language. OS (process vs thread, deadlock) and networking (OSI model, TCP vs UDP) appear with moderate frequency.

**2. Do I need to write code in the Infosys technical interview?**

For the standard SE track, some interviews include a basic coding problem on paper; others do not. For DSE and PP tracks, coding is more consistently required. Always be prepared to write basic code demonstrating string manipulation, array operations, and simple recursive solutions. The code written on paper does not need to compile, but it should be logically correct and follow reasonable syntax.

**3. How in-depth should I know each topic?**

The depth should be sufficient to handle follow-up questions to an initial answer. If you say you know inheritance, you should be able to explain the difference between IS-A and HAS-A relationships, discuss the limitations of multiple inheritance in Java, and give a concrete example from your project or a hypothetical scenario. One level deeper than the definition, with a concrete example, is the practical target.

**4. Is it okay to say "I don't know" in the Infosys technical interview?**

Yes, combined with genuine engagement with what you do know. A bare "I don't know" with no follow-through is weak. "I don't know the exact answer, but based on X and Y, my reasoning suggests Z" is strong. Intellectual honesty paired with intellectual engagement is valued.

**5. How long should the project explanation be?**

The initial project explanation (in response to "tell me about your project") should be two to three minutes. It should be comprehensive enough to give the interviewer a clear picture without being so long that you have already answered all the follow-up questions before they are asked. The goal is to create an accurate context and then engage in a dialogue.

**6. Should I prepare for questions about technologies not in my project?**

Yes. The interviewer may ask about technologies listed on your resume or commonly associated with your programming language even if they were not in your specific project. If you list Java on your resume, expect Java-specific questions regardless of what your project used. Only list technologies you can discuss with genuine depth.

**7. What is the most common mistake freshers make in the Infosys technical interview?**

Claiming knowledge of something and then being unable to handle the follow-up. The most damaging interview moments are not admissions of ignorance but demonstrated overconfidence: asserting you know a topic and then revealing through follow-up responses that you do not. Accurate self-assessment of what you genuinely know, and clear boundaries around what you are less certain about, consistently produces better interview outcomes than overclaiming.

**8. How should I prepare for the coding component?**

Practice writing code by hand (or in a basic text editor without IDE features). Code written during interviews is evaluated for logic and correctness, not compilation. Practice the most common patterns: string reversal and manipulation, array searching and sorting, basic recursive problems (factorial, Fibonacci, tower of Hanoi), stack and queue implementations, and linked list traversal. For DSE and PP tracks, add medium-difficulty algorithmic problems involving trees and dynamic programming.

**9. Can I ask the interviewer for clarification during the technical interview?**

Not only can you, but you should. Asking a clarifying question before answering a technical question demonstrates professional maturity. It ensures you answer the question actually being asked. Interviewers consistently prefer candidates who ask one clarifying question and then answer precisely over those who assume, answer, and then discover they misunderstood the question.

**10. What should I wear to the Infosys technical interview?**

Formal attire: formal trousers, formal shirt, and formal shoes for men; formal western or formal Indian attire for women. The technical interview is part of a professional evaluation process, and appearance contributes to the overall impression even before the first technical question is asked.

---

## Quick-Reference: Most Commonly Asked Infosys Technical Interview Questions

The following condensed list represents the questions that appear most consistently across Infosys technical interviews for freshers, organized by topic. Use this as a final review checklist before your interview.

**OOP Checklist:**
- [ ] Define the four pillars of OOP with real examples
- [ ] Difference between overloading and overriding
- [ ] Abstract class vs interface - when to use each
- [ ] What is encapsulation - how is it different from abstraction
- [ ] What is multiple inheritance - why Java doesn't support it through classes
- [ ] Constructor - how it differs from a method
- [ ] Static keyword - what it means for variables, methods, and blocks
- [ ] IS-A vs HAS-A relationships

**Java Checklist:**
- [ ] ArrayList vs LinkedList - internal working and when to use each
- [ ] HashMap internal working - hash code, buckets, equals() contract
- [ ] Checked vs unchecked exceptions - examples of each
- [ ] String vs StringBuilder vs StringBuffer
- [ ] final keyword - variables, methods, classes
- [ ] Stack vs heap memory
- [ ] Collections framework - key interfaces and their implementations
- [ ] == vs .equals()

**DBMS Checklist:**
- [ ] 1NF, 2NF, 3NF - definitions and violation examples
- [ ] ACID properties - all four with examples
- [ ] Types of joins - INNER, LEFT, RIGHT, FULL, SELF with examples
- [ ] Clustered vs non-clustered index
- [ ] Primary key vs foreign key vs unique key
- [ ] Difference between WHERE and HAVING
- [ ] Difference between DELETE, TRUNCATE, and DROP
- [ ] What is a view - benefits and limitations

**SQL Queries to Practice:**
- [ ] Second highest salary
- [ ] Employees earning more than department average
- [ ] Department with maximum employees (including departments with zero)
- [ ] Self-join: employees and their managers
- [ ] Find duplicates in a table
- [ ] Running total (cumulative sum)

**OS Checklist:**
- [ ] Process vs program vs thread
- [ ] Deadlock - definition and four conditions
- [ ] Paging vs segmentation
- [ ] CPU scheduling algorithms - FCFS, SJF, Round Robin
- [ ] Semaphore vs mutex
- [ ] Virtual memory - concept and benefits

**Networking Checklist:**
- [ ] OSI model - all 7 layers with functions
- [ ] TCP vs UDP - when to use each
- [ ] What happens when you type a URL
- [ ] HTTP vs HTTPS
- [ ] What is DNS and how it works
- [ ] IP address - IPv4 vs IPv6 basics

**Data Structures Checklist:**
- [ ] Array vs linked list - when to use each
- [ ] Stack and queue - implementations and applications
- [ ] Binary search tree - properties and operations
- [ ] BFS vs DFS - when to use each
- [ ] Hash table - collision handling strategies

Preparing a concrete answer to every item on this checklist, with at least one real example or code snippet for each, constitutes thorough Infosys technical interview preparation.

---

## What Separates a Strong Technical Interview From a Weak One

The difference between a candidate who gets through the Infosys technical interview and one who does not is rarely a matter of knowing more topics. It is almost always a matter of how deeply they know the topics they claim to know, and how they communicate that knowledge.

The strongest technical interview performances have three qualities in common: specificity (concrete examples, actual code, real numbers rather than vague generalities), intellectual honesty (clear acknowledgment of what is known and what is not), and engagement (asking clarifying questions, thinking out loud, inviting dialogue rather than delivering a monologue).

The weakest performances have a different pattern: memorized definitions recited without context, inability to handle any follow-up question that deviates from the memorized script, and silence when a question falls outside the prepared material.

Preparing by genuinely understanding each concept (well enough to explain it to someone who does not know it) rather than by memorizing definitions (well enough to recite the textbook entry) is the practical preparation approach that produces the strongest interview performance. Use this guide as a framework for that genuine understanding, not as a memorization list.
