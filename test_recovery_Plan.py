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


# recovery plan

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
                    "Analyze the failure and create a corrected executable plan. "
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


task = "Add 10 and 20, then divide the result by 0."

failed_plan = {
    "steps": [
        {
            "tool": "calculator",
            "arguments": {
                "a": 10,
                "b": 20,
                "operation": "add"
            }
        },
        {
            "tool": "calculator",
            "arguments": {
                "a": "$previous_result",
                "b": 0,
                "operation": "divide"
            }
        }
    ]
}

execution = {
    "success": False,
    "failed_step": 2,
    "failed_tool": "calculator",
    "results": [30],
    "error": "Error: cannot divide by zero"
}

print("\nCreating recovery plan...")

recovery_plan = create_recovery_plan(
    task,
    failed_plan,
    execution
)

print("\nRecovery Plan:")
print(json.dumps(recovery_plan, indent=2))