import pytest

from agent.executor import PlanExecutor
from agent.planning import Plan, PlanStepStatus
from agent.progress import (
    ProgressStatus,
    ProgressUpdate,
)
from agent.state import AgentState


def test_continue_progress_keeps_step_running() -> None:
    state = AgentState.create("test")

    state.attach_plan(
        Plan.create(
            [
                "Locate root cause",
            ]
        )
    )

    executor = PlanExecutor()

    step = executor.start_next_step(state)

    executor.apply_progress(
        state,
        ProgressUpdate(
            step_id=step.id,
            status=ProgressStatus.CONTINUE,
            summary=("Found the login path, root cause still unknown."),
        ),
    )

    assert step.status == PlanStepStatus.IN_PROGRESS

    assert step.result is None


def test_completed_progress_completes_step() -> None:
    state = AgentState.create("test")

    state.attach_plan(
        Plan.create(
            [
                "Locate root cause",
            ]
        )
    )

    executor = PlanExecutor()

    step = executor.start_next_step(state)

    executor.apply_progress(
        state,
        ProgressUpdate(
            step_id=step.id,
            status=(ProgressStatus.COMPLETED),
            summary=("Root cause is stale session cache."),
        ),
    )

    assert step.status == PlanStepStatus.COMPLETED

    assert step.result == "Root cause is stale session cache."


def test_failed_progress_fails_step() -> None:
    state = AgentState.create("test")

    state.attach_plan(
        Plan.create(
            [
                "Locate root cause",
            ]
        )
    )

    executor = PlanExecutor()

    step = executor.start_next_step(state)

    executor.apply_progress(
        state,
        ProgressUpdate(
            step_id=step.id,
            status=ProgressStatus.FAILED,
            summary=("Cannot modify the generated source."),
        ),
    )

    assert step.status == PlanStepStatus.FAILED

    assert step.result == "Cannot modify the generated source."


def test_progress_must_match_current_step() -> None:
    state = AgentState.create("test")

    state.attach_plan(
        Plan.create(
            [
                "Locate root cause",
            ]
        )
    )

    executor = PlanExecutor()

    executor.start_next_step(state)

    with pytest.raises(
        RuntimeError,
        match="does not match",
    ):
        executor.apply_progress(
            state,
            ProgressUpdate(
                step_id="step-999",
                status=(ProgressStatus.COMPLETED),
                summary="done",
            ),
        )
