"""
Procurement Agent
=================
Handles vendors, purchases, bids, inventory.
"""

from typing import Dict, Any, Set
from .base_agent import EnterpriseAgent, AgentConfig, AgentCapability
from ..compliance.policies.base import PolicyCategory


class ProcurementAgent(EnterpriseAgent):
    """
    Procurement domain agent.

    Capabilities:
    - Vendor approval and management
    - Purchase order creation
    - Bid management
    - Inventory tracking
    """

    def __init__(self):
        config = AgentConfig(
            name="Procurement",
            agent_type="procurement",
            capabilities={
                AgentCapability.APPROVE_VENDOR,
                AgentCapability.CREATE_PO,
                AgentCapability.MANAGE_BID,
                AgentCapability.INVENTORY_CHECK,
                AgentCapability.RECEIVE_GOODS,
            },
            policy_categories=[
                PolicyCategory.VENDOR_APPROVAL,
                PolicyCategory.SPENDING_LIMITS,
                PolicyCategory.BID_REQUIREMENTS,
            ],
            description="Handles procurement operations including vendors, POs, and inventory",
        )
        super().__init__(config)

        # Approved vendors registry
        self._approved_vendors: Set[str] = set()
        self._preferred_vendors: Set[str] = set()

    def approve_vendor(self, vendor_id: str, preferred: bool = False):
        """Add a vendor to approved list."""
        self._approved_vendors.add(vendor_id)
        if preferred:
            self._preferred_vendors.add(vendor_id)

    async def _execute_action(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute procurement action."""
        action_lower = action.lower()

        if "vendor" in action_lower:
            return await self._handle_vendor(payload)
        elif "po" in action_lower or "purchase" in action_lower:
            return await self._create_po(payload)
        elif "bid" in action_lower or "rfp" in action_lower:
            return await self._manage_bid(payload)
        elif "inventory" in action_lower:
            return await self._check_inventory(payload)
        elif "receive" in action_lower or "goods" in action_lower:
            return await self._receive_goods(payload)
        else:
            return {"status": "completed", "action": action}

    async def _handle_vendor(self, payload: Dict) -> Dict:
        """Handle vendor operations."""
        operation = payload.get("operation", "check")
        vendor_id = payload.get("vendor_id", "")
        vendor_name = payload.get("name", "")

        if operation == "approve":
            self._approved_vendors.add(vendor_id)
            return {
                "status": "approved",
                "vendor_id": vendor_id,
                "name": vendor_name,
                "approval_id": f"VND-{self._action_count:06d}",
            }
        elif operation == "check":
            is_approved = vendor_id in self._approved_vendors
            is_preferred = vendor_id in self._preferred_vendors
            return {
                "status": "checked",
                "vendor_id": vendor_id,
                "is_approved": is_approved,
                "is_preferred": is_preferred,
            }
        else:
            return {"status": "completed", "operation": operation}

    async def _create_po(self, payload: Dict) -> Dict:
        """Create a purchase order."""
        vendor_id = payload.get("vendor_id", "")
        items = payload.get("items", [])
        total_amount = payload.get("amount", 0)

        # Check vendor approval
        vendor_approved = vendor_id in self._approved_vendors

        return {
            "status": "created" if vendor_approved else "pending_vendor_approval",
            "po_id": f"PO-{self._action_count:06d}",
            "vendor_id": vendor_id,
            "vendor_approved": vendor_approved,
            "items": len(items),
            "total_amount": total_amount,
            "requires_approval": total_amount > 5000,
        }

    async def _manage_bid(self, payload: Dict) -> Dict:
        """Manage bid/RFP."""
        operation = payload.get("operation", "create")
        bid_type = payload.get("type", "rfp")
        amount = payload.get("estimated_amount", 0)

        # Determine bid requirements
        if amount < 10000:
            requirement = "single_source"
        elif amount < 50000:
            requirement = "three_quotes"
        else:
            requirement = "formal_rfp"

        return {
            "status": "created",
            "bid_id": f"BID-{self._action_count:06d}",
            "type": bid_type,
            "operation": operation,
            "estimated_amount": amount,
            "requirement": requirement,
            "vendors_invited": 0,
        }

    async def _check_inventory(self, payload: Dict) -> Dict:
        """Check inventory levels."""
        item_id = payload.get("item_id", "")
        location = payload.get("location", "main_warehouse")

        return {
            "status": "checked",
            "item_id": item_id,
            "location": location,
            "quantity_on_hand": 100,
            "quantity_reserved": 20,
            "quantity_available": 80,
            "reorder_point": 50,
            "needs_reorder": False,
        }

    async def _receive_goods(self, payload: Dict) -> Dict:
        """Receive goods against a PO."""
        po_id = payload.get("po_id", "")
        items_received = payload.get("items", [])

        return {
            "status": "received",
            "receipt_id": f"RCV-{self._action_count:06d}",
            "po_id": po_id,
            "items_received": len(items_received),
            "inventory_updated": True,
            "inspection_required": False,
        }
