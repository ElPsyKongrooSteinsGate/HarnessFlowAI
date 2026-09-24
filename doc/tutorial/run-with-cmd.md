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

## 7) Define business workflows

Business processes can be declared as workflows and routed by capabilities:

```python
from core.types import WorkflowDefinition, WorkflowStep

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
```

When the goal contains matching capabilities, the router selects the workflow automatically:

```python
selected = router.select("Approve invoice INV-1001 for payment")
print(selected.name)
```

Expected output:

```text
invoice_approval
```

Each workflow receives its own governed `AgentHarness` with its own tools, approvals, step limit, and system prompt.

### Workflow-specific governance RAG

Governance documents can be attached to each workflow:

```python
WorkflowDefinition(
    name="invoice_approval",
    governance_collection="finance-governance",
    governance_documents=[
        "Invoices over 5000 require manager approval before payment.",
        "Validate the invoice number, vendor, amount, and budget before approval.",
    ],
)
```

When the workflow is selected, `RAGEngine` retrieves documents from that workflow's collection and `ContextEngine` adds them to the model context as governance knowledge. The `ControlPlane` still enforces hard limits and tool permissions; retrieved policy text informs the agent but is not a security boundary.

### Check that RAG is working

Run this direct ChromaDB retrieval check from Command Prompt:

```cmd
python -c "import asyncio; from engines.rag_engine import RAGEngine; rag=RAGEngine(); rag.add_document('Invoices over 5000 require manager approval.','finance-governance'); rag.add_document('Verify employee identity before account creation.','hr-governance'); docs=asyncio.run(rag.retrieve('invoice payment approval','finance-governance')); print(docs); assert docs == ['Invoices over 5000 require manager approval.']; print('RAG_OK')"
```

Expected output:

```text
['Invoices over 5000 require manager approval.']
RAG_OK
```

This verifies collection isolation, retrieval relevance, and persistent vector storage. ChromaDB data is stored under `data/chroma`. Running `python run.py` alone does not prove that the model used the retrieved policy because the current `ModelGateway` is a fixed local stub.

On the first retrieval, ChromaDB may download its default `all-MiniLM-L6-v2` embedding model into the local Chroma cache. Later runs reuse that cache.

### Query ChromaDB with the utility script

The reusable query utility is located at:

```text
script/data/query/chromedb/query.py
```

List available collections:

```cmd
python script/data/query/chromedb/query.py --list
```

Run a semantic query:

```cmd
python script/data/query/chromedb/query.py --collection finance-governance --query "invoice approval" --limit 5
```

Inspect all records in a collection:

```cmd
python script/data/query/chromedb/query.py --collection finance-governance --get
```

The utility reads the persistent store from `data/chroma` by default.

## 8) Where governance fits

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
- Workflow routing is capability-based. An unknown goal should be handled by a future model-based classifier or explicit agent name.
- The current model gateway is a local stub, so workflow execution currently demonstrates routing and governance but does not call a real LLM or business system.
- This setup is intended for local development and experimentation.

## 9) Run the minimal API

The API entry point is `api/app.py` and the dependency list is `requirements.txt`.

Install the API dependencies:

```cmd
python -m pip install -r requirements.txt
```

Start the backend:

```cmd
python -m uvicorn api.app:app --host 127.0.0.1 --port 8000
```

In a second Command Prompt window, verify the API:

```cmd
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/workflows
curl -X POST http://127.0.0.1:8000/workflows/run -H "Content-Type: application/json" -d "{\"goal\":\"Approve invoice INV-1001 for payment\"}"
```

The response contains the selected workflow and lifecycle events:

```json
{
    "workflow": "invoice_approval",
    "status": "TASK_COMPLETED",
    "events": ["TASK_STARTED", "THOUGHT_START", "THOUGHT_COMPLETE", "TASK_COMPLETED"]
}
```

The current API runs workflows synchronously and stores task results in memory. It is intended as a working development backend before adding a database, background workers, authentication, and real model providers.
