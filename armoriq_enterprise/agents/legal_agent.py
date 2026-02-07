"""
Legal Agent
===========
Handles contracts, NDAs, IP, litigation.
"""

from typing import Dict, Any
from .base_agent import EnterpriseAgent, AgentConfig, AgentCapability
from ..compliance.policies.base import PolicyCategory


class LegalAgent(EnterpriseAgent):
    """
    Legal domain agent.

    Capabilities:
    - Contract review and approval
    - NDA drafting and management
    - IP protection and checks
    - Litigation support
    """

    def __init__(self):
        config = AgentConfig(
            name="Legal",
            agent_type="legal",
            capabilities={
                AgentCapability.REVIEW_CONTRACT,
                AgentCapability.DRAFT_NDA,
                AgentCapability.CHECK_IP,
                AgentCapability.LITIGATION_SEARCH,
                AgentCapability.APPROVE_TERMS,
            },
            policy_categories=[
                PolicyCategory.CONTRACT_REVIEW,
                PolicyCategory.NDA_ENFORCEMENT,
                PolicyCategory.IP_PROTECTION,
                PolicyCategory.LITIGATION_HOLD,
            ],
            description="Handles legal operations including contracts, NDAs, and IP",
        )
        super().__init__(config)

    async def _execute_action(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute legal action."""
        action_lower = action.lower()

        if "contract" in action_lower:
            return await self._review_contract(payload)
        elif "nda" in action_lower:
            return await self._handle_nda(payload)
        elif "ip" in action_lower:
            return await self._check_ip(payload)
        elif "litigation" in action_lower:
            return await self._litigation_search(payload)
        elif "terms" in action_lower or "approve" in action_lower:
            return await self._approve_terms(payload)
        else:
            return {"status": "completed", "action": action}

    async def _review_contract(self, payload: Dict) -> Dict:
        """Review a contract."""
        contract_type = payload.get("type", "standard")
        value = payload.get("value", 0)
        counterparty = payload.get("counterparty", "unknown")

        # Determine review level
        if value > 100000:
            review_level = "senior_counsel"
        elif value > 50000:
            review_level = "legal_review"
        else:
            review_level = "standard_review"

        return {
            "status": "reviewed",
            "contract_id": f"CON-{self._action_count:06d}",
            "type": contract_type,
            "value": value,
            "counterparty": counterparty,
            "review_level": review_level,
            "risk_flags": [],
            "recommended_changes": [],
        }

    async def _handle_nda(self, payload: Dict) -> Dict:
        """Handle NDA operations."""
        operation = payload.get("operation", "draft")
        counterparty = payload.get("counterparty", "unknown")
        nda_type = payload.get("type", "mutual")

        return {
            "status": "completed",
            "nda_id": f"NDA-{self._action_count:06d}",
            "operation": operation,
            "counterparty": counterparty,
            "type": nda_type,
            "template_used": f"{nda_type}_standard",
        }

    async def _check_ip(self, payload: Dict) -> Dict:
        """Check IP-related matters."""
        ip_type = payload.get("type", "patent")
        subject = payload.get("subject", "")

        return {
            "status": "checked",
            "ip_check_id": f"IP-{self._action_count:04d}",
            "type": ip_type,
            "subject": subject,
            "conflicts_found": [],
            "clearance_status": "clear",
        }

    async def _litigation_search(self, payload: Dict) -> Dict:
        """Search for litigation-related information."""
        entity = payload.get("entity", "")
        jurisdiction = payload.get("jurisdiction", "all")

        return {
            "status": "completed",
            "search_id": f"LIT-{self._action_count:04d}",
            "entity": entity,
            "jurisdiction": jurisdiction,
            "cases_found": 0,
            "holds_active": False,
        }

    async def _approve_terms(self, payload: Dict) -> Dict:
        """Approve contract terms."""
        contract_id = payload.get("contract_id", "")
        terms = payload.get("terms", [])

        return {
            "status": "approved",
            "contract_id": contract_id,
            "terms_reviewed": len(terms),
            "approval_id": f"APR-{self._action_count:04d}",
        }
