import hashlib

import pytest

from tools.edit import (
    _find_unique_match,
    create_apply_patch_tool,
    create_write_file_tool,
)
from tools.workspace import Workspace


def sha256(
    value: str,
) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_create_file(
    tmp_path,
) -> None:
    tool = create_write_file_tool(
        workspace=Workspace(tmp_path),
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
        workspace=Workspace(tmp_path),
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
        workspace=Workspace(tmp_path),
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
        workspace=Workspace(tmp_path),
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
        workspace=Workspace(tmp_path),
    )

    with pytest.raises(
        ValueError,
    ):
        tool.handler(
            path=".git/config",
            content="bad",
            expected_sha256="MISSING",
        )


def test_find_unique_match() -> None:
    content = "hello\nworld\n"

    index = _find_unique_match(
        content=content,
        old_text="world",
    )

    assert index == 6


def test_reject_missing_match() -> None:
    with pytest.raises(
        ValueError,
        match="not found",
    ):
        _find_unique_match(
            content="hello",
            old_text="world",
        )


def test_reject_ambiguous_match() -> None:
    with pytest.raises(
        ValueError,
        match="ambiguous",
    ):
        _find_unique_match(
            content="foo foo",
            old_text="foo",
        )


def test_reject_empty_old_text() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        _find_unique_match(
            content="hello",
            old_text="",
        )


def test_apply_patch(
    tmp_path,
) -> None:
    target = tmp_path / "calc.py"

    original = "def add(a, b):\n    return a - b\n"

    target.write_text(
        original,
        encoding="utf-8",
    )

    tool = create_apply_patch_tool(
        workspace=Workspace(tmp_path),
    )

    result = tool.handler(
        path="calc.py",
        old_text="return a - b",
        new_text="return a + b",
        expected_sha256=sha256(original),
    )

    assert target.read_text(encoding="utf-8") == ("def add(a, b):\n    return a + b\n")

    assert result["previous_sha256"] == sha256(original)


def test_apply_patch_rejects_ambiguous_text(
    tmp_path,
) -> None:
    target = tmp_path / "example.py"

    original = "return None\nreturn None\n"

    target.write_text(
        original,
        encoding="utf-8",
    )

    tool = create_apply_patch_tool(
        workspace=Workspace(tmp_path),
    )

    with pytest.raises(
        ValueError,
        match="ambiguous",
    ):
        tool.handler(
            path="example.py",
            old_text="return None",
            new_text="return value",
            expected_sha256=sha256(original),
        )


def test_apply_patch_rejects_stale_version(
    tmp_path,
) -> None:
    target = tmp_path / "example.py"

    target.write_text(
        "current\n",
        encoding="utf-8",
    )

    tool = create_apply_patch_tool(
        workspace=Workspace(tmp_path),
    )

    with pytest.raises(
        ValueError,
        match="changed since it was read",
    ):
        tool.handler(
            path="example.py",
            old_text="current",
            new_text="new",
            expected_sha256=sha256("old\n"),
        )

    assert target.read_text(encoding="utf-8") == "current\n"
