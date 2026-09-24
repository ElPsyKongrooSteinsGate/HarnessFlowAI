# HarnessFlowAI Run Guide

## Overview

HarnessFlowAI is a Python-based agent framework designed to manage a task lifecycle, context windowing, provider-based model access, tool execution, and execution tracing.

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
python -c "from core.harness import AgentHarness; from core.types import HarnessConfig; print('loaded')"
```

This should print:

```text
loaded
```

## Example runner script

```python
import asyncio
from core.harness import AgentHarness
from core.types import HarnessConfig

async def main():
    config = HarnessConfig(
        system_prompt="You are a helpful AI coding assistant.",
        max_steps=5,
        allowed_tools=[]
    )
    harness = AgentHarness(config)
    async for event in harness.run("Write a hello world script"):
        print(event)

asyncio.run(main())
```

Run it with:

```cmd
python run.py
```

## Current status

The project imports successfully in the `ml` environment, but it remains a scaffold framework rather than a complete production agent runtime. Some modules are intentionally minimal and may require further implementation for advanced tool execution and model integration.
