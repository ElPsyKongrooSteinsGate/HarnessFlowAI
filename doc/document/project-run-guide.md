# HarnessFlowAI Run Guide

## Overview

HarnessFlowAI is a Python-based execution and governance layer for AI agents. It manages a task lifecycle, context windowing, provider-based model access, tool execution, approval policies, and execution tracing.

`AgentRouter` is the entry point for choosing among registered agents. The selected agent is an `AgentHarness` configured with its own model, tool, memory, and governance settings.

```text
User goal
    -> AgentRouter selects an agent
    -> AgentHarness executes the workflow
    -> Model, tools, approvals, memory, and events
```

## Declarative business workflows

Business use cases are represented by `WorkflowDefinition` objects. A workflow declares its capabilities, ordered process steps, tools, approvals, system prompt, and execution limit.

```python
from core.types import WorkflowDefinition, WorkflowStep

router.register_workflow(
    WorkflowDefinition(
        name="invoice_approval",
        description="Invoice approval and payment workflow",
        capabilities=["invoice", "approval", "payment", "billing"],
        steps=[
            WorkflowStep(name="validate_invoice"),
            WorkflowStep(name="check_budget"),
            WorkflowStep(name="request_approval", required_approval=True),
        ],
        allowed_tools=["invoice_lookup", "budget_check", "request_approval"],
        approval_tools=["request_approval"],
        max_steps=10,
        system_prompt="You manage invoice approval workflows and follow company policy.",
    )
)
```

The router resolves a goal against workflow capabilities:

```python
selected = router.select("Approve invoice INV-1001 for payment")
print(selected.name)
```

This prints `invoice_approval`. A second workflow, such as employee onboarding, can be registered with different capabilities and policies. The selected workflow automatically creates its own governed `AgentHarness`.

## Environment

This project is intended to run with the Conda environment named `ml`.

## Command Prompt workflow

Use the following steps from Windows Command Prompt:

```cmd
conda activate ml
cd /d "C:\Users\Acer\Desktop\my\anaconda\Harness\HarnessFlowAI"
python -c "import sys; print(sys.executable)"
```

Expected Python path:

```text
C:\Users\Acer\anaconda3\envs\ml\python.exe
```

## Import validation

```cmd
python -c "from core.agent_router import AgentRouter; from core.harness import AgentHarness; print('loaded')"
```

This should print:

```text
loaded
```

## Example routed runner

```python
import asyncio
from core.agent_router import AgentRouter
from core.types import HarnessConfig

async def main():
    router = AgentRouter()
    router.register(
        name="coding",
        description="coding software programming development",
        config=HarnessConfig(
            system_prompt="You are a helpful AI coding assistant.",
            max_steps=5,
            allowed_tools=[]
        )
    )
    async for event in router.run("Write a hello world script"):
        print(event)

asyncio.run(main())
```

Run it with:

```cmd
python run.py
```

## Agent selection

Register additional agents with different configurations:

```python
router.register(
    name="review",
    description="review inspect audit quality",
    config=HarnessConfig(
        system_prompt="You review code for correctness and risk.",
        max_steps=10,
        allowed_tools=[]
    )
)
```

Automatic selection uses the registered agent descriptions and the words in the user goal. Explicit selection is also supported:

```python
async for event in router.run(
    "Inspect the implementation",
    agent_name="review"
):
    print(event)
```

`AgentRouter` chooses the agent; `AgentHarness` remains responsible for controlled execution, approvals, tools, memory, and lifecycle events.

## Governance model

Governance is enforced by the `ControlPlane` owned by each `AgentHarness`. This keeps agent selection separate from execution policy:

```text
AgentRouter
    -> selects a named agent and its HarnessConfig
AgentHarness
    -> creates the task and runs the workflow
ControlPlane
    -> enforces max_steps and approval_tools
ToolRuntime
    -> executes the approved tool call
Tracer and Events
    -> expose the workflow outcome
```

The main governance checks are:

- **Step limit:** `validate_step_limit()` stops a workflow that exceeds `max_steps`.
- **Tool approval:** `request_approval_if_needed()` checks tools listed in `approval_tools`.
- **Tool allow-list:** `ToolRuntime` receives `allowed_tools` for the selected agent.
- **Failure state:** policy violations and runtime errors produce `TASK_FAILED` and set the harness state to `FAILED`.

Each registered agent can use a different policy profile because its `HarnessConfig` is passed into its own `AgentHarness`:

```python
router.register(
     name="restricted-review",
     description="review inspect audit quality",
     config=HarnessConfig(
          system_prompt="Review code for correctness and risk.",
          max_steps=10,
          allowed_tools=[],
          approval_tools=["file_delete", "terminal_execute"]
     )
)
```

This is the governance boundary of HarnessFlowAI: the router decides **which** worker runs, while the selected harness decides **how** that worker may run.

## Current status

The project imports successfully in the `ml` environment. Workflow routing and per-workflow governance are implemented, but the model gateway is still a local stub. Production use requires a real LLM provider, real business tools, persistent workflow state, and a stronger intent classifier for unmatched goals.

## Minimal API backend

The project now includes a small FastAPI backend in `api/app.py`.

Backend files:

```text
api/
├── __init__.py
└── app.py
requirements.txt
```

Install dependencies:

```cmd
python -m pip install -r requirements.txt
```

Start it from Windows Command Prompt:

```cmd
conda activate ml
cd /d "C:\Users\Acer\Desktop\my\anaconda\Harness\HarnessFlowAI"
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

Available endpoints:

```text
GET  /health
GET  /workflows
POST /workflows/run
GET  /tasks/{task_id}
```

Example request from a second Command Prompt window:

```cmd
curl -X POST http://127.0.0.1:8000/workflows/run -H "Content-Type: application/json" -d "{\"goal\":\"Approve invoice INV-1001 for payment\"}"
```

Example response shape:

```json
{
    "task_id": "generated-task-id",
    "workflow": "invoice_approval",
    "status": "TASK_COMPLETED",
    "events": [
        {"type": "TASK_STARTED"},
        {"type": "THOUGHT_START"},
        {"type": "THOUGHT_COMPLETE"},
        {"type": "TASK_COMPLETED"}
    ]
}
```

The response includes the selected workflow, task ID, final status, and emitted events. This first backend version runs synchronously and uses in-memory task storage so the request flow is easy to test. It is not yet production-ready; database persistence, authentication, background workers, real model providers, and business integrations come next.
