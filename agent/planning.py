from dataclasses import dataclass, field
from enum import Enum


class PlanStepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class PlanStep:
    id: str
    description: str

    status: PlanStepStatus = PlanStepStatus.PENDING

    result: str | None = None

    def start(self) -> None:
        if self.status != PlanStepStatus.PENDING:
            raise RuntimeError(
                f"Cannot start plan step from status: {self.status.value}"
            )

        self.status = PlanStepStatus.IN_PROGRESS

    def complete(
        self,
        result: str,
    ) -> None:
        if self.status != PlanStepStatus.IN_PROGRESS:
            raise RuntimeError(
                f"Cannot complete plan step from status: {self.status.value}"
            )

        if not result:
            raise ValueError("Completed plan step must have a result")

        self.result = result
        self.status = PlanStepStatus.COMPLETED

    def fail(
        self,
        result: str,
    ) -> None:
        if self.status != PlanStepStatus.IN_PROGRESS:
            raise RuntimeError(
                f"Cannot fail plan step from status: {self.status.value}"
            )

        if not result:
            raise ValueError("Completed plan step must have a result")

        self.result = result
        self.status = PlanStepStatus.FAILED


@dataclass(slots=True)
class Plan:
    steps: list[PlanStep] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        descriptions: list[str],
    ) -> "Plan":
        if not descriptions:
            raise ValueError("Plan must contain at least one step")

        steps: list[PlanStep] = []

        for index, description in enumerate(
            descriptions,
            start=1,
        ):
            description = description.strip()

            if not description:
                raise ValueError("Plan step description cannot be empty")

            steps.append(
                PlanStep(
                    id=f"step-{index}",
                    description=description,
                )
            )

        return cls(
            steps=steps,
        )

    @property
    def current_step(
        self,
    ) -> PlanStep | None:
        current = [
            step for step in self.steps if (step.status == PlanStepStatus.IN_PROGRESS)
        ]

        if len(current) > 1:
            raise RuntimeError("Plan cannot have multiple in-progress steps")

        if not current:
            return None

        return current[0]

    @property
    def pending_steps(
        self,
    ) -> list[PlanStep]:
        return [step for step in self.steps if (step.status == PlanStepStatus.PENDING)]

    @property
    def is_completed(self) -> bool:
        return all(step.status == PlanStepStatus.COMPLETED for step in self.steps)
