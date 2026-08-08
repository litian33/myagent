import json
from typing import Any

import tiktoken
from openai import OpenAI
from openai.types.responses import ResponseInputParam

from agent.context import TokenCounter
from tools.registry import ToolRegistry

TOKEN_ESTIMATE_MARGIN = 1.10


def create_token_counter_openai(
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

def create_token_counter(
    *,
    instructions: str,
    tools: ToolRegistry,
    encoding_name: str = "o200k_base",
) -> TokenCounter:
    encoding = tiktoken.get_encoding(encoding_name)
    tool_schemas = tools.schemas()

    def encode(value: str) -> int:
        return len(encoding.encode(value))

    def count_value(value: Any) -> int:
        if value is None:
            return 0

        if isinstance(value, str):
            return encode(value)

        # ResponseInputParam / Tool schema 都是结构化输入。
        # 这里统一转换成紧凑 JSON，作为本地 token 预算估算。
        serialized = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )

        return encode(serialized)

    def count_tokens(
        input_items: ResponseInputParam,
    ) -> int:
        token_count = 0

        # system/developer instructions
        token_count += encode(instructions)

        # tools definitions
        token_count += count_value(tool_schemas)

        # conversation / reasoning / tool calls / tool outputs
        token_count += count_value(input_items)

        # 给 Provider 的内部结构化包装预留少量余量
        return int(token_count * TOKEN_ESTIMATE_MARGIN)

    return count_tokens
