import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.responses import (
    FunctionToolParam,
)

from agent.compaction import ContextCompactor
from agent.completion_evaluator import (
    CompletionEvaluator,
)
from agent.context import ContextManager
from agent.control import PlanningController
from agent.executor import PlanExecutor
from agent.runtime import AgentRuntime
from execution.bubblewrap import (
    BubblewrapCommandExecutor,
    BubblewrapConfig,
)
from execution.command import (
    CommandExecutor,
    LocalCommandExecutor,
)
from policy.approval import (
    CliApprovalHandler,
)
from policy.engine import ToolPolicy
from tools.edit import (
    create_apply_patch_tool,
    create_write_file_tool,
)
from tools.filesystem import (
    create_filesystem_tools,
)
from tools.registry import ToolRegistry
from tools.shell import (
    create_run_command_tool,
)
from tools.token import create_token_counter
from tools.workspace import (
    Workspace,
)

INSTRUCTIONS = """
You are MyAgent, a coding assistant.
You must use the runtime planning protocol.

At the beginning of a task:
- call agent_create_plan;
- create concise plan steps;
- create concrete completion criteria.

The runtime automatically starts the next plan step.

While executing a plan step:
- use environment tools to act and observe;
- after observing tool results, use
  agent_update_progress in a later response;
- do not mix environment tool calls and planning
  control calls in the same response.

Use:
- continue when the current step still needs work;
- completed only when the current step is actually done;
- failed when the current plan step cannot be completed
  under the current plan.

After a failed step:
- call agent_replan before continuing execution.

Use agent_satisfy_criterion only when concrete evidence
already observed during execution supports the criterion.

A plain text response does not finish the task.

Use agent_finish only after:
- the plan is complete; and
- every completion criterion is satisfied.

The summary passed to agent_finish is the final answer
shown to the user.

Use the available tools when you need information
from the local environment.

Do not guess file contents.
Read files when their contents are needed.

When modifying an existing file:
1. read the current file;
2. use the sha256 returned by read_file as
   expected_sha256;
3. prefer apply_patch for localized edits;
4. use write_file only for creating files or when
   a complete replacement is genuinely appropriate;
5. never invent expected_sha256.

For apply_patch:
- old_text must be copied exactly from the current
  file content;
- include enough surrounding text to make old_text
  unique;
- if the patch is rejected, read the file again
  rather than guessing.

After modifying code:
1. inspect git diff;
2. run relevant tests or static checks;
3. fix problems if necessary;
4. do not claim success until verification passes.

Use expected_sha256="MISSING" only when creating
a new file with write_file.

Do not attempt destructive commands, network access,
or changes outside the workspace.

If a tool call is denied by policy or not approved
by the user, do not retry the same action unless
the user explicitly asks you to reconsider it.

All filesystem access is restricted to the current
workspace.

Protected or secret resources must not be accessed.

If access to a file is denied by the workspace,
do not attempt to bypass the restriction using
run_command, git, Python, shell commands, symlinks,
or alternative paths.

Do not request or expose credentials, API keys,
private keys, tokens, or environment secrets.
"""


def create_tool_registry(
    *,
    workspace: Workspace,
    command_executor: CommandExecutor,
) -> ToolRegistry:
    registry = ToolRegistry()

    for tool in create_filesystem_tools(workspace=workspace):
        registry.register(tool)

    registry.register(
        create_run_command_tool(
            workspace=workspace,
            executor=(command_executor),
        )
    )

    registry.register(
        create_write_file_tool(
            workspace=workspace,
        )
    )

    registry.register(
        create_apply_patch_tool(
            workspace=workspace,
        )
    )

    return registry


def create_command_executor(
    *,
    workspace: Workspace,
) -> CommandExecutor:
    if sys.platform.startswith("linux"):
        config = BubblewrapConfig(
            runtime_roots=(Path("/usr/local/go"),),
            extra_path_entries=("/usr/local/go/bin",),
        )

        try:
            executor = BubblewrapCommandExecutor(
                workspace=workspace,
                config=config,
            )

            executor.verify()

            return executor

        except (RuntimeError, ValueError, OSError) as exc:
            require_sandbox = (
                os.getenv(
                    "MYAGENT_REQUIRE_SANDBOX",
                    "",
                )
                .strip()
                .lower()
            )

            if require_sandbox in {
                "1",
                "true",
                "yes",
            }:
                raise

            print(
                "[warning] bubblewrap sandbox unavailable: "
                f"{exc}\n"
                "The sandbox requires Linux with bubblewrap installed "
                "(e.g. 'sudo apt install bubblewrap'). "
            )

            raise
    return LocalCommandExecutor()


def main() -> None:
    load_dotenv()

    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    context_window_tokens = int(os.environ["OPENAI_CONTEXT_WINDOW_TOKENS"])

    max_output_tokens = int(
        os.getenv(
            "OPENAI_MAX_OUTPUT_TOKENS",
            "4096",
        )
    )

    safety_margin_tokens = int(
        os.getenv(
            "MYAGENT_CONTEXT_SAFETY_MARGIN_TOKENS",
            "1024",
        )
    )

    max_input_tokens = context_window_tokens - max_output_tokens - safety_margin_tokens

    if max_input_tokens <= 0:
        raise ValueError(
            "Invalid context budget: "
            "context window must be larger than "
            "output reserve plus safety margin"
        )

    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-5.6-luna",
    )

    workspace = Workspace(Path(__file__).resolve().parent)
    command_executor = create_command_executor(
        workspace=workspace,
    )

    registry = create_tool_registry(
        workspace=workspace,
        command_executor=(command_executor),
    )

    plan_executor = PlanExecutor()
    completion_evaluator = CompletionEvaluator()
    planning = PlanningController(
        executor=plan_executor,
        completion=completion_evaluator,
    )

    model_tools: list[FunctionToolParam] = [
        *registry.schemas(),
        *planning.schemas(),
    ]
    token_counter = create_token_counter(
        instructions=INSTRUCTIONS,
        tools=model_tools,
    )

    context = ContextManager(
        count_tokens=token_counter,
        max_input_tokens=max_input_tokens,
    )
    compactor = ContextCompactor(
        client=client,
        model=model,
        max_output_tokens=2048,
    )
    policy = ToolPolicy()

    approval = CliApprovalHandler()
    agent = AgentRuntime(
        client=client,
        model=model,
        instructions=INSTRUCTIONS,
        tools=registry,
        model_tools=model_tools,
        planning=planning,
        plan_executor=plan_executor,
        context=context,
        compactor=compactor,
        policy=policy,
        approval=approval,
        max_output_tokens=max_output_tokens,
        max_steps=20,
    )

    task = input("You: ").strip()

    if not task:
        return

    result = agent.run(task)

    print()
    print(f"[status] {result.status.value}")

    if result.output is not None:
        print("[final answer]")
        print(result.output)

    if result.error is not None:
        print(
            "[error] "
            f"kind={result.error.kind.value}, "
            f"retryable={result.error.retryable}"
        )
        print(result.error.message)


if __name__ == "__main__":
    main()
