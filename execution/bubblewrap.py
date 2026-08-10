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
    decode_timeout_output,
    truncate_output,
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
            try:
                resolved = root.resolve(strict=True)
            except OSError as exc:
                raise ValueError(
                    f"Bubblewrap runtime root does not exist: {root}"
                ) from exc

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

    def _venv_bin(
        self,
    ) -> Path | None:
        candidate = self._workspace.root / ".venv" / "bin"

        if not candidate.is_dir():
            return None

        return candidate

    def _venv_python_roots(
        self,
    ) -> tuple[Path, ...]:
        venv_bin = self._venv_bin()

        if venv_bin is None:
            return ()

        python = venv_bin / "python"

        if not python.exists():
            python = venv_bin / "python3"

        if not python.exists():
            return ()

        try:
            real = python.resolve(strict=True)
        except OSError:
            return ()

        if real.is_relative_to(self._workspace.root):
            return ()

        for root in SYSTEM_RUNTIME_PATHS:
            try:
                if real.is_relative_to(root.resolve(strict=True)):
                    return ()
            except OSError:
                continue

        install_root = real.parent.parent

        if install_root == real.parent:
            return ()

        return (install_root,)

    def _sandbox_path_entries(
        self,
    ) -> tuple[str, ...]:
        entries = list(self._config.extra_path_entries)

        venv_bin = self._venv_bin()

        if venv_bin is not None:
            entries.append(str(venv_bin))

        entries.extend(DEFAULT_SANDBOX_PATHS)

        return tuple(dict.fromkeys(entries))

    def _build_sandbox_path(
        self,
    ) -> str:
        return ":".join(self._sandbox_path_entries())

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
        # The venv interpreter may live outside the workspace
        # (e.g. asdf/pyenv installs). Mount its install root
        # read-only so sandboxed python/pytest can run.
        #
        for venv_root in self._venv_python_roots():
            arguments.extend(
                [
                    "--ro-bind",
                    str(venv_root),
                    str(venv_root),
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
        # Remote URLs in .git/config can embed credentials.
        # Hide the file from sandboxed commands.
        #
        git_config = git_dir / "config"

        if git_config.is_file():
            arguments.extend(
                [
                    "--ro-bind",
                    str(empty_secret_file),
                    str(git_config),
                ]
            )

        #
        # Hide workspace secrets.
        #
        venv_roots = self._venv_python_roots()

        for secret in self._workspace.secret_paths():
            if secret.is_symlink():
                try:
                    target = secret.resolve(strict=True)
                except OSError:
                    target = None

                if target is not None and any(
                    target.is_relative_to(root) for root in venv_roots
                ):
                    #
                    # Symlink into an explicitly exposed runtime
                    # root (e.g. .venv/bin/python -> interpreter
                    # install). Masking it would break the venv.
                    #
                    continue

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

        sandbox_path = self._build_sandbox_path()

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
        #
        # Resolve against the sandbox PATH first, then fall back
        # to the host PATH. This keeps lookup consistent with the
        # environment the command will actually run in.
        #
        search_path = os.pathsep.join(
            [
                *self._sandbox_path_entries(),
                os.environ.get("PATH", ""),
            ]
        )

        resolved = shutil.which(
            executable,
            path=search_path,
        )

        if resolved is None:
            raise ValueError(f"Executable not found in sandbox PATH: {executable}")

        candidate = Path(resolved)

        #
        # Keep workspace-relative paths (e.g. .venv/bin/python3)
        # as-is: resolving the symlink chain would point at the
        # base interpreter and hide the virtualenv from Python.
        #
        if candidate.is_relative_to(self._workspace.root):
            return candidate

        path = candidate.resolve()

        allowed_roots = [
            Path("/usr"),
            Path("/bin"),
            Path("/sbin"),
            Path("/lib"),
            Path("/lib64"),
            *self._config.runtime_roots,
            *self._venv_python_roots(),
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
                    # The sandboxed command must not read the
                    # agent's terminal stdin.
                    #
                    stdin=subprocess.DEVNULL,
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
                stdout = decode_timeout_output(exc.stdout)

                stderr = decode_timeout_output(exc.stderr)

                stdout, (stdout_truncated) = truncate_output(stdout)

                stderr, (stderr_truncated) = truncate_output(stderr)

                return CommandExecutionResult(
                    exit_code=None,
                    stdout=stdout,
                    stderr=stderr,
                    stdout_truncated=(stdout_truncated),
                    stderr_truncated=(stderr_truncated),
                    timed_out=True,
                    duration_ms=int((time.monotonic() - started_at) * 1000),
                )

        stdout, (stdout_truncated) = truncate_output(completed.stdout)

        stderr, (stderr_truncated) = truncate_output(completed.stderr)

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
        result = self.execute(
            CommandRequest(
                argv=("true",),
                cwd=self._workspace.root,
                timeout_seconds=5,
            )
        )

        if result.timed_out or result.exit_code != 0:
            raise RuntimeError(
                f"Bubblewrap sandbox is not available:\n{result.stderr.strip()}"
            )
