from typing import Protocol

from policy.model import (
    ApprovalRequest,
)


class ApprovalHandler(Protocol):
    def request(
        self,
        request: ApprovalRequest,
    ) -> bool: ...


MAX_ARGUMENT_PREVIEW_CHARS = 2_000


class CliApprovalHandler:
    def request(
        self,
        request: ApprovalRequest,
    ) -> bool:
        arguments = request.arguments

        if len(arguments) > MAX_ARGUMENT_PREVIEW_CHARS:
            arguments = arguments[:MAX_ARGUMENT_PREVIEW_CHARS] + "\n... [truncated]"

        print()
        print("[approval required]")
        print(f"tool={request.tool_name}")
        print(f"capability={request.capability.value}")
        print(f"reason={request.reason}")

        print("[arguments]")
        print(arguments)

        answer = input("Approve this tool call? [y/N]: ").strip().lower()

        return answer in {
            "y",
            "yes",
        }
