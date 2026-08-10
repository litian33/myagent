from dataclasses import dataclass
from enum import Enum


class AgentErrorKind(str, Enum):
    MODEL = "model"
    CONTEXT = "context"
    RUNTIME = "runtime"


@dataclass(
    frozen=True,
    slots=True,
)
class AgentRunError:
    kind: AgentErrorKind
    message: str
    retryable: bool


class AgentExecutionError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        kind: AgentErrorKind,
        retryable: bool = False,
    ) -> None:
        super().__init__(message)

        self.kind = kind
        self.retryable = retryable


class ModelInvocationError(AgentExecutionError):
    def __init__(
        self,
        message: str,
        *,
        retryable: bool,
    ) -> None:
        super().__init__(
            message,
            kind=AgentErrorKind.MODEL,
            retryable=retryable,
        )


class ContextExecutionError(AgentExecutionError):
    def __init__(
        self,
        message: str,
    ) -> None:
        super().__init__(
            message,
            kind=AgentErrorKind.CONTEXT,
            retryable=False,
        )
