from dataclasses import dataclass
from enum import Enum

from agent.memory.model import (
    MemoryKind,
    MemoryRecord,
    MemoryScope,
    MemoryScopeKind,
)
from agent.memory.store import MemoryStore


class MemorySource(str, Enum):
    USER_EXPLICIT = "user_explicit"
    VERIFIED_OBSERVATION = "verified_observation"
    AGENT_INFERENCE = "agent_inference"


@dataclass(
    frozen=True,
    slots=True,
)
class MemoryCandidate:
    kind: MemoryKind
    scope: MemoryScope
    content: str
    source: MemorySource

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("Memory candidate content cannot be empty")


class MemoryWriteDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(
    frozen=True,
    slots=True,
)
class MemoryWriteEvaluation:
    decision: MemoryWriteDecision
    reason: str


class MemoryWritePolicy:
    def evaluate(
        self,
        candidate: MemoryCandidate,
    ) -> MemoryWriteEvaluation:
        if candidate.scope.kind == MemoryScopeKind.GLOBAL:
            return MemoryWriteEvaluation(
                decision=MemoryWriteDecision.DENY,
                reason=("Automatic global memory writes are not allowed"),
            )

        if candidate.source == MemorySource.AGENT_INFERENCE:
            return MemoryWriteEvaluation(
                decision=MemoryWriteDecision.DENY,
                reason=("Agent inference cannot be persisted as memory"),
            )

        if candidate.kind == MemoryKind.EPISODIC:
            if candidate.source != MemorySource.VERIFIED_OBSERVATION:
                return MemoryWriteEvaluation(
                    decision=(MemoryWriteDecision.DENY),
                    reason=("Episodic memory requires a verified observation"),
                )

        if candidate.kind == MemoryKind.PROCEDURAL:
            if candidate.source != MemorySource.USER_EXPLICIT:
                return MemoryWriteEvaluation(
                    decision=(MemoryWriteDecision.DENY),
                    reason=("Procedural memory requires an explicit user instruction"),
                )

        return MemoryWriteEvaluation(
            decision=MemoryWriteDecision.ALLOW,
            reason="Memory candidate is allowed",
        )


@dataclass(
    frozen=True,
    slots=True,
)
class MemoryWriteResult:
    evaluation: MemoryWriteEvaluation
    memory: MemoryRecord | None


class MemoryWriter:
    def __init__(
        self,
        *,
        store: MemoryStore,
        policy: MemoryWritePolicy,
    ) -> None:
        self._store = store
        self._policy = policy

    def write(
        self,
        candidate: MemoryCandidate,
    ) -> MemoryWriteResult:
        evaluation = self._policy.evaluate(candidate)

        if evaluation.decision == MemoryWriteDecision.DENY:
            return MemoryWriteResult(
                evaluation=evaluation,
                memory=None,
            )

        memory = self._store.put(
            kind=candidate.kind,
            scope=candidate.scope,
            content=candidate.content,
        )

        return MemoryWriteResult(
            evaluation=evaluation,
            memory=memory,
        )
