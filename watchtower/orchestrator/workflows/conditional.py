"""
Conditional Workflow
====================
Executes steps based on conditions.
"""

import logging
from typing import Dict, Optional, Any, Callable
from datetime import datetime

from .engine import Workflow, WorkflowResult, WorkflowStep, WorkflowStatus
from ...agents.base_agent import EnterpriseAgent

logger = logging.getLogger("Orchestrator.Conditional")


class ConditionalWorkflow(Workflow):
    """
    Executes workflow steps based on conditions.

    Supports:
    - If/else branching
    - Switch-case like routing
    - Condition evaluation on context
    """

    def __init__(
        self,
        workflow_id: str,
        name: str = "",
    ):
        super().__init__(workflow_id, name)
        self.conditions: Dict[str, Callable[[Dict], bool]] = {}
        self.branches: Dict[str, list] = {"default": []}
        self._current_branch = "default"

    def add_branch(
        self,
        branch_name: str,
        condition: Callable[[Dict], bool],
    ):
        """
        Add a conditional branch.

        Args:
            branch_name: Name of the branch
            condition: Function that takes context and returns bool
        """
        self.conditions[branch_name] = condition
        self.branches[branch_name] = []

    def add_step_to_branch(
        self,
        branch_name: str,
        action: str,
        payload: Optional[Dict] = None,
        agent_type: Optional[str] = None,
    ):
        """Add a step to a specific branch."""
        if branch_name not in self.branches:
            self.branches[branch_name] = []

        step_id = f"{self.workflow_id}_B{branch_name}_{len(self.branches[branch_name]) + 1}"
        step = WorkflowStep(
            step_id=step_id,
            action=action,
            payload=payload or {},
            agent_type=agent_type,
        )
        self.branches[branch_name].append(step)

    def add_step(
        self,
        action: str,
        payload: Optional[Dict] = None,
        agent_type: Optional[str] = None,
        depends_on: Optional[list] = None,
    ):
        """Add a step to the current/default branch."""
        step_id = f"{self.workflow_id}_S{len(self.steps) + 1}"
        step = WorkflowStep(
            step_id=step_id,
            action=action,
            payload=payload or {},
            agent_type=agent_type,
            depends_on=depends_on or [],
        )
        self.steps.append(step)
        self.branches["default"].append(step)

    async def execute(
        self,
        agents: Dict[str, EnterpriseAgent],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Execute workflow, choosing branch based on conditions."""
        context = context or {}
        self.status = WorkflowStatus.RUNNING
        started_at = datetime.now()

        logger.info(f"Starting conditional workflow: {self.name}")

        # Determine which branch to execute
        selected_branch = "default"
        for branch_name, condition in self.conditions.items():
            try:
                if condition(context):
                    selected_branch = branch_name
                    break
            except Exception as e:
                logger.warning(f"Condition {branch_name} failed: {e}")

        logger.info(f"Selected branch: {selected_branch}")

        # Get steps for selected branch
        steps_to_execute = self.branches.get(selected_branch, [])

        if not steps_to_execute:
            logger.warning(f"No steps in branch {selected_branch}, using default")
            steps_to_execute = self.branches.get("default", [])

        # Execute steps
        for step in steps_to_execute:
            agent = self._find_agent(step, agents)

            if not agent:
                step.status = WorkflowStatus.FAILED
                logger.error(f"Step {step.step_id}: No agent found")
                self.status = WorkflowStatus.FAILED
                break

            step.status = WorkflowStatus.RUNNING
            step.started_at = datetime.now()

            try:
                step_payload = {**step.payload, **context}
                result = await agent.execute(step.action, step_payload, context)
                step.result = result
                step.completed_at = datetime.now()

                if result.success:
                    step.status = WorkflowStatus.COMPLETED
                    context[f"{step.step_id}_result"] = result.result_data
                else:
                    step.status = WorkflowStatus.FAILED
                    self.status = WorkflowStatus.FAILED
                    break

            except Exception as e:
                step.status = WorkflowStatus.FAILED
                step.completed_at = datetime.now()
                logger.error(f"Step {step.step_id}: {e}")
                self.status = WorkflowStatus.FAILED
                break

        # Determine final status
        if self.status == WorkflowStatus.RUNNING:
            executed = [s for s in steps_to_execute if s.status != WorkflowStatus.PENDING]
            all_completed = all(s.status == WorkflowStatus.COMPLETED for s in executed)
            self.status = WorkflowStatus.COMPLETED if all_completed else WorkflowStatus.FAILED

        # Update self.steps with executed branch for result
        self.steps = steps_to_execute

        result = self._create_result()
        result.started_at = started_at
        result.completed_at = datetime.now()
        result.duration_seconds = (result.completed_at - started_at).total_seconds()
        result.step_results["selected_branch"] = selected_branch

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
