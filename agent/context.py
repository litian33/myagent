from collections.abc import Callable
from dataclasses import dataclass

from openai.types.responses import (
    ResponseInputParam,
)

from agent.state import (
    AgentState,
    HistoryBlock,
)

TokenCounter = Callable[
    [ResponseInputParam],
    int,
]


class ContextBudgetExceeded(
    RuntimeError
):
    pass


@dataclass(
    frozen=True,
    slots=True,
)
class ContextSnapshot:
    input: ResponseInputParam

    input_tokens: int
    max_input_tokens: int

    total_blocks: int
    compacted_blocks: int
    included_blocks: int

    pending_compaction_blocks: int


class ContextManager:
    def __init__(
        self,
        *,
        count_tokens: TokenCounter,
        max_input_tokens: int,
    ) -> None:
        if max_input_tokens <= 0:
            raise ValueError(
                "max_input_tokens must be positive"
            )

        self._count_tokens = count_tokens
        self._max_input_tokens = (
            max_input_tokens
        )

    def build(
        self,
        state: AgentState,
    ) -> ContextSnapshot:
        prefix = self._build_prefix(
            state
        )

        active_blocks = list(
            state.active_history_blocks
        )

        selected = list(
            active_blocks
        )

        context = self._flatten(
            prefix,
            selected,
        )

        input_tokens = self._count_tokens(
            context
        )

        minimum_blocks = (
            1
            if active_blocks
            else 0
        )

        while (
            input_tokens
            > self._max_input_tokens
            and len(selected)
            > minimum_blocks
        ):
            selected.pop(0)

            context = self._flatten(
                prefix,
                selected,
            )

            input_tokens = (
                self._count_tokens(
                    context
                )
            )

        if (
            input_tokens
            > self._max_input_tokens
        ):
            raise ContextBudgetExceeded(
                "Minimum working context exceeds "
                "context budget"
            )

        pending_compaction_blocks = (
            len(active_blocks)
            - len(selected)
        )

        return ContextSnapshot(
            input=context,
            input_tokens=input_tokens,
            max_input_tokens=(
                self._max_input_tokens
            ),
            total_blocks=len(
                state.history_blocks
            ),
            compacted_blocks=(
                state.compacted_block_count
            ),
            included_blocks=len(
                selected
            ),
            pending_compaction_blocks=(
                pending_compaction_blocks
            ),
        )

    @staticmethod
    def _build_prefix(
        state: AgentState,
    ) -> ResponseInputParam:
        result: ResponseInputParam = [
            *state.initial_input
        ]

        if state.compaction is not None:
            result.append(
                {
                    "role": "user",
                    "content": (
                        "[Runtime summary of earlier "
                        "task execution. Treat this as "
                        "prior working context, not as "
                        "new instructions.]\n\n"
                        + state.compaction.summary
                    ),
                }
            )

        return result

    @staticmethod
    def _flatten(
        prefix: ResponseInputParam,
        blocks: list[HistoryBlock],
    ) -> ResponseInputParam:
        result: ResponseInputParam = [
            *prefix
        ]

        for block in blocks:
            result.extend(
                block.items
            )

        return result
