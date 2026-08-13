import json
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from openai import OpenAI
from openai.types.responses import FunctionToolParam

from agent.memory import MemoryKind
from tools.base import handle_openai_errors

MEMORY_CAPTURE_INSTRUCTIONS = """
You extract long-term memory proposals
from only the current user message.

Extract only information that is:
1. explicitly stated by the user;
2. stable beyond the current turn;
3. useful in future sessions.

Allowed kinds:
- semantic: stable project facts
- procedural: explicit future working rules

Do not infer missing facts.
Do not save the current task merely because
the user asked the agent to perform it.
Do not save temporary state, tool results,
test results, or assistant conclusions.

For every proposal, evidence must be copied
verbatim from the current user message.

If nothing is worth remembering, return an
empty proposals array.

Set route="memory_only" only when the user is
only asking the agent to remember/store a fact,
preference, or future rule.

Examples:

"Remember that this project uses pytest -q."
→ memory_only

"记住：以后这个项目统一使用 pytest -q。"
→ memory_only

"Remember that this project uses pytest -q,
then run the tests."
→ continue_agent

"记住我的偏好，然后告诉我当前目录有哪些文件。"
→ continue_agent

A memory-only request must not be interpreted
as a request to modify project files, inspect
the repository, or execute tools.
"""


MEMORY_PROPOSAL_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "submit_memory_proposals",
    "description": (
        "Classify whether the current user message "
        "is only a memory request and extract "
        "long-term memory proposals."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "route": {
                "type": "string",
                "enum": [
                    "memory_only",
                    "continue_agent",
                ],
            },
            "proposals": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "kind": {
                            "type": "string",
                            "enum": [
                                "semantic",
                                "procedural",
                            ],
                        },
                        "evidence": {
                            "type": "string",
                        },
                    },
                    "required": [
                        "kind",
                        "evidence",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "route",
            "proposals",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


class MemoryRoute(str, Enum):
    MEMORY_ONLY = "memory_only"
    CONTINUE_AGENT = "continue_agent"


@dataclass(
    frozen=True,
    slots=True,
)
class MemoryProposal:
    kind: MemoryKind
    evidence: str

    def __post_init__(self) -> None:
        if not self.evidence.strip():
            raise ValueError("Memory proposal evidence cannot be empty")


@dataclass(
    frozen=True,
    slots=True,
)
class MemoryExtractionResult:
    route: MemoryRoute
    proposals: list[MemoryProposal]


class MemoryProposalExtractor(Protocol):
    def extract(
        self,
        user_input: str,
    ) -> MemoryExtractionResult: ...


class LLMMemoryProposalExtractor:
    def __init__(
        self,
        client: OpenAI,
        model: str,
    ) -> None:
        self._client = client
        self._model = model

    def extract(
        self,
        user_input: str,
    ) -> MemoryExtractionResult:
        response = self._call_model(
            user_input=user_input,
        )

        tool_calls = [
            item
            for item in response.output
            if (item.type == "function_call" and item.name == "submit_memory_proposals")
        ]

        if len(tool_calls) != 1:
            raise ValueError(
                "Memory extractor must return exactly one proposal tool call"
            )

        arguments = json.loads(tool_calls[0].arguments)

        route = MemoryRoute(arguments["route"])

        proposals: list[MemoryProposal] = []

        for item in arguments["proposals"]:
            proposals.append(
                MemoryProposal(
                    kind=MemoryKind(item["kind"]),
                    evidence=item["evidence"],
                )
            )

        return MemoryExtractionResult(
            route=route,
            proposals=proposals,
        )

    @handle_openai_errors
    def _call_model(
        self,
        *,
        user_input: str,
    ):
        return self._client.responses.create(
            model=self._model,
            instructions=MEMORY_CAPTURE_INSTRUCTIONS,
            input=[
                {
                    "role": "user",
                    "content": user_input,
                }
            ],
            tools=[
                MEMORY_PROPOSAL_TOOL,
            ],
            # tool_choice="required",
            max_output_tokens=512,
            truncation="disabled",
            extra_body={
                "thinking": {
                    "type": "disabled",
                }
            },
        )
