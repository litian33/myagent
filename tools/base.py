from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from openai.types.responses import FunctionToolParam


@dataclass(frozen=True, slots=True)
class Tool:
    schema: FunctionToolParam
    handler: Callable[..., Any]

    @property
    def name(self) -> str:
        return self.schema["name"]
