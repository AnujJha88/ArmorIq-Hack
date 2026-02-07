"""
Agentic Orchestrator
====================
Central coordinator for multi-agent pipelines with Watchtower verification.
"""

import os
import sys
import json
import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from orchestrator.registry import AgentRegistry, AgentCapability, AgentStatus, get_registry
from orchestrator.context import PipelineContext, Task, TaskResult, TaskStatus
from orchestrator.agents import BaseAgent, create_all_agents
from orchestrator.policies import PolicyEngine, PolicyAction, get_policy_engine
from orchestrator.drift import DriftDetector, DriftLevel, get_drift_detector
from orchestrator.approvals import ApprovalManager, ApprovalWorkflow, ApprovalStatus, ApprovalType, get_approval_manager
from orchestrator.persistence import StateStore, AuditLogger, AuditEventType, get_state_store, get_audit_logger
from orchestrator.tools import ToolRegistry, get_tool_registry

logger = logging.getLogger("Orchestrator")


@dataclass
class HandoffVerification:
    """Result of Watchtower verification for agent handoff."""
    allowed: bool
    token_id: Optional[str] = None
    plan_hash: Optional[str] = None
    policy_triggered: Optional[str] = None
    reason: Optional[str] = None
    suggestion: Optional[str] = None
    modified_payload: Optional[Dict] = None
    risk_score: float = 0.0
    requires_approval: bool = False
    approval_type: Optional[ApprovalType] = None


@dataclass
class ExecutionConfig:
    """Configuration for pipeline execution."""
    max_parallel_tasks: int = 3
    task_timeout_seconds: int = 300
    enable_drift_detection: bool = True
    enable_approvals: bool = True
    enable_persistence: bool = True
    auto_pause_on_drift: bool = True
    auto_kill_threshold: float = 0.7
    auto_pause_threshold: float = 0.5


class Orchestrator:
    """
    Central orchestrator for multi-agent pipelines.

    Responsibilities:
    1. Plan pipelines from high-level goals
    2. Route tasks to appropriate agents
    3. Verify EVERY handoff with Watchtower
    4. Track drift across the pipeline
    5. Block pipeline if risk too high
    6. Request human approval when needed
    7. Persist state and audit trail
    """

    def __init__(self, config: ExecutionConfig = None):
        self.config = config or ExecutionConfig()
        self.registry = get_registry()
        self.policy_engine = get_policy_engine()
        self.drift_detector = get_drift_detector()
        self.approval_manager = get_approval_manager()
        self.tool_registry = get_tool_registry()
        self.state_store = get_state_store() if self.config.enable_persistence else None
        self.audit_logger = get_audit_logger() if self.config.enable_persistence else None

        self.watchtower_client = None
        self.pipelines: Dict[str, PipelineContext] = {}
        self.execution_lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_parallel_tasks)

        # Initialize Watchtower
        self._init_watchtower()

        # Register all agents
        self._register_agents()

        logger.info("Orchestrator initialized with advanced features")

    def _init_watchtower(self):
        """Initialize Watchtower SDK."""
        api_key = os.getenv("WATCHTOWER_API_KEY", "")

        try:
            from watchtower_sdk import WatchtowerClient
            if api_key.startswith("ak_"):
                self.watchtower_client = WatchtowerClient(
                    api_key=api_key,
                    user_id=os.getenv("WATCHTOWER_USER_ID", "orchestrator"),
                    agent_id=os.getenv("WATCHTOWER_AGENT_ID", "orchestrator-main")
                )
                logger.info("Watchtower SDK initialized (LIVE MODE)")
            else:
                logger.warning("No valid Watchtower API key - using local policies only")
        except ImportError:
            logger.warning("watchtower-sdk not installed")

    def _register_agents(self):
        """Register all available agents."""
        agents = create_all_agents()
        for agent in agents:
            info = agent.to_agent_info()
            self.registry.register(info)

    # ═══════════════════════════════════════════════════════════════════════════
    # PIPELINE PLANNING
    # ═══════════════════════════════════════════════════════════════════════════

    def plan_pipeline(self, goal: str, parameters: Dict[str, Any] = None) -> PipelineContext:
        """
        Plan a pipeline from a high-level goal.

        This could use LLM to dynamically plan, but for now we use predefined templates.
        """
        parameters = parameters or {}
        context = PipelineContext(goal=goal)

        # Determine pipeline type from goal
        goal_lower = goal.lower()

        if "hire" in goal_lower or "recruit" in goal_lower or "candidate" in goal_lower:
            self._plan_hiring_pipeline(context, parameters)
        elif "onboard" in goal_lower:
            self._plan_onboarding_pipeline(context, parameters)
        elif "expense" in goal_lower or "reimburse" in goal_lower:
            self._plan_expense_pipeline(context, parameters)
        elif "review" in goal_lower or "performance" in goal_lower:
            self._plan_performance_pipeline(context, parameters)
        else:
            # Default hiring pipeline
            self._plan_hiring_pipeline(context, parameters)

        context.status = "planned"
        self.pipelines[context.pipeline_id] = context

        # Persist and log
        if self.state_store:
            self.state_store.save_pipeline(context.pipeline_id, {
                "goal": goal,
                "status": "planned",
                "config": parameters
            })
        if self.audit_logger:
            self.audit_logger.log_pipeline_created(context.pipeline_id, goal, parameters)

        logger.info(f"Planned pipeline {context.pipeline_id} with {context.total_tasks} tasks")
        return context

    def _plan_hiring_pipeline(self, context: PipelineContext, params: Dict):
        """Plan a full hiring pipeline."""
        role = params.get("role", "Software Engineer")
        skills = params.get("skills", ["Python", "JavaScript"])
        salary = params.get("salary", 175000)
        level = params.get("level", "L4")
        interview_time = params.get("interview_time", "2026-02-10 14:00")

        # Task 1: Source candidates
        context.add_task(Task(
            task_id="task_source",
            name="Source Candidates",
            capability=AgentCapability.SEARCH_CANDIDATES.value,
            payload={"role": role, "skills": skills, "count": 10}
        ))

        # Task 2: Screen resumes (depends on sourcing)
        context.add_task(Task(
            task_id="task_screen",
            name="Screen Resumes",
            capability=AgentCapability.SCREEN_RESUME.value,
            payload={"criteria": skills},
            depends_on=["task_source"]
        ))

        # Task 3: Schedule interview (depends on screening)
        context.add_task(Task(
            task_id="task_schedule",
            name="Schedule Interview",
            capability=AgentCapability.SCHEDULE_INTERVIEW.value,
            payload={"time": interview_time, "interviewer": params.get("interviewer", "Hiring Manager")},
            depends_on=["task_screen"]
        ))

        # Task 4: Generate offer (depends on interview)
        context.add_task(Task(
            task_id="task_offer",
            name="Generate Offer",
            capability=AgentCapability.GENERATE_OFFER.value,
            payload={"role": role, "level": level, "salary": salary},
            depends_on=["task_schedule"]
        ))

        # Task 5: Verify I-9 (depends on offer)
        context.add_task(Task(
            task_id="task_i9",
            name="Verify I-9",
            capability=AgentCapability.VERIFY_I9.value,
            payload={"i9_status": params.get("i9_status", "verified")},
            depends_on=["task_offer"]
        ))

        # Task 6: Onboard (depends on I-9)
        context.add_task(Task(
            task_id="task_onboard",
            name="Onboard Employee",
            capability=AgentCapability.ONBOARD_EMPLOYEE.value,
            payload={"start_date": params.get("start_date", "2026-03-01"), "i9_status": "verified"},
            depends_on=["task_i9"]
        ))

    def _plan_onboarding_pipeline(self, context: PipelineContext, params: Dict):
        """Plan an onboarding-only pipeline."""
        context.add_task(Task(
            task_id="task_i9",
            name="Verify I-9",
            capability=AgentCapability.VERIFY_I9.value,
            payload={"i9_status": params.get("i9_status", "verified")}
        ))

        context.add_task(Task(
            task_id="task_onboard",
            name="Onboard Employee",
            capability=AgentCapability.ONBOARD_EMPLOYEE.value,
            payload={
                "employee": params.get("employee", "New Hire"),
                "start_date": params.get("start_date", "2026-03-01"),
                "i9_status": "verified"
            },
            depends_on=["task_i9"]
        ))

    def _plan_expense_pipeline(self, context: PipelineContext, params: Dict):
        """Plan an expense processing pipeline."""
        context.add_task(Task(
            task_id="task_submit",
            name="Submit Expense",
            capability=AgentCapability.PROCESS_EXPENSE.value,
            payload={
                "amount": params.get("amount", 100),
                "category": params.get("category", "travel"),
                "description": params.get("description", "Business expense")
            }
        ))

        context.add_task(Task(
            task_id="task_approve",
            name="Approve Expense",
            capability=AgentCapability.APPROVE_EXPENSE.value,
            payload={"approval_level": params.get("approval_level", "manager")},
            depends_on=["task_submit"]
        ))

    def _plan_performance_pipeline(self, context: PipelineContext, params: Dict):
        """Plan a performance review pipeline."""
        context.add_task(Task(
            task_id="task_gather",
            name="Gather Feedback",
            capability=AgentCapability.PROCESS_FEEDBACK.value,
            payload={"employee": params.get("employee", "Employee")}
        ))

        context.add_task(Task(
            task_id="task_review",
            name="Write Review",
            capability=AgentCapability.WRITE_REVIEW.value,
            payload={"period": params.get("period", "Q4 2025")},
            depends_on=["task_gather"]
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # WATCHTOWER VERIFICATION
    # ═══════════════════════════════════════════════════════════════════════════

    def verify_handoff(self, from_agent: str, to_agent: str, task: Task, context: PipelineContext) -> HandoffVerification:
        """
        Verify agent handoff with Watchtower and local policies.

        This is called BEFORE every task execution to ensure:
        1. The receiving agent is allowed to perform the action
        2. The payload meets policy requirements
        3. The cumulative pipeline risk is acceptable
        """
        plan_structure = {
            "goal": f"Handoff from {from_agent} to {to_agent}",
            "steps": [{
                "mcp": "hr-tools",
                "action": task.capability,
                "params": task.payload
            }]
        }

        # Get token from Watchtower
        token_id = None
        plan_hash = None

        if self.watchtower_client:
            try:
                plan = self.watchtower_client.capture_plan(
                    llm=to_agent,
                    prompt=f"Execute {task.name}: {json.dumps(task.payload)[:100]}",
                    plan=plan_structure
                )
                token = self.watchtower_client.get_intent_token(plan)
                token_id = token.token_id if hasattr(token, 'token_id') else None
                plan_hash = token.plan_hash[:16] if hasattr(token, 'plan_hash') else None

                # Log token
                if self.audit_logger and token_id:
                    self.audit_logger.log_watchtower_token(
                        context.pipeline_id,
                        task.task_id,
                        to_agent,
                        token_id,
                        plan_hash or ""
                    )
            except Exception as e:
                logger.error(f"Watchtower error: {e}")

        # Apply local policies via policy engine
        policy_result, all_results = self.policy_engine.evaluate(
            task.capability,
            task.payload,
            {"pipeline_id": context.pipeline_id, "agent_id": to_agent}
        )

        # Check if approval is required
        requires_approval = policy_result.action == PolicyAction.ESCALATE
        approval_type = None
        if requires_approval:
            # Determine approval type based on action
            if "salary" in task.capability or "offer" in task.capability:
                approval_type = ApprovalType.FINANCE
            elif "i9" in task.capability or "background" in task.capability:
                approval_type = ApprovalType.LEGAL
            else:
                approval_type = ApprovalType.MANAGER

        # Determine final allowed status
        allowed = policy_result.action in [PolicyAction.ALLOW, PolicyAction.MODIFY, PolicyAction.WARN]
        if requires_approval and self.config.enable_approvals:
            allowed = False  # Will be handled by approval workflow

        return HandoffVerification(
            allowed=allowed,
            token_id=token_id,
            plan_hash=plan_hash,
            policy_triggered=policy_result.policy_id if policy_result.action != PolicyAction.ALLOW else None,
            reason=policy_result.reason,
            suggestion=policy_result.suggestion,
            modified_payload=policy_result.modified_payload,
            risk_score=policy_result.risk_delta,
            requires_approval=requires_approval,
            approval_type=approval_type
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # PIPELINE EXECUTION
    # ═══════════════════════════════════════════════════════════════════════════

    def execute_pipeline(self, pipeline_id: str, callbacks: Dict = None) -> PipelineContext:
        """
        Execute a planned pipeline.

        Callbacks:
        - on_task_start(task, agent)
        - on_task_complete(task, result)
        - on_handoff(from_agent, to_agent, verification)
        - on_blocked(task, verification)
        - on_pipeline_complete(context)
        - on_drift_alert(alert)
        - on_approval_required(request)
        """
        callbacks = callbacks or {}
        context = self.pipelines.get(pipeline_id)

        if not context:
            raise ValueError(f"Pipeline {pipeline_id} not found")

        context.status = "running"
        previous_agent = "orchestrator"

        # Update persistence
        if self.state_store:
            self.state_store.update_pipeline_status(pipeline_id, "running")

        while True:
            # Check drift state
            if self.config.enable_drift_detection:
                drift_state = self.drift_detector.get_pipeline_drift(pipeline_id)
                if drift_state.get("is_killed"):
                    context.status = "killed"
                    break
                if drift_state.get("is_paused") and self.config.auto_pause_on_drift:
                    context.status = "paused"
                    break

            # Get next task
            task = context.get_next_task()

            if task is None:
                # No more tasks
                break

            # Find agent for this task
            capability = AgentCapability(task.capability)
            agent_info = self.registry.find_agent_for_capability(capability)

            if not agent_info:
                # No agent available
                result = TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    agent_id="none",
                    error=f"No agent available for {task.capability}"
                )
                context.record_result(task.task_id, result)
                continue

            task.agent_id = agent_info.agent_id

            # WATCHTOWER: Verify handoff
            verification = self.verify_handoff(previous_agent, agent_info.agent_id, task, context)

            if callbacks.get("on_handoff"):
                callbacks["on_handoff"](previous_agent, agent_info.agent_id, verification)

            # Handle approval requirement
            if verification.requires_approval and self.config.enable_approvals:
                approval_workflow = ApprovalWorkflow(self.approval_manager)
                request = approval_workflow.request_approval(
                    pipeline_id=context.pipeline_id,
                    task_id=task.task_id,
                    agent_id=agent_info.agent_id,
                    action=task.capability,
                    payload=task.payload,
                    policy_result=type('PolicyResult', (), {
                        'reason': verification.reason,
                        'policy_id': verification.policy_triggered,
                        'suggestion': verification.suggestion,
                        'risk_delta': verification.risk_score,
                        'metadata': {}
                    })()
                )

                if callbacks.get("on_approval_required"):
                    callbacks["on_approval_required"](request)

                # For demo, we'll skip the task as pending approval
                result = TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.BLOCKED,
                    agent_id=agent_info.agent_id,
                    blocked_reason="Requires human approval",
                    policy_triggered=verification.policy_triggered,
                    suggestion=f"Pending {verification.approval_type.value} approval",
                    risk_score=verification.risk_score
                )
                context.record_result(task.task_id, result)

                if self.audit_logger:
                    self.audit_logger.log(
                        AuditEventType.APPROVAL_REQUESTED,
                        pipeline_id=context.pipeline_id,
                        task_id=task.task_id,
                        agent_id=agent_info.agent_id,
                        details={"approval_type": verification.approval_type.value}
                    )

                continue

            if not verification.allowed:
                # Blocked by policy
                result = TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.BLOCKED,
                    agent_id=agent_info.agent_id,
                    blocked_reason=verification.reason,
                    policy_triggered=verification.policy_triggered,
                    suggestion=verification.suggestion,
                    watchtower_token=verification.token_id,
                    risk_score=verification.risk_score
                )
                context.record_result(task.task_id, result)

                if callbacks.get("on_blocked"):
                    callbacks["on_blocked"](task, verification)

                # Record drift
                if self.config.enable_drift_detection:
                    drift_level, alerts = self.drift_detector.record_action(
                        pipeline_id=context.pipeline_id,
                        agent_id=agent_info.agent_id,
                        action=task.capability,
                        risk_delta=verification.risk_score,
                        blocked=True
                    )

                    for alert in alerts:
                        if callbacks.get("on_drift_alert"):
                            callbacks["on_drift_alert"](alert)
                        if self.audit_logger:
                            self.audit_logger.log_drift_alert(
                                context.pipeline_id,
                                agent_info.agent_id,
                                alert.alert_type.value,
                                alert.severity.value,
                                alert.message
                            )

                # Update agent risk
                self.registry.update_risk(agent_info.agent_id, agent_info.risk_score + 0.2)

                if self.audit_logger:
                    self.audit_logger.log_task_blocked(
                        context.pipeline_id,
                        task.task_id,
                        agent_info.agent_id,
                        verification.reason,
                        verification.policy_triggered or "unknown"
                    )

                # Check if we should abort pipeline
                if context.max_risk >= self.config.auto_kill_threshold:
                    context.status = "killed"
                    break
                elif context.max_risk >= self.config.auto_pause_threshold:
                    context.status = "paused"
                    break

                continue

            # Apply modified payload if needed
            if verification.modified_payload:
                task.payload = verification.modified_payload

            if callbacks.get("on_task_start"):
                callbacks["on_task_start"](task, agent_info)

            if self.audit_logger:
                self.audit_logger.log_task_started(
                    context.pipeline_id,
                    task.task_id,
                    agent_info.agent_id,
                    task.capability
                )

            # Execute task
            try:
                self.registry.update_status(agent_info.agent_id, AgentStatus.BUSY)
                agent_info.current_task = task.task_id

                result = agent_info.executor(task, context)
                result.watchtower_token = verification.token_id
                result.risk_score = verification.risk_score

                context.record_result(task.task_id, result)
                self.registry.record_task_result(agent_info.agent_id, result.success)

                # Record drift
                if self.config.enable_drift_detection:
                    drift_level, alerts = self.drift_detector.record_action(
                        pipeline_id=context.pipeline_id,
                        agent_id=agent_info.agent_id,
                        action=task.capability,
                        risk_delta=verification.risk_score,
                        blocked=False
                    )

                    for alert in alerts:
                        if callbacks.get("on_drift_alert"):
                            callbacks["on_drift_alert"](alert)

                if self.audit_logger:
                    self.audit_logger.log_task_completed(
                        context.pipeline_id,
                        task.task_id,
                        agent_info.agent_id,
                        result.to_dict()
                    )

            except Exception as e:
                result = TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    agent_id=agent_info.agent_id,
                    error=str(e),
                    risk_score=0.3
                )
                context.record_result(task.task_id, result)
                self.registry.record_task_result(agent_info.agent_id, False)

                if self.config.enable_drift_detection:
                    self.drift_detector.record_action(
                        pipeline_id=context.pipeline_id,
                        agent_id=agent_info.agent_id,
                        action=task.capability,
                        risk_delta=0.3,
                        blocked=False
                    )

            finally:
                self.registry.update_status(agent_info.agent_id, AgentStatus.AVAILABLE)
                agent_info.current_task = None

            if callbacks.get("on_task_complete"):
                callbacks["on_task_complete"](task, result)

            previous_agent = agent_info.agent_id

        # Pipeline complete
        if context.status not in ["killed", "paused"]:
            if context.blocked_tasks > 0:
                context.status = "blocked"
            elif context.failed_tasks > 0:
                context.status = "failed"
            else:
                context.status = "completed"

        # Persist final state
        if self.state_store:
            self.state_store.update_pipeline_status(
                pipeline_id,
                context.status,
                context.get_summary()
            )
        if self.audit_logger:
            self.audit_logger.log_pipeline_completed(pipeline_id, context.get_summary())

        if callbacks.get("on_pipeline_complete"):
            callbacks["on_pipeline_complete"](context)

        return context

    def get_pipeline(self, pipeline_id: str) -> Optional[PipelineContext]:
        """Get a pipeline by ID."""
        return self.pipelines.get(pipeline_id)

    def list_pipelines(self) -> List[PipelineContext]:
        """List all pipelines."""
        return list(self.pipelines.values())

    def get_drift_state(self, pipeline_id: str) -> Dict:
        """Get drift state for a pipeline."""
        return self.drift_detector.get_pipeline_drift(pipeline_id)

    def get_pending_approvals(self) -> List:
        """Get all pending approval requests."""
        return self.approval_manager.list_pending()

    def approve_request(self, request_id: str, user_id: str, notes: str = None) -> bool:
        """Approve an approval request."""
        result = self.approval_manager.approve(request_id, user_id, notes)
        if result and self.audit_logger:
            self.audit_logger.log(
                AuditEventType.APPROVAL_GRANTED,
                user_id=user_id,
                details={"request_id": request_id, "notes": notes}
            )
        return result

    def reject_request(self, request_id: str, user_id: str, notes: str = None) -> bool:
        """Reject an approval request."""
        result = self.approval_manager.reject(request_id, user_id, notes)
        if result and self.audit_logger:
            self.audit_logger.log(
                AuditEventType.APPROVAL_DENIED,
                user_id=user_id,
                details={"request_id": request_id, "notes": notes}
            )
        return result

    def get_system_stats(self) -> Dict:
        """Get overall system statistics."""
        stats = {
            "agents": {
                "total": len(self.registry.list_agents()),
                "available": len(self.registry.list_available())
            },
            "pipelines": {
                "total": len(self.pipelines),
                "by_status": {}
            },
            "drift": self.drift_detector.get_summary(),
            "approvals": self.approval_manager.get_stats(),
            "policies": self.policy_engine.get_policy_stats(),
            "tools": self.tool_registry.get_tools_summary()
        }

        for pipeline in self.pipelines.values():
            status = pipeline.status
            stats["pipelines"]["by_status"][status] = stats["pipelines"]["by_status"].get(status, 0) + 1

        if self.state_store:
            stats["persistence"] = self.state_store.get_stats()

        return stats


# Singleton
_orchestrator = None

def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
