from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class TaskState(str, Enum):
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class AgentCapabilities(BaseModel):
    streaming: bool = False
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


class AgentProvider(BaseModel):
    organization: str
    url: Optional[str] = None


class AgentSkill(BaseModel):
    id: str
    name: str
    description: Optional[str] = None


class AgentAuthentication(BaseModel):
    schemes: List[str]
    credentials: Optional[str] = None


class AgentCard(BaseModel):
    name: str
    description: Optional[str] = None
    url: str
    provider: Optional[AgentProvider] = None
    version: str
    documentationUrl: Optional[str] = None
    capabilities: AgentCapabilities
    authentication: Optional[AgentAuthentication] = None
    defaultInputModes: List[str] = ["text"]
    defaultOutputModes: List[str] = ["text"]
    skills: List[AgentSkill]


class TextPart(BaseModel):
    text: str
    type: str = "text"


class Message(BaseModel):
    role: str
    parts: List[TextPart]


class Artifact(BaseModel):
    id: str
    mimeType: str
    parts: List[Any]


class Task(BaseModel):
    id: str
    state: TaskState
    messages: List[Message] = []
    artifacts: List[Artifact] = []
    error: Optional[str] = None


class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any]
    id: Optional[Union[str, int]] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None


class GetTaskRequest(JSONRPCRequest):
    method: str = "tasks/get"


class GetTaskResponse(JSONRPCResponse):
    result: Optional[Dict[str, Any]] = None


class SendTaskRequest(JSONRPCRequest):
    method: str = "tasks/send"


class SendTaskResponse(JSONRPCResponse):
    result: Optional[Dict[str, Any]] = None


class CancelTaskRequest(JSONRPCRequest):
    method: str = "tasks/cancel"


class CancelTaskResponse(JSONRPCResponse):
    result: Optional[Dict[str, Any]] = None
