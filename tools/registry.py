import json
from typing import Any

from openai.types.responses import (
    FunctionToolParam,
    ResponseFunctionToolCall,
)

from tools.base import Tool

MAX_TOOL_OUTPUT_CHARS = 12_000


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
            ValueError,
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
