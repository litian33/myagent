from openai import OpenAI
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseInputParam,
)

from tools.registry import ToolRegistry


class AgentRuntime:
    def __init__(
        self,
        *,
        client: OpenAI,
        model: str,
        instructions: str,
        tools: ToolRegistry,
        max_steps: int = 10,
    ) -> None:
        self._client = client
        self._model = model
        self._instructions = instructions
        self._tools = tools
        self._max_steps = max_steps

    def run(self, task: str) -> str:
        response = self._client.responses.create(
            model=self._model,
            instructions=self._instructions,
            input=task,
            tools=self._tools.schemas(),
        )

        for step in range(
            1,
            self._max_steps + 1,
        ):
            print(f"\n[agent step {step}]")

            tool_calls: list[
                ResponseFunctionToolCall
            ] = []

            for item in response.output:
                if item.type == "function_call":
                    tool_calls.append(item)

            if not tool_calls:
                return response.output_text

            tool_outputs: ResponseInputParam = []

            for tool_call in tool_calls:
                print(
                    f"[tool call] "
                    f"{tool_call.name}"
                    f"({tool_call.arguments})"
                )

                result = self._tools.execute(
                    tool_call
                )

                print(
                    f"[tool result] {result}"
                )

                tool_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": tool_call.call_id,
                        "output": result,
                    }
                )

            response = self._client.responses.create(
                model=self._model,
                instructions=self._instructions,
                tools=self._tools.schemas(),
                previous_response_id=response.id,
                input=tool_outputs,
            )

        raise RuntimeError(
            "Agent exceeded maximum steps: "
            f"{self._max_steps}"
        )
