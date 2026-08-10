import json

import pytest
from openai.types.responses import (
    ResponseFunctionToolCall,
)

from policy.model import ToolCapability
from tools.base import tool
from tools.registry import ToolRegistry


def make_tool_call(
    *,
    name: str,
    arguments: str = "{}",
) -> ResponseFunctionToolCall:
    return ResponseFunctionToolCall.model_construct(
        type="function_call",
        call_id="call_test",
        name=name,
        arguments=arguments,
    )


@tool(
    description="Always fails with bad input.",
    capability=ToolCapability.READ,
)
def expected_failure() -> str:
    raise ValueError("bad input")


@tool(
    description="Always crashes unexpectedly.",
    capability=ToolCapability.READ,
)
def broken_tool() -> str:
    raise AssertionError("unexpected bug")


def test_expected_tool_error_becomes_observation() -> None:
    registry = ToolRegistry()

    registry.register(expected_failure)

    result = registry.execute(
        make_tool_call(
            name="expected_failure",
        )
    )

    payload = json.loads(result)

    assert payload == {
        "error": "bad input",
        "tool": "expected_failure",
    }


def test_unexpected_tool_bug_is_not_swallowed() -> None:
    registry = ToolRegistry()

    registry.register(broken_tool)

    with pytest.raises(
        AssertionError,
        match="unexpected bug",
    ):
        registry.execute(
            make_tool_call(
                name="broken_tool",
            )
        )
