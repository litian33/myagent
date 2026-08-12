from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MemoryKind(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class MemoryScopeKind(str, Enum):
    GLOBAL = "global"
    USER = "user"
    PROJECT = "project"
    WORKSPACE = "workspace"


@dataclass(
    frozen=True,
    slots=True,
)
class MemoryScope:
    kind: MemoryScopeKind
    key: str | None = None

    def __post_init__(self) -> None:
        if self.kind == MemoryScopeKind.GLOBAL:
            if self.key is not None:
                raise ValueError("Global memory scope cannot have a key")
            return

        if self.key is None or not self.key.strip():
            raise ValueError(f"{self.kind.value} memory scope requires a key")


@dataclass(
    frozen=True,
    slots=True,
)
class MemoryRecord:
    id: str
    kind: MemoryKind
    scope: MemoryScope
    content: str
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Memory id cannot be empty")

        if not self.content.strip():
            raise ValueError("Memory content cannot be empty")
