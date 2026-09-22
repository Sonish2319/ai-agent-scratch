Agent Architecture

This project uses Qwen as the planner/reasoning layer and Python as the execution layer.

The architecture has evolved from simple tool calling into a stateful, structured planning and execution system.

1. Basic Tool Calling

The initial architecture allows Qwen to select a tool, while the tool registry finds and executes the corresponding Python function.

                    USER
                      │
                      ▼
                 ┌─────────┐
                 │  QWEN   │
                 │   LLM   │
                 └────┬────┘
                      │
                Tool selection
                      │
                      ▼
              ┌───────────────┐
              │ Tool Registry │
              └───────┬───────┘
                      │
                 Find function
                      │
                      ▼
              ┌───────────────┐
              │ Tool Executor │
              └───────┬───────┘
                      │
             ┌────────┴────────┐
             ▼                 ▼
       calculator()      get_current_time()
             │                 │
             └────────┬────────┘
                      ▼
                 Tool result
                      │
                      ▼
                    QWEN
                      │
                      ▼
                Final answer


The basic flow is:

USER
  -> QWEN
  -> Tool Selection
  -> Tool Registry
  -> Tool Executor
  -> Tool Result
  -> QWEN
  -> Final Answer

2. Agent State

The next step is introducing persistent agent state.

Instead of treating every tool call independently, the agent keeps track of the current task, previous results, execution step, and completion status.

                 ┌─────────────────┐
                 │   Agent State   │
                 │                 │
                 │ messages        │
                 │ task            │
                 │ step            │
                 │ results         │
                 │ status          │
                 └────────┬────────┘
                          │
                          ▼
                        QWEN
                          │
                       Decision
                          │
                          ▼
                         TOOL
                          │
                        Result
                          │
                          ▼
                   Update State
                          │
                          ▼
                        QWEN


Conceptually:

agent_state = {
    task = "...",
    step = 1,
    messages = {},
    results = {},
    status = "running"
}


The agent can now use the previous execution context when deciding what to do next.

3. Agent State Flow

The agent loop combines conversation memory with agent execution state.

                         USER
                          │
                          ▼
                  ┌───────────────┐
                  │   AGENT LOOP  │
                  └───────┬───────┘
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
       Conversation                Agent State
          Memory                   agent_state
        messages[]                     │
             │                         ├── current_task
             │                         ├── last_tool
             │                         ├── last_result
             │                         └── completed
             │
             ├── user messages
             ├── tool calls
             ├── tool results
             └── assistant responses


This gives the agent two important forms of context:

conversation_memory = {
    user_messages = {},
    tool_calls = {},
    tool_results = {},
    assistant_responses = {}
}

agent_state = {
    current_task = "...",
    last_tool = nil,
    last_result = nil,
    completed = false
}

4. Planning by Qwen, Execution by Python

The architecture then separates planning from execution.

Qwen creates a structured plan, while Python executes that plan.

                         USER
                           │
                           ▼
                    create_plan()
                           │
                           ▼
                  ┌─────────────────┐
                  │ Structured Plan │
                  └────────┬────────┘
                           │
                           ▼
                    execute_plan()
                           │
                           ▼
                     tool_registry
                           │
                           ▼
                      calculator()
                           │
                           ▼
                           40


The separation is:

-- Qwen
plan = create_plan(user_request)

-- Python
result = execute_plan(plan)


Qwen decides what should happen.

Python decides how the actual tools are executed.

5. Current Architecture

The current architecture combines:

Qwen-based planning

Structured JSON plans

Persistent plan state

Tool registry

Sequential execution

Previous-step results

Final response generation

                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │   PLANNER   │
                    │    Qwen     │
                    └──────┬──────┘
                           │
                           ▼
                    Structured JSON
                           │
                           ▼
                  ┌─────────────────┐
                  │   PLAN STATE    │
                  │                 │
                  │ Step 1          │
                  │ Step 2          │
                  │ Step 3          │
                  └────────┬────────┘
                           │
                           ▼
                    EXECUTE PLAN
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
           Tool 1                    Tool 2
              │                         │
              ▼                         ▼
           Result 1 ───────────────→ Result 2
              │
              ▼
        previous_result
              │
              ▼
          Next Step
              │
              ▼
       Execution Complete
              │
              ▼
            Qwen
              │
              ▼
         Final Answer

6. Structured Plan

The planner produces a machine-readable plan rather than directly executing tools.

For example:

plan = {
    steps = {
        {
            id = 1,
            tool = "calculator",
            input = {
                expression = "20 + 20"
            }
        }
    }
}


The execution layer receives this plan and resolves the requested tool through the registry.

function execute_plan(plan)
    for _, step in ipairs(plan.steps) do
        local tool = tool_registry[step.tool]

        local result = tool(step.input)

        agent_state.last_tool = step.tool
        agent_state.last_result = result
        agent_state.step = step.id
    end

    agent_state.completed = true
end

7. Previous Result → Next Step

A key part of the architecture is that one step can provide information to the next step.

        Step 1
          │
          ▼
       Tool 1
          │
          ▼
       Result 1
          │
          ▼
   previous_result
          │
          ▼
        Step 2
          │
          ▼
       Tool 2
          │
          ▼
       Result 2


For example:

Step 1:
    calculator("20 + 20")
    
Result:
    40

Step 2:
    calculator(previous_result * 2)

Result:
    80


This allows the agent to build multi-step workflows instead of treating each tool call as an isolated operation.

8. Overall Architecture

The complete system can be summarized as:

                         ┌──────────────┐
                         │     USER     │
                         └──────┬───────┘
                                │
                                ▼
                     ┌────────────────────┐
                     │       QWEN         │
                     │      PLANNER       │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │  Structured Plan   │
                     │       JSON         │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │    PLAN STATE      │
                     │                    │
                     │ current_step       │
                     │ previous_result    │
                     │ status             │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │   PYTHON EXECUTOR  │
                     └─────────┬──────────┘
                               │
                               ▼
                     ┌────────────────────┐
                     │   TOOL REGISTRY    │
                     └─────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
            calculator()   get_time()    custom_tool()
                 │             │             │
                 └─────────────┼─────────────┘
                               ▼
                         Tool Result
                               │
                               ▼
                      Update Agent State
                               │
                               ▼
                         Next Plan Step
                               │
                               ▼
                       Execution Complete
                               │
                               ▼
                             QWEN
                               │
                               ▼
                         Final Answer

Architecture Principle

The main design principle is:

QWEN   = Planning + Reasoning
PYTHON = Execution + Tool Management
STATE  = Memory + Execution Context


Or more simply:

             QWEN
              │
              │ "What should I do?"
              ▼
       Structured Plan
              │
              ▼
            Python
              │
              │ "Execute the plan."
              ▼
            Tools
              │
              ▼
           Results
              │
              ▼
          Agent State
              │
              ▼
            QWEN
              │
              ▼
        Final Answer


This architecture keeps reasoning, planning, state management, and execution separated while allowing them to work together as an agent loop.