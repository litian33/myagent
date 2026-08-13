from agent.knowledge.chunking import LineChunker
from agent.knowledge.model import Document, DocumentMetadata


def test_line_chunker_preserves_source_metadata() -> None:
    document = Document(
        id="example.py",
        content=("line1\nline2\nline3\nline4\nline5\n"),
        metadata=DocumentMetadata(
            path="example.py",
            language="python",
        ),
    )

    chunker = LineChunker(
        lines_per_chunk=2,
    )

    chunks = chunker.chunk(document)

    assert len(chunks) == 3

    assert chunks[0].content == ("line1\nline2")

    assert chunks[0].metadata.start_line == 1

    assert chunks[0].metadata.end_line == 2

    assert chunks[0].metadata.path == "example.py"

    assert chunks[2].metadata.start_line == 5

    assert chunks[2].metadata.end_line == 5
