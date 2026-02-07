"""
IT Agent
========
Handles access control, security, incidents, assets.
"""

from typing import Dict, Any
from .base_agent import EnterpriseAgent, AgentConfig, AgentCapability
from ..compliance.policies.base import PolicyCategory


class ITAgent(EnterpriseAgent):
    """
    IT/Security domain agent.

    Capabilities:
    - Access provisioning and revocation
    - Incident management
    - Change management
    - Asset management
    """

    def __init__(self):
        config = AgentConfig(
            name="IT",
            agent_type="it",
            capabilities={
                AgentCapability.PROVISION_ACCESS,
                AgentCapability.REVOKE_ACCESS,
                AgentCapability.CREATE_TICKET,
                AgentCapability.RESOLVE_INCIDENT,
                AgentCapability.DEPLOY_CHANGE,
                AgentCapability.ASSET_MANAGEMENT,
            },
            policy_categories=[
                PolicyCategory.ACCESS_CONTROL,
                PolicyCategory.DATA_CLASSIFICATION,
                PolicyCategory.CHANGE_MANAGEMENT,
                PolicyCategory.INCIDENT_RESPONSE,
            ],
            description="Handles IT operations including access, security, and incidents",
        )
        super().__init__(config)

    async def _execute_action(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute IT action."""
        action_lower = action.lower()

        if "provision" in action_lower or "access" in action_lower:
            if "revoke" in action_lower:
                return await self._revoke_access(payload)
            return await self._provision_access(payload)
        elif "ticket" in action_lower:
            return await self._create_ticket(payload)
        elif "incident" in action_lower:
            return await self._handle_incident(payload)
        elif "change" in action_lower or "deploy" in action_lower:
            return await self._deploy_change(payload)
        elif "asset" in action_lower:
            return await self._manage_asset(payload)
        else:
            return {"status": "completed", "action": action}

    async def _provision_access(self, payload: Dict) -> Dict:
        """Provision access for a user."""
        user_id = payload.get("user_id", "")
        resources = payload.get("resources", [])
        role = payload.get("role", "standard")

        return {
            "status": "provisioned",
            "access_request_id": f"ACC-{self._action_count:06d}",
            "user_id": user_id,
            "role": role,
            "resources_granted": resources,
            "expiry": payload.get("expiry", "never"),
        }

    async def _revoke_access(self, payload: Dict) -> Dict:
        """Revoke access for a user."""
        user_id = payload.get("user_id", "")
        resources = payload.get("resources", [])
        reason = payload.get("reason", "")

        return {
            "status": "revoked",
            "revocation_id": f"REV-{self._action_count:06d}",
            "user_id": user_id,
            "resources_revoked": resources,
            "reason": reason,
            "immediate": True,
        }

    async def _create_ticket(self, payload: Dict) -> Dict:
        """Create a support ticket."""
        ticket_type = payload.get("type", "incident")
        priority = payload.get("priority", "medium")
        description = payload.get("description", "")

        return {
            "status": "created",
            "ticket_id": f"TKT-{self._action_count:06d}",
            "type": ticket_type,
            "priority": priority,
            "description": description[:200],
            "assigned_to": "L1_support",
        }

    async def _handle_incident(self, payload: Dict) -> Dict:
        """Handle a security incident."""
        incident_type = payload.get("type", "unknown")
        severity = payload.get("severity", "medium")
        affected_systems = payload.get("affected_systems", [])

        return {
            "status": "handling",
            "incident_id": f"INC-{self._action_count:06d}",
            "type": incident_type,
            "severity": severity,
            "affected_systems": affected_systems,
            "containment_status": "in_progress",
            "notifications_sent": ["security_team"],
        }

    async def _deploy_change(self, payload: Dict) -> Dict:
        """Deploy a change."""
        change_type = payload.get("type", "normal")
        environment = payload.get("environment", "staging")
        change_description = payload.get("description", "")

        return {
            "status": "deployed",
            "change_id": f"CHG-{self._action_count:06d}",
            "type": change_type,
            "environment": environment,
            "description": change_description[:200],
            "rollback_available": True,
        }

    async def _manage_asset(self, payload: Dict) -> Dict:
        """Manage IT asset."""
        operation = payload.get("operation", "check")
        asset_id = payload.get("asset_id", "")
        asset_type = payload.get("type", "laptop")

        return {
            "status": "completed",
            "asset_id": asset_id or f"AST-{self._action_count:06d}",
            "operation": operation,
            "type": asset_type,
            "inventory_updated": True,
        }
