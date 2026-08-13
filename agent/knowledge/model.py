from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class DocumentMetadata:
    path: str
    language: str | None = None

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("Document path cannot be empty")


@dataclass(
    frozen=True,
    slots=True,
)
class Document:
    id: str
    content: str
    metadata: "DocumentMetadata"

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Document id cannot be empty")

        if not self.content:
            raise ValueError("Document content cannot be empty")


@dataclass(
    frozen=True,
    slots=True,
)
class ChunkMetadata:
    path: str
    start_line: int
    end_line: int
    language: str | None = None

    def __post_init__(self) -> None:
        if not self.path.strip():
            raise ValueError("Chunk path cannot be empty")

        if self.start_line < 1:
            raise ValueError("start_line must be >= 1")

        if self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")


@dataclass(
    frozen=True,
    slots=True,
)
class Chunk:
    id: str
    document_id: str
    content: str
    metadata: "ChunkMetadata"

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("Chunk id cannot be empty")

        if not self.document_id.strip():
            raise ValueError("Chunk document_id cannot be empty")

        if not self.content:
            raise ValueError("Chunk content cannot be empty")
