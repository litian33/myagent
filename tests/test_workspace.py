import pytest

from tools.workspace import (
    Workspace,
)


def test_reject_parent_escape(
    tmp_path,
) -> None:
    workspace = Workspace(tmp_path)

    with pytest.raises(
        ValueError,
        match="Parent path traversal",
    ):
        workspace.resolve_file("../outside.txt")


def test_reject_absolute_path(
    tmp_path,
) -> None:
    workspace = Workspace(tmp_path)

    with pytest.raises(
        ValueError,
        match="relative",
    ):
        workspace.resolve_file("/etc/passwd")


def test_reject_dotenv(
    tmp_path,
) -> None:
    target = tmp_path / ".env"

    target.write_text("TOKEN=secret\n")

    workspace = Workspace(tmp_path)

    with pytest.raises(
        ValueError,
        match="secret file",
    ):
        workspace.resolve_file(".env")


def test_allow_dotenv_example(
    tmp_path,
) -> None:
    target = tmp_path / ".env.example"

    target.write_text("TOKEN=\n")

    workspace = Workspace(tmp_path)

    resolved = workspace.resolve_file(".env.example")

    assert resolved == target


def test_reject_symlink_escape(
    tmp_path,
) -> None:
    outside = tmp_path.parent / "outside.txt"

    outside.write_text("secret")

    link = tmp_path / "inside.txt"

    link.symlink_to(outside)

    workspace = Workspace(tmp_path)

    with pytest.raises(
        ValueError,
        match="stay inside",
    ):
        workspace.resolve_file("inside.txt")


def test_reject_symlink_to_secret(
    tmp_path,
) -> None:
    secret = tmp_path / ".env"

    secret.write_text("TOKEN=secret")

    alias = tmp_path / "config.txt"

    alias.symlink_to(secret)

    workspace = Workspace(tmp_path)

    with pytest.raises(
        ValueError,
        match="secret file",
    ):
        workspace.resolve_file("config.txt")


def test_reject_private_key_content(
    tmp_path,
) -> None:
    target = tmp_path / "config.txt"

    data = b"-----BEGIN PRIVATE KEY-----\nsecret\n"

    target.write_bytes(data)

    workspace = Workspace(tmp_path)

    with pytest.raises(
        ValueError,
        match="private key",
    ):
        workspace.validate_read_content(data)
