from dataclasses import dataclass, field
from enum import Enum


class CompletionCriterionStatus(
    str,
    Enum,
):
    PENDING = "pending"
    SATISFIED = "satisfied"


@dataclass(slots=True)
class CompletionCriterion:
    id: str
    description: str

    status: CompletionCriterionStatus = CompletionCriterionStatus.PENDING

    evidence: str | None = None

    def satisfy(
        self,
        evidence: str,
    ) -> None:
        if self.status != CompletionCriterionStatus.PENDING:
            raise RuntimeError(
                f"Cannot satisfy completion criterion from status: {self.status.value}"
            )

        evidence = evidence.strip()

        if not evidence:
            raise ValueError("Completion evidence cannot be empty")

        self.evidence = evidence
        self.status = CompletionCriterionStatus.SATISFIED


@dataclass(slots=True)
class CompletionCriteria:
    items: list[CompletionCriterion] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        descriptions: list[str],
    ) -> "CompletionCriteria":
        if not descriptions:
            raise ValueError("Completion criteria must contain at least one item")

        items: list[CompletionCriterion] = []

        for index, description in enumerate(
            descriptions,
            start=1,
        ):
            description = description.strip()

            if not description:
                raise ValueError("Completion criterion description cannot be empty")

            items.append(
                CompletionCriterion(
                    id=f"criterion-{index}",
                    description=description,
                )
            )

        return cls(
            items=items,
        )

    def get(
        self,
        criterion_id: str,
    ) -> CompletionCriterion:
        for item in self.items:
            if item.id == criterion_id:
                return item

        raise KeyError(f"Unknown completion criterion: {criterion_id}")

    @property
    def is_satisfied(self) -> bool:
        return all(
            item.status == CompletionCriterionStatus.SATISFIED for item in self.items
        )
