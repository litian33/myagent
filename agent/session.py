from dataclasses import dataclass, field

from openai.types.responses import (
    ResponseInputParam,
)


@dataclass(
    frozen=True,
    slots=True,
)
class SessionTurn:
    user_input: str
    assistant_output: str

    def __post_init__(self) -> None:
        if not self.user_input.strip():
            raise ValueError("Session user input cannot be empty")

        if not self.assistant_output.strip():
            raise ValueError("Session assistant output cannot be empty")


@dataclass(slots=True)
class AgentSession:
    turns: list[SessionTurn] = field(default_factory=list)

    def record_turn(
        self,
        *,
        user_input: str,
        assistant_output: str,
    ) -> None:
        self.turns.append(
            SessionTurn(
                user_input=user_input,
                assistant_output=(assistant_output),
            )
        )

    def project_context(
        self,
    ) -> ResponseInputParam:
        result: ResponseInputParam = []

        for turn in self.turns:
            result.append(
                {
                    "role": "user",
                    "content": turn.user_input,
                }
            )

            result.append(
                {
                    "role": "assistant",
                    "content": (turn.assistant_output),
                }
            )

        return result
