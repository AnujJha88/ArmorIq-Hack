"""
Pipeline Context & State Management
====================================
Shared state that flows through the multi-agent pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import json
import uuid


class TaskStatus(Enum):
    """Status of a task in the pipeline."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"      # Blocked by ArmorIQ
    SKIPPED = "skipped"      # Skipped due to dependency failure


@dataclass
class TaskResult:
    """Result of a task execution."""
    task_id: str
    status: TaskStatus
    agent_id: str
    output: Any = None
    error: Optional[str] = None
    blocked_reason: Optional[str] = None
    policy_triggered: Optional[str] = None
    suggestion: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    risk_score: float = 0.0
    armoriq_token: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    @property
    def duration_ms(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "agent_id": self.agent_id,
            "output": self.output,
            "error": self.error,
            "blocked_reason": self.blocked_reason,
            "policy_triggered": self.policy_triggered,
            "suggestion": self.suggestion,
            "risk_score": self.risk_score,
            "armoriq_token": self.armoriq_token,
            "duration_ms": self.duration_ms
        }


@dataclass
class Task:
    """A task in the pipeline."""
    task_id: str
    name: str
    capability: str
    payload: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    agent_id: Optional[str] = None  # Assigned agent
    result: Optional[TaskResult] = None
    priority: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "capability": self.capability,
            "payload": self.payload,
            "depends_on": self.depends_on,
            "agent_id": self.agent_id,
            "result": self.result.to_dict() if self.result else None,
            "priority": self.priority,
            "metadata": self.metadata
        }


@dataclass
class PipelineContext:
    """
    Shared context that flows through the entire pipeline.

    Contains:
    - The original goal/request
    - All tasks and their results
    - Accumulated data from each step
    - Audit trail
    """
    pipeline_id: str = field(default_factory=lambda: f"pipe_{uuid.uuid4().hex[:12]}")
    goal: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Tasks
    tasks: Dict[str, Task] = field(default_factory=dict)
    task_order: List[str] = field(default_factory=list)

    # Accumulated data from task outputs
    data: Dict[str, Any] = field(default_factory=dict)

    # Pipeline status
    status: str = "created"  # created, running, completed, failed, blocked

    # Metrics
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    blocked_tasks: int = 0

    # Risk tracking
    cumulative_risk: float = 0.0
    max_risk: float = 0.0

    # Audit trail
    audit_log: List[Dict] = field(default_factory=list)

    # ArmorIQ tokens
    intent_tokens: List[str] = field(default_factory=list)

    def add_task(self, task: Task):
        """Add a task to the pipeline."""
        self.tasks[task.task_id] = task
        self.task_order.append(task.task_id)
        self.total_tasks += 1
        self._log("task_added", {"task_id": task.task_id, "name": task.name})

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def get_next_task(self) -> Optional[Task]:
        """Get the next task that's ready to execute."""
        for task_id in self.task_order:
            task = self.tasks[task_id]

            # Skip if already has result
            if task.result is not None:
                continue

            # Check dependencies
            deps_satisfied = True
            for dep_id in task.depends_on:
                dep_task = self.tasks.get(dep_id)
                if not dep_task or not dep_task.result or not dep_task.result.success:
                    deps_satisfied = False
                    break

            if deps_satisfied:
                return task

        return None

    def record_result(self, task_id: str, result: TaskResult):
        """Record a task result."""
        if task_id not in self.tasks:
            return

        self.tasks[task_id].result = result
        self.updated_at = datetime.now()

        # Update counters
        if result.status == TaskStatus.COMPLETED:
            self.completed_tasks += 1
        elif result.status == TaskStatus.FAILED:
            self.failed_tasks += 1
        elif result.status == TaskStatus.BLOCKED:
            self.blocked_tasks += 1

        # Update risk
        self.cumulative_risk += result.risk_score
        self.max_risk = max(self.max_risk, result.risk_score)

        # Store token
        if result.armoriq_token:
            self.intent_tokens.append(result.armoriq_token)

        # Log
        self._log("task_completed", {
            "task_id": task_id,
            "status": result.status.value,
            "risk_score": result.risk_score
        })

    def store_data(self, key: str, value: Any):
        """Store data in the shared context."""
        self.data[key] = value
        self._log("data_stored", {"key": key})

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from the shared context."""
        return self.data.get(key, default)

    def merge_data(self, new_data: Dict[str, Any]):
        """Merge new data into context."""
        self.data.update(new_data)

    def is_complete(self) -> bool:
        """Check if all tasks are done."""
        return all(task.result is not None for task in self.tasks.values())

    def is_blocked(self) -> bool:
        """Check if pipeline is blocked."""
        # Blocked if any task is blocked or cumulative risk too high
        if self.max_risk >= 0.7:
            return True
        return self.blocked_tasks > 0

    def get_summary(self) -> Dict:
        """Get pipeline summary."""
        return {
            "pipeline_id": self.pipeline_id,
            "goal": self.goal,
            "status": self.status,
            "total_tasks": self.total_tasks,
            "completed": self.completed_tasks,
            "failed": self.failed_tasks,
            "blocked": self.blocked_tasks,
            "cumulative_risk": self.cumulative_risk,
            "max_risk": self.max_risk,
            "intent_tokens": len(self.intent_tokens)
        }

    def _log(self, event: str, details: Dict):
        """Add to audit log."""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "details": details
        })

    def to_dict(self) -> dict:
        return {
            "pipeline_id": self.pipeline_id,
            "goal": self.goal,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "task_order": self.task_order,
            "data": self.data,
            "summary": self.get_summary(),
            "audit_log": self.audit_log
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)
