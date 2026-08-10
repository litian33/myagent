# import shutil
# import sys

# import pytest

# from execution.bubblewrap import (
#     BubblewrapCommandExecutor,
#     BubblewrapConfig,
# )
# from execution.command import CommandRequest
# from tools.workspace import Workspace


# def _bwrap_available() -> bool:
#     if not sys.platform.startswith("linux"):
#         return False

#     return shutil.which("bwrap") is not None


# pytestmark = pytest.mark.skipif(
#     not _bwrap_available(),
#     reason="bubblewrap is only available on Linux with bwrap installed",
# )


# def test_host_file_is_not_visible(
#     tmp_path,
# ) -> None:
#     workspace_root = (
#         tmp_path / "workspace"
#     )

#     workspace_root.mkdir()

#     outside = (
#         tmp_path / "secret.txt"
#     )

#     outside.write_text(
#         "host-secret"
#     )

#     workspace = Workspace(
#         workspace_root
#     )

#     executor = (
#         BubblewrapCommandExecutor(
#             workspace=workspace,
#             config=(
#                 BubblewrapConfig()
#             ),
#         )
#     )

#     result = executor.execute(
#         CommandRequest(
#             argv=(
#                 "/usr/bin/python3",
#                 "-c",
#                 (
#                     "from pathlib import Path;"
#                     f"print(Path("
#                     f"{str(outside)!r}"
#                     ").read_text())"
#                 ),
#             ),
#             cwd=workspace_root,
#             timeout_seconds=10,
#         )
#     )

#     assert (
#         result.exit_code
#         != 0
#     )

#     assert (
#         "host-secret"
#         not in result.stdout
#     )

# def test_workspace_is_writable(
#     tmp_path,
# ) -> None:
#     workspace = Workspace(
#         tmp_path
#     )

#     executor = (
#         BubblewrapCommandExecutor(
#             workspace=workspace,
#             config=(
#                 BubblewrapConfig()
#             ),
#         )
#     )

#     result = executor.execute(
#         CommandRequest(
#             argv=(
#                 "/usr/bin/python3",
#                 "-c",
#                 (
#                     "from pathlib import Path;"
#                     "Path('generated.txt')"
#                     ".write_text('hello')"
#                 ),
#             ),
#             cwd=tmp_path,
#             timeout_seconds=10,
#         )
#     )

#     assert (
#         result.exit_code
#         == 0
#     )

#     assert (
#         tmp_path
#         / "generated.txt"
#     ).read_text() == "hello"


# def test_git_config_is_hidden(
#     tmp_path,
# ) -> None:
#     workspace_root = (
#         tmp_path / "workspace"
#     )

#     workspace_root.mkdir()

#     git_dir = (
#         workspace_root / ".git"
#     )

#     git_dir.mkdir()

#     (
#         git_dir / "config"
#     ).write_text(
#         "https://user:token@example.com/repo.git"
#     )

#     workspace = Workspace(
#         workspace_root
#     )

#     executor = (
#         BubblewrapCommandExecutor(
#             workspace=workspace,
#             config=(
#                 BubblewrapConfig()
#             ),
#         )
#     )

#     result = executor.execute(
#         CommandRequest(
#             argv=(
#                 "/usr/bin/python3",
#                 "-c",
#                 (
#                     "from pathlib import Path;"
#                     "print(Path('.git/config')"
#                     ".read_text())"
#                 ),
#             ),
#             cwd=workspace_root,
#             timeout_seconds=10,
#         )
#     )

#     assert (
#         result.exit_code
#         == 0
#     )

#     assert (
#         "token"
#         not in result.stdout
#     )


# def test_verify(
#     tmp_path,
# ) -> None:
#     executor = (
#         BubblewrapCommandExecutor(
#             workspace=Workspace(
#                 tmp_path
#             ),
#             config=(
#                 BubblewrapConfig()
#             ),
#         )
#     )

#     #
#     # Should not raise when the sandbox is usable.
#     #
#     executor.verify()
