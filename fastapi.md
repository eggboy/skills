---
description: FastAPI best practices and architectural patterns for production-ready applications
applyTo: '**/*.py'
---

# FastAPI Best Practices

These guidelines help you build maintainable, scalable, and production-ready FastAPI applications.

## OpenAPI Documentation

- FastAPI automatically generates OpenAPI documentation at `/docs`
- Use Pydantic field examples to enhance documentation
- Document custom exceptions manually using the `responses` parameter:

```python
@app.get("/animals/{animal_id}",
    responses={
        404: {
            "description": "Animal not found",
            "content": {
                "application/json": {
                    "example": {"message": "Animal not found"}
                }
            }
        }
    })
async def get_animal(animal_id: uuid.UUID) -> Animal:
    ...
```

## Asynchronous Code

### When to Use Async
- Use `async def` for I/O-bound operations: database queries, HTTP requests, file operations
- FastAPI supports both async and sync endpoints seamlessly
- The event loop runs on a single thread - avoid blocking operations

```python
@app.get("/animals/{animal_id}")
async def get_animal(animal_id: uuid.UUID):
    # Use with async libraries
    result = await database.fetch_one(query)
    return result

@app.post("/animals")
def create_animal(animal: Animal):
    # Sync endpoint - FastAPI handles it appropriately
    ...
```

### Important Warnings
- **Do not** use blocking libraries in async functions - they will freeze the entire event loop
- Only use `async/await` when working with async-compatible libraries
- Don't make everything async just because you can - use it when it provides real benefits

## Error Handling

### Global Exception Handlers
Define handlers at the FastAPI layer:

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(AnimalNotFoundError)
async def animal_not_found_exception_handler(
    request: Request,
    exc: AnimalNotFoundError
):
    return JSONResponse(
        status_code=404,
        content={"message": "Animal not found"},
    )

@app.exception_handler(AnimalAlreadyExistsError)
async def animal_already_exists_exception_handler(
    request: Request,
    exc: AnimalAlreadyExistsError
):
    return JSONResponse(
        status_code=409,
        content={"message": "Could not create the animal. It already exists"},
    )
```

### Document Exceptions
Add exception responses to OpenAPI documentation:

```python
@app.get("/animals/{animal_id}",
    responses={
        404: {
            "description": "Animal not found",
            "content": {
                "application/json": {
                    "example": {"message": "Animal not found"}
                }
            }
        }
    })
async def get_animal(animal_id: uuid.UUID) -> Animal:
    ...
```

## Additional Resources
- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Async Documentation](https://fastapi.tiangolo.com/async/)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OpenAPI Specification](https://www.openapis.org/)
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
