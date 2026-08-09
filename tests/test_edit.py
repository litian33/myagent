import hashlib

import pytest

from tools.edit import (
    create_write_file_tool,
)


def sha256(
    value: str,
) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_create_file(
    tmp_path,
) -> None:
    tool = create_write_file_tool(
        workspace_root=tmp_path,
    )

    result = tool.handler(
        path="hello.txt",
        content="hello\n",
        expected_sha256="MISSING",
    )

    assert result["created"] is True

    assert (tmp_path / "hello.txt").read_text() == "hello\n"


def test_replace_existing_file(
    tmp_path,
) -> None:
    target = tmp_path / "hello.txt"

    target.write_text("before\n")

    tool = create_write_file_tool(
        workspace_root=tmp_path,
    )

    result = tool.handler(
        path="hello.txt",
        content="after\n",
        expected_sha256=sha256("before\n"),
    )

    assert result["created"] is False

    assert target.read_text() == ("after\n")


def test_reject_stale_write(
    tmp_path,
) -> None:
    target = tmp_path / "hello.txt"

    target.write_text("current\n")

    tool = create_write_file_tool(
        workspace_root=tmp_path,
    )

    with pytest.raises(
        ValueError,
        match="changed since it was read",
    ):
        tool.handler(
            path="hello.txt",
            content="new\n",
            expected_sha256=sha256("old\n"),
        )

    assert target.read_text() == ("current\n")


def test_reject_parent_escape(
    tmp_path,
) -> None:
    tool = create_write_file_tool(
        workspace_root=tmp_path,
    )

    with pytest.raises(
        ValueError,
    ):
        tool.handler(
            path="../outside.txt",
            content="bad",
            expected_sha256="MISSING",
        )


def test_reject_git_directory(
    tmp_path,
) -> None:
    git_dir = tmp_path / ".git"

    git_dir.mkdir()

    tool = create_write_file_tool(
        workspace_root=tmp_path,
    )

    with pytest.raises(
        ValueError,
    ):
        tool.handler(
            path=".git/config",
            content="bad",
            expected_sha256="MISSING",
        )


def add(
    a: int,
    b: int,
) -> int:
    return a + b


def test_add() -> None:
    assert add(1, 2) == 3
