import json
from dataclasses import dataclass

from openai.types.responses import (
    FunctionToolParam,
    ResponseFunctionToolCall,
)

from agent.completion import CompletionCriteria
from agent.completion_evaluator import CompletionEvaluator
from agent.executor import PlanExecutor
from agent.planning import Plan
from agent.progress import ProgressStatus, ProgressUpdate
from agent.state import AgentState

CREATE_PLAN = "agent_create_plan"
UPDATE_PROGRESS = "agent_update_progress"
REPLAN = "agent_replan"
SATISFY_CRITERION = "agent_satisfy_criterion"
FINISH = "agent_finish"

CONTROL_NAMES = {
    CREATE_PLAN,
    UPDATE_PROGRESS,
    REPLAN,
    SATISFY_CRITERION,
    FINISH,
}

PLANNING_CONTROL_SCHEMAS: list[FunctionToolParam] = [
    {
        "type": "function",
        "name": CREATE_PLAN,
        "description": (
            "Create the initial plan and completion criteria for the current task."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
                "completion_criteria": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
            "required": [
                "steps",
                "completion_criteria",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": UPDATE_PROGRESS,
        "description": ("Report progress for the current in-progress plan step."),
        "parameters": {
            "type": "object",
            "properties": {
                "step_id": {
                    "type": "string",
                },
                "status": {
                    "type": "string",
                    "enum": [
                        "continue",
                        "completed",
                        "failed",
                    ],
                },
                "summary": {
                    "type": "string",
                },
            },
            "required": [
                "step_id",
                "status",
                "summary",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": REPLAN,
        "description": (
            "Replace invalid future work after the current plan has failed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "string",
                    },
                },
            },
            "required": ["steps"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": SATISFY_CRITERION,
        "description": (
            "Mark one completion criterion as satisfied using concrete evidence."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "criterion_id": {
                    "type": "string",
                },
                "evidence": {
                    "type": "string",
                },
            },
            "required": [
                "criterion_id",
                "evidence",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": FINISH,
        "description": (
            "Finish the task only after the plan "
            "is complete and all completion "
            "criteria are satisfied."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                },
            },
            "required": ["summary"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


@dataclass(
    frozen=True,
    slots=True,
)
class PlanningControlResult:
    output: str

    final_output: str | None = None


class PlanningController:
    def __init__(
        self,
        *,
        executor: PlanExecutor,
        completion: CompletionEvaluator,
    ) -> None:
        self._executor = executor
        self._completion = completion

    def schemas(
        self,
    ) -> list[FunctionToolParam]:
        return list(PLANNING_CONTROL_SCHEMAS)

    def handles(
        self,
        name: str,
    ) -> bool:
        return name in CONTROL_NAMES

    def _require_string_list(
        self,
        arguments: dict[str, object],
        key: str,
    ) -> list[str]:
        value = arguments.get(key)

        if not isinstance(value, list):
            raise TypeError(
                f"{key} must be a list"
            )

        if not all(
            isinstance(item, str)
            for item in value
        ):
            raise TypeError(
                f"{key} must contain only strings"
            )

        return value

    def _require_string(
        self,
        arguments: dict[str, object],
        key: str,
    ) -> str:
        value = arguments.get(key)
        if not isinstance(value, str):
            raise TypeError(f"{key} must be a string")
        return value

    def _create_plan(
        self,
        state: AgentState,
        arguments: dict[str, object],
    ) -> PlanningControlResult:
        if state.plan is not None or state.completion_criteria is not None:
            raise RuntimeError("Agent planning state already exists")

        steps = self._require_string_list(
            arguments,
            "steps",
        )

        criteria_descriptions = self._require_string_list(
            arguments,
            "completion_criteria",
        )

        plan = Plan.create(steps)

        criteria = CompletionCriteria.create(criteria_descriptions)

        state.attach_plan(plan)

        state.attach_completion_criteria(criteria)

        return PlanningControlResult(
            output=json.dumps(
                {
                    "created": True,
                    "steps": [step.id for step in plan.steps],
                    "criteria": [item.id for item in criteria.items],
                },
                ensure_ascii=False,
            )
        )

    def _update_progress(
        self,
        state: AgentState,
        arguments: dict[str, object],
    ) -> PlanningControlResult:
        step_id = self._require_string(
            arguments,
            "step_id",
        )

        status = ProgressStatus(
            self._require_string(
                arguments,
                "status",
            )
        )

        summary = self._require_string(
            arguments,
            "summary",
        )

        step = self._executor.apply_progress(
            state,
            ProgressUpdate(
                step_id=step_id,
                status=status,
                summary=summary,
            ),
        )

        return PlanningControlResult(
            output=json.dumps(
                {
                    "step_id": step.id,
                    "status": step.status.value,
                    "result": step.result,
                },
                ensure_ascii=False,
            )
        )

    def _replan(
        self,
        state: AgentState,
        arguments: dict[str, object],
    ) -> PlanningControlResult:
        descriptions = self._require_string_list(
            arguments,
            "steps",
        )

        new_steps = self._executor.replan(
            state,
            descriptions,
        )

        return PlanningControlResult(
            output=json.dumps(
                {
                    "replanned": True,
                    "new_steps": [
                        {
                            "id": step.id,
                            "description": (step.description),
                        }
                        for step in new_steps
                    ],
                },
                ensure_ascii=False,
            )
        )

    def _satisfy_criterion(
        self,
        state: AgentState,
        arguments: dict[str, object],
    ) -> PlanningControlResult:
        criterion = self._completion.satisfy(
            state,
            criterion_id=(
                self._require_string(
                    arguments,
                    "criterion_id",
                )
            ),
            evidence=(
                self._require_string(
                    arguments,
                    "evidence",
                )
            ),
        )

        return PlanningControlResult(
            output=json.dumps(
                {
                    "criterion_id": criterion.id,
                    "status": (criterion.status.value),
                    "evidence": (criterion.evidence),
                },
                ensure_ascii=False,
            )
        )

    def _finish(
        self,
        state: AgentState,
        arguments: dict[str, object],
    ) -> PlanningControlResult:
        summary = self._require_string(
            arguments,
            "summary",
        )

        if not self._completion.can_complete(state):
            return PlanningControlResult(
                output=json.dumps(
                    {
                        "accepted": False,
                        "reason": ("Plan or completion criteria are incomplete"),
                        "plan_completed": (
                            state.plan is not None and state.plan.is_completed
                        ),
                        "criteria_satisfied": (
                            state.completion_criteria is not None
                            and state.completion_criteria.is_satisfied
                        ),
                    },
                    ensure_ascii=False,
                )
            )

        return PlanningControlResult(
            output=json.dumps(
                {
                    "accepted": True,
                },
                ensure_ascii=False,
            ),
            final_output=summary,
        )

    def _dispatch(
        self,
        state: AgentState,
        name: str,
        arguments: dict[str, object],
    ) -> PlanningControlResult:
        if name == CREATE_PLAN:
            return self._create_plan(state, arguments)
        elif name == UPDATE_PROGRESS:
            return self._update_progress(state, arguments)
        elif name == REPLAN:
            return self._replan(state, arguments)
        elif name == SATISFY_CRITERION:
            return self._satisfy_criterion(state, arguments)
        elif name == FINISH:
            return self._finish(state, arguments)
        else:
            raise ValueError(f"Unknown control name: {name}")

    def execute(
        self,
        state: AgentState,
        tool_call: ResponseFunctionToolCall,
    ) -> PlanningControlResult:
        try:
            arguments = json.loads(tool_call.arguments)

            if not isinstance(
                arguments,
                dict,
            ):
                raise TypeError("Control call arguments must be a JSON object")

            return self._dispatch(
                state,
                name=tool_call.name,
                arguments=arguments,
            )

        except (
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            return PlanningControlResult(
                output=json.dumps(
                    {
                        "error": str(exc),
                        "control": tool_call.name,
                    },
                    ensure_ascii=False,
                )
            )
