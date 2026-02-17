# Code Quality

Naming conventions, common bug patterns, code smells, and code review checklist.

## Table of Contents

- [Naming Conventions](#naming-conventions)
- [Common Bug Patterns](#common-bug-patterns)
- [Common Code Smells](#common-code-smells)
- [Code Review Checklist](#code-review-checklist)

---

## Naming Conventions

Follow Google's Java style guide:
- **Classes/Interfaces**: `UpperCamelCase` (e.g., `UserService`, `PaymentRepository`)
- **Methods/Variables**: `lowerCamelCase` (e.g., `getUserById`, `totalAmount`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- **Packages**: `lowercase` (e.g., `com.example.service`)

Additional conventions:
- Use nouns for classes (`UserService`) and verbs for methods (`getUserById`)
- Avoid abbreviations and Hungarian notation
- Make names descriptive and self-documenting

---

## Common Bug Patterns

These map to static analysis rules (e.g., Sonar, SpotBugs, PMD) but can be applied manually:

- **Resource management**: Always close resources (files, sockets, streams). Use try-with-resources where possible so resources are closed automatically
- **Equality checks**: Compare object equality with `.equals()` or `Objects.equals(...)` rather than `==` for non-primitives; this avoids reference-equality bugs
- **Redundant casts**: Remove unnecessary casts; prefer correct generic typing and let the compiler infer types where possible
- **Reachable conditions**: Avoid conditional expressions that are always true or false; they indicate bugs or dead code and should be corrected

---

## Common Code Smells

These patterns indicate potential issues that should be addressed:

- **Parameter count**: Keep method parameter lists short. If a method needs many params, consider grouping into a value object or using the builder pattern
- **Method size**: Keep methods focused and small. Extract helper methods to improve readability and testability
- **Cognitive complexity**: Reduce nested conditionals and heavy branching by extracting methods, using polymorphism, or applying the Strategy pattern
- **Duplicated literals**: Extract repeated strings and numbers into named constants or enums to reduce errors and ease changes
- **Dead code**: Remove unused variables and assignments. They confuse readers and can hide bugs
- **Magic numbers**: Replace numeric literals with named constants that explain intent (e.g., `MAX_RETRIES`, `DEFAULT_PAGE_SIZE`)

---

## Code Review Checklist

### Modern Java Patterns

- [ ] Records used for DTOs and data-only classes (JDK 16+)
- [ ] Pattern matching used for instanceof and switch (JDK 16+)
- [ ] Text blocks used for multi-line strings (JDK 15+)
- [ ] Immutable collections with `List.of()`/`Map.of()` (JDK 9+)
- [ ] `Stream.toList()` instead of `collect(Collectors.toList())` where appropriate (JDK 16+)
- [ ] `var` used for local variables with clear types (JDK 10+)
- [ ] HTTP Client used instead of legacy HTTP APIs (JDK 11+)
- [ ] java.time API used instead of Date/Calendar (JDK 8+)
- [ ] Virtual threads considered for high-throughput I/O (JDK 21+)

### Best Practices

- [ ] Resources properly closed (try-with-resources)
- [ ] Object equality using `.equals()`, not `==`
- [ ] No magic numbers - extracted to named constants
- [ ] Methods focused and small (< 20 lines ideal)
- [ ] Exception handling follows unchecked exception strategy
- [ ] Validation at boundaries with `@Valid`
- [ ] Immutable objects and collections where appropriate
- [ ] No dead code or unused variables
- [ ] Appropriate JDK version features used for target version

### Exception Type Decision Tree

```
Is this a programming error (bug)?
├─ YES → IllegalArgumentException, IllegalStateException (unchecked)
└─ NO → Is this expected in normal business flow?
    ├─ YES → Use validation, Result<T>, or Optional<T>
    └─ NO → Custom unchecked exception (extends RuntimeException)
```
