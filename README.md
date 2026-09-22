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

## Where I Am Now: `agent.py`

The current implementation (`agent.py`) is a working, runnable version of Stage 5–8 above, built on **Ollama + `qwen3:4b`**. It maps directly onto the diagrams:

| Concept above | Implemented as |
|---|---|
| Tool functions | `calculator(a, b, operation)`, `get_current_time()` |
| Tool registry | `tool_registry = { "calculator": ..., "get_current_time": ... }` |
| Agent state | `agent_state` dict — `current_task`, `plan`, `current_step`, `last_tool`, `last_result`, `completed` |
| Tool definitions (for the LLM) | JSON-schema `tools` list passed to `ollama.chat` |
| Planner (Qwen) | `create_plan(task)` — sends the task + a system prompt to `qwen3:4b`, asking for **JSON-only** output with a `steps` array |
| Structured plan | Each step has `tool` and `arguments`; a dependent step can reference `"$previous_result"` |
| Plan executor (Python) | `execute_plan(plan)` — loops through steps, resolves `$previous_result`, looks up the tool in the registry, calls it, and records results |
| Previous result → next step | The `$previous_result` placeholder is swapped for the prior step's actual return value before each call |
| Error handling | Division by zero and unknown tools return an `"Error: ..."` string; `execute_plan` stops early and reports `success: False` if any step errors |
| Conversation memory | `messages[]` — a running list of user/assistant turns, seeded with a system prompt telling Qwen not to invent tool results |
| Final answer generation | After execution, the task, plan, and execution results are serialized to JSON and handed back to `qwen3:4b`, which is told to answer using *only* those results |
| Transparency | Each run prints the plan, step-by-step execution, and the full `agent_state` at the end, so the whole loop is inspectable |

### What's new in this version specifically

- **Real LLM plumbing**: swapped the conceptual pseudocode for an actual `ollama.chat()` integration against `qwen3:4b`.
- **JSON-schema tool defs**: tools are now described the way most LLM tool-calling APIs expect (`type: function`, `parameters`, `enum` for `operation`), even though the planner doesn't call them directly — it just uses the schema as a reference when writing the plan.
- **Graceful JSON failure handling**: if Qwen returns malformed JSON for a plan, `create_plan` catches it and falls back to an empty plan instead of crashing.
- **Fail-fast execution**: the executor stops at the first error instead of silently continuing, and reports exactly which step failed.
- **A real REPL loop**: `while True` chat loop with `exit` to quit, state reset per task, and printed agent state after every turn — this is the first version that's actually usable interactively.

---

## Key Takeaways So Far

1. **Separate reasoning from execution.** Letting the LLM plan and letting deterministic Python act is far more reliable than free-form tool calling turn by turn.
2. **State is not the same as memory.** Conversation history (what was said) and execution state (what was done, and what's next) serve different purposes and should be tracked separately.
3. **Structured plans are debuggable.** A JSON plan can be printed, logged, validated, and retried — a stream of ad-hoc tool calls can't.
4. **Chaining results (`$previous_result`) is what makes it an *agent* and not just a router.**
5. **Fail fast, and tell the LLM the truth.** Feeding only verified execution results back to Qwen (not letting it "recalculate" or invent numbers) keeps the final answer grounded.

## Next Steps

- Support parallel (non-sequential) steps in a plan
- Add more tools and a way for the planner to discover them dynamically
- Persist `agent_state` and `messages` across sessions (currently in-memory only)
- Add retries/repair for malformed plans instead of falling back to an empty plan
- Move from single-shot planning to re-planning when a step fails