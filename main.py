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
Do not guess file contents. Read files when their contents are needed.
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
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Read the text contents of a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to read.",
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

def read_file(path: str) -> str:
    file_path = Path(path)

    return file_path.read_text(encoding="utf-8")

def execute_tool(tool_call: ResponseFunctionToolCall) -> str:
    try:
        if tool_call.name == "list_files":
            return json.dumps(
                list_files(
                    path=json.loads(tool_call.arguments)["path"],
                ),
                ensure_ascii=False,
            )
        elif tool_call.name == "read_file":
            return json.dumps(
                read_file(
                    path=json.loads(tool_call.arguments)["path"],
                ),
                ensure_ascii=False,
            )
        else:
            return json.dumps(
                {"error": f"Unknown tool: {tool_call.name}"},
                ensure_ascii=False,
            )
    except (
        json.JSONDecodeError,
        KeyError,
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

def main() -> None:
    load_dotenv()

    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    model = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")

    # input = (
    #     "请分析当前项目里的 Python 代码是做什么的。"
    #     "先了解项目目录，再根据需要读取相关文件，"
    #     "最后根据你实际看到的代码进行总结。"
    # )
    input = (
        "请阅读 agent.py，并告诉我 execute_tool 函数负责什么。"
    )
    response = client.responses.create(
        model=model,
        instructions=INSTRUCTIONS,
        input=input,
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
