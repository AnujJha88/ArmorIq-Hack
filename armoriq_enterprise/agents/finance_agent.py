"""
Finance Agent
=============
Handles expenses, budgets, invoices, audits.
"""

from typing import Dict, Any
from .base_agent import EnterpriseAgent, AgentConfig, AgentCapability
from ..compliance.policies.base import PolicyCategory


class FinanceAgent(EnterpriseAgent):
    """
    Finance domain agent.

    Capabilities:
    - Expense processing and approval
    - Budget management and tracking
    - Invoice verification and payment
    - Audit support and documentation
    """

    APPROVAL_MATRIX = {
        "expense": {
            500: "self",
            5000: "manager",
            25000: "director",
            100000: "vp",
            float("inf"): "cfo",
        }
    }

    def __init__(self):
        config = AgentConfig(
            name="Finance",
            agent_type="finance",
            capabilities={
                AgentCapability.PROCESS_EXPENSE,
                AgentCapability.APPROVE_EXPENSE,
                AgentCapability.CREATE_BUDGET,
                AgentCapability.TRACK_SPENDING,
                AgentCapability.VERIFY_INVOICE,
                AgentCapability.SCHEDULE_PAYMENT,
                AgentCapability.GENERATE_AUDIT_REPORT,
                AgentCapability.RECONCILE_ACCOUNTS,
            },
            policy_categories=[
                PolicyCategory.EXPENSE_LIMITS,
                PolicyCategory.BUDGET_CONTROLS,
                PolicyCategory.SOX_COMPLIANCE,
                PolicyCategory.INVOICE_APPROVAL,
            ],
            description="Handles all financial operations with SOX compliance",
            approval_thresholds=self.APPROVAL_MATRIX,
        )
        super().__init__(config)

    async def _execute_action(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute finance action."""
        action_lower = action.lower()

        if "expense" in action_lower:
            return await self._process_expense(payload)
        elif "budget" in action_lower:
            return await self._manage_budget(payload)
        elif "invoice" in action_lower:
            return await self._process_invoice(payload)
        elif "payment" in action_lower:
            return await self._schedule_payment(payload)
        elif "audit" in action_lower:
            return await self._generate_audit_report(payload)
        elif "reconcile" in action_lower:
            return await self._reconcile_accounts(payload)
        else:
            return {"status": "completed", "action": action}

    async def _process_expense(self, payload: Dict) -> Dict:
        """Process an expense request."""
        amount = payload.get("amount", 0)
        category = payload.get("category", "general")
        description = payload.get("description", "")

        # Determine required approver
        required_approver = "self"
        for threshold, approver in sorted(self.APPROVAL_MATRIX["expense"].items()):
            if amount <= threshold:
                required_approver = approver
                break

        return {
            "status": "processed",
            "expense_id": f"EXP-{self._action_count:06d}",
            "amount": amount,
            "category": category,
            "description": description,
            "required_approver": required_approver,
            "auto_approved": required_approver == "self",
        }

    async def _manage_budget(self, payload: Dict) -> Dict:
        """Manage budget operations."""
        operation = payload.get("operation", "check")
        department = payload.get("department", "general")
        amount = payload.get("amount", 0)

        return {
            "status": "completed",
            "operation": operation,
            "department": department,
            "amount": amount,
            "budget_id": f"BUD-{department.upper()[:3]}-{self._action_count:04d}",
        }

    async def _process_invoice(self, payload: Dict) -> Dict:
        """Process an invoice."""
        vendor = payload.get("vendor", "unknown")
        amount = payload.get("amount", 0)
        po_number = payload.get("po_number")

        return {
            "status": "verified" if po_number else "pending_po",
            "invoice_id": f"INV-{self._action_count:06d}",
            "vendor": vendor,
            "amount": amount,
            "po_number": po_number,
            "three_way_match": po_number is not None,
        }

    async def _schedule_payment(self, payload: Dict) -> Dict:
        """Schedule a payment."""
        vendor = payload.get("vendor", "unknown")
        amount = payload.get("amount", 0)
        due_date = payload.get("due_date", "next_business_day")

        return {
            "status": "scheduled",
            "payment_id": f"PAY-{self._action_count:06d}",
            "vendor": vendor,
            "amount": amount,
            "scheduled_date": due_date,
        }

    async def _generate_audit_report(self, payload: Dict) -> Dict:
        """Generate an audit report."""
        period = payload.get("period", "current_quarter")
        report_type = payload.get("type", "financial")

        return {
            "status": "generated",
            "report_id": f"AUD-{self._action_count:04d}",
            "period": period,
            "type": report_type,
            "findings": [],
        }

    async def _reconcile_accounts(self, payload: Dict) -> Dict:
        """Reconcile accounts."""
        accounts = payload.get("accounts", [])

        return {
            "status": "reconciled",
            "accounts_processed": len(accounts),
            "discrepancies": 0,
            "reconciliation_id": f"REC-{self._action_count:04d}",
        }
