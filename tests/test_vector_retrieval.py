from agent.knowledge.embedding import Embedding
from agent.knowledge.indexing import index_chunks
from agent.knowledge.model import Chunk, ChunkMetadata
from agent.knowledge.retrieval import VectorRetriever
from agent.knowledge.vector import InMemoryVectorIndex


class KeywordEmbeddingModel:
    def embed(
        self,
        texts: list[str],
    ) -> list[Embedding]:
        return [
            [
                float("context" in text.lower()),
                float("memory" in text.lower()),
                float("database" in text.lower()),
            ]
            for text in texts
        ]


def test_vector_retriever_returns_most_relevant_chunk():
    chunks = [
        Chunk(
            id="context:1-1",
            document_id="context",
            content=("Context compaction handles context budget."),
            metadata=ChunkMetadata(
                path="context.py",
                start_line=1,
                end_line=1,
                language="python",
            ),
        ),
        Chunk(
            id="memory:1-1",
            document_id="memory",
            content=("Memory store persists long-term memory."),
            metadata=ChunkMetadata(
                path="memory.py",
                start_line=1,
                end_line=1,
                language="python",
            ),
        ),
    ]

    embedding_model = KeywordEmbeddingModel()

    index = InMemoryVectorIndex()

    index_chunks(
        chunks=chunks,
        embedding_model=(embedding_model),
        index=index,
    )

    retriever = VectorRetriever(
        embedding_model=(embedding_model),
        index=index,
        max_results=1,
    )

    results = retriever.retrieve("How does context work?")

    assert len(results) == 1

    assert results[0].chunk.id == "context:1-1"
