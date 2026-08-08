import os

from dotenv import load_dotenv
from openai import OpenAI

from agent.context import ContextManager
from agent.runtime import AgentRuntime
from tools.filesystem import FILESYSTEM_TOOLS
from tools.registry import ToolRegistry

INSTRUCTIONS = """
You are MyAgent, a coding assistant.
Use the available tools when you need information
from the local environment.
Do not guess file contents.
Read files when their contents are needed.
"""


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    for tool in FILESYSTEM_TOOLS:
        registry.register(tool)

    return registry


def main() -> None:
    load_dotenv()

    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    model = os.getenv(
        "OPENAI_MODEL",
        "gpt-5.6-luna",
    )

    registry = create_tool_registry()

    context = ContextManager(
        max_input_chars=15_000,
    )

    agent = AgentRuntime(
        client=client,
        model=model,
        instructions=INSTRUCTIONS,
        tools=registry,
        context=context,
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
