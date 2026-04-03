# Workflows and Orchestrations Reference

Multi-agent orchestrations, workflow builders, events, and state management.

## Table of Contents

- [Orchestration Builders](#orchestration-builders)
- [SequentialBuilder](#sequentialbuilder)
- [GroupChatBuilder](#groupchatbuilder)
- [HandoffBuilder](#handoffbuilder)
- [MagenticBuilder](#magenticbuilder)
- [ConcurrentBuilder](#concurrentbuilder)
- [Custom WorkflowBuilder](#custom-workflowbuilder)
- [WorkflowEvent](#workflowevent)
- [State Management](#state-management)
- [Workflow Streaming](#workflow-streaming)
- [Declarative Workflows](#declarative-workflows)
- [Checkpointing](#checkpointing)
- [Background Responses](#background-responses)

## Orchestration Builders

All orchestration builders import from `agent_framework.orchestrations`:

```python
from agent_framework.orchestrations import (
    SequentialBuilder,
    ConcurrentBuilder,
    GroupChatBuilder,
    MagenticBuilder,
    HandoffBuilder,
)
```

All builders use constructor parameters — fluent setter methods are removed.

---

## SequentialBuilder

Agents execute in order, each receiving the previous agent's output:

```python
from agent_framework.orchestrations import SequentialBuilder

workflow = SequentialBuilder(participants=[writer, reviewer, editor]).build()
result = await workflow.run("Write a blog post about AI agents")
```

### With Checkpointing

```python
workflow = SequentialBuilder(
    participants=[writer, reviewer],
    checkpoint_storage=storage,
).build()
```

---

## GroupChatBuilder

Multi-agent conversation with orchestrated turn selection:

```python
from agent_framework.orchestrations import GroupChatBuilder

workflow = GroupChatBuilder(
    participants=[researcher, writer, critic],
    selection_func=my_selector,
    termination_condition=lambda conv: len(conv) >= 10,
    max_rounds=15,
).build()

result = await workflow.run("Discuss the future of AI agents")
```

---

## HandoffBuilder

Agents can hand off control to each other:

```python
from agent_framework.orchestrations import HandoffBuilder

workflow = HandoffBuilder(
    participants=[triage, billing, support],
    start_agent=triage,
    termination_condition=lambda conv: len(conv) > 20,
    checkpoint_storage=storage,
).build()

result = await workflow.run("I need help with my account")
```

---

## MagenticBuilder

Manager-coordinated multi-agent planning and execution:

```python
from agent_framework.orchestrations import MagenticBuilder

workflow = MagenticBuilder(
    participants=[researcher, coder, tester],
    manager_agent=manager,
    enable_plan_review=True,
).build()

result = await workflow.run("Build a data pipeline")
```

---

## ConcurrentBuilder

Agents execute in parallel:

```python
from agent_framework.orchestrations import ConcurrentBuilder

workflow = ConcurrentBuilder(participants=[analyst_a, analyst_b, analyst_c]).build()
result = await workflow.run("Analyze market trends")
```

---

## Custom WorkflowBuilder

Build arbitrary directed graphs with executors:

```python
from agent_framework import WorkflowBuilder

upper = UpperCaseExecutor(id="upper")
reverse = ReverseExecutor(id="reverse")
summarize = SummarizeExecutor(id="summarize")

workflow = (
    WorkflowBuilder(start_executor=upper, checkpoint_storage=storage)
    .add_edge(upper, reverse)
    .add_edge(reverse, summarize)
    .build()
)
```

### With Agents

```python
writer = create_writer_agent()
reviewer = create_reviewer_agent()

workflow = WorkflowBuilder(start_executor=writer).add_edge(writer, reviewer).build()
```

### State Isolation

For workflows that need isolated state per invocation, wrap construction in a helper:

```python
def create_workflow():
    """Each call produces fresh executor instances."""
    upper = UpperCaseExecutor(id="upper")
    reverse = ReverseExecutor(id="reverse")
    return WorkflowBuilder(start_executor=upper).add_edge(upper, reverse).build()

workflow_a = create_workflow()
workflow_b = create_workflow()
```

### Edge Types

```python
# Simple edge
builder.add_edge(source, target)

# Fan-out (one to many)
builder.add_fan_out_edges(source, [target_a, target_b])

# Fan-in (many to one)
builder.add_fan_in_edges([source_a, source_b], target)

# Chain (sequential)
builder.add_chain([step_1, step_2, step_3])

# Switch/case (conditional routing)
builder.add_switch_case_edge_group(source, {
    "positive": positive_handler,
    "negative": negative_handler,
    "neutral": neutral_handler,
})

# Multi-selection (dynamic routing)
builder.add_multi_selection_edge_group(source, {
    "route_a": handler_a,
    "route_b": handler_b,
})
```

### Validation

- `WorkflowBuilder` requires `start_executor` as a constructor argument
- `SequentialBuilder`, `ConcurrentBuilder`, `GroupChatBuilder`, and `MagenticBuilder` require either `participants` or `participant_factories` — passing neither raises `ValueError`

---

## WorkflowEvent

All workflow events use a single generic `WorkflowEvent[DataT]` class with a `type` string discriminator:

```python
from agent_framework import WorkflowEvent

async for event in workflow.run_stream("Process this"):
    if event.type == "output":
        print(f"Output from {event.executor_id}: {event.data}")
    elif event.type == "request_info":
        requests[event.request_id] = event.data
    elif event.type == "status":
        print(f"Status: {event.state}")
    elif event.type == "started":
        print("Workflow started")
    elif event.type == "executor_invoked":
        print(f"Executor {event.executor_id} invoked")
    elif event.type == "executor_completed":
        print(f"Executor {event.executor_id} completed")
    elif event.type == "failed":
        print(f"Workflow failed: {event.data}")
```

### Event Types

| `event.type` | Purpose |
|--------------|---------|
| `"output"` | Workflow output data |
| `"request_info"` | Information request from executor |
| `"status"` | Workflow status update |
| `"started"` | Workflow started |
| `"failed"` | Workflow failed |
| `"executor_invoked"` | Executor began execution |
| `"executor_completed"` | Executor finished |
| `"executor_failed"` | Executor failed |
| `"superstep_started"` | Superstep began |
| `"superstep_completed"` | Superstep finished |

### Type Annotations

```python
from typing import Any
from agent_framework import WorkflowEvent

pending_requests: list[WorkflowEvent[Any]] = []
output: WorkflowEvent | None = None
```

---

## State Management

State access is synchronous. Use `ctx.state`, `ctx.get_state()`, `ctx.set_state()`:

```python
class MyExecutor:
    async def execute(self, ctx):
        # Read state
        count = ctx.get_state("count") or 0

        # Write state
        ctx.set_state("count", count + 1)

        # Direct access
        all_state = ctx.state
```

### Checkpoint State

```python
# Checkpoint state is also accessed via .state
checkpoint.state  # Dict of workflow state at checkpoint time
```

---

## Workflow Streaming

### Stream with AgentResponseUpdate

```python
from agent_framework import AgentResponseUpdate

async for event in workflow.run_stream("Write a blog post about AI agents."):
    if event.type == "output" and isinstance(event.data, AgentResponseUpdate):
        print(event.data, end="", flush=True)
    elif event.type == "output":
        print(f"Final output: {event.data}")
```

### Continue Paused Workflows

Pass responses directly to `run()` (not `send_responses()`):

```python
async for event in workflow.run(
    checkpoint_id=checkpoint_id,
    responses=[approved_response],
):
    print(event)
```

### Runtime Kwargs in Workflows

Pass kwargs per-executor or globally:

```python
# Per-executor targeting
await workflow.run(
    "Draft the report",
    function_invocation_kwargs={
        "researcher": {"db_config": {"connection_string": "..."}},
        "writer": {"user_preferences": {"format": "markdown"}},
    },
)

# Global (forwarded to all executors)
await workflow.run(
    "Draft the report",
    function_invocation_kwargs={"api_key": "shared-key"},
)
```

---

## Declarative Workflows

Define workflows in YAML and register Python tools:

```python
from agent_framework import WorkflowFactory

factory = WorkflowFactory().register_tool("send_email", send_email)
```

```yaml
actions:
  - kind: InvokeFunctionTool
    functionName: send_email
```

---

## Checkpointing

Enable checkpointing on any builder with `checkpoint_storage`:

```python
from agent_framework.orchestrations import SequentialBuilder

workflow = SequentialBuilder(
    participants=[agent_a, agent_b],
    checkpoint_storage=storage,
).build()
```

- `FileCheckpointStorage` uses pickle serialization
- Checkpoint internals store live objects (serialization happens in checkpoint storage)

---

## Background Responses

For long-running agent tasks:

```python
response = await agent.run("Long task", options={"background": True})
while response.continuation_token is not None:
    response = await agent.run(
        options={"continuation_token": response.continuation_token}
    )
```
