from dataclasses import dataclass, field
from typing import cast

from openai.types.responses import (
    ResponseInputItemParam,
    ResponseInputParam,
    ResponseOutputItem,
)


@dataclass(slots=True)
class AgentState:
    task: str
    history: ResponseInputParam = field(
        default_factory=list
    )
    step: int = 0

    @classmethod
    def create(
        cls,
        task: str,
    ) -> "AgentState":
        history: ResponseInputParam = [
            {
                "role": "user",
                "content": task,
            }
        ]

        return cls(
            task=task,
            history=history,
        )

    def append_model_output(
        self,
        output: list[ResponseOutputItem],
    ) -> None:
        for item in output:
            input_item = cast(
                ResponseInputItemParam,
                item.model_dump(
                    exclude_unset=True
                ),
            )

            self.history.append(
                input_item
            )

    @property
    def history_size(self) -> int:
        return len(self.history)
