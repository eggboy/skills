---
description: 'Python coding conventions and guidelines'
applyTo: '**/*.py'
---

# Python Coding Instructions

## General Instructions

- Implement requests thoroughly and adhere strictly to the requirements.
- Plan solutions carefully before writing any code.
- Always prioritize readability and clarity.
- For algorithm-related code, include explanations of the approach used.
- Write code with good maintainability practices, including comments on why certain design decisions were made.
- Handle edge cases and write clear exception handling.
- For libraries or external dependencies, mention their usage and purpose in comments.
- Use consistent naming conventions and follow language-specific best practices.
- Write concise, efficient, and idiomatic code that is also easily understandable.

## Python Instructions

- Write clear and concise comments for each function.
- Ensure functions have descriptive names and include type hints.
- Provide docstrings following PEP 257 conventions.
- Use the `typing` module for type annotations (e.g., `List[str]`, `Dict[str, int]`).
- Break down complex functions into smaller, more manageable functions.

## Edge Cases and Testing

- Always include test cases for critical paths of the application.
- Account for common edge cases like empty inputs, invalid data types, and large datasets.
- Include comments for edge cases and the expected behavior in those cases.
- Write unit tests for functions and document them with docstrings explaining the test cases.

## Package Management
- ONLY use uv, NEVER pip
- Installation: `uv add <package>`
- Running tools: `uv run <tool>`
- Upgrading: `uv lock --upgrade-package <package>`
- FORBIDDEN: `uv pip install`, `@latest` syntax

## Code Style and Formatting

- Python 3.12+ with pyproject.toml configuration
- Follow the **PEP 8** style guide for Python.
- Maintain proper indentation (use 4 spaces for each level of indentation).
- Ensure lines do not exceed 120 characters.
- Ruff for linting
- Place function and class docstrings immediately after the `def` or `class` keyword.
- Use blank lines to separate functions, classes, and code blocks where appropriate.
- Type hints required for all public APIs

### Naming Conventions**
```python
# Files: snake_case
mcp_server.py
customer_analysis.py

# Classes: PascalCase
class CustomerQueryTool:
class ItineraryPlanningServer:

# Functions/variables: snake_case
async def analyze_customer_query():
server_config = get_config()

# Constants: SCREAMING_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_PORT = 3000
```

## Exception Handling
- Use `logger.exception()` not `logger.error()` when catching exceptions
- Catch specific exceptions:
  - File ops: `except (OSError, PermissionError):`
  - JSON: `except json.JSONDecodeError:`
  - Network: `except (ConnectionError, TimeoutError):`
- FORBIDDEN: bare `except Exception:` unless in top-level handlers

## Writing Tests
- Use pytest framework
- Extract the common setup into a pytest fixture
- Use parametrized tests for parameter variation and fixtures for commonly used test data using pytest.mark.parametrize
- Use Faker() for generating realistic test data
- Use snapshot testing with pytest-snapshot to capture the output from API endpoints, so that changes can be detected easily and effectively asserting on every field
- Use coverage to measure test coverage and write tests for any uncovered code paths
- Use hypothesis for property-based testing of complex functions and schemathesis for property-based testing of API endpoints
