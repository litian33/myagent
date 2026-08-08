from openai import OpenAI
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseInputParam,
)

from agent.context import ContextManager
from agent.state import AgentState
from tools.registry import ToolRegistry


class AgentRuntime:
    def __init__(
        self,
        *,
        client: OpenAI,
        model: str,
        instructions: str,
        tools: ToolRegistry,
        context: ContextManager,
        max_output_tokens: int,
        max_steps: int = 10,
    ) -> None:
        self._client = client
        self._model = model
        self._instructions = instructions
        self._tools = tools
        self._context = context
        self._max_output_tokens = max_output_tokens
        self._max_steps = max_steps

    def run(
        self,
        task: str,
    ) -> str:
        state = AgentState.create(
            task
        )

        for step in range(
            1,
            self._max_steps + 1,
        ):
            state.step = step

            context = self._context.build(
                state
            )

            print(
                f"\n[agent step {state.step}]"
            )

            print(
                "[context] "
                f"tokens={context.input_tokens}, "
                f"max_input_tokens={context.max_input_tokens}, "
                f"blocks="
                f"{context.included_blocks}/"
                f"{context.total_blocks}, "
                f"dropped="
                f"{context.dropped_blocks}"
            )

            response = (
                self._client.responses.create(
                    model=self._model,
                    instructions=self._instructions,
                    input=context.input,
                    tools=self._tools.schemas(),
                    max_output_tokens=(
                                self._max_output_tokens
                            ),
                    truncation="disabled",
                )
            )

            tool_calls: list[
                ResponseFunctionToolCall
            ] = []

            for item in response.output:
                if item.type == "function_call":
                    tool_calls.append(item)

            if not tool_calls:
                state.record_step(
                    response.output,
                    [],
                )

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

            state.record_step(
                response.output,
                tool_outputs,
            )

        raise RuntimeError(
            "Agent exceeded maximum steps: "
            f"{self._max_steps}"
        )
