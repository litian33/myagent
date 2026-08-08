from dataclasses import dataclass, field
from typing import cast

from openai.types.responses import (
    ResponseInputItemParam,
    ResponseInputParam,
    ResponseOutputItem,
)


@dataclass(slots=True)
class HistoryBlock:
    items: ResponseInputParam


@dataclass(slots=True)
class AgentState:
    task: str

    initial_input: ResponseInputParam

    history_blocks: list[HistoryBlock] = field(
        default_factory=list
    )

    step: int = 0

    @classmethod
    def create(
        cls,
        task: str,
    ) -> "AgentState":
        initial_input: ResponseInputParam = [
            {
                "role": "user",
                "content": task,
            }
        ]

        return cls(
            task=task,
            initial_input=initial_input,
        )

    def record_step(
        self,
        model_output: list[ResponseOutputItem],
        tool_outputs: ResponseInputParam,
    ) -> None:
        items: ResponseInputParam = []

        for item in model_output:
            input_item = cast(
                ResponseInputItemParam,
                item.model_dump(
                    exclude_unset=True
                ),
            )

            items.append(input_item)

        items.extend(tool_outputs)

        self.history_blocks.append(
            HistoryBlock(
                items=items,
            )
        )

    @property
    def history(self) -> ResponseInputParam:
        items: ResponseInputParam = [
            *self.initial_input
        ]

        for block in self.history_blocks:
            items.extend(block.items)

        return items

    @property
    def history_size(self) -> int:
        return len(self.history)
