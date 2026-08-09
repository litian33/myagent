从零开始手搓自己的Agent，学习Agent开发。

初步具备Human in the loop.

添加安全沙箱。

## 运行前提

命令沙箱基于 bubblewrap（bwrap），仅支持 Linux：

- 安装：`sudo apt install bubblewrap`（Debian/Ubuntu）
- 需要内核允许非特权用户命名空间
  （`sysctl kernel.unprivileged_userns_clone=1`）

bwrap 缺失或沙箱不可用时，默认回退到本地命令执行器（无沙箱）；
设置 `MYAGENT_REQUIRE_SANDBOX=1` 可强制要求沙箱并直接报错。


                        LLM
                         │
                         ▼
                    Tool Call
                         │
                         ▼
                  ToolPermission
                         │
                 Human Approval
                         │
                         ▼
                   run_command
                         │
              Command Validation
                         │
                  Workspace Scope
                         │
                         ▼
                  CommandRequest
                         │
                         ▼
              CommandExecutor Port
                         │
                         ▼
           BubblewrapCommandExecutor
                         │
          ┌──────────────┼──────────────┐
          │              │              │
        Mount          Namespace      Env
        Policy          Policy       Policy
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
               Untrusted Repo Code
                         │
                         ▼
              CommandExecutionResult
                         │
                         ▼
                   Observation
                         │
                         ▼
                        LLM
