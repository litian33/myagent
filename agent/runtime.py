import json

from openai import OpenAI
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseInputParam,
)

from agent.compaction import (
    ContextCompactor,
)
from agent.context import ContextManager
from agent.state import AgentRunResult, AgentState
from policy.approval import (
    ApprovalHandler,
)
from policy.engine import ToolPolicy
from policy.model import (
    ApprovalRequest,
    PolicyDecision,
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
        context: ContextManager,
        compactor: ContextCompactor,
        policy: ToolPolicy,
        approval: ApprovalHandler,
        max_output_tokens: int,
        max_steps: int = 10,
    ) -> None:
        self._client = client
        self._model = model
        self._instructions = instructions
        self._tools = tools
        self._context = context
        self._compactor = compactor
        self._max_output_tokens = max_output_tokens
        self._max_steps = max_steps
        self._policy = policy
        self._approval = approval

    def run(
        self,
        task: str,
    ) -> AgentRunResult:
        state = AgentState.create(task)
        state.start()

        for step in range(
            1,
            self._max_steps + 1,
        ):
            state.step = step

            context = self._build_context(state)

            print(f"\n[agent step {state.step}]")

            print(
                "[context] "
                f"tokens={context.input_tokens}/"
                f"{context.max_input_tokens}, "
                f"blocks="
                f"{context.included_blocks}, "
                f"compacted="
                f"{context.compacted_blocks}"
            )

            response = self._client.responses.create(
                model=self._model,
                instructions=self._instructions,
                input=context.input,
                tools=self._tools.schemas(),
                max_output_tokens=(self._max_output_tokens),
                truncation="disabled",
            )

            tool_calls: list[ResponseFunctionToolCall] = []

            for item in response.output:
                if item.type == "function_call":
                    tool_calls.append(item)

            if not tool_calls:
                state.record_step(
                    response.output,
                    [],
                )

                state.complete()

                return AgentRunResult(status=state.status, output=response.output_text)

            tool_outputs: ResponseInputParam = []

            for tool_call in tool_calls:
                print(f"[tool call] {tool_call.name}({tool_call.arguments})")

                result = self._execute_tool_call(tool_call)

                print(f"[tool result] {result}")

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

        state.reach_max_steps()
        # raise RuntimeError(f"Agent exceeded maximum steps: {self._max_steps}")
        return AgentRunResult(status=state.status, output=None)

    def _build_context(
        self,
        state: AgentState,
    ):
        while True:
            context = self._context.build(state)

            if context.pending_compaction_blocks == 0:
                return context

            print(f"[compaction] blocks={context.pending_compaction_blocks}")

            self._compactor.compact(
                state,
                block_count=(context.pending_compaction_blocks),
            )

    def _execute_tool_call(
        self,
        tool_call: ResponseFunctionToolCall,
    ) -> str:
        tool = self._tools.get(tool_call.name)

        #
        # Unknown tools cannot execute anyway.
        # Let ToolRegistry produce the normal
        # structured "unknown tool" result.
        #
        if tool is None:
            return self._tools.execute(tool_call)

        policy_result = self._policy.evaluate(tool)

        print(
            "[policy] "
            f"tool={tool.name}, "
            f"capability={tool.capability.value}, "
            f"decision={policy_result.decision.value}"
        )

        if policy_result.decision == PolicyDecision.DENY:
            return json.dumps(
                {
                    "error": ("Tool execution denied by policy"),
                    "tool": tool.name,
                    "capability": (tool.capability.value),
                    "policy_decision": (PolicyDecision.DENY.value),
                    "reason": (policy_result.reason),
                },
                ensure_ascii=False,
            )

        if policy_result.decision == PolicyDecision.REQUIRE_APPROVAL:
            approved = self._approval.request(
                ApprovalRequest(
                    tool_name=tool.name,
                    capability=(tool.capability),
                    arguments=(tool_call.arguments),
                    reason=(policy_result.reason),
                )
            )

            if not approved:
                return json.dumps(
                    {
                        "error": (
                            "Tool execution was not approved by the user"
                        ),
                        "tool": tool.name,
                        "capability": (tool.capability.value),
                        "policy_decision": ("denied_by_user"),
                    },
                    ensure_ascii=False,
                )

        return self._tools.execute(tool_call)
