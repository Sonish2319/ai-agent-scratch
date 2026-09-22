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
    """Return the current time as a string."""

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ============================================================
# 2. TOOL REGISTRY
# ============================================================

tool_registry = {
    "calculator": calculator,
    "get_current_time": get_current_time
}


def create_plan(task):
    """Create an executable tool-based plan."""

    response = ollama.chat(
        model="qwen3:4b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an AI agent planner. "
                    "Break the user's task into executable steps. "
                    "Return ONLY valid JSON. "

                    "The JSON must have a 'steps' array. "

                    "Each step must contain 'tool' and 'arguments'. "

                    "Available tools are: "

                    "1. calculator "
                    "Arguments: "
                    "a, b, operation. "
                    "operation must be one of: "
                    "add, subtract, multiply, divide. "

                    "2. get_current_time "
                    "Arguments: none. "

                    "If a step needs the result of a previous step, "
                    "use the exact placeholder "
                    "'$previous_result' as the argument value. "

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

    plan = json.loads(plan_text)

    return plan


def execute_plan(plan):
    """Execute a plan and pass each result to the next step."""

    results = []

    previous_result = None

    for step in plan["steps"]:

        tool_name = step["tool"]
        arguments = step["arguments"].copy()

        print(f"\nExecuting planned tool: {tool_name}")
        print(f"Original arguments: {arguments}")


        # Replace $previous_result
        # with the actual result from the previous step

        for key, value in arguments.items():

            if value == "$previous_result":

                arguments[key] = previous_result


        print(f"Resolved arguments: {arguments}")


        # Find the tool

        tool = tool_registry.get(tool_name)


        if tool is None:

            result = f"Error: Tool '{tool_name}' not found."

        else:

            try:

                result = tool(**arguments)

            except Exception as e:

                result = f"Tool error: {str(e)}"


        print(f"Result: {result}")


        # Store result

        previous_result = result

        results.append(result)


    return results

task = "Add 25 and 15, then multiply the result by 3."

plan = create_plan(task)

print("Plan: \n")
print(plan)


results = execute_plan(plan)

print("\nFinal Results:")
print(results)

