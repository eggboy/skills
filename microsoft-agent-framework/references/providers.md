# Provider Reference

Client types, configuration, and environment variables for all supported providers.

## Table of Contents

- [OpenAI](#openai)
- [Azure OpenAI](#azure-openai)
- [Microsoft Foundry](#microsoft-foundry)
- [Foundry Local](#foundry-local)
- [Anthropic](#anthropic)
- [Foundry Embeddings](#foundry-embeddings)
- [OpenAI Embeddings](#openai-embeddings)
- [Environment Variables](#environment-variables)
- [Client Mapping from Pre-1.0](#client-mapping-from-pre-10)

## OpenAI

### OpenAIChatClient (Responses API)

The primary OpenAI client. Uses the Responses API.

```python
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

client = OpenAIChatClient(model="gpt-4o")
agent = Agent(client=client, name="assistant", instructions="You are helpful.")

response = await agent.run("Hello!")
print(response.value)
```

### OpenAIChatCompletionClient (Chat Completions API)

For the older Chat Completions API surface:

```python
from agent_framework.openai import OpenAIChatCompletionClient

client = OpenAIChatCompletionClient(model="gpt-4o-mini")
```

### Direct API Usage (without Agent)

```python
from agent_framework.openai import OpenAIChatClient

client = OpenAIChatClient(model="gpt-4o")
response = await client.get_response(
    "What is Python?",
    options={"temperature": 0.7, "max_tokens": 500},
)
print(response.value)
```

---

## Azure OpenAI

Use the OpenAI clients with explicit Azure routing signals (`azure_endpoint` + `credential`):

```python
from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient
from azure.identity import AzureCliCredential

client = OpenAIChatClient(
    model="gpt-4o",
    azure_endpoint="https://your-resource.openai.azure.com",
    credential=AzureCliCredential(),
    api_version="2025-03-01-preview",
)

agent = Agent(client=client, name="azure-agent", instructions="You are helpful.")
```

### Azure OpenAI Chat Completions

```python
from agent_framework.openai import OpenAIChatCompletionClient
from azure.identity import AzureCliCredential

client = OpenAIChatCompletionClient(
    model="gpt-4o-mini",
    azure_endpoint="https://your-resource.openai.azure.com",
    credential=AzureCliCredential(),
    api_version="2025-03-01-preview",
)
```

### Azure OpenAI Routing

Generic OpenAI clients prefer explicit routing signals. If both `OPENAI_API_KEY` and `AZURE_OPENAI_*` env vars are set, the client stays on OpenAI unless you pass `credential` or `azure_endpoint`. Always be explicit about Azure routing:

```python
# Explicit Azure routing (recommended)
client = OpenAIChatClient(
    model="gpt-4o",
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    credential=AzureCliCredential(),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
)
```

---

## Microsoft Foundry

### FoundryChatClient (Project Inference)

For direct model inference through a Foundry project endpoint:

```python
from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

client = FoundryChatClient(
    project_endpoint="https://your-project.services.ai.azure.com",
    model="gpt-4o-mini",
    credential=DefaultAzureCredential(),
)

agent = Agent(client=client, name="foundry-agent", instructions="You are helpful.")
```

### FoundryAgent (Service-Managed)

For Prompt Agents and Hosted Agents managed by the Foundry service:

```python
from agent_framework.foundry import FoundryAgent
from azure.identity import DefaultAzureCredential

agent = FoundryAgent(
    project_endpoint="https://your-project.services.ai.azure.com",
    credential=DefaultAzureCredential(),
    agent_name="my-agent",
    agent_version="1.0",
)

response = await agent.run("Hello!")
```

### FoundryAgent with Tools

```python
from agent_framework import tool
from agent_framework.foundry import FoundryAgent
from azure.identity import DefaultAzureCredential

@tool
def get_stock_price(symbol: str) -> str:
    """Get current stock price."""
    return f"{symbol}: $150.00"

agent = FoundryAgent(
    project_endpoint="https://your-project.services.ai.azure.com",
    credential=DefaultAzureCredential(),
    agent_name="finance-agent",
    tools=[get_stock_price],
)
```

---

## Foundry Local

For local model runtimes:

```python
from agent_framework import Agent
from agent_framework.foundry import FoundryLocalClient

client = FoundryLocalClient(model="phi-4-mini")
agent = Agent(client=client, name="local-agent", instructions="You are helpful.")
```

If `model` is omitted, set `FOUNDRY_LOCAL_MODEL` in your environment.

---

## Anthropic

```python
from agent_framework import Agent
from agent_framework.anthropic import AnthropicClient

client = AnthropicClient(model="claude-sonnet-4-5-20250929")
agent = Agent(client=client, name="claude-agent", instructions="You are helpful.")
```

### Anthropic on Provider-Hosted Platforms

```python
from agent_framework.anthropic import AnthropicFoundryClient, AnthropicBedrockClient, AnthropicVertexClient

# Anthropic via Foundry
client = AnthropicFoundryClient(model="claude-sonnet-4-5-20250929")

# Anthropic via AWS Bedrock
client = AnthropicBedrockClient(model="claude-sonnet-4-5-20250929")

# Anthropic via Google Vertex
client = AnthropicVertexClient(model="claude-sonnet-4-5-20250929")
```

---

## Foundry Embeddings

```python
from agent_framework.foundry import FoundryEmbeddingClient

client = FoundryEmbeddingClient(
    endpoint=os.environ["FOUNDRY_MODELS_ENDPOINT"],
    api_key=os.environ["FOUNDRY_MODELS_API_KEY"],
    model=os.environ["FOUNDRY_EMBEDDING_MODEL"],
)
```

---

## OpenAI Embeddings

### OpenAI Direct

```python
from agent_framework.openai import OpenAIEmbeddingClient

client = OpenAIEmbeddingClient(model="text-embedding-3-small")
```

### Azure OpenAI Embeddings

```python
from agent_framework.openai import OpenAIEmbeddingClient
from azure.identity import AzureCliCredential

client = OpenAIEmbeddingClient(
    model=os.environ["AZURE_OPENAI_EMBEDDING_MODEL"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    credential=AzureCliCredential(),
    api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
)
```

---

## Environment Variables

### OpenAI

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | API key |
| `OPENAI_MODEL` | Shared fallback model name |
| `OPENAI_CHAT_MODEL` | Model for `OpenAIChatClient` |
| `OPENAI_CHAT_COMPLETION_MODEL` | Model for `OpenAIChatCompletionClient` |
| `OPENAI_EMBEDDING_MODEL` | Model for `OpenAIEmbeddingClient` |

### Azure OpenAI

| Variable | Purpose |
|----------|---------|
| `AZURE_OPENAI_ENDPOINT` | Resource endpoint URL |
| `AZURE_OPENAI_API_VERSION` | API version |
| `AZURE_OPENAI_MODEL` | Shared fallback model name |
| `AZURE_OPENAI_CHAT_MODEL` | Model for `OpenAIChatClient` |
| `AZURE_OPENAI_CHAT_COMPLETION_MODEL` | Model for `OpenAIChatCompletionClient` |
| `AZURE_OPENAI_EMBEDDING_MODEL` | Embedding model name |

### Foundry

| Variable | Purpose |
|----------|---------|
| `FOUNDRY_PROJECT_ENDPOINT` | Project endpoint URL |
| `FOUNDRY_MODEL` | Default model |
| `FOUNDRY_AGENT_NAME` | Agent name for FoundryAgent |
| `FOUNDRY_AGENT_VERSION` | Agent version |
| `FOUNDRY_MODELS_ENDPOINT` | Endpoint for embeddings |
| `FOUNDRY_MODELS_API_KEY` | API key for embeddings |
| `FOUNDRY_EMBEDDING_MODEL` | Embedding model name |
| `FOUNDRY_IMAGE_EMBEDDING_MODEL` | Image embedding model |
| `FOUNDRY_LOCAL_MODEL` | Model for FoundryLocalClient |

### Anthropic

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | API key |
| `ANTHROPIC_CHAT_MODEL` | Default model |

---

## Client Mapping from Pre-1.0

If upgrading from preview versions, use this mapping:

| Old class | New class | Package |
|-----------|-----------|---------|
| `AzureOpenAIResponsesClient` | `OpenAIChatClient` | `agent-framework-openai` |
| `AzureOpenAIChatClient` | `OpenAIChatCompletionClient` | `agent-framework-openai` |
| `AzureOpenAIEmbeddingClient` | `OpenAIEmbeddingClient` | `agent-framework-openai` |
| `AzureAIAgentsProvider` | `FoundryAgent` | `agent-framework-foundry` |
| `AzureAIClient` | `FoundryChatClient` or `FoundryAgent` | `agent-framework-foundry` |
| `OpenAIResponsesClient` | `OpenAIChatClient` | `agent-framework-openai` |
| `OpenAIAssistantsClient` | `OpenAIChatClient` or `FoundryAgent` | varies |
| `AzureAIInferenceEmbeddingClient` | `FoundryEmbeddingClient` | `agent-framework-foundry` |

Key parameter changes:
- `model_id` → `model`
- `deployment_name` → `model`
- `model_deployment_name` → `model`
- `ad_token_provider` → `credential`
- `endpoint` → `azure_endpoint` (for Azure OpenAI)
