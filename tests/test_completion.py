import pytest

from agent.completion import CompletionCriteria
from agent.completion_evaluator import CompletionEvaluator
from agent.planning import Plan
from agent.state import AgentState


def test_create_completion_criteria() -> None:
    criteria = CompletionCriteria.create(
        [
            "Bug is fixed",
            "Regression test exists",
            "Relevant tests pass",
        ]
    )

    assert len(criteria.items) == 3

    assert criteria.items[0].id == "criterion-1"

    assert criteria.is_satisfied is False


def test_completion_evidence_cannot_be_empty() -> None:
    criteria = CompletionCriteria.create(
        [
            "Relevant tests pass",
        ]
    )

    criterion = criteria.items[0]

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        criterion.satisfy("   ")


def test_completion_criteria_require_all_items() -> None:
    criteria = CompletionCriteria.create(
        [
            "Bug fixed",
            "Tests pass",
        ]
    )

    criteria.items[0].satisfy("Bug no longer reproduces")

    assert criteria.is_satisfied is False

    criteria.items[1].satisfy("pytest: 10 passed")

    assert criteria.is_satisfied is True


def test_completed_plan_is_not_enough() -> None:
    state = AgentState.create("test")

    plan = Plan.create(
        [
            "Fix bug",
        ]
    )

    state.attach_plan(plan)

    state.attach_completion_criteria(
        CompletionCriteria.create(
            [
                "Relevant tests pass",
            ]
        )
    )

    plan.steps[0].start()
    plan.steps[0].complete("Implementation updated")

    evaluator = CompletionEvaluator()

    assert plan.is_completed is True

    assert evaluator.can_complete(state) is False


def test_satisfied_criteria_are_not_enough() -> None:
    state = AgentState.create("test")

    state.attach_plan(
        Plan.create(
            [
                "Fix bug",
            ]
        )
    )

    criteria = CompletionCriteria.create(
        [
            "Relevant tests pass",
        ]
    )

    state.attach_completion_criteria(criteria)

    evaluator = CompletionEvaluator()

    evaluator.satisfy(
        state,
        criterion_id="criterion-1",
        evidence="pytest: 10 passed",
    )

    assert evaluator.can_complete(state) is False


def test_goal_can_complete_with_plan_and_evidence() -> None:
    state = AgentState.create("test")

    plan = Plan.create(
        [
            "Fix bug",
        ]
    )

    state.attach_plan(plan)

    state.attach_completion_criteria(
        CompletionCriteria.create(
            [
                "Relevant tests pass",
            ]
        )
    )

    plan.steps[0].start()
    plan.steps[0].complete("Bug fixed")

    evaluator = CompletionEvaluator()

    evaluator.satisfy(
        state,
        criterion_id="criterion-1",
        evidence="pytest: 10 passed",
    )

    assert evaluator.can_complete(state) is True
