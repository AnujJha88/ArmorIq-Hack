"""
Workflow Engine
===============
Core workflow execution engine.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
from enum import Enum

from ...agents.base_agent import EnterpriseAgent, ActionResult

logger = logging.getLogger("Orchestrator.Workflow")


class WorkflowStatus(Enum):
    """Status of a workflow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    PAUSED = "paused"


@dataclass
class WorkflowStep:
    """A step in a workflow."""
    step_id: str
    action: str
    payload: Dict[str, Any]
    agent_type: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)

    # Execution state
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Optional[ActionResult] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "agent_type": self.agent_type,
            "depends_on": self.depends_on,
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None,
        }


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_id: str
    status: WorkflowStatus
    steps: List[WorkflowStep]

    # Summary
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    blocked_steps: int = 0

    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0

    # Risk
    max_risk_score: float = 0.0
    total_risk_delta: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "blocked_steps": self.blocked_steps,
            "max_risk_score": self.max_risk_score,
            "duration_seconds": self.duration_seconds,
            "steps": [s.to_dict() for s in self.steps],
        }


class Workflow(ABC):
    """Abstract base class for workflows."""

    def __init__(self, workflow_id: str, name: str = ""):
        self.workflow_id = workflow_id
        self.name = name or workflow_id
        self.steps: List[WorkflowStep] = []
        self.status = WorkflowStatus.PENDING
        self._step_counter = 0

    def add_step(
        self,
        action: str,
        payload: Dict[str, Any],
        agent_type: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
    ) -> str:
        """Add a step to the workflow."""
        self._step_counter += 1
        step_id = f"{self.workflow_id}_step_{self._step_counter:03d}"

        step = WorkflowStep(
            step_id=step_id,
            action=action,
            payload=payload,
            agent_type=agent_type,
            depends_on=depends_on or [],
        )

        self.steps.append(step)
        return step_id

    @abstractmethod
    async def execute(
        self,
        agents: Dict[str, EnterpriseAgent],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Execute the workflow."""
        pass

    def _create_result(self) -> WorkflowResult:
        """Create a workflow result from current state."""
        completed = sum(1 for s in self.steps if s.status == WorkflowStatus.COMPLETED)
        failed = sum(1 for s in self.steps if s.status == WorkflowStatus.FAILED)
        blocked = sum(1 for s in self.steps if s.status == WorkflowStatus.BLOCKED)

        max_risk = max((s.result.risk_score for s in self.steps if s.result), default=0.0)

        return WorkflowResult(
            workflow_id=self.workflow_id,
            status=self.status,
            steps=self.steps,
            total_steps=len(self.steps),
            completed_steps=completed,
            failed_steps=failed,
            blocked_steps=blocked,
            max_risk_score=max_risk,
        )


class WorkflowEngine:
    """
    Executes workflows with full TIRS and compliance integration.
    """

    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._results: Dict[str, WorkflowResult] = {}

    def register_workflow(self, workflow: Workflow):
        """Register a workflow."""
        self._workflows[workflow.workflow_id] = workflow

    async def execute(
        self,
        workflow_id: str,
        agents: Dict[str, EnterpriseAgent],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """Execute a registered workflow."""
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        logger.info(f"Executing workflow: {workflow.name}")

        result = await workflow.execute(agents, context)
        self._results[workflow_id] = result

        return result

    def get_result(self, workflow_id: str) -> Optional[WorkflowResult]:
        """Get workflow result."""
        return self._results.get(workflow_id)

    def list_workflows(self) -> List[Dict]:
        """List all registered workflows."""
        return [
            {
                "workflow_id": w.workflow_id,
                "name": w.name,
                "steps": len(w.steps),
                "status": w.status.value,
            }
            for w in self._workflows.values()
        ]
