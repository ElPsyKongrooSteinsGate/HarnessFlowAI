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

## 7) Run the ISO 37301 compliance agent

The default agent is designed for ISO 37301 compliance management system assessment. It is selected for goals containing compliance, governance, obligations, risk, audit, or ISO 37301 concepts.

The workflow includes:

```text
Understand context and scope
   -> Identify compliance obligations
   -> Assess compliance risk
   -> Evaluate evidence and gaps
   -> Recommend corrective action
```

Run it with:

```cmd
python run.py
```

The runner selects:

```text
iso37301_compliance
```

To register another business workflow, use `WorkflowDefinition` with its own capabilities, steps, tools, and governance policy. The current default workflow is intentionally ISO 37301-specific because the loaded governance source is ISO 37301.

### Workflow-specific governance RAG

The ISO workflow uses the shared `workflows` collection for process knowledge and the shared `governance` collection for policies. Global ISO records are loaded from `data/governance/ISO/ISO_37301.csv` before any harness is created.

Workflow-specific policies can still be attached like this:

```python
WorkflowDefinition(
    name="iso37301_compliance",
    workflow_collection="workflows",
    governance_collection="governance",
    workflow_documents=[
        "Assess context, obligations, risk, evidence, gaps, and corrective actions.",
    ],
    governance_documents=[
        "Use the approved compliance policy and cite the applicable ISO clause.",
    ],
)
```

When the workflow is selected, `RAGEngine` retrieves workflow knowledge and both workflow-specific and global ISO governance. `ContextEngine` keeps those sections separate. The `ControlPlane` still enforces hard limits and tool permissions; retrieved policy text informs the agent but is not a security boundary.

The ISO governance CSV under `data/governance/ISO/` is loaded automatically when `AgentRouter` starts. This happens before `register_workflow()` creates any `AgentHarness`, so the shared governance collection already contains ISO policy data before a workflow can run. Global ISO records are marked with `scope=global` and are available to every workflow; workflow-specific policies are marked with that workflow name.

The current ISO source file is:

```text
data/governance/ISO/ISO_37301.csv
```

You can confirm that ISO records are present in the shared collection with:

```cmd
python script/data/query/chromedb/query.py --collection governance --query "compliance obligations" --limit 5
```

The loader uses deterministic document IDs, so starting the application again updates existing ISO records instead of creating duplicates.

### Check that RAG is working

Run this direct ChromaDB retrieval check from Command Prompt:

```cmd
python script/data/query/chromedb/query.py --collection governance --query "compliance obligations" --limit 5
```

Expected output:

The result should contain ISO governance records from `ISO_37301.csv`.

This verifies collection isolation, retrieval relevance, and persistent vector storage. Because ChromaDB is persistent, queries can return multiple matching records and should not assert one exact result. Running `python run.py` alone does not prove that the model used the retrieved policy because the current `ModelGateway` is a fixed local stub.

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

Run a semantic query against all workflow definitions:

```cmd
python script/data/query/chromedb/query.py --collection workflows --query "invoice approval" --limit 5
```

Run a semantic query against all governance policies:

```cmd
python script/data/query/chromedb/query.py --collection governance --query "invoice approval limit" --limit 5
```

Inspect all records in a collection:

```cmd
python script/data/query/chromedb/query.py --collection governance --get
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
curl -X POST http://127.0.0.1:8000/workflows/run -H "Content-Type: application/json" -d "{\"goal\":\"Assess compliance obligations and risks under ISO 37301\"}"
```

The response contains the selected workflow and lifecycle events:

```json
{
    "workflow": "iso37301_compliance",
    "status": "TASK_COMPLETED",
    "events": ["TASK_STARTED", "THOUGHT_START", "THOUGHT_COMPLETE", "TASK_COMPLETED"]
}
```

The current API runs workflows synchronously and stores task results in memory. It is intended as a working development backend before adding a database, background workers, authentication, and real model providers.

## 10) Add user documents to Workflow RAG

The ISO 37301 CSV is Governance RAG. User-provided domain documents belong in Workflow RAG. Add an HR document to the active workflow:

```cmd
curl -X POST http://127.0.0.1:8000/knowledge/workflow -H "Content-Type: application/json" -d "{\"workflow\":\"iso37301_compliance\",\"source\":\"hr-handbook.txt\",\"content\":\"HR onboarding requires identity verification, manager approval, and access review before account creation.\"}"
```

Query the uploaded document:

```cmd
curl "http://127.0.0.1:8000/knowledge/workflow/iso37301_compliance?query=HR%20onboarding%20identity%20approval"
```

The next workflow run combines this HR knowledge from `workflows` with ISO 37301 requirements from `governance`.
