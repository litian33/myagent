from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from execution.command import (
    CommandExecutionResult,
    CommandRequest,
    IsolationProfile,
)
from tools.workspace import Workspace

SYSTEM_RUNTIME_PATHS = (
    Path("/usr"),
    Path("/bin"),
    Path("/sbin"),
    Path("/lib"),
    Path("/lib64"),
)

SYSTEM_CONFIG_PATHS = (
    Path("/etc/ld.so.cache"),
    Path("/etc/ld.so.conf"),
    Path("/etc/ld.so.conf.d"),
    Path("/etc/passwd"),
    Path("/etc/group"),
    Path("/etc/nsswitch.conf"),
    Path("/etc/localtime"),
    Path("/etc/gitconfig"),
)

DEFAULT_SANDBOX_PATHS = (
    "/usr/local/bin",
    "/usr/bin",
    "/bin",
    "/usr/local/sbin",
    "/usr/sbin",
    "/sbin",
)


@dataclass(
    frozen=True,
    slots=True,
)
class BubblewrapConfig:
    runtime_roots: tuple[
        Path,
        ...,
    ] = ()

    extra_path_entries: tuple[
        str,
        ...,
    ] = ()


def _append_system_mount(
    arguments: list[str],
    path: Path,
) -> None:
    if not path.exists():
        return

    if path.is_symlink():
        arguments.extend(
            [
                "--symlink",
                os.readlink(path),
                str(path),
            ]
        )
        return
    arguments.extend(
        [
            "--ro-bind",
            str(path),
            str(path),
        ]
    )


def _append_system_config_mounts(
    arguments: list[str],
) -> None:
    for path in SYSTEM_CONFIG_PATHS:
        arguments.extend(
            [
                "--ro-bind-try",
                str(path),
                str(path),
            ]
        )


def _append_environment(
    arguments: list[str],
    *,
    path: str,
) -> None:
    environment = {
        "HOME": "/home/myagent",
        "TMPDIR": "/tmp",
        "PATH": path,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "XDG_CACHE_HOME": "/tmp/cache",
    }

    arguments.append("--clearenv")

    for name, value in environment.items():
        arguments.extend(
            [
                "--setenv",
                name,
                value,
            ]
        )


def _build_sandbox_path(
    config: BubblewrapConfig,
) -> str:
    entries = [
        *config.extra_path_entries,
        *DEFAULT_SANDBOX_PATHS,
    ]

    return ":".join(dict.fromkeys(entries))


class BubblewrapCommandExecutor:
    def __init__(
        self,
        *,
        workspace: Workspace,
        config: BubblewrapConfig,
    ) -> None:
        binary = shutil.which("bwrap")

        if binary is None:
            raise RuntimeError(
                "bubblewrap is not installed or bwrap is not available on PATH"
            )

        self._binary = Path(binary)

        self._workspace = workspace

        self._config = config

        for root in config.runtime_roots:
            resolved = root.resolve(strict=True)

            if not (resolved.is_dir()):
                raise ValueError(f"Bubblewrap runtime root must be a directory: {root}")

    @property
    def isolation(
        self,
    ) -> IsolationProfile:
        return IsolationProfile(
            filesystem_isolated=True,
            environment_isolated=True,
            network_isolated=True,
            process_isolated=True,
        )

    def _build_arguments(
        self,
        *,
        request: CommandRequest,
        executable: Path,
        empty_secret_file: Path,
    ) -> list[str]:
        arguments = [
            str(self._binary),
            "--unshare-user",
            "--unshare-pid",
            "--unshare-net",
            "--unshare-ipc",
            "--unshare-uts",
            "--unshare-cgroup-try",
            "--disable-userns",
            "--die-with-parent",
            "--new-session",
            "--clearenv",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--dir",
            "/home",
            "--dir",
            "/home/myagent",
        ]

        for path in SYSTEM_RUNTIME_PATHS:
            _append_system_mount(
                arguments,
                path,
            )

        _append_system_config_mounts(arguments)

        for runtime_root in self._config.runtime_roots:
            arguments.extend(
                [
                    "--ro-bind",
                    str(runtime_root),
                    str(runtime_root),
                ]
            )

        #
        # Workspace itself is writable.
        #
        arguments.extend(
            [
                "--bind",
                str(self._workspace.root),
                str(self._workspace.root),
            ]
        )

        #
        # Protect git metadata.
        #
        git_dir = self._workspace.root / ".git"

        if git_dir.exists():
            arguments.extend(
                [
                    "--ro-bind",
                    str(git_dir),
                    str(git_dir),
                ]
            )

        #
        # Hide workspace secrets.
        #
        for secret in self._workspace.secret_paths():
            if secret.is_dir():
                arguments.extend(
                    [
                        "--tmpfs",
                        str(secret),
                    ]
                )

            else:
                arguments.extend(
                    [
                        "--ro-bind",
                        str(empty_secret_file),
                        str(secret),
                    ]
                )

        sandbox_path = _build_sandbox_path(self._config)

        environment = {
            "HOME": "/home/myagent",
            "TMPDIR": "/tmp",
            "XDG_CACHE_HOME": "/tmp/cache",
            "PATH": sandbox_path,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }

        for name, value in environment.items():
            arguments.extend(
                [
                    "--setenv",
                    name,
                    value,
                ]
            )

        arguments.extend(
            [
                "--chdir",
                str(request.cwd),
                "--",
                str(executable),
                *request.argv[1:],
            ]
        )

        return arguments

    def _resolve_executable(
        self,
        executable: str,
    ) -> Path:
        resolved = shutil.which(executable)

        if resolved is None:
            raise ValueError(f"Executable not found: {executable}")

        path = Path(resolved).resolve()

        if path.is_relative_to(self._workspace.root):
            return path

        allowed_roots = [
            Path("/usr"),
            Path("/bin"),
            Path("/sbin"),
            Path("/lib"),
            Path("/lib64"),
            *self._config.runtime_roots,
        ]

        for root in allowed_roots:
            try:
                resolved_root = root.resolve(strict=True)
            except OSError:
                continue

            if path.is_relative_to(resolved_root):
                return path

        raise ValueError(f"Executable is outside the sandbox runtime roots: {path}")

    def execute(
        self,
        request: CommandRequest,
    ) -> CommandExecutionResult:
        executable = self._resolve_executable(request.argv[0])

        started_at = time.monotonic()

        with tempfile.NamedTemporaryFile() as empty_secret_file:
            arguments = self._build_arguments(
                request=request,
                executable=executable,
                empty_secret_file=(Path(empty_secret_file.name)),
            )

            try:
                completed = subprocess.run(
                    arguments,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=(request.timeout_seconds),
                    check=False,
                    #
                    # This is the environment
                    # of bwrap itself.
                    #
                    env={
                        "PATH": "/usr/bin:/bin",
                        "LANG": "C.UTF-8",
                    },
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

    def verify(
        self,
    ) -> None:
        probe = subprocess.run(
            [
                str(self._binary),
                "--unshare-user",
                "--unshare-pid",
                "--unshare-net",
                "--new-session",
                "--ro-bind",
                "/usr",
                "/usr",
                "--proc",
                "/proc",
                "--dev",
                "/dev",
                "--",
                "/usr/bin/true",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            env={
                "PATH": "/usr/bin:/bin",
            },
        )

        if probe.returncode != 0:
            raise RuntimeError(
                f"Bubblewrap sandbox is not available:\n{probe.stderr.strip()}"
            )
