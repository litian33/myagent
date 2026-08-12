from agent.memory.model import (
    MemoryKind,
    MemoryScope,
)
from agent.memory.write import (
    MemoryCandidate,
    MemorySource,
)


class MemoryCapture:
    def __init__(
        self,
        *,
        scope: MemoryScope,
    ) -> None:
        self._scope = scope

    def capture_completed_run(
        self,
        *,
        task: str,
        output: str,
    ) -> list[MemoryCandidate]:
        if not task.strip():
            raise ValueError("Task cannot be empty")

        if not output.strip():
            raise ValueError("Run output cannot be empty")

        content = f"Completed task: {task.strip()}\nOutcome: {output.strip()}"

        return [
            MemoryCandidate(
                kind=MemoryKind.EPISODIC,
                scope=self._scope,
                content=content,
                source=(MemorySource.VERIFIED_OBSERVATION),
            )
        ]
