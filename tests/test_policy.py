from policy.engine import ToolPolicy
from policy.model import (
    PolicyDecision,
    ToolCapability,
)
from tools.base import tool


def test_read_is_allowed() -> None:
    @tool(
        description="Read something.",
        capability=ToolCapability.READ,
    )
    def read_something(
        path: str,
    ) -> str:
        return path

    policy = ToolPolicy()

    result = policy.evaluate(read_something)

    assert result.decision == PolicyDecision.ALLOW


def test_execute_requires_approval() -> None:
    @tool(
        description="Execute something.",
        capability=(ToolCapability.EXECUTE),
    )
    def execute(
        command: str,
    ) -> str:
        return command

    policy = ToolPolicy()

    result = policy.evaluate(execute)

    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_write_requires_approval() -> None:
    @tool(
        description="Write something.",
        capability=ToolCapability.WRITE,
    )
    def write(
        path: str,
    ) -> str:
        return path

    policy = ToolPolicy()

    result = policy.evaluate(write)

    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_destructive_is_denied() -> None:
    @tool(
        description="Destroy something.",
        capability=(ToolCapability.DESTRUCTIVE),
    )
    def destroy(
        path: str,
    ) -> str:
        return path

    policy = ToolPolicy()

    result = policy.evaluate(destroy)

    assert result.decision == PolicyDecision.DENY
