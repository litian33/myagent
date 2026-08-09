from collections.abc import Mapping

from policy.model import (
    PolicyDecision,
    PolicyResult,
    ToolCapability,
)
from tools.base import Tool

DEFAULT_POLICY: dict[
    ToolCapability,
    PolicyDecision,
] = {
    ToolCapability.READ: PolicyDecision.ALLOW,
    ToolCapability.EXECUTE: PolicyDecision.REQUIRE_APPROVAL,
    ToolCapability.WRITE: PolicyDecision.REQUIRE_APPROVAL,
    ToolCapability.DESTRUCTIVE: PolicyDecision.DENY,
    ToolCapability.NETWORK: PolicyDecision.DENY,
}


class ToolPolicy:
    def __init__(
        self,
        *,
        decisions: Mapping[
            ToolCapability,
            PolicyDecision,
        ]
        | None = None,
    ) -> None:
        self._decisions = dict(DEFAULT_POLICY if decisions is None else decisions)

    def evaluate(
        self,
        tool: Tool,
    ) -> PolicyResult:
        decision = self._decisions.get(
            tool.capability,
            PolicyDecision.DENY,
        )

        return PolicyResult(
            decision=decision,
            reason=(
                f"Capability "
                f"{tool.capability.value!r} "
                f"is configured as "
                f"{decision.value!r}"
            ),
        )
