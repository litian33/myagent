from agent.knowledge.lexical import InMemoryBM25Index
from agent.knowledge.model import Chunk, ChunkMetadata


def test_bm25_prefers_exact_identifier():
    chunks = [
        Chunk(
            id="runtime:1",
            document_id="runtime",
            content=(
                "AgentRuntime uses MemoryCaptureResult before starting the agent loop."
            ),
            metadata=ChunkMetadata(
                path="agent/runtime.py",
                start_line=1,
                end_line=5,
                language="python",
            ),
        ),
        Chunk(
            id="memory:1",
            document_id="memory",
            content=("Long term memory is stored persistently."),
            metadata=ChunkMetadata(
                path="agent/memory/store.py",
                start_line=1,
                end_line=5,
                language="python",
            ),
        ),
    ]

    index = InMemoryBM25Index()

    index.add(chunks)

    results = index.search(
        "MemoryCaptureResult",
        limit=1,
    )

    assert len(results) == 1

    assert results[0].chunk.id == "runtime:1"
