"""
HR Compliance Policies
======================
IRCA, FCRA, EEOC, hiring, compensation, termination.
"""

from typing import Dict, Any, List
from datetime import datetime
from .base import (
    Policy, PolicyCategory, PolicyAction, PolicySeverity, PolicyResult,
)


class HiringCompliancePolicy(Policy):
    """I-9 and hiring compliance (IRCA)."""

    def __init__(self):
        super().__init__(
            policy_id="HR-001",
            name="Hiring Compliance Policy",
            category=PolicyCategory.HIRING_COMPLIANCE,
            severity=PolicySeverity.CRITICAL,
            description="Enforces I-9 and hiring compliance requirements",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate hiring compliance requirements."""
        hiring_actions = ["hire", "onboard", "start_employment", "offer"]
        if not any(ha in action.lower() for ha in hiring_actions):
            return self._allow("Not a hiring action")

        i9_status = payload.get("i9_status")
        background_check = payload.get("background_check_complete", False)
        offer_letter_signed = payload.get("offer_signed", False)

        # I-9 must be verified
        if i9_status not in ["verified", "pending_reverification"]:
            return self._deny(
                "Cannot complete hire without I-9 verification (IRCA requirement)",
                "Complete I-9 verification before start date",
            )

        # Background check for certain roles
        role_type = payload.get("role_type", "standard")
        if role_type in ["finance", "security", "executive"] and not background_check:
            return self._deny(
                f"Background check required for {role_type} roles (FCRA)",
                "Complete background check before hire",
            )

        if not offer_letter_signed:
            return self._escalate(
                "Offer letter must be signed before onboarding",
                "Obtain signed offer letter",
            )

        return self._allow("Hiring compliance requirements met")


class CompensationPolicy(Policy):
    """Compensation band and equity compliance."""

    # Salary bands by level (example)
    SALARY_BANDS = {
        "L1": (50000, 75000),
        "L2": (65000, 95000),
        "L3": (85000, 125000),
        "L4": (110000, 165000),
        "L5": (145000, 210000),
        "L6": (180000, 280000),
        "L7": (230000, 380000),
    }

    def __init__(self):
        super().__init__(
            policy_id="HR-002",
            name="Compensation Policy",
            category=PolicyCategory.COMPENSATION,
            severity=PolicySeverity.HIGH,
            description="Enforces salary bands and compensation equity",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate compensation requirements."""
        comp_actions = ["salary", "compensation", "offer", "raise", "adjustment"]
        if not any(ca in action.lower() for ca in comp_actions):
            return self._allow("Not a compensation action")

        salary = payload.get("salary") or payload.get("amount")
        level = payload.get("level", "L3")

        try:
            salary = float(salary)
        except (TypeError, ValueError):
            return self._allow("No salary specified")

        # Get band for level
        band = self.SALARY_BANDS.get(level, (0, float("inf")))
        min_salary, max_salary = band

        if salary < min_salary:
            return self._warn(
                f"Salary ${salary:,.0f} below band minimum for {level} (${min_salary:,.0f})",
            )

        if salary > max_salary:
            return self._escalate(
                f"Salary ${salary:,.0f} exceeds band maximum for {level} (${max_salary:,.0f})",
                "Requires VP/HR approval for above-band compensation",
            )

        # Check for large increases
        current_salary = payload.get("current_salary", 0)
        if current_salary:
            try:
                increase_pct = (salary - float(current_salary)) / float(current_salary) * 100
                if increase_pct > 20:
                    return self._escalate(
                        f"Salary increase of {increase_pct:.1f}% exceeds 20% threshold",
                        "Requires executive approval for large increases",
                    )
            except (TypeError, ValueError, ZeroDivisionError):
                pass

        return self._allow(f"Compensation within {level} band (${min_salary:,}-${max_salary:,})")


class TerminationPolicy(Policy):
    """Termination compliance and documentation."""

    def __init__(self):
        super().__init__(
            policy_id="HR-003",
            name="Termination Policy",
            category=PolicyCategory.TERMINATION,
            severity=PolicySeverity.HIGH,
            description="Enforces termination documentation and process",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate termination requirements."""
        if "terminate" not in action.lower() and "offboard" not in action.lower():
            return self._allow("Not a termination action")

        termination_type = payload.get("type", "voluntary")
        documentation = payload.get("documentation", [])
        hr_reviewed = payload.get("hr_reviewed", False)
        legal_reviewed = payload.get("legal_reviewed", False)

        # Involuntary terminations need more scrutiny
        if termination_type == "involuntary":
            required_docs = ["performance_records", "warnings", "pip"]
            missing_docs = [d for d in required_docs if d not in documentation]

            if missing_docs:
                return self._deny(
                    f"Involuntary termination requires documentation: {missing_docs}",
                    f"Provide: {', '.join(missing_docs)}",
                )

            if not legal_reviewed:
                return self._escalate(
                    "Involuntary terminations require legal review",
                    "Submit to legal for review before proceeding",
                )

        if not hr_reviewed:
            return self._escalate(
                "All terminations require HR review",
                "Submit to HR for review",
            )

        # Check for protected class concerns
        if payload.get("protected_class_flag"):
            return self._deny(
                "Termination flagged for protected class review",
                "Requires additional HR and legal review",
            )

        return self._allow("Termination compliance requirements met")


class LeaveManagementPolicy(Policy):
    """Leave and PTO compliance."""

    def __init__(self):
        super().__init__(
            policy_id="HR-004",
            name="Leave Management Policy",
            category=PolicyCategory.LEAVE_MANAGEMENT,
            severity=PolicySeverity.MEDIUM,
            description="Enforces leave policies and FMLA compliance",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate leave management requirements."""
        if "leave" not in action.lower() and "pto" not in action.lower():
            return self._allow("Not a leave action")

        leave_type = payload.get("type", "pto")
        days_requested = payload.get("days", 0)
        balance = payload.get("balance", 0)
        is_fmla = payload.get("fmla", False)

        # FMLA requests have special handling
        if is_fmla:
            if not payload.get("fmla_certified"):
                return self._escalate(
                    "FMLA leave requires certification",
                    "Submit FMLA certification documentation",
                )
            return self._allow("FMLA leave request - protected leave")

        # Check balance
        try:
            if float(days_requested) > float(balance):
                return self._deny(
                    f"Insufficient leave balance ({balance} days available, {days_requested} requested)",
                    "Request fewer days or apply for unpaid leave",
                )
        except (TypeError, ValueError):
            pass

        # Long leaves need manager approval
        try:
            if float(days_requested) > 10:
                if not payload.get("manager_approved"):
                    return self._escalate(
                        f"Leave over 10 days requires manager approval",
                        "Submit for manager approval",
                    )
        except (TypeError, ValueError):
            pass

        return self._allow("Leave request compliant")


def get_hr_policies() -> List[Policy]:
    """Get all HR policies."""
    return [
        HiringCompliancePolicy(),
        CompensationPolicy(),
        TerminationPolicy(),
        LeaveManagementPolicy(),
    ]
