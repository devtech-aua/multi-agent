import os
import sys
import subprocess
import time
import signal
import argparse

# Define the agent processes to run
AGENTS = [
    {
        "name": "Coordinator Agent",
        "module": "agents.coordinator.agent",
        "port": 8000
    },
    {
        "name": "Calculator Agent",
        "module": "agents.calculator.agent",
        "port": 8001
    },
    {
        "name": "Translator Agent",
        "module": "agents.translator.agent",
        "port": 8002
    },
    {
        "name": "Weather Agent",
        "module": "agents.weather.agent",
        "port": 8003
    },
    {
        "name": "Timer Agent",
        "module": "agents.timer.agent",
        "port": 8004
    }
]

def run_agents():
    """Start all agent processes."""
    print("Starting A2A Demo agents...")
    
    # Keep track of all processes
    processes = []
    
    try:
        # Start each agent in a separate process
        for agent in AGENTS:
            print(f"Starting {agent['name']} on port {agent['port']}...")
            process = subprocess.Popen(
                [sys.executable, "-m", agent["module"]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            processes.append(process)
            # Give it a moment to start up
            time.sleep(1)
        
        print("\nAll agents started successfully!")
        print("\nPress Ctrl+C to stop all agents and exit\n")
        
        # Wait for user to press Ctrl+C
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nStopping all agents...")
    finally:
        # Stop all processes
        for process in processes:
            process.terminate()
        
        # Wait for processes to terminate
        for process in processes:
            process.wait()
        
        print("All agents stopped. Exiting.")

def run_client():
    """Run the client application."""
    subprocess.run([sys.executable, "-m", "client.client"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A2A Demo Runner")
    parser.add_argument("--client-only", action="store_true", help="Run only the client")
    parser.add_argument("--agents-only", action="store_true", help="Run only the agents")
    
    args = parser.parse_args()
    
    if args.client_only:
        run_client()
    elif args.agents_only:
        run_agents()
    else:
        # Default: run both in separate processes
        print("Starting both agents and client...")
        
        # Start agents in a separate process
        agents_process = subprocess.Popen(
            [sys.executable, __file__, "--agents-only"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give agents time to start up
        time.sleep(5)
        
        try:
            # Run client in main process
            run_client()
        finally:
            # Stop agents process when client exits
            agents_process.terminate()
            agents_process.wait()
