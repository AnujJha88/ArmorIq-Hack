"""
Financial Compliance Policies
=============================
SOX, expense limits, approval chains, budget controls.
"""

from typing import Dict, Any, List
from .base import (
    Policy, PolicyCategory, PolicyAction, PolicySeverity, PolicyResult,
    ThresholdPolicy, RuleBasedPolicy
)


class ExpenseLimitPolicy(ThresholdPolicy):
    """Enforce expense limits with approval escalation."""

    # Approval matrix
    APPROVAL_MATRIX = {
        500: "self",
        5000: "manager",
        25000: "director",
        100000: "vp",
        float("inf"): "cfo",
    }

    def __init__(self):
        super().__init__(
            policy_id="FIN-001",
            name="Expense Limit Policy",
            category=PolicyCategory.EXPENSE_LIMITS,
            field="amount",
            warn_threshold=400,
            escalate_threshold=500,
            deny_threshold=None,  # Never deny, just escalate
            severity=PolicySeverity.MEDIUM,
            description="Enforces expense limits and approval requirements",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate expense with approval matrix."""
        if "expense" not in action.lower() and "reimbursement" not in action.lower():
            return self._allow("Not an expense action")

        amount = payload.get("amount", 0)
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return self._allow("No amount specified")

        # Determine required approver
        required_approver = None
        for threshold, approver in sorted(self.APPROVAL_MATRIX.items()):
            if amount <= threshold:
                required_approver = approver
                break

        if required_approver == "self":
            return self._allow(f"Expense ${amount:.2f} within self-approval limit")

        return self._escalate(
            f"Expense ${amount:.2f} requires {required_approver} approval",
            f"Submit to {required_approver} for approval",
        )


class SOXSeparationOfDutiesPolicy(Policy):
    """SOX compliance: separation of duties."""

    # Actions that cannot be performed by the same person
    INCOMPATIBLE_PAIRS = [
        ("create_invoice", "approve_invoice"),
        ("create_payment", "approve_payment"),
        ("create_vendor", "approve_vendor"),
        ("request_expense", "approve_expense"),
        ("modify_ledger", "approve_modification"),
    ]

    def __init__(self):
        super().__init__(
            policy_id="FIN-002",
            name="SOX Separation of Duties",
            category=PolicyCategory.SOX_COMPLIANCE,
            severity=PolicySeverity.CRITICAL,
            description="Enforces SOX separation of duties requirements",
        )
        self._action_history: Dict[str, str] = {}  # object_id -> last_actor

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Check for separation of duties violations."""
        object_id = payload.get("object_id") or payload.get("id")
        current_actor = context.get("user_id") or context.get("agent_id")

        if not object_id or not current_actor:
            return self._allow("Cannot verify - missing object_id or actor")

        # Check for incompatible action pairs
        for action1, action2 in self.INCOMPATIBLE_PAIRS:
            if action1 in action.lower() or action2 in action.lower():
                history_key = f"{object_id}:{action1 if action1 in action.lower() else action2}"
                previous_actor = self._action_history.get(history_key)

                if previous_actor == current_actor:
                    return self._deny(
                        f"SOX violation: Same actor ({current_actor}) cannot perform both actions",
                        "Request must be processed by a different authorized person",
                    )

                # Record for future checks
                self._action_history[f"{object_id}:{action.lower()}"] = current_actor

        return self._allow("Separation of duties maintained")


class BudgetControlPolicy(Policy):
    """Enforce budget limits and controls."""

    def __init__(self):
        super().__init__(
            policy_id="FIN-003",
            name="Budget Control Policy",
            category=PolicyCategory.BUDGET_CONTROLS,
            severity=PolicySeverity.HIGH,
            description="Enforces budget limits and prevents overspending",
        )
        self._budgets: Dict[str, float] = {}  # department -> remaining budget
        self._spent: Dict[str, float] = {}

    def set_budget(self, department: str, amount: float):
        """Set budget for a department."""
        self._budgets[department] = amount
        self._spent[department] = 0

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Check against department budget."""
        if "spend" not in action.lower() and "expense" not in action.lower():
            return self._allow("Not a spending action")

        department = payload.get("department") or context.get("department")
        amount = payload.get("amount", 0)

        if not department:
            return self._warn("No department specified for budget check")

        budget = self._budgets.get(department, float("inf"))
        spent = self._spent.get(department, 0)
        remaining = budget - spent

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return self._allow("No amount specified")

        if amount > remaining:
            return self._deny(
                f"Insufficient budget: ${amount:.2f} requested, ${remaining:.2f} remaining",
                f"Reduce amount to ${remaining:.2f} or request budget increase",
            )

        if amount > remaining * 0.8:
            return self._warn(
                f"Spending ${amount:.2f} will use >{80}% of remaining budget (${remaining:.2f})"
            )

        return self._allow(f"Within budget: ${remaining:.2f} remaining after this transaction")


class InvoiceApprovalPolicy(Policy):
    """Invoice approval workflow policy."""

    def __init__(self):
        super().__init__(
            policy_id="FIN-004",
            name="Invoice Approval Policy",
            category=PolicyCategory.INVOICE_APPROVAL,
            severity=PolicySeverity.MEDIUM,
            description="Enforces invoice approval requirements",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate invoice approval requirements."""
        if "invoice" not in action.lower():
            return self._allow("Not an invoice action")

        amount = payload.get("amount", 0)
        vendor_approved = payload.get("vendor_approved", False)
        po_number = payload.get("po_number")
        three_way_match = payload.get("three_way_match", False)

        # Check vendor approval
        if not vendor_approved:
            return self._deny(
                "Invoice from unapproved vendor",
                "Request vendor approval before processing invoice",
            )

        # Check PO for amounts over $1000
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = 0

        if amount > 1000 and not po_number:
            return self._deny(
                f"Invoice over $1,000 requires PO number",
                "Attach valid PO number to invoice",
            )

        # Check three-way match for amounts over $5000
        if amount > 5000 and not three_way_match:
            return self._escalate(
                f"Invoice over $5,000 requires three-way match verification",
                "Complete three-way match (PO, receipt, invoice) before approval",
            )

        return self._allow("Invoice meets approval requirements")


def get_financial_policies() -> List[Policy]:
    """Get all financial policies."""
    return [
        ExpenseLimitPolicy(),
        SOXSeparationOfDutiesPolicy(),
        BudgetControlPolicy(),
        InvoiceApprovalPolicy(),
    ]
