import pytest

from agent.state import AgentState, AgentStatus


def test_running_agent_can_fail() -> None:
    state = AgentState.create("test")

    state.start()
    state.fail()

    assert state.status == AgentStatus.FAILED


def test_created_agent_cannot_fail() -> None:
    state = AgentState.create("test")

    with pytest.raises(RuntimeError):
        state.fail()
