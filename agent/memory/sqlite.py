import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from agent.memory.model import (
    MemoryKind,
    MemoryRecord,
    MemoryScope,
    MemoryScopeKind,
)


class SQLiteMemoryStore:
    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _from_row(
        row: sqlite3.Row,
    ) -> MemoryRecord:
        return MemoryRecord(
            id=row["id"],
            kind=MemoryKind(row["kind"]),
            scope=MemoryScope(
                kind=MemoryScopeKind(row["scope_kind"]),
                key=row["scope_key"],
            ),
            content=row["content"],
            created_at=(datetime.fromisoformat(row["created_at"])),
            updated_at=(datetime.fromisoformat(row["updated_at"])),
        )

    def __init__(
        self,
        path: Path,
    ) -> None:
        self._path = path

        self._path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    def _connect(
        self,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)

        connection.row_factory = sqlite3.Row

        return connection

    def _initialize(
        self,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    scope_kind TEXT NOT NULL,
                    scope_key TEXT,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_memories_scope
                ON memories (
                    scope_kind,
                    scope_key
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                    idx_memories_kind
                ON memories (
                    kind
                )
                """
            )

    def put(
        self,
        *,
        kind: MemoryKind,
        scope: MemoryScope,
        content: str,
    ) -> MemoryRecord:
        if not content.strip():
            raise ValueError("Memory content cannot be empty")

        now = self._now()

        memory = MemoryRecord(
            id=str(uuid4()),
            kind=kind,
            scope=scope,
            content=content.strip(),
            created_at=now,
            updated_at=now,
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO memories (
                    id,
                    kind,
                    scope_kind,
                    scope_key,
                    content,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory.id,
                    memory.kind.value,
                    memory.scope.kind.value,
                    memory.scope.key,
                    memory.content,
                    memory.created_at.isoformat(),
                    memory.updated_at.isoformat(),
                ),
            )

        return memory

    def get(
        self,
        memory_id: str,
    ) -> MemoryRecord | None:
        if not memory_id.strip():
            raise ValueError("Memory id cannot be empty")

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    kind,
                    scope_kind,
                    scope_key,
                    content,
                    created_at,
                    updated_at
                FROM memories
                WHERE id = ?
                """,
                (memory_id,),
            ).fetchone()

        if row is None:
            return None

        return self._from_row(row)

    def search(
        self,
        query: str,
        *,
        kind: MemoryKind | None = None,
        scope: MemoryScope | None = None,
        limit: int = 20,
    ) -> list[MemoryRecord]:
        if not query.strip():
            raise ValueError("Memory search query cannot be empty")

        if limit <= 0:
            raise ValueError("Memory search limit must be positive")

        conditions = ["content LIKE ?"]

        parameters: list[object] = [f"%{query.strip()}%"]

        if kind is not None:
            conditions.append("kind = ?")
            parameters.append(kind.value)

        if scope is not None:
            conditions.append("scope_kind = ?")
            parameters.append(scope.kind.value)

            if scope.key is None:
                conditions.append("scope_key IS NULL")
            else:
                conditions.append("scope_key = ?")
                parameters.append(scope.key)

        parameters.append(limit)

        sql = f"""
            SELECT
                id,
                kind,
                scope_kind,
                scope_key,
                content,
                created_at,
                updated_at
            FROM memories
            WHERE {" AND ".join(conditions)}
            ORDER BY updated_at DESC
            LIMIT ?
        """

        with self._connect() as connection:
            rows = connection.execute(
                sql,
                parameters,
            ).fetchall()

        return [self._from_row(row) for row in rows]

    def delete(
        self,
        memory_id: str,
    ) -> bool:
        if not memory_id.strip():
            raise ValueError("Memory id cannot be empty")

        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM memories
                WHERE id = ?
                """,
                (memory_id,),
            )

            return cursor.rowcount > 0
