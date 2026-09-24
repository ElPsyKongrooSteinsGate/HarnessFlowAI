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