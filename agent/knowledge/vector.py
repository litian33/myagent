from dataclasses import dataclass
from typing import Protocol

from agent.knowledge.embedding import (
    Embedding,
)
from agent.knowledge.model import (
    Chunk,
)
from agent.knowledge.similarity import cosine_similarity


@dataclass(
    frozen=True,
    slots=True,
)
class VectorEntry:
    chunk: Chunk
    embedding: Embedding


@dataclass(
    frozen=True,
    slots=True,
)
class VectorSearchResult:
    chunk: Chunk
    score: float


class VectorIndex(Protocol):
    def add(
        self,
        entries: list[VectorEntry],
    ) -> None: ...

    def search(
        self,
        query: Embedding,
        *,
        limit: int,
    ) -> list[VectorSearchResult]: ...


class InMemoryVectorIndex:
    def __init__(self) -> None:
        self._entries: list[VectorEntry] = []

    def add(
        self,
        entries: list[VectorEntry],
    ) -> None:
        self._entries.extend(entries)

    def search(
        self,
        query: Embedding,
        *,
        limit: int,
    ) -> list[VectorSearchResult]:
        if limit < 1:
            raise ValueError("limit must be >= 1")

        results: list[VectorSearchResult] = []

        for entry in self._entries:
            score = cosine_similarity(
                query,
                entry.embedding,
            )

            results.append(
                VectorSearchResult(
                    chunk=entry.chunk,
                    score=score,
                )
            )

        results.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return results[:limit]
