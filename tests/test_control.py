import pytest

from agent.completion_evaluator import CompletionEvaluator
from agent.control import (
    CREATE_PLAN,
    FINISH,
    REPLAN,
    SATISFY_CRITERION,
    UPDATE_PROGRESS,
    PlanningController,
)
from agent.executor import PlanExecutor
from agent.planning import Plan
from agent.state import AgentState


def test_controller_exposes_control_schemas() -> None:
    controller = PlanningController(
        executor=PlanExecutor(), completion=CompletionEvaluator()
    )
    schemas = controller.schemas()
    assert schemas is not None
    assert len(schemas) > 0


def test_controller_handles_control_names() -> None:
    controller = PlanningController(
        executor=PlanExecutor(), completion=CompletionEvaluator()
    )
    assert controller.handles(CREATE_PLAN)
    assert controller.handles(UPDATE_PROGRESS)
    assert controller.handles(REPLAN)
    assert controller.handles(SATISFY_CRITERION)
    assert controller.handles(FINISH)
    assert not controller.handles("read_file")


def test_controller_create_plan() -> None:
    controller = PlanningController(
        executor=PlanExecutor(), completion=CompletionEvaluator()
    )
    state = AgentState.create(task="test task")
    result = controller._create_plan(
        state, {"steps": ["test step"], "completion_criteria": ["test criterion"]}
    )
    assert result is not None
    assert state.plan is not None
    assert state.completion_criteria is not None
    assert state.plan.steps[0].id == "step-1"
    assert state.completion_criteria.items[0].id == "criterion-1"

    with pytest.raises(RuntimeError, match="already exists"):
        controller._create_plan(state, {"steps": [], "completion_criteria": []})

def test_controller_create_plan_structure_error() -> None:
    controller = PlanningController(
        executor=PlanExecutor(), completion=CompletionEvaluator()
    )
    state = AgentState.create(task="test task")
    with pytest.raises(TypeError, match="must be a list"):
        controller._create_plan(
            state, {"steps": ["test step"]}
        )

    with pytest.raises(TypeError, match="only strings"):
        controller._create_plan(
            state, {"steps": ["test step", 123], "completion_criteria": ["test criterion", 456]}
        )


def test_controller_progress_update() -> None:
    executor=PlanExecutor()
    controller = PlanningController(
        executor=executor, completion=CompletionEvaluator()
    )
    state = AgentState.create(task="test task")
    state.attach_plan(
        Plan.create(descriptions=["test step1", "test step2"])
    )

    executor.start_next_step(state)

    controller._update_progress(state, {"step_id": "step-1", "status": "completed", "summary": "test summary"})

    assert state.plan is not None
    assert state.plan.steps[0].id == "step-1"
    assert state.plan.steps[0].result == "test summary"
    assert state.plan.steps[0].status == "completed"
