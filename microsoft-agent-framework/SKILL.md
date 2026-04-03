---
name: microsoft-agent-framework
description: Build AI agents using the Microsoft Agent Framework Python SDK 1.0.0. Use when creating agents with OpenAI, Azure OpenAI, Foundry, or Anthropic providers. Covers Agent creation, function tools, workflows, orchestrations, streaming, structured outputs, MCP integration, middleware, and content types. Applies to agent-framework-core and provider packages.
---

# Microsoft Agent Framework Python SDK 1.0.0

Build AI agents with the Microsoft Agent Framework — a provider-agnostic Python SDK supporting OpenAI, Azure OpenAI, Microsoft Foundry, Anthropic, and local models.

## Architecture

```
User Query → Agent(client=<ChatClient>) → run() / run(stream=True)
                    ↓
              Tools: @tool functions | MCP | OpenAPI
                    ↓
              Workflows: Sequential | GroupChat | Handoff | Magentic | Custom
```

## Package Installation

| Scenario | Install command |
|----------|----------------|
| Everything (meta) | `pip install agent-framework` |
| Core only | `pip install agent-framework-core` |
| OpenAI / Azure OpenAI | `pip install agent-framework-openai` |
| Microsoft Foundry | `pip install agent-framework-foundry` |
| Foundry Local | `pip install agent-framework-foundry-local --pre` |

Beta connectors (`agent-framework-ag-ui`, `agent-framework-github-copilot`, `agent-framework-ollama`, etc.) still require `--pre`.

## Core Pattern

Every agent follows this skeleton — create a client, then an `Agent`:

```python
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

client = OpenAIChatClient(model="gpt-4o")
agent = Agent(client=client, name="assistant", instructions="You are a helpful assistant.")

response = await agent.run("Hello!")
print(response.value)
```

## Provider Selection

Select the client matching your backend. All clients produce a standard `Agent`.

**OpenAI (direct)**

```python
from agent_framework.openai import OpenAIChatClient

client = OpenAIChatClient(model="gpt-4o")
```

**Azure OpenAI**

```python
from agent_framework.openai import OpenAIChatClient
from azure.identity import AzureCliCredential

client = OpenAIChatClient(
    model="gpt-4o",
    azure_endpoint="https://your-resource.openai.azure.com",
    credential=AzureCliCredential(),
    api_version="2025-03-01-preview",
)
```

**Microsoft Foundry (project endpoint)**

```python
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

client = FoundryChatClient(
    project_endpoint="https://your-project.services.ai.azure.com",
    model="gpt-4o",
    credential=DefaultAzureCredential(),
)
```

**Foundry Service-Managed Agent**

```python
from agent_framework.foundry import FoundryAgent
from azure.identity import DefaultAzureCredential

agent = FoundryAgent(
    project_endpoint="https://your-project.services.ai.azure.com",
    credential=DefaultAzureCredential(),
    agent_name="my-agent",
)
```

**Foundry Local**

```python
from agent_framework.foundry import FoundryLocalClient

client = FoundryLocalClient(model="phi-4-mini")
```

**Anthropic**

```python
from agent_framework.anthropic import AnthropicClient

client = AnthropicClient(model="claude-sonnet-4-5-20250929")
```

See [references/providers.md](references/providers.md) for embeddings, environment variables, and advanced provider configuration.

## Function Tools

Decorate Python functions with `@tool`. Use `Annotated` + `Field` for parameter descriptions:

```python
from typing import Annotated
from pydantic import Field
from agent_framework import Agent, tool

@tool
def get_weather(
    city: Annotated[str, Field(description="City name")],
) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: 72°F, sunny"

agent = Agent(
    client=client,
    name="weather-bot",
    instructions="You help with weather queries.",
    tools=[get_weather],
)
```

For runtime data injection, use `FunctionInvocationContext`:

```python
from agent_framework import FunctionInvocationContext, tool

@tool
def send_email(address: str, ctx: FunctionInvocationContext) -> str:
    user_id = ctx.kwargs["user_id"]
    return f"Queued email for {user_id}"

response = await agent.run(
    "Send update to finance@example.com",
    session=agent.create_session(),
    function_invocation_kwargs={"user_id": "user-123"},
)
```

See [references/tools.md](references/tools.md) for MCP tools, OpenAPI tools, and hosted Foundry tools.

## Streaming

Pass `stream=True` to `run()` to get a `ResponseStream`:

```python
stream = agent.run("Tell me a story", stream=True)
async for update in stream:
    if update.text:
        print(update.text, end="", flush=True)
```

## Structured Outputs

Pass a Pydantic model or JSON schema to `response_format`:

```python
from pydantic import BaseModel, ConfigDict

class MovieReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    rating: float
    summary: str

response = await agent.run(
    "Review Inception",
    options={"response_format": MovieReview},
)
movie = response.value  # Typed as MovieReview
```

## Options (TypedDict)

Pass runtime options as a dictionary:

```python
response = await agent.run(
    "Hello!",
    options={
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1000,
    },
)
```

## Content Types

All content uses a single `Content` class with classmethod constructors:

```python
from agent_framework import Content, Message

text = Content.from_text("Hello world")
image = Content.from_uri(uri="https://example.com/img.png", media_type="image/png")
data = Content.from_data(data=b"binary", media_type="application/octet-stream")

message = Message(role="user", contents=["Hello"])  # Strings auto-convert to text content
```

Check content type via `content.type` string (not `isinstance()`):

```python
if content.type == "text":
    print(content.text)
elif content.type == "function_call":
    print(content.name)
```

## Middleware

Define middleware with `call_next` continuation (no arguments to `call_next()`):

```python
async def logging_middleware(context, call_next):
    print(f"Request: {context.messages}")
    response = await call_next()
    print(f"Response: {response}")
    return response

agent = Agent(
    client=client,
    name="agent",
    instructions="...",
    middleware=[logging_middleware],  # Must be a list
)
```

## Workflows

Build multi-agent orchestrations with constructor-parameter builders:

```python
from agent_framework.orchestrations import SequentialBuilder

workflow = SequentialBuilder(participants=[agent_a, agent_b]).build()
result = await workflow.run("Draft and review a report")
```

See [references/workflows.md](references/workflows.md) for GroupChat, Handoff, Magentic, custom WorkflowBuilder, events, and state.

## Exception Handling

```python
from agent_framework.exceptions import (
    AgentFrameworkException,
    AgentException,
    AgentInvalidResponseException,
)

try:
    result = await agent.run("Hello")
except AgentInvalidResponseException:
    print("Invalid response from model")
except AgentException:
    print("Agent-level error")
except AgentFrameworkException:
    print("Any framework error")
```

## Key Conventions

- Use `model` parameter everywhere (not `model_id` or `deployment_name`)
- Use `credential=` for Azure auth (not `ad_token` or `ad_token_provider`)
- Import providers from their namespace: `agent_framework.openai`, `agent_framework.foundry`
- Content, WorkflowEvent use `type` string discriminator (not `isinstance()`)
- Middleware uses `call_next()` with no arguments
- State access is synchronous: `ctx.get_state("key")`, `ctx.set_state("key", value)`
- `Message` construction uses `contents=[...]` (not `text=...`)
- Orchestration builders use constructor parameters (not fluent methods)

## Reference Files

- [references/providers.md](references/providers.md) — Client types, embeddings, environment variables, Azure OpenAI migration
- [references/tools.md](references/tools.md) — Function tools, MCP integration, OpenAPI tools, Foundry hosted tools
- [references/workflows.md](references/workflows.md) — Orchestration builders, WorkflowEvent, state, declarative workflows
- [references/types.md](references/types.md) — Content, Message, annotations, exceptions, settings, middleware patterns
- [references/acceptance-criteria.md](references/acceptance-criteria.md) — Correct import patterns, anti-patterns, validation checklist
