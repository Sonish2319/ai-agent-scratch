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
