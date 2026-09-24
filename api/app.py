from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from core.agent_router import AgentRouter
from core.default_workflows import register_default_workflows
from core.types import EventType


class WorkflowRunRequest(BaseModel):
    goal: str = Field(min_length=1)
    agent_name: Optional[str] = None


class WorkflowRunResponse(BaseModel):
    task_id: str
    workflow: str
    status: str
    events: List[Dict[str, Any]]


class WorkflowDocumentRequest(BaseModel):
    workflow: str = Field(min_length=1)
    content: str = Field(min_length=1)
    source: str = Field(default="user-input", min_length=1)


class WorkflowDocumentResponse(BaseModel):
    workflow: str
    collection: str
    source: str
    status: str


router = AgentRouter()
register_default_workflows(router)

task_store: Dict[str, WorkflowRunResponse] = {}
app = FastAPI(title="HarnessFlowAI API", version="0.1.0")


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/workflows")
async def list_workflows() -> Dict[str, List[str]]:
    return {"workflows": list(router.workflows.names())}


@app.post("/knowledge/workflow", response_model=WorkflowDocumentResponse)
async def add_workflow_document(
    request: WorkflowDocumentRequest,
) -> WorkflowDocumentResponse:
    try:
        router.add_workflow_document(
            workflow_name=request.workflow,
            content=request.content,
            source=request.source,
        )
        workflow = router.workflows.get(request.workflow)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return WorkflowDocumentResponse(
        workflow=request.workflow,
        collection=workflow.workflow_collection,
        source=request.source,
        status="stored",
    )


@app.get("/knowledge/workflow/{workflow_name}")
async def query_workflow_knowledge(
    workflow_name: str,
    query: str = Query(min_length=1),
    limit: int = 5,
) -> Dict[str, Any]:
    try:
        workflow = router.workflows.get(workflow_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    documents = await router.rag_engine.retrieve(
        query=query,
        collection=workflow.workflow_collection,
        limit=limit,
        where={"workflow": workflow_name},
    )
    return {
        "workflow": workflow_name,
        "collection": workflow.workflow_collection,
        "documents": documents,
    }


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
