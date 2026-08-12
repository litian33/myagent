from agent.memory import (
    MemoryCandidate,
    MemoryKind,
    MemoryScope,
    MemoryScopeKind,
    MemorySource,
    MemoryWriteDecision,
    MemoryWritePolicy,
    MemoryWriter,
    SQLiteMemoryStore,
)


def test_memory_write_policy(
    tmp_path,
) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.db")

    writer = MemoryWriter(
        store=store,
        policy=MemoryWritePolicy(),
    )

    user_scope = MemoryScope(
        kind=MemoryScopeKind.USER,
        key="testuser",
    )

    allowed = writer.write(
        MemoryCandidate(
            kind=MemoryKind.SEMANTIC,
            scope=user_scope,
            content=("User prefers typed OpenAI SDK definitions."),
            source=(MemorySource.USER_EXPLICIT),
        )
    )

    assert allowed.evaluation.decision == MemoryWriteDecision.ALLOW
    assert allowed.memory is not None

    denied = writer.write(
        MemoryCandidate(
            kind=MemoryKind.SEMANTIC,
            scope=MemoryScope(
                kind=(MemoryScopeKind.PROJECT),
                key="myagent",
            ),
            content=("Project probably uses Redis."),
            source=(MemorySource.AGENT_INFERENCE),
        )
    )

    assert denied.evaluation.decision == MemoryWriteDecision.DENY
    assert denied.memory is None

    assert store.search("Redis") == []
