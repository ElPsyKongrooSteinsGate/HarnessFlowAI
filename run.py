import asyncio
from core.agent_router import AgentRouter
from core.default_workflows import register_default_workflows

async def main():
    router = AgentRouter()
    register_default_workflows(router)

    goal = "Assess compliance obligations and risks for our organization under ISO 37301"
    selected = router.select(goal)
    print(f"Selected workflow: {selected.name}")
    async for event in router.run(goal):
        print(event)

asyncio.run(main())