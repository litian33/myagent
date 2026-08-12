# MyAgent 学习进度打卡表

> 本文档只记录学习进度、完成证据和下一步，不扩展课程内容。
>
> 完整课程结构和课程编号的唯一来源见：[AI Agent 开发学习课程大纲](./learning-roadmap.md)。

---

## 1. 编号与状态约定

### 1.1 课程编号规则

课程编号必须与 `learning-roadmap.md` **一一对应**。

例如 Phase 4 在 Roadmap 中只有：

```text
P4.1 AgentState
P4.2 History 与 Context
P4.3 Token Budget
P4.4 Context Compaction
P4.5 Runtime Lifecycle
P4.6 Error Boundary
```

像“本地 Token 计数”“Working Set”“Build → Compact → Rebuild”等实现步骤，只作为对应课程下面的完成细项，不再单独生成 `P4.x` 课程号。

后续任何新增课程，都必须先修改 Roadmap，再同步到本打卡表，禁止只在打卡表中自行扩展课程编号。

### 1.2 状态约定

- `[x]`：已完成，并通过代码/实验验证
- `[~]`：部分完成，仍需补齐本课程或 Phase 的 Exit Criteria
- `[ ]`：未开始
- `ADV`：Advanced，可选，不阻塞主线
- `提前完成`：历史课程顺序中已经实现，但仍需在对应 Phase 做概念归纳和 Exit Review

---

## 2. 总体进度

| Phase | 主题 | 状态 | 当前结论 |
|---|---|---|---|
| Phase 1 | LLM Application 基础 | ✅ 完成 | 不再深入 Provider / Tokenizer 细节 |
| Phase 2 | Agent Loop | ✅ 完成 | 已形成真实 Tool Call → Observation → LLM 循环 |
| Phase 3 | Tool Runtime | ✅ 完成 | 已完成文件系统以及系统命令封装调用 |
| Phase 4 | Agent State + Runtime | ✅ 完成 | 已完成单轮会话状态驱动 |
| Phase 5 | Planning | ✅ 完成 | 已完成单轮会话状态内的任务规划以及驱动 |
| Phase 6 | Context + Memory | 🟡 进行中 | 已经完成存储策略以及存储能力提高，未接入运行时 |
| Phase 7 | RAG / Knowledge Retrieval | ⬜ 未开始 | — |
| Phase 8 | Safety / Guardrails / HITL | 🟡 部分提前完成 | Policy / Approval / Sandbox 等已提前实现，当前冻结深入 |
| Phase 9 | Observability + Evaluation | ⬜ 未开始 | — |
| Phase 10 | Multi-Agent | ⬜ 未开始 | — |
| Framework Stage 1 | OpenAI Agents SDK | ⬜ 未开始 | 10 个手写 Phase 完成后进入 |
| Framework Stage 2 | LangGraph | ⬜ 未开始 | Agents SDK 之后 |
| Framework Stage 3 | MCP | ⬜ 未开始 | 最后进入 |

---

# 3. Phase 1：LLM Application 基础

**状态：完成**

- [x] **P1.1 最小 LLM 调用**
  - [x] Responses API 基本调用
  - [x] 理解 model / instructions / input / output_text
- [x] **P1.2 观察真实 Response 结构**
  - [x] 观察 `Response.output[]`
  - [x] 理解 message / reasoning / function_call 等 Output Item
- [x] **P1.3 Structured Output 与类型边界**
  - [x] 理解 Schema / typed request 的价值
  - [x] 后续代码持续使用 SDK 类型定义构造请求
- [x] **P1.4 Function Calling 协议预览**
  - [x] 理解 `function_call` 只是模型输出
  - [x] 理解 LLM 决策与 Runtime 执行的边界

### Exit Review

- [x] 能解释 LLM 应用为什么还不是 Agent
- [x] 能解释 Response 为什么不只是字符串
- [x] 能解释 `function_call` 为什么仍只是模型生成的结构化 Action
- [x] 能解释非确定性 LLM 与确定性 Runtime 的边界

---

# 4. Phase 2：Agent Loop

**状态：完成**

- [x] **P2.1 第一个 `list_files` Tool**
  - [x] Python Function → Tool Schema
  - [x] `function_call` → 参数反序列化 → Tool 执行
  - [x] 构造 `function_call_output`
- [x] **P2.2 多轮 Tool Call**
  - [x] Tool Result 作为 Observation 返回模型
  - [x] 支持模型继续产生下一次 Tool Call
- [x] **P2.3 第一个 `while` Agent Loop**
  - [x] 从写死 first/second response 演进为循环
- [x] **P2.4 Stop Conditions**
  - [x] Final Answer
  - [x] `max_steps`
  - [x] Tool / Model failure 的基本退出理解
- [x] **P2.5 多 Tool Call**
  - [x] 支持一个模型 Step 中多个 function call

### Exit Review

- [x] 能解释 `Reason → Act → Observe` 的真实代码对应关系
- [x] 能解释为什么 LLM 决策、Runtime 执行
- [x] 能从零说明 Agent Loop 的停止条件

---

# 5. Phase 3：Tool Runtime

**状态：基本完成，主线冻结扩展**

- [x] **P3.1 从 `if/elif` 到 Tool Registry**
  - [x] 动态注册与派发 Tool
- [x] **P3.2 Tool 模型**
  - [x] name / description / schema / handler / capability
- [x] **P3.3 类型注解生成 Schema**
  - [x] 使用 Python type hints / annotation 减少多源维护
- [x] **P3.4 Filesystem Tools**
  - [x] `list_files`
  - [x] `read_file`
  - [x] 搜索类能力
- [x] **P3.5 Shell Tool**
  - [x] `run_command`
  - [x] argv / cwd / timeout
  - [x] exit code / stdout / stderr
  - [x] output truncation
- [x] **P3.6 Editing Tools**
  - [x] `write_file`
  - [x] `apply_patch`
  - [x] expected hash / optimistic concurrency
  - [x] Tool Unknown / Tool Error 能返回结构化 Observation

### Exit Review

- [x] 能解释 Tool Implementation 和 Tool Schema 的区别
- [x] 能解释 Tool Description 为什么也是模型决策的一部分
- [x] 能解释 Tool Registry 解决的扩展性问题
- [x] 能解释 Tool Error 如何重新进入 Observation

### 冻结项

除非后续 Phase 的实验明确需要，当前不继续扩展：

- 更多 Shell 命令适配
- 更复杂 Patch Engine
- 更多 Git Tool
- 更复杂 Tool Middleware

---

# 6. Phase 4：Agent State + Runtime

**状态：进行中**

- [x] **P4.1 AgentState**
  - [x] 引入 `AgentState`
  - [x] 使用 `HistoryBlock` 保存 Agent Step
  - [x] 区分 task / step / model output / tool output
- [x] **P4.2 History 与 Context**
  - [x] 分离 Raw History 与 Context
  - [x] 引入 `ContextManager`
  - [x] 能区分 State / Raw History / Context
- [x] **P4.3 Token Budget**
  - [x] Context Window
  - [x] Output Reserve
  - [x] Safety Margin
  - [x] 本地 Token 计数/估算
  - [x] Context 超预算时选择 Working Set
- [x] **P4.4 Context Compaction**
  - [x] `CompactionState`
  - [x] Raw History 不因 Compaction 删除
  - [x] Incremental Compaction
  - [x] Build → Compact → Rebuild
  - [x] 能区分 Raw History / Compaction / Context
- [x] **P4.5 Runtime Lifecycle**
  - [x] CREATED
  - [x] RUNNING
  - [x] COMPLETED
  - [x] FAILED
  - [x] MAX_STEPS_REACHED
  - [x] `WAITING_APPROVAL` 与已有 HITL 的关系
  - [x] `CANCELLED` 先理解概念
- [x] **P4.6 Error Boundary**
  - [x] Model Error
  - [x] Tool Error
  - [x] Context Error
  - [x] Runtime Error
  - [x] retryable / non-retryable 最小分类

### Phase 4 Exit Review

- [x] 能准确解释 Agent / AgentRuntime / AgentState / History / Context / Compaction
- [x] Runtime 对任务结束原因有明确状态
- [x] 主要错误边界清晰，不依赖到处 `try/except` 猜测状态

**完成后立即进入 Phase 5，不继续深入 Context/Sandbox。**

---

# 7. Phase 5：Planning
- [x] **P5.1 Reactive Agent 与 ReAct**
- [x] **P5.2 Goal、Plan、Todo、Action 的区别**
- [x] **P5.3 最小 Planner**
  - [x] Plan
  - [x] PlanStep
  - [x] PlanStepStatus
- [x] **P5.4 Executor**
- [x] **P5.5 Progress Update**
- [x] **P5.6 Replanning**
- [x] **P5.7 Completion Criteria**
- [x] **P5.8 Phase 实验：完整修复任务**

### Phase 5 Exit Review

- [x] 能解释 ReAct 与 Plan-and-Execute 的差异
- [x] 能让 MyAgent 对一个多步骤任务维护显式 Plan 和 Progress
- [x] 能根据 Observation 调整计划
- [x] 能通过外部验证而不是模型自述判断任务完成

---

# 8. Phase 6：Context + Memory

**状态：部分提前完成**

- [~] **P6.1 Context Engineering 复盘**
  - [x] History
  - [x] Token Budget
  - [x] Working Context
  - [x] Compaction
  - [x] Phase 6 正式进入时做一次概念收束
- [x] **P6.2 Memory Taxonomy**
- [x] **P6.3 Multi-turn Session**
- [x] **P6.4 Memory Store**
  - [x] SQLite
  - [x] put / get / search / delete
- [x] **P6.5 Memory Write Policy**
- [ ] **P6.6 Memory Retrieval**
- [ ] **P6.7 Restart 实验**

### Phase 6 Exit Review

- [ ] 能解释 Context ≠ History ≠ Compaction ≠ Session Memory ≠ Long-term Memory ≠ Knowledge Base
- [ ] Agent 能跨运行保存并召回少量长期事实

---

# 9. Phase 7：RAG / Knowledge Retrieval

**状态：未开始**

- [ ] **P7.1 为什么需要 Retrieval**
- [ ] **P7.2 Document → Chunk → Metadata**
- [ ] **P7.3 Embedding**
- [ ] **P7.4 最小 Vector Retrieval**
- [ ] **P7.5 Lexical Search / BM25**
- [ ] **P7.6 Hybrid Retrieval**
- [ ] **P7.7 Metadata Filtering**
- [ ] **P7.8 Code RAG**
- [ ] **P7.9 Retrieval Quality 实验**

### Phase 7 Exit Review

- [ ] 能解释 RAG 与 Memory 的区别
- [ ] 能解释 Retrieval 与 Context 的关系
- [ ] 能解释为什么代码搜索不能只靠 Embedding
- [ ] 能比较 grep / vector / hybrid 的效果

---

# 10. Phase 8：Safety + Guardrails + Human-in-the-loop

**状态：大量内容已提前实践；当前冻结深入**

- [ ] **P8.1 Threat Model**
  - [x] 已在实现中接触 path escape / secret / dangerous command 等风险
  - [ ] Phase 8 正式进入时系统归纳 Prompt Injection / Tool Misuse / Exfiltration 等威胁
- [~] **P8.2 Tool Capability**
  - [x] Tool Capability / Permission 基础已实现
  - [ ] 正式学习时完成概念归纳
- [~] **P8.3 Policy Engine**
  - [x] `ALLOW / DENY / REQUIRE_APPROVAL`
  - [ ] 正式学习时完成边界复盘
- [~] **P8.4 Human-in-the-loop**
  - [x] CLI Human Approval 已实现
  - [ ] 正式学习时补生命周期归纳
- [~] **P8.5 Workspace Scope**
  - [x] Filesystem / Edit / Command 的工作区限制已实践
- [~] **P8.6 Secret Protection**
  - [x] Secret / Protected Resource 限制已实践
- [ ] **P8.7 Input / Output / Tool Guardrail**
- [~] **P8.8 Sandbox 概念总结**
  - [x] Bubblewrap Sandbox 基础已实现
  - [x] filesystem / network / process / env isolation 已实践
  - [ ] 正式学习时只做概念总结，不继续深挖
- [ ] **P8.9 安全回归实验**

### ADV：不阻塞主线

- [ ] ADV seccomp
- [ ] ADV cgroups
- [ ] ADV Container / VM Sandbox
- [ ] ADV macOS / Windows Sandbox
- [ ] ADV Network Egress Policy

**当前规则：不要继续实现这些 Advanced 项。**

---

# 11. Phase 9：Observability + Evaluation

**状态：未开始**

## Part A：Tracing / Observability

- [ ] **P9.1 Agent Run / Step / Span 模型**
- [ ] **P9.2 最小 Tracer**
- [ ] **P9.3 Structured Events**
- [ ] **P9.4 Trace Viewer / CLI Summary**

## Part B：Evaluation

- [ ] **P9.5 为什么 Agent 需要 Eval**
- [ ] **P9.6 Eval Dataset**
- [ ] **P9.7 Deterministic Evaluation**
- [ ] **P9.8 LLM-as-Judge**
- [ ] **P9.9 Metrics**
- [ ] **P9.10 Regression**

### Phase 9 Exit Review

- [ ] 拥有结构化 Trace
- [ ] 拥有固定 Eval Cases
- [ ] 能重复运行结果统计
- [ ] 能发现一次真实回归

---

# 12. Phase 10：Multi-Agent

**状态：未开始**

- [ ] **P10.1 Single Agent 的边界**
- [ ] **P10.2 Agent as Tool**
- [ ] **P10.3 Handoff**
- [ ] **P10.4 Manager Pattern**
- [ ] **P10.5 Context Isolation**
- [ ] **P10.6 Parallelism**
- [ ] **P10.7 Multi-Agent Evaluation**

### Phase 10 Exit Review

- [ ] 能判断一个任务是否真的需要 Multi-Agent
- [ ] 能实现 Agent-as-Tool
- [ ] 能实现 Handoff
- [ ] 能比较 Single Agent 与 Multi-Agent 的收益和成本

---

# 13. Framework Stages

## Framework Stage 1：OpenAI Agents SDK

- [ ] 映射 Agent / Runner / run loop
- [ ] 映射 Tools / function tools
- [ ] 映射 Run context / session state
- [ ] 映射 Sessions
- [ ] 映射 Guardrails / HITL
- [ ] 映射 Tracing
- [ ] 映射 Agent as Tool
- [ ] 映射 Handoff
- [ ] 用 Agents SDK 重写一个 MyAgent 子集
- [ ] Exit Review：能读懂 SDK 执行模型，而不只是会调 API

## Framework Stage 2：LangGraph

- [ ] State
- [ ] Node
- [ ] Edge
- [ ] Conditional Edge
- [ ] Checkpoint / Persistence
- [ ] Interrupt / HITL
- [ ] Durable Execution
- [ ] 用 Graph 重写一个已完成的 Planning Flow
- [ ] Exit Review：能解释 Graph 相对手写 Loop 的收益和成本

## Framework Stage 3：MCP

- [ ] Host / Client / Server
- [ ] Tool / Resource / Prompt
- [ ] Capability discovery / negotiation
- [ ] Lifecycle / Transport / Trust Boundary
- [ ] **MCP-1：写一个最小 MCP Server**
- [ ] **MCP-2：MyAgent 作为 MCP Client**
- [ ] **MCP-3：本地 Tool 与 MCP Tool 统一抽象**
- [ ] Exit Review：能明确 MCP 解决的是能力互操作问题

---

# 14. 当前打卡

## Current

```text
当前阶段：Phase 4 — Agent State + Runtime
当前课程：P4.5 Runtime Lifecycle
随后课程：P4.6 Error Boundary
下一阶段：Phase 5 — Planning
暂时冻结：Phase 8 Sandbox 深入优化
```

## P4.5 完成条件

- [ ] 定义最小 Runtime Status
- [ ] `AgentRuntime.run()` 在不同退出路径写入正确状态
- [ ] `max_steps` 不再只表现为一个孤立异常，而有明确 Runtime 语义
- [ ] 增加最小测试
- [ ] 自己能够解释状态机为什么属于 Runtime，而不是 LLM

---

# 15. 每节课打卡模板

完成一节课后，在本文件相应条目勾选，并可在下面追加一条简短记录：

```markdown
## YYYY-MM-DD — P?.? 课程名

- 状态：✅ 完成
- 核心概念：
- 代码改动：
- 实验结果：
- 我现在能解释的问题：
- 仍然不清楚的问题：
- 下一课：
```

打卡的重点不是记录写了多少代码，而是确认：

> **这个 Agent 概念是否已经真正理解，并能通过代码和实验解释。**

---

# 16. 历史打卡

## 2026-08 — 课程路线重新基线化

- 状态：✅ 完成
- 结论：前期已完成 Agent Loop、Tool Runtime、Context Compaction，并提前进入 Safety/Sandbox 深水区。
- 调整：冻结 Sandbox 深入优化，回到 10 Phase 主线。
- 编号修正：所有课程号以 `learning-roadmap.md` 为唯一来源，完成细项不再自行扩展 `P?.?` 编号。
- 当前：Phase 4 收尾，下一课为 P4.5 Runtime Lifecycle。
- 下一主要阶段：Phase 5 Planning。
