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