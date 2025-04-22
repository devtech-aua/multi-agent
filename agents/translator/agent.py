import asyncio
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

# Simple translation dictionary for demo purposes
translations = {
    "en-es": {
        "hello": "hola",
        "goodbye": "adiós",
        "thank you": "gracias",
        "please": "por favor",
        "yes": "sí",
        "no": "no",
        "how are you": "cómo estás",
        "good morning": "buenos días",
        "good afternoon": "buenas tardes",
        "good night": "buenas noches"
    },
    "en-fr": {
        "hello": "bonjour",
        "goodbye": "au revoir",
        "thank you": "merci",
        "please": "s'il vous plaît",
        "yes": "oui",
        "no": "non",
        "how are you": "comment allez-vous",
        "good morning": "bonjour",
        "good afternoon": "bon après-midi",
        "good night": "bonne nuit"
    }
}

# Define the agent's capabilities
translator_card = AgentCard(
    name="Translator Agent",
    description="A simple translator agent that can translate between languages",
    url="http://localhost:8002",
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
            id="translate-en-es",
            name="English to Spanish",
            description="Translates English to Spanish"
        ),
        AgentSkill(
            id="translate-en-fr",
            name="English to French",
            description="Translates English to French"
        )
    ]
)

# Define the translation function
def translate(text, source_lang, target_lang):
    lang_pair = f"{source_lang}-{target_lang}"
    
    if lang_pair not in translations:
        return f"Translation for {lang_pair} is not supported"
    
    # Convert to lowercase for lookup
    text_lower = text.lower()
    
    # Check if the phrase is in our dictionary
    if text_lower in translations[lang_pair]:
        return translations[lang_pair][text_lower]
    
    # For words that aren't in our dictionary, we'll just return the original
    # In a real implementation, you would use a proper translation service
    return f"No translation available for '{text}'"

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
    
    # Parse the command to get language pair and text
    try:
        # Expected format: "translate [source]-[target]: [text]"
        # e.g., "translate en-es: hello"
        command_parts = query.split(":", 1)
        
        if len(command_parts) < 2:
            raise ValueError("Invalid format. Expected 'translate [source]-[target]: [text]'")
        
        command = command_parts[0].strip()
        text_to_translate = command_parts[1].strip()
        
        # Extract language pair
        lang_pair = command.replace("translate", "").strip()
        source_lang, target_lang = lang_pair.split("-")
        
        # Translate the text
        result = translate(text_to_translate, source_lang, target_lang)
    except Exception as e:
        result = f"Error: {str(e)}\nExpected format: 'translate [source]-[target]: [text]'"
    
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
server = A2AServer(translator_card, handle_task)

if __name__ == "__main__":
    uvicorn.run(server.app, host="0.0.0.0", port=8002)
