import asyncio
import argparse
import uuid
from common.client import A2AClient, get_agent_card
from common.types import TextPart

COORDINATOR_URL = "http://localhost:8000"

async def send_message(message):
    """Send a message to the coordinator agent and print the response."""
    try:
        # Create a client for the coordinator agent
        client = A2AClient(url=COORDINATOR_URL)
        
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
        
        # Extract and print the response
        if response.result and "task" in response.result:
            task = response.result["task"]
            
            # Find the agent's response message
            agent_messages = [m for m in task.get("messages", []) if m.get("role") == "agent"]
            if agent_messages:
                last_message = agent_messages[-1]
                for part in last_message.get("parts", []):
                    if part.get("type") == "text":
                        print(f"\n{part['text']}\n")
                        return
            
            print("\nNo response received from agent.\n")
        else:
            print(f"\nError: Unexpected response format.\n")
    
    except Exception as e:
        print(f"\nError: {str(e)}\n")

async def interactive_mode():
    """Run an interactive session with the coordinator agent."""
    print("\n===== A2A Demo Multi-Agent System =====")
    print("Type 'exit' or 'quit' to end the session")
    print("Type 'help' to see available agents and commands")
    print("=========================================\n")
    
    while True:
        try:
            # Get user input
            user_input = input("You: ")
            
            # Check if the user wants to exit
            if user_input.lower() in ["exit", "quit"]:
                print("\nGoodbye!\n")
                break
            
            # Send the message to the coordinator agent
            print("\nAgent:", end=" ")
            await send_message(user_input)
            
        except KeyboardInterrupt:
            print("\n\nSession terminated by user.\n")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A2A Demo Client")
    parser.add_argument("--message", help="Send a single message and exit")
    
    args = parser.parse_args()
    
    if args.message:
        # Single message mode
        asyncio.run(send_message(args.message))
    else:
        # Interactive mode
        asyncio.run(interactive_mode())
