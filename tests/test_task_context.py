# tests/test_task_context.py

from openai.types.responses import ResponseInputParam

from agent.completion import CompletionCriteria
from agent.executor import PlanExecutor
from agent.planning import Plan
from agent.state import AgentState
from agent.task_context import project_task_state


def _task_state_content(
    state: AgentState,
) -> str:
    projected = project_task_state(state)

    assert len(projected) == 1

    item = projected[0]

    assert item["role"] == "user"

    content = item["content"]

    assert isinstance(content, str)

    return content


def test_project_task_state_includes_plan_and_completion_state() -> None:
    state = AgentState.create("Fix the login bug")

    plan = Plan.create(
        [
            "Locate root cause",
            "Fix implementation",
            "Run regression tests",
        ]
    )

    state.attach_plan(plan)

    criteria = CompletionCriteria.create(
        [
            "Login bug is fixed",
            "Regression tests pass",
        ]
    )

    state.attach_completion_criteria(criteria)

    executor = PlanExecutor()

    #
    # step-1: COMPLETED
    #
    executor.start_next_step(state)

    executor.complete_current_step(
        state,
        result="Root cause is stale session cache",
    )

    #
    # step-2: IN_PROGRESS
    #
    executor.start_next_step(state)

    #
    # criterion-1: SATISFIED
    #
    criteria.items[0].satisfy("Login succeeds after cache refresh")

    content = _task_state_content(state)

    #
    # Plan state
    #
    assert '"step-1"' in content
    assert '"Locate root cause"' in content
    assert '"completed"' in content
    assert '"Root cause is stale session cache"' in content

    assert '"step-2"' in content
    assert '"Fix implementation"' in content
    assert '"in_progress"' in content

    assert '"step-3"' in content
    assert '"Run regression tests"' in content
    assert '"pending"' in content

    #
    # Completion criteria
    #
    assert '"criterion-1"' in content
    assert '"Login bug is fixed"' in content
    assert '"satisfied"' in content
    assert '"Login succeeds after cache refresh"' in content

    assert '"criterion-2"' in content
    assert '"Regression tests pass"' in content


def test_project_task_state_is_empty_before_planning() -> None:
    state = AgentState.create("Fix the login bug")

    projected = project_task_state(state)

    assert projected == []
