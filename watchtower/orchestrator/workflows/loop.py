"""
Loop Workflow
=============
Executes steps in a loop until condition is met.
"""

import logging
from typing import Dict, Optional, Any, Callable
from datetime import datetime

from .engine import Workflow, WorkflowResult, WorkflowStep, WorkflowStatus
from ...agents.base_agent import EnterpriseAgent

logger = logging.getLogger("Orchestrator.Loop")


class LoopWorkflow(Workflow):
    """
    Executes workflow steps in a loop.

    Continues until:
    - Condition function returns False
    - Max iterations reached
    - A step fails (if stop_on_failure=True)
    """

    def __init__(
        self,
        workflow_id: str,
        name: str = "",
        max_iterations: int = 10,
        condition: Optional[Callable[[int, Dict], bool]] = None,
        stop_on_failure: bool = True,
    ):
        super().__init__(workflow_id, name)
        self.max_iterations = max_iterations
        self.condition = condition or (lambda i, ctx: i < max_iterations)
        self.stop_on_failure = stop_on_failure
        self._iterations_completed = 0

    async def execute(
        self,
        agents: Dict[str, EnterpriseAgent],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Execute steps in a loop."""
        context = context or {}
        self.status = WorkflowStatus.RUNNING
        started_at = datetime.now()

        logger.info(f"Starting loop workflow: {self.name} (max {self.max_iterations} iterations)")

        iteration = 0
        all_results = []

        while iteration < self.max_iterations:
            # Check condition
            if not self.condition(iteration, context):
                logger.info(f"Loop condition false at iteration {iteration}")
                break

            logger.info(f"Loop iteration {iteration + 1}")

            # Execute all steps
            iteration_failed = False
            for step in self.steps:
                # Reset step status for new iteration
                step.status = WorkflowStatus.PENDING
                step.result = None

                # Find agent
                agent = self._find_agent(step, agents)
                if not agent:
                    step.status = WorkflowStatus.FAILED
                    logger.error(f"Step {step.step_id}: No agent found")
                    iteration_failed = True
                    if self.stop_on_failure:
                        break
                    continue

                # Execute
                step.status = WorkflowStatus.RUNNING
                step.started_at = datetime.now()

                try:
                    step_payload = {
                        **step.payload,
                        **context,
                        "iteration": iteration,
                    }

                    result = await agent.execute(step.action, step_payload, context)
                    step.result = result
                    step.completed_at = datetime.now()

                    if result.success:
                        step.status = WorkflowStatus.COMPLETED
                        context[f"{step.step_id}_result"] = result.result_data
                        all_results.append(result)
                    else:
                        step.status = WorkflowStatus.FAILED
                        iteration_failed = True
                        if self.stop_on_failure:
                            break

                except Exception as e:
                    step.status = WorkflowStatus.FAILED
                    iteration_failed = True
                    logger.error(f"Step {step.step_id}: Exception - {e}")
                    if self.stop_on_failure:
                        break

            if iteration_failed and self.stop_on_failure:
                self.status = WorkflowStatus.FAILED
                break

            iteration += 1
            self._iterations_completed = iteration

        # Determine final status
        if self.status == WorkflowStatus.RUNNING:
            self.status = WorkflowStatus.COMPLETED

        result = self._create_result()
        result.started_at = started_at
        result.completed_at = datetime.now()
        result.duration_seconds = (result.completed_at - started_at).total_seconds()

        # Adjust counts for loop
        result.completed_steps = sum(1 for r in all_results if r.success)
        result.total_steps = len(self.steps) * self._iterations_completed

        logger.info(f"Loop workflow {self.name}: {self.status.value} "
                   f"({self._iterations_completed} iterations)")

        return result

    def _find_agent(
        self,
        step: WorkflowStep,
        agents: Dict[str, EnterpriseAgent],
    ) -> Optional[EnterpriseAgent]:
        """Find an agent for a step."""
        if step.agent_type:
            for agent in agents.values():
                if agent.config.agent_type == step.agent_type:
                    return agent

        for agent in agents.values():
            cap = agent._action_to_capability(step.action)
            if cap and cap in agent.capabilities:
                return agent

        return None

    @property
    def iterations_completed(self) -> int:
        """Get number of completed iterations."""
        return self._iterations_completed
