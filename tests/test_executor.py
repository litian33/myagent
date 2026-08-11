import pytest

from agent.executor import PlanExecutor
from agent.planning import (
    Plan,
    PlanStepStatus,
)
from agent.state import (
    AgentState,
    AgentStatus,
)


def test_agent_state_can_attach_plan() -> None:
    state = AgentState.create("test")

    plan = Plan.create(
        [
            "Locate root cause",
            "Fix implementation",
        ]
    )

    state.attach_plan(plan)

    assert state.plan is plan


def test_agent_state_cannot_attach_plan_twice() -> None:
    state = AgentState.create("test")

    state.attach_plan(Plan.create(["step one"]))

    with pytest.raises(
        RuntimeError,
        match="already has a plan",
    ):
        state.attach_plan(Plan.create(["step two"]))


def test_executor_starts_first_pending_step() -> None:
    state = AgentState.create("test")

    state.attach_plan(
        Plan.create(
            [
                "Locate root cause",
                "Fix implementation",
            ]
        )
    )

    executor = PlanExecutor()

    step = executor.start_next_step(state)

    assert step.id == "step-1"

    assert step.status == PlanStepStatus.IN_PROGRESS


def test_executor_advances_sequentially() -> None:
    state = AgentState.create("test")

    state.attach_plan(
        Plan.create(
            [
                "Locate root cause",
                "Fix implementation",
            ]
        )
    )

    executor = PlanExecutor()

    first = executor.start_next_step(state)

    executor.complete_current_step(state)

    second = executor.start_next_step(state)

    assert first.status == PlanStepStatus.COMPLETED

    assert second.id == "step-2"

    assert second.status == PlanStepStatus.IN_PROGRESS


def test_executor_rejects_second_running_step() -> None:
    state = AgentState.create("test")

    state.attach_plan(
        Plan.create(
            [
                "step one",
                "step two",
            ]
        )
    )

    executor = PlanExecutor()

    executor.start_next_step(state)

    with pytest.raises(
        RuntimeError,
        match="in-progress",
    ):
        executor.start_next_step(state)


def test_failed_plan_step_does_not_fail_agent() -> None:
    state = AgentState.create("test")

    state.start()

    state.attach_plan(
        Plan.create(
            [
                "Try implementation",
                "Run tests",
            ]
        )
    )

    executor = PlanExecutor()

    executor.start_next_step(state)

    executor.fail_current_step(state)

    assert state.plan is not None

    assert state.plan.steps[0].status == PlanStepStatus.FAILED

    assert state.status == AgentStatus.RUNNING


def test_executor_does_not_skip_failed_step() -> None:
    state = AgentState.create("test")

    state.attach_plan(
        Plan.create(
            [
                "Fix implementation",
                "Run tests",
            ]
        )
    )

    executor = PlanExecutor()

    executor.start_next_step(state)
    executor.fail_current_step(state)

    with pytest.raises(
        RuntimeError,
        match="failed step",
    ):
        executor.start_next_step(state)
