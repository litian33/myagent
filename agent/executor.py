from agent.planning import (
    Plan,
    PlanStep,
    PlanStepStatus,
)
from agent.progress import (
    ProgressStatus,
    ProgressUpdate,
)
from agent.state import AgentState


class PlanExecutor:
    def start_next_step(
        self,
        state: AgentState,
    ) -> PlanStep:
        plan = self._require_plan(state)

        if plan.current_step is not None:
            raise RuntimeError("Plan already has an in-progress step")

        if any(step.status == PlanStepStatus.FAILED for step in plan.steps):
            raise RuntimeError("Cannot continue a plan with a failed step")

        pending = plan.pending_steps

        if not pending:
            raise RuntimeError("Plan has no pending steps")

        step = pending[0]

        step.start()

        return step

    def complete_current_step(
        self,
        state: AgentState,
        result: str,
    ) -> PlanStep:
        plan = self._require_plan(state)

        step = plan.current_step

        if step is None:
            raise RuntimeError("Plan has no in-progress step")

        step.complete(result)

        return step

    def fail_current_step(
        self,
        state: AgentState,
        result: str,
    ) -> PlanStep:
        plan = self._require_plan(state)

        step = plan.current_step

        if step is None:
            raise RuntimeError("Plan has no in-progress step")

        step.fail(result)

        return step

    @staticmethod
    def _require_plan(
        state: AgentState,
    ) -> Plan:
        if state.plan is None:
            raise RuntimeError("Agent has no plan")

        return state.plan

    def apply_progress(
        self,
        state: AgentState,
        update: ProgressUpdate,
    ) -> PlanStep:
        plan = self._require_plan(state)

        step = plan.current_step

        if step is None:
            raise RuntimeError("Plan has no in-progress step")

        if update.step_id != step.id:
            raise RuntimeError("Progress update does not match the current plan step")

        if update.status == ProgressStatus.CONTINUE:
            return step

        if update.status == ProgressStatus.COMPLETED:
            return self.complete_current_step(
                state,
                result=update.summary,
            )

        if update.status == ProgressStatus.FAILED:
            return self.fail_current_step(
                state,
                result=update.summary,
            )

        raise AssertionError(f"Unsupported progress status: {update.status}")

    def replan(
        self,
        state: AgentState,
        descriptions: list[str],
    ) -> list[PlanStep]:
        plan = self._require_plan(state)

        return plan.replan(descriptions)
