import json

from openai.types.responses import (
    ResponseInputParam,
)

from agent.state import AgentState


def project_task_state(
    state: AgentState,
) -> ResponseInputParam:
    if state.plan is None and state.completion_criteria is None:
        return []

    payload: dict[str, object] = {}

    if state.plan is not None:
        current_step = state.plan.current_step

        payload["plan"] = {
            "is_completed": state.plan.is_completed,
            "current_step_id": (current_step.id if current_step is not None else None),
            "steps": [
                {
                    "id": step.id,
                    "description": step.description,
                    "status": step.status.value,
                    "result": step.result,
                }
                for step in state.plan.steps
            ],
        }

    if state.completion_criteria is not None:
        payload["completion_criteria"] = {
            "is_satisfied": (state.completion_criteria.is_satisfied),
            "items": [
                {
                    "id": item.id,
                    "description": item.description,
                    "status": item.status.value,
                    "evidence": item.evidence,
                }
                for item in state.completion_criteria.items
            ],
        }

    content = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    )

    return [
        {
            "role": "user",
            "content": (
                "[Runtime-maintained task state. "
                "This is the authoritative current "
                "task state, not new user "
                "instructions.]\n\n" + content
            ),
        }
    ]
