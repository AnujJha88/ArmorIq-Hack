"""
Operations Compliance Policies
==============================
SLA compliance, ITIL processes, maintenance windows.
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, time
from .base import (
    Policy, PolicyCategory, PolicyAction, PolicySeverity, PolicyResult,
)

logger = logging.getLogger("Compliance.Operations")


class SLACompliancePolicy(Policy):
    """Service Level Agreement compliance."""

    # SLA definitions by priority
    SLA_DEFINITIONS = {
        "critical": {"response_minutes": 15, "resolution_hours": 4},
        "high": {"response_minutes": 60, "resolution_hours": 8},
        "medium": {"response_minutes": 240, "resolution_hours": 24},
        "low": {"response_minutes": 480, "resolution_hours": 72},
    }

    def __init__(self):
        super().__init__(
            policy_id="OPS-001",
            name="SLA Compliance Policy",
            category=PolicyCategory.SLA_COMPLIANCE,
            severity=PolicySeverity.HIGH,
            description="Enforces SLA response and resolution times",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate SLA compliance."""
        if "ticket" not in action.lower() and "incident" not in action.lower():
            return self._allow("Not a ticket/incident action")

        priority = payload.get("priority", "medium")
        response_time = payload.get("response_time_minutes", 0)
        resolution_time = payload.get("resolution_time_hours")

        sla = self.SLA_DEFINITIONS.get(priority.lower(), self.SLA_DEFINITIONS["medium"])

        # Check response time
        if response_time > sla["response_minutes"]:
            return self._warn(
                f"Response time ({response_time}min) exceeds SLA ({sla['response_minutes']}min)",
            )

        # Check resolution time if provided
        if resolution_time is not None:
            try:
                if float(resolution_time) > sla["resolution_hours"]:
                    return self._warn(
                        f"Resolution time ({resolution_time}h) exceeds SLA ({sla['resolution_hours']}h)",
                    )
            except (TypeError, ValueError) as e:
                logger.warning(f"Resolution time validation failed: {e}, skipping SLA resolution check")

        return self._allow(f"SLA compliance met for {priority} priority")


class ITILProcessPolicy(Policy):
    """ITIL process compliance."""

    REQUIRED_FIELDS = {
        "incident": ["description", "priority", "category", "affected_users"],
        "change": ["description", "risk_level", "rollback_plan", "testing_status"],
        "problem": ["description", "root_cause_analysis", "related_incidents"],
        "service_request": ["description", "requester", "approval_status"],
    }

    def __init__(self):
        super().__init__(
            policy_id="OPS-002",
            name="ITIL Process Policy",
            category=PolicyCategory.ITIL_PROCESSES,
            severity=PolicySeverity.MEDIUM,
            description="Enforces ITIL process documentation requirements",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate ITIL process requirements."""
        # Determine record type
        record_type = None
        for rt in self.REQUIRED_FIELDS.keys():
            if rt in action.lower():
                record_type = rt
                break

        if not record_type:
            return self._allow("Not an ITIL record action")

        required = self.REQUIRED_FIELDS[record_type]
        missing = [f for f in required if not payload.get(f)]

        if missing:
            return self._deny(
                f"{record_type.title()} record missing required fields: {missing}",
                f"Provide: {', '.join(missing)}",
            )

        # Check for proper categorization
        if record_type == "incident":
            category = payload.get("category", "")
            valid_categories = ["hardware", "software", "network", "security", "access", "other"]
            if category.lower() not in valid_categories:
                return self._modify(
                    f"Invalid category: {category}",
                    {**payload, "category": "other"},
                    f"Use valid category: {', '.join(valid_categories)}",
                )

        return self._allow(f"ITIL {record_type} requirements met")


class MaintenanceWindowPolicy(Policy):
    """Maintenance window enforcement."""

    # Standard maintenance windows (UTC hours)
    MAINTENANCE_WINDOWS = {
        "weekday": (2, 6),   # 2 AM - 6 AM UTC
        "weekend": (0, 8),   # Midnight - 8 AM UTC
    }

    def __init__(self):
        super().__init__(
            policy_id="OPS-003",
            name="Maintenance Window Policy",
            category=PolicyCategory.SLA_COMPLIANCE,
            severity=PolicySeverity.MEDIUM,
            description="Enforces maintenance window restrictions",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate maintenance window requirements."""
        maintenance_actions = ["maintenance", "upgrade", "patch", "restart", "reboot"]
        if not any(ma in action.lower() for ma in maintenance_actions):
            return self._allow("Not a maintenance action")

        environment = context.get("environment", "production")
        is_emergency = payload.get("emergency", False)

        # Non-production doesn't require maintenance window
        if environment != "production":
            return self._allow("Non-production environment")

        # Emergency maintenance is allowed with documentation
        if is_emergency:
            if not payload.get("emergency_justification"):
                return self._escalate(
                    "Emergency maintenance requires justification",
                    "Provide emergency justification",
                )
            return self._warn("Emergency maintenance outside window - document post-incident")

        # Check if within maintenance window
        now = datetime.now()
        is_weekend = now.weekday() >= 5
        window_type = "weekend" if is_weekend else "weekday"
        window_start, window_end = self.MAINTENANCE_WINDOWS[window_type]

        current_hour = now.hour
        in_window = window_start <= current_hour < window_end

        if not in_window:
            return self._deny(
                f"Maintenance only allowed during window ({window_start}:00-{window_end}:00 UTC)",
                f"Schedule for {window_type} maintenance window or request emergency exception",
            )

        return self._allow("Within maintenance window")


class CapacityManagementPolicy(Policy):
    """Capacity and resource management."""

    # Thresholds
    WARNING_THRESHOLD = 0.75
    CRITICAL_THRESHOLD = 0.90

    def __init__(self):
        super().__init__(
            policy_id="OPS-004",
            name="Capacity Management Policy",
            category=PolicyCategory.SLA_COMPLIANCE,
            severity=PolicySeverity.MEDIUM,
            description="Monitors and enforces capacity limits",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate capacity requirements."""
        if "provision" not in action.lower() and "allocate" not in action.lower():
            return self._allow("Not a provisioning action")

        requested = payload.get("resources_requested", {})
        available = payload.get("resources_available", {})

        for resource, amount in requested.items():
            if resource not in available:
                continue

            try:
                usage = float(amount) / float(available[resource])
            except (TypeError, ValueError, ZeroDivisionError):
                continue

            if usage > self.CRITICAL_THRESHOLD:
                return self._deny(
                    f"Resource {resource} would exceed critical threshold ({usage:.1%} of capacity)",
                    "Request fewer resources or increase capacity",
                )

            if usage > self.WARNING_THRESHOLD:
                return self._warn(
                    f"Resource {resource} nearing capacity ({usage:.1%})",
                )

        return self._allow("Resource allocation within capacity")


def get_operations_policies() -> List[Policy]:
    """Get all operations policies."""
    return [
        SLACompliancePolicy(),
        ITILProcessPolicy(),
        MaintenanceWindowPolicy(),
        CapacityManagementPolicy(),
    ]
