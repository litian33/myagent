import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agent.compaction import ContextCompactor
from agent.context import ContextManager
from agent.runtime import AgentRuntime
from tools.edit import (
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

Before modifying an existing file:
1. read the current file;
2. use the sha256 returned by read_file as the
   expected_sha256 argument to write_file;
3. never invent an expected_sha256 value.

After modifying code:
1. inspect the resulting git diff;
2. run relevant tests or static checks;
3. fix problems if necessary before finishing.

Use expected_sha256="MISSING" only when creating
a file that does not already exist.

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
