import json
from dataclasses import dataclass

from openai.types.responses import ResponseInputParam

from agent.state import (
    AgentState,
    HistoryBlock,
)


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

    input_chars: int

    total_blocks: int

    included_blocks: int

    dropped_blocks: int


class ContextManager:
    def __init__(
        self,
        *,
        max_input_chars: int = 40_000,
    ) -> None:
        if max_input_chars <= 0:
            raise ValueError(
                "max_input_chars must be positive"
            )

        self._max_input_chars = (
            max_input_chars
        )

    def build(
        self,
        state: AgentState,
    ) -> ContextSnapshot:
        initial = [
            *state.initial_input
        ]

        initial_chars = (
            self._estimate_chars(
                initial
            )
        )

        if (
            initial_chars
            > self._max_input_chars
        ):
            raise ContextBudgetExceeded(
                "Initial task exceeds context budget"
            )

        selected: list[
            HistoryBlock
        ] = []

        for block in reversed(
            state.history_blocks
        ):
            candidate_blocks = [
                block,
                *selected,
            ]

            candidate = self._flatten(
                initial,
                candidate_blocks,
            )

            candidate_chars = (
                self._estimate_chars(
                    candidate
                )
            )

            if (
                candidate_chars
                <= self._max_input_chars
            ):
                selected = candidate_blocks
                continue

            if not selected:
                raise ContextBudgetExceeded(
                    "Most recent history block "
                    "exceeds context budget"
                )

            break

        context = self._flatten(
            initial,
            selected,
        )

        input_chars = self._estimate_chars(
            context
        )

        total_blocks = len(
            state.history_blocks
        )

        included_blocks = len(
            selected
        )

        return ContextSnapshot(
            input=context,
            input_chars=input_chars,
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

    @staticmethod
    def _estimate_chars(
        input_items: ResponseInputParam,
    ) -> int:
        return len(
            json.dumps(
                input_items,
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
