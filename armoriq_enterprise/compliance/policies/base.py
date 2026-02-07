"""
Base Policy Classes
===================
Foundation for all compliance policies.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger("Compliance.Policy")


class PolicyCategory(Enum):
    """Categories of compliance policies."""
    # Financial
    EXPENSE_LIMITS = "expense_limits"
    BUDGET_CONTROLS = "budget_controls"
    INVOICE_APPROVAL = "invoice_approval"
    SOX_COMPLIANCE = "sox_compliance"

    # Legal
    CONTRACT_REVIEW = "contract_review"
    NDA_ENFORCEMENT = "nda_enforcement"
    IP_PROTECTION = "ip_protection"
    LITIGATION_HOLD = "litigation_hold"

    # Security/IT
    ACCESS_CONTROL = "access_control"
    DATA_CLASSIFICATION = "data_classification"
    INCIDENT_RESPONSE = "incident_response"
    CHANGE_MANAGEMENT = "change_management"

    # HR/Employment
    HIRING_COMPLIANCE = "hiring_compliance"
    COMPENSATION = "compensation"
    TERMINATION = "termination"
    LEAVE_MANAGEMENT = "leave_management"

    # Procurement
    VENDOR_APPROVAL = "vendor_approval"
    SPENDING_LIMITS = "spending_limits"
    BID_REQUIREMENTS = "bid_requirements"

    # Data Privacy
    PII_PROTECTION = "pii_protection"
    CROSS_BORDER = "cross_border"
    RETENTION = "retention"
    CONSENT = "consent"

    # Operations
    SLA_COMPLIANCE = "sla_compliance"
    ITIL_PROCESSES = "itil_processes"


class PolicyAction(Enum):
    """Actions a policy can take."""
    ALLOW = "allow"
    DENY = "deny"
    MODIFY = "modify"
    WARN = "warn"
    ESCALATE = "escalate"
    AUDIT = "audit"


class PolicySeverity(Enum):
    """Severity of policy violations."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    policy_id: str
    policy_name: str
    category: PolicyCategory
    action: PolicyAction
    severity: PolicySeverity

    # Outcome details
    allowed: bool
    reason: str
    suggestion: Optional[str] = None
    modified_payload: Optional[Dict] = None

    # Risk contribution
    risk_delta: float = 0.0

    # Audit trail
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "policy_id": self.policy_id,
            "policy_name": self.policy_name,
            "category": self.category.value,
            "action": self.action.value,
            "severity": self.severity.name,
            "allowed": self.allowed,
            "reason": self.reason,
            "suggestion": self.suggestion,
            "risk_delta": self.risk_delta,
            "timestamp": self.timestamp.isoformat(),
        }


class Policy(ABC):
    """
    Abstract base class for compliance policies.

    All policies must implement the evaluate method.
    """

    def __init__(
        self,
        policy_id: str,
        name: str,
        category: PolicyCategory,
        severity: PolicySeverity = PolicySeverity.MEDIUM,
        enabled: bool = True,
        description: str = "",
    ):
        self.policy_id = policy_id
        self.name = name
        self.category = category
        self.severity = severity
        self.enabled = enabled
        self.description = description

        # Track evaluations
        self.evaluation_count = 0
        self.violation_count = 0

    @abstractmethod
    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """
        Evaluate the policy against an action.

        Args:
            action: The action being performed
            payload: The action payload
            context: Additional context (agent, pipeline, etc.)

        Returns:
            PolicyResult with the evaluation outcome
        """
        pass

    def _allow(self, reason: str = "Policy passed") -> PolicyResult:
        """Create an ALLOW result."""
        self.evaluation_count += 1
        return PolicyResult(
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            action=PolicyAction.ALLOW,
            severity=self.severity,
            allowed=True,
            reason=reason,
        )

    def _deny(self, reason: str, suggestion: Optional[str] = None) -> PolicyResult:
        """Create a DENY result."""
        self.evaluation_count += 1
        self.violation_count += 1
        return PolicyResult(
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            action=PolicyAction.DENY,
            severity=self.severity,
            allowed=False,
            reason=reason,
            suggestion=suggestion,
            risk_delta=0.1 * self.severity.value,
        )

    def _modify(
        self,
        reason: str,
        modified_payload: Dict,
        suggestion: Optional[str] = None,
    ) -> PolicyResult:
        """Create a MODIFY result."""
        self.evaluation_count += 1
        return PolicyResult(
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            action=PolicyAction.MODIFY,
            severity=self.severity,
            allowed=True,
            reason=reason,
            suggestion=suggestion,
            modified_payload=modified_payload,
            risk_delta=0.05,
        )

    def _escalate(self, reason: str, suggestion: Optional[str] = None) -> PolicyResult:
        """Create an ESCALATE result."""
        self.evaluation_count += 1
        return PolicyResult(
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            action=PolicyAction.ESCALATE,
            severity=self.severity,
            allowed=False,
            reason=reason,
            suggestion=suggestion or "Requires approval from authorized approver",
            risk_delta=0.05,
        )

    def _warn(self, reason: str) -> PolicyResult:
        """Create a WARN result."""
        self.evaluation_count += 1
        return PolicyResult(
            policy_id=self.policy_id,
            policy_name=self.name,
            category=self.category,
            action=PolicyAction.WARN,
            severity=self.severity,
            allowed=True,
            reason=reason,
            risk_delta=0.02,
        )

    def to_dict(self) -> Dict:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "category": self.category.value,
            "severity": self.severity.name,
            "enabled": self.enabled,
            "description": self.description,
            "evaluation_count": self.evaluation_count,
            "violation_count": self.violation_count,
        }


class RuleBasedPolicy(Policy):
    """
    Policy based on simple rules.

    Uses a list of rule functions that are evaluated in order.
    """

    def __init__(
        self,
        policy_id: str,
        name: str,
        category: PolicyCategory,
        rules: Optional[List[Callable]] = None,
        **kwargs,
    ):
        super().__init__(policy_id, name, category, **kwargs)
        self.rules = rules or []

    def add_rule(self, rule: Callable):
        """Add a rule function."""
        self.rules.append(rule)

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate all rules in order."""
        for rule in self.rules:
            try:
                result = rule(action, payload, context)
                if result is not None:
                    return result
            except Exception as e:
                logger.error(f"Rule evaluation error in {self.policy_id}: {e}")

        return self._allow("All rules passed")


class ThresholdPolicy(Policy):
    """
    Policy based on numeric thresholds.
    """

    def __init__(
        self,
        policy_id: str,
        name: str,
        category: PolicyCategory,
        field: str,
        warn_threshold: Optional[float] = None,
        deny_threshold: Optional[float] = None,
        escalate_threshold: Optional[float] = None,
        **kwargs,
    ):
        super().__init__(policy_id, name, category, **kwargs)
        self.field = field
        self.warn_threshold = warn_threshold
        self.deny_threshold = deny_threshold
        self.escalate_threshold = escalate_threshold

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate against thresholds."""
        value = payload.get(self.field)

        if value is None:
            return self._allow(f"Field {self.field} not present")

        try:
            value = float(value)
        except (TypeError, ValueError):
            return self._allow(f"Field {self.field} is not numeric")

        # Check thresholds (order matters: deny > escalate > warn)
        if self.deny_threshold is not None and value >= self.deny_threshold:
            return self._deny(
                f"{self.field} ({value}) exceeds maximum ({self.deny_threshold})",
                f"Reduce {self.field} below {self.deny_threshold}",
            )

        if self.escalate_threshold is not None and value >= self.escalate_threshold:
            return self._escalate(
                f"{self.field} ({value}) requires approval (threshold: {self.escalate_threshold})",
            )

        if self.warn_threshold is not None and value >= self.warn_threshold:
            return self._warn(
                f"{self.field} ({value}) approaching limit ({self.deny_threshold or 'N/A'})",
            )

        return self._allow(f"{self.field} ({value}) within limits")
