from dataclasses import dataclass
from enum import Enum


class ProgressStatus(
    str,
    Enum,
):
    CONTINUE = "continue"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(
    frozen=True,
    slots=True,
)
class ProgressUpdate:
    step_id: str
    status: ProgressStatus
    summary: str

    def __post_init__(self) -> None:
        if not self.step_id.strip():
            raise ValueError("Progress step id cannot be empty")

        if not self.summary.strip():
            raise ValueError("Progress summary cannot be empty")
