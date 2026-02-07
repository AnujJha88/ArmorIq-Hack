"""
Operations Agent
================
Handles incidents, changes, SLAs, maintenance.
"""

from typing import Dict, Any
from datetime import datetime
from .base_agent import EnterpriseAgent, AgentConfig, AgentCapability
from ..compliance.policies.base import PolicyCategory


class OperationsAgent(EnterpriseAgent):
    """
    Operations domain agent.

    Capabilities:
    - Incident management
    - Change management
    - SLA monitoring
    - Maintenance scheduling
    """

    SLA_DEFINITIONS = {
        "critical": {"response_minutes": 15, "resolution_hours": 4},
        "high": {"response_minutes": 60, "resolution_hours": 8},
        "medium": {"response_minutes": 240, "resolution_hours": 24},
        "low": {"response_minutes": 480, "resolution_hours": 72},
    }

    def __init__(self):
        config = AgentConfig(
            name="Operations",
            agent_type="operations",
            capabilities={
                AgentCapability.CREATE_INCIDENT,
                AgentCapability.MANAGE_CHANGE,
                AgentCapability.SLA_MONITORING,
                AgentCapability.SCHEDULE_MAINTENANCE,
            },
            policy_categories=[
                PolicyCategory.SLA_COMPLIANCE,
                PolicyCategory.ITIL_PROCESSES,
                PolicyCategory.CHANGE_MANAGEMENT,
            ],
            description="Handles operations including incidents, changes, and SLAs",
        )
        super().__init__(config)

    async def _execute_action(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute operations action."""
        action_lower = action.lower()

        if "incident" in action_lower:
            return await self._handle_incident(payload)
        elif "change" in action_lower:
            return await self._manage_change(payload)
        elif "sla" in action_lower:
            return await self._monitor_sla(payload)
        elif "maintenance" in action_lower:
            return await self._schedule_maintenance(payload)
        else:
            return {"status": "completed", "action": action}

    async def _handle_incident(self, payload: Dict) -> Dict:
        """Handle an incident."""
        operation = payload.get("operation", "create")
        priority = payload.get("priority", "medium")
        description = payload.get("description", "")
        affected_services = payload.get("affected_services", [])

        sla = self.SLA_DEFINITIONS.get(priority, self.SLA_DEFINITIONS["medium"])

        if operation == "create":
            return {
                "status": "created",
                "incident_id": f"INC-{self._action_count:06d}",
                "priority": priority,
                "description": description[:200],
                "affected_services": affected_services,
                "sla_response_minutes": sla["response_minutes"],
                "sla_resolution_hours": sla["resolution_hours"],
                "assigned_team": "L1_support",
                "created_at": datetime.now().isoformat(),
            }
        elif operation == "update":
            return {
                "status": "updated",
                "incident_id": payload.get("incident_id", ""),
                "update_type": payload.get("update_type", "status_change"),
                "new_status": payload.get("new_status", "in_progress"),
            }
        elif operation == "resolve":
            return {
                "status": "resolved",
                "incident_id": payload.get("incident_id", ""),
                "resolution": payload.get("resolution", ""),
                "resolved_at": datetime.now().isoformat(),
            }
        else:
            return {"status": "completed", "operation": operation}

    async def _manage_change(self, payload: Dict) -> Dict:
        """Manage a change request."""
        operation = payload.get("operation", "create")
        change_type = payload.get("type", "normal")
        risk_level = payload.get("risk_level", "medium")
        description = payload.get("description", "")

        if operation == "create":
            # Determine approvals needed
            if change_type == "emergency":
                approvals_needed = ["on_call_manager"]
            elif risk_level == "high":
                approvals_needed = ["change_manager", "cab"]
            else:
                approvals_needed = ["change_manager"]

            return {
                "status": "created",
                "change_id": f"CHG-{self._action_count:06d}",
                "type": change_type,
                "risk_level": risk_level,
                "description": description[:200],
                "approvals_needed": approvals_needed,
                "testing_required": change_type != "emergency",
                "rollback_plan_required": True,
            }
        elif operation == "approve":
            return {
                "status": "approved",
                "change_id": payload.get("change_id", ""),
                "approved_by": payload.get("approver", ""),
                "approved_at": datetime.now().isoformat(),
            }
        elif operation == "implement":
            return {
                "status": "implemented",
                "change_id": payload.get("change_id", ""),
                "implementation_started": datetime.now().isoformat(),
                "environment": payload.get("environment", "production"),
            }
        else:
            return {"status": "completed", "operation": operation}

    async def _monitor_sla(self, payload: Dict) -> Dict:
        """Monitor SLA compliance."""
        service = payload.get("service", "all")
        period = payload.get("period", "current_month")

        return {
            "status": "checked",
            "service": service,
            "period": period,
            "sla_metrics": {
                "availability": 99.95,
                "response_time_avg_ms": 150,
                "incidents_within_sla": 98.5,
                "resolution_within_sla": 95.0,
            },
            "breaches": 2,
            "at_risk": 5,
            "compliant": True,
        }

    async def _schedule_maintenance(self, payload: Dict) -> Dict:
        """Schedule maintenance window."""
        systems = payload.get("systems", [])
        maintenance_type = payload.get("type", "routine")
        duration_hours = payload.get("duration_hours", 2)
        scheduled_time = payload.get("scheduled_time", "")

        # Determine if in maintenance window
        now = datetime.now()
        is_weekend = now.weekday() >= 5
        is_late_night = 2 <= now.hour < 6

        in_window = is_weekend or is_late_night

        return {
            "status": "scheduled",
            "maintenance_id": f"MNT-{self._action_count:06d}",
            "systems": systems,
            "type": maintenance_type,
            "duration_hours": duration_hours,
            "scheduled_time": scheduled_time,
            "in_maintenance_window": in_window,
            "notifications_sent": True,
            "change_record_created": True,
        }
