from agent.knowledge.vector import VectorSearchResult


class FakeVectorRetriever:
    def __init__(
        self,
        results: list[VectorSearchResult],
    ) -> None:
        self._results = results

    def retrieve(
        self,
        query: str,
        *,
        limit: int | None = None,
    ) -> list[VectorSearchResult]:
        if limit is None:
            return self._results

        return self._results[:limit]
