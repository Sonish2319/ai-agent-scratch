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
    "completed": False,
    "recovery_attempts": 0
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
# 6. RECOVERY PLANNER
# ============================================================

def create_recovery_plan(task, failed_plan, execution):
    """Ask Qwen to create a new plan after a failure."""

    recovery_context = {
        "original_task": task,
        "failed_plan": failed_plan,
        "execution_result": execution
    }

    response = ollama.chat(
        model="qwen3:4b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI agent recovery planner. "

                    "A previous plan failed during execution. "

                    "Analyze the failure and create a corrected "
                    "executable plan. "

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

                    "Only create the corrected plan."
                )
            },
            {
                "role": "user",
                "content": (
                    "The following task failed during execution.\n\n"
                    f"{json.dumps(recovery_context, indent=2)}\n\n"
                    "Create a corrected plan."
                )
            }
        ]
    )

    plan_text = response.message.content

    try:

        plan = json.loads(plan_text)

        return plan

    except json.JSONDecodeError:

        print("\nRecovery planner returned invalid JSON:")
        print(plan_text)

        return {
            "steps": []
        }


# ============================================================
# 7. PLAN EXECUTOR
# ============================================================

def execute_plan(plan):
    """
    Execute the planned steps.

    Results from previous steps can be used
    through the '$previous_result' placeholder.
    """

    results = []

    previous_result = None

    for index, step in enumerate(
        plan.get("steps", []),
        start=1
    ):

        agent_state["current_step"] = index

        tool_name = step.get("tool")

        arguments = step.get(
            "arguments",
            {}
        ).copy()

        print(f"\nExecuting Step {index}")
        print(f"Tool: {tool_name}")
        print(f"Original arguments: {arguments}")

        # ----------------------------------------------------
        # Resolve previous result
        # ----------------------------------------------------

        for key, value in arguments.items():

            if value == "$previous_result":

                arguments[key] = previous_result

        print(
            f"Resolved arguments: {arguments}"
        )

        agent_state["last_tool"] = tool_name

        # ----------------------------------------------------
        # Find tool
        # ----------------------------------------------------

        tool = tool_registry.get(
            tool_name
        )

        if tool is None:

            result = (
                f"Error: Tool '{tool_name}' not found."
            )

            agent_state["last_result"] = result

            return {
                "success": False,
                "failed_step": index,
                "failed_tool": tool_name,
                "results": results,
                "error": result
            }

        # ----------------------------------------------------
        # Execute tool
        # ----------------------------------------------------

        try:

            result = tool(**arguments)

        except Exception as e:

            result = f"Tool error: {str(e)}"

            agent_state["last_result"] = result

            return {
                "success": False,
                "failed_step": index,
                "failed_tool": tool_name,
                "results": results,
                "error": result
            }

        agent_state["last_result"] = result

        previous_result = result

        results.append(result)

        print(f"Result: {result}")

        # ----------------------------------------------------
        # Detect tool-level errors
        # ----------------------------------------------------

        if isinstance(result, str) and (
            result.startswith("Error")
            or result.startswith("Tool error")
        ):

            return {
                "success": False,
                "failed_step": index,
                "failed_tool": tool_name,
                "results": results,
                "error": result
            }

    # --------------------------------------------------------
    # Plan completed
    # --------------------------------------------------------

    return {
        "success": True,
        "failed_step": None,
        "failed_tool": None,
        "results": results,
        "error": None
    }


# ============================================================
# 8. START AGENT
# ============================================================

print("Simple AI Agent")
print("Type 'exit' to quit.\n")


# ============================================================
# 9. CONVERSATION MEMORY
# ============================================================

messages = [

    {
        "role": "system",
        "content": (
            "You are a helpful AI agent. "
            "You receive results from a Python planning "
            "and execution system. "
            "Do not invent tool results. "
            "Use the provided execution results "
            "when answering the user."
        )
    }

]


# ============================================================
# 10. MAXIMUM RECOVERY ATTEMPTS
# ============================================================

MAX_RECOVERY_ATTEMPTS = 3


# ============================================================
# 11. CHAT LOOP
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

    agent_state["recovery_attempts"] = 0


    # ========================================================
    # Add user message to memory
    # ========================================================

    messages.append({
        "role": "user",
        "content": user_message
    })


    # ========================================================
    # Create initial plan
    # ========================================================

    print("\nCreating plan...")

    plan = create_plan(
        user_message
    )

    agent_state["plan"] = plan


    # ========================================================
    # Display initial plan
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
    # Execute initial plan
    # ========================================================

    print("\nExecuting plan...")

    execution = execute_plan(
        plan
    )


    # ========================================================
    # RECOVERY LOOP
    # ========================================================

    while (
        not execution["success"]
        and agent_state["recovery_attempts"]
        < MAX_RECOVERY_ATTEMPTS
    ):

        print("\nPlan failed.")

        print(
            "Execution result:"
        )

        print(
            json.dumps(
                execution,
                indent=2
            )
        )


        # ----------------------------------------------------
        # Increase recovery attempt count
        # ----------------------------------------------------

        agent_state["recovery_attempts"] += 1

        attempt = agent_state[
            "recovery_attempts"
        ]

        print(
            f"\nRecovery attempt "
            f"{attempt}/{MAX_RECOVERY_ATTEMPTS}"
        )


        # ----------------------------------------------------
        # Create recovery plan
        # ----------------------------------------------------

        print(
            "\nCreating recovery plan..."
        )

        recovery_plan = create_recovery_plan(
            user_message,
            plan,
            execution
        )


        # ----------------------------------------------------
        # Display recovery plan
        # ----------------------------------------------------

        print("\nRecovery Plan:")

        for index, step in enumerate(
            recovery_plan.get("steps", []),
            start=1
        ):

            print(
                f"{index}. "
                f"{step.get('tool')} "
                f"{step.get('arguments')}"
            )


        # ----------------------------------------------------
        # Check whether recovery planner
        # actually produced steps
        # ----------------------------------------------------

        if not recovery_plan.get("steps"):

            print(
                "\nRecovery planner "
                "did not create a valid plan."
            )

            execution = {
                "success": False,
                "failed_step": None,
                "failed_tool": None,
                "results": [],
                "error": (
                    "Recovery planner "
                    "returned an empty plan."
                )
            }

            break


        # ----------------------------------------------------
        # Save recovery plan
        # ----------------------------------------------------

        plan = recovery_plan

        agent_state["plan"] = recovery_plan


        # ----------------------------------------------------
        # Execute recovery plan
        # ----------------------------------------------------

        print(
            "\nExecuting recovery plan..."
        )

        execution = execute_plan(
            recovery_plan
        )


        # ----------------------------------------------------
        # Check recovery result
        # ----------------------------------------------------

        if execution["success"]:

            agent_state["completed"] = True

            print(
                "\nRecovery plan "
                "completed successfully."
            )

            break


    # ========================================================
    # FINAL EXECUTION STATUS
    # ========================================================

    if execution["success"]:

        agent_state["completed"] = True

        print(
            "\nTask completed successfully."
        )

    else:

        print(
            "\nTask could not be completed."
        )

        print(
            f"Maximum recovery attempts: "
            f"{MAX_RECOVERY_ATTEMPTS}"
        )

        print(
            f"Attempts used: "
            f"{agent_state['recovery_attempts']}"
        )

        print(
            f"Final error: "
            f"{execution['error']}"
        )


    # ========================================================
    # GIVE FINAL EXECUTION RESULT TO QWEN
    # ========================================================

    execution_message = (
        "The Python planner and executor "
        "processed the user's task.\n\n"

        f"Task:\n"
        f"{user_message}\n\n"

        f"Final Plan:\n"
        f"{json.dumps(plan, indent=2)}\n\n"

        f"Execution:\n"
        f"{json.dumps(execution, indent=2)}\n\n"

        f"Recovery Attempts Used:\n"
        f"{agent_state['recovery_attempts']}\n\n"

        "Provide the final answer to the user "
        "using only the execution results above. "

        "Do not invent or recalculate tool results."
    )


    messages.append({
        "role": "user",
        "content": execution_message
    })


    # ========================================================
    # FINAL ANSWER FROM QWEN
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
        f"\nQwen: "
        f"{final_response.message.content}"
    )


    # ========================================================
    # DISPLAY AGENT STATE
    # ========================================================

    print("\nAgent State:")

    print(
        agent_state
    )

    print()