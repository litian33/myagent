import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.responses import FunctionToolParam, ResponseInputParam


def list_files(path: str) -> list[str]:
    directory = Path(path)

    return [item.name for item in directory.iterdir()]

def main() -> None:
    load_dotenv()

    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    model = os.getenv("OPENAI_MODEL", "deepseek-v4-flash")

    tools: list[FunctionToolParam] = [
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

    response = client.responses.create(
        model=model,
        instructions="You are MyAgent, a coding assistant.",
        input="请告诉我当前目录有哪些代码文件",
        tools=tools,
    )

    tool_call = None

    for item in response.output:
        if item.type == "function_call":
            tool_call = item
            break
    if tool_call is None:
        print(response.output_text)
        return

    print(f"[tool call] {tool_call.name}")
    print(f"[arguments] {tool_call.arguments}")

    arguments = json.loads(tool_call.arguments)
    result = list_files(
        path=arguments["path"]
    )
    print(f"[tool result] {result}")

    tool_output: ResponseInputParam = [{
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": json.dumps(result),
    }]

    second_response = client.responses.create(
        model=model,
        instructions="You are MyAgent, a coding assistant.",
        tools=tools,
        previous_response_id=response.id,
        input=tool_output,
    )
    print(second_response.output_text)

if __name__ == "__main__":
    main()
