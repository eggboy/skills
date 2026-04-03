# Tools Reference

Function tools, MCP integration, OpenAPI tools, and Foundry hosted tools.

## Table of Contents

- [Function Tools (@tool)](#function-tools-tool)
- [FunctionInvocationContext](#functioninvocationcontext)
- [FunctionTool Class](#functiontool-class)
- [MCP Integration](#mcp-integration)
- [OpenAPI Tools](#openapi-tools)
- [Foundry Hosted Tools](#foundry-hosted-tools)
- [Combining Multiple Tools](#combining-multiple-tools)

## Function Tools (@tool)

Decorate Python functions with `@tool`. The decorator converts functions into `FunctionTool` instances automatically.

### Basic Tool

```python
from agent_framework import Agent, tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"Weather in {city}: 72°F, sunny"

agent = Agent(
    client=client,
    name="weather-bot",
    instructions="You help with weather queries.",
    tools=[get_weather],
)
```

### Rich Parameter Descriptions

Use `Annotated` + `Field` for parameter descriptions visible to the model:

```python
from typing import Annotated
from pydantic import Field
from agent_framework import tool

@tool
def search_products(
    query: Annotated[str, Field(description="Search terms")],
    category: Annotated[str, Field(description="Product category")] = "all",
    max_results: Annotated[int, Field(description="Maximum results to return")] = 10,
) -> str:
    """Search the product catalog."""
    return f"Found {max_results} results for '{query}' in {category}"
```

### Async Tools

```python
from agent_framework import tool

@tool
async def fetch_data(url: str) -> str:
    """Fetch data from a URL."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

---

## FunctionInvocationContext

Access runtime data, session state, and kwargs within tools:

```python
from agent_framework import Agent, FunctionInvocationContext, tool

@tool
def process_order(item: str, ctx: FunctionInvocationContext) -> str:
    """Process a customer order."""
    user_id = ctx.kwargs["user_id"]
    session_id = ctx.session.session_id if ctx.session else "no-session"
    return f"Order for {item} by {user_id} in session {session_id}"

response = await agent.run(
    "Order a laptop",
    session=agent.create_session(),
    function_invocation_kwargs={"user_id": "user-123", "request_id": "req-789"},
)
```

The `ctx` parameter:
- Can be named `ctx`, `context`, or any name annotated as `FunctionInvocationContext`
- Is NOT exposed in the schema the model sees
- Provides access to `ctx.kwargs`, `ctx.session`, and runtime state

### Explicit Kwargs Buckets

Runtime kwargs are split by purpose:

```python
response = await agent.run(
    "Process this request",
    session=agent.create_session(),
    function_invocation_kwargs={"user_id": "user-123"},  # For tools/function middleware
    client_kwargs={"custom_header": "value"},  # For client-layer middleware
)
```

### Sub-Agent as Tool with Session Propagation

```python
child_agent = Agent(client=client, name="child", instructions="...")
parent_agent = Agent(
    client=client,
    name="parent",
    instructions="...",
    tools=[child_agent.as_tool(propagate_session=True)],
)
```

---

## FunctionTool Class

Use `FunctionTool` directly when you need explicit control:

```python
from agent_framework.core import FunctionTool

func = FunctionTool(get_weather)
agent = Agent(client=client, name="agent", instructions="...", tools=[func])
```

---

## MCP Integration

### MCPStreamableHTTPTool (Client-Managed)

You manage the MCP connection lifecycle. Requires async context manager:

```python
from agent_framework import Agent, MCPStreamableHTTPTool

async with MCPStreamableHTTPTool(
    name="Docs MCP",
    url="https://learn.microsoft.com/api/mcp",
) as mcp_tool:
    agent = Agent(
        client=client,
        name="docs-agent",
        instructions="Answer questions using docs.",
        tools=[mcp_tool],
    )
    response = await agent.run("How do I use Azure Functions?")
```

### MCPStreamableHTTPTool with Authentication

```python
from httpx import AsyncClient
from agent_framework import MCPStreamableHTTPTool

http_client = AsyncClient(
    headers={"Authorization": f"Bearer {api_key}"},
    timeout=30.0,
)

async with MCPStreamableHTTPTool(
    name="Private MCP",
    url="https://my-mcp-server.example.com/mcp",
    http_client=http_client,
) as mcp_tool:
    agent = Agent(client=client, name="agent", instructions="...", tools=[mcp_tool])
```

### Multiple MCP Servers

```python
async with (
    MCPStreamableHTTPTool(name="Docs", url="https://docs-mcp.example.com/mcp") as docs_mcp,
    MCPStreamableHTTPTool(name="GitHub", url="https://api.github.com/mcp", http_client=auth_client) as github_mcp,
):
    agent = Agent(
        client=client,
        name="multi-mcp-agent",
        instructions="Search docs and interact with GitHub.",
        tools=[docs_mcp, github_mcp],
    )
```

### Agent as MCP Server

Expose an agent as an MCP server:

```python
mcp_server = agent.as_mcp_server()
```

Requires `mcp` package. For WebSocket support: `pip install mcp[ws] --pre`.

---

## OpenAPI Tools

Integrate external REST APIs via OpenAPI specifications:

```python
from agent_framework import Agent, OpenAPITool

openapi_tool = OpenAPITool(
    name="WeatherAPI",
    spec="https://api.weather.example.com/openapi.json",
    base_url="https://api.weather.example.com",
)

agent = Agent(
    client=client,
    name="api-agent",
    instructions="Use the weather API to answer questions.",
    tools=[openapi_tool],
)
```

### With Authentication

```python
openapi_tool = OpenAPITool(
    name="SecureAPI",
    spec=openapi_spec_dict,
    base_url="https://api.example.com",
    headers={"Authorization": "Bearer your-api-key"},
)
```

---

## Foundry Hosted Tools

When using `FoundryAgent`, hosted tools are available through the Foundry service. These are configured on the service side rather than in code. Configure tools in Azure AI Foundry portal and reference them by the agent name/version.

For code interpreter, file search, and web search through Foundry, configure the agent in the Foundry portal and use `FoundryAgent` to invoke it.

---

## Combining Multiple Tools

Mix function tools, MCP tools, and OpenAPI tools:

```python
from agent_framework import Agent, MCPStreamableHTTPTool, OpenAPITool, tool

@tool
def get_current_date() -> str:
    """Get today's date."""
    from datetime import date
    return date.today().isoformat()

async with MCPStreamableHTTPTool(
    name="Docs MCP",
    url="https://learn.microsoft.com/api/mcp",
) as docs_mcp:
    agent = Agent(
        client=client,
        name="super-agent",
        instructions="You have multiple capabilities.",
        tools=[
            get_current_date,
            docs_mcp,
            OpenAPITool(name="API", spec=spec, base_url=base_url),
        ],
    )
```
