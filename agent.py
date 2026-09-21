import ollama


def calculator(a, b):
    """Add two numbers."""
    return a + b


tools = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Add two numbers together.",
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
                    }
                },
                "required": ["a", "b"]
            }
        }
    }
]


print("Simple AI Agent")
print("Type 'exit' to quit.\n")

while True:
    user_message = input("You: ")

    if user_message.lower() == "exit":
        print("Goodbye!")
        break

    messages = [
        {
            "role": "user",
            "content": user_message
        }
    ]

    # 1. Ask Qwen what to do
    response = ollama.chat(
        model="qwen3:4b",
        messages=messages,
        tools=tools
    )

    # 2. Check if Qwen wants to use a tool
    if response.message.tool_calls:

        # Add Qwen's tool request to the conversation
        messages.append(response.message)

        for tool_call in response.message.tool_calls:

            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            print(f"Agent wants to use: {tool_name}")
            print(f"Arguments: {arguments}")

            # 3. Execute the Python tool
            if tool_name == "calculator":

                result = calculator(
                    arguments["a"],
                    arguments["b"]
                )

                print(f"Tool result: {result}")

                # 4. Give the tool result back to Qwen
                messages.append({
                    "role": "tool",
                    "content": str(result)
                })

        # 5. Ask Qwen for the final answer
        final_response = ollama.chat(
            model="qwen3:4b",
            messages=messages,
            tools=tools
        )

        print(f"Qwen: {final_response.message.content}")

    else:
        # No tool was needed
        print(f"Qwen: {response.message.content}")

    print()