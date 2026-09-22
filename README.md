# AI Agent Architecture

This project uses **Qwen** (via Ollama) as the planner/reasoning layer and **Python** as the execution layer.

What started as simple tool calling has evolved, step by step, into a stateful, structured planning-and-execution system. This README traces that journey — from the first naive version to the current `agent.py` implementation.

---

## Stage 1: Basic Tool Calling

The starting point: Qwen picks a tool, a registry finds the matching Python function, and the function runs.

```
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
```

Flow: `USER → QWEN → Tool Selection → Tool Registry → Tool Executor → Tool Result → QWEN → Final Answer`

**Lesson learned:** an LLM can call functions, but every call is isolated — there's no memory of what happened before.

---

## Stage 2: Agent State

Next came the idea of **persistent agent state** — instead of treating each tool call independently, the agent tracks the current task, step, results, and status.

```
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
```

```python
agent_state = {
    task = "...",
    step = 1,
    messages = {},
    results = {},
    status = "running"
}
```

**Lesson learned:** giving the agent a "memory of itself" lets it reason about what it already did, not just what tool to call next.

---

## Stage 3: Agent State Flow

Then the agent loop combined **conversation memory** (what was said) with **agent execution state** (what was done).

```
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
```

**Lesson learned:** two distinct kinds of context are needed — the *conversation* (for natural dialogue) and the *execution state* (for reliable multi-step behavior). Conflating them makes the agent brittle.

---

## Stage 4: Planning by Qwen, Execution by Python

A clean separation of concerns: **Qwen plans, Python executes.**

```
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
```

```
-- Qwen
plan = create_plan(user_request)

-- Python
result = execute_plan(plan)
```

**Lesson learned:** letting the LLM *decide* and letting deterministic code *act* is safer and more debuggable than letting the LLM call tools directly, turn by turn.

---

## Stage 5: Current Architecture

The current design combines everything learned so far:

- Qwen-based planning
- Structured JSON plans
- Persistent plan state
- A tool registry
- Sequential execution
- Passing results from one step to the next
- Final response generation

```
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
```

---

## Stage 6: Structured Plan

The planner outputs a **machine-readable plan**, not direct tool calls:

```python
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
```

The executor resolves each step's tool through the registry:

```python
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
```

---

## Stage 7: Previous Result → Next Step

Steps can now feed results into one another instead of running in isolation:

```
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
```

```
Step 1:
    calculator("20 + 20")
Result:
    40

Step 2:
    calculator(previous_result * 2)
Result:
    80
```

**Lesson learned:** this is what turns a bag of tools into an actual multi-step *workflow*.

---

## Stage 8: Overall Architecture

```
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
```

### Architecture Principle

```
QWEN   = Planning + Reasoning
PYTHON = Execution + Tool Management
STATE  = Memory + Execution Context
```

Or more simply:

```
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
```
---