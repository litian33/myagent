import os

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.responses import (
    ResponseInputParam,
)

from agent.compaction import (
    ContextCompactor,
)
from agent.context import (
    ContextManager,
    TokenCounter,
)
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

def create_token_counter(
    *,
    client: OpenAI,
    model: str,
    instructions: str,
    tools: ToolRegistry,
) -> TokenCounter:
    tool_schemas = tools.schemas()

    def count_tokens(
        input_items: ResponseInputParam,
    ) -> int:
        result = (
            client.responses.input_tokens.count(
                model=model,
                instructions=instructions,
                input=input_items,
                tools=tool_schemas,
                truncation="disabled",
            )
        )

        return result.input_tokens

    return count_tokens

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
    context_window_tokens = int(
        os.environ[
            "OPENAI_CONTEXT_WINDOW_TOKENS"
        ]
    )

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

    max_input_tokens = (
        context_window_tokens
        - max_output_tokens
        - safety_margin_tokens
    )

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

    registry = create_tool_registry()

    token_counter = create_token_counter(
        client=client,
        model=model,
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
