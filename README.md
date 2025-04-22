# A2A Multi-Agent Demo

This is a sample application demonstrating the Agent-to-Agent (A2A) protocol with 5 different agents that can communicate with each other.

## Agents

1. **Coordinator Agent** - The main entry point that routes requests to specialized agents
2. **Calculator Agent** - Performs basic arithmetic operations
3. **Translator Agent** - Translates between languages (English to Spanish/French)
4. **Weather Agent** - Provides weather information for various cities
5. **Timer Agent** - Provides time-related functions

## Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Demo

To start all agents and the client, simply run:

```bash
python run.py
```

This will:
1. Start all five agents in the background
2. Launch the interactive client

You can also:
- Start only the agents: `python run.py --agents-only`
- Start only the client: `python run.py --client-only`

## Usage Examples

Once the interactive client is running, you can try these commands:

- **Get Help**:
  ```
  help
  ```

- **Calculator**:
  ```
  calculate: 2 + 2 * 3
  calc: (5+3)/2
  5 * 4 - 2
  ```

- **Translator**:
  ```
  translate en-es: hello
  translate en-fr: thank you
  ```

- **Weather**:
  ```
  list-cities
  weather london
  weather tokyo
  ```

- **Timer**:
  ```
  time
  timer 5m
  countdown 10
  ```

## Project Structure

```
a2a_demo/
├── agents/
│   ├── calculator/
│   │   └── agent.py
│   ├── coordinator/
│   │   └── agent.py
│   ├── timer/
│   │   └── agent.py
│   ├── translator/
│   │   └── agent.py
│   └── weather/
│       └── agent.py
├── client/
│   └── client.py
├── common/
│   ├── __init__.py
│   ├── client.py
│   ├── server.py
│   └── types.py
├── run.py
├── requirements.txt
└── README.md
```

## A2A Protocol Implementation

This demo implements a simplified version of the A2A protocol with:

- Agent Cards for capability discovery
- Task-based communication
- Message passing with text parts
- Well-known endpoint for agent discovery

Each agent exposes an HTTP endpoint that follows the JSON-RPC 2.0 format for requests and responses.

## Notes

- This is a simplified demo meant for educational purposes
- The implementation uses mock data for services like weather and translation
- In a production environment, you would use proper authentication, error handling, and actual service integrations
# multi-agent
