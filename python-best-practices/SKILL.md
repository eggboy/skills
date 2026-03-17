---
name: python-best-practices
description: >
  Python coding best practices, conventions, and architectural patterns for production-ready applications.
  Use when writing, reviewing, or refactoring Python code to apply modern patterns and idiomatic style.
  Covers: general Python conventions (PEP 8, type hints, testing with pytest/hypothesis/Faker),
  dataframe mindset (vectorization, columnar operations, method chaining across Pandas/Polars/DuckDB/Spark),
  and Python data model (dunder methods, iterators, context managers, descriptors, properties).
  Applicable to Python 3.12+ projects using pyproject.toml and Ruff for linting.
  USE FOR: Python style, PEP 8, type hints, testing, dataframes, Python data model.
  DO NOT USE FOR: FastAPI applications (use fastapi skill).
---

# Python Best Practices

## Domain-Specific References

Load the relevant reference when the task involves these domains:

- **FastAPI applications**: Defer to the `fastapi` skill for project setup, endpoints, error handling, and Pydantic integration
- **Dataframe / data engineering**: Read [references/dataframe.md](references/dataframe.md) — columnar thinking, vectorization over row loops, method chaining, Pandas → Polars → DuckDB → Spark
- **Python data model**: Read [references/datamodel.md](references/datamodel.md) — `__iter__`/`__next__`, `__enter__`/`__exit__`, descriptors, `@property`, native-feeling APIs

## Code Style

- Python 3.12+ with pyproject.toml configuration
- Follow PEP 8; use Ruff for linting and formatting
- 4 spaces indentation, 120-char line limit
- Type hints required for all public APIs using built-in generics (`list[str]`, `dict[str, int]`), not `typing.List`/`typing.Dict`
- Provide PEP 257 docstrings for all public functions and classes
- Break complex functions into smaller, well-named functions

### Naming Conventions

```python
# Files: snake_case
mcp_server.py

# Classes: PascalCase
class CustomerQueryTool:

# Functions/variables: snake_case
async def analyze_customer_query():
server_config = get_config()

# Constants: SCREAMING_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
```

## Project Structure

Use this layout for new Python projects:

```
project-name/
├── pyproject.toml          # Project metadata, dependencies, tool config
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── main.py
│       └── models.py
├── tests/
│   ├── conftest.py         # Shared fixtures
│   └── test_main.py
└── README.md
```

- Use `src/` layout to prevent accidental imports of uninstalled code
- Configure all tools (ruff, pytest, mypy) in `pyproject.toml`
- Prefer `uv` for dependency management; fall back to `pip`

## Testing

- Use pytest with `conftest.py` for shared fixtures
- Use `@pytest.mark.parametrize` for input variation
- Use `Faker()` for generating realistic test data
- Use `hypothesis` for property-based testing of pure functions
- Use `schemathesis` for property-based testing of API endpoints
- Use `pytest-snapshot` for snapshot testing API responses
- Measure coverage with `pytest-cov`; write tests for uncovered paths
- Handle edge cases: empty inputs, invalid types, boundary values, large datasets

```python
# Example: parametrized test with fixture
@pytest.fixture
def sample_user(faker):
    return {"name": faker.name(), "email": faker.email()}

@pytest.mark.parametrize("quantity,expected", [(0, 0), (5, 50), (-1, ValueError)])
def test_calculate_total(quantity, expected):
    if isinstance(expected, type) and issubclass(expected, Exception):
        with pytest.raises(expected):
            calculate_total(price=10, quantity=quantity)
    else:
        assert calculate_total(price=10, quantity=quantity) == expected
```

## Error Handling

- Prefer specific exceptions over generic `Exception`
- Use custom exception classes for domain errors
- Document raised exceptions in docstrings
- Handle cleanup with context managers (`with`), not bare `try/finally`
