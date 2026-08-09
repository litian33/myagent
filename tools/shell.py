from __future__ import annotations

import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import TypedDict

from policy.model import (
    ToolCapability,
)
from tools.base import Tool, tool
from tools.workspace import Workspace

SAFE_ENVIRONMENT_VARIABLES = (
    "PATH",
    "HOME",
    "USER",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TERM",
    "TMPDIR",
    "VIRTUAL_ENV",
    # Windows compatibility.
    "SYSTEMROOT",
    "WINDIR",
)

MAX_TIMEOUT_SECONDS = 120
MAX_STREAM_CHARS = 5_000

SHELL_CONTROL_TOKENS = {
    "|",
    "||",
    "&&",
    ";",
    ">",
    ">>",
    "<",
    "<<",
}


class CommandResult(TypedDict):
    command: str
    cwd: str
    exit_code: int | None

    stdout: str
    stderr: str

    stdout_truncated: bool
    stderr_truncated: bool

    timed_out: bool
    duration_ms: int


def _build_safe_environment() -> dict[str, str]:
    result: dict[str, str] = {}

    for name in SAFE_ENVIRONMENT_VARIABLES:
        value = os.environ.get(name)

        if value is not None:
            result[name] = value

    return result


def _truncate_output(
    value: str,
) -> tuple[str, bool]:
    if len(value) <= MAX_STREAM_CHARS:
        return value, False

    return (
        value[:MAX_STREAM_CHARS],
        True,
    )


def _decode_timeout_output(
    value: str | bytes | None,
) -> str:
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode(
            "utf-8",
            errors="replace",
        )

    return value


def _resolve_cwd(
    *,
    workspace_root: Path,
    cwd: str,
) -> Path:
    relative = Path(cwd)

    if relative.is_absolute():
        raise ValueError("cwd must be relative to the workspace root")

    resolved = (workspace_root / relative).resolve()

    if not resolved.is_relative_to(workspace_root):
        raise ValueError("cwd must stay inside the workspace")

    if not resolved.exists():
        raise ValueError(f"Working directory does not exist: {cwd}")

    if not resolved.is_dir():
        raise ValueError(f"Working directory is not a directory: {cwd}")

    return resolved


def _validate_command(
    argv: list[str],
) -> None:
    if not argv:
        raise ValueError("Command cannot be empty")

    if any(token in SHELL_CONTROL_TOKENS for token in argv):
        raise ValueError("Shell operators are not supported")

    executable = argv[0]

    if "/" in executable:
        raise ValueError("Executable paths are not allowed")

    if executable in {
        "pwd",
        "ls",
        "pytest",
        "mypy",
    }:
        return

    if executable == "ruff":
        if len(argv) >= 2 and argv[1] == "check":
            return

        raise ValueError("Only 'ruff check' is allowed")

    if executable == "git":
        if len(argv) >= 2 and argv[1] in {
            "status",
            "diff",
            "log",
            "show",
            "rev-parse",
            "ls-files",
        }:
            return

        raise ValueError("Only read-only git commands are allowed")

    if executable == "go":
        if len(argv) >= 2 and argv[1] in {
            "test",
            "vet",
        }:
            return

        raise ValueError("Only 'go test' and 'go vet' are allowed")

    if executable == "cargo":
        if len(argv) >= 2 and argv[1] in {
            "test",
            "check",
            "clippy",
        }:
            return

        raise ValueError("Only cargo test/check/clippy are allowed")

    if executable in {
        "python",
        "python3",
    }:
        if (
            len(argv) >= 3
            and argv[1] == "-m"
            and argv[2]
            in {
                "pytest",
                "unittest",
            }
        ):
            return

        raise ValueError("Python may only run pytest or unittest")

    if executable in {
        "npm",
        "pnpm",
        "yarn",
    }:
        if len(argv) >= 2 and argv[1] == "test":
            return

        if len(argv) >= 3 and argv[1] == "run" and argv[2] == "test":
            return

        raise ValueError("Only test scripts are allowed")

    if executable == "make":
        if len(argv) >= 2 and argv[1] in {
            "test",
            "check",
            "lint",
        }:
            return

        raise ValueError("Only make test/check/lint are allowed")

    raise ValueError(f"Command is not allowed: {executable}")


def create_run_command_tool(
    *,
    workspace: Workspace,
) -> Tool:

    @tool(
        description=(
            "Run an approved read-only inspection, test, "
            "lint, or build-check command inside the current "
            "workspace. Shell operators, destructive commands, "
            "network commands, and commands outside the "
            "workspace are not allowed. "
            "Use cwd='.' for the workspace root."
        ),
        capability=ToolCapability.EXECUTE,
    )
    def run_command(
        command: str,
        cwd: str,
        timeout_seconds: int,
    ) -> CommandResult:
        if not command.strip():
            raise ValueError("Command cannot be empty")

        if not (1 <= timeout_seconds <= MAX_TIMEOUT_SECONDS):
            raise ValueError(
                f"timeout_seconds must be between 1 and {MAX_TIMEOUT_SECONDS}"
            )

        cwd_path = workspace.resolve_directory(cwd)

        try:
            argv = shlex.split(command)
        except ValueError as exc:
            raise ValueError(f"Invalid command syntax: {exc}") from exc

        _validate_command(argv)

        started_at = time.monotonic()

        try:
            completed = subprocess.run(
                argv,
                cwd=cwd_path,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                check=False,
                shell=False,
                env=_build_safe_environment(),
            )

            stdout, stdout_truncated = _truncate_output(completed.stdout)

            stderr, stderr_truncated = _truncate_output(completed.stderr)

            duration_ms = int((time.monotonic() - started_at) * 1000)

            return {
                "command": command,
                "cwd": workspace.relative_path(cwd_path),
                "exit_code": (completed.returncode),
                "stdout": stdout,
                "stderr": stderr,
                "stdout_truncated": (stdout_truncated),
                "stderr_truncated": (stderr_truncated),
                "timed_out": False,
                "duration_ms": duration_ms,
            }

        except subprocess.TimeoutExpired as exc:
            stdout = _decode_timeout_output(exc.stdout)
            stderr = _decode_timeout_output(exc.stderr)

            stdout, stdout_truncated = _truncate_output(stdout)

            stderr, stderr_truncated = _truncate_output(stderr)

            duration_ms = int((time.monotonic() - started_at) * 1000)

            return {
                "command": command,
                "cwd": str(cwd_path.relative_to(workspace_root)) or ".",
                "exit_code": None,
                "stdout": stdout,
                "stderr": stderr,
                "stdout_truncated": (stdout_truncated),
                "stderr_truncated": (stderr_truncated),
                "timed_out": True,
                "duration_ms": duration_ms,
            }

    return run_command
