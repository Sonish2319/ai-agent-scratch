import ollama
from datetime import datetime


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


print("Simple AI Agent")
print("Type 'exit' to quit.\n")

# Conversation memory

messages = []

# Chat loop

while True:

    user_message = input("You: ")

    if user_message.lower() == "exit":
        print("Goodbye!")
        break

    # Add user message to memory
    messages.append({
        "role": "user",
        "content": user_message
    })

    # Agent loop

    while True:

        print("\nThinking...")

        response = ollama.chat(
            model="qwen3:4b",
            messages=messages,
            tools=tools
        )

        # Does Qwen want to use a tool?
        
        if response.message.tool_calls:

            # Store Qwen's tool request
            messages.append(response.message)

            for tool_call in response.message.tool_calls:

                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments

                print(f"Agent wants to use: {tool_name}")
                print(f"Arguments: {arguments}")

                # Execute calculator
                if tool_name == "calculator":

                    result = calculator(
                        arguments["a"],
                        arguments["b"],
                        arguments["operation"]
                    )

                    print(f"Tool result: {result}")

                    # Give tool result back to Qwen
                    messages.append({
                        "role": "tool",
                        "content": str(result)
                    })

                elif tool_name == "get_current_time":

                    result = get_current_time()
                    print(f"Current time: {result}")

                    messages.append({
                        "role": "tool",
                        "content": result
                    })

            # Continue the agent loop
            continue

        # No tool needed

        messages.append({
            "role": "assistant",
            "content": response.message.content
        })

        print(f"\nQwen: {response.message.content}")

        # Agent is finished
        break

    print()