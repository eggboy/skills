# FastAPI Patterns

## Project Structure

Organize by feature using routers. Keep `main.py` thin.

```
src/
├── main.py              # App factory, middleware, lifespan
├── routers/
│   ├── animals.py       # Router per domain
│   └── users.py
├── models/
│   ├── animal.py        # Pydantic schemas
│   └── user.py
├── services/
│   └── animal_service.py
├── dependencies.py      # Shared dependencies
└── exceptions.py        # Custom exception classes
```

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routers import animals, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize DB pool, caches, etc.
    app.state.db = await create_db_pool()
    yield
    # Shutdown: cleanup
    await app.state.db.close()

app = FastAPI(lifespan=lifespan)
app.include_router(animals.router, prefix="/animals", tags=["animals"])
app.include_router(users.router, prefix="/users", tags=["users"])
```

## Pydantic Models

Separate input, output, and internal models. Use strict validation.

```python
from pydantic import BaseModel, Field, EmailStr
import uuid

# Input (creation)
class AnimalCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Luna"])
    species: str
    age: int = Field(..., ge=0)

# Output (response) — includes server-generated fields
class Animal(AnimalCreate):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Update (partial)
class AnimalUpdate(BaseModel):
    name: str | None = None
    species: str | None = None
    age: int | None = Field(None, ge=0)
```

## Dependency Injection

Use `Depends()` for shared logic: DB sessions, auth, pagination.

```python
from fastapi import Depends, Query
from typing import Annotated

async def get_db():
    async with async_session() as session:
        yield session

DbSession = Annotated[AsyncSession, Depends(get_db)]

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    user = await verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

# Pagination dependency
async def pagination(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    return {"skip": skip, "limit": limit}
```

```python
# Usage in router
@router.get("/", response_model=list[Animal])
async def list_animals(db: DbSession, user: CurrentUser, pages: dict = Depends(pagination)):
    return await db.execute(select(AnimalModel).offset(pages["skip"]).limit(pages["limit"]))
```

## Async vs Sync Endpoints

- Use `async def` with async libraries (asyncpg, httpx, aiofiles)
- Use `def` with blocking libraries (requests, psycopg2) — FastAPI runs them in a threadpool
- **Never** call blocking code inside `async def` — it freezes the event loop

```python
# CORRECT: async with async library
@router.get("/{animal_id}")
async def get_animal(animal_id: uuid.UUID, db: DbSession):
    result = await db.get(AnimalModel, animal_id)
    return result

# CORRECT: sync with blocking library
@router.post("/report")
def generate_report(data: ReportRequest):
    result = blocking_pdf_library.generate(data)  # runs in threadpool
    return FileResponse(result)

# WRONG: blocking call in async function
@router.get("/bad")
async def bad_endpoint():
    requests.get("https://api.example.com")  # FREEZES event loop
```

## Error Handling

Define custom exceptions and register global handlers. Document errors in OpenAPI.

```python
# exceptions.py
class AnimalNotFoundError(Exception):
    def __init__(self, animal_id: uuid.UUID):
        self.animal_id = animal_id

class AnimalAlreadyExistsError(Exception):
    pass

# main.py — register handlers
@app.exception_handler(AnimalNotFoundError)
async def handle_not_found(request: Request, exc: AnimalNotFoundError):
    return JSONResponse(status_code=404, content={"detail": f"Animal {exc.animal_id} not found"})

@app.exception_handler(AnimalAlreadyExistsError)
async def handle_conflict(request: Request, exc: AnimalAlreadyExistsError):
    return JSONResponse(status_code=409, content={"detail": "Animal already exists"})
```

```python
# Document in endpoint
@router.get("/{animal_id}",
    response_model=Animal,
    responses={404: {"description": "Animal not found", "content": {"application/json": {"example": {"detail": "Animal ... not found"}}}}},
)
async def get_animal(animal_id: uuid.UUID, db: DbSession) -> Animal:
    animal = await db.get(AnimalModel, animal_id)
    if not animal:
        raise AnimalNotFoundError(animal_id)
    return animal
```

## Middleware

```python
import time
from fastapi.middleware.cors import CORSMiddleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://frontend.example.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Process-Time"] = f"{time.perf_counter() - start:.4f}"
    return response
```

## Background Tasks

Use for fire-and-forget work (emails, logging). For heavy jobs, use a task queue (Celery, arq).

```python
from fastapi import BackgroundTasks

async def send_welcome_email(email: str):
    # async email sending
    ...

@router.post("/users", status_code=201)
async def create_user(user: UserCreate, bg: BackgroundTasks, db: DbSession):
    new_user = await create_user_in_db(db, user)
    bg.add_task(send_welcome_email, new_user.email)
    return new_user
```
