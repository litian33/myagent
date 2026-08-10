import pytest

from agent.state import AgentState, AgentStatus


def test_agent_state_starts_created() -> None:
    state = AgentState.create("test")

    assert state.status == AgentStatus.CREATED


def test_agent_state_can_start() -> None:
    state = AgentState.create("test")

    state.start()

    assert state.status == AgentStatus.RUNNING


def test_agent_state_can_complete() -> None:
    state = AgentState.create("test")

    state.start()
    state.complete()

    assert state.status == AgentStatus.COMPLETED


def test_agent_state_can_reach_max_steps() -> None:
    state = AgentState.create("test")

    state.start()
    state.reach_max_steps()

    assert state.status == AgentStatus.MAX_STEPS_REACHED


def test_agent_cannot_complete_before_start() -> None:
    state = AgentState.create("test")

    with pytest.raises(RuntimeError):
        state.complete()


def test_completed_agent_cannot_start_again() -> None:
    state = AgentState.create("test")

    state.start()
    state.complete()

    with pytest.raises(RuntimeError):
        state.start()
