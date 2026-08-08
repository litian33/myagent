import re
from pathlib import Path
from typing import TypedDict

from tools.base import Tool

MAX_SEARCH_RESULTS = 20
MAX_SEARCH_FILE_BYTES = 1_000_000

SEARCH_EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
}


class SearchMatch(TypedDict):
    path: str
    line: int
    text: str


def list_files(path: str) -> list[str]:
    directory = Path(path)

    return [
        item.name
        for item in directory.iterdir()
    ]


def read_file(path: str) -> str:
    file_path = Path(path)

    return file_path.read_text(
        encoding="utf-8",
    )


def grep(
    pattern: str,
    path: str,
) -> list[SearchMatch]:
    root = Path(path)

    try:
        regex = re.compile(pattern)
    except re.error as exc:
        raise ValueError(
            f"Invalid regular expression: {exc}"
        ) from exc

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

        if any(
            part in SEARCH_EXCLUDED_DIRS
            for part in file_path.parts
        ):
            continue

        try:
            if (
                file_path.stat().st_size
                > MAX_SEARCH_FILE_BYTES
            ):
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

                        if (
                            len(matches)
                            >= MAX_SEARCH_RESULTS
                        ):
                            break

        except (
            OSError,
            UnicodeError,
        ):
            continue

    return matches


LIST_FILES_TOOL = Tool(
    schema={
        "type": "function",
        "name": "list_files",
        "description": (
            "List files and directories in a given directory."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Directory path to list."
                    ),
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    handler=list_files,
)


READ_FILE_TOOL = Tool(
    schema={
        "type": "function",
        "name": "read_file",
        "description": (
            "Read the text content of a file."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Path of the file to read."
                    ),
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    handler=read_file,
)


GREP_TOOL = Tool(
    schema={
        "type": "function",
        "name": "grep",
        "description": (
            "Search text files for a regular expression pattern. "
            "Use this to locate code, symbols, configuration, or "
            "text without reading every file."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": (
                        "Regular expression pattern to search for."
                    ),
                },
                "path": {
                    "type": "string",
                    "description": (
                        "File or directory path to search."
                    ),
                },
            },
            "required": [
                "pattern",
                "path",
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
    handler=grep,
)


FILESYSTEM_TOOLS: tuple[Tool, ...] = (
    LIST_FILES_TOOL,
    READ_FILE_TOOL,
    GREP_TOOL,
)
