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
    "current_step": None,
    "last_tool": None,
    "last_result": None,
    "completed": False
}


# ============================================================
# 4. TOOL DEFINITIONS
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
    """Ask Qwen to create an executable plan."""

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

                    "Each step must contain "
                    "'tool' and 'arguments'. "

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
# 6. PLAN EXECUTOR
# ============================================================

def execute_plan(plan):
    """
    Execute the planned steps.

    Results from previous steps can be used
    through the '$previous_result' placeholder.
    """

    results = []

    previous_result = None


    # --------------------------------------------------------
    # Execute every planned step
    # --------------------------------------------------------

    for index, step in enumerate(plan.get("steps", []), start=1):

        agent_state["current_step"] = index


        # ----------------------------------------------------
        # Read tool and arguments
        # ----------------------------------------------------

        tool_name = step.get("tool")

        arguments = step.get("arguments", {}).copy()


        print(f"\nExecuting Step {index}")
        print(f"Tool: {tool_name}")
        print(f"Original arguments: {arguments}")


        # ----------------------------------------------------
        # Resolve $previous_result
        # ----------------------------------------------------

        for key, value in arguments.items():

            if value == "$previous_result":

                arguments[key] = previous_result


        print(f"Resolved arguments: {arguments}")


        # ----------------------------------------------------
        # Store current tool in agent state
        # ----------------------------------------------------

        agent_state["last_tool"] = tool_name


        # ----------------------------------------------------
        # Find tool in registry
        # ----------------------------------------------------

        tool = tool_registry.get(tool_name)


        if tool is None:

            result = f"Error: Tool '{tool_name}' not found."


        else:

            try:

                # Generic tool execution
                result = tool(**arguments)

            except Exception as e:

                result = f"Tool error: {str(e)}"


        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        agent_state["last_result"] = result

        previous_result = result

        results.append(result)


        print(f"Result: {result}")


        # ----------------------------------------------------
        # Stop if tool produced an error
        # ----------------------------------------------------

        if isinstance(result, str) and result.startswith("Error"):

            return {
                "success": False,
                "results": results,
                "error": result
            }


    # --------------------------------------------------------
    # Plan completed successfully
    # --------------------------------------------------------

    return {
        "success": True,
        "results": results,
        "error": None
    }


# ============================================================
# 7. START AGENT
# ============================================================

print("Simple AI Agent")
print("Type 'exit' to quit.\n")


# ============================================================
# 8. CONVERSATION MEMORY
# ============================================================

messages = [

    {
        "role": "system",
        "content": (
            "You are a helpful AI agent. "
            "You receive results from a Python planning and execution system. "
            "Do not invent tool results. "
            "Use the provided execution results when answering the user."
        )
    }

]


# ============================================================
# 9. CHAT LOOP
# ============================================================

while True:

    user_message = input("You: ")


    if user_message.lower() == "exit":

        print("Goodbye!")

        break


    # ========================================================
    # Reset state for new task
    # ========================================================

    agent_state["current_task"] = user_message
    agent_state["plan"] = None
    agent_state["current_step"] = None
    agent_state["last_tool"] = None
    agent_state["last_result"] = None
    agent_state["completed"] = False


    # ========================================================
    # 10. ADD USER MESSAGE TO MEMORY
    # ========================================================

    messages.append({
        "role": "user",
        "content": user_message
    })


    # ========================================================
    # 11. CREATE PLAN
    # ========================================================

    print("\nCreating plan...")

    plan = create_plan(user_message)

    agent_state["plan"] = plan


    # ========================================================
    # 12. DISPLAY PLAN
    # ========================================================

    print("\nPlan:")

    for index, step in enumerate(
        plan.get("steps", []),
        start=1
    ):

        print(
            f"{index}. "
            f"{step.get('tool')} "
            f"{step.get('arguments')}"
        )


    # ========================================================
    # 13. EXECUTE PLAN
    # ========================================================

    print("\nExecuting plan...")

    execution = execute_plan(plan)


    # ========================================================
    # 14. CHECK EXECUTION
    # ========================================================

    if execution["success"]:

        agent_state["completed"] = True

        print("\nPlan completed successfully.")

    else:

        print("\nPlan failed.")

        print(
            f"Error: {execution['error']}"
        )


    # ========================================================
    # 15. GIVE EXECUTION RESULTS TO QWEN
    # ========================================================

    execution_message = (
        "The Python planner and executor processed the user's task.\n\n"
        f"Task:\n{user_message}\n\n"
        f"Plan:\n{json.dumps(plan, indent=2)}\n\n"
        f"Execution:\n{json.dumps(execution, indent=2)}\n\n"
        "Provide the final answer to the user using only the "
        "execution results above. "
        "Do not invent or recalculate tool results."
    )


    messages.append({
        "role": "user",
        "content": execution_message
    })


    # ========================================================
    # 16. FINAL ANSWER FROM QWEN
    # ========================================================

    final_response = ollama.chat(
        model="qwen3:4b",
        messages=messages
    )


    messages.append({
        "role": "assistant",
        "content": final_response.message.content
    })


    print(
        f"\nQwen: {final_response.message.content}"
    )


    # ========================================================
    # 17. DISPLAY AGENT STATE
    # ========================================================

    print("\nAgent State:")

    print(agent_state)


    print()