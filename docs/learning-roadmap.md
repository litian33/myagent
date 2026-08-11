# MyAgent AI Agent 开发学习课程大纲

> 目标：通过从零手工实现一个完整 AI Agent，系统掌握现代 Agent 的核心原理、运行时设计和工程方法，而不是只会使用某个框架。

MyAgent 是整套课程的学习载体。课程以 Coding Agent 为实践场景，但学习目标不是把它无限打磨成生产级 Coding Agent，而是借它走完整个 Agent 知识体系。

---

## 1. 课程目标

完成课程后，应能够从架构角度理解并独立实现：

```text
Agent
=
LLM
+ Instructions / Prompt
+ Context
+ State
+ Tools
+ Agent Loop
+ Planning
+ Memory
+ Retrieval / RAG
+ Guardrails / HITL
+ Persistence
+ Observability
+ Evaluation
+ Multi-Agent
```

并能够回答：

- LLM 应用与 Agent 的本质区别是什么？
- Tool Calling 到底是谁决定、谁执行、谁负责安全？
- Agent State、History、Context、Memory 分别是什么？
- Agent 如何规划、执行、观察、修正计划并判断任务完成？
- 长任务为什么需要 Context Management 和 Compaction？
- RAG、Memory、Context 三者分别解决什么问题？
- Human-in-the-loop、Guardrail、Permission、Sandbox 有什么区别？
- 如何通过 Trace 和 Eval 判断 Agent 是否真的变好？
- 什么情况下应该使用 Multi-Agent，什么情况下不应该？
- OpenAI Agents SDK、LangGraph、MCP 分别解决哪一层问题？

---

## 2. 学习方法

整个课程遵循以下原则。

### 2.1 先手写核心，再学习框架

主线顺序固定为：

```text
手写 MyAgent
    ↓
OpenAI Agents SDK
    ↓
LangGraph
    ↓
MCP
```

不在核心概念还没有亲手实现前，用框架替代学习过程。

### 2.2 每节课只引入一个主要概念

默认节奏：

```text
原理
 ↓
最小实现
 ↓
运行实验
 ↓
观察日志/行为
 ↓
总结边界
 ↓
进入下一概念
```

### 2.3 先看到问题，再产生抽象

不为了“架构漂亮”提前引入大量接口、层次和模式。只有当当前实现真实暴露问题后，再引入新的抽象。

### 2.4 每个 Phase 都必须有 Exit Criteria

达到退出标准后立即进入下一阶段，不因为某个局部方向还有优化空间而继续深入。

### 2.5 Advanced 内容不阻塞主线

以下类型内容默认属于 Advanced：

- 复杂 Linux Sandbox / namespace / seccomp / cgroups
- 极致 Tokenizer 精度和多 Provider 兼容
- 高级 Reranker / Retrieval Pipeline
- 分布式 Agent Runtime
- 复杂 Durable Workflow
- 大规模 Multi-Agent 调度

它们可以以后专题深入，但不能阻塞 10 个 Phase 的完整学习。

---

# Phase 1：LLM Application 基础

## 学习目标

理解 LLM API 是 Agent 的基础能力，但单次 LLM 调用本身不是 Agent。

## 核心知识

- Model / Provider / SDK
- Responses API 基本调用
- `instructions` 与 `input`
- Response 与 Output Item
- Token 与 Context Window
- Structured Output
- Function Calling 基本协议
- Streaming 的基本概念
- 非确定性模型与确定性程序的边界

## 课程

### P1.1 最小 LLM 调用

实现：

```text
User → LLM → Text
```

理解 SDK Client、model、instructions、input、output_text。

### P1.2 观察真实 Response 结构

不只读取 `output_text`，而是理解：

```text
Response
 └── output[]
      ├── message
      ├── reasoning
      └── function_call
```

### P1.3 Structured Output 与类型边界

理解 LLM 输出如何进入确定性程序，以及为什么 Schema / 类型约束重要。

### P1.4 Function Calling 协议预览

理解：

```text
LLM 生成 Tool Call
≠
LLM 执行 Tool
```

## 实践结果

可以通过最小 Python 程序调用模型，并读懂 Responses API 的关键输入输出结构。

## Exit Criteria

能够清楚解释：

- 为什么 LLM API 返回的不只是字符串？
- `instructions` 和用户任务有什么区别？
- 为什么 Function Calling 仍然只是模型输出？
- 为什么 LLM 的非确定性会影响 Agent 工程？

---

# Phase 2：Agent Loop

## 学习目标

亲手实现第一个真正的 Agent，理解 Agent 的核心循环。

## 核心模型

```text
Goal
 ↓
LLM
 ↓
Action
 ↓
Environment
 ↓
Observation
 └────→ LLM
```

也就是：

```text
Reason → Act → Observe → Reason ...
```

## 课程

### P2.1 第一个 `list_files` Tool

手工完成：

```text
Python Function
 ↓
Tool Schema
 ↓
LLM function_call
 ↓
参数反序列化
 ↓
执行函数
 ↓
function_call_output
 ↓
LLM Final Answer
```

### P2.2 多轮 Tool Call

理解一次 Tool 调用为什么不够。

### P2.3 第一个 `while` Agent Loop

从写死的 first/second response 重构为：

```python
while not finished:
    response = call_model()
    if has_tool_calls(response):
        execute_tools()
        continue
    return final_answer
```

### P2.4 Stop Conditions

引入：

- Final Answer
- `max_steps`
- Tool failure
- Model failure

### P2.5 多 Tool Call

理解一个模型 Step 中出现多个 function call 时 Runtime 如何处理。

## 实践结果

形成最小但真实的 Agent Loop。

## Exit Criteria

能够从零写出并解释：

```text
LLM → Tool Call → Runtime → Tool Result → LLM
```

并明确：

> LLM 决定下一步做什么，Runtime 决定如何执行。

---

# Phase 3：Tool Runtime

## 学习目标

从几个写死的函数调用演进成通用 Tool Runtime，理解 Agent 如何获得外部能力。

## 核心知识

- Tool implementation
- Tool schema
- Tool description
- JSON Schema
- Schema validation
- Tool Registry
- Tool Dispatch
- Tool Result / Tool Error
- Tool Capability
- Tool schema 自动生成

## 课程

### P3.1 从 `if/elif` 到 Tool Registry

把：

```text
if tool == read_file
if tool == list_files
...
```

重构为动态注册和派发。

### P3.2 Tool 模型

明确一个 Tool 至少包含：

```text
name
description
schema
handler
capability
```

### P3.3 类型注解生成 Schema

利用 Python type hints / annotation 减少 Tool 实现与 Schema 多源维护。

### P3.4 Filesystem Tools

实现或整理：

- `list_files`
- `read_file`
- 搜索类能力

### P3.5 Shell Tool

最小实现 `run_command`，理解：

- argv
- cwd
- timeout
- exit code
- stdout/stderr
- output truncation

### P3.6 Editing Tools

实现：

- `write_file`
- `apply_patch`
- optimistic concurrency / expected hash

重点学习 Tool 契约，不在这里无限扩充 Coding Agent 功能。

## 实践结果

形成独立的 Tool / ToolRegistry / Schema / Executor 体系。

## Exit Criteria

能够回答：

- Tool 和普通函数是什么关系？
- Tool Schema 为什么同时是接口定义和模型决策提示？
- Tool Registry 解决什么问题？
- Tool Error 应该如何重新进入 Observation？

达到标准后冻结 Tool Runtime 基础建设，后续只按课程需要新增 Tool。

---

# Phase 4：Agent State + Runtime

## 学习目标

从“能循环调用 Tool 的脚本”演进成具有明确 State、Context 和 Lifecycle 的 Agent Runtime。

## 核心知识

```text
Agent
AgentRuntime
AgentState
History
Context
Lifecycle
Error Boundary
```

## 课程

### P4.1 AgentState

区分：

```text
Task
Step
HistoryBlock
Model Output
Tool Output
```

### P4.2 History 与 Context

建立关键认知：

```text
State = Runtime 当前真正掌握的状态
Context = 本轮实际发送给模型的 State 子集
```

### P4.3 Token Budget

理解 Context Window、Output Reserve、Safety Margin，以及本地 Token 估算的作用。

### P4.4 Context Compaction

理解：

```text
Raw History = 真实发生的历史
Compaction = 有损的工作摘要
Context = 本轮工作集
```

并实现 Build → Compact → Rebuild。

### P4.5 Runtime Lifecycle

补齐最小生命周期：

```text
CREATED
 ↓
RUNNING
 ↓
COMPLETED

FAILED
MAX_STEPS_REACHED
CANCELLED（概念）
WAITING_APPROVAL（需要时）
```

### P4.6 Error Boundary

区分：

- Model Error
- Tool Error
- Context Error
- Runtime Error

理解 retryable / non-retryable，而不进入复杂容错系统。

## 实践结果

`AgentRuntime`、`AgentState`、`ContextManager` 各自职责清晰。

## Exit Criteria

能够准确解释：

> Agent、AgentRuntime、AgentState、Raw History、Context、Compaction 分别是什么？

并能通过 Runtime 状态判断任务是成功、失败还是超过执行限制。

---

# Phase 5：Planning

## 学习目标

从纯 Reactive Agent 进入 Goal → Plan → Execute → Replan，理解 Agent 如何处理复杂任务。

这是 Phase 4 完成后的下一重点阶段。

## 核心知识

- ReAct
- Goal
- Plan
- PlanStep
- Todo / Task State
- Planner / Executor
- Plan-and-Execute
- Replanning
- Reflection 的合理边界
- Completion Criteria

## 课程

### P5.1 Reactive Agent 与 ReAct

复盘当前 Agent：

```text
Goal
 ↓
LLM
 ↓
Next Action
 ↓
Observation
 ↓
LLM
```

理解它的优点和长任务局限。

### P5.2 Goal、Plan、Todo、Action 的区别

建立明确模型：

```text
Goal
 └── Plan
      ├── PlanStep
      └── PlanStep
           └── Action
```

### P5.3 最小 Planner

引入：

```text
Plan
PlanStep
PlanStepStatus
```

使 Agent 能先生成可检查的任务计划。

### P5.4 Executor

Planner 负责“准备怎么做”，Executor 负责执行下一步，不把两者混成一段 Prompt。

### P5.5 Progress Update

每完成一步，根据 Observation 更新：

```text
PENDING
IN_PROGRESS
COMPLETED
FAILED
SKIPPED
```

### P5.6 Replanning

遇到：

- 文件不存在
- 测试结果与预期不同
- 已有假设被事实推翻

时允许调整计划，而不是机械执行旧 Plan。

### P5.7 Completion Criteria

学习区分：

```text
模型说“完成了”
≠
任务真的完成
```

Coding Agent 中至少考虑：

```text
修改完成
+ diff inspected
+ relevant tests/checks passed
= 更可信的完成判断
```

### P5.8 Phase 实验：完整修复任务

给 MyAgent 一个真实的小型失败案例，让它：

```text
分析任务
→ 制定计划
→ 调查
→ 修改
→ 验证
→ 必要时 Replan
→ 完成
```

## Exit Criteria

能够解释 ReAct 与 Plan-and-Execute 的差异，并能让 MyAgent 对一个多步骤任务维护显式 Plan 和 Progress。

---

# Phase 6：Context + Memory

## 学习目标

彻底区分 Context Management 与 Memory，并让 Agent 第一次具备跨 Turn、跨运行保存信息的能力。

## 核心分类

```text
Context
Working Memory
Conversation / Session Memory
Task Memory
Long-term Memory
Knowledge
```

## 课程

### P6.1 Context Engineering 复盘

整理已经实现的：

- History
- Token Budget
- Sliding Selection
- Compaction
- Working Context

到这里不再深挖压缩算法。

### P6.2 Memory Taxonomy

通过具体案例区分：

- 当前任务发现的临时事实
- 当前会话历史
- 用户长期偏好
- 项目长期事实
- 外部知识库

### P6.3 Multi-turn Session

让 MyAgent 不再只处理一次 `input()`，而能够在同一个 Session 中连续对话和执行。

### P6.4 Memory Store

使用简单 SQLite 实现：

```text
put
get
search
delete
```

先掌握抽象，不引入复杂 Memory Framework。

### P6.5 Memory Write Policy

学习一个关键问题：

> 什么值得写入长期记忆？

避免把所有对话无差别保存成“Memory”。

### P6.6 Memory Retrieval

学习：

> Memory 存在数据库里，不等于模型每轮都应该看到全部 Memory。

实现按任务相关性 Recall。

### P6.7 Restart 实验

退出 MyAgent 后重新启动，让新任务能够召回此前保存的少量长期事实。

## Exit Criteria

能够清楚区分：

```text
Context ≠ History ≠ Compaction ≠ Session Memory ≠ Long-term Memory ≠ Knowledge Base
```

---

# Phase 7：RAG / Knowledge Retrieval

## 学习目标

从零理解 Retrieval-Augmented Generation，不把 RAG 简化成“接一个向量数据库”。

## 核心知识

- Document
- Chunk
- Metadata
- Embedding
- Similarity
- Top-K
- Lexical Search
- BM25 概念
- Vector Search
- Hybrid Retrieval
- Ranking / Reranking 概念
- Retrieval Context

## 课程

### P7.1 为什么需要 Retrieval

理解 Context Window 不是知识库，Agent 也不应该把整个仓库永久塞进 Context。

### P7.2 Document → Chunk → Metadata

自己定义最小索引数据模型。

### P7.3 Embedding

理解文本向量、语义相似度和 Embedding 的适用边界。

### P7.4 最小 Vector Retrieval

实现：

```text
query
 ↓
embedding
 ↓
search
 ↓
top-k
 ↓
context
```

### P7.5 Lexical Search / BM25

理解代码、标识符、错误码等场景下，关键词检索为什么仍然重要。

### P7.6 Hybrid Retrieval

组合 lexical + semantic candidates，理解为什么检索通常不是单一算法。

### P7.7 Metadata Filtering

针对代码仓库引入 path / language / file type 等基本过滤。

### P7.8 Code RAG

对当前代码库建立最小索引：

```text
Repository
 ↓
Code Index
 ↓
Retrieve Relevant Code
 ↓
MyAgent Context
```

### P7.9 Retrieval Quality 实验

比较：

- 纯 grep
- 纯 vector
- hybrid

在几个固定任务上的结果。

## Exit Criteria

能够解释：

- RAG 与 Memory 的区别
- Retrieval 与 Context 的关系
- 为什么代码搜索不能只靠 Embedding
- Top-K 结果为什么还需要质量控制

---

# Phase 8：Safety + Guardrails + Human-in-the-loop

## 学习目标

建立完整的 Agent 安全边界模型，而不是把安全等同于 Shell Sandbox。

> 当前 MyAgent 已经提前实现了这一阶段的一部分能力。后续本阶段以概念收束、补齐边界和验证为主，不继续深挖 Bubblewrap。

## 核心知识

```text
LLM Decision
      ↓
Tool Request
      ↓
Validation
      ↓
Policy
      ↓
ALLOW / DENY / REQUIRE_APPROVAL
      ↓
Execution Boundary
```

## 课程

### P8.1 Threat Model

讨论 Agent 真实风险：

- Prompt Injection
- Tool Misuse
- Secret Exposure
- Path Escape
- Dangerous Command
- Network Exfiltration
- Destructive Write
- Untrusted Repository Content

### P8.2 Tool Capability

为 Tool 定义能力分类，而不是只根据函数名判断风险。

### P8.3 Policy Engine

实现/整理：

```text
ALLOW
DENY
REQUIRE_APPROVAL
```

### P8.4 Human-in-the-loop

让高风险动作在 Runtime 层暂停并请求用户确认。

### P8.5 Workspace Scope

保证 Filesystem / Edit / Command 能力遵守工作目录边界。

### P8.6 Secret Protection

避免 `.env`、凭证、私钥、Git remote credential 等资源被 Agent 或不可信代码读取。

### P8.7 Input / Output / Tool Guardrail

理解三种 Guardrail 的不同位置和职责。

### P8.8 Sandbox 概念总结

当前已有 Bubblewrap 实践，只需总结：

- filesystem isolation
- network isolation
- process isolation
- environment isolation

不继续把主线扩展到 seccomp、cgroups、容器安全体系。

### P8.9 安全回归实验

构造固定场景验证：

- workspace escape 被拒绝
- secret access 被拒绝
- 高风险 Tool 进入 approval
- 未批准后 Agent 不重复绕过
- sandbox 不可用时行为符合配置

## Advanced（不阻塞主线）

- seccomp
- cgroups
- container / VM isolation
- macOS / Windows sandbox
- 复杂 command parser
- 网络 egress policy

## Exit Criteria

能够解释 Permission、Policy、Guardrail、HITL、Workspace Isolation、Sandbox 各自解决什么问题，并拥有一组可重复执行的安全测试。

---

# Phase 9：Observability + Evaluation

## 学习目标

从“感觉 Agent 能工作”进入可观察、可度量、可回归的 Agent Engineering。

## Part A：Tracing / Observability

### P9.1 Agent Run / Step / Span 模型

设计：

```text
AgentRun
 ├── AgentStep
 │    ├── ModelCall
 │    └── ToolCall
 ├── AgentStep
 └── FinalResult
```

### P9.2 最小 Tracer

记录：

- run id
- step
- model
- latency
- input/output tokens
- tool name
- arguments
- result summary
- error

### P9.3 Structured Events

从 `print()` 日志升级为可测试的 Runtime Event。

### P9.4 Trace Viewer / CLI Summary

先做最小文本输出，不为了 UI 分散课程注意力。

## Part B：Evaluation

### P9.5 为什么 Agent 需要 Eval

理解传统单元测试不足以评价非确定性 Agent。

### P9.6 Eval Dataset

建立固定任务集，例如：

- 定位文件
- 查找符号
- 分析错误
- 修改小 Bug
- 拒绝危险动作
- 正确请求 Approval

### P9.7 Deterministic Evaluation

可程序判断的指标优先程序判断：

- 是否生成预期文件
- 测试是否通过
- 是否访问禁区
- Tool 是否调用成功

### P9.8 LLM-as-Judge

仅对难以完全程序化判断的结果使用 Judge，并理解它也具有不确定性。

### P9.9 Metrics

最少关注：

```text
Task Success Rate
Tool Success Rate
Average Steps
Token Usage
Latency
Safety Violation Rate
```

### P9.10 Regression

每次修改 Agent 后重复运行 Eval，比较：

```text
不是“感觉更聪明”
而是行为和指标是否真的改善
```

## Exit Criteria

MyAgent 至少拥有：

- 结构化 Trace
- 一组固定 Eval Cases
- 可重复运行的结果统计
- 能发现一次真实回归

---

# Phase 10：Multi-Agent

## 学习目标

在单 Agent 核心能力完整后，再学习真正需要 Multi-Agent 的场景和协作模式。

## 第一原则

先学：

> 什么情况下不应该使用 Multi-Agent。

不要为了“看起来像 Agent 系统”创建大量角色。

## 课程

### P10.1 Single Agent 的边界

识别 Multi-Agent 可能真正解决的问题：

- Context Isolation
- Specialized Capability
- Independent Review
- Parallel Work
- Ownership / Handoff

### P10.2 Agent as Tool

实现：

```text
Main Agent
   ↓
research(...)
   ↓
Research Agent
   ↓
Result
   ↓
Main Agent
```

主 Agent 保持控制权。

### P10.3 Handoff

实现：

```text
Agent A
  ↓ transfer control
Agent B
```

理解 Handoff 和 Agent-as-Tool 的本质区别。

### P10.4 Manager Pattern

设计一个最小 Manager：

```text
          Manager
         /   |   \
    Coder  Reviewer  Researcher
```

避免无限层级。

### P10.5 Context Isolation

理解 Sub-Agent 的重要价值之一是减少 Context 污染，而不只是“角色扮演”。

### P10.6 Parallelism

区分：

- parallel tool calls
- parallel agents
- dependency graph

### P10.7 Multi-Agent Evaluation

比较同一任务：

```text
Single Agent
vs
Multi-Agent
```

从成功率、Token、延迟、复杂度判断是否值得。

## Exit Criteria

能够独立判断一个任务是否需要 Multi-Agent，并实现 Agent-as-Tool 与 Handoff 两种最小模式，而不是用多个 Agent 替代清晰的软件设计。

---

# Framework Stage 1：OpenAI Agents SDK

10 个手写阶段完成后，再开始框架映射。

## 学习目标

不是重新学 Agent，而是把已经亲手实现的概念映射到 SDK。

## 重点映射

```text
MyAgent                     Agents SDK
------------------------------------------------
Agent Runtime               Runner / run loop
Tool / ToolRegistry         Tools / function tools
Agent State                 Run context / session state
Memory                      Sessions
Policy / Approval           Guardrails / HITL
Tracing                     Tracing
Sub-Agent                   Agent as Tool
Delegation                  Handoff
```

## 实践

选择 MyAgent 的一个小版本，用 Agents SDK 重写，并逐项比较：

- SDK 隐藏了什么？
- 哪些控制能力更方便？
- 哪些地方手写 Runtime 更灵活？

## Exit Criteria

能读懂 Agents SDK 的执行模型，而不是停留在 API 用法。

---

# Framework Stage 2：LangGraph

## 学习目标

理解什么时候 `while` Agent Loop 足够，什么时候需要显式 Graph / Workflow。

## 重点知识

- State
- Node
- Edge
- Conditional Edge
- Checkpoint
- Persistence
- Interrupt
- Human-in-the-loop
- Durable Execution

## 实践

把一个已经完成的 Planning Flow 重写成：

```text
Planner Node
 ↓
Executor Node
 ↓
Verifier Node
 ↘ conditional edge / replan
```

## Exit Criteria

能解释 Graph 模型相对于手写 Loop 的收益和成本，并知道什么时候不需要 LangGraph。

---

# Framework Stage 3：MCP

## 学习目标

理解 MCP 不是 Agent 本身，而是 Agent/Host 与外部能力之间的标准化连接协议。

## 重点知识

- Host
- Client
- Server
- Tool
- Resource
- Prompt
- Capability discovery / negotiation
- Lifecycle
- Transport
- Trust boundary

## 实践

### MCP-1：写一个最小 MCP Server

暴露一个简单 Tool。

### MCP-2：MyAgent 作为 MCP Client

完成：

```text
MyAgent
 ↓
MCP Client
 ↓
Discover Tools
 ↓
Call MCP Tool
 ↓
Observation
 ↓
Agent Loop
```

### MCP-3：本地 Tool 与 MCP Tool 统一抽象

理解本地 Tool Registry 如何与远程 MCP Capability 共存。

## Exit Criteria

能够自己实现一个 MCP Server 和 Client，并明确 MCP 解决的是能力互操作问题，而不是 Planning、Memory 或 Multi-Agent 本身。

---

# 3. 最终综合项目

完成所有阶段后，让 MyAgent 具备一个教学意义完整的 Coding Agent 闭环：

```text
User Goal
   ↓
Session / Memory Recall
   ↓
Planning
   ↓
Agent Runtime
   ↓
Context Builder
   ↓
LLM
   ↓
Tool / MCP Capability
   ↓
Policy / Approval
   ↓
Execution
   ↓
Observation
   ↓
Plan Update / Replan
   ↓
Verification
   ↓
Completion Criteria
   ↓
Final Answer

整个过程同时产生：
Trace + Metrics + Eval Evidence
```

最终项目应以“概念清晰、模块职责清晰、可以实验和测试”为目标，而不是追求生产级功能数量。

---

# 4. 当前项目学习基线

截至本课程大纲建立时，MyAgent 已经实际覆盖多个阶段：

| Phase | 当前状态 | 说明 |
|---|---|---|
| Phase 1 | 已完成 | LLM / Responses API / typed request 基础已经掌握 |
| Phase 2 | 已完成 | 已有真实 Agent Loop 和多 Tool Call |
| Phase 3 | 基本完成 | Tool Registry、filesystem、shell、editing 已有实现 |
| Phase 4 | 进行中 | State、Context、Token Budget、Compaction 已有实现；应补 Runtime Lifecycle / Error Boundary 后退出 |
| Phase 5 | 未开始 | 下一主要学习阶段 |
| Phase 6 | 部分提前完成 | Context 已较深入；真正 Session / Long-term Memory 未开始 |
| Phase 7 | 未开始 | RAG / Retrieval 尚未系统学习 |
| Phase 8 | 部分提前完成 | Tool Policy、Approval、Workspace、Secret Protection、Bubblewrap 已经实现不少；暂时冻结深入 |
| Phase 9 | 未开始 | Tracing / Evaluation 尚未系统实现 |
| Phase 10 | 未开始 | Multi-Agent 尚未开始 |

当前推荐学习顺序：

```text
P4.5 Runtime Lifecycle
        ↓
P4.6 Error Boundary
        ↓
Phase 4 Exit Review
        ↓
Phase 5 Planning
```

Phase 8 的 Sandbox 方向暂时冻结，等主线走到 Phase 8 时再统一复盘。

---

# 5. 课程防偏规则

以后每次准备进入新内容时，都用下面 5 个问题检查：

1. 这个内容属于当前 Phase 吗？
2. 它是否直接帮助达到当前 Phase 的 Exit Criteria？
3. 如果不做它，会阻塞后续主线吗？
4. 它是在学习 Agent 核心概念，还是在优化一个局部工程细节？
5. 如果属于 Advanced，是否应该先记录下来而不是现在实现？

只要第 2、3 项答案都是否，就默认不在当前阶段继续深入。

---

# 6. 学习进度

实际完成情况统一维护在：

- [学习进度打卡表](./learning-progress.md)

本文件只维护课程结构、学习目标和退出标准，避免“课程大纲”和“每日进度”混在一起。
