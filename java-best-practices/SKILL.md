---
name: java-best-practices
description: Expert guidance on modern Java patterns (JDK 8-24) and industry best practices. Use when writing, reviewing, or refactoring Java code to apply modern language features, APIs, and architectural patterns. Covers type inference (var), Records, sealed classes, pattern matching, switch expressions, text blocks, Streams, virtual threads, structured concurrency, modern collections APIs, I/O improvements, security enhancements, DTO design, exception handling strategies (unchecked exceptions, validation-first approach, global handlers), naming conventions, code smells, and build verification. Essential for modernizing legacy Java code, Spring Boot applications, REST APIs, and enterprise Java development.
---

# Java Best Practices

Expert reference for modern Java development from JDK 8 through JDK 24, combining 90+ modern language patterns with architectural best practices for enterprise applications.

## Quick Start

### Modern Java Patterns from JDK 8-24

```java
// Use Records for DTOs (JDK 16+)
public record UserDTO(Long id, String name, String email) {}

// Pattern matching for instanceof (JDK 16+)
if (obj instanceof String s) {
    return s.toUpperCase();
}

// Type inference with var (JDK 10+)
var users = userRepository.findAll(); // Type is clear from context

// Immutable collections (JDK 9+)
var statuses = List.of("ACTIVE", "PENDING", "CLOSED");

// Streams and method references (JDK 8+)
users.stream()
    .map(User::getName)
    .toList(); // JDK 16+ alternative to .collect(Collectors.toList())

// Null handling with Optional (JDK 8+)
Optional<User> user = userRepository.findById(id);
return user.orElseThrow(() -> new UserNotFoundException(id));

// Text blocks for multi-line strings (JDK 15+)
var json = """
    {
        "name": "%s",
        "status": "ACTIVE"
    }
    """.formatted(userName);

// Virtual threads for high-throughput I/O (JDK 21+)
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    executor.submit(() -> processRequest(request));
}
```

### Exception Handling Strategy

```java
// ✅ GOOD: Unchecked custom exceptions
public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException(Long id) {
        super("User not found with id: " + id);
    }
}

// ✅ GOOD: Validate at the boundary
@PostMapping("/users")
public User createUser(@Valid @RequestBody UserRequest request) {
    return userService.create(request);
}
```

## Core Principles

### 1. Favor Modern Java Features (JDK 8-24)
- Use Records for data-only classes, pattern matching for type checks, `var` for clear local types
- Prefer immutable collections (`List.of()`, `Map.of()`, `Stream.toList()`)
- Use Streams API and method references for collection processing
- Adopt virtual threads for high-throughput I/O (JDK 21+)
- Use text blocks for multi-line strings, modern APIs (HTTP Client, java.time, Files)

### 2. Validate First, Catch Never
- Prevent bad data at the boundary using `@Valid` and validation annotations
- Don't catch exceptions that validation should prevent
- Make illegal states unrepresentable
- Use Records and sealed types to enforce constraints

### 3. Use Unchecked Exceptions
- Default to `RuntimeException` for custom exceptions
- Avoid checked exceptions - they create maintenance burden
- Wrap checked exceptions from libraries when necessary
- Use exception chaining to preserve stack traces

### 4. Centralize Exception Handling
- Use `@ControllerAdvice` for global exception handling
- Build a custom exception hierarchy that's self-explanatory
- Never use empty catch blocks or generic `catch (Exception e)`
- Leverage helpful NullPointerExceptions (JDK 14+)

### 5. Result Objects for Expected Cases
- Use `Optional<T>` or `Result<T>` for expected absence/failure
- Reserve exceptions for truly exceptional conditions
- "User not found" is a normal outcome, not an exception
- Use Optional chaining methods (orElseThrow, or, ifPresentOrElse)

### 6. Know Your JDK Version
- Check pattern references for minimum JDK version requirements
- Target LTS versions: JDK 8, 11, 17, 21
- Use preview features cautiously (require --enable-preview flag)
- Plan migrations: Java 8 → 17, Java 11 → 21

## Reference Routing

Match the user's request to the appropriate reference file:

| Domain | Triggers | Reference |
|---|---|---|
| Language features | Records, pattern matching, var, sealed classes, switch expressions, text blocks | [language.md](references/language.md) (18 patterns) |
| Collections | List.of, Map.of, immutability, sequenced collections | [collections.md](references/collections.md) (9 patterns) |
| Streams/Optional | Collection processing, null safety, Predicate.not, gatherers | [streams.md](references/streams.md) (11 patterns) |
| Concurrency | Virtual threads, async, structured concurrency, scoped values | [concurrency.md](references/concurrency.md) (10 patterns) |
| I/O/Networking | HTTP client, files, Path.of, try-with-resources | [io.md](references/io.md) (9 patterns) |
| Strings | Text blocks, formatting, isBlank, strip, repeat | [strings.md](references/strings.md) (8 patterns) |
| Error handling | Exceptions, Optional, NPE, multi-catch | [errors.md](references/errors.md) (7 patterns) |
| Date/time | Temporal operations, Duration, formatting | [datetime.md](references/datetime.md) (6 patterns) |
| Security | Crypto, random, TLS, PEM | [security.md](references/security.md) (5 patterns) |
| Tooling | Execution, profiling, jshell, JFR | [tooling.md](references/tooling.md) (7 patterns) |
| DTOs/APIs | REST request/response design | [dto-patterns.md](references/dto-patterns.md) |
| Exception strategy | Exception hierarchies, @ControllerAdvice, Result objects | [exception-handling.md](references/exception-handling.md) |
| Code quality | Naming, bug patterns, code smells, review checklist | [code-quality.md](references/code-quality.md) |

Each pattern reference shows old vs. modern approach with minimum JDK version. Always note the JDK version requirement when suggesting modern features.

### JDK Version Quick Reference

- **JDK 8**: Streams, Lambdas, Optional, java.time
- **JDK 9**: Immutable collections (List.of, Map.of)
- **JDK 10**: Type inference (var)
- **JDK 11**: HTTP Client, Files.readString/writeString
- **JDK 14**: Helpful NullPointerExceptions, switch expressions
- **JDK 15**: Text blocks
- **JDK 16**: Pattern matching for instanceof, Records, Stream.toList()
- **JDK 17**: Sealed classes (stable), RandomGenerator, HexFormat
- **JDK 21**: Virtual threads, structured concurrency, sequenced collections, Math.clamp()
- **JDK 24**: Multi-file source programs, stable values, gatherers

## Build Verification

After modifying code, verify the build: `mvn clean install` (Maven) or `./gradlew build` (Gradle).
