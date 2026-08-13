from agent.knowledge.embedding import EmbeddingModel
from agent.knowledge.model import Chunk
from agent.knowledge.vector import VectorEntry, VectorIndex


def index_chunks(
    *,
    chunks: list[Chunk],
    embedding_model: EmbeddingModel,
    index: VectorIndex,
) -> None:
    if not chunks:
        return

    embeddings = embedding_model.embed([chunk.content for chunk in chunks])

    if len(embeddings) != len(chunks):
        raise ValueError("Embedding count must match chunk count")

    entries = [
        VectorEntry(
            chunk=chunk,
            embedding=embedding,
        )
        for chunk, embedding in zip(
            chunks,
            embeddings,
            strict=True,
        )
    ]

    index.add(entries)
