"""
Procurement Compliance Policies
===============================
Vendor approval, spending limits, bid requirements.
"""

import logging
from typing import Dict, Any, List, Set
from .base import (
    Policy, PolicyCategory, PolicyAction, PolicySeverity, PolicyResult,
)

logger = logging.getLogger("Compliance.Procurement")


class VendorApprovalPolicy(Policy):
    """Vendor approval and onboarding requirements."""

    def __init__(self):
        super().__init__(
            policy_id="PROC-001",
            name="Vendor Approval Policy",
            category=PolicyCategory.VENDOR_APPROVAL,
            severity=PolicySeverity.HIGH,
            description="Enforces vendor approval and due diligence requirements",
        )
        self._approved_vendors: Set[str] = set()
        self._preferred_vendors: Set[str] = set()

    def approve_vendor(self, vendor_id: str, preferred: bool = False):
        """Add vendor to approved list."""
        self._approved_vendors.add(vendor_id)
        if preferred:
            self._preferred_vendors.add(vendor_id)

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate vendor requirements."""
        vendor_actions = ["vendor", "supplier", "purchase", "order"]
        if not any(va in action.lower() for va in vendor_actions):
            return self._allow("Not a vendor action")

        vendor_id = payload.get("vendor_id") or payload.get("supplier")
        amount = payload.get("amount", 0)

        if not vendor_id:
            return self._warn("No vendor specified")

        # Check if vendor is approved
        if vendor_id not in self._approved_vendors:
            # New vendor onboarding
            has_w9 = payload.get("w9_on_file", False)
            has_insurance = payload.get("insurance_verified", False)
            has_contract = payload.get("contract_signed", False)

            missing = []
            if not has_w9:
                missing.append("W-9")
            if not has_insurance:
                missing.append("insurance certificate")
            if not has_contract:
                missing.append("vendor agreement")

            if missing:
                return self._deny(
                    f"Vendor {vendor_id} not approved. Missing: {', '.join(missing)}",
                    "Complete vendor onboarding before placing orders",
                )

            return self._escalate(
                f"New vendor {vendor_id} requires procurement approval",
                "Submit vendor approval request",
            )

        # Check for preferred vendor on large purchases
        try:
            amount = float(amount)
            if amount > 10000 and vendor_id not in self._preferred_vendors:
                return self._warn(
                    f"Consider using preferred vendor for purchases over $10,000",
                )
        except (TypeError, ValueError) as e:
            logger.warning(f"Amount validation failed for vendor check: {e}, skipping preferred vendor check")

        return self._allow(f"Vendor {vendor_id} is approved")


class SpendingLimitsPolicy(Policy):
    """Purchase and spending limit controls."""

    SPENDING_LIMITS = {
        "employee": 500,
        "manager": 5000,
        "director": 25000,
        "vp": 100000,
        "cfo": 500000,
    }

    def __init__(self):
        super().__init__(
            policy_id="PROC-002",
            name="Spending Limits Policy",
            category=PolicyCategory.SPENDING_LIMITS,
            severity=PolicySeverity.HIGH,
            description="Enforces spending limits by role",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate spending limits."""
        spending_actions = ["purchase", "order", "spend", "buy"]
        if not any(sa in action.lower() for sa in spending_actions):
            return self._allow("Not a spending action")

        amount = payload.get("amount", 0)
        role = context.get("role", "employee")

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return self._allow("No amount specified")

        limit = self.SPENDING_LIMITS.get(role.lower(), 500)

        if amount > limit:
            # Find required approver
            required_role = None
            for r, l in sorted(self.SPENDING_LIMITS.items(), key=lambda x: x[1]):
                if l >= amount:
                    required_role = r
                    break

            if not required_role:
                required_role = "cfo"

            return self._escalate(
                f"Amount ${amount:,.2f} exceeds {role} limit (${limit:,.2f})",
                f"Requires {required_role} approval",
            )

        return self._allow(f"Amount ${amount:,.2f} within {role} limit (${limit:,.2f})")


class BidRequirementsPolicy(Policy):
    """Competitive bidding requirements."""

    BID_THRESHOLDS = {
        "single_source": 10000,  # Up to $10k - single source OK
        "three_quotes": 50000,   # $10k-$50k - 3 quotes required
        "formal_rfp": 100000,    # $50k-$100k - formal RFP
        "public_bid": float("inf"),  # $100k+ - public bid (if applicable)
    }

    def __init__(self):
        super().__init__(
            policy_id="PROC-003",
            name="Bid Requirements Policy",
            category=PolicyCategory.BID_REQUIREMENTS,
            severity=PolicySeverity.MEDIUM,
            description="Enforces competitive bidding requirements",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate bidding requirements."""
        if "purchase" not in action.lower() and "contract" not in action.lower():
            return self._allow("Not a purchase action")

        amount = payload.get("amount", 0)
        num_quotes = payload.get("quotes_received", 0)
        has_rfp = payload.get("rfp_complete", False)
        sole_source_justification = payload.get("sole_source_justification")

        try:
            amount = float(amount)
        except (TypeError, ValueError):
            return self._allow("No amount specified")

        # Single source threshold
        if amount <= 10000:
            return self._allow("Amount under single source threshold")

        # Three quotes threshold
        if amount <= 50000:
            if num_quotes < 3 and not sole_source_justification:
                return self._deny(
                    f"Purchases $10,000-$50,000 require 3 quotes ({num_quotes} received)",
                    "Obtain additional quotes or provide sole source justification",
                )
            return self._allow("Competitive quotes requirement met")

        # Formal RFP threshold
        if amount <= 100000:
            if not has_rfp:
                return self._deny(
                    f"Purchases $50,000-$100,000 require formal RFP",
                    "Complete RFP process before awarding contract",
                )
            return self._allow("RFP requirement met")

        # Large purchases
        if not has_rfp:
            return self._deny(
                f"Purchases over $100,000 require formal RFP and competitive process",
                "Complete full procurement process",
            )

        return self._allow("Procurement requirements met")


def get_procurement_policies() -> List[Policy]:
    """Get all procurement policies."""
    return [
        VendorApprovalPolicy(),
        SpendingLimitsPolicy(),
        BidRequirementsPolicy(),
    ]
