import asyncio
import uvicorn
import re
from typing import Dict
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
from common.client import A2AClient, get_agent_card

# Define the agent's capabilities
coordinator_card = AgentCard(
    name="Coordinator Agent",
    description="A coordinator agent that routes requests to specialized agents",
    url="http://localhost:8000",
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
            id="route",
            name="Route",
            description="Routes requests to the appropriate agent"
        ),
        AgentSkill(
            id="help",
            name="Help",
            description="Lists available agents and their capabilities"
        )
    ]
)

# Define the agent URLs
AGENT_URLS = {
    "calculator": "http://localhost:8001",
    "translator": "http://localhost:8002",
    "weather": "http://localhost:8003",
    "timer": "http://localhost:8004"
}

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
    query = query.strip().lower()
    
    if query == "help":
        # Generate help message with available agents and commands
        result = await get_help()
    else:
        # Identify which agent should handle this request
        target_agent, cleaned_query = identify_agent(query)
        
        if target_agent:
            # Forward the request to the target agent
            result = await forward_request(target_agent, cleaned_query)
        else:
            result = (
                "I'm not sure which agent can help with that. "
                "Please try one of these formats:\n"
                "- calculate: [expression]\n"
                "- translate en-es: [text]\n"
                "- weather [city]\n"
                "- timer [duration]\n"
                "Or type 'help' for more information."
            )
    
    # Create a response message
    response = Message(
        role="agent",
        parts=[TextPart(text=result)]
    )
    
    # Add the response to the task
    task.messages.append(response)
    task.state = TaskState.COMPLETED
    
    return task

def identify_agent(query):
    """Identify which agent should handle the query."""
    query = query.lower()
    
    # Calculator patterns
    calc_patterns = [r'^\s*calculate\s*:', r'^\s*calc\s*:', r'^\s*[\d\(\)\+\-\*/\s\.]+$']
    for pattern in calc_patterns:
        if re.match(pattern, query):
            cleaned = query.split(':', 1)[-1].strip() if ':' in query else query
            return "calculator", cleaned
    
    # Translator patterns
    if re.match(r'^\s*translate\s+[a-z]{2}-[a-z]{2}\s*:', query):
        return "translator", query
    
    # Weather patterns
    if query.startswith("weather ") or query == "list-cities":
        return "weather", query
    
    # Timer patterns
    timer_patterns = [
        r'^\s*what\s+time\s+is\s+it\s*$',
        r'^\s*time\s*$',
        r'^\s*now\s*$',
        r'^\s*(set\s+)?timer\s+.*$',
        r'^\s*countdown\s+\d+\s*$'
    ]
    for pattern in timer_patterns:
        if re.match(pattern, query):
            return "timer", query
    
    # No match found
    return None, query

async def forward_request(agent_name, query):
    """Forward the request to the specified agent."""
    try:
        client = A2AClient(url=AGENT_URLS[agent_name])
        response = await client.send_task({
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": query}]
            }
        })
        
        # Extract the response from the agent
        if response.result and "task" in response.result:
            task = response.result["task"]
            if task.get("messages", []) and len(task["messages"]) > 0:
                agent_message = task["messages"][-1]
                if agent_message.get("role") == "agent" and agent_message.get("parts", []):
                    return agent_message["parts"][0]["text"]
        
        return f"Error: Received malformed response from {agent_name} agent."
    except Exception as e:
        return f"Error communicating with {agent_name} agent: {str(e)}"

async def get_help():
    """Generate a help message listing all available agents and their capabilities."""
    help_text = "# Available Agents\n\n"
    
    for agent_name, url in AGENT_URLS.items():
        try:
            card = await get_agent_card(url)
            help_text += f"## {card.name}\n"
            if card.description:
                help_text += f"{card.description}\n\n"
                
            help_text += "### Skills:\n"
            for skill in card.skills:
                help_text += f"- **{skill.name}**: {skill.description or 'No description'}\n"
            
            help_text += "\n"
        except Exception as e:
            help_text += f"## {agent_name.title()} Agent\nError fetching agent information: {str(e)}\n\n"
    
    help_text += (
        "# Usage Examples\n\n"
        "- Calculator: `calculate: 2 + 2 * 3`\n"
        "- Translator: `translate en-es: hello`\n"
        "- Weather: `weather london` or `list-cities`\n"
        "- Timer: `time`, `timer 5m`, or `countdown 10`\n"
    )
    
    return help_text

# Create and run the server
server = A2AServer(coordinator_card, handle_task)

if __name__ == "__main__":
    uvicorn.run(server.app, host="0.0.0.0", port=8000)
