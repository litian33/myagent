from unittest.mock import MagicMock, Mock

import pytest
from openai import OpenAI

from agent.compaction import ContextCompactor
from agent.context import ContextManager
from agent.errors import (
    AgentErrorKind,
    ContextExecutionError,
    ModelInvocationError,
)
from agent.runtime import AgentRuntime
from agent.state import AgentState, AgentStatus
from policy.approval import ApprovalHandler
from policy.engine import ToolPolicy
from tools.registry import ToolRegistry


@pytest.fixture
def runtime() -> AgentRuntime:
    return AgentRuntime(
        client=MagicMock(spec=OpenAI),
        model="test-model",
        instructions="test",
        tools=ToolRegistry(),
        context=MagicMock(spec=ContextManager),
        compactor=MagicMock(spec=ContextCompactor),
        policy=MagicMock(spec=ToolPolicy),
        approval=MagicMock(spec=ApprovalHandler),
        max_output_tokens=100,
        max_steps=3,
    )


def test_running_agent_can_fail() -> None:
    state = AgentState.create("test")

    state.start()
    state.fail()

    assert state.status == AgentStatus.FAILED


def test_created_agent_cannot_fail() -> None:
    state = AgentState.create("test")

    with pytest.raises(RuntimeError):
        state.fail()


@pytest.mark.parametrize(
    "retryable",
    [
        True,
        False,
    ],
)
def test_model_error_becomes_failed_result(
    runtime: AgentRuntime,
    monkeypatch: pytest.MonkeyPatch,
    retryable: bool,
) -> None:
    monkeypatch.setattr(
        runtime,
        "_run",
        Mock(
            side_effect=ModelInvocationError(
                "model failed",
                retryable=retryable,
            )
        ),
    )

    result = runtime.run("test")

    assert result.status == AgentStatus.FAILED
    assert result.output is None

    assert result.error is not None
    assert result.error.kind == AgentErrorKind.MODEL
    assert result.error.retryable is retryable


def test_context_error_becomes_failed_result(
    runtime: AgentRuntime,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runtime,
        "_run",
        Mock(side_effect=ContextExecutionError("context budget exceeded")),
    )

    result = runtime.run("test")

    assert result.status == AgentStatus.FAILED
    assert result.output is None

    assert result.error is not None
    assert result.error.kind == AgentErrorKind.CONTEXT
    assert result.error.retryable is False
