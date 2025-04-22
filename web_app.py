import asyncio
import os
import subprocess
import signal
import time
import uvicorn
import json
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any

from common.client import A2AClient

# Initialize FastAPI app
app = FastAPI()

# Initialize templates
templates = Jinja2Templates(directory="templates")

# Store running agent processes
agent_processes = []

# Store WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Define agent configuration
AGENTS = [
    {
        "name": "Coordinator Agent",
        "module": "agents.coordinator.agent",
        "port": 8000,
        "url": "http://localhost:8000"
    },
    {
        "name": "Calculator Agent",
        "module": "agents.calculator.agent",
        "port": 8001,
        "url": "http://localhost:8001"
    },
    {
        "name": "Translator Agent",
        "module": "agents.translator.agent",
        "port": 8002,
        "url": "http://localhost:8002"
    },
    {
        "name": "Weather Agent",
        "module": "agents.weather.agent",
        "port": 8003,
        "url": "http://localhost:8003"
    },
    {
        "name": "Timer Agent",
        "module": "agents.timer.agent",
        "port": 8004,
        "url": "http://localhost:8004"
    }
]

# Function to start all agents
def start_agents():
    global agent_processes
    
    print("Starting A2A Demo agents...")
    
    for agent in AGENTS:
        print(f"Starting {agent['name']} on port {agent['port']}...")
        process = subprocess.Popen(
            ["python3", "-m", agent["module"]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        agent_processes.append(process)
        # Give it a moment to start up
        time.sleep(1)
    
    print("All agents started successfully!")

# Function to stop all agents
def stop_agents():
    global agent_processes
    
    print("Stopping all agents...")
    
    for process in agent_processes:
        process.terminate()
    
    # Wait for processes to terminate
    for process in agent_processes:
        process.wait()
    
    agent_processes = []
    print("All agents stopped.")

# Start agents when the application starts
@app.on_event("startup")
async def startup_event():
    start_agents()

# Stop agents when the application shuts down
@app.on_event("shutdown")
async def shutdown_event():
    stop_agents()

# Serve HTML
@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse the received data
            request_data = json.loads(data)
            message = request_data.get("message", "")
            
            # Process the message through the coordinator agent
            response = await process_message(message)
            
            # Send the response back to the client
            await manager.send_personal_message(json.dumps({
                "sender": "agent",
                "message": response
            }), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Process message through coordinator agent
async def process_message(message: str) -> str:
    try:
        # Create a client for the coordinator agent
        client = A2AClient(url=AGENTS[0]["url"])
        
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Create and send the task
        response = await client.send_task({
            "taskId": task_id,
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": message}]
            }
        })
        
        # Extract and return the response
        if response.result and "task" in response.result:
            task = response.result["task"]
            
            # Find the agent's response message
            agent_messages = [m for m in task.get("messages", []) if m.get("role") == "agent"]
            if agent_messages:
                last_message = agent_messages[-1]
                for part in last_message.get("parts", []):
                    if part.get("type") == "text":
                        return part["text"]
        
        return "No response received from agent."
    
    except Exception as e:
        return f"Error: {str(e)}"

# Create directories for templates and static files
os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8089)
    except KeyboardInterrupt:
        stop_agents()
