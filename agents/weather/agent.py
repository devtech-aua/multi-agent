import asyncio
import uvicorn
from datetime import datetime
import random
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

# Mock weather data for demo purposes
weather_data = {
    "new york": {"temp_c": lambda: random.randint(15, 25), "condition": "Partly Cloudy"},
    "london": {"temp_c": lambda: random.randint(10, 18), "condition": "Rainy"},
    "tokyo": {"temp_c": lambda: random.randint(20, 30), "condition": "Sunny"},
    "paris": {"temp_c": lambda: random.randint(12, 22), "condition": "Clear"},
    "sydney": {"temp_c": lambda: random.randint(18, 28), "condition": "Sunny"},
    "berlin": {"temp_c": lambda: random.randint(10, 20), "condition": "Cloudy"},
    "moscow": {"temp_c": lambda: random.randint(0, 10), "condition": "Snowy"},
    "dubai": {"temp_c": lambda: random.randint(30, 40), "condition": "Hot"},
    "mumbai": {"temp_c": lambda: random.randint(25, 35), "condition": "Humid"},
    "rio de janeiro": {"temp_c": lambda: random.randint(22, 32), "condition": "Sunny"}
}

# Define the agent's capabilities
weather_card = AgentCard(
    name="Weather Agent",
    description="A simple agent that provides weather information for cities",
    url="http://localhost:8003",
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
            id="get-weather",
            name="Get Weather",
            description="Gets the current weather for a specified city"
        ),
        AgentSkill(
            id="list-cities",
            name="List Cities",
            description="Lists the cities available in the weather service"
        )
    ]
)

# Define the weather functions
def get_weather(city):
    city = city.lower()
    if city in weather_data:
        temp = weather_data[city]["temp_c"]()
        condition = weather_data[city]["condition"]
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"Weather for {city.title()} at {current_time}:\nTemperature: {temp}°C\nCondition: {condition}"
    else:
        return f"Weather data for {city} is not available. Use 'list-cities' to see available cities."

def list_cities():
    cities = sorted(city.title() for city in weather_data.keys())
    return "Available cities:\n" + "\n".join(cities)

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
    
    if query == "list-cities":
        result = list_cities()
    elif query.startswith("weather "):
        city = query.replace("weather ", "", 1).strip()
        result = get_weather(city)
    else:
        result = "Invalid command. Use 'weather [city]' to get weather or 'list-cities' to see available cities."
    
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
server = A2AServer(weather_card, handle_task)

if __name__ == "__main__":
    uvicorn.run(server.app, host="0.0.0.0", port=8003)
