---
layout: post
title: "TCS ILP Java: Complete Training Roadmap"
page_title: "TCS ILP Java Stream - Curriculum, Assessment Guide, Project Phase, and Week-by-Week Preparation Plan"
date: 2023-11-21
categories: ["Industry"]
tags: ["TCS ILP Java", "TCS Java training", "TCS ILP syllabus", "TCS ILP assessment", "TCS Aspire Java"]
excerpt: "Master the TCS ILP Java stream. Curriculum breakdown, IRA assessment prep, project phase guide, and a complete week-by-week study plan."
image: "/assets/images/blog/blog-03.webp"
reading_time: 60
author: "Insight Crunch Team"
last_updated: 2026-03-23
---
Java is the most commonly assigned TCS ILP stream because TCS's project portfolio is dominated by Java-based enterprise applications. Banking systems, insurance platforms, retail order management, healthcare records, logistics trackers - the overwhelming majority of the applications TCS builds and maintains for its clients run on Java. When you are allocated to the Java stream, TCS is investing in converting you from a college-educated programmer into a productive contributor to these systems. This guide maps that journey in full: the complete curriculum, the weekly pacing, the assessment structure, the project phase, and the specific preparation strategies that help you perform well at each stage - starting from before ILP begins to the moment you walk into your first real project.

![TCS Guide](/assets/images/blog/blog-03.webp)

## Why Java Dominates TCS's ILP Stream Allocation

Understanding why Java is the most common stream makes you a better Java ILP candidate. You are not just learning a language - you are learning the language of TCS's core business.

**Enterprise Java dominance:** The Java Enterprise Edition (now Jakarta EE) ecosystem was designed specifically for building large-scale business applications. The architectural patterns it establishes - layered architecture, separation of concerns, declarative configuration, dependency injection - are the patterns that every TCS enterprise project uses regardless of whether it uses Spring, Jakarta EE, or another Java framework.

**Client portfolio composition:** TCS's largest clients are in BFSI (Banking, Financial Services, Insurance), retail, and manufacturing. These sectors standardised on Java in the early 2000s and built enormous codebases in it. Migrating to a different language would require rewriting millions of lines of tested, running code - which clients will not do. TCS needs large numbers of Java-competent engineers to serve these clients.

**Spring Framework ubiquity:** Spring Boot and Spring MVC are the de facto standard for Java web application development in TCS client environments. The ILP Java curriculum culminates in Spring Framework - teaching it ensures that every Java-stream ILP graduate can contribute to the most common type of TCS project.

**Long project lifespans:** Enterprise Java applications are built to last decades. Unlike mobile apps that get rewritten every few years, a bank's core transaction processing system written in Java may run for 20 years with ongoing enhancement. This creates permanent demand for Java developers who understand both the language and the legacy codebase conventions.

---

## Pre-ILP: Java Aspire and What to Study

### The Aspire Portal: Your First Preparation Layer

TCS's Aspire pre-ILP program gives you access to foundational content from the day your offer is accepted. For the Java stream, Aspire covers:

- Programming fundamentals (data types, variables, control flow)
- Basic OOP concepts (class, object, methods)
- Introduction to Java syntax
- Basic SQL (SELECT, INSERT, UPDATE, DELETE)

**How to use Aspire for Java preparation:**

Do not simply read the content - type the code examples into an IDE and run them. Seeing code execute on your own machine converts abstract syntax into tangible understanding. A trainee who runs 50 Java programs during Aspire arrives at ILP Day 1 with the hand-memory of Java syntax already building. A trainee who only read the Aspire content arrives needing to learn syntax and concepts simultaneously.

**Setting up your Java development environment before ILP:**

Install the following before your first day:
- **JDK (Java Development Kit):** Download from Oracle's official site. ILP typically uses JDK 11 or 17 (LTS versions). If unsure, install JDK 17.
- **Eclipse IDE:** TCS ILP primarily uses Eclipse. Download Eclipse IDE for Java Developers from eclipse.org. Practice creating projects, packages, and classes in Eclipse before ILP. The keyboard shortcuts (Ctrl+Space for autocomplete, Ctrl+Shift+O for organise imports, Ctrl+/ for comment) save significant time.
- **MySQL:** For database work in ILP. MySQL Community Server (free) is the standard.
- **MySQL Workbench:** GUI tool for writing and executing SQL queries.

Having this environment configured and tested before ILP Day 1 means you can focus on learning content from the start rather than spending your first two days on tooling setup.

### What to Study on Aspire: Java-Specific Priority

**Priority 1 (must complete before ILP):**
- Java basic syntax (main method structure, print statements, variable declarations)
- Data types (primitive: int, double, char, boolean; wrapper: Integer, Double, Character, Boolean)
- Control flow (if-else, switch, for loop, while loop, do-while)
- Methods (defining methods, parameters, return types, method overloading)

**Priority 2 (complete before ILP if possible):**
- OOP introduction (class, object, constructor)
- Arrays (single-dimensional array creation, traversal, modification)
- Basic String methods (length, charAt, substring, equals, toUpperCase, split)

**Priority 3 (exposure level, deep learning happens in ILP):**
- Inheritance concept (extends keyword)
- Interface concept
- Exception basics (try-catch)

For additional practice beyond Aspire with assessment-style questions, the [TCS ILP Preparation Guide](https://reportmedic.org/tools/tcs-ilp-preparation-guide.html) provides interactive exercises across Core Java, Advanced Java, SQL, and web technologies matched to the actual IRA assessment format.

---

## The Java ILP Curriculum: Complete Week-by-Week Breakdown

The Java ILP runs approximately 10-12 weeks. The following curriculum is representative - actual pacing varies by batch and facilitator. Use this as a guide for self-pacing your preparation and study.

### Week 1: Java Foundations

**Content covered:**
- Java history, JDK/JRE/JVM architecture and their relationships
- Writing, compiling, and running a Java program from the command line
- Data types: primitive types (byte, short, int, long, float, double, char, boolean) and their ranges
- Variables and constants (final keyword)
- Type casting (implicit widening, explicit narrowing)
- Operators: arithmetic, relational, logical, bitwise, assignment, ternary
- Control flow: if, else-if, else, switch-case, for, while, do-while, break, continue

**The JVM architecture question (always appears in IRA MCQ):**

The JVM (Java Virtual Machine) executes Java bytecode. The compilation chain is:

```
Source code (.java) → Java Compiler (javac) → Bytecode (.class) → JVM → Machine code
```

This is what makes Java "write once, run anywhere" - the .class bytecode is platform-independent. The JVM is platform-specific (Windows JVM, Linux JVM, macOS JVM) but translates the same bytecode to native machine instructions on each platform.

**Week 1 practice problems:**
- Write a program that reads two integers from command line arguments and prints their sum, difference, product, and quotient
- Write a program that determines if a number is positive, negative, or zero
- Write a program that prints the multiplication table for a given number
- Write a program that calculates compound interest using the formula A = P(1 + r/n)^(nt) using Math.pow()

### Week 2: Object-Oriented Programming - Classes, Objects, and Constructors

**Content covered:**
- Class definition: fields (instance variables), methods, constructors
- Object creation with `new` keyword
- `this` keyword (referring to current object, chaining constructors)
- Access modifiers: `public`, `private`, `protected`, default (package-private)
- Getters and setters (encapsulation)
- Static fields and static methods (class-level vs instance-level)
- The `final` keyword on classes, methods, and fields
- `toString()` method and why overriding it matters

**Encapsulation - the concept and the code:**

Encapsulation means hiding the internal state of an object and requiring all interaction to happen through well-defined methods (getters and setters). This is one of the four pillars of OOP and is directly testable in IRA.

```java
public class BankAccount {
    private double balance;  // private = encapsulated, not directly accessible
    private String accountHolder;

    public BankAccount(String holder, double initialBalance) {
        this.accountHolder = holder;
        this.balance = initialBalance;
    }

    public double getBalance() {  // getter provides controlled read access
        return balance;
    }

    public boolean deposit(double amount) {  // controlled write with validation
        if (amount <= 0) return false;
        balance += amount;
        return true;
    }

    public boolean withdraw(double amount) {  // business rule enforced through method
        if (amount <= 0 || amount > balance) return false;
        balance -= amount;
        return true;
    }

    @Override
    public String toString() {
        return accountHolder + ": Rs. " + balance;
    }
}
```

**Week 2 practice problems:**
- Create a `Student` class with name, rollNumber, and marks. Add methods for gradeComputation, toString.
- Create a `Rectangle` class. Calculate area and perimeter. Make fields private and add getters/setters.
- Demonstrate method overloading with an `add()` method that handles int, double, and String.

### Week 3: Inheritance, Polymorphism, and Abstraction

**Content covered:**
- Inheritance with `extends`: single inheritance in Java (no multiple class inheritance)
- Method overriding vs method overloading
- `super` keyword (calling parent class constructor and methods)
- `instanceof` operator
- Abstract classes and abstract methods
- Interfaces: `interface` keyword, `implements`, multiple interface implementation
- Default methods in interfaces (Java 8+)
- Polymorphism: compile-time (overloading) and runtime (overriding)

**The four pillars of OOP for IRA:**

IRA MCQ questions routinely ask "which OOP principle does this code demonstrate?" Memorise:
- **Encapsulation:** Hiding data, exposing through methods (private fields + public getters/setters)
- **Inheritance:** A subclass extends a superclass, inheriting its attributes and methods (`extends`)
- **Polymorphism:** One interface, multiple implementations (method overriding enables runtime polymorphism)
- **Abstraction:** Hiding implementation details, exposing only what the user needs (abstract classes and interfaces)

**Abstract class vs Interface (a near-certain IRA topic):**

| Feature | Abstract Class | Interface |
|---|---|---|
| Instantiation | Cannot be instantiated | Cannot be instantiated |
| Methods | Can have abstract AND concrete methods | Methods are abstract by default (Java 7-); can have default/static methods (Java 8+) |
| Fields | Can have instance fields | Only static final constants |
| Constructor | Can have constructors | Cannot have constructors |
| Inheritance | Single inheritance (extends) | Multiple implementation (implements) |
| When to use | When classes share code AND relationship | When unrelated classes should share behaviour |

**Week 3 practice problems:**
- Create a `Shape` abstract class with an abstract `area()` method. Create `Circle`, `Rectangle`, and `Triangle` subclasses.
- Create a `Printable` interface and a `Serialisable` interface. Create a `Document` class implementing both.
- Demonstrate runtime polymorphism: a `Shape` reference pointing to a `Circle` object, calling `area()`.

### Week 4: Exception Handling and Java Collections Framework

**Content covered:**

**Exception Handling:**
- Exception hierarchy: `Throwable` → `Error` and `Exception` → `RuntimeException` (unchecked) and checked exceptions
- `try`, `catch`, `finally`, `throw`, `throws`
- Multi-catch (catching multiple exceptions in one block)
- `try-with-resources` for AutoCloseable objects
- Custom exceptions (extending Exception or RuntimeException)
- Checked vs unchecked exceptions - when to use each

**The exception hierarchy for IRA:**

```
Throwable
├── Error (JVM-level, should not be caught: OutOfMemoryError, StackOverflowError)
└── Exception
    ├── Checked (must be handled or declared: IOException, SQLException, ClassNotFoundException)
    └── RuntimeException/Unchecked (need not be declared: NullPointerException, ArrayIndexOutOfBoundsException,
        ClassCastException, IllegalArgumentException, NumberFormatException, ArithmeticException)
```

**Collections Framework:**
- `List` interface: `ArrayList` (dynamic array), `LinkedList` (doubly linked)
- `Set` interface: `HashSet` (unordered unique), `TreeSet` (sorted unique), `LinkedHashSet` (insertion-order unique)
- `Map` interface: `HashMap` (unordered key-value), `TreeMap` (sorted keys), `LinkedHashMap` (insertion-order keys)
- `Queue` interface: `PriorityQueue`, `ArrayDeque`
- Iterator and enhanced for-loop
- `Collections` utility class: sort, reverse, shuffle, frequency, min, max

**Collections performance for IRA MCQ:**

| Structure | Get | Add (end) | Remove (middle) | Contains |
|---|---|---|---|---|
| ArrayList | O(1) | O(1) amortised | O(n) | O(n) |
| LinkedList | O(n) | O(1) | O(1) after finding | O(n) |
| HashSet | - | O(1) average | O(1) average | O(1) average |
| TreeSet | - | O(log n) | O(log n) | O(log n) |
| HashMap | O(1) average | O(1) average | O(1) average | O(1) average |
| TreeMap | O(log n) | O(log n) | O(log n) | O(log n) |

**Week 4 practice problems:**
- Write a program that reads words from a file and uses a `HashMap` to count frequency of each word.
- Implement a simple phone book using `TreeMap<String, String>` (name → phone number, sorted by name).
- Write a custom checked exception `InsufficientFundsException` and use it in the `BankAccount.withdraw()` method.
- Demonstrate the difference between `ArrayList` and `LinkedList` by timing insertion at index 0 for 10,000 elements.

### Week 5: Generics, Multithreading, and Java I/O

**Content covered:**

**Generics:**
- Generic classes: `class Box<T> { private T value; ... }`
- Generic methods: `public <T> void print(T t) { ... }`
- Bounded type parameters: `<T extends Comparable<T>>`
- Wildcards: `?`, `? extends T`, `? super T`
- Why generics: type safety at compile time, eliminates casting

**Multithreading:**
- Creating threads: extending `Thread` class vs implementing `Runnable` interface (prefer Runnable)
- Thread lifecycle: NEW → RUNNABLE → BLOCKED/WAITING/TIMED_WAITING → TERMINATED
- `start()` vs `run()` - the critical distinction: `start()` creates a new thread; calling `run()` directly executes in the current thread
- `sleep()`, `join()`, `wait()`, `notify()`, `notifyAll()`
- Synchronisation: `synchronized` keyword (method-level and block-level)
- Deadlock: what it is, conditions for it, how to avoid it
- `volatile` keyword: ensures visibility of changes across threads

**The most common IRA multithreading MCQ:**

"What happens when you call `thread.run()` instead of `thread.start()`?"

Answer: `run()` executes the thread's logic in the current (calling) thread, not in a new thread. No new thread is created. `start()` creates a new thread and then calls `run()` in that new thread.

**Java I/O:**
- Byte streams: `InputStream`, `OutputStream` (low-level, binary data)
- Character streams: `Reader`, `Writer` (character data, handles encoding)
- Buffered wrappers: `BufferedReader`, `BufferedWriter`, `BufferedInputStream`, `BufferedOutputStream`
- File reading pattern with try-with-resources:

```java
try (BufferedReader br = new BufferedReader(new FileReader("file.txt"))) {
    String line;
    while ((line = br.readLine()) != null) {
        System.out.println(line);
    }
} catch (IOException e) {
    System.err.println("Error: " + e.getMessage());
}
```

- `Scanner` for parsing input
- `java.nio.file.Files` utility class (newer API, cleaner for most use cases)

**Week 5 practice problems:**
- Write a generic `Stack<T>` class with push, pop, peek, and isEmpty operations.
- Create two threads that increment a shared counter. Demonstrate the race condition, then fix it with synchronisation.
- Write a program that reads a text file and writes a processed version (e.g., all uppercase) to a new file.

### Week 6: Java 8 Features and Functional Programming

**Content covered:**
- Lambda expressions: `(params) -> expression` and `(params) -> { statements; }`
- Functional interfaces: `Predicate<T>`, `Function<T,R>`, `Consumer<T>`, `Supplier<T>`, `BiFunction<T,U,R>`
- Method references: `ClassName::methodName`, `instance::methodName`, `ClassName::new`
- Stream API: `filter()`, `map()`, `reduce()`, `collect()`, `forEach()`, `sorted()`, `distinct()`, `limit()`, `count()`, `anyMatch()`, `allMatch()`, `findFirst()`
- `Optional<T>`: avoiding NullPointerException, `isPresent()`, `orElse()`, `map()`, `ifPresent()`
- Default and static methods in interfaces

**Lambda and Stream examples for IRA:**

```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5, 6, 7, 8, 9, 10);

// Filter even numbers and collect to list
List<Integer> evens = numbers.stream()
    .filter(n -> n % 2 == 0)
    .collect(Collectors.toList());

// Sum of squares of odd numbers
int sumOfOddSquares = numbers.stream()
    .filter(n -> n % 2 != 0)
    .mapToInt(n -> n * n)
    .sum();

// Find first number greater than 7
Optional<Integer> first = numbers.stream()
    .filter(n -> n > 7)
    .findFirst();
first.ifPresent(System.out::println);  // method reference
```

**IRA Stream questions pattern:** Given a stream chain, determine the output. These test whether you understand which terminal operation is used (collect, sum, count, findFirst) and what the intermediate operations produce.

**Week 6 practice problems:**
- Given a list of Student objects, use streams to: find students scoring above 75, calculate average marks, and find the top-scoring student's name.
- Rewrite any three traditional for-loop algorithms you have written earlier using Stream API.
- Practice converting between lambda and method reference styles for common operations.

### Week 7: JDBC and Database Integration

**Content covered:**
- JDBC architecture: DriverManager, Connection, Statement, PreparedStatement, ResultSet, CallableStatement
- Database connection establishment and connection string format
- CRUD operations through JDBC
- PreparedStatement vs Statement (security and performance advantages)
- Transaction management: `setAutoCommit(false)`, `commit()`, `rollback()`
- ResultSet navigation and data extraction
- Connection pooling concepts (why raw DriverManager is not used in production)

**The JDBC pattern every ILP Java trainee must memorise:**

```java
// The six steps of JDBC
// Step 1: Load driver (modern JDBC auto-loads, but older code has this)
// Class.forName("com.mysql.cj.jdbc.Driver");

// Step 2: Establish connection
String url = "jdbc:mysql://localhost:3306/dbname";
Connection conn = DriverManager.getConnection(url, "username", "password");

// Step 3: Create statement (use PreparedStatement for user input)
String query = "SELECT * FROM employees WHERE dept_id = ?";
PreparedStatement ps = conn.prepareStatement(query);
ps.setInt(1, departmentId);  // parameterised to prevent SQL injection

// Step 4: Execute query
ResultSet rs = ps.executeQuery();

// Step 5: Process results
while (rs.next()) {
    int id = rs.getInt("employee_id");
    String name = rs.getString("name");
    double salary = rs.getDouble("salary");
    System.out.println(id + ": " + name + " - " + salary);
}

// Step 6: Close resources (use try-with-resources in modern code)
rs.close();
ps.close();
conn.close();
```

**SQL covered alongside JDBC:**
The JDBC module includes a comprehensive SQL component. Topics tested in IRA:
- DDL: CREATE TABLE, ALTER TABLE, DROP TABLE, constraints (PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL, CHECK)
- DML: INSERT, UPDATE, DELETE, SELECT with WHERE, ORDER BY, GROUP BY, HAVING
- Joins: INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN, SELF JOIN
- Subqueries: correlated and non-correlated, in WHERE and in SELECT
- Aggregate functions: COUNT, SUM, AVG, MAX, MIN
- Views, indexes, stored procedures (concepts)

**The SQL question that appears in almost every IRA:**

"Find the second-highest salary from the employees table."

```sql
-- Method 1: Using subquery
SELECT MAX(salary) FROM employees WHERE salary < (SELECT MAX(salary) FROM employees);

-- Method 2: Using LIMIT/OFFSET (MySQL)
SELECT DISTINCT salary FROM employees ORDER BY salary DESC LIMIT 1 OFFSET 1;

-- Method 3: Using window functions
SELECT salary FROM (
    SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS rank_num
    FROM employees
) ranked WHERE rank_num = 2;
```

Know all three methods. IRA may show one and ask which is correct, or show two and ask which is more efficient.

### Week 8: Servlets and Web Application Architecture

**Content covered:**
- HTTP protocol fundamentals: request methods (GET, POST, PUT, DELETE), response codes (200, 201, 301, 302, 400, 401, 403, 404, 500), headers, body
- Web application architecture: client (browser), web server, application server, database
- Servlet lifecycle: `init()`, `service()` (dispatches to doGet/doPost), `destroy()`
- `HttpServlet` class, `HttpServletRequest`, `HttpServletResponse`
- Getting request parameters: `request.getParameter("fieldName")`
- Session management: URL rewriting, cookies, HttpSession
- RequestDispatcher: `forward()` vs `redirect()` distinction
- Servlet configuration in web.xml (traditional) and @WebServlet annotation (modern)

**Servlet lifecycle for IRA:**

The servlet lifecycle question appears in most IRA2 exams:

1. **Loading and instantiation:** The container (Tomcat, etc.) loads the servlet class and creates one instance.
2. **Initialisation:** `init()` is called once. Used for one-time setup.
3. **Request handling:** `service()` is called for each request. Dispatches to `doGet()` or `doPost()` based on HTTP method.
4. **Destruction:** `destroy()` is called once when the servlet is taken out of service. Used for cleanup.

Key point: Only one servlet instance exists; multiple threads may call `service()` concurrently. Servlets must be thread-safe.

**forward() vs redirect():**

`forward()`: Server-side. The request is forwarded to another resource (another servlet or JSP) on the server. The client's URL does not change.

`redirect()`: Client-side. The server sends a 302 response telling the client to make a new request to a different URL. The client's URL changes to the new URL.

### Week 9: JSP and Spring Framework Introduction

**Content covered:**

**JSP (JavaServer Pages):**
- JSP elements: scriptlets (`<% code %>`), expressions (`<%= expression %>`), declarations (`<%! declaration %>`), directives (`<%@ %>`), actions (`<jsp:...>`)
- JSP implicit objects: request, response, session, application, out, page, config, pageContext, exception
- JSTL (JSP Standard Tag Library): `<c:if>`, `<c:forEach>`, `<c:out>`, `<c:set>`
- EL (Expression Language): `${variable}`, `${object.property}`, `${list[index]}`
- MVC pattern with Servlets (Controller) and JSP (View)

**Spring Framework:**
- Why Spring: the problems it solves (boilerplate configuration, manual dependency management)
- IoC (Inversion of Control) and DI (Dependency Injection) concepts
- Spring Bean lifecycle
- Spring annotations: `@Component`, `@Service`, `@Repository`, `@Controller`, `@Autowired`, `@Bean`
- Spring Boot: auto-configuration, embedded server (Tomcat), application.properties
- Spring MVC: `@RestController`, `@GetMapping`, `@PostMapping`, `@RequestParam`, `@PathVariable`, `@RequestBody`, `@ResponseBody`

**Dependency Injection - the concept that IRA tests most in Spring:**

Without DI:
```java
public class OrderService {
    private PaymentService paymentService = new PaymentService(); // tight coupling
}
```

With DI (Spring manages the dependency):
```java
@Service
public class OrderService {
    @Autowired
    private PaymentService paymentService; // Spring injects - loose coupling
}
```

Why this matters: You can swap out `PaymentService` for a mock in tests without changing `OrderService`. The objects depend on abstractions, not concrete implementations.

**Spring Boot REST API example:**
```java
@RestController
@RequestMapping("/api/students")
public class StudentController {

    @Autowired
    private StudentService studentService;

    @GetMapping
    public List<Student> getAllStudents() {
        return studentService.findAll();
    }

    @GetMapping("/{id}")
    public Student getStudentById(@PathVariable Long id) {
        return studentService.findById(id);
    }

    @PostMapping
    public Student createStudent(@RequestBody Student student) {
        return studentService.save(student);
    }
}
```

### Week 10: Web Technologies - HTML, CSS, JavaScript

**Content covered:**

**HTML:**
- Document structure: DOCTYPE, html, head, body
- Semantic elements: header, nav, main, section, article, aside, footer
- Forms: input types (text, password, email, number, submit, radio, checkbox, select), form attributes (action, method)
- Tables: thead, tbody, tr, th, td
- Links, images, lists (ul, ol, li)

**CSS:**
- Selectors: element, class (.), id (#), descendant, pseudo-classes (:hover, :nth-child)
- Box model: content, padding, border, margin
- Display: block, inline, inline-block, flex, grid (basics)
- Positioning: static, relative, absolute, fixed
- Flexbox: flex-direction, justify-content, align-items, flex-wrap

**JavaScript:**
- Variables: `var`, `let`, `const` and their scoping differences
- Data types: string, number, boolean, undefined, null, object, array
- Functions: function declarations, function expressions, arrow functions
- DOM manipulation: `document.getElementById()`, `querySelector()`, `innerHTML`, `textContent`, `style`, `classList`
- Event handling: `addEventListener()`, event object, `preventDefault()`
- Fetch API for making HTTP requests to backend
- JSON: `JSON.parse()`, `JSON.stringify()`
- Promises and async/await basics

**JavaScript for IRA:** Web technologies questions in IRA2 focus on: variable scoping (var vs let vs const in loops), event bubbling vs capturing, synchronous vs asynchronous execution (why callbacks and promises exist), and basic DOM manipulation patterns.

### Week 11: Unit Testing and JUnit

**Content covered:**
- Why unit testing: catching bugs early, enabling refactoring, documenting behaviour
- JUnit 5 annotations: `@Test`, `@BeforeEach`, `@AfterEach`, `@BeforeAll`, `@AfterAll`, `@Disabled`, `@DisplayName`, `@ParameterizedTest`
- Assertions: `assertEquals()`, `assertNotEquals()`, `assertTrue()`, `assertFalse()`, `assertNull()`, `assertNotNull()`, `assertThrows()`, `assertAll()`
- Mockito basics: `@Mock`, `@InjectMocks`, `when().thenReturn()`, `verify()`
- Test coverage concepts
- Test-Driven Development (TDD) concept

**JUnit test structure:**
```java
@ExtendWith(MockitoExtension.class)
class BankAccountTest {

    @Mock
    private TransactionLogger logger;  // mock dependency

    @InjectMocks
    private BankAccount account;       // subject under test with mocks injected

    @BeforeEach
    void setUp() {
        account = new BankAccount("Test User", 1000.0);
    }

    @Test
    @DisplayName("Deposit positive amount increases balance")
    void depositPositiveAmount() {
        account.deposit(500.0);
        assertEquals(1500.0, account.getBalance(), 0.001);
    }

    @Test
    @DisplayName("Withdrawing more than balance returns false")
    void overdraftReturnsFalse() {
        boolean result = account.withdraw(2000.0);
        assertFalse(result);
        assertEquals(1000.0, account.getBalance(), 0.001);  // balance unchanged
    }

    @Test
    @DisplayName("Withdrawing negative amount throws exception")
    void negativeWithdrawalThrowsException() {
        assertThrows(IllegalArgumentException.class, () -> account.withdraw(-100));
    }
}
```

### Week 12: Phase 2 Project

**Typical Java ILP Project Brief:**

A representative Phase 2 project brief: "Build a Student Grade Management System. The system must allow: registration of students with name, roll number, and programme; recording marks per subject per student; computing grade based on marks (A: 90+, B: 75-89, C: 60-74, D: 50-59, F: below 50); generating report cards; and a REST API exposing all these operations."

**The full-stack architecture expected:**
- **Backend:** Spring Boot REST API
- **Database:** MySQL with JDBC or Spring Data JPA
- **Frontend:** HTML/CSS/JavaScript making fetch() calls to the REST API
- **Testing:** JUnit tests for service layer logic

**What the team must produce:**
1. Database schema (CREATE TABLE statements for all entities)
2. Spring Boot project with service, repository, and controller layers
3. Basic HTML/JS frontend
4. JUnit tests for at least 3 meaningful test cases
5. A 15-minute presentation explaining architecture, design decisions, and live demonstration

---

## The IRA Assessment Structure: Detailed Preparation Guide

### IRA1 - Core Java and SQL Assessment

**Typical IRA1 coverage:**
Weeks 1-4 content: Java basics, OOP (all four pillars), Exception handling, Collections Framework, and SQL fundamentals.

**MCQ question patterns:**

**Output-prediction questions (most common):**
"What is the output of the following code?"
```java
int x = 5;
System.out.println(x++);    // prints 5 (post-increment: use then increment)
System.out.println(++x);    // prints 7 (pre-increment: increment then use)
System.out.println(x);      // prints 7
```

These require understanding operator precedence, short-circuit evaluation, and how Java evaluates expressions.

**Exception-type identification:**
"Which exception is thrown when: dividing an integer by zero? (ArithmeticException) / accessing a null reference? (NullPointerException) / array index out of bounds? (ArrayIndexOutOfBoundsException) / casting incompatible types? (ClassCastException)"

**Collections behaviour:**
"A HashSet contains: [1, 3, 3, 5, 7]. After all insertions, how many elements does it contain?" Answer: 4 (HashSet rejects duplicates; 3 appears twice but is stored once).

**SQL join result prediction:**
Given two tables and a JOIN query, determine the result set. These require understanding which rows are included in INNER vs LEFT JOIN.

**IRA1 coding component:**

Typical IRA1 coding problems (30-45 minutes for 1-2 problems):
- Implement a class hierarchy (e.g., Animal → Dog, Cat, Bird) demonstrating inheritance and method overriding
- Write a method that uses HashMap to return the frequency of each character in a string
- Implement a simple stack using ArrayList
- Write a recursive method with exception handling

**IRA1 preparation strategy:**
- Practice 20 output-prediction questions per day in the week before IRA1
- Know the four OOP pillars, abstract class vs interface, and Collections time complexity without hesitation
- Write the HashMap frequency count and ArrayList stack from memory - these appear or variants of them appear in most IRA1 coding sections

### IRA2 - Advanced Java and Web Technologies

**Typical IRA2 coverage:**
Weeks 5-9 content: Generics, Multithreading, Java I/O, Java 8 features, JDBC, Servlets, JSP, and Spring Framework introduction.

**MCQ patterns for IRA2:**

**Thread safety identification:**
"Which of the following is thread-safe: StringBuilder or StringBuffer?" Answer: StringBuffer (methods are synchronised). StringBuilder is faster but not thread-safe.

**Stream API output:**
"What does this code print?"
```java
Arrays.asList(3, 1, 4, 1, 5, 9, 2, 6)
    .stream()
    .filter(n -> n > 3)
    .sorted()
    .distinct()
    .forEach(System.out::println);
```
Answer: 4, 5, 6, 9 (filter for > 3: [4, 1, 5, 9, 6] → sorted: [4, 5, 6, 9] → distinct: no duplicates → print each)

Note: 1 appears twice but is filtered out at the filter step. This type of question requires tracing the stream pipeline step by step.

**Servlet lifecycle:**
"In what order are servlet lifecycle methods called?" Answer: init() → service() (repeatedly) → destroy()

**JDBC sequence:**
"Which object is used for parameterised queries to prevent SQL injection?" Answer: PreparedStatement.

**IRA2 coding component:**

Typical IRA2 problems:
- Write a multithreaded application where two threads update a shared list concurrently, then fix thread safety issues
- Implement a JDBC-based CRUD application for a simple entity (Product, Employee, etc.)
- Write a Stream API solution: given a list of Employee objects with name, department, and salary, find the average salary per department

**IRA2 preparation strategy:**
- Practice Stream API chains daily from Week 6. The ability to read and write Stream chains fluently is the single most testable Java 8 skill.
- Write the JDBC connection and CRUD pattern from memory
- Know the servlet lifecycle and the forward/redirect distinction cold

### PRA - The Final Comprehensive Assessment

**PRA scope:**
All ILP content - Weeks 1-11 syllabus. The PRA is typically a longer, project-style assessment lasting 4-6 hours.

**PRA format:**

Most PRA assessments have:
1. **MCQ section:** 30-50 questions across all topics (faster pacing than IRA MCQ - the full breadth is tested)
2. **Coding problem (primary):** Build a small application. The requirements are provided; you implement from scratch. Common PRA projects include: a library management system, a student grade calculator, or a simple e-commerce backend.

**PRA coding problem preparation:**

The PRA coding problem tests whether you can independently build a working application. Preparation:
- Build at least 2 complete projects independently (not just exercises) before PRA
- Practice the "start to running application" workflow: create Maven/Gradle project → add dependencies → implement domain model → add service layer → add repository/DAO → test with main method or unit tests
- Time yourself: the goal is a working application in 3-4 hours, leaving time for testing and edge cases

---

## Non-CS Students: Succeeding in Java ILP Without a CS Background

Many Java ILP trainees come from non-CS engineering branches (ECE, Mechanical, Civil, Chemical) or from MCA/BCA programs with varying Java exposure. The adjustment is real but entirely manageable.

### What Non-CS Students Have That Helps

**Problem-solving foundation:** Engineering education builds systematic problem decomposition - the same skill that software development requires. Non-CS engineers often think through problems methodically in ways that serve programming well.

**Domain knowledge:** An ECE graduate who joins a Java project developing telecom billing systems brings domain understanding that pure CS graduates may lack. Domain knowledge is valuable in enterprise software.

**Exam discipline:** Non-CS engineering graduates have typically written demanding examinations across multiple subjects simultaneously. The discipline of managing a large syllabus under time pressure is already developed.

### The Specific Gaps to Bridge

**Programming practice volume:** CS students typically have written hundreds of programs by the time they reach ILP. Non-CS engineering students may have written tens. This practice gap is real and requires deliberate bridging. Write code every day during Aspire and ILP.

**Data structures intuition:** CS graduates learn data structures as a dedicated subject and develop strong intuition about when to use which structure. Non-CS graduates often need to build this intuition explicitly. The Collections Framework section of this guide's complexity table should be memorised.

**OOP thinking:** Object-oriented design requires thinking in terms of objects, responsibilities, and relationships rather than procedures and steps. This mental model takes time to build. Practice designing classes on paper before coding them.

### The Practical Plan for Non-CS Students

**Before ILP (during Aspire or pre-joining period):**
Week 1: Complete Chapters 1-5 of a beginner Java book (Head First Java or Core Java Volume I). Focus on Weeks 1-2 content from this guide.
Week 2: Write 10 Java programs from scratch. No copy-paste. Type every character and understand every line.
Week 3: Complete the Collections Framework section. Build 3 programs using HashMap, ArrayList, and LinkedList.
Week 4: Write one complete OOP program with inheritance (e.g., Shape hierarchy) and one program using exception handling.

**During ILP:**
- Arrive 30 minutes early each day to review the previous day's content
- Never skip the coding exercises in the portal
- Pair with a CS-background batchmate for the most complex topics (multithreading, Spring DI) - explanation by a peer often clarifies faster than rereading the PDF

---

## How Java ILP Maps to Actual TCS Projects

The ILP curriculum is not theoretical - it maps directly to what Java developers do in TCS projects. Understanding this mapping helps you focus on the right depth for each topic.

**Core Java (Weeks 1-5):** Used in every Java project. Exception handling, Collections, and multithreading appear daily in any non-trivial Java application. These deserve the deepest preparation because they never stop being relevant.

**Java 8 features (Week 6):** Almost every TCS Java project written in the past several years uses Streams and Lambdas. You will see Stream API code in the first week of your first project. Fluency with functional Java style is a daily requirement.

**JDBC (Week 7):** Direct JDBC is used in older projects and in performance-sensitive components. Most modern TCS projects use Spring Data JPA or MyBatis as an abstraction over JDBC. Understanding JDBC gives you the foundation to understand what Spring Data JPA is doing under the hood.

**Servlets (Week 8):** Pure Servlet-based web applications are legacy but still exist in TCS's maintenance project portfolio. More importantly, understanding Servlets gives you the foundation to understand Spring MVC - which is what modern TCS projects actually use.

**JSP (Week 9):** Server-side rendering with JSP is decreasing in modern projects in favour of React/Angular frontends with REST backends. However, legacy JSP-based UI exists throughout TCS's maintenance portfolio. Understanding JSP means you can read and modify legacy UI code.

**Spring Boot (Week 9):** This is where the highest-value ILP content lives. Spring Boot with REST APIs is the dominant architecture for new TCS Java projects. Every Java developer on a new project in TCS will be writing `@RestController` classes, using `@Service` beans, and leveraging Spring Boot auto-configuration.

**HTML/CSS/JS (Week 10):** Frontend development in TCS projects is increasingly handled by separate frontend developers using React or Angular. However, Java developers need enough HTML/CSS/JS to understand the full-stack architecture, debug cross-origin issues, and participate in architectural discussions.

**JUnit (Week 11):** TCS projects maintain unit test suites. Adding unit tests for new code is expected. Knowing how to write testable code (dependency injection enables mocking) and how to write good tests (test behaviour, not implementation) is a real day-to-day skill.

---

## External Resources for Supplementing TCS Portal Content

The TCS portal PDFs and videos are the primary reference for ILP content. These external resources supplement them effectively:

**For Core Java (Weeks 1-5):**
- Oracle's official Java documentation: the authoritative reference, best for precise behaviour
- Baeldung.com: excellent Java tutorials with working code examples for every topic
- "Effective Java" by Joshua Bloch: for depth on best practices (read selectively - Chapter 2 on creating and destroying objects, Chapter 4 on classes and interfaces)

**For Java 8 features (Week 6):**
- Oracle's Java 8 stream documentation: precise and complete
- Baeldung's Stream API tutorial series: practical examples for every stream operation

**For JDBC and Spring (Weeks 7-9):**
- Spring official documentation (spring.io): the authoritative Spring reference
- "Spring in Action" by Craig Walls: comprehensive Spring book (select chapters relevant to ILP scope)
- Spring Boot's official guides (spring.io/guides): short, runnable examples for specific topics

**For SQL:**
- SQLZoo.net: interactive SQL practice with immediate feedback
- HackerRank SQL challenges: graded SQL problems for practice

**For interactive assessment practice:**
The [TCS ILP Preparation Guide](https://reportmedic.org/tools/tcs-ilp-preparation-guide.html) provides IRA-format MCQ and coding practice across all Java ILP topics, with questions calibrated to the actual difficulty and format of TCS assessments.

---

## Common Mistakes Freshers Make in Java ILP

**Mistake 1: Reading code instead of writing code.**
The TCS portal provides PDF notes and code examples. Reading them feels productive but produces limited learning. The only way to build coding skill is to write code. Ratio should be: 20% reading, 80% coding.

**Mistake 2: Memorising syntax instead of understanding concepts.**
IRA MCQ tests conceptual understanding, not syntax memorisation. "What does `++x` return compared to `x++`" tests operator understanding, not syntax. Understanding why the distinction exists (post-increment uses the current value, then increments; pre-increment increments first, then uses the result) makes every related question answerable without separate memorisation.

**Mistake 3: Not reading error messages.**
Java error messages are informative. `NullPointerException at line 47` tells you exactly where and what failed. Many trainees see an error, feel discouraged, and ask for help before reading the error carefully. Read every error message completely before attempting to fix it - it usually tells you exactly what is wrong.

**Mistake 4: Writing code without testing it.**
Every program written during ILP should be run and its output verified against expected output. Writing 10 programs you never ran teaches you nothing. Writing and running 5 programs, understanding why each output is what it is, teaches you significantly.

**Mistake 5: Treating Java 8 features as optional.**
Some trainees focus heavily on Core Java and treat Java 8 features (Streams, Lambdas) as advanced content that can be studied later. In IRA2 and in real projects, Java 8 features are not advanced - they are standard. The Stream API appears in IRA2 and in every real TCS Java project.

**Mistake 6: Underestimating SQL.**
SQL questions appear in IRA1 and IRA2. JOIN queries, GROUP BY with HAVING, and subqueries are regularly tested. Trainees who focus entirely on Java and treat SQL as secondary consistently underperform in IRA assessments.

---

## The Daily Routine in Java ILP: What a Well-Structured Day Looks Like

A productive Java ILP day (representative, actual schedules vary by center):

**8:30-9:00 AM: Morning Review (30 minutes)**
Re-read yesterday's notes. Write down three concepts you are not 100% clear on. This sets the agenda for the day's deeper engagement.

**9:00 AM - 1:00 PM: Portal Content (4 hours)**
Work through the day's assigned content on the TCS portal. For every code example in the PDF: type it yourself, run it, modify it in 2-3 ways to test your understanding. Do not proceed to the next section until the current section's code examples run and you understand why each line works.

**1:00-2:00 PM: Lunch Break**

**2:00-4:00 PM: Practice Problems (2 hours)**
Complete the portal's exercises. If portal exercises are finished, write additional programs from the topic area. Minimum: write 3 programs from the day's topic independently (without copying code from the PDF).

**4:00-5:30 PM: Deep Dive (1.5 hours)**
Pick the one concept from the day that was least clear. Read about it from an external source (Baeldung, Oracle docs). Write a program that specifically demonstrates that concept.

**5:30-6:00 PM: Tomorrow's Preview (30 minutes)**
Read the first few pages of tomorrow's content. This primes your brain to process the content more effectively when you cover it in depth.

**Evening (1-2 hours, personal/project time):**
Work on your personal practice project - incrementally adding features as you learn them. By the end of ILP, your practice project should demonstrate every major topic covered.

---

## Week-by-Week Study Plan: Summary

| Week | Topics | Daily Practice Focus | Assessment Approaching |
|---|---|---|---|
| 1 | Java basics, control flow | Arithmetic programs, simple algorithms | - |
| 2 | OOP: classes, objects, encapsulation | BankAccount, Student, Shape classes | - |
| 3 | Inheritance, polymorphism, abstraction | Class hierarchies, interfaces | - |
| 4 | Exceptions, Collections | HashMap programs, custom exceptions | IRA1 preparation begins |
| 5 | Generics, Threads, I/O | File reader, thread safety demos | **IRA1** |
| 6 | Java 8: Streams, Lambdas | Stream pipeline exercises | - |
| 7 | JDBC, SQL | CRUD with PreparedStatement | - |
| 8 | Servlets, HTTP | Simple servlet web app | IRA2 preparation begins |
| 9 | JSP, Spring Boot | Spring REST API | **IRA2** |
| 10 | HTML, CSS, JS | Full-stack mini app | PRA preparation begins |
| 11 | JUnit, Mockito | Test-first development | **PRA** |
| 12 | Phase 2 project | Team project implementation | Final presentation |

---

## Frequently Asked Questions: TCS ILP Java

**Can I use IntelliJ IDEA instead of Eclipse during ILP?**
The TCS portal and lab computers typically have Eclipse configured. Your personal laptop can use IntelliJ. For IRA assessments conducted on TCS lab computers, Eclipse is the available IDE. Practice in Eclipse enough to be comfortable - keyboard shortcuts, project setup, and debugging interface differ from IntelliJ.

**Is Spring Boot in the ILP or only Spring Framework?**
Both are covered. The trajectory is: Spring Framework concepts (IoC, DI, beans) → Spring MVC → Spring Boot (which makes Spring MVC setup much faster). By the end of Week 9, you should be able to create a working Spring Boot REST API.

**How much of Java ILP content is directly tested in PRA?**
PRA covers the full syllabus but the coding portion focuses on building an application - which tests whether you can integrate knowledge from multiple weeks (OOP model + Collections + JDBC + Spring). It is less about recalling specific API methods and more about applying the full-stack architecture.

**How should I handle topics where the TCS PDF is unclear?**
External resources (Oracle documentation, Baeldung) are consistently clearer than ILP PDFs for many topics. Using external resources to understand a topic and then returning to the ILP portal to do the exercises is a completely valid approach. The portal exercises are the core practice; the PDF is the explanation.

**What is the best single project to build during ILP for practice?**
A Library Management System covers nearly every ILP Java topic: a `Book` class (OOP, encapsulation), a `Library` class with `List<Book>` (Collections), custom exceptions for unavailable books (Exception handling), a JDBC layer for book storage (JDBC), a Spring REST API exposing book operations (Spring Boot), and JUnit tests for the lending logic. Build it from scratch, adding one feature per week, and you have practised the entire curriculum through application.

**What do ILP facilitators actually evaluate beyond assessments?**
Facilitators observe: engagement during sessions (asking questions, participating in discussions), how you interact with batchmates during group activities, your response when you make mistakes (do you learn from them?), and your consistency (do you engage the same way on Day 1 as on Day 40?). These observations feed into the holistic ILP rating alongside assessment scores.

---

## Core Java: Extended Concept Reference

### Understanding Java Memory Model

The Java memory model is a frequently tested IRA topic that non-CS students often find abstract. A clear mental model makes the questions straightforward.

**Stack and Heap:**

When your Java program runs, two memory areas are active:

**Stack:** Stores method call frames. Each time you call a method, a new frame is pushed containing: local variables, the method's parameters, and the return address. When the method returns, the frame is popped. Stack memory is fast, automatically managed, and limited in size (StackOverflowError = stack full, usually from infinite recursion).

**Heap:** Stores objects (all objects created with `new`). The heap is managed by Java's garbage collector, which automatically reclaims memory from objects with no references. The heap is large but slower than the stack.

**Implications for IRA:**

```java
int x = 5;              // x lives on the stack (primitive)
String s = "hello";     // s reference lives on stack, "hello" object lives on heap
Student st = new Student("Priya"); // st reference on stack, Student object on heap
```

When you pass a primitive to a method, a copy is made (the original is unaffected). When you pass an object reference, the reference is copied but it still points to the same heap object (modifications to the object are visible outside the method).

### The String Pool

The String pool is a special area in Java's heap where String literals are stored for reuse.

```java
String s1 = "hello";    // stored in String pool
String s2 = "hello";    // reuses the same pool object
String s3 = new String("hello"); // creates NEW object in heap (NOT pool)

System.out.println(s1 == s2);   // true (same pool object)
System.out.println(s1 == s3);   // false (different heap objects)
System.out.println(s1.equals(s3)); // true (same content)
```

IRA questions about String comparison (== vs .equals()) almost always relate to this pool distinction.

### Wrapper Classes and Auto-boxing

Every Java primitive has a corresponding wrapper class:
`int` → `Integer`, `double` → `Double`, `boolean` → `Boolean`, `char` → `Character`, etc.

**Auto-boxing:** Java automatically converts primitives to wrapper objects when needed.
**Unboxing:** Java automatically converts wrapper objects back to primitives.

```java
int x = 5;
Integer y = x;    // auto-boxing: int → Integer
int z = y;        // unboxing: Integer → int
```

**The Integer cache trap (frequent IRA question):**
```java
Integer a = 127;
Integer b = 127;
System.out.println(a == b);  // true (Java caches Integer values -128 to 127)

Integer c = 128;
Integer d = 128;
System.out.println(c == d);  // false (outside cache range, new objects created)
System.out.println(c.equals(d));  // true (content comparison)
```

This is a classic IRA trap. Always use `.equals()` to compare Integer objects.

### Comparable and Comparator

Sorting custom objects requires either implementing `Comparable` (natural order) or providing a `Comparator` (custom order).

```java
// Natural ordering with Comparable
public class Student implements Comparable<Student> {
    private String name;
    private double gpa;

    @Override
    public int compareTo(Student other) {
        return Double.compare(this.gpa, other.gpa); // ascending by GPA
    }
}

// Custom ordering with Comparator (Java 8 lambda style)
List<Student> students = getStudentList();
students.sort(Comparator.comparing(Student::getName));         // by name
students.sort(Comparator.comparingDouble(Student::getGpa).reversed()); // descending GPA
students.sort(Comparator.comparing(Student::getName)
    .thenComparingDouble(Student::getGpa));  // name first, then GPA
```

IRA questions: "Which interface provides natural ordering?" (Comparable). "Which method must be implemented from Comparable?" (compareTo). "How do you sort in descending order using Comparator?" (.reversed() or reversed compareTo logic).

---

## Advanced Java Deep Dive: Thread Coordination

### The Producer-Consumer Pattern

Thread coordination using wait/notify is a classic IRA and real-world problem. The producer-consumer pattern demonstrates it cleanly:

```java
class SharedBuffer {
    private int data;
    private boolean hasData = false;

    // Producer calls this
    public synchronized void produce(int value) throws InterruptedException {
        while (hasData) {
            wait();  // wait until consumer has consumed
        }
        data = value;
        hasData = true;
        System.out.println("Produced: " + value);
        notify();  // wake up consumer
    }

    // Consumer calls this
    public synchronized int consume() throws InterruptedException {
        while (!hasData) {
            wait();  // wait until producer has produced
        }
        hasData = false;
        System.out.println("Consumed: " + data);
        notify();  // wake up producer
        return data;
    }
}
```

**Why `wait()` is in a `while` loop, not an `if`:** Spurious wakeups (threads waking up without notify being called) can occur. The while loop re-checks the condition after waking, ensuring correctness even under spurious wakeup.

### ExecutorService: The Modern Threading Approach

Modern Java code uses ExecutorService rather than raw Threads:

```java
ExecutorService executor = Executors.newFixedThreadPool(4); // thread pool of 4

// Submit tasks
Future<Integer> future = executor.submit(() -> {
    // compute something and return result
    return computeExpensiveResult();
});

// Get result (blocks until available)
try {
    Integer result = future.get();
} catch (InterruptedException | ExecutionException e) {
    e.printStackTrace();
}

executor.shutdown(); // stop accepting new tasks
executor.awaitTermination(1, TimeUnit.MINUTES); // wait for completion
```

ILP assessments at the later stages cover ExecutorService concepts. The key difference from raw threads: the thread pool is managed for you, task submission is decoupled from thread management, and Future provides a way to retrieve results.

---

## Spring Framework: Deeper Understanding

### The IoC Container

The Spring IoC container is responsible for creating objects, wiring their dependencies, and managing their lifecycle. Understanding this end-to-end helps demystify Spring's "magic."

**Without Spring (manual dependency management):**
```java
// OrderController manually creates all dependencies
DataSource dataSource = new MySQLDataSource("jdbc:mysql://localhost/orders");
ProductRepository productRepo = new JdbcProductRepository(dataSource);
InventoryService inventoryService = new InventoryServiceImpl(productRepo);
OrderRepository orderRepo = new JdbcOrderRepository(dataSource);
OrderService orderService = new OrderServiceImpl(orderRepo, inventoryService);
OrderController controller = new OrderController(orderService);
```

**With Spring (IoC container does the wiring):**
```java
@Repository
public class JdbcProductRepository implements ProductRepository {
    @Autowired
    private DataSource dataSource;  // Spring injects configured DataSource
}

@Service
public class OrderServiceImpl implements OrderService {
    @Autowired
    private OrderRepository orderRepository;  // Spring injects
    @Autowired
    private InventoryService inventoryService;  // Spring injects
}

@RestController
public class OrderController {
    @Autowired
    private OrderService orderService;  // Spring injects
}
```

Spring reads the annotations, figures out what each class needs, creates instances in the right order, and wires everything together. The result: OrderController gets a fully-wired OrderService without any manual construction code.

### Spring Boot application.properties

Understanding configuration through `application.properties` or `application.yml` is an ILP requirement:

```properties
# application.properties
server.port=8080
spring.datasource.url=jdbc:mysql://localhost:3306/studentdb
spring.datasource.username=root
spring.datasource.password=rootpassword
spring.datasource.driver-class-name=com.mysql.cj.jdbc.Driver

# JPA configuration
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
spring.jpa.database-platform=org.hibernate.dialect.MySQL8Dialect

# Logging
logging.level.com.tcs.training=DEBUG
```

Configuring the database connection through properties (not hardcoded in source) is the production-quality approach that ILP teaches.

---

## IRA Practice Problem Bank

These problems match the type, format, and difficulty of actual TCS ILP IRA assessments. Practice each under timed conditions.

### Core Java MCQ Practice (IRA1 Level)

**Problem 1:** What is the output?
```java
String s = "Java";
s.concat(" Programming");
System.out.println(s);
```
Options: (A) Java Programming (B) Java (C) Compilation error (D) Null

**Answer: (B) Java.** String objects are immutable. `concat()` returns a new String but does not modify the original. Since the returned value is not assigned to anything, `s` still points to "Java". Correct code: `s = s.concat(" Programming");`

**Problem 2:** Which Collection allows duplicate elements and maintains insertion order?
Options: (A) HashSet (B) TreeSet (C) ArrayList (D) HashMap

**Answer: (C) ArrayList.** HashSet and TreeSet store unique elements. HashMap stores key-value pairs (keys are unique). ArrayList maintains insertion order and allows duplicates.

**Problem 3:** What is the output?
```java
int[] arr = {10, 20, 30, 40, 50};
System.out.println(arr[arr.length]);
```
Options: (A) 50 (B) 0 (C) ArrayIndexOutOfBoundsException (D) Compilation error

**Answer: (C) ArrayIndexOutOfBoundsException.** `arr.length` is 5. Valid indices are 0-4. `arr[5]` throws ArrayIndexOutOfBoundsException at runtime.

**Problem 4:** Which keyword prevents a method from being overridden in a subclass?
Options: (A) static (B) private (C) final (D) abstract

**Answer: (C) final.** A `final` method cannot be overridden. `private` methods are not inherited (so cannot be overridden, but for a different reason). `abstract` requires overriding. `static` methods are hidden, not overridden.

**Problem 5:** What is the output?
```java
int x = 10;
int y = x++;
System.out.println(x + " " + y);
```
Options: (A) 10 10 (B) 11 10 (C) 10 11 (D) 11 11

**Answer: (B) 11 10.** Post-increment: `y = x++` assigns the current value of x (10) to y, then increments x to 11.

### Collections and Generics Practice

**Problem 6:** What is the output?
```java
Map<String, Integer> map = new HashMap<>();
map.put("A", 1);
map.put("B", 2);
map.put("A", 3);
System.out.println(map.size() + " " + map.get("A"));
```
Answer: `2 3`. HashMap stores unique keys. Second `put("A", 3)` replaces the first value. Size remains 2 (keys A and B), and `get("A")` returns 3.

**Problem 7:** Which of the following will throw ConcurrentModificationException?
```java
List<Integer> list = new ArrayList<>(Arrays.asList(1, 2, 3, 4, 5));
for (Integer n : list) {
    if (n % 2 == 0) list.remove(n);  // (A)
}
```
vs.
```java
Iterator<Integer> iter = list.iterator();
while (iter.hasNext()) {
    if (iter.next() % 2 == 0) iter.remove();  // (B)
}
```
Answer: (A) throws ConcurrentModificationException. (B) is safe. Use `Iterator.remove()` when removing during iteration.

### Stream API Practice (IRA2 Level)

**Problem 8:** What does this code print?
```java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie", "David", "Eve");
long count = names.stream()
    .filter(name -> name.length() > 3)
    .map(String::toUpperCase)
    .filter(name -> name.startsWith("C") || name.startsWith("D"))
    .count();
System.out.println(count);
```
Answer: `2`. Trace: filter(length > 3) → [Alice, Charlie, David] (Bob=3 letters excluded, Eve=3 letters excluded, wait - Alice has 5, Bob has 3, Charlie has 7, David has 5, Eve has 3). Filter passes: Alice, Charlie, David. Map to uppercase: ALICE, CHARLIE, DAVID. Filter starts with C or D: CHARLIE, DAVID. Count = 2.

**Problem 9:** What does `Optional.ofNullable(null).orElse("default")` return?
Answer: `"default"`. `ofNullable()` creates an Optional that can contain null. `orElse()` returns the wrapped value if present, or the provided default if empty/null.

### SQL Practice

**Problem 10:** Given table `Orders(order_id, customer_id, amount, order_date)`, write a query to find customers who have placed more than 3 orders with total amount greater than Rs. 50,000.

```sql
SELECT customer_id,
       COUNT(order_id) AS order_count,
       SUM(amount) AS total_amount
FROM Orders
GROUP BY customer_id
HAVING COUNT(order_id) > 3
AND SUM(amount) > 50000;
```

Key points: GROUP BY groups rows by customer. HAVING filters groups (use HAVING, not WHERE, for aggregate conditions).

**Problem 11:** Write a query to display employee names along with their manager's name from a self-referential `Employees(emp_id, name, manager_id)` table.

```sql
SELECT e.name AS employee,
       m.name AS manager
FROM Employees e
INNER JOIN Employees m ON e.manager_id = m.emp_id;
```

Self-join: join the table to itself. The employee table aliased as `e` is joined to the same table aliased as `m` where the employee's manager_id matches the manager's emp_id.

---

## The Phase 2 Project: Building a Complete Application

### Architecture Planning: Before Writing Code

The most common Phase 2 mistake is to start coding immediately without designing. Spend the first 2-3 hours of Phase 2 on design:

**1. Requirements clarification:** Read the project brief carefully. List every feature required. Identify ambiguities and decide (as a team) how to handle them.

**2. Database design:** Identify entities (nouns in the requirements) and their attributes. Define relationships (one-to-many, many-to-many). Write CREATE TABLE statements before writing any Java code.

**3. API design:** Define the REST endpoints your backend will expose:
- `GET /api/students` - list all students
- `GET /api/students/{id}` - get one student
- `POST /api/students` - create student
- `PUT /api/students/{id}` - update student
- `DELETE /api/students/{id}` - delete student

**4. Layer architecture:** Plan the layers:
- Controller (handles HTTP, calls Service)
- Service (business logic, calls Repository)
- Repository (database access, returns domain objects)
- Model/Entity (Java classes representing database tables)

**5. Work division:** Assign each team member specific components. Typical division for a 5-person team: 1 person on database + data model, 2 people on service + repository layers, 1 person on controllers + REST API, 1 person on frontend + integration.

### A Sample Phase 2 Project: Student Grade Management

**Database schema:**
```sql
CREATE TABLE students (
    student_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    roll_number VARCHAR(20) UNIQUE NOT NULL,
    programme VARCHAR(50) NOT NULL,
    email VARCHAR(100)
);

CREATE TABLE subjects (
    subject_id INT PRIMARY KEY AUTO_INCREMENT,
    subject_name VARCHAR(100) NOT NULL,
    max_marks INT DEFAULT 100
);

CREATE TABLE grades (
    grade_id INT PRIMARY KEY AUTO_INCREMENT,
    student_id INT NOT NULL,
    subject_id INT NOT NULL,
    marks_obtained DECIMAL(5,2),
    grade_letter CHAR(1),
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);
```

**Spring Boot entity (Student.java):**
```java
@Entity
@Table(name = "students")
public class Student {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long studentId;

    @Column(nullable = false)
    private String name;

    @Column(unique = true, nullable = false)
    private String rollNumber;

    private String programme;
    private String email;

    // Getters, setters, constructors
}
```

**Service layer (StudentService.java):**
```java
@Service
public class StudentService {

    @Autowired
    private StudentRepository studentRepository;

    public List<Student> getAllStudents() {
        return studentRepository.findAll();
    }

    public Student createStudent(Student student) {
        // Business validation
        if (studentRepository.existsByRollNumber(student.getRollNumber())) {
            throw new RuntimeException("Roll number already exists: " + student.getRollNumber());
        }
        return studentRepository.save(student);
    }

    public String computeGrade(double marks) {
        if (marks >= 90) return "A";
        if (marks >= 75) return "B";
        if (marks >= 60) return "C";
        if (marks >= 50) return "D";
        return "F";
    }
}
```

**Controller layer (StudentController.java):**
```java
@RestController
@RequestMapping("/api/students")
@CrossOrigin(origins = "*")  // allow frontend requests during development
public class StudentController {

    @Autowired
    private StudentService studentService;

    @GetMapping
    public ResponseEntity<List<Student>> getAllStudents() {
        return ResponseEntity.ok(studentService.getAllStudents());
    }

    @PostMapping
    public ResponseEntity<Student> createStudent(@RequestBody Student student) {
        try {
            Student created = studentService.createStudent(student);
            return ResponseEntity.status(HttpStatus.CREATED).body(created);
        } catch (RuntimeException e) {
            return ResponseEntity.badRequest().build();
        }
    }
}
```

**Frontend fetch call (JavaScript):**
```javascript
async function loadStudents() {
    try {
        const response = await fetch('http://localhost:8080/api/students');
        const students = await response.json();
        displayStudents(students);
    } catch (error) {
        console.error('Failed to load students:', error);
    }
}

function displayStudents(students) {
    const tableBody = document.getElementById('studentTableBody');
    tableBody.innerHTML = '';
    students.forEach(student => {
        const row = `<tr>
            <td>${student.rollNumber}</td>
            <td>${student.name}</td>
            <td>${student.programme}</td>
        </tr>`;
        tableBody.innerHTML += row;
    });
}
```

---

## Self-Learning Format: Making It Work Without a Classroom

TCS ILP's self-paced model requires a different learning approach than classroom instruction. Students accustomed to lectures need to actively build the structure that the classroom previously provided.

### Building Your Own Study Structure

**Active recall over passive reading:** After reading a section of the ILP PDF, close it and write down everything you remember. The effort of recall strengthens retention far more than rereading. For every 30 minutes of reading, spend 10 minutes recalling without reference.

**The Feynman method for difficult concepts:** When a concept is unclear (IoC, polymorphism dispatch, thread safety), explain it aloud to yourself as if teaching it to someone who knows nothing about Java. The process of explanation reveals gaps in your understanding more accurately than any test.

**Spaced repetition for memorisation:** For facts that must be memorised (collection time complexities, exception hierarchy, servlet lifecycle order), review them with increasing intervals: review today, tomorrow, in 3 days, in 7 days, in 14 days. Apps like Anki support this pattern. Even a physical set of flashcards works.

**Peer teaching:** Form a study group where each person teaches one topic per day. The person who teaches learns the most. If you are given 20 minutes to explain lambda expressions to your batchmates, you will understand lambda expressions far more deeply than someone who just read about them.

### When the Portal Content Is Insufficient

TCS ILP portal content ranges from excellent to unclear depending on the topic and the PDF author. When a topic is not clear from the portal:

**Step 1:** Try a different explanation source first (Baeldung for most Java topics, Oracle documentation for precise API behaviour).

**Step 2:** Write a small program that demonstrates the concept in isolation. Often the confusion is about how something behaves in practice, not what it is in theory.

**Step 3:** Ask a batchmate who has understood the topic. Peer explanation is often faster than rereading.

**Step 4:** Ask the facilitator with a specific question ("I understand that HashMap uses hashCode(), but I'm not clear on what happens when two keys have the same hashCode - can you walk me through that?"). Specific questions get useful answers. Vague questions get generic answers.

---

## Life After Java ILP: Your First Java Project

### What to Expect on a Real TCS Java Project

The application you are likely to work on in your first TCS Java project is significantly larger and more complex than anything built in ILP. Realistic expectations:

**Codebase size:** Enterprise Java projects can have hundreds of classes across dozens of packages. Do not expect to understand the full codebase in your first month. Focus on the specific module assigned to you.

**Build tools:** Most TCS Java projects use Maven or Gradle for dependency management and build automation. ILP may have introduced these; your first project will use them daily. Learn `mvn clean install`, `mvn test`, and how to read the `pom.xml` or `build.gradle`.

**Version control:** Every TCS project uses Git. Learn the basic Git workflow: clone → branch → commit → push → pull request. Knowing git rebase, git cherry-pick, and git bisect comes later - the fundamental workflow comes first.

**Code review culture:** Your code will be reviewed by senior developers before it is merged. This is not a judgment of your worth - it is a quality gate that every developer, regardless of seniority, goes through. Read code review comments as learning opportunities, not criticisms.

**Testing expectations:** TCS projects maintain unit test suites. Adding unit tests for any new code you write is standard practice. ILP's JUnit content directly applies from Day 1 of your first project.

**The gap between ILP and project reality:** ILP teaches you the technologies; your first project teaches you how to use them in a real system. The gap is real but bridgeable. Every senior TCS Java developer you work with went through the same transition. Ask questions, contribute early, and be patient with the learning curve.

---

## Java ILP: The Complete Preparation Checklist

Before ILP starts - confirm each item:

**Environment:**
- [ ] JDK 17 installed and `java -version` returns correct version
- [ ] Eclipse IDE installed and a test project created/compiled/run
- [ ] MySQL Community Server installed and running
- [ ] MySQL Workbench installed and connected to local MySQL

**Aspire completion:**
- [ ] Programming fundamentals module completed (code typed and run, not just read)
- [ ] OOP module completed
- [ ] Database/SQL module completed (queries executed in MySQL Workbench)
- [ ] Software engineering module reviewed

**Pre-ILP coding practice:**
- [ ] Written and run at least 15 Java programs from scratch
- [ ] Implemented at least one class hierarchy (3+ classes)
- [ ] Written a HashMap-based program
- [ ] Written a file reading program with exception handling

**Conceptual readiness:**
- [ ] Can explain the four OOP pillars with examples without reference
- [ ] Know when to use ArrayList vs LinkedList vs HashSet vs HashMap
- [ ] Know the servlet lifecycle order
- [ ] Can write a basic SELECT with JOIN from memory

**Assessment preparation:**
- [ ] Completed the IRA-style practice at [TCS ILP Preparation Guide](https://reportmedic.org/tools/tcs-ilp-preparation-guide.html)
- [ ] Attempted at least 10 Java output-prediction problems
- [ ] Written at least one complete application from requirements (not just exercises)

The Java ILP is intensive but entirely manageable for candidates who prepare deliberately. Every concept is learnable. Every assessment is passable. The difference between candidates who struggle and candidates who excel is almost entirely a function of how much code they wrote before and during ILP - not of innate talent or background.

Write code. Understand your errors. Ask specific questions. Build something complete. Those four practices, sustained for twelve weeks, will make you the kind of Java developer that TCS projects need from the first day you report to one.

---

## JavaScript Deep Dive: What ILP Actually Tests

The JavaScript component of Java ILP is often the section that surprises trainees. Many assume it is brief since they are in the "Java" stream, but web technologies including JavaScript carry enough IRA2 weight to deserve serious preparation.

### The Three JavaScript Questions That Appear in Almost Every IRA2

**Question Type 1: var vs let vs const scoping**

```javascript
for (var i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);
}
// Output: 3, 3, 3 (var is function-scoped; by the time callbacks fire, loop has finished)

for (let i = 0; i < 3; i++) {
    setTimeout(() => console.log(i), 100);
}
// Output: 0, 1, 2 (let is block-scoped; each iteration has its own i)
```

This specific difference between `var` and `let` in loop closures is one of the most tested JavaScript concepts in IRA2. The key: `var` has function scope (shared across all iterations), `let` has block scope (each iteration's `i` is independent).

**Question Type 2: Event Bubbling**

When you click a button inside a div inside the body, which event handlers fire and in what order?

**Bubbling (default):** The event starts at the target element (button) and bubbles up: button → div → body → document. By default, event listeners fire during bubbling.

**Capturing:** The event starts at the top and captures down: document → body → div → button. You opt into capturing by passing `true` as the third argument to `addEventListener`.

**`stopPropagation()`:** Stops the event from bubbling further up (or capturing further down).

IRA question format: "A click event fires on the innermost element. In what order do the event listeners on parent elements fire?" Answer: from innermost to outermost (bubbling order).

**Question Type 3: Asynchronous JavaScript**

```javascript
console.log("Start");

setTimeout(() => console.log("Timer"), 0);

Promise.resolve().then(() => console.log("Promise"));

console.log("End");
```

Output order: `Start` → `End` → `Promise` → `Timer`

Explanation: Synchronous code runs first (Start, End). The microtask queue (Promises) runs after synchronous code but before the macrotask queue (setTimeout). Even setTimeout with 0ms delay runs after Promise callbacks.

### DOM Manipulation Pattern

```javascript
// Adding a row to a table dynamically
function addStudentRow(student) {
    const table = document.getElementById("studentTable");
    const tbody = table.querySelector("tbody");

    const row = document.createElement("tr");

    const nameCell = document.createElement("td");
    nameCell.textContent = student.name;
    row.appendChild(nameCell);

    const gradeCell = document.createElement("td");
    gradeCell.textContent = student.grade;
    gradeCell.className = student.grade === "F" ? "fail" : "pass"; // conditional class
    row.appendChild(gradeCell);

    tbody.appendChild(row);
}
```

IRA Web Technologies questions sometimes show DOM manipulation code and ask which method adds a child element (appendChild), which removes an element (removeChild or element.remove()), or which method changes an element's text content (textContent vs innerHTML - textContent is safe, innerHTML parses HTML and carries XSS risk).

---

## JDBC: Transaction Management in Practice

Transaction management is an ILP topic where the gap between concept and implementation is significant. Many trainees understand that transactions exist but cannot implement them correctly.

### When Transactions Matter

Consider a bank transfer: debit Rs. 5,000 from Account A and credit Rs. 5,000 to Account B. If the debit succeeds but the application crashes before the credit, Account A loses Rs. 5,000 that Account B never receives. Transactions prevent this: either both operations complete or neither does.

### The JDBC Transaction Pattern

```java
Connection conn = null;
try {
    conn = DriverManager.getConnection(url, user, password);
    conn.setAutoCommit(false);  // start transaction (auto-commit is true by default)

    // Operation 1: Debit from source account
    PreparedStatement debit = conn.prepareStatement(
        "UPDATE accounts SET balance = balance - ? WHERE account_id = ?");
    debit.setDouble(1, 5000.0);
    debit.setInt(2, sourceAccountId);
    int debitRows = debit.executeUpdate();

    if (debitRows == 0) throw new RuntimeException("Source account not found");

    // Operation 2: Credit to destination account
    PreparedStatement credit = conn.prepareStatement(
        "UPDATE accounts SET balance = balance + ? WHERE account_id = ?");
    credit.setDouble(1, 5000.0);
    credit.setInt(2, destAccountId);
    int creditRows = credit.executeUpdate();

    if (creditRows == 0) throw new RuntimeException("Destination account not found");

    conn.commit();  // both operations succeeded - commit transaction
    System.out.println("Transfer successful");

} catch (Exception e) {
    if (conn != null) {
        try {
            conn.rollback();  // something failed - undo everything
            System.out.println("Transfer rolled back: " + e.getMessage());
        } catch (SQLException rollbackEx) {
            rollbackEx.printStackTrace();
        }
    }
} finally {
    if (conn != null) conn.close();
}
```

IRA question pattern: "Which method must be called before executing multiple SQL statements as a unit?" Answer: `setAutoCommit(false)`. "Which method saves the transaction permanently?" Answer: `commit()`. "Which method undoes all changes if an error occurs?" Answer: `rollback()`.

---

## Servlets: Session Management in Practice

Session management is tested conceptually in IRA2. Understanding what a session is and how to use HttpSession in code is required.

### Why Sessions Exist

HTTP is stateless - each request is independent. The server has no memory of previous requests from the same client. Sessions solve this: the server creates a session object and sends the client a session ID (usually in a cookie). On each subsequent request, the client sends this session ID, allowing the server to retrieve the corresponding session data.

### HttpSession Code Pattern

```java
@WebServlet("/login")
public class LoginServlet extends HttpServlet {

    @Override
    protected void doPost(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        String username = request.getParameter("username");
        String password = request.getParameter("password");

        if (authenticate(username, password)) {
            // Create or retrieve session
            HttpSession session = request.getSession(true); // true = create if not exists
            session.setAttribute("loggedInUser", username);
            session.setAttribute("loginTime", System.currentTimeMillis());
            session.setMaxInactiveInterval(30 * 60); // 30 minutes timeout

            response.sendRedirect("dashboard");
        } else {
            request.setAttribute("error", "Invalid credentials");
            request.getRequestDispatcher("login.jsp").forward(request, response);
        }
    }
}

@WebServlet("/dashboard")
public class DashboardServlet extends HttpServlet {

    @Override
    protected void doGet(HttpServletRequest request, HttpServletResponse response)
            throws ServletException, IOException {

        HttpSession session = request.getSession(false); // false = don't create, null if absent
        if (session == null || session.getAttribute("loggedInUser") == null) {
            response.sendRedirect("login"); // not logged in, redirect to login
            return;
        }

        String user = (String) session.getAttribute("loggedInUser");
        request.setAttribute("username", user);
        request.getRequestDispatcher("dashboard.jsp").forward(request, response);
    }
}
```

---

## Expanding Your Java Skills Beyond ILP

### Skills That ILP Introduces But Real Projects Demand More Of

**Design Patterns:** ILP introduces Spring's IoC, which embodies the Dependency Injection pattern. Real projects use: Singleton (one instance per application - Spring beans are singleton by default), Factory (creates objects without specifying the exact class), Strategy (defines a family of algorithms and makes them interchangeable), Observer (publish-subscribe pattern - Spring Events use this). Learning these patterns from a book or Refactoring.Guru while in ILP will make you significantly more effective in your first project.

**Spring Data JPA:** ILP covers JDBC for database access. Most modern TCS projects use Spring Data JPA, which eliminates most JDBC boilerplate. ILP exposes the underlying layer (JDBC) so you understand what JPA does for you. After ILP, investing time in Spring Data JPA (specifically, how to write `@Repository` interfaces and use derived query methods like `findByNameAndDepartment(String name, String dept)`) accelerates your project ramp-up.

**REST API design principles:** ILP teaches how to build REST APIs. Real projects require understanding proper REST design: when to use GET vs POST vs PUT vs PATCH vs DELETE, how to handle errors consistently (standardised error response format), how to version APIs, and how to document APIs with Swagger/OpenAPI.

**Docker basics:** Many TCS projects run applications in Docker containers. Understanding what Docker is (a container that packages an application with its dependencies, ensuring consistent behaviour across environments) and being able to run `docker build` and `docker run` commands makes you more effective from Day 1.

### What to Do in the Two Weeks After ILP, Before Project Posting

If you have a bench period between ILP completion and project allocation, invest it specifically:

**Day 1-5:** Build a complete Spring Boot application from scratch with full CRUD, database integration, proper exception handling, and at least 5 unit tests. No tutorial - requirements of your own design.

**Day 6-10:** Add authentication to that application using Spring Security (JWT-based). This is the most immediately practical skill gap between ILP and real projects.

**Day 11-14:** Set up your application to run in a Docker container. This involves writing a Dockerfile and running the containerised application locally. The skill gap in Docker between ILP and real projects is consistent and bridgeable in under two weeks.

These two weeks, used this way, compress months of early project learning into a pre-deployment investment.

---

## Closing: The Java Developer You Are Building Toward

Twelve weeks of Java ILP, approached seriously, does not make you an expert. It makes you a competent junior Java developer with exposure to the full stack of technologies that TCS enterprise projects use. That is exactly what is needed at this stage.

The expert part comes from the projects after ILP. Every complex bug you debug, every code review comment you incorporate, every design decision you make in a real system with real constraints deepens the foundation that ILP built. The training and the career compound together.

What ILP gives you is the vocabulary and the first principles. What you do with them in your first project is your first real contribution to TCS - and to the clients whose systems you will eventually help build, run, and improve.

Make the most of the twelve weeks. Write the code. Understand the errors. Build something complete. And arrive at your first project ready to contribute, not just to observe.
