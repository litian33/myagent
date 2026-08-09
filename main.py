import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agent.compaction import ContextCompactor
from agent.context import ContextManager
from agent.runtime import AgentRuntime
from tools.edit import (
    create_apply_patch_tool,
    create_write_file_tool,
)
from tools.filesystem import FILESYSTEM_TOOLS
from tools.registry import ToolRegistry
from tools.shell import (
    create_run_command_tool,
)
from tools.token import create_token_counter

INSTRUCTIONS = """
You are MyAgent, a coding assistant.

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
"""


def create_tool_registry(
    *,
    workspace_root: Path,
) -> ToolRegistry:
    registry = ToolRegistry()

    for tool in FILESYSTEM_TOOLS:
        registry.register(tool)

    registry.register(
        create_run_command_tool(
            workspace_root=workspace_root,
        )
    )

    registry.register(
        create_write_file_tool(
            workspace_root=workspace_root,
        )
    )

    registry.register(
        create_apply_patch_tool(
            workspace_root=workspace_root,
        )
    )

    return registry


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

    workspace_root = Path(__file__).resolve().parent

    registry = create_tool_registry(
        workspace_root=workspace_root,
    )

    token_counter = create_token_counter(
        instructions=INSTRUCTIONS,
        tools=registry,
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
    agent = AgentRuntime(
        client=client,
        model=model,
        instructions=INSTRUCTIONS,
        tools=registry,
        context=context,
        compactor=compactor,
        max_output_tokens=max_output_tokens,
        max_steps=20,
    )

    task = input("You: ").strip()

    if not task:
        return

    answer = agent.run(task)

    print("\n[final answer]")
    print(answer)


if __name__ == "__main__":
    main()
