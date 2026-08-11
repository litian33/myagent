from dataclasses import dataclass, field
from enum import Enum
from typing import cast

from openai.types.responses import (
    ResponseInputItemParam,
    ResponseInputParam,
    ResponseOutputItem,
)

from agent.completion import (
    CompletionCriteria,
)
from agent.errors import AgentRunError
from agent.planning import Plan


class AgentStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MAX_STEPS_REACHED = "max_steps_reached"


@dataclass(
    frozen=True,
    slots=True,
)
class AgentRunResult:
    status: AgentStatus
    output: str | None
    error: AgentRunError | None = None


@dataclass(slots=True)
class HistoryBlock:
    items: ResponseInputParam


@dataclass(slots=True)
class CompactionState:
    summary: str
    compacted_blocks: int


@dataclass(slots=True)
class AgentState:
    task: str

    initial_input: ResponseInputParam

    plan: Plan | None = None

    completion_criteria: CompletionCriteria | None = None

    history_blocks: list[HistoryBlock] = field(default_factory=list)

    compaction: CompactionState | None = None

    step: int = 0

    status: AgentStatus = AgentStatus.CREATED

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

    def start(self) -> None:
        if self.status != AgentStatus.CREATED:
            raise RuntimeError(f"Cannot start agent from status: {self.status.value}")

        self.status = AgentStatus.RUNNING

    def complete(self) -> None:
        if self.status != AgentStatus.RUNNING:
            raise RuntimeError(
                f"Cannot complete agent from status: {self.status.value}"
            )

        self.status = AgentStatus.COMPLETED

    def reach_max_steps(self) -> None:
        if self.status != AgentStatus.RUNNING:
            raise RuntimeError(
                f"Cannot mark max steps from status: {self.status.value}"
            )

        self.status = AgentStatus.MAX_STEPS_REACHED

    def fail(self) -> None:
        if self.status != AgentStatus.RUNNING:
            raise RuntimeError(f"Cannot fail agent from status: {self.status.value}")

        self.status = AgentStatus.FAILED

    def record_step(
        self,
        model_output: list[ResponseOutputItem],
        tool_outputs: ResponseInputParam,
    ) -> None:
        items: ResponseInputParam = []

        for item in model_output:
            input_item = cast(
                ResponseInputItemParam,
                item.model_dump(exclude_unset=True),
            )

            items.append(input_item)

        items.extend(tool_outputs)

        self.history_blocks.append(
            HistoryBlock(
                items=items,
            )
        )

    @property
    def compacted_block_count(self) -> int:
        if self.compaction is None:
            return 0

        return self.compaction.compacted_blocks

    @property
    def active_history_blocks(
        self,
    ) -> list[HistoryBlock]:
        return self.history_blocks[self.compacted_block_count :]

    def blocks_for_compaction(
        self,
        count: int,
    ) -> list[HistoryBlock]:
        if count <= 0:
            raise ValueError("Compaction block count must be positive")

        start = self.compacted_block_count
        end = start + count

        if end > len(self.history_blocks):
            raise ValueError("Compaction exceeds available history blocks")

        return self.history_blocks[start:end]

    def apply_compaction(
        self,
        *,
        summary: str,
        block_count: int,
    ) -> None:
        if not summary.strip():
            raise ValueError("Compaction summary cannot be empty")

        compacted_blocks = self.compacted_block_count + block_count

        if compacted_blocks > len(self.history_blocks):
            raise ValueError("Compaction exceeds history size")

        self.compaction = CompactionState(
            summary=summary,
            compacted_blocks=compacted_blocks,
        )

    @property
    def history(self) -> ResponseInputParam:
        items: ResponseInputParam = [*self.initial_input]

        for block in self.history_blocks:
            items.extend(block.items)

        return items

    def attach_plan(
        self,
        plan: Plan,
    ) -> None:
        if self.plan is not None:
            raise RuntimeError("Agent already has a plan")

        self.plan = plan

    def attach_completion_criteria(
        self,
        criteria: CompletionCriteria,
    ) -> None:
        if self.completion_criteria is not None:
            raise RuntimeError("Agent already has completion criteria")

        self.completion_criteria = criteria
