# MyAgent

MyAgent 是一个 **AI Agent 开发学习与实践项目**。

项目目标不是直接使用现成 Agent Framework 拼装应用，而是从零开始手工实现 Agent 的核心能力，在代码实践中理解现代 AI Agent 的运行机制和工程设计。

## 学习目标

通过逐步实现 MyAgent，系统学习：

```text
LLM
 + Tools
 + Agent Loop
 + State / Context
 + Planning
 + Memory
 + RAG
 + Guardrails / HITL
 + Tracing / Evaluation
 + Multi-Agent
```

完成手写 Agent 主线后，再学习并对照：

```text
OpenAI Agents SDK
       ↓
LangGraph
       ↓
MCP
```

重点不是记住框架 API，而是理解框架替 Agent Runtime 解决了什么问题。

## 当前项目

MyAgent 目前已经具备一个 Coding Agent 的基础运行闭环，包括：

- OpenAI Responses API 模型调用
- Agent Loop
- Function Tool Calling
- Tool Registry
- Filesystem / Command / File Edit Tools
- Agent State 与 History
- Context Token Budget 与 Compaction
- Tool Policy 与 Human Approval
- Workspace / Secret 基础保护
- 可选的本地命令 Sandbox 实践

当前课程正在完成 **Agent State + Runtime** 阶段，随后进入 **Planning**。

## 学习文档

- [完整学习课程大纲](docs/learning-roadmap.md)
- [学习进度打卡表](docs/learning-progress.md)

后续课程和代码演进都以这两份文档为基线，避免在某个局部能力上过度深入而偏离完整 Agent 学习主线。

## 运行入口

当前主要入口：

```bash
python main.py
```

模型、API 地址和 Context Window 等运行参数通过环境变量配置，具体以 `main.py` 当前实现为准。

## 项目原则

1. 先理解原理，再引入框架。
2. 先看到真实问题，再增加抽象。
3. 每个学习阶段达到 Exit Criteria 后立即进入下一阶段。
4. Advanced 工程优化不阻塞 Agent 核心知识主线。
5. 每个核心概念都尽量通过可运行代码和实验验证。

---

这是一个持续演进的学习项目，代码本身就是课程的一部分。
