from __future__ import annotations

import os
from pathlib import Path

PROTECTED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "__pycache__",
        "node_modules",
    }
)


SECRET_DIRECTORY_NAMES = frozenset(
    {
        ".ssh",
        ".aws",
        ".gnupg",
        ".kube",
    }
)


SECRET_FILE_NAMES = frozenset(
    {
        ".env",
        ".npmrc",
        ".pypirc",
        ".netrc",
        ".dockerconfigjson",
        "credentials.json",
        "terraform.tfstate",
        "terraform.tfstate.backup",
        "secrets.toml",
    }
)


SAFE_ENV_TEMPLATE_NAMES = frozenset(
    {
        ".env.example",
        ".env.sample",
        ".env.template",
    }
)


PRIVATE_KEY_FILE_NAMES = frozenset(
    {
        "id_rsa",
        "id_dsa",
        "id_ecdsa",
        "id_ed25519",
    }
)


SECRET_FILE_SUFFIXES = frozenset(
    {
        ".key",
        ".p12",
        ".pfx",
    }
)


PRIVATE_KEY_MARKERS = (
    b"-----BEGIN PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN EC PRIVATE KEY-----",
    b"-----BEGIN OPENSSH PRIVATE KEY-----",
)


class Workspace:
    def __init__(
        self,
        root: Path,
    ) -> None:
        root = root.resolve(strict=True)

        if not root.is_dir():
            raise ValueError("Workspace root must be an existing directory")

        self._root = root

    @property
    def root(self) -> Path:
        return self._root

    def resolve_existing(
        self,
        path: str,
    ) -> Path:
        relative = self._validate_requested_path(path)

        candidate = self._root / relative

        try:
            resolved = candidate.resolve(strict=True)
        except FileNotFoundError as exc:
            raise ValueError(f"Path does not exist: {path}") from exc

        self._validate_resolved_path(resolved)

        return resolved

    def resolve_file(
        self,
        path: str,
    ) -> Path:
        resolved = self.resolve_existing(path)

        if not resolved.is_file():
            raise ValueError(f"Path is not a file: {path}")

        return resolved

    def resolve_directory(
        self,
        path: str,
    ) -> Path:
        resolved = self.resolve_existing(path)

        if not resolved.is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        return resolved

    def resolve_write_file(
        self,
        path: str,
    ) -> Path:
        relative = self._validate_requested_path(path)

        candidate = self._root / relative

        if candidate.is_symlink():
            raise ValueError("Writing through symbolic links is not allowed")

        resolved = candidate.resolve(strict=False)

        self._validate_resolved_path(resolved)

        if resolved.exists():
            if not resolved.is_file():
                raise ValueError(f"Target is not a file: {path}")

            return resolved

        parent = resolved.parent

        if not parent.exists():
            raise ValueError(
                f"Parent directory does not exist: {self.relative_path(parent)}"
            )

        if not parent.is_dir():
            raise ValueError("Parent path is not a directory")

        return resolved

    def relative_path(
        self,
        path: Path,
    ) -> str:
        relative = path.relative_to(self._root)

        value = str(relative)

        return value or "."

    def validate_read_content(
        self,
        data: bytes,
    ) -> None:
        for marker in PRIVATE_KEY_MARKERS:
            if marker in data:
                raise ValueError("File appears to contain private key material")

    def _validate_requested_path(
        self,
        path: str,
    ) -> Path:
        if not path.strip():
            raise ValueError("Path cannot be empty")

        relative = Path(path)

        if relative.is_absolute():
            raise ValueError("Path must be relative to the workspace root")

        if ".." in relative.parts:
            raise ValueError("Parent path traversal is not allowed")

        self._validate_parts(relative.parts)

        return relative

    def _validate_resolved_path(
        self,
        path: Path,
    ) -> None:
        if not path.is_relative_to(self._root):
            raise ValueError("Path must stay inside the workspace")

        relative = path.relative_to(self._root)

        self._validate_parts(relative.parts)

    @classmethod
    def _validate_parts(
        cls,
        parts: tuple[str, ...],
    ) -> None:
        for part in parts:
            lower = part.lower()

            if lower in PROTECTED_DIRECTORY_NAMES:
                raise ValueError(
                    f"Access to protected runtime path is not allowed: {part}"
                )

            if lower in SECRET_DIRECTORY_NAMES:
                raise ValueError(f"Access to secret directory is not allowed: {part}")

            if cls._is_secret_file_name(lower):
                raise ValueError(f"Access to secret file is not allowed: {part}")

    @staticmethod
    def _is_secret_file_name(
        name: str,
    ) -> bool:
        if name in SAFE_ENV_TEMPLATE_NAMES:
            return False

        if name == ".env" or name.startswith(".env."):
            return True

        if name in SECRET_FILE_NAMES:
            return True

        if name in PRIVATE_KEY_FILE_NAMES:
            return True

        suffix = Path(name).suffix

        return suffix in SECRET_FILE_SUFFIXES

    def secret_paths(
        self,
    ) -> tuple[Path, ...]:
        result: list[Path] = []

        for (
            directory,
            directory_names,
            file_names,
        ) in os.walk(
            self._root,
            followlinks=False,
        ):
            current = Path(directory)

            for name in list(directory_names):
                lower = name.lower()

                if lower in SECRET_DIRECTORY_NAMES:
                    result.append(current / name)

                    directory_names.remove(name)

            for name in file_names:
                lower = name.lower()

                if self._is_secret_file_name(lower):
                    result.append(current / name)

            #
            # Handle symlink aliases such as:
            #
            # config.txt -> .env
            #
            for name in [
                *directory_names,
                *file_names,
            ]:
                candidate = current / name

                if not (candidate.is_symlink()):
                    continue

                try:
                    resolved = candidate.resolve(strict=True)
                except OSError:
                    continue

                if not (resolved.is_relative_to(self._root)):
                    #
                    # Existing workspace escape
                    # should not be visible either.
                    #
                    result.append(candidate)

                    continue

                relative = resolved.relative_to(self._root)

                try:
                    self._validate_parts(relative.parts)
                except ValueError:
                    result.append(candidate)

        return tuple(dict.fromkeys(result))
