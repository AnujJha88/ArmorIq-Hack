"""
Sequential Workflow
===================
Executes steps in sequence, one after another.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime

from .engine import Workflow, WorkflowResult, WorkflowStep, WorkflowStatus
from ...agents.base_agent import EnterpriseAgent

logger = logging.getLogger("Orchestrator.Sequential")


class SequentialWorkflow(Workflow):
    """
    Executes workflow steps in sequence.

    Each step must complete before the next begins.
    Failure in any step can optionally halt the workflow.
    """

    def __init__(
        self,
        workflow_id: str,
        name: str = "",
        stop_on_failure: bool = True,
        stop_on_block: bool = False,
    ):
        super().__init__(workflow_id, name)
        self.stop_on_failure = stop_on_failure
        self.stop_on_block = stop_on_block

    async def execute(
        self,
        agents: Dict[str, EnterpriseAgent],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Execute steps sequentially."""
        context = context or {}
        self.status = WorkflowStatus.RUNNING
        started_at = datetime.now()

        logger.info(f"Starting sequential workflow: {self.name} ({len(self.steps)} steps)")

        for step in self.steps:
            # Find agent for step
            agent = self._find_agent(step, agents)

            if not agent:
                step.status = WorkflowStatus.FAILED
                step.result = None
                logger.error(f"Step {step.step_id}: No agent found for {step.action}")

                if self.stop_on_failure:
                    self.status = WorkflowStatus.FAILED
                    break
                continue

            # Execute step
            step.status = WorkflowStatus.RUNNING
            step.started_at = datetime.now()

            try:
                # Merge context with step payload
                step_payload = {**step.payload, **context}

                result = await agent.execute(step.action, step_payload, context)
                step.result = result
                step.completed_at = datetime.now()

                if result.success:
                    step.status = WorkflowStatus.COMPLETED
                    logger.info(f"Step {step.step_id}: COMPLETED (risk: {result.risk_score:.2f})")

                    # Add result to context for next step
                    context[f"{step.step_id}_result"] = result.result_data

                elif not result.compliance_passed:
                    step.status = WorkflowStatus.BLOCKED
                    logger.warning(f"Step {step.step_id}: BLOCKED by compliance")

                    if self.stop_on_block:
                        self.status = WorkflowStatus.BLOCKED
                        break

                else:
                    step.status = WorkflowStatus.FAILED
                    logger.error(f"Step {step.step_id}: FAILED")

                    if self.stop_on_failure:
                        self.status = WorkflowStatus.FAILED
                        break

            except Exception as e:
                step.status = WorkflowStatus.FAILED
                step.completed_at = datetime.now()
                logger.error(f"Step {step.step_id}: Exception - {e}")

                if self.stop_on_failure:
                    self.status = WorkflowStatus.FAILED
                    break

        # Determine final status
        if self.status == WorkflowStatus.RUNNING:
            all_completed = all(s.status == WorkflowStatus.COMPLETED for s in self.steps)
            any_blocked = any(s.status == WorkflowStatus.BLOCKED for s in self.steps)

            if all_completed:
                self.status = WorkflowStatus.COMPLETED
            elif any_blocked:
                self.status = WorkflowStatus.BLOCKED
            else:
                self.status = WorkflowStatus.FAILED

        result = self._create_result()
        result.started_at = started_at
        result.completed_at = datetime.now()
        result.duration_seconds = (result.completed_at - started_at).total_seconds()

        logger.info(f"Workflow {self.name}: {self.status.value} "
                   f"({result.completed_steps}/{result.total_steps} completed)")

        return result

    def _find_agent(
        self,
        step: WorkflowStep,
        agents: Dict[str, EnterpriseAgent],
    ) -> Optional[EnterpriseAgent]:
        """Find an agent for a step."""
        # If agent type specified, find matching agent
        if step.agent_type:
            for agent in agents.values():
                if agent.config.agent_type == step.agent_type:
                    return agent

        # Otherwise, find agent with matching capability
        for agent in agents.values():
            cap = agent._action_to_capability(step.action)
            if cap and cap in agent.capabilities:
                return agent

        return None
