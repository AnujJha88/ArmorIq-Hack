"""
Remediation Engine
==================
Automated remediation suggestions and execution.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("TIRS.Remediation")


class RemediationType(Enum):
    """Types of remediation actions."""
    REDUCE_SCOPE = "reduce_scope"
    REQUEST_APPROVAL = "request_approval"
    DELAY_ACTION = "delay_action"
    MODIFY_PAYLOAD = "modify_payload"
    SPLIT_REQUEST = "split_request"
    USE_ALTERNATIVE = "use_alternative"
    ESCALATE = "escalate"


class RemediationPriority(Enum):
    """Priority levels for remediation."""
    OPTIONAL = 1
    RECOMMENDED = 2
    REQUIRED = 3
    MANDATORY = 4


@dataclass
class RemediationStep:
    """Single step in a remediation plan."""
    step_id: str
    action: RemediationType
    description: str
    expected_impact: float  # Expected risk reduction (0-1)
    priority: RemediationPriority
    parameters: Dict = field(default_factory=dict)
    automated: bool = False


@dataclass
class RemediationPlan:
    """
    Complete remediation plan for addressing drift.
    """
    plan_id: str
    agent_id: str

    # The issue being addressed
    issue_summary: str
    current_risk_score: float
    target_risk_score: float

    # Fields with defaults must come after required fields
    created_at: datetime = field(default_factory=datetime.now)

    # Steps to take
    steps: List[RemediationStep] = field(default_factory=list)

    # Expected outcome
    expected_risk_reduction: float = 0.0
    confidence: float = 0.0

    # Execution tracking
    executed: bool = False
    execution_result: Optional[str] = None

    def add_step(self, step: RemediationStep):
        """Add a step to the plan."""
        self.steps.append(step)
        self._recalculate_expected_reduction()

    def _recalculate_expected_reduction(self):
        """Recalculate expected risk reduction."""
        if not self.steps:
            self.expected_risk_reduction = 0.0
            return

        # Combine step impacts (diminishing returns)
        remaining_risk = self.current_risk_score
        for step in self.steps:
            reduction = remaining_risk * step.expected_impact
            remaining_risk -= reduction

        self.expected_risk_reduction = self.current_risk_score - remaining_risk
        self.target_risk_score = remaining_risk

    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "agent_id": self.agent_id,
            "created_at": self.created_at.isoformat(),
            "issue_summary": self.issue_summary,
            "current_risk_score": self.current_risk_score,
            "target_risk_score": self.target_risk_score,
            "expected_risk_reduction": self.expected_risk_reduction,
            "confidence": self.confidence,
            "steps": [
                {
                    "step_id": s.step_id,
                    "action": s.action.value,
                    "description": s.description,
                    "expected_impact": s.expected_impact,
                    "priority": s.priority.name,
                    "automated": s.automated,
                }
                for s in self.steps
            ],
            "executed": self.executed,
        }


class RemediationEngine:
    """
    Generates and executes remediation plans.

    Uses rules and patterns to suggest appropriate
    remediation steps based on the type of drift detected.
    """

    def __init__(self):
        self._step_counter = 0
        self._plan_counter = 0
        self._plan_history: List[RemediationPlan] = []

        # Remediation rules by signal type
        self._signal_remediations = self._load_signal_rules()

    def _load_signal_rules(self) -> Dict[str, List[Dict]]:
        """Load remediation rules for each signal type."""
        return {
            "embedding_drift": [
                {
                    "action": RemediationType.REDUCE_SCOPE,
                    "description": "Limit operations to core capabilities",
                    "impact": 0.4,
                    "priority": RemediationPriority.RECOMMENDED,
                },
                {
                    "action": RemediationType.REQUEST_APPROVAL,
                    "description": "Request approval for expanded operations",
                    "impact": 0.3,
                    "priority": RemediationPriority.RECOMMENDED,
                },
            ],
            "capability_surprisal": [
                {
                    "action": RemediationType.REQUEST_APPROVAL,
                    "description": "Request explicit authorization for new capabilities",
                    "impact": 0.5,
                    "priority": RemediationPriority.REQUIRED,
                },
                {
                    "action": RemediationType.USE_ALTERNATIVE,
                    "description": "Use standard capability instead of unusual one",
                    "impact": 0.4,
                    "priority": RemediationPriority.RECOMMENDED,
                },
            ],
            "violation_rate": [
                {
                    "action": RemediationType.MODIFY_PAYLOAD,
                    "description": "Adjust request to comply with policies",
                    "impact": 0.6,
                    "priority": RemediationPriority.REQUIRED,
                },
                {
                    "action": RemediationType.ESCALATE,
                    "description": "Escalate to supervisor for policy exception",
                    "impact": 0.3,
                    "priority": RemediationPriority.OPTIONAL,
                },
            ],
            "velocity_anomaly": [
                {
                    "action": RemediationType.DELAY_ACTION,
                    "description": "Reduce action rate to normal levels",
                    "impact": 0.5,
                    "priority": RemediationPriority.RECOMMENDED,
                },
                {
                    "action": RemediationType.SPLIT_REQUEST,
                    "description": "Split bulk operation into smaller batches",
                    "impact": 0.4,
                    "priority": RemediationPriority.RECOMMENDED,
                },
            ],
            "context_deviation": [
                {
                    "action": RemediationType.DELAY_ACTION,
                    "description": "Delay operation to normal business hours",
                    "impact": 0.3,
                    "priority": RemediationPriority.OPTIONAL,
                },
                {
                    "action": RemediationType.REQUEST_APPROVAL,
                    "description": "Request approval for off-hours operation",
                    "impact": 0.4,
                    "priority": RemediationPriority.RECOMMENDED,
                },
            ],
        }

    def generate_plan(
        self,
        agent_id: str,
        risk_score: float,
        signals: List[Dict],  # List of {name, raw_value, contribution}
        issue_summary: Optional[str] = None,
    ) -> RemediationPlan:
        """
        Generate a remediation plan based on detected drift.

        Args:
            agent_id: Agent needing remediation
            risk_score: Current risk score
            signals: Drift signals with their contributions
            issue_summary: Optional human-readable summary

        Returns:
            RemediationPlan with prioritized steps
        """
        self._plan_counter += 1
        plan_id = f"REM-{datetime.now().strftime('%Y%m%d')}-{self._plan_counter:04d}"

        # Generate summary if not provided
        if not issue_summary:
            top_signal = max(signals, key=lambda s: s.get("contribution", 0)) if signals else None
            issue_summary = f"Elevated risk ({risk_score:.2f}) primarily from {top_signal['name']}" if top_signal else "Elevated risk detected"

        plan = RemediationPlan(
            plan_id=plan_id,
            agent_id=agent_id,
            issue_summary=issue_summary,
            current_risk_score=risk_score,
            target_risk_score=risk_score,
        )

        # Sort signals by contribution
        sorted_signals = sorted(signals, key=lambda s: s.get("contribution", 0), reverse=True)

        # Generate steps for top contributing signals
        for signal in sorted_signals[:3]:  # Top 3 signals
            signal_name = signal.get("name", "")
            contribution = signal.get("contribution", 0)

            if contribution < 0.05:  # Skip minor contributors
                continue

            rules = self._signal_remediations.get(signal_name, [])

            for rule in rules:
                self._step_counter += 1
                step = RemediationStep(
                    step_id=f"STEP-{self._step_counter:04d}",
                    action=rule["action"],
                    description=rule["description"],
                    expected_impact=rule["impact"] * (contribution / risk_score),
                    priority=rule["priority"],
                    parameters={"signal": signal_name, "contribution": contribution},
                )
                plan.add_step(step)

        # Calculate confidence based on coverage
        if signals:
            covered = sum(s.get("contribution", 0) for s in sorted_signals[:3])
            plan.confidence = min(covered / risk_score, 1.0) if risk_score > 0 else 0.5

        self._plan_history.append(plan)

        logger.info(f"Generated remediation plan {plan_id} with {len(plan.steps)} steps")
        return plan

    def apply_step(
        self,
        plan: RemediationPlan,
        step_id: str,
        context: Optional[Dict] = None,
    ) -> Tuple[bool, str]:
        """
        Apply a single remediation step.

        Returns:
            (success, message)
        """
        step = next((s for s in plan.steps if s.step_id == step_id), None)
        if not step:
            return False, f"Step {step_id} not found"

        # Execute based on action type
        if step.action == RemediationType.REDUCE_SCOPE:
            return True, "Scope reduced to core capabilities"

        elif step.action == RemediationType.REQUEST_APPROVAL:
            # In production, this would create an approval request
            return True, "Approval request created"

        elif step.action == RemediationType.DELAY_ACTION:
            return True, "Action delayed"

        elif step.action == RemediationType.MODIFY_PAYLOAD:
            # In production, this would modify the actual payload
            return True, "Payload modified to comply"

        elif step.action == RemediationType.SPLIT_REQUEST:
            return True, "Request split into batches"

        elif step.action == RemediationType.USE_ALTERNATIVE:
            return True, "Alternative capability suggested"

        elif step.action == RemediationType.ESCALATE:
            return True, "Escalated to supervisor"

        return False, "Unknown action type"

    def get_quick_fix(
        self,
        signal_name: str,
        current_value: float,
    ) -> Optional[str]:
        """Get a quick fix suggestion for a specific signal."""
        fixes = {
            "embedding_drift": "Return to standard operations or request approval for expanded scope",
            "capability_surprisal": "Request authorization before using unusual capabilities",
            "violation_rate": "Review recent actions and comply with policy requirements",
            "velocity_anomaly": "Reduce action rate to normal levels",
            "context_deviation": "Operate during business hours or request after-hours approval",
        }
        return fixes.get(signal_name)

    def get_plan_history(self, agent_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get remediation plan history."""
        history = self._plan_history
        if agent_id:
            history = [p for p in history if p.agent_id == agent_id]

        return [p.to_dict() for p in history[-limit:]]


# Singleton
_engine: Optional[RemediationEngine] = None


def get_remediation_engine() -> RemediationEngine:
    """Get singleton remediation engine."""
    global _engine
    if _engine is None:
        _engine = RemediationEngine()
    return _engine
