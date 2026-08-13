from dataclasses import dataclass

from agent.knowledge.lexical import (
    LexicalIndex,
)
from agent.knowledge.model import Chunk
from agent.knowledge.retrieval import (
    VectorRetriever,
)


@dataclass(
    frozen=True,
    slots=True,
)
class HybridSearchResult:
    chunk: Chunk
    score: float
    vector_rank: int | None
    lexical_rank: int | None


class HybridRetriever:
    def __init__(
        self,
        *,
        vector_retriever: VectorRetriever,
        lexical_index: LexicalIndex,
        max_results: int = 5,
        candidate_limit: int = 20,
        rrf_k: int = 60,
    ) -> None:
        self._vector_retriever = vector_retriever
        self._lexical_index = lexical_index
        self._max_results = max_results
        self._candidate_limit = candidate_limit
        self._rrf_k = rrf_k

    def retrieve(
        self,
        query: str,
    ) -> list[HybridSearchResult]:
        if not query.strip():
            return []

        vector_results = self._vector_retriever.retrieve(
            query,
            limit=self._candidate_limit,
        )

        lexical_results = self._lexical_index.search(
            query,
            limit=self._candidate_limit,
        )
        scores: dict[str, float] = {}
        chunks: dict[str, Chunk] = {}
        vector_ranks: dict[str, int] = {}
        lexical_ranks: dict[str, int] = {}

        for rank, result in enumerate(
            vector_results,
            start=1,
        ):
            chunk_id = result.chunk.id

            chunks[chunk_id] = result.chunk

            vector_ranks[chunk_id] = rank

            scores[chunk_id] = scores.get(
                chunk_id,
                0.0,
            ) + 1.0 / (self._rrf_k + rank)

        for rank, result in enumerate(
            lexical_results,
            start=1,
        ):
            chunk_id = result.chunk.id

            chunks[chunk_id] = result.chunk

            lexical_ranks[chunk_id] = rank

            scores[chunk_id] = scores.get(
                chunk_id,
                0.0,
            ) + 1.0 / (self._rrf_k + rank)

        results = [
            HybridSearchResult(
                chunk=chunks[chunk_id],
                score=score,
                vector_rank=(vector_ranks.get(chunk_id)),
                lexical_rank=(lexical_ranks.get(chunk_id)),
            )
            for chunk_id, score in scores.items()
        ]

        results.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return results[: self._max_results]
