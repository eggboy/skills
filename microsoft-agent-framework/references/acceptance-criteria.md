# Acceptance Criteria

Correct import patterns, anti-patterns, and validation checklist for Agent Framework 1.0.0.

## Table of Contents

- [1. Correct Import Patterns](#1-correct-import-patterns)
- [2. Agent Construction](#2-agent-construction)
- [3. Content and Messages](#3-content-and-messages)
- [4. Tools](#4-tools)
- [5. Streaming](#5-streaming)
- [6. Options and Configuration](#6-options-and-configuration)
- [7. Workflows](#7-workflows)
- [8. Middleware](#8-middleware)
- [9. Common Anti-Patterns](#9-common-anti-patterns)

---

## 1. Correct Import Patterns

### ✅ CORRECT

```python
# Core types
from agent_framework import Agent, Message, Content, AgentResponse, AgentResponseUpdate

# Tools
from agent_framework import tool, FunctionTool, FunctionInvocationContext
from agent_framework.core import tool, FunctionTool

# MCP
from agent_framework import MCPStreamableHTTPTool

# OpenAPI
from agent_framework import OpenAPITool

# Workflows
from agent_framework import WorkflowBuilder, WorkflowEvent
from agent_framework.orchestrations import SequentialBuilder, GroupChatBuilder, HandoffBuilder, MagenticBuilder, ConcurrentBuilder

# Providers
from agent_framework.openai import OpenAIChatClient, OpenAIChatCompletionClient, OpenAIEmbeddingClient
from agent_framework.foundry import FoundryChatClient, FoundryAgent, FoundryLocalClient, FoundryEmbeddingClient
from agent_framework.anthropic import AnthropicClient

# Exceptions
from agent_framework.exceptions import AgentFrameworkException, AgentException, ChatClientException

# Azure credentials
from azure.identity import AzureCliCredential, DefaultAzureCredential
```

### ❌ INCORRECT — Removed/Renamed Types

```python
# WRONG — ChatAgent was renamed to Agent
from agent_framework import ChatAgent

# WRONG — ChatMessage was renamed to Message
from agent_framework import ChatMessage

# WRONG — AIFunction renamed to FunctionTool, @ai_function renamed to @tool
from agent_framework.core import ai_function, AIFunction

# WRONG — Old content types removed
from agent_framework.core import TextContent, DataContent, UriContent

# WRONG — Old event classes removed
from agent_framework import WorkflowOutputEvent, RequestInfoEvent, WorkflowStatusEvent

# WRONG — Old exception classes removed
from agent_framework.exceptions import ServiceException, ServiceResponseException

# WRONG — AzureAIAgentsProvider removed, use FoundryAgent
from agent_framework.azure import AzureAIAgentsProvider

# WRONG — AzureOpenAI wrappers removed
from agent_framework.azure import AzureOpenAIResponsesClient, AzureOpenAIChatClient

# WRONG — Old response types
from agent_framework import AgentRunResponse, AgentRunResponseUpdate

# WRONG — Old orchestration imports
from agent_framework import SequentialBuilder, GroupChatBuilder

# WRONG — GithubCopilotAgent (wrong casing)
from agent_framework_github_copilot import GithubCopilotAgent
```

---

## 2. Agent Construction

### ✅ CORRECT

```python
from agent_framework import Agent

agent = Agent(
    client=client,
    name="my-agent",
    instructions="You are a helpful assistant.",
    tools=[my_tool],
    middleware=[my_middleware],
)
```

### ❌ INCORRECT

```python
# WRONG — ChatAgent does not exist
agent = ChatAgent(chat_client=client, name="agent", instructions="...")

# WRONG — display_name was removed
agent = Agent(client=client, name="agent", display_name="My Agent", instructions="...")

# WRONG — context_providers (plural) was changed to context_provider (singular)
agent = Agent(client=client, name="agent", instructions="...", context_providers=[p1, p2])

# WRONG — middleware must be a list
agent = Agent(client=client, name="agent", instructions="...", middleware=single_middleware)
```

---

## 3. Content and Messages

### ✅ CORRECT

```python
from agent_framework import Content, Message

# Content creation via classmethods
text = Content.from_text("Hello")
data = Content.from_data(data=b"bytes", media_type="application/octet-stream")

# Type checking via .type string
if content.type == "text":
    print(content.text)

# Message construction with contents=
message = Message(role="user", contents=["Hello"])
```

### ❌ INCORRECT

```python
# WRONG — Old content class constructors
text = TextContent(text="Hello")

# WRONG — isinstance() for content type checking
if isinstance(content, TextContent):
    print(content.text)

# WRONG — text= parameter on Message
message = Message(role="user", text="Hello")
```

---

## 4. Tools

### ✅ CORRECT

```python
from agent_framework import tool

@tool
def my_function(param: str) -> str:
    """Does something."""
    return "result"

agent = Agent(client=client, name="agent", instructions="...", tools=[my_function])
```

### ❌ INCORRECT

```python
# WRONG — @ai_function renamed to @tool
from agent_framework.core import ai_function

@ai_function
def my_function(param: str) -> str:
    ...

# WRONG — Tool names as strings
agent = Agent(tools=["code_interpreter"])

# WRONG — MCPStreamableHTTPTool without context manager
mcp = MCPStreamableHTTPTool(name="MCP", url="https://...")
agent = Agent(tools=[mcp])  # Missing async with
```

---

## 5. Streaming

### ✅ CORRECT

```python
# Stream via run(stream=True)
stream = agent.run("Hello", stream=True)
async for update in stream:
    if update.text:
        print(update.text, end="", flush=True)
```

### ❌ INCORRECT

```python
# WRONG — run_stream() was replaced by run(stream=True)
async for update in agent.run_stream("Hello"):
    print(update)

# WRONG — sync iteration
for update in agent.run("Hello", stream=True):
    print(update)
```

---

## 6. Options and Configuration

### ✅ CORRECT

```python
# Options as TypedDict
response = await agent.run("Hello", options={"model": "gpt-4o", "temperature": 0.7})

# Model parameter
client = OpenAIChatClient(model="gpt-4o")

# Credential for Azure
client = OpenAIChatClient(model="gpt-4o", credential=AzureCliCredential(), azure_endpoint="...")
```

### ❌ INCORRECT

```python
# WRONG — model_id was renamed to model
client = OpenAIChatClient(model_id="gpt-4o")

# WRONG — Flat kwargs instead of options dict
response = await client.get_response("Hello", model_id="gpt-4", temperature=0.7)

# WRONG — deployment_name instead of model
client = OpenAIChatClient(deployment_name="gpt-4o")

# WRONG — ad_token_provider instead of credential
client = OpenAIChatClient(azure_ad_token_provider=token_provider)
```

---

## 7. Workflows

### ✅ CORRECT

```python
# Constructor parameters
workflow = SequentialBuilder(participants=[a, b]).build()

# WorkflowEvent type checking
if event.type == "output":
    print(event.data)

# State access (synchronous)
count = ctx.get_state("count")
ctx.set_state("count", count + 1)

# Orchestrations import path
from agent_framework.orchestrations import SequentialBuilder
```

### ❌ INCORRECT

```python
# WRONG — Fluent builder methods removed
workflow = SequentialBuilder().participants([a, b]).build()

# WRONG — isinstance for event type checking
if isinstance(event, WorkflowOutputEvent):
    ...

# WRONG — Async state access
count = await ctx.get_shared_state("count")
await ctx.set_shared_state("count", count + 1)

# WRONG — Old import path
from agent_framework import SequentialBuilder

# WRONG — send_responses removed
await workflow.send_responses_streaming(checkpoint_id=id, responses=[r])

# WRONG — SharedState
state = ctx.shared_state
```

---

## 8. Middleware

### ✅ CORRECT

```python
# call_next() with no arguments
async def my_middleware(context, call_next):
    response = await call_next()
    return response
```

### ❌ INCORRECT

```python
# WRONG — call_next with context argument
async def my_middleware(context, call_next):
    return await call_next(context)

# WRONG — parameter named 'next' instead of 'call_next'
async def my_middleware(context, next):
    return await next(context)
```

---

## 9. Common Anti-Patterns

| Anti-Pattern | Correct Approach |
|-------------|-----------------|
| `from agent_framework import ChatAgent` | `from agent_framework import Agent` |
| `from agent_framework import ChatMessage` | `from agent_framework import Message` |
| `Message(role="user", text="Hello")` | `Message(role="user", contents=["Hello"])` |
| `TextContent(text="Hello")` | `Content.from_text("Hello")` |
| `isinstance(content, TextContent)` | `content.type == "text"` |
| `isinstance(event, WorkflowOutputEvent)` | `event.type == "output"` |
| `@ai_function` | `@tool` |
| `AIFunction(fn)` | `FunctionTool(fn)` |
| `model_id="gpt-4o"` | `model="gpt-4o"` |
| `deployment_name="gpt-4o"` | `model="gpt-4o"` |
| `azure_ad_token_provider=...` | `credential=AzureCliCredential()` |
| `await call_next(context)` | `await call_next()` |
| `ctx.shared_state` | `ctx.state` |
| `await ctx.get_shared_state(k)` | `ctx.get_state(k)` |
| `from agent_framework import SequentialBuilder` | `from agent_framework.orchestrations import SequentialBuilder` |
| `agent.run_stream("Hello")` | `agent.run("Hello", stream=True)` |
| `display_name="My Agent"` | *(removed — use `name` only)* |
| `context_providers=[p1, p2]` | `context_provider=my_provider` |
| `AgentRunResponse` | `AgentResponse` |
| `AgentRunResponseUpdate` | `AgentResponseUpdate` |
| `GithubCopilotAgent` | `GitHubCopilotAgent` |
| `ServiceException` | `AgentFrameworkException` |
| `AzureAIAgentsProvider` | `FoundryAgent` |
| `AzureOpenAIChatClient` | `OpenAIChatCompletionClient` |
| `OpenAIResponsesClient` | `OpenAIChatClient` |
