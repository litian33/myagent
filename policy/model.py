from dataclasses import dataclass
from enum import StrEnum


class ToolCapability(StrEnum):
    READ = "read"
    EXECUTE = "execute"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    NETWORK = "network"


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


@dataclass(
    frozen=True,
    slots=True,
)
class PolicyResult:
    decision: PolicyDecision
    reason: str


@dataclass(
    frozen=True,
    slots=True,
)
class ApprovalRequest:
    tool_name: str
    capability: ToolCapability
    arguments: str
    reason: str
