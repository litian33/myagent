from dataclasses import dataclass, field
from enum import Enum


class PlanStepStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SUPERSEDED = "superseded"


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

        result = result.strip()

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

        result = result.strip()

        if not result:
            raise ValueError("Failed plan step must have a result")

        self.result = result
        self.status = PlanStepStatus.FAILED

    def supersede(self) -> None:
        if self.status not in {
            PlanStepStatus.PENDING,
            PlanStepStatus.FAILED,
        }:
            raise RuntimeError(
                f"Cannot supersede plan step from status: {self.status.value}"
            )

        self.status = PlanStepStatus.SUPERSEDED


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
        terminal_success_states = {
            PlanStepStatus.COMPLETED,
            PlanStepStatus.SUPERSEDED,
        }

        return all(step.status in terminal_success_states for step in self.steps)

    def replan(
        self,
        descriptions: list[str],
    ) -> list[PlanStep]:
        if self.current_step is not None:
            raise RuntimeError("Cannot replan while a plan step is in progress")

        if not any(step.status == PlanStepStatus.FAILED for step in self.steps):
            raise RuntimeError("Replan requires a failed step")

        normalized: list[str] = []

        for description in descriptions:
            description = description.strip()

            if not description:
                raise ValueError("Replan step description cannot be empty")

            normalized.append(description)

        if not normalized:
            raise ValueError("Replan must contain at least one step")

        for step in self.steps:
            if step.status in {
                PlanStepStatus.FAILED,
                PlanStepStatus.PENDING,
            }:
                step.supersede()

        start = len(self.steps) + 1

        new_steps = [
            PlanStep(
                id=f"step-{index}",
                description=description,
            )
            for index, description in enumerate(
                normalized,
                start=start,
            )
        ]

        self.steps.extend(new_steps)

        return new_steps
