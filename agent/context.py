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
    included_blocks: int
    dropped_blocks: int


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
        initial = [
            *state.initial_input
        ]

        selected = list(
            state.history_blocks
        )

        context = self._flatten(
            initial,
            selected,
        )

        input_tokens = self._count_tokens(
            context
        )

        minimum_blocks = (
            1
            if state.history_blocks
            else 0
        )

        while (
            input_tokens
            > self._max_input_tokens
            and len(selected) > minimum_blocks
        ):
            selected.pop(0)

            context = self._flatten(
                initial,
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
            if state.history_blocks:
                raise ContextBudgetExceeded(
                    "Initial task and most recent "
                    "history block exceed "
                    "context budget"
                )

            raise ContextBudgetExceeded(
                "Initial task exceeds "
                "context budget"
            )

        total_blocks = len(
            state.history_blocks
        )

        included_blocks = len(
            selected
        )

        return ContextSnapshot(
            input=context,
            input_tokens=input_tokens,
            max_input_tokens=(
                self._max_input_tokens
            ),
            total_blocks=total_blocks,
            included_blocks=(
                included_blocks
            ),
            dropped_blocks=(
                total_blocks
                - included_blocks
            ),
        )

    @staticmethod
    def _flatten(
        initial: ResponseInputParam,
        blocks: list[HistoryBlock],
    ) -> ResponseInputParam:
        result: ResponseInputParam = [
            *initial
        ]

        for block in blocks:
            result.extend(
                block.items
            )

        return result
