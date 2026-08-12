import json
from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI
from openai.types.responses import FunctionToolParam, ResponseFunctionToolCall

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
"""


MEMORY_PROPOSAL_TOOL: FunctionToolParam = {
    "type": "function",
    "name": "submit_memory_proposals",
    "description": (
        "Extract explicit, stable, reusable "
        "long-term information from the current "
        "user message. Return an empty proposals "
        "array when nothing should be remembered."
    ),
    "parameters": {
        "type": "object",
        "properties": {
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
                            "description": (
                                "Exact text copied from the current user input."
                            ),
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
            "proposals",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


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


class MemoryProposalExtractor(Protocol):
    def extract(
        self,
        user_input: str,
    ) -> list[MemoryProposal]: ...


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
    ) -> list[MemoryProposal]:
        response = self._call_model(user_input=user_input)
        print(f"llm result {response}")
        tool_calls: list[ResponseFunctionToolCall] = [
            item for item in response.output if item.type == "function_call"
        ]

        proposals: list[MemoryProposal] = []
        for tool_call in tool_calls:
            print(f"process tool call {tool_call}")
            arguments = json.loads(tool_call.arguments)
            proposal = MemoryProposal(kind=arguments.kind, evidence=arguments.evidence)
            proposals.append(proposal)
        return proposals

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
            tool_choice="required",
            max_output_tokens=512,
            truncation="disabled",
        )
