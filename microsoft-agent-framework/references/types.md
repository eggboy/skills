# Types Reference

Content, Message, annotations, exceptions, settings, middleware, and context providers.

## Table of Contents

- [Content](#content)
- [Message](#message)
- [Annotations](#annotations)
- [Response Types](#response-types)
- [Exception Hierarchy](#exception-hierarchy)
- [Settings](#settings)
- [Middleware](#middleware)
- [Context and History Providers](#context-and-history-providers)
- [Sessions](#sessions)
- [TypeVar Naming](#typevar-naming)

## Content

All content uses a single `Content` class with classmethod constructors. Check types via `content.type` string.

### Creating Content

```python
from agent_framework import Content

text = Content.from_text("Hello world")
reasoning = Content.from_text_reasoning("Let me think about this...")
data = Content.from_data(data=b"binary", media_type="application/octet-stream")
uri = Content.from_uri(uri="https://example.com/image.png", media_type="image/png")
error = Content.from_error(message="Something went wrong")
hosted_file = Content.from_hosted_file(file_id="file-abc123")
vector_store = Content.from_hosted_vector_store(vector_store_id="vs-123")
usage = Content.from_usage(prompt_tokens=100, completion_tokens=50)
```

### Function Call Content

```python
func_call = Content.from_function_call(name="get_weather", arguments='{"city":"NYC"}', call_id="call-1")
func_result = Content.from_function_result(call_id="call-1", result="72°F sunny")
approval_req = Content.from_function_approval_request(name="delete_file", call_id="call-2")
approval_res = Content.from_function_approval_response(call_id="call-2", approved=True)
```

### MCP and Tool Content

```python
mcp_call = Content.from_mcp_server_tool_call(name="search", arguments={})
mcp_result = Content.from_mcp_server_tool_result(result="Found 5 results")
code_call = Content.from_code_interpreter_tool_call(code="print('hello')")
code_result = Content.from_code_interpreter_tool_result(output="hello")
img_call = Content.from_image_generation_tool_call(prompt="A sunset")
img_result = Content.from_image_generation_tool_result(image_url="https://...")
```

### Type Checking

Use `content.type` string — not `isinstance()`:

```python
for content in message.contents:
    if content.type == "text":
        print(content.text)
    elif content.type == "function_call":
        print(f"Calling {content.name}")
    elif content.type == "data":
        print(f"Binary data: {content.media_type}")
    elif content.type == "uri":
        print(f"URI: {content.uri}")
    elif content.type == "error":
        print(f"Error: {content.message}")
    elif content.type == "text_reasoning":
        print(f"Thinking: {content.text}")
```

---

## Message

Construct messages with `contents=[...]`. Strings in `contents` are auto-converted to text content:

```python
from agent_framework import Message

# Simple text message
message = Message(role="user", contents=["Hello"])

# Multi-content message
message = Message(role="user", contents=[
    Content.from_text("Describe this image:"),
    Content.from_uri(uri="https://example.com/photo.jpg", media_type="image/jpeg"),
])
```

### Roles

`Role` is a `NewType` wrapper over `str`. Use string literals directly:

```python
user_msg = Message(role="user", contents=["Hello"])
assistant_msg = Message(role="assistant", contents=["Hi there!"])
system_msg = Message(role="system", contents=["You are helpful."])
```

---

## Annotations

`Annotation` and `TextSpanRegion` are `TypedDict` definitions (create as dictionaries):

```python
from agent_framework import Annotation, TextSpanRegion

region: TextSpanRegion = {"start_index": 0, "end_index": 25}
citation: Annotation = {
    "type": "citation",
    "annotated_regions": [region],
    "url": "https://example.com/source",
    "title": "Source Title",
}
```

---

## Response Types

### ChatResponse and AgentResponse

Generic over response format type:

```python
from agent_framework import ChatResponse, AgentResponse
from pydantic import BaseModel

class MyOutput(BaseModel):
    name: str
    score: int

# Type parameter enables inference
response: AgentResponse[MyOutput] = await agent.run(
    "Query",
    options={"response_format": MyOutput},
)
result: MyOutput | None = response.value  # Type inferred
```

### Validation Errors

`response.value` raises `ValidationError` on schema validation failure (does not silently return `None`):

```python
from pydantic import ValidationError

try:
    result = response.value
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Response Updates

Construct response updates with `contents=` (not `text=`):

```python
from agent_framework import AgentResponseUpdate, Content

update = AgentResponseUpdate(
    contents=[Content.from_text("Processing...")],
    role="assistant",
)
```

### Helper Methods

```python
# Combine streaming updates into final response
final = ChatResponse.from_updates(updates)
final = ChatResponse.from_update_generator(async_generator)
final = AgentResponse.from_updates(updates)
```

### FinishReason

`FinishReason` is a `NewType` over `str`. Treat as a plain string:

```python
if response.finish_reason == "stop":
    print("Completed normally")
```

---

## Exception Hierarchy

```
AgentFrameworkException
├── AgentException
│   ├── AgentInvalidAuthException
│   ├── AgentInvalidRequestException
│   ├── AgentInvalidResponseException
│   └── AgentContentFilterException
├── ChatClientException
│   ├── ChatClientInvalidAuthException
│   ├── ChatClientInvalidRequestException
│   ├── ChatClientInvalidResponseException
│   └── ChatClientContentFilterException
├── IntegrationException
│   ├── IntegrationInitializationError
│   ├── IntegrationInvalidAuthException
│   ├── IntegrationInvalidRequestException
│   ├── IntegrationInvalidResponseException
│   └── IntegrationContentFilterException
├── ContentError
├── WorkflowException
│   ├── WorkflowRunnerException
│   ├── WorkflowValidationError
│   └── WorkflowActionError
├── ToolExecutionException
├── MiddlewareTermination
└── SettingNotFoundError
```

Init validation errors use built-in `ValueError`/`TypeError`.

### Usage

```python
from agent_framework.exceptions import (
    AgentFrameworkException,
    AgentException,
    AgentInvalidResponseException,
    ChatClientException,
    ToolExecutionException,
    WorkflowException,
)

try:
    result = await agent.run("Hello")
except AgentInvalidResponseException:
    ...  # Specific response error
except AgentException:
    ...  # Any agent error
except ChatClientException:
    ...  # Client-level error
except ToolExecutionException:
    ...  # Tool execution failure
except WorkflowException:
    ...  # Workflow error
except AgentFrameworkException:
    ...  # Catch-all
```

---

## Settings

Settings use `TypedDict` + `load_settings()` (not Pydantic Settings):

```python
from agent_framework import load_settings

settings = load_settings()
```

---

## Middleware

### Chat Middleware

Middleware runs per model call (including each tool-calling loop iteration). Use `call_next()` with no arguments:

```python
async def telemetry_middleware(context, call_next):
    start = time.time()
    response = await call_next()
    duration = time.time() - start
    print(f"Model call took {duration:.2f}s")
    return response

agent = Agent(
    client=client,
    name="agent",
    instructions="...",
    middleware=[telemetry_middleware],  # Must be a list
)
```

### Pipeline Order

```
FunctionInvocation → ChatMiddleware → ChatTelemetry → RawChatClient
```

Chat middleware runs per model call, not once per agent invocation. Ensure middleware is safe for repeated execution within a single tool-calling loop.

---

## Context and History Providers

### ContextProvider

```python
from agent_framework import Agent, ContextProvider

class MyContextProvider(ContextProvider):
    async def before_run(self, session_context):
        session_context.add_message(Message(role="system", contents=["Extra context"]))

    async def after_run(self, session_context, response):
        print(f"Response received: {response}")

agent = Agent(
    client=client,
    name="agent",
    instructions="...",
    context_provider=my_provider,  # Singular, only 1 allowed
)
```

### HistoryProvider

```python
from agent_framework import Agent, HistoryProvider

class MyHistoryProvider(HistoryProvider):
    ...

agent = Agent(
    client=client,
    name="agent",
    instructions="...",
    context_provider=MyHistoryProvider(),
    require_per_service_call_history_persistence=True,  # History per model call
)
```

### SessionContext Middleware Extension

Context providers can add middleware through `SessionContext`:

```python
class MiddlewareProvider(ContextProvider):
    async def before_run(self, session_context):
        session_context.extend_middleware([my_middleware])
```

---

## Sessions

```python
session = agent.create_session()
response = await agent.run("Hello", session=session)
```

---

## TypeVar Naming

TypeVars use suffix `T` convention:

```python
MessageT = TypeVar("MessageT")
ContentT = TypeVar("ContentT")
```

Not prefix `T`:

```python
# Old convention — do not use
TMessage = TypeVar("TMessage")
```
