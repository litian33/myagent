# MyAgent 学习进度打卡表

> 本文档只记录学习进度、完成证据和下一步，不扩展课程内容。
>
> 完整课程结构见：[AI Agent 开发学习课程大纲](./learning-roadmap.md)。

---

## 1. 状态约定

- `[x]`：已完成，并通过代码/实验验证
- `[~]`：部分完成，仍需补齐本 Phase 的 Exit Criteria
- `[ ]`：未开始
- `ADV`：Advanced，可选，不阻塞主线
- `提前完成`：因为历史课程顺序提前做过，但仍需在对应 Phase 做一次概念归纳和退出检查

---

## 2. 总体进度

| Phase | 主题 | 状态 | 当前结论 |
|---|---|---|---|
| Phase 1 | LLM Application 基础 | ✅ 完成 | 不再深入 Provider / Tokenizer 细节 |
| Phase 2 | Agent Loop | ✅ 完成 | 已形成真实 Tool Call → Observation → LLM 循环 |
| Phase 3 | Tool Runtime | ✅ 基本完成 | 基础设施冻结，后续按需增加 Tool |
| Phase 4 | Agent State + Runtime | 🟡 进行中 | State / Context / Compaction 已完成，补 Lifecycle / Error Boundary |
| Phase 5 | Planning | ⬜ 未开始 | **Phase 4 完成后立即进入** |
| Phase 6 | Context + Memory | 🟡 部分提前完成 | Context 已有实践，Session / Long-term Memory 未开始 |
| Phase 7 | RAG / Retrieval | ⬜ 未开始 | — |
| Phase 8 | Safety / Guardrails / HITL | 🟡 部分提前完成 | Policy / Approval / Sandbox 等已提前实现，当前冻结深入 |
| Phase 9 | Observability + Evaluation | ⬜ 未开始 | — |
| Phase 10 | Multi-Agent | ⬜ 未开始 | — |
| Framework 1 | OpenAI Agents SDK | ⬜ 未开始 | 10 个手写 Phase 完成后进入 |
| Framework 2 | LangGraph | ⬜ 未开始 | Agents SDK 之后 |
| Framework 3 | MCP | ⬜ 未开始 | 最后进入 |

---

# 3. Phase 1：LLM Application 基础

**状态：完成**

- [x] P1.1 最小 LLM 调用
- [x] P1.2 观察真实 Response / Output Item 结构
- [x] P1.3 理解 `instructions`、`input`、Response 的边界
- [x] P1.4 理解 Structured Output / typed request 的价值
- [x] P1.5 Function Calling 协议预览
- [x] 理解 LLM 非确定性与确定性 Runtime 的边界

### 完成证据

已使用 OpenAI Responses API 构造真实请求，并在后续阶段持续使用 SDK 类型定义构造输入和 Tool Output。

### Exit Review

- [x] 能解释 LLM 应用为什么还不是 Agent
- [x] 能解释 `function_call` 为什么仍只是模型生成的结构化 Action

---

# 4. Phase 2：Agent Loop

**状态：完成**

- [x] P2.1 实现第一个 `list_files` Tool
- [x] P2.2 执行 `function_call` 并返回 `function_call_output`
- [x] P2.3 从两次写死调用重构为 `while` / step loop
- [x] P2.4 支持连续多次 Tool Call
- [x] P2.5 支持一个 Step 中的多个 Tool Call
- [x] P2.6 引入 `max_steps` 运行约束
- [x] 模型无 Tool Call 时返回 Final Answer

### Exit Review

- [x] 能解释 `Reason → Act → Observe` 的真实代码对应关系
- [x] 能解释为什么 LLM 决策、Runtime 执行

---

# 5. Phase 3：Tool Runtime

**状态：基本完成，主线冻结扩展**

- [x] P3.1 从写死 Tool Dispatch 演进为 Tool Registry
- [x] P3.2 Tool 定义包含 name / description / schema / handler
- [x] P3.3 使用 Python 注解/类型减少 Schema 多源维护
- [x] P3.4 Filesystem Tools
- [x] P3.5 `run_command` Shell Tool
- [x] P3.6 timeout / cwd / exit code / stdout / stderr / output truncation
- [x] P3.7 `write_file`
- [x] P3.8 `apply_patch`
- [x] P3.9 文件修改使用 expected hash / optimistic concurrency 思路
- [x] Tool Unknown / Tool Error 能返回结构化 Observation

### Exit Review

- [x] 能解释 Tool Implementation 和 Tool Schema 的区别
- [x] 能解释 Tool Description 为什么也是模型决策的一部分
- [x] 能解释 Tool Registry 解决的扩展性问题

### 冻结项

以下内容不在当前阶段继续扩展：

- 更多 Shell 命令适配
- 更复杂 Patch Engine
- 更多 Git Tool
- 更复杂 Tool Middleware

除非后续 Phase 的实验明确需要。

---

# 6. Phase 4：Agent State + Runtime

**状态：进行中**

## 已完成

- [x] P4.1 引入 `AgentState`
- [x] P4.2 使用 `HistoryBlock` 保存每个 Agent Step
- [x] P4.3 分离 Raw History 与 Context
- [x] P4.4 引入 Context Manager
- [x] P4.5 引入 Context Token Budget
- [x] P4.6 本地 Token 计数/估算能力
- [x] P4.7 Context 超预算时选择 Working Set
- [x] P4.8 引入 Context Compaction
- [x] P4.9 Raw History 不因 Compaction 删除
- [x] P4.10 Build → Compact → Rebuild
- [x] 能区分 Raw History / State / Context / Compaction

## 当前下一课

- [ ] **P4.11 Runtime Lifecycle**

建议只实现最小状态：

```text
CREATED
RUNNING
COMPLETED
FAILED
MAX_STEPS_REACHED
```

`WAITING_APPROVAL` 可映射已有 HITL，`CANCELLED` 先理解概念即可。

## 随后完成

- [ ] P4.12 Error Boundary
  - [ ] Model Error
  - [ ] Tool Error
  - [ ] Context Error
  - [ ] Runtime Error
  - [ ] retryable / non-retryable 最小分类
- [ ] Phase 4 Exit Review

### Phase 4 Exit Criteria

- [ ] 能准确解释 Agent / AgentRuntime / AgentState / History / Context / Compaction
- [ ] Runtime 对任务结束原因有明确状态
- [ ] 主要错误边界清晰，不依赖到处 `try/except` 猜测状态

**完成后立即进入 Phase 5，不继续深入 Context/Sandbox。**

---

# 7. Phase 5：Planning

**状态：未开始；下一主要阶段**

- [ ] P5.1 Reactive Agent 与 ReAct
- [ ] P5.2 Goal / Plan / Todo / Action 的区别
- [ ] P5.3 `Plan` / `PlanStep` / `PlanStatus`
- [ ] P5.4 最小 Planner
- [ ] P5.5 Executor
- [ ] P5.6 Progress Update
- [ ] P5.7 Replanning
- [ ] P5.8 Completion Criteria
- [ ] P5.9 真实小型修复任务综合实验
- [ ] Phase 5 Exit Review

### Phase 5 实验目标

```text
Goal
 ↓
Plan
 ↓
Execute
 ↓
Observation
 ↓
Update Progress
 ↓
Replan if needed
 ↓
Verify
 ↓
Complete
```

---

# 8. Phase 6：Context + Memory

**状态：部分提前完成**

## Context 部分

- [x] History
- [x] Working Context
- [x] Token Budget
- [x] Compaction
- [x] Summary 与 Raw History 分离

## Memory 主线待学习

- [ ] P6.1 Memory Taxonomy
- [ ] P6.2 Multi-turn Session
- [ ] P6.3 Session State
- [ ] P6.4 SQLite `MemoryStore`
- [ ] P6.5 Memory Write Policy
- [ ] P6.6 Memory Retrieval / Recall
- [ ] P6.7 跨进程 Restart 实验
- [ ] Phase 6 Exit Review

### Exit Review 重点

- [ ] 能解释 Context ≠ Memory
- [ ] 能解释 Compaction Summary 为什么不是 Long-term Memory
- [ ] 能解释 Memory 为什么不能每轮全量塞进 Context

---

# 9. Phase 7：RAG / Retrieval

**状态：未开始**

- [ ] P7.1 为什么需要 Retrieval
- [ ] P7.2 Document / Chunk / Metadata
- [ ] P7.3 Embedding
- [ ] P7.4 Vector Similarity / Top-K
- [ ] P7.5 最小 Vector Retrieval
- [ ] P7.6 Lexical Search / BM25 概念
- [ ] P7.7 Hybrid Retrieval
- [ ] P7.8 Metadata Filter
- [ ] P7.9 Code Repository Index
- [ ] P7.10 grep vs vector vs hybrid 对比实验
- [ ] Phase 7 Exit Review

---

# 10. Phase 8：Safety + Guardrails + HITL

**状态：大量内容已提前实践；当前冻结深入**

## 已提前完成

- [x] Tool Capability / Permission 基础
- [x] `ALLOW / DENY / REQUIRE_APPROVAL`
- [x] CLI Human Approval
- [x] Workspace Scope
- [x] Filesystem 安全边界
- [x] Secret / Protected Resource 限制
- [x] 命令执行权限控制
- [x] Command Executor 抽象
- [x] Bubblewrap Sandbox 基础
- [x] 网络 / namespace / mount / env 隔离的实际实践

## Phase 8 正式学习时需要补齐/归纳

- [ ] P8.1 Threat Model
- [ ] P8.2 Prompt Injection 与 Untrusted Repository Content
- [ ] P8.3 Capability / Policy / Guardrail 的关系
- [ ] P8.4 Input Guardrail
- [ ] P8.5 Output Guardrail
- [ ] P8.6 Tool Guardrail
- [ ] P8.7 HITL 生命周期归纳
- [ ] P8.8 安全回归测试集
- [ ] Phase 8 Exit Review

## ADV：不阻塞主线

- [ ] ADV seccomp
- [ ] ADV cgroups
- [ ] ADV Container / VM Sandbox
- [ ] ADV 跨平台 Sandbox
- [ ] ADV Network Egress Policy

**规则：当前不要继续实现这些 Advanced 项。**

---

# 11. Phase 9：Observability + Evaluation

**状态：未开始**

## Tracing

- [ ] P9.1 AgentRun / AgentStep / ModelCall / ToolCall 模型
- [ ] P9.2 最小 Tracer
- [ ] P9.3 结构化 Runtime Event
- [ ] P9.4 latency / token / tool / error metrics
- [ ] P9.5 CLI Trace Summary

## Evaluation

- [ ] P9.6 Eval Dataset
- [ ] P9.7 Deterministic Eval
- [ ] P9.8 LLM-as-Judge
- [ ] P9.9 Task Success Rate
- [ ] P9.10 Tool Success Rate
- [ ] P9.11 Steps / Tokens / Latency
- [ ] P9.12 Safety Violation Rate
- [ ] P9.13 Regression Comparison
- [ ] Phase 9 Exit Review

---

# 12. Phase 10：Multi-Agent

**状态：未开始**

- [ ] P10.1 什么时候不应该使用 Multi-Agent
- [ ] P10.2 Single Agent 的真实边界
- [ ] P10.3 Agent as Tool
- [ ] P10.4 Handoff
- [ ] P10.5 Manager Pattern
- [ ] P10.6 Context Isolation
- [ ] P10.7 Parallel Tool vs Parallel Agent
- [ ] P10.8 Single vs Multi-Agent 对比 Eval
- [ ] Phase 10 Exit Review

---

# 13. Framework Stage

## OpenAI Agents SDK

- [ ] F1.1 Agent / Runner
- [ ] F1.2 Function Tool
- [ ] F1.3 Session
- [ ] F1.4 Guardrail / HITL
- [ ] F1.5 Tracing
- [ ] F1.6 Agent as Tool
- [ ] F1.7 Handoff
- [ ] F1.8 用 SDK 重写一个 MyAgent 子集
- [ ] F1 Exit Review

## LangGraph

- [ ] F2.1 State
- [ ] F2.2 Node / Edge
- [ ] F2.3 Conditional Edge
- [ ] F2.4 Checkpoint / Persistence
- [ ] F2.5 Interrupt / HITL
- [ ] F2.6 Durable Execution
- [ ] F2.7 用 Graph 重写 Planning Flow
- [ ] F2 Exit Review

## MCP

- [ ] F3.1 Host / Client / Server
- [ ] F3.2 Tools / Resources / Prompts
- [ ] F3.3 Capability Discovery
- [ ] F3.4 最小 MCP Server
- [ ] F3.5 MyAgent MCP Client
- [ ] F3.6 MCP Tool 接入 Agent Loop
- [ ] F3.7 本地 Tool 与 MCP Tool 的统一边界
- [ ] F3 Exit Review

---

# 14. 当前打卡

## Current

```text
当前阶段：Phase 4 — Agent State + Runtime
当前课程：P4.11 Runtime Lifecycle
下一阶段：Phase 5 — Planning
暂时冻结：Phase 8 Sandbox 深入优化
```

## 本轮课程完成条件

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
- 结论：前期已完成 Agent Loop、Tool Runtime、Context Compaction，并提前进入了 Safety/Sandbox 深水区。
- 调整：冻结 Sandbox 深入优化，回到 10 Phase 主线。
- 当前：Phase 4 收尾。
- 下一主要阶段：Phase 5 Planning。
