import ollama


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

    # Add user's message to memory
    messages.append({
        "role": "user",
        "content": user_message
    })

    # Ask Qwen what to do
    response = ollama.chat(
        model="qwen3:4b",
        messages=messages,
        tools=tools
    )

    # Did Qwen request a tool?
    if response.message.tool_calls:

        # Store Qwen's tool request in memory
        messages.append(response.message)

        for tool_call in response.message.tool_calls:

            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            print(f"Agent wants to use: {tool_name}")
            print(f"Arguments: {arguments}")

            # Execute the tool
            if tool_name == "calculator":

                result = calculator(
                    arguments["a"],
                    arguments["b"],
                    arguments["operation"]
                )

                print(f"Tool result: {result}")

                # Store tool result in memory
                messages.append({
                    "role": "tool",
                    "content": str(result)
                })

        # Ask Qwen for final answer
        final_response = ollama.chat(
            model="qwen3:4b",
            messages=messages,
            tools=tools
        )

        # Store final answer in memory
        messages.append({
            "role": "assistant",
            "content": final_response.message.content
        })

        print(f"Qwen: {final_response.message.content}")

    else:

        # Store normal Qwen response in memory
        messages.append({
            "role": "assistant",
            "content": response.message.content
        })

        print(f"Qwen: {response.message.content}")

    print()