from pydantic import BaseModel
from typing import List, Optional, TypedDict
from enum import Enum
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    State for the Country Information Agent.
    """
    messages: List[BaseMessage]
    country: Optional[str]
    intent_fields: Optional[List[str]]
    api_response: Optional[dict]
    error: Optional[str]
    retry_count: int
    validator_feedback: Optional[str]
    dynamic_instructions: Optional[str]

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str
    error: Optional[str] = None

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskUpdate(BaseModel):
    task_id: str
    status: TaskStatus
    thoughts: List[str] = []
    result: Optional[str] = None
    error: Optional[str] = None
