from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional, Callable, Awaitable, List
import json
import uuid
from common.types import (
    AgentCard,
    Task,
    TaskState,
    Message,
    TextPart,
    JSONRPCRequest,
    JSONRPCResponse,
    GetTaskRequest,
    SendTaskRequest,
    CancelTaskRequest
)


class A2AServer:
    def __init__(
        self,
        agent_card: AgentCard,
        task_handler: Callable[[Task], Awaitable[Task]],
    ):
        self.agent_card = agent_card
        self.task_handler = task_handler
        self.tasks: Dict[str, Task] = {}
        self.app = FastAPI()
        
        @self.app.get("/.well-known/agent.json")
        async def get_agent_card():
            return self.agent_card.model_dump(exclude_none=True)
        
        @self.app.post("/")
        async def handle_request(request: Request):
            try:
                body = await request.json()
                
                # Parse JSON-RPC request
                if "method" not in body:
                    return JSONResponse(
                        status_code=400,
                        content={"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": None}
                    )
                
                method = body["method"]
                
                if method == "tasks/get":
                    return await self._handle_get_task(body)
                elif method == "tasks/send":
                    return await self._handle_send_task(body)
                elif method == "tasks/cancel":
                    return await self._handle_cancel_task(body)
                else:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "jsonrpc": "2.0",
                            "error": {"code": -32601, "message": f"Method '{method}' not found"},
                            "id": body.get("id")
                        }
                    )
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=400,
                    content={"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None}
                )
            except Exception as e:
                return JSONResponse(
                    status_code=500,
                    content={
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                        "id": body.get("id", None)
                    }
                )
    
    async def _handle_get_task(self, request_data: Dict[str, Any]) -> JSONResponse:
        try:
            request = GetTaskRequest.model_validate(request_data)
            task_id = request.params.get("taskId")
            
            if not task_id or task_id not in self.tasks:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "error": {"code": -32001, "message": "Task not found"},
                        "id": request.id
                    }
                )
            
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "result": {"task": self.tasks[task_id].model_dump(exclude_none=True)},
                    "id": request.id
                }
            )
        except Exception as e:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                    "id": request_data.get("id")
                }
            )
    
    async def _handle_send_task(self, request_data: Dict[str, Any]) -> JSONResponse:
        try:
            request = SendTaskRequest.model_validate(request_data)
            task_id = request.params.get("taskId", str(uuid.uuid4()))
            
            # Check if this is a new task or an update to an existing task
            if task_id in self.tasks:
                # Update existing task with new message
                task = self.tasks[task_id]
                
                # Add the new message
                if "message" in request.params:
                    message_data = request.params["message"]
                    parts = [TextPart(text=part["text"]) if part["type"] == "text" else part 
                             for part in message_data.get("parts", [])]
                    
                    message = Message(
                        role=message_data.get("role", "user"),
                        parts=parts
                    )
                    task.messages.append(message)
                
                # Update task state to working
                task.state = TaskState.WORKING
            else:
                # Create a new task
                initial_message = None
                if "message" in request.params:
                    message_data = request.params["message"]
                    parts = [TextPart(text=part["text"]) if part["type"] == "text" else part 
                             for part in message_data.get("parts", [])]
                    
                    initial_message = Message(
                        role=message_data.get("role", "user"),
                        parts=parts
                    )
                
                task = Task(
                    id=task_id,
                    state=TaskState.SUBMITTED,
                    messages=[initial_message] if initial_message else [],
                    artifacts=[]
                )
                self.tasks[task_id] = task
            
            # Process the task
            result_task = await self.task_handler(task)
            self.tasks[task_id] = result_task
            
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "result": {"task": result_task.model_dump(exclude_none=True)},
                    "id": request.id
                }
            )
        except Exception as e:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                    "id": request_data.get("id")
                }
            )
    
    async def _handle_cancel_task(self, request_data: Dict[str, Any]) -> JSONResponse:
        try:
            request = CancelTaskRequest.model_validate(request_data)
            task_id = request.params.get("taskId")
            
            if not task_id or task_id not in self.tasks:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "error": {"code": -32001, "message": "Task not found"},
                        "id": request.id
                    }
                )
            
            # Cancel the task
            task = self.tasks[task_id]
            task.state = TaskState.CANCELED
            
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "result": {"task": task.model_dump(exclude_none=True)},
                    "id": request.id
                }
            )
        except Exception as e:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                    "id": request_data.get("id")
                }
            )
