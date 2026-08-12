from agent.memory import (
    MemoryKind,
    MemoryScope,
    MemoryScopeKind,
    SQLiteMemoryStore,
)


def test_sqlite_memory_store_lifecycle(
    tmp_path,
) -> None:
    path = tmp_path / "memory.db"

    scope = MemoryScope(
        kind=MemoryScopeKind.PROJECT,
        key="myagent",
    )

    #
    # Process/store instance A
    #
    store = SQLiteMemoryStore(path)

    created = store.put(
        kind=MemoryKind.SEMANTIC,
        scope=scope,
        content="Project uses pytest.",
    )

    loaded = store.get(created.id)

    assert loaded == created

    matches = store.search(
        "pytest",
        kind=MemoryKind.SEMANTIC,
        scope=scope,
    )

    assert [memory.id for memory in matches] == [created.id]

    #
    # Simulate a new process by constructing
    # a new store over the same SQLite file.
    #
    reopened = SQLiteMemoryStore(path)

    persisted = reopened.get(created.id)

    assert persisted == created

    assert reopened.delete(created.id)

    assert reopened.get(created.id) is None

    assert not reopened.delete(created.id)
