import asyncio
import logging
from typing import AsyncGenerator, List, Dict, Any, Optional
from core.types import (
    AgentState, HarnessConfig, StepResult, Event, EventType, ToolCall
)
from engines.task_runtime import TaskRuntime
from engines.context_engine import ContextEngine
from engines.model_gateway import ModelGateway
from engines.state_memory import MemoryEngine
from engines.rag_engine import RAGEngine
from tools.base import ToolRuntime
from core.control_plane import ControlPlane
from observability.tracer import Tracer

logger = logging.getLogger(__name__)

class AgentHarness:
    def __init__(
        self,
        config: HarnessConfig,
        rag_engine: Optional[RAGEngine] = None,
        workflow_name: Optional[str] = None,
        workflow_collection: str = "workflows",
        governance_collection: str = "governance",
    ):
        self.config = config
        self.task_runtime = TaskRuntime()
        self.context_engine = ContextEngine(max_tokens=config.max_context_tokens)
        self.model_gateway = ModelGateway(providers=config.providers)
        self.tool_runtime = ToolRuntime(allowed_tools=config.allowed_tools)
        self.memory = MemoryEngine(storage_uri=config.memory_uri)
        self.rag_engine = rag_engine or RAGEngine()
        self.workflow_name = workflow_name
        self.workflow_collection = workflow_collection
        self.governance_collection = governance_collection
        self.control_plane = ControlPlane(
            max_steps=config.max_steps, 
            require_approval_for=config.approval_tools
        )
        self.tracer = Tracer()
        self.state = AgentState.IDLE

    async def run(self, user_goal: str) -> AsyncGenerator[Event, None]:
        """Main Agent Harness execution loop."""
        self.state = AgentState.RUNNING
        task = await self.task_runtime.initialize_task(user_goal)
        yield Event(type=EventType.TASK_STARTED, payload={"task_id": task.id, "goal": user_goal})

        step_count = 0

        try:
            while self.state == AgentState.RUNNING:
                step_count += 1
                
                # 1. CONTROL PLANE: Enforce step limits and budget guardrails
                self.control_plane.validate_step_limit(step_count)
                
                # 2. CONTEXT ENGINE: Build optimized prompt context
                workflow_knowledge = await self.rag_engine.retrieve(
                    query=user_goal,
                    collection=self.workflow_collection,
                    where={"workflow": self.workflow_name} if self.workflow_name else None,
                )
                if self.workflow_name:
                    governance_knowledge = await self.rag_engine.retrieve_workflow_governance(
                        query=user_goal,
                        collection=self.governance_collection,
                        workflow_name=self.workflow_name,
                    )
                else:
                    governance_knowledge = await self.rag_engine.retrieve(
                        query=user_goal,
                        collection=self.governance_collection,
                    )
                working_context = await self.context_engine.assemble_context(
                    task=task,
                    memory=await self.memory.retrieve_relevant(user_goal),
                    system_prompt=self.config.system_prompt,
                    workflow_knowledge=workflow_knowledge,
                    governance_knowledge=governance_knowledge,
                )

                # 3. MODEL GATEWAY: Call LLM with routing and fallbacks
                yield Event(type=EventType.THOUGHT_START, payload={"step": step_count})
                response = await self.model_gateway.generate_completion(
                    messages=working_context,
                    tools=self.tool_runtime.get_schemas()
                )
                yield Event(type=EventType.THOUGHT_COMPLETE, payload={"content": response.text})

                # 4. TASK TERMINATION CHECK
                if response.is_complete:
                    self.state = AgentState.COMPLETED
                    await self.task_runtime.mark_complete(task.id, response.text)
                    yield Event(type=EventType.TASK_COMPLETED, payload={"result": response.text})
                    break

                # 5. TOOL RUNTIME & CONTROL PLANE APPROVALS
                for tool_call in response.tool_calls:
                    allowed, reason = self.control_plane.check_tool_policy(
                        tool_call, self.config.allowed_tools
                    )
                    if not allowed:
                        await self.context_engine.add_observation(tool_call.id, reason)
                        yield Event(
                            type=EventType.TOOL_CALL_REJECTED,
                            payload={"tool": tool_call.name, "reason": reason},
                        )
                        continue

                    # Governance & Approval check
                    approved = await self.control_plane.request_approval_if_needed(tool_call)
                    if not approved:
                        observation = "Error: Tool execution rejected by Control Plane safety policy."
                        await self.context_engine.add_observation(tool_call.id, observation)
                        yield Event(
                            type=EventType.TOOL_CALL_REJECTED,
                            payload={"tool": tool_call.name, "reason": observation},
                        )
                        continue

                    # Execute tool safely
                    yield Event(type=EventType.TOOL_CALL_START, payload={"tool": tool_call.name, "args": tool_call.args})
                    tool_result = await self.tool_runtime.execute(tool_call)
                    
                    # 6. OBSERVATION & STATE UPDATE
                    await self.context_engine.add_observation(tool_call.id, tool_result.output)
                    await self.memory.save_working_memory(tool_call.name, tool_result.output)
                    
                    yield Event(
                        type=EventType.TOOL_CALL_COMPLETE, 
                        payload={"tool": tool_call.name, "output": tool_result.output}
                    )

        except Exception as exc:
            self.state = AgentState.FAILED
            logger.error(f"Harness failure at step {step_count}: {str(exc)}", exc_info=True)
            yield Event(type=EventType.TASK_FAILED, payload={"error": str(exc)})
        finally:
            await self.tracer.flush()