from __future__ import annotations

import hashlib
import os
import stat
import tempfile
from pathlib import Path
from typing import TypedDict

from tools.base import Tool, tool

MAX_WRITE_BYTES = 200_000

MISSING_FILE_SHA256 = "MISSING"


PROTECTED_PATH_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
}


class WriteFileResult(TypedDict):
    path: str

    created: bool

    previous_sha256: str | None
    sha256: str

    bytes_written: int


def _resolve_target_path(
    *,
    workspace_root: Path,
    path: str,
) -> Path:
    relative = Path(path)

    if relative.is_absolute():
        raise ValueError("File path must be relative to the workspace root")

    if not relative.parts:
        raise ValueError("File path cannot be empty")

    if any(part in PROTECTED_PATH_PARTS for part in relative.parts):
        raise ValueError("Writing to protected workspace paths is not allowed")

    candidate = workspace_root / relative

    #
    # Do not allow writing through an
    # existing symbolic link.
    #
    if candidate.is_symlink():
        raise ValueError("Writing through symbolic links is not allowed")

    resolved = candidate.resolve(
        strict=False,
    )

    if not resolved.is_relative_to(workspace_root):
        raise ValueError("File path must stay inside the workspace")

    if resolved.exists():
        if not resolved.is_file():
            raise ValueError(f"Target is not a file: {path}")
    else:
        parent = resolved.parent

        if not parent.exists():
            raise ValueError(
                f"Parent directory does not exist: {parent.relative_to(workspace_root)}"
            )

        if not parent.is_dir():
            raise ValueError("Parent path is not a directory")

    return resolved

def _sha256_bytes(
    data: bytes,
) -> str:
    return hashlib.sha256(
        data
    ).hexdigest()

def _sha256_file(
    path: Path,
) -> str:
    return _sha256_bytes(
        path.read_bytes()
    )

def _validate_expected_version(
    *,
    target: Path,
    expected_sha256: str,
) -> str | None:
    if target.exists():
        actual_sha256 = (
            _sha256_file(target)
        )

        if (
            expected_sha256
            == MISSING_FILE_SHA256
        ):
            raise ValueError(
                "File already exists; "
                "creation requires a missing target"
            )

        if (
            actual_sha256
            != expected_sha256
        ):
            raise ValueError(
                "File changed since it was read. "
                f"Expected SHA-256 "
                f"{expected_sha256}, "
                f"but current SHA-256 is "
                f"{actual_sha256}. "
                "Read the file again before writing."
            )

        return actual_sha256

    if (
        expected_sha256
        != MISSING_FILE_SHA256
    ):
        raise ValueError(
            "File does not exist. "
            "Use expected_sha256='MISSING' "
            "when creating a new file."
        )

    return None

def _atomic_write(
    *,
    target: Path,
    data: bytes,
) -> None:
    existing_mode: int | None = None

    if target.exists():
        existing_mode = stat.S_IMODE(
            target.stat().st_mode
        )

    file_descriptor, temp_name = (
        tempfile.mkstemp(
            prefix=f".{target.name}.",
            suffix=".tmp",
            dir=target.parent,
        )
    )

    temp_path = Path(temp_name)

    try:
        with os.fdopen(
            file_descriptor,
            "wb",
        ) as temp_file:
            temp_file.write(data)

            temp_file.flush()

            os.fsync(
                temp_file.fileno()
            )

        if existing_mode is not None:
            os.chmod(
                temp_path,
                existing_mode,
            )

        os.replace(
            temp_path,
            target,
        )

    finally:
        if temp_path.exists():
            temp_path.unlink()


def create_write_file_tool(
    *,
    workspace_root: Path,
) -> Tool:
    workspace_root = (
        workspace_root.resolve()
    )

    @tool(
        description=(
            "Create or replace a UTF-8 text file inside "
            "the current workspace. "
            "Before replacing an existing file, first call "
            "read_file and pass its returned sha256 as "
            "expected_sha256. Never invent the hash. "
            "To create a new file, pass "
            "expected_sha256='MISSING'. "
            "Writing outside the workspace or into protected "
            "runtime directories is not allowed."
        )
    )
    def write_file(
        path: str,
        content: str,
        expected_sha256: str,
    ) -> WriteFileResult:
        target = _resolve_target_path(
            workspace_root=workspace_root,
            path=path,
        )

        data = content.encode(
            "utf-8",
        )

        if len(data) > MAX_WRITE_BYTES:
            raise ValueError(
                "File content is too large: "
                f"{len(data)} bytes; "
                f"maximum is "
                f"{MAX_WRITE_BYTES} bytes"
            )

        previous_sha256 = (
            _validate_expected_version(
                target=target,
                expected_sha256=(
                    expected_sha256
                ),
            )
        )

        created = (
            previous_sha256 is None
        )

        #
        # Re-check immediately before replacing.
        # This narrows the race window.
        #
        _validate_expected_version(
            target=target,
            expected_sha256=(
                expected_sha256
            ),
        )

        _atomic_write(
            target=target,
            data=data,
        )

        new_sha256 = (
            _sha256_bytes(data)
        )

        return {
            "path": str(
                target.relative_to(
                    workspace_root
                )
            ),
            "created": created,
            "previous_sha256": (
                previous_sha256
            ),
            "sha256": new_sha256,
            "bytes_written": len(data),
        }

    return write_file
