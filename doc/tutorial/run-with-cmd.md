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
python -c "from core.harness import AgentHarness; from core.types import HarnessConfig; print('loaded')"
```

A successful result will print:

```text
loaded
```

## 6) Run a simple script

Create a file named `run.py` in the project root with this content:

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

Then run it:

```cmd
python run.py
```

## Notes

- The project currently imports successfully in the `ml` environment.
- It is still a framework scaffold and may not yet perform full end-to-end runtime behavior automatically.
- This setup is intended for local development and experimentation.
