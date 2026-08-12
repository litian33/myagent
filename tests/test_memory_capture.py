from agent.memory import MemoryKind, MemoryScope, MemoryScopeKind, MemorySource
from agent.memory.capture import MemoryCapture


def test_capture_completed_run() -> None:
    scope = MemoryScope(
        kind=MemoryScopeKind.PROJECT,
        key="myagent",
    )

    capture = MemoryCapture(scope=scope)

    candidates = capture.capture_completed_run(
        task=("Fix normalize_username"),
        output=("Fixed and tests passed."),
    )

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.kind == MemoryKind.EPISODIC

    assert candidate.source == MemorySource.VERIFIED_OBSERVATION

    assert "normalize_username" in candidate.content
