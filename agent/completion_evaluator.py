from agent.completion import (
    CompletionCriteria,
    CompletionCriterion,
)
from agent.state import AgentState


class CompletionEvaluator:
    def satisfy(
        self,
        state: AgentState,
        *,
        criterion_id: str,
        evidence: str,
    ) -> CompletionCriterion:
        criteria = self._require_criteria(state)

        criterion = criteria.get(criterion_id)

        criterion.satisfy(evidence)

        return criterion

    def can_complete(
        self,
        state: AgentState,
    ) -> bool:
        if state.plan is None:
            return False

        if state.completion_criteria is None:
            return False

        return state.plan.is_completed and state.completion_criteria.is_satisfied

    @staticmethod
    def _require_criteria(
        state: AgentState,
    ) -> CompletionCriteria:
        if state.completion_criteria is None:
            raise RuntimeError("Agent has no completion criteria")

        return state.completion_criteria
