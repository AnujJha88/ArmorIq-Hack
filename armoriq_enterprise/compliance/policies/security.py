"""
Security/IT Compliance Policies
===============================
Access control, data classification, incident response, change management.
"""

from typing import Dict, Any, List, Set, Optional
from datetime import datetime, timedelta
from .base import (
    Policy, PolicyCategory, PolicyAction, PolicySeverity, PolicyResult,
)


class AccessControlPolicy(Policy):
    """Enforce role-based access control."""

    # Role hierarchy
    ROLE_HIERARCHY = {
        "admin": 100,
        "manager": 80,
        "senior": 60,
        "standard": 40,
        "contractor": 20,
        "guest": 10,
    }

    # Resource access requirements
    RESOURCE_REQUIREMENTS = {
        "production_database": 80,
        "financial_records": 60,
        "customer_data": 60,
        "source_code": 40,
        "internal_docs": 20,
        "public_docs": 10,
    }

    def __init__(self):
        super().__init__(
            policy_id="SEC-001",
            name="Access Control Policy",
            category=PolicyCategory.ACCESS_CONTROL,
            severity=PolicySeverity.HIGH,
            description="Enforces role-based access control for resources",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate access control."""
        resource = payload.get("resource") or payload.get("target")
        role = context.get("role", "guest")

        if not resource:
            return self._allow("No resource specified")

        # Get role level
        role_level = self.ROLE_HIERARCHY.get(role.lower(), 10)

        # Get required level for resource
        required_level = 10
        for res_pattern, level in self.RESOURCE_REQUIREMENTS.items():
            if res_pattern in resource.lower():
                required_level = max(required_level, level)

        if role_level < required_level:
            return self._deny(
                f"Insufficient access level for {resource} (role: {role})",
                f"Request elevated access or contact administrator",
            )

        return self._allow(f"Access granted to {resource}")


class DataClassificationPolicy(Policy):
    """Enforce data classification and handling requirements."""

    # Classification levels
    CLASSIFICATIONS = {
        "public": {"encrypt": False, "audit": False, "external_ok": True},
        "internal": {"encrypt": False, "audit": True, "external_ok": False},
        "confidential": {"encrypt": True, "audit": True, "external_ok": False},
        "secret": {"encrypt": True, "audit": True, "external_ok": False, "mfa_required": True},
        "restricted": {"encrypt": True, "audit": True, "external_ok": False, "mfa_required": True, "approval_required": True},
    }

    def __init__(self):
        super().__init__(
            policy_id="SEC-002",
            name="Data Classification Policy",
            category=PolicyCategory.DATA_CLASSIFICATION,
            severity=PolicySeverity.HIGH,
            description="Enforces data handling based on classification",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate data classification requirements."""
        classification = payload.get("classification", "internal")
        is_encrypted = payload.get("encrypted", False)
        is_external = payload.get("external", False) or context.get("external", False)
        has_mfa = context.get("mfa_verified", False)

        requirements = self.CLASSIFICATIONS.get(classification.lower(), self.CLASSIFICATIONS["internal"])

        # Check encryption requirement
        if requirements.get("encrypt") and not is_encrypted:
            return self._modify(
                f"{classification} data must be encrypted",
                {**payload, "encrypt_required": True},
                "Enable encryption before processing",
            )

        # Check external transfer
        if is_external and not requirements.get("external_ok"):
            return self._deny(
                f"{classification} data cannot be shared externally",
                "Request data reclassification or use approved external sharing method",
            )

        # Check MFA
        if requirements.get("mfa_required") and not has_mfa:
            return self._deny(
                f"Access to {classification} data requires MFA",
                "Complete MFA verification before accessing",
            )

        # Check approval
        if requirements.get("approval_required") and not payload.get("approved"):
            return self._escalate(
                f"Access to {classification} data requires prior approval",
                "Submit access request for approval",
            )

        return self._allow(f"Data handling compliant for {classification} classification")


class ChangeManagementPolicy(Policy):
    """Enforce change management (ITIL) requirements."""

    # Change categories
    CHANGE_CATEGORIES = {
        "standard": {"approval": None, "testing": False, "rollback": False},
        "normal": {"approval": "manager", "testing": True, "rollback": True},
        "major": {"approval": "cab", "testing": True, "rollback": True, "staging": True},
        "emergency": {"approval": "on_call", "testing": False, "rollback": True, "post_review": True},
    }

    def __init__(self):
        super().__init__(
            policy_id="SEC-003",
            name="Change Management Policy",
            category=PolicyCategory.CHANGE_MANAGEMENT,
            severity=PolicySeverity.MEDIUM,
            description="Enforces ITIL change management process",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate change management requirements."""
        if "change" not in action.lower() and "deploy" not in action.lower():
            return self._allow("Not a change action")

        change_type = payload.get("change_type", "normal")
        has_approval = payload.get("approved", False)
        has_testing = payload.get("tested", False)
        has_rollback = payload.get("rollback_plan", False)
        is_staging = context.get("environment") == "staging"

        requirements = self.CHANGE_CATEGORIES.get(change_type, self.CHANGE_CATEGORIES["normal"])

        # Check approval
        if requirements.get("approval") and not has_approval:
            approver = requirements["approval"]
            return self._escalate(
                f"{change_type.title()} change requires {approver} approval",
                f"Submit change request to {approver}",
            )

        # Check testing
        if requirements.get("testing") and not has_testing:
            return self._deny(
                f"{change_type.title()} change requires testing",
                "Complete testing before deployment",
            )

        # Check rollback plan
        if requirements.get("rollback") and not has_rollback:
            return self._deny(
                f"{change_type.title()} change requires rollback plan",
                "Document rollback procedure before deployment",
            )

        # Check staging for major changes
        if requirements.get("staging") and not is_staging:
            if context.get("environment") == "production":
                return self._deny(
                    "Major changes must be tested in staging first",
                    "Deploy to staging environment before production",
                )

        return self._allow(f"Change management requirements met for {change_type} change")


class IncidentResponsePolicy(Policy):
    """Enforce incident response procedures."""

    # Incident severity levels
    SEVERITY_REQUIREMENTS = {
        "critical": {"notify": ["security", "executives"], "max_response_minutes": 15},
        "high": {"notify": ["security", "manager"], "max_response_minutes": 60},
        "medium": {"notify": ["security"], "max_response_minutes": 240},
        "low": {"notify": [], "max_response_minutes": 1440},
    }

    def __init__(self):
        super().__init__(
            policy_id="SEC-004",
            name="Incident Response Policy",
            category=PolicyCategory.INCIDENT_RESPONSE,
            severity=PolicySeverity.CRITICAL,
            description="Enforces incident response procedures",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate incident response requirements."""
        if "incident" not in action.lower():
            return self._allow("Not an incident action")

        severity = payload.get("severity", "medium")
        notifications_sent = payload.get("notifications_sent", [])
        response_time_minutes = payload.get("response_time_minutes", 0)

        requirements = self.SEVERITY_REQUIREMENTS.get(severity, self.SEVERITY_REQUIREMENTS["medium"])

        # Check notification requirements
        required_notifications = requirements.get("notify", [])
        missing = [n for n in required_notifications if n not in notifications_sent]

        if missing:
            return self._modify(
                f"Missing required notifications for {severity} incident: {missing}",
                {**payload, "additional_notifications": missing},
                f"Notify: {', '.join(missing)}",
            )

        # Check response time
        max_response = requirements.get("max_response_minutes", 60)
        if response_time_minutes > max_response:
            return self._warn(
                f"Response time ({response_time_minutes}min) exceeds SLA ({max_response}min)",
            )

        return self._allow(f"Incident response procedures followed for {severity} incident")


def get_security_policies() -> List[Policy]:
    """Get all security policies."""
    return [
        AccessControlPolicy(),
        DataClassificationPolicy(),
        ChangeManagementPolicy(),
        IncidentResponsePolicy(),
    ]
