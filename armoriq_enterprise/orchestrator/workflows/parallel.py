"""
Parallel Workflow
=================
Executes steps in parallel.
"""

import logging
import asyncio
from typing import Dict, Optional, Any, List
from datetime import datetime

from .engine import Workflow, WorkflowResult, WorkflowStep, WorkflowStatus
from ...agents.base_agent import EnterpriseAgent

logger = logging.getLogger("Orchestrator.Parallel")


class ParallelWorkflow(Workflow):
    """
    Executes workflow steps in parallel.

    All steps without dependencies execute concurrently.
    Steps with dependencies wait for their dependencies to complete.
    """

    def __init__(
        self,
        workflow_id: str,
        name: str = "",
        max_concurrent: int = 5,
    ):
        super().__init__(workflow_id, name)
        self.max_concurrent = max_concurrent

    async def execute(
        self,
        agents: Dict[str, EnterpriseAgent],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Execute steps in parallel."""
        context = context or {}
        self.status = WorkflowStatus.RUNNING
        started_at = datetime.now()

        logger.info(f"Starting parallel workflow: {self.name} ({len(self.steps)} steps)")

        # Group steps by dependency level
        levels = self._group_by_dependency()

        for level_idx, level_steps in enumerate(levels):
            logger.info(f"Executing level {level_idx + 1} with {len(level_steps)} steps")

            # Execute steps at this level in parallel
            tasks = []
            for step in level_steps:
                agent = self._find_agent(step, agents)
                if agent:
                    tasks.append(self._execute_step(step, agent, context))
                else:
                    step.status = WorkflowStatus.FAILED
                    logger.error(f"Step {step.step_id}: No agent found")

            if tasks:
                # Use semaphore for max concurrent
                semaphore = asyncio.Semaphore(self.max_concurrent)

                async def run_with_semaphore(coro):
                    async with semaphore:
                        return await coro

                await asyncio.gather(*[run_with_semaphore(t) for t in tasks])

            # Check for failures that should stop
            if any(s.status == WorkflowStatus.FAILED for s in level_steps):
                # Check if any remaining steps depend on failed steps
                failed_ids = {s.step_id for s in level_steps if s.status == WorkflowStatus.FAILED}
                remaining = [s for s in self.steps if s.status == WorkflowStatus.PENDING]

                for s in remaining:
                    if any(dep in failed_ids for dep in s.depends_on):
                        s.status = WorkflowStatus.BLOCKED

        # Determine final status
        all_completed = all(s.status == WorkflowStatus.COMPLETED for s in self.steps)
        any_failed = any(s.status == WorkflowStatus.FAILED for s in self.steps)
        any_blocked = any(s.status == WorkflowStatus.BLOCKED for s in self.steps)

        if all_completed:
            self.status = WorkflowStatus.COMPLETED
        elif any_failed:
            self.status = WorkflowStatus.FAILED
        elif any_blocked:
            self.status = WorkflowStatus.BLOCKED
        else:
            self.status = WorkflowStatus.COMPLETED

        result = self._create_result()
        result.started_at = started_at
        result.completed_at = datetime.now()
        result.duration_seconds = (result.completed_at - started_at).total_seconds()

        logger.info(f"Parallel workflow {self.name}: {self.status.value}")

        return result

    async def _execute_step(
        self,
        step: WorkflowStep,
        agent: EnterpriseAgent,
        context: Dict[str, Any],
    ):
        """Execute a single step."""
        step.status = WorkflowStatus.RUNNING
        step.started_at = datetime.now()

        try:
            step_payload = {**step.payload, **context}
            result = await agent.execute(step.action, step_payload, context)

            step.result = result
            step.completed_at = datetime.now()

            if result.success:
                step.status = WorkflowStatus.COMPLETED
                logger.info(f"Step {step.step_id}: COMPLETED")
            elif not result.compliance_passed:
                step.status = WorkflowStatus.BLOCKED
                logger.warning(f"Step {step.step_id}: BLOCKED")
            else:
                step.status = WorkflowStatus.FAILED
                logger.error(f"Step {step.step_id}: FAILED")

        except Exception as e:
            step.status = WorkflowStatus.FAILED
            step.completed_at = datetime.now()
            logger.error(f"Step {step.step_id}: Exception - {e}")

    def _group_by_dependency(self) -> List[List[WorkflowStep]]:
        """Group steps by dependency level."""
        levels = []
        assigned = set()

        while len(assigned) < len(self.steps):
            # Find steps whose dependencies are all assigned
            current_level = []
            for step in self.steps:
                if step.step_id in assigned:
                    continue

                deps_met = all(dep in assigned for dep in step.depends_on)
                if deps_met:
                    current_level.append(step)

            if not current_level:
                # Deadlock - remaining steps have circular dependencies
                remaining = [s for s in self.steps if s.step_id not in assigned]
                current_level = remaining
                for s in remaining:
                    s.status = WorkflowStatus.BLOCKED
                assigned.update(s.step_id for s in remaining)
                break

            levels.append(current_level)
            assigned.update(s.step_id for s in current_level)

        return levels

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
