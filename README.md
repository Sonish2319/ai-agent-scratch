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




                Agent State

                    ┌───────────────┐
                    │  Agent State  │
                    │               │
                    │ messages      │
                    │ task          │
                    │ step          │
                    │ results       │
                    │ status        │
                    └───────┬───────┘
                            │
                            ▼
                         QWEN
                            │
                      decision
                            │
                            ▼
                          TOOL
                            │
                         result
                            │
                            ▼
                    Update State
                            │
                            ▼
                         QWEN



Agent state flow::

                 USER
                  │
                  ▼
          ┌───────────────┐
          │   AGENT LOOP  │
          └───────┬───────┘
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
 Conversation             Agent
   Memory                  State
 messages[]              agent_state
        │                   │
        │                   ├── current_task
        │                   ├── last_tool
        │                   ├── last_result
        │                   └── completed
        │
        ├── user messages
        ├── tool calls
        ├── tool results
        └── assistant responses




Planning by qwen and executing by python


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



              till now architecture::

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
             ┌─────────────┴─────────────┐
             ▼                           ▼
          Tool 1                      Tool 2
             │                           │
             ▼                           ▼
          Result 1 ────────────────→ Result 2
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