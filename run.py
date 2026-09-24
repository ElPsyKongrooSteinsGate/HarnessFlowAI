import asyncio
from core.agent_router import AgentRouter
from core.types import HarnessConfig, WorkflowDefinition, WorkflowStep

async def main():
    router = AgentRouter()
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
    router.register_workflow(
        WorkflowDefinition(
            name="employee_onboarding",
            description="Employee onboarding and access workflow",
            capabilities=["employee", "onboarding", "access", "hire"],
            steps=[
                WorkflowStep(name="validate_employee"),
                WorkflowStep(name="create_accounts", required_approval=True),
            ],
            allowed_tools=["employee_lookup", "create_accounts"],
            approval_tools=["create_accounts"],
            max_steps=10,
            system_prompt="You manage employee onboarding workflows and follow access policy.",
        )
    )

    goal = "Approve invoice INV-1001 for payment"
    selected = router.select(goal)
    print(f"Selected workflow: {selected.name}")
    async for event in router.run(goal):
        print(event)

asyncio.run(main())