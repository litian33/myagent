import hashlib
import re
from typing import TypedDict

from policy.model import (
    ToolCapability,
)
from tools.base import Tool, tool
from tools.workspace import Workspace

MAX_READ_FILE_BYTES = 1_000_000
MAX_SEARCH_RESULTS = 20
MAX_SEARCH_FILE_BYTES = 1_000_000


class FileContent(TypedDict):
    path: str
    content: str
    sha256: str


class SearchMatch(TypedDict):
    path: str
    line: int
    text: str


def create_filesystem_tools(
    *,
    workspace: Workspace,
) -> tuple[Tool, ...]:

    @tool(
        description=(
            "List accessible files and directories inside the current workspace."
        ),
        capability=ToolCapability.READ,
    )
    def list_files(
        path: str,
    ) -> list[str]:
        directory = workspace.resolve_directory(path)

        result: list[str] = []

        for item in directory.iterdir():
            relative = workspace.relative_path(item)

            try:
                workspace.resolve_existing(relative)
            except (
                ValueError,
                OSError,
            ):
                #
                # Protected / secret / escaped
                # resources are not exposed.
                #
                continue

            result.append(item.name)

        return sorted(result)

    @tool(
        description=(
            "Read an accessible UTF-8 text file "
            "inside the current workspace and "
            "return its SHA-256 version identifier. "
            "Protected and secret files cannot be read."
        ),
        capability=ToolCapability.READ,
    )
    def read_file(
        path: str,
    ) -> FileContent:
        file_path = workspace.resolve_file(path)

        size = file_path.stat().st_size

        if size > MAX_READ_FILE_BYTES:
            raise ValueError(
                "File is too large to read: "
                f"{size} bytes; maximum is "
                f"{MAX_READ_FILE_BYTES} bytes"
            )

        data = file_path.read_bytes()

        workspace.validate_read_content(data)

        try:
            content = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("read_file only supports UTF-8 text files") from exc

        return {
            "path": (workspace.relative_path(file_path)),
            "content": content,
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    @tool(
        description=(
            "Search accessible UTF-8 text files "
            "inside the current workspace for a "
            "regular expression pattern. "
            "Protected and secret files are excluded."
        ),
        capability=ToolCapability.READ,
    )
    def grep(
        pattern: str,
        path: str,
    ) -> list[SearchMatch]:
        root = workspace.resolve_existing(path)

        try:
            regex = re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"Invalid regular expression: {exc}") from exc

        matches: list[SearchMatch] = []

        if root.is_file():
            candidates = [root]
            explicit_file = True
        else:
            candidates = root.rglob("*")
            explicit_file = False

        for candidate in candidates:
            if len(matches) >= MAX_SEARCH_RESULTS:
                break

            if not candidate.is_file():
                continue

            try:
                relative = workspace.relative_path(candidate)

                file_path = workspace.resolve_file(relative)

                if file_path.stat().st_size > MAX_SEARCH_FILE_BYTES:
                    continue

                data = file_path.read_bytes()

                workspace.validate_read_content(data)

                content = data.decode("utf-8")

            except (
                OSError,
                UnicodeError,
                ValueError,
            ):
                if explicit_file:
                    raise

                continue

            for (
                line_number,
                line,
            ) in enumerate(
                content.splitlines(),
                start=1,
            ):
                if regex.search(line):
                    matches.append(
                        {
                            "path": (workspace.relative_path(file_path)),
                            "line": (line_number),
                            "text": line,
                        }
                    )

                    if len(matches) >= MAX_SEARCH_RESULTS:
                        break

        return matches

    return (
        list_files,
        read_file,
        grep,
    )
