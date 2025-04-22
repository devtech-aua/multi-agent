import httpx
from typing import Any, Dict, Optional
import json
from common.types import (
    AgentCard, 
    GetTaskRequest, 
    GetTaskResponse, 
    SendTaskRequest, 
    SendTaskResponse, 
    CancelTaskRequest, 
    CancelTaskResponse, 
    JSONRPCRequest, 
    JSONRPCResponse
)


class A2AClient:
    def __init__(self, agent_card: Optional[AgentCard] = None, url: Optional[str] = None):
        if agent_card:
            self.url = agent_card.url
        elif url:
            self.url = url
        else:
            raise ValueError("Must provide either agent_card or url")
    
    async def send_task(self, payload: Dict[str, Any]) -> SendTaskResponse:
        request = SendTaskRequest(params=payload)
        return SendTaskResponse.model_validate(await self._send_request(request))
    
    async def get_task(self, payload: Dict[str, Any]) -> GetTaskResponse:
        request = GetTaskRequest(params=payload)
        return GetTaskResponse.model_validate(await self._send_request(request))
    
    async def cancel_task(self, payload: Dict[str, Any]) -> CancelTaskResponse:
        request = CancelTaskRequest(params=payload)
        return CancelTaskResponse.model_validate(await self._send_request(request))
    
    async def _send_request(self, request: JSONRPCRequest) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.url, json=request.model_dump(), timeout=30
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise Exception(f"HTTP error: {e.response.status_code} - {e}")
            except json.JSONDecodeError as e:
                raise Exception(f"JSON parse error: {e}")


async def get_agent_card(url: str) -> AgentCard:
    """Fetch an agent card from the well-known URL."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{url}/.well-known/agent.json")
            response.raise_for_status()
            data = response.json()
            return AgentCard.model_validate(data)
        except httpx.HTTPStatusError as e:
            raise Exception(f"Failed to get agent card: {e.response.status_code} - {e}")
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse agent card: {e}")
