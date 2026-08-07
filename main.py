import json
import os
from pathlib import Path

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
"""

TOOLS: list[FunctionToolParam] = [
    {
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
    }
]

def list_files(path: str) -> list[str]:
    directory = Path(path)

    return [item.name for item in directory.iterdir()]


def execute_tool(tool_call: ResponseFunctionToolCall) -> str:
    if tool_call.name != "list_files":
        return json.dumps(
            {"error": f"Unknown tool: {tool_call.name}"},
            ensure_ascii=False,
        )

    arguments = json.loads(tool_call.arguments)

    result = list_files(
        path=arguments["path"],
    )

    return json.dumps(result, ensure_ascii=False)


def main() -> None:
    load_dotenv()

    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

    response = client.responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        input=(
            "请查看当前项目目录。根据第一次查看到的结果，"
            "如果你认为有值得继续查看的目录，请再调用 list_files 查看它，"
            "最后总结你看到的项目结构。"
        ),
        tools=TOOLS,
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

        # 搜集需要调用工具的响应
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

            result = execute_tool(tool_call)

            print(f"[tool result] {result}")

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": result,
                }
            )

            # 根据工具调用结果再次调用大模型获取下一步输出
            response = client.responses.create(
                model=model,
                instructions=INSTRUCTIONS,
                tools=TOOLS,
                previous_response_id=response.id,
                input=tool_outputs
            )


if __name__ == "__main__":
    main()
