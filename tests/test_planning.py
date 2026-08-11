import pytest

from agent.planning import (
    Plan,
    PlanStepStatus,
)


def test_create_plan() -> None:
    plan = Plan.create(
        [
            "Locate root cause",
            "Fix implementation",
            "Run tests",
        ]
    )

    assert len(plan.steps) == 3

    assert plan.steps[0].id == "step-1"
    assert plan.steps[0].description == "Locate root cause"

    assert all(step.status == PlanStepStatus.PENDING for step in plan.steps)


def test_plan_cannot_be_empty() -> None:
    with pytest.raises(
        ValueError,
        match="at least one step",
    ):
        Plan.create([])


def test_plan_step_description_cannot_be_empty() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        Plan.create(
            [
                "Locate root cause",
                "   ",
            ]
        )


def test_plan_step_lifecycle() -> None:
    plan = Plan.create(
        [
            "Locate root cause",
        ]
    )

    step = plan.steps[0]

    assert step.status == PlanStepStatus.PENDING

    step.start()

    assert step.status == PlanStepStatus.IN_PROGRESS

    step.complete("Root cause located")

    assert step.status == PlanStepStatus.COMPLETED


def test_pending_step_cannot_complete() -> None:
    plan = Plan.create(
        [
            "Locate root cause",
        ]
    )

    step = plan.steps[0]

    with pytest.raises(
        RuntimeError,
        match="Cannot complete",
    ):
        step.complete("Root cause located")


def test_running_step_can_fail() -> None:
    plan = Plan.create(
        [
            "Locate root cause",
        ]
    )

    step = plan.steps[0]

    step.start()
    step.fail("Unable to complete")

    assert step.status == PlanStepStatus.FAILED

    assert plan.is_completed is False


def test_plan_is_completed_when_all_steps_complete() -> None:
    plan = Plan.create(
        [
            "Locate root cause",
            "Fix implementation",
        ]
    )

    for step in plan.steps:
        step.start()
        step.complete("Root cause located")

    assert plan.is_completed is True

def test_plan_exposes_current_step(
) -> None:
    plan = Plan.create(
        [
            "Locate root cause",
            "Fix implementation",
        ]
    )

    assert plan.current_step is None

    plan.steps[0].start()

    assert (
        plan.current_step
        is plan.steps[0]
    )
