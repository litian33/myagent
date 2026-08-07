import json
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.responses import (
    FunctionToolParam,
    ResponseFunctionToolCall,
    ResponseInputParam,
)

MAX_STEPS = 10

INSTRUCTIONS = """
You are MyAgent, a coding assistant.
Use the available tools when you need information from the local environment.
Do not guess file contents. Read files when their contents are needed.
"""


def list_files(path: str) -> list[str]:
    directory = Path(path)

    return [item.name for item in directory.iterdir()]


def read_file(path: str) -> str:
    file_path = Path(path)

    return file_path.read_text(encoding="utf-8")


@dataclass(frozen=True, slots=True)
class Tool:
    schema: FunctionToolParam
    handler: Callable[..., Any]

    @property
    def name(self) -> str:
        return self.schema["name"]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(
                f"Tool already registered: {tool.name}"
            )

        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas(self) -> list[FunctionToolParam]:
        return [
            tool.schema
            for tool in self._tools.values()
        ]

    def execute(
        self,
        tool_call: ResponseFunctionToolCall,
    ) -> str:
        tool = self.get(tool_call.name)

        if tool is None:
            return json.dumps(
                {
                    "error": f"Unknown tool: {tool_call.name}",
                },
                ensure_ascii=False,
            )

        try:
            arguments = json.loads(tool_call.arguments)

            if not isinstance(arguments, dict):
                return json.dumps(
                    {
                        "error": "Tool arguments must be a JSON object.",
                        "tool": tool_call.name,
                    },
                    ensure_ascii=False,
                )

            result = tool.handler(**arguments)

            return json.dumps(
                result,
                ensure_ascii=False,
            )

        except (
            json.JSONDecodeError,
            TypeError,
            OSError,
            UnicodeError,
        ) as exc:
            return json.dumps(
                {
                    "error": str(exc),
                    "tool": tool_call.name,
                },
                ensure_ascii=False,
            )


LIST_FILES_TOOL = Tool(
    schema={
        "type": "function",
        "name": "list_files",
        "description": "List files and directories in a given directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list.",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    handler=list_files,
)


READ_FILE_TOOL = Tool(
    schema={
        "type": "function",
        "name": "read_file",
        "description": "Read the text content of a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path of the file to read.",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    handler=read_file,
)


def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(LIST_FILES_TOOL)
    registry.register(READ_FILE_TOOL)

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

    response = client.responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        input=(
            "请分析当前项目里的 Python 代码是做什么的。"
            "根据需要使用工具调查项目，"
            "最后根据你实际看到的代码进行总结。"
        ),
        tools=registry.schemas(),
    )

    step = 0

    while True:
        step += 1

        if step > MAX_STEPS:
            raise RuntimeError(
                f"Agent exceeded maximum steps: {MAX_STEPS}"
            )

        print(f"\n[agent step {step}]")

        tool_calls: list[ResponseFunctionToolCall] = []

        for item in response.output:
            if item.type == "function_call":
                tool_calls.append(item)

        if not tool_calls:
            print("\n[final answer]")
            print(response.output_text)
            return

        tool_outputs: ResponseInputParam = []

        for tool_call in tool_calls:
            print(
                f"[tool call] "
                f"{tool_call.name}({tool_call.arguments})"
            )

            result = registry.execute(tool_call)

            print(f"[tool result] {result}")

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": result,
                }
            )

        response = client.responses.create(
            model=model,
            instructions=INSTRUCTIONS,
            tools=registry.schemas(),
            previous_response_id=response.id,
            input=tool_outputs,
        )


if __name__ == "__main__":
    main()
