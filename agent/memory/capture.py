from dataclasses import dataclass

from agent.memory.model import (
    MemoryKind,
    MemoryScope,
)
from agent.memory.proposal import MemoryProposalExtractor, MemoryRoute
from agent.memory.write import (
    MemoryCandidate,
    MemorySource,
)


@dataclass(
    frozen=True,
    slots=True,
)
class MemoryCaptureResult:
    route: MemoryRoute
    candidates: list[MemoryCandidate]


class MemoryCapture:
    def __init__(
        self,
        *,
        scope: MemoryScope,
        extractor: MemoryProposalExtractor,
    ) -> None:
        self._scope = scope
        self._extractor = extractor

    def capture_user_input(
        self,
        *,
        user_input: str,
    ) -> MemoryCaptureResult:
        extraction = self._extractor.extract(user_input)

        candidates: list[MemoryCandidate] = []

        for proposal in extraction.proposals:
            evidence = proposal.evidence.strip()

            if not evidence:
                continue

            if evidence not in user_input:
                continue

            if proposal.kind not in {
                MemoryKind.SEMANTIC,
                MemoryKind.PROCEDURAL,
            }:
                continue

            candidates.append(
                MemoryCandidate(
                    kind=proposal.kind,
                    scope=self._scope,
                    content=evidence,
                    source=(MemorySource.USER_EXPLICIT),
                )
            )

        return MemoryCaptureResult(
            route=extraction.route,
            candidates=candidates,
        )
