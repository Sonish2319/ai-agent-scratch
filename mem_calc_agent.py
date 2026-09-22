import ollama
from datetime import datetime


# ============================================================
# 1. TOOL FUNCTIONS
# ============================================================

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


# ============================================================
# 2. TOOL REGISTRY
# ============================================================

tool_registry = {
    "calculator": calculator,
    "get_current_time": get_current_time
}


# ============================================================
# 3. AGENT STATE
# ============================================================

agent_state = {
    "current_task": None,
    "last_tool": None,
    "last_result": None,
    "completed": False
}


# ============================================================
# 4. TOOL DEFINITIONS FOR QWEN
# ============================================================

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


# ============================================================
# 5. START AGENT
# ============================================================

print("Simple AI Agent")
print("Type 'exit' to quit.\n")


# Conversation memory
messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful AI agent. "
            "Use the calculator tool for mathematical calculations. "
            "Use the get_current_time tool when the user asks for the current time. "
            "Do not invent tool results. "
            "Use tools when they are appropriate."
        )
    }
]


# ============================================================
# 6. CHAT LOOP
# ============================================================

while True:

    user_message = input("You: ")

    if user_message.lower() == "exit":
        print("Goodbye!")
        break


    # --------------------------------------------------------
    # Reset state for the new task
    # --------------------------------------------------------

    agent_state["current_task"] = user_message
    agent_state["last_tool"] = None
    agent_state["last_result"] = None
    agent_state["completed"] = False


    # --------------------------------------------------------
    # Add user message to conversation
    # --------------------------------------------------------

    messages.append({
        "role": "user",
        "content": user_message
    })


    # ========================================================
    # 7. AGENT LOOP
    # ========================================================

    while True:

        print("\nThinking...")


        response = ollama.chat(
            model="qwen3:4b",
            messages=messages,
            tools=tools
        )


        # ====================================================
        # 8. DID QWEN REQUEST A TOOL?
        # ====================================================

        if response.message.tool_calls:

            # Store Qwen's tool request in conversation
            messages.append(response.message)


            # A model response can contain multiple tool calls
            for tool_call in response.message.tool_calls:

                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments


                print(f"Agent wants to use: {tool_name}")
                print(f"Arguments: {arguments}")


                # ------------------------------------------------
                # Store current tool in agent state
                # ------------------------------------------------

                agent_state["last_tool"] = tool_name


                # =================================================
                # 9. LOOK UP TOOL IN REGISTRY
                # =================================================

                tool = tool_registry.get(tool_name)


                if tool is None:

                    result = f"Error: Tool '{tool_name}' not found."


                else:

                    try:

                        # Generic tool execution
                        result = tool(**arguments)

                    except Exception as e:

                        result = f"Tool error: {str(e)}"


                print(f"Tool result: {result}")


                # ------------------------------------------------
                # Store tool result in agent state
                # ------------------------------------------------

                agent_state["last_result"] = result


                # =================================================
                # 10. GIVE TOOL RESULT BACK TO QWEN
                # =================================================

                messages.append({
                    "role": "tool",
                    "content": str(result)
                })


            # Ask Qwen what to do next
            continue


        # ====================================================
        # 11. NO TOOL NEEDED
        # ====================================================

        messages.append({
            "role": "assistant",
            "content": response.message.content
        })


        print(f"\nQwen: {response.message.content}")


        # ----------------------------------------------------
        # Agent has finished
        # ----------------------------------------------------

        agent_state["completed"] = True


        # ----------------------------------------------------
        # Display current state
        # ----------------------------------------------------

        print("\nAgent State:")
        print(agent_state)


        break


    print()