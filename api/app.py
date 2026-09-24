from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.agent_router import AgentRouter
from core.types import EventType, WorkflowDefinition, WorkflowStep


class WorkflowRunRequest(BaseModel):
    goal: str = Field(min_length=1)
    agent_name: Optional[str] = None


class WorkflowRunResponse(BaseModel):
    task_id: str
    workflow: str
    status: str
    events: List[Dict[str, Any]]


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

task_store: Dict[str, WorkflowRunResponse] = {}
app = FastAPI(title="HarnessFlowAI API", version="0.1.0")


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/workflows")
async def list_workflows() -> Dict[str, List[str]]:
    return {"workflows": list(router.workflows.names())}


@app.post("/workflows/run", response_model=WorkflowRunResponse)
async def run_workflow(request: WorkflowRunRequest) -> WorkflowRunResponse:
    try:
        selected = router.select(request.goal, request.agent_name)
    except (KeyError, LookupError, RuntimeError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    events: List[Dict[str, Any]] = []
    async for event in router.run(request.goal, request.agent_name):
        events.append(event.model_dump(mode="json"))

    if not events or events[0]["type"] != EventType.TASK_STARTED.value:
        raise HTTPException(status_code=500, detail="Workflow did not produce a task-start event.")

    task_id = events[0]["payload"]["task_id"]
    status = events[-1]["type"]
    result = WorkflowRunResponse(
        task_id=task_id,
        workflow=selected.name,
        status=status,
        events=events,
    )
    task_store[task_id] = result
    return result


@app.get("/tasks/{task_id}", response_model=WorkflowRunResponse)
async def get_task(task_id: str) -> WorkflowRunResponse:
    task = task_store.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found.")
    return task
