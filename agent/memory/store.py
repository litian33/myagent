from typing import Protocol

from agent.memory.model import (
    MemoryKind,
    MemoryRecord,
    MemoryScope,
)


class MemoryStore(Protocol):
    def put(
        self,
        *,
        kind: MemoryKind,
        scope: MemoryScope,
        content: str,
    ) -> MemoryRecord: ...

    def get(
        self,
        memory_id: str,
    ) -> MemoryRecord | None: ...

    def search(
        self,
        query: str,
        *,
        kind: MemoryKind | None = None,
        scope: MemoryScope | None = None,
        limit: int = 20,
    ) -> list[MemoryRecord]: ...

    def delete(
        self,
        memory_id: str,
    ) -> bool: ...
