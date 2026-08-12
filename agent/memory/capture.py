from agent.memory.model import (
    MemoryKind,
    MemoryScope,
)
from agent.memory.proposal import MemoryProposalExtractor
from agent.memory.write import (
    MemoryCandidate,
    MemorySource,
)

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
    ) -> list[MemoryCandidate]:
        proposals = self._extractor.extract(user_input)

        candidates: list[MemoryCandidate] = []

        for proposal in proposals:
            evidence = proposal.evidence.strip()

            if not evidence:
                continue

            #
            # Grounding:
            # model cannot invent evidence.
            #
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

        return candidates
