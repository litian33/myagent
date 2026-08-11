import json
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

import openai
from openai import OpenAI
from openai.types.responses import (
    FunctionToolParam,
    ResponseFunctionToolCall,
    ResponseInputParam,
)

from agent.compaction import (
    ContextCompactor,
)
from agent.context import (
    ContextBudgetExceeded,
    ContextCompactionError,
    ContextManager,
    ContextSnapshot,
)
from agent.control import PlanningController
from agent.errors import (
    AgentExecutionError,
    AgentRunError,
    ContextExecutionError,
    ModelInvocationError,
)
from agent.executor import PlanExecutor
from agent.planning import (
    PlanStepStatus,
)
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

P = ParamSpec("P")
R = TypeVar("R")


def handle_openai_errors(func: Callable[P, R]) -> Callable[P, R]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return func(*args, **kwargs)
        except (
            openai.APIConnectionError,
            openai.APITimeoutError,
            openai.RateLimitError,
            openai.InternalServerError,
        ) as exc:
            raise ModelInvocationError(
                str(exc),
                retryable=True,
            ) from exc
        except openai.APIError as exc:
            raise ModelInvocationError(
                str(exc),
                retryable=False,
            ) from exc

    return wrapper


class AgentRuntime:
    def __init__(
        self,
        *,
        client: OpenAI,
        model: str,
        instructions: str,
        tools: ToolRegistry,
        model_tools: list[FunctionToolParam],
        planning: PlanningController,
        plan_executor: PlanExecutor,
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
        self._model_tools = list(model_tools)
        self._planning = planning
        self._plan_executor = plan_executor
        self._context = context
        self._compactor = compactor
        self._max_output_tokens = max_output_tokens
        self._max_steps = max_steps
        self._policy = policy
        self._approval = approval

    @staticmethod
    def _protocol_error_outputs(
        tool_calls: list[ResponseFunctionToolCall],
        *,
        message: str,
    ) -> ResponseInputParam:
        outputs: ResponseInputParam = []

        for tool_call in tool_calls:
            outputs.append(
                {
                    "type": ("function_call_output"),
                    "call_id": (tool_call.call_id),
                    "output": json.dumps(
                        {
                            "error": message,
                            "call": (tool_call.name),
                        },
                        ensure_ascii=False,
                    ),
                }
            )

        return outputs

    def _start_next_plan_step_if_ready(
        self,
        state: AgentState,
    ) -> None:
        plan = state.plan

        if plan is None:
            return

        if plan.is_completed:
            return

        if plan.current_step is not None:
            return

        if any(step.status == PlanStepStatus.FAILED for step in plan.steps):
            return

        if not plan.pending_steps:
            return

        step = self._plan_executor.start_next_step(state)

        print(f"[plan step] started {step.id}: {step.description}")

    def _run(
        self,
        state: AgentState,
    ) -> AgentRunResult:
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

            response = self._call_model(context=context.input)

            tool_calls: list[ResponseFunctionToolCall] = [
                item for item in response.output if item.type == "function_call"
            ]

            if not tool_calls:
                state.record_step(
                    response.output,
                    [],
                )

                print(
                    "[protocol] "
                    "Task remains running; "
                    "agent_finish is required "
                    "to complete the task."
                )

                continue
            control_calls = [
                call for call in tool_calls if self._planning.handles(call.name)
            ]
            environment_calls = [
                call for call in tool_calls if not self._planning.handles(call.name)
            ]

            if control_calls and environment_calls:
                tool_outputs = self._protocol_error_outputs(
                    tool_calls,
                    message=(
                        "Environment tool calls "
                        "and planning control calls "
                        "cannot be mixed in the "
                        "same model response"
                    ),
                )

                state.record_step(
                    response.output,
                    tool_outputs,
                )

                continue

            if len(control_calls) > 1:
                tool_outputs = self._protocol_error_outputs(
                    control_calls,
                    message=(
                        "Only one planning control call is allowed per model response"
                    ),
                )

                state.record_step(
                    response.output,
                    tool_outputs,
                )

                continue
            tool_outputs: ResponseInputParam = []
            if control_calls:
                tool_call = control_calls[0]
                print(f"[planning execute] {tool_call.name}({tool_call.arguments})")
                result = self._planning.execute(
                    state,
                    tool_call,
                )
                print(f"[planning result] {result}")
                tool_outputs = [
                    {
                        "type": ("function_call_output"),
                        "call_id": (tool_call.call_id),
                        "output": result.output,
                    }
                ]
                state.record_step(
                    response.output,
                    tool_outputs,
                )

                if result.final_output is not None:
                    state.complete()

                    return AgentRunResult(
                        status=state.status,
                        output=result.final_output,
                    )

                # 如果计划没有结束，这里驱动下一个Step
                self._start_next_plan_step_if_ready(state)
                continue

            for tool_call in environment_calls:
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

    def run(
        self,
        task: str,
    ) -> AgentRunResult:
        state = AgentState.create(task)
        state.start()
        try:
            return self._run(state)
        except AgentExecutionError as exc:
            state.fail()
            return AgentRunResult(
                status=state.status,
                output=None,
                error=AgentRunError(
                    kind=exc.kind,
                    message=str(exc),
                    retryable=exc.retryable,
                ),
            )
        except Exception:
            state.fail()
            raise

    @handle_openai_errors
    def _call_model(
        self,
        *,
        context: ResponseInputParam,
    ):
        return self._client.responses.create(
            model=self._model,
            instructions=self._instructions,
            input=context,
            tools=self._model_tools,
            max_output_tokens=(self._max_output_tokens),
            truncation="disabled",
        )

    def _build_context(
        self,
        state: AgentState,
    ) -> ContextSnapshot:
        try:
            while True:
                context = self._context.build(state)

                if context.pending_compaction_blocks == 0:
                    return context

                print(f"[compaction] blocks={context.pending_compaction_blocks}")

                self._compact_context(
                    state,
                    block_count=(context.pending_compaction_blocks),
                )

        except (
            ContextBudgetExceeded,
            ContextCompactionError,
        ) as exc:
            raise ContextExecutionError(str(exc)) from exc

    @handle_openai_errors
    def _compact_context(
        self,
        state: AgentState,
        *,
        block_count: int,
    ) -> None:
        self._compactor.compact(
            state,
            block_count=block_count,
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
                        "error": ("Tool execution was not approved by the user"),
                        "tool": tool.name,
                        "capability": (tool.capability.value),
                        "policy_decision": ("denied_by_user"),
                    },
                    ensure_ascii=False,
                )

        return self._tools.execute(tool_call)
