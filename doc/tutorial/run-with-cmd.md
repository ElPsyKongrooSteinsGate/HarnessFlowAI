# Running HarnessFlowAI from Windows Command Prompt

This guide explains how to run the project from the Windows `cmd` shell using the Conda `ml` environment.

## 1) Open Command Prompt

Open a new Windows Command Prompt window.

## 2) Activate the Conda environment

```cmd
conda activate ml
```

## 3) Go to the project folder

```cmd
cd /d "C:\Users\Acer\Desktop\my\anaconda\Harness\HarnessFlowAI"
```

## 4) Verify Python is using the correct environment

```cmd
python -c "import sys; print(sys.executable)"
```

The output should point to:

```text
C:\Users\Acer\anaconda3\envs\ml\python.exe
```

## 5) Import the project

```cmd
python -c "from core.agent_router import AgentRouter; from core.harness import AgentHarness; print('loaded')"
```

A successful result will print:

```text
loaded
```

## 6) Run a routed agent

The project uses `AgentRouter` to choose a named agent before handing the goal to its `AgentHarness`. The sample `run.py` registers a `coding` agent and selects it from the goal description.

The core pattern is:

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

Then run it:

```cmd
python run.py
```

To select a registered agent explicitly, pass its name:

```python
async for event in router.run("Review this code", agent_name="coding"):
    print(event)
```

The router selects an agent automatically when `agent_name` is omitted. Each registered agent has its own `HarnessConfig`, so governance limits, approval rules, providers, and tools can vary by agent.

## 7) Where governance fits

Governance runs inside the selected `AgentHarness`, after the router chooses an agent:

```text
User goal
   -> AgentRouter selects an agent
   -> AgentHarness starts the workflow
   -> ControlPlane checks limits and approvals
   -> Approved tools execute through ToolRuntime
   -> Events and memory record the result
```

The `ControlPlane` enforces the configured step limit before each model step and checks every requested tool before execution. Configure these policies per agent:

```python
HarnessConfig(
    max_steps=5,
    approval_tools=["terminal_execute", "file_delete"],
    allowed_tools=["terminal_execute"]
)
```

The router chooses the worker; the harness and control plane govern how that worker operates.

## Notes

- The project currently imports successfully in the `ml` environment.
- It is still a framework scaffold and may not yet perform full end-to-end runtime behavior automatically.
- This setup is intended for local development and experimentation.
