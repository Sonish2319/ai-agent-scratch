import ollama
import json
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
    """Return the current local date and time."""

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
    "plan": None,
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
# 5. PLANNER
# ============================================================

def create_plan(task):
    """Ask Qwen to create a plan without executing any tools."""

    response = ollama.chat(
        model="qwen3:4b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI agent planner. "
                    "Break the user's task into clear executable steps. "
                    "Return ONLY valid JSON. "

                    "The JSON must contain a 'steps' array. "

                    "Each step must contain 'tool' and 'arguments'. "

                    "Available tools are: "

                    "1. calculator "
                    "Arguments: a, b, operation. "
                    "operation must be one of: "
                    "add, subtract, multiply, divide. "

                    "2. get_current_time "
                    "Arguments: none. "

                    "If a step depends on the result of a previous step, "
                    "use '$previous_result' as the argument value. "

                    "Do not execute any tools. "
                    "Only create the plan."
                )
            },
            {
                "role": "user",
                "content": task
            }
        ]
    )

    plan_text = response.message.content

    try:
        plan = json.loads(plan_text)
        return plan

    except json.JSONDecodeError:
        print("\nPlanner returned invalid JSON:")
        print(plan_text)

        return {
            "steps": []
        }


# ============================================================
# 6. START AGENT
# ============================================================

print("Simple AI Agent")
print("Type 'exit' to quit.\n")


# ============================================================
# 7. CONVERSATION MEMORY
# ============================================================

messages = [
    {
        "role": "system",
        "content": (
            "You are a helpful AI agent. "

            "Use the calculator tool for mathematical calculations. "

            "Use the get_current_time tool when the user asks "
            "for the current time. "

            "Do not invent tool results. "

            "Use tools when they are appropriate. "

            "Follow the planner's suggested plan when possible, "
            "but use your own tool-calling reasoning to determine "
            "the correct execution."
        )
    }
]


# ============================================================
# 8. CHAT LOOP
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
    agent_state["plan"] = None
    agent_state["last_tool"] = None
    agent_state["last_result"] = None
    agent_state["completed"] = False


    # ========================================================
    # 9. CREATE PLAN
    # ========================================================

    print("\nCreating plan...")

    plan = create_plan(user_message)

    agent_state["plan"] = plan


    print("\nPlan:")

    for index, step in enumerate(plan.get("steps", []), start=1):

        print(
            f"{index}. "
            f"{step.get('tool')} "
            f"{step.get('arguments')}"
        )


    # --------------------------------------------------------
    # Give the plan to the main agent
    # --------------------------------------------------------

    messages.append({
        "role": "user",
        "content": user_message
    })

    messages.append({
        "role": "system",
        "content": (
            "Planner generated the following plan for the current task:\n"
            + json.dumps(plan)
            + "\n"
            "Use this plan as guidance when deciding which tools to call."
        )
    })


    # ========================================================
    # 10. MAIN AGENT LOOP
    # ========================================================

    while True:

        print("\nThinking...")


        response = ollama.chat(
            model="qwen3:4b",
            messages=messages,
            tools=tools
        )


        # ====================================================
        # 11. DID QWEN REQUEST A TOOL?
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
                # 12. LOOK UP TOOL IN REGISTRY
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
                # 13. GIVE TOOL RESULT BACK TO QWEN
                # =================================================

                messages.append({
                    "role": "tool",
                    "content": str(result)
                })


            # ------------------------------------------------
            # Ask Qwen what to do next
            # ------------------------------------------------

            continue


        # ====================================================
        # 14. NO TOOL NEEDED
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