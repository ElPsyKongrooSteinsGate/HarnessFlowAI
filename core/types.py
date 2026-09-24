from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class AgentState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EventType(str, Enum):
    TASK_STARTED = "TASK_STARTED"
    THOUGHT_START = "THOUGHT_START"
    THOUGHT_COMPLETE = "THOUGHT_COMPLETE"
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_COMPLETE = "TOOL_CALL_COMPLETE"
    TOOL_CALL_REJECTED = "TOOL_CALL_REJECTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"


class WorkflowState(str, Enum):
    RECEIVED = "RECEIVED"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"


class ToolCall(BaseModel):
    id: str
    name: str
    args: Dict[str, Any]


class Event(BaseModel):
    type: EventType
    payload: Dict[str, Any]


class HarnessConfig(BaseModel):
    system_prompt: str = "You are a helpful coding agent."
    max_steps: int = 30
    max_context_tokens: int = 128000
    providers: List[str] = ["claude-3-5-sonnet", "gpt-4o"]
    allowed_tools: List[str] = []
    approval_tools: List[str] = ["terminal_execute"]
    memory_uri: str = "sqlite:///memory.db"


class WorkflowStep(BaseModel):
    name: str
    description: str = ""
    required_approval: bool = False


class WorkflowDefinition(BaseModel):
    name: str
    description: str
    capabilities: List[str] = []
    steps: List[WorkflowStep] = []
    allowed_tools: List[str] = []
    approval_tools: List[str] = []
    max_steps: int = 30
    system_prompt: str = "You are a business process agent."


class StepResult(BaseModel):
    step: int
    status: str = "pending"
    output: str = ""
    error: Optional[str] = None


class TaskRecord(BaseModel):
    id: str
    goal: str
    status: str = "pending"
    result: Optional[str] = None