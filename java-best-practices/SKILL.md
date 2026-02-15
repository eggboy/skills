---
name: java-best-practices
description: Expert guidance for modern Java development following industry best practices. Use when writing, reviewing, or refactoring Java code. Covers modern Java patterns (Records, Streams, pattern matching), DTO design with interface-based patterns, exception handling strategies (unchecked exceptions, validation-first approach, global handlers), naming conventions, code smells, and build verification. Essential for Spring Boot applications, REST APIs, and enterprise Java development.
---

# Java Best Practices

This skill provides comprehensive guidance for writing modern, maintainable Java code following industry best practices.

## When to Use This Skill

Use this skill when:
- Writing new Java code
- Reviewing or refactoring existing Java code
- Designing DTOs for REST APIs
- Implementing exception handling strategies
- Working with Spring Boot applications
- Addressing code smells or technical debt

## Quick Start

### Modern Java Patterns

```java
// Use Records for DTOs
public record UserDTO(Long id, String name, String email) {}

// Pattern matching for instanceof
if (obj instanceof String s) {
    return s.toUpperCase();
}

// Type inference with var
var users = userRepository.findAll(); // Type is clear from context

// Immutable collections
var statuses = List.of("ACTIVE", "PENDING", "CLOSED");
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

## Detailed Guides

This skill includes comprehensive reference documentation:

### Core Development Guidelines

See [references/java.instructions.md](references/java.instructions.md) for:
- General development instructions
- Modern Java features (Records, Pattern Matching, Streams)
- Naming conventions
- Common bug patterns and code smells
- Build and verification procedures

**When to read:** For general Java coding standards and best practices.

### DTO Design Patterns

See [references/dto-patterns.md](references/dto-patterns.md) for:
- Interface-based DTO pattern
- Organizing DTOs by controller
- Reusable validation and documentation
- Type-safe DTO utilities

**When to read:** When designing REST API request/response objects or refactoring DTOs.

### Exception Handling

See [references/exception-handling.md](references/exception-handling.md) for:
- Unchecked vs checked exceptions (prefer unchecked)
- Four exception handling patterns senior developers use
- Custom exception hierarchies
- Global exception handling with @ControllerAdvice
- Result objects for expected failures
- Complete decision tree for exception strategy

**When to read:** When implementing error handling, designing exception hierarchies, or addressing exception-related code smells.

## Core Principles

### 1. Favor Modern Java Features
- Use Records for data-only classes
- Leverage pattern matching and type inference
- Prefer immutable objects and collections
- Use Streams API for collection processing

### 2. Validate First, Catch Never
- Prevent bad data at the boundary using `@Valid` and validation annotations
- Don't catch exceptions that validation should prevent
- Make illegal states unrepresentable

### 3. Use Unchecked Exceptions
- Default to `RuntimeException` for custom exceptions
- Avoid checked exceptions - they create maintenance burden
- Wrap checked exceptions from libraries when necessary
- Use exception chaining to preserve stack traces

### 4. Centralize Exception Handling
- Use `@ControllerAdvice` for global exception handling
- Build a custom exception hierarchy that's self-explanatory
- Never use empty catch blocks or generic `catch (Exception e)`

### 5. Result Objects for Expected Cases
- Use `Optional<T>` or `Result<T>` for expected absence/failure
- Reserve exceptions for truly exceptional conditions
- "User not found" is a normal outcome, not an exception

## Quick Reference

### When to Use Each Exception Type

```
Is this a programming error (bug)?
├─ YES → IllegalArgumentException, IllegalStateException (unchecked)
└─ NO → Is this expected in normal business flow?
    ├─ YES → Use validation, Result<T>, or Optional<T>
    └─ NO → Custom unchecked exception (extends RuntimeException)
```

### Naming Conventions
- Classes/Interfaces: `UpperCamelCase` (e.g., `UserService`)
- Methods/Variables: `lowerCamelCase` (e.g., `getUserById`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`)
- Packages: `lowercase` (e.g., `com.example.service`)

### Common Code Smells to Address
- Resource leaks (use try-with-resources)
- Equality checks with `==` instead of `.equals()`
- High parameter count (use builder pattern or value objects)
- Long methods (extract smaller methods)
- Deep nesting (reduce cognitive complexity)
- Magic numbers (extract to named constants)

## Build Verification

After making changes:
- **Maven**: `mvn clean install`
- **Gradle**: `./gradlew build`
- Ensure all tests pass

## Integration with Tools

This guidance complements static analysis tools:
- **SonarLint/Sonar**: Direct connections preferred
- **SpotBugs/PMD**: Use for additional checks
- **IDE warnings**: Address proactively during development

The principles in this skill are tool-agnostic and can be applied manually or with any static analyzer.
