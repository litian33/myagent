import hashlib
import re
from pathlib import Path
from typing import TypedDict

from tools.base import Tool, tool

MAX_SEARCH_RESULTS = 20
MAX_SEARCH_FILE_BYTES = 1_000_000

SEARCH_EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
}


class FileContent(TypedDict):
    path: str
    content: str
    sha256: str


class SearchMatch(TypedDict):
    path: str
    line: int
    text: str


@tool(description=("List files and directories in a given directory."))
def list_files(path: str) -> list[str]:
    directory = Path(path)

    return [item.name for item in directory.iterdir()]


@tool(
    description=(
        "Read the text content of a file and return its "
        "SHA-256 version identifier. When modifying an "
        "existing file, pass this sha256 value to write_file "
        "as expected_sha256. Never invent the hash."
    )
)
def read_file(
    path: str,
) -> FileContent:
    file_path = Path(path)

    data = file_path.read_bytes()

    content = data.decode(
        "utf-8",
    )

    return {
        "path": str(file_path),
        "content": content,
        "sha256": hashlib.sha256(data).hexdigest(),
    }


@tool(
    description=(
        "Search text files for a regular expression pattern. "
        "Use this to locate code, symbols, configuration, or "
        "text without reading every file."
    )
)
def grep(
    pattern: str,
    path: str,
) -> list[SearchMatch]:
    root = Path(path)

    try:
        regex = re.compile(pattern)
    except re.error as exc:
        raise ValueError(f"Invalid regular expression: {exc}") from exc

    matches: list[SearchMatch] = []

    if root.is_file():
        candidates = [root]
    else:
        candidates = root.rglob("*")

    for file_path in candidates:
        if len(matches) >= MAX_SEARCH_RESULTS:
            break

        if not file_path.is_file():
            continue

        if any(part in SEARCH_EXCLUDED_DIRS for part in file_path.parts):
            continue

        try:
            if file_path.stat().st_size > MAX_SEARCH_FILE_BYTES:
                continue

            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                for line_number, line in enumerate(
                    file,
                    start=1,
                ):
                    if regex.search(line):
                        matches.append(
                            {
                                "path": str(file_path),
                                "line": line_number,
                                "text": line.rstrip(),
                            }
                        )

                        if len(matches) >= MAX_SEARCH_RESULTS:
                            break

        except (
            OSError,
            UnicodeError,
        ):
            continue

    return matches


FILESYSTEM_TOOLS: tuple[Tool, ...] = (
    list_files,
    read_file,
    grep,
)
