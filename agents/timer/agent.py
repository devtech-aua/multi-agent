import asyncio
import uvicorn
import re
from datetime import datetime, timedelta
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
timer_card = AgentCard(
    name="Timer Agent",
    description="A simple agent that provides timer functionality",
    url="http://localhost:8004",
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
            id="time-now",
            name="Current Time",
            description="Returns the current time"
        ),
        AgentSkill(
            id="set-timer",
            name="Set Timer",
            description="Sets a timer for a specified duration (simulated)"
        ),
        AgentSkill(
            id="countdown",
            name="Countdown",
            description="Shows a countdown for a specified number of seconds (simulated)"
        )
    ]
)

# Define the timer functions
def get_current_time():
    now = datetime.now()
    return f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}"

def set_timer(duration_str):
    # Parse the duration string
    pattern = r'(\d+)\s*(m(?:in(?:ute)?s?)?|s(?:ec(?:ond)?s?)?|h(?:(?:ou)?rs?)?)'
    
    matches = re.findall(pattern, duration_str, re.IGNORECASE)
    if not matches:
        return "Invalid duration format. Please use a format like '5m', '30s', or '1h'."
    
    total_seconds = 0
    for value, unit in matches:
        value = int(value)
        if unit.startswith('h'):
            total_seconds += value * 3600
        elif unit.startswith('m'):
            total_seconds += value * 60
        elif unit.startswith('s'):
            total_seconds += value
    
    if total_seconds <= 0:
        return "Duration must be greater than zero."
    
    now = datetime.now()
    end_time = now + timedelta(seconds=total_seconds)
    
    # In a real implementation, you'd actually start a timer here
    # For this demo, we'll just return when the timer would end
    return f"Timer set for {format_duration(total_seconds)}. It would end at {end_time.strftime('%H:%M:%S')}."

def countdown(seconds_str):
    try:
        seconds = int(seconds_str)
        if seconds <= 0 or seconds > 60:
            return "Please provide a positive number of seconds (max 60)."
        
        # In a real implementation, you'd actually perform a countdown
        # For this demo, we'll just simulate it
        return f"Countdown from {seconds}: {', '.join(str(i) for i in range(seconds, 0, -1))}, 0!"
    except ValueError:
        return "Invalid number of seconds. Please provide a number."

def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds > 0 or not parts:
        parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
    
    return " and ".join(parts)

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
    
    if query == "time" or query == "what time is it" or query == "now":
        result = get_current_time()
    elif query.startswith("timer ") or query.startswith("set timer "):
        if query.startswith("set timer "):
            duration = query.replace("set timer ", "", 1).strip()
        else:
            duration = query.replace("timer ", "", 1).strip()
        result = set_timer(duration)
    elif query.startswith("countdown "):
        seconds = query.replace("countdown ", "", 1).strip()
        result = countdown(seconds)
    else:
        result = "Invalid command. Available commands: 'time', 'timer [duration]', 'countdown [seconds]'."
    
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
server = A2AServer(timer_card, handle_task)

if __name__ == "__main__":
    uvicorn.run(server.app, host="0.0.0.0", port=8004)
