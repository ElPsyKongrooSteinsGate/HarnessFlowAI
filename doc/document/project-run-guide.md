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

## Current status

The project imports successfully in the `ml` environment, but it remains a scaffold framework rather than a complete production agent runtime. Some modules are intentionally minimal and may require further implementation for advanced tool execution and model integration.
