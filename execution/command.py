from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

MAX_STREAM_CHARS = 5_000


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
    "SYSTEMROOT",
    "WINDIR",
)


@dataclass(
    frozen=True,
    slots=True,
)
class CommandRequest:
    argv: tuple[str, ...]
    cwd: Path
    timeout_seconds: int


@dataclass(
    frozen=True,
    slots=True,
)
class CommandExecutionResult:
    exit_code: int | None

    stdout: str
    stderr: str

    stdout_truncated: bool
    stderr_truncated: bool

    timed_out: bool
    duration_ms: int


@dataclass(
    frozen=True,
    slots=True,
)
class IsolationProfile:
    filesystem_isolated: bool
    environment_isolated: bool
    network_isolated: bool
    process_isolated: bool


class CommandExecutor(Protocol):
    @property
    def isolation(
        self,
    ) -> IsolationProfile: ...

    def execute(
        self,
        request: CommandRequest,
    ) -> CommandExecutionResult: ...


def _build_safe_environment() -> dict[str, str]:
    result: dict[
        str,
        str,
    ] = {}

    for name in SAFE_ENVIRONMENT_VARIABLES:
        value = os.environ.get(name)

        if value is not None:
            result[name] = value

    return result


def _truncate_output(
    value: str,
) -> tuple[str, bool]:
    if len(value) <= MAX_STREAM_CHARS:
        return (
            value,
            False,
        )

    return (
        value[:MAX_STREAM_CHARS],
        True,
    )


def _decode_timeout_output(
    value: str | bytes | None,
) -> str:
    if value is None:
        return ""

    if isinstance(
        value,
        bytes,
    ):
        return value.decode(
            "utf-8",
            errors="replace",
        )

    return value


class LocalCommandExecutor:
    @property
    def isolation(
        self,
    ) -> IsolationProfile:
        return IsolationProfile(
            filesystem_isolated=False,
            environment_isolated=True,
            network_isolated=False,
            process_isolated=False,
        )

    def execute(
        self,
        request: CommandRequest,
    ) -> CommandExecutionResult:
        started_at = time.monotonic()

        try:
            completed = subprocess.run(
                list(request.argv),
                cwd=request.cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=(request.timeout_seconds),
                check=False,
                shell=False,
                env=(_build_safe_environment()),
            )

            stdout, (stdout_truncated) = _truncate_output(completed.stdout)

            stderr, (stderr_truncated) = _truncate_output(completed.stderr)

            return CommandExecutionResult(
                exit_code=(completed.returncode),
                stdout=stdout,
                stderr=stderr,
                stdout_truncated=(stdout_truncated),
                stderr_truncated=(stderr_truncated),
                timed_out=False,
                duration_ms=int((time.monotonic() - started_at) * 1000),
            )

        except subprocess.TimeoutExpired as exc:
            stdout = _decode_timeout_output(exc.stdout)

            stderr = _decode_timeout_output(exc.stderr)

            stdout, (stdout_truncated) = _truncate_output(stdout)

            stderr, (stderr_truncated) = _truncate_output(stderr)

            return CommandExecutionResult(
                exit_code=None,
                stdout=stdout,
                stderr=stderr,
                stdout_truncated=(stdout_truncated),
                stderr_truncated=(stderr_truncated),
                timed_out=True,
                duration_ms=int((time.monotonic() - started_at) * 1000),
            )
