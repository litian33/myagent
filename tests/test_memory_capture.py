from agent.memory import MemoryKind, MemoryScope, MemoryScopeKind, MemorySource
from agent.memory.capture import MemoryCapture
from agent.memory.proposal import MemoryProposal


class FakeExtractor:
    def extract(
        self,
        user_input: str,
    ) -> list[MemoryProposal]:
        return [
            MemoryProposal(
                kind=MemoryKind.PROCEDURAL,
                evidence=("本项目统一使用 pytest -q"),
            ),
            MemoryProposal(
                kind=MemoryKind.SEMANTIC,
                evidence=("用户根本没有说过 Redis"),
            ),
        ]


def test_memory_capture_grounds_user_evidence():
    scope = MemoryScope(
        kind=MemoryScopeKind.PROJECT,
        key="myagent",
    )

    capture = MemoryCapture(
        scope=scope,
        extractor=FakeExtractor(),
    )

    candidates = capture.capture_user_input(
        user_input=("记住：本项目统一使用 pytest -q")
    )

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.kind == MemoryKind.PROCEDURAL

    assert candidate.source == MemorySource.USER_EXPLICIT

    assert candidate.content == ("本项目统一使用 pytest -q")
