from agent.knowledge.embedding import EmbeddingModel
from agent.knowledge.vector import VectorIndex, VectorSearchResult


class VectorRetriever:
    def __init__(
        self,
        *,
        embedding_model: EmbeddingModel,
        index: VectorIndex,
        max_results: int = 5,
    ) -> None:
        if max_results < 1:
            raise ValueError("max_results must be >= 1")

        self._embedding_model = embedding_model
        self._index = index
        self._max_results = max_results

    def retrieve(
        self,
        query: str,
    ) -> list[VectorSearchResult]:
        if not query.strip():
            return []

        embeddings = self._embedding_model.embed([query])

        if len(embeddings) != 1:
            raise ValueError("Embedding model must return exactly one query embedding")

        return self._index.search(
            embeddings[0],
            limit=self._max_results,
        )
