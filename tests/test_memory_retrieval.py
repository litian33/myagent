from agent.memory import (
    MemoryKind,
    MemoryScope,
    MemoryScopeKind,
    SQLiteMemoryStore,
)
from agent.memory.retrieval import (
    MemoryRetriever,
    project_memories,
)


def test_memory_retrieval(
    tmp_path,
) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.db")

    scope = MemoryScope(
        kind=MemoryScopeKind.PROJECT,
        key="myagent",
    )

    expected = store.put(
        kind=MemoryKind.SEMANTIC,
        scope=scope,
        content=("Project uses pytest for Python tests."),
    )

    store.put(
        kind=MemoryKind.SEMANTIC,
        scope=scope,
        content=("Project uses PostgreSQL."),
    )

    retriever = MemoryRetriever(
        store=store,
        scopes=[scope],
        max_results=5,
    )

    memories = retriever.retrieve("Run pytest tests")

    assert [memory.id for memory in memories] == [expected.id]

    context = project_memories(memories)

    assert len(context) == 1

    content = context[0]["content"]

    assert "Project uses pytest" in content
