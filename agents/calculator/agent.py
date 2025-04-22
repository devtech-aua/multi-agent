import asyncio
import re
import uvicorn
from common.types import (
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    Task,
    TaskState,
    Message,
    TextPart
)
from common.server import A2AServer


# Define the agent's capabilities
calculator_card = AgentCard(
    name="Calculator Agent",
    description="A simple calculator agent that can perform basic arithmetic operations",
    url="http://localhost:8001",
    provider=AgentProvider(
        organization="A2A Demo",
        url="https://example.com"
    ),
    version="1.0.0",
    capabilities=AgentCapabilities(
        streaming=False,
        pushNotifications=False,
        stateTransitionHistory=False
    ),
    skills=[
        AgentSkill(
            id="add",
            name="Addition",
            description="Adds two numbers"
        ),
        AgentSkill(
            id="subtract",
            name="Subtraction",
            description="Subtracts two numbers"
        ),
        AgentSkill(
            id="multiply", 
            name="Multiplication",
            description="Multiplies two numbers"
        ),
        AgentSkill(
            id="divide",
            name="Division",
            description="Divides two numbers"
        )
    ]
)


# Define the calculate function that handles arithmetic operations
def calculate(expression):
    # Remove non-alphanumeric characters except +-*/().
    cleaned_expr = re.sub(r'[^0-9+\-*/().\s]', '', expression)
    
    try:
        # Using eval for simplicity, but in a real application you should use a safer method
        result = eval(cleaned_expr)
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating: {str(e)}"


# Define the task handler
async def handle_task(task: Task) -> Task:
    if not task.messages:
        task.state = TaskState.FAILED
        task.error = "No messages provided"
        return task
    
    # Get the latest user message
    last_message = task.messages[-1]
    if last_message.role != "user":
        task.state = TaskState.FAILED
        task.error = "Expected a user message"
        return task
    
    # Extract the text from the message parts
    query = ""
    for part in last_message.parts:
        if part.type == "text":
            query += part.text
    
    # Process the query
    result = calculate(query)
    
    # Create a response message
    response = Message(
        role="agent",
        parts=[TextPart(text=result)]
    )
    
    # Add the response to the task
    task.messages.append(response)
    task.state = TaskState.COMPLETED
    
    return task


# Create and run the server
server = A2AServer(calculator_card, handle_task)

if __name__ == "__main__":
    uvicorn.run(server.app, host="0.0.0.0", port=8001)
