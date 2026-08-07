import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict

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

MAX_SEARCH_RESULTS = 20
MAX_SEARCH_FILE_BYTES = 1_000_000
MAX_TOOL_OUTPUT_CHARS = 12_000

SEARCH_EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
}
class SearchMatch(TypedDict):
    path: str
    line: int
    text: str

def grep(
    pattern: str,
    path: str,
) -> list[SearchMatch]:
    root = Path(path)
    regex = re.compile(pattern)

    matches: list[SearchMatch] = []

    if root.is_file():
        candidates = [root]
    else:
        candidates = root.rglob("*")

    for file_path in candidates:
        if len(matches) >= MAX_SEARCH_RESULTS:
            break

        if not file_path.is_file():
            continue

        if any(
            part in SEARCH_EXCLUDED_DIRS
            for part in file_path.parts
        ):
            continue

        try:
            if file_path.stat().st_size > MAX_SEARCH_FILE_BYTES:
                continue

            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                for line_number, line in enumerate(file, start=1):
                    if regex.search(line):
                        matches.append(
                            {
                                "path": str(file_path),
                                "line": line_number,
                                "text": line.rstrip(),
                            }
                        )

                        if len(matches) >= MAX_SEARCH_RESULTS:
                            break

        except (
            OSError,
            UnicodeError,
        ):
            continue

    return matches

def list_files(path: str) -> list[str]:
    directory = Path(path)

    return [item.name for item in directory.iterdir()]


def read_file(path: str) -> str:
    file_path = Path(path)

    return file_path.read_text(encoding="utf-8")


def serialize_tool_result(result: Any) -> str:
    serialized = json.dumps(
        result,
        ensure_ascii=False,
    )

    if len(serialized) <= MAX_TOOL_OUTPUT_CHARS:
        return serialized

    return json.dumps(
        {
            "truncated": True,
            "original_chars": len(serialized),
            "content": serialized[:MAX_TOOL_OUTPUT_CHARS],
        },
        ensure_ascii=False,
    )

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

            return serialize_tool_result(result)

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

GREP_TOOL = Tool(
    schema={
        "type": "function",
        "name": "grep",
        "description": (
            "Search text files for a regular expression pattern. "
            "Use this to locate code, symbols, configuration, or text "
            "without reading every file."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": (
                        "Regular expression pattern to search for."
                    ),
                },
                "path": {
                    "type": "string",
                    "description": (
                        "File or directory path to search."
                    ),
                },
            },
            "required": [
                "pattern",
                "path",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
    handler=grep,
)

def create_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()

    registry.register(LIST_FILES_TOOL)
    registry.register(READ_FILE_TOOL)
    registry.register(GREP_TOOL)

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
            "请找到 AgentRuntime 类并解释它。"
            "如果项目里没有，请根据实际搜索结果回答，不要猜。"
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
