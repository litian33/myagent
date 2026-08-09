import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agent.compaction import ContextCompactor
from agent.context import ContextManager
from agent.runtime import AgentRuntime
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

Use run_command when you need to inspect repository
state or run tests, linters, or static checks.

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

    workspace_root = (
        Path(__file__)
        .resolve()
        .parent
    )

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
        max_steps=10,
    )

    task = input("You: ").strip()

    if not task:
        return

    answer = agent.run(task)

    print("\n[final answer]")
    print(answer)


if __name__ == "__main__":
    main()
