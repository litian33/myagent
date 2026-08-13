from typing import Protocol

from agent.knowledge.model import (
    Chunk,
    ChunkMetadata,
    Document,
)


class DocumentChunker(Protocol):
    def chunk(
        self,
        document: Document,
    ) -> list[Chunk]: ...


class LineChunker:
    def __init__(
        self,
        *,
        lines_per_chunk: int = 40,
    ) -> None:
        if lines_per_chunk < 1:
            raise ValueError("lines_per_chunk must be >= 1")

        self._lines_per_chunk = lines_per_chunk

    def chunk(
        self,
        document: Document,
    ) -> list[Chunk]:
        lines = document.content.splitlines()

        chunks: list[Chunk] = []

        for offset in range(
            0,
            len(lines),
            self._lines_per_chunk,
        ):
            chunk_lines = lines[offset : offset + self._lines_per_chunk]

            start_line = offset + 1

            end_line = offset + len(chunk_lines)

            content = "\n".join(chunk_lines)

            chunks.append(
                Chunk(
                    id=(f"{document.id}:{start_line}-{end_line}"),
                    document_id=(document.id),
                    content=content,
                    metadata=ChunkMetadata(
                        path=(document.metadata.path),
                        start_line=start_line,
                        end_line=end_line,
                        language=(document.metadata.language),
                    ),
                )
            )

        return chunks
