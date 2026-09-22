import ollama
from datetime import datetime

# 1. TOOL FUNCTIONS

def calculator(a, b, operation):
    """Perform a mathematical operation on two numbers."""

    if operation == "add":
        return a + b

    elif operation == "subtract":
        return a - b

    elif operation == "multiply":
        return a * b

    elif operation == "divide":
        if b == 0:
            return "Error: cannot divide by zero"

        return a / b

    else:
        return "Error: unknown operation"


def get_current_time():
    """Return the current time as a string."""

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 2. TOOL REGISTRY

tool_registry = {
    "calculator": calculator,
    "get_current_time": get_current_time
}

# 3. TOOL DEFINITIONS FOR QWEN

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform basic mathematical operations on two numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "The first number"
                    },
                    "b": {
                        "type": "number",
                        "description": "The second number"
                    },
                    "operation": {
                        "type": "string",
                        "enum": [
                            "add",
                            "subtract",
                            "multiply",
                            "divide"
                        ],
                        "description": "The mathematical operation to perform"
                    }
                },
                "required": ["a", "b", "operation"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current local date and time.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

# 4. START AGENT

print("Simple AI Agent")
print("Type 'exit' to quit.\n")

# Conversation memory
messages = []

# 5. CHAT LOOP

while True:

    user_message = input("You: ")

    if user_message.lower() == "exit":
        print("Goodbye!")
        break

    # Add user message to conversation
    messages.append({
        "role": "user",
        "content": user_message
    })

    # 6. AGENT LOOP
    
    while True:

        print("\nThinking...")

        response = ollama.chat(
            model="qwen3:4b",
            messages=messages,
            tools=tools
        )
        
        # 7. DID QWEN REQUEST A TOOL?
        
        if response.message.tool_calls:

            # Store Qwen's tool request in conversation
            messages.append(response.message)


            # A model response can contain multiple tool calls
            for tool_call in response.message.tool_calls:

                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments

                print(f"Agent wants to use: {tool_name}")
                print(f"Arguments: {arguments}")

                # 8. LOOK UP TOOL IN REGISTRY                

                tool = tool_registry.get(tool_name)


                if tool is None:

                    print(f"Error: Tool '{tool_name}' not found.")

                    result = f"Error: Tool '{tool_name}' not found."


                else:

                    try:

                        result = tool(**arguments) # this automatically unpacks the arguments dictionary into keyword arguments for the tool function
                        # this above is also called generic tool execution because it does not care about argument or not ?
                    except Exception as e:
                        result = f"Tool error: {str(e)}"

                print(f"Tool result: {result}")
                
                # 10. GIVE TOOL RESULT BACK TO QWEN

                messages.append({
                    "role": "tool",
                    "content": str(result)
                })

            # Ask Qwen what to do next
            continue
        
        # 11. NO TOOL NEEDED
        
        messages.append({
            "role": "assistant",
            "content": response.message.content
        })

        print(f"\nQwen: {response.message.content}")

        # Agent has finished
        break


    print()
