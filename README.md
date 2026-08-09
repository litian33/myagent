从零开始手搓自己的Agent，学习Agent开发。

初步具备Human in the loop.

```text

                        User
                          │
                          ▼
                    AgentRuntime
                          │
                          ▼
                         LLM
                          │
                     Tool Call
                          │
                          ▼
                    ToolRegistry
                       lookup
                          │
                          ▼
                         Tool
                  ┌───────┴────────┐
                  │                │
               schema          capability
                                   │
                                   ▼
                             ToolPolicy
                                   │
                 ┌─────────────────┼──────────────┐
                 │                 │              │
               ALLOW             DENY        APPROVAL
                 │                                │
                 │                                ▼
                 │                              Human
                 │                             yes/no
                 │                                │
                 └────────────────┬───────────────┘
                                  ▼
                            ToolRegistry
                              execute
                                  │
                                  ▼
                            Tool Handler
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
                filesystem     process       edit
                    │             │             │
                    └─────────────┼─────────────┘
                                  ▼
                              Observation
                                  │
                                  └────→ LLM
```
