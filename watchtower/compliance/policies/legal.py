"""
Legal Compliance Policies
=========================
Contract review, NDA enforcement, IP protection, litigation hold.
"""

from typing import Dict, Any, List, Set
from datetime import datetime, timedelta
from .base import (
    Policy, PolicyCategory, PolicyAction, PolicySeverity, PolicyResult,
)


class ContractReviewPolicy(Policy):
    """Enforce contract review requirements."""

    # Thresholds for different review levels
    REVIEW_THRESHOLDS = {
        10000: "legal_review",
        50000: "senior_legal",
        100000: "general_counsel",
        500000: "ceo_approval",
    }

    def __init__(self):
        super().__init__(
            policy_id="LEG-001",
            name="Contract Review Policy",
            category=PolicyCategory.CONTRACT_REVIEW,
            severity=PolicySeverity.HIGH,
            description="Enforces contract review requirements based on value and type",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate contract review requirements."""
        if "contract" not in action.lower():
            return self._allow("Not a contract action")

        contract_value = payload.get("value", 0)
        contract_type = payload.get("type", "standard")
        has_legal_review = payload.get("legal_reviewed", False)
        terms_modified = payload.get("terms_modified", False)

        try:
            contract_value = float(contract_value)
        except (TypeError, ValueError):
            contract_value = 0

        # Determine required review level
        required_review = None
        for threshold, review_level in sorted(self.REVIEW_THRESHOLDS.items()):
            if contract_value <= threshold:
                required_review = review_level
                break
        if not required_review:
            required_review = "ceo_approval"

        # High-risk contract types always need senior review
        high_risk_types = ["licensing", "ip_transfer", "exclusivity", "indemnification"]
        if contract_type in high_risk_types:
            required_review = "general_counsel"

        # Modified terms always need review
        if terms_modified and not has_legal_review:
            return self._escalate(
                "Contract with modified terms requires legal review",
                f"Submit to {required_review} for review",
            )

        if contract_value > 10000 and not has_legal_review:
            return self._escalate(
                f"Contract value ${contract_value:,.2f} requires {required_review}",
                f"Submit to {required_review} before execution",
            )

        return self._allow("Contract review requirements met")


class NDAEnforcementPolicy(Policy):
    """Enforce NDA requirements for confidential information."""

    def __init__(self):
        super().__init__(
            policy_id="LEG-002",
            name="NDA Enforcement Policy",
            category=PolicyCategory.NDA_ENFORCEMENT,
            severity=PolicySeverity.CRITICAL,
            description="Prevents disclosure of confidential information without NDA",
        )
        self._nda_registry: Set[str] = set()  # Entities with active NDAs

    def register_nda(self, entity_id: str):
        """Register an entity as having an active NDA."""
        self._nda_registry.add(entity_id)

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Check NDA requirements for information sharing."""
        if "share" not in action.lower() and "disclose" not in action.lower() and "send" not in action.lower():
            return self._allow("Not a disclosure action")

        is_confidential = payload.get("confidential", False)
        recipient = payload.get("recipient") or payload.get("to")
        classification = payload.get("classification", "internal")

        if not is_confidential and classification not in ["confidential", "secret", "restricted"]:
            return self._allow("Not confidential information")

        if not recipient:
            return self._warn("No recipient specified for confidential disclosure")

        # Check if recipient has NDA
        if recipient not in self._nda_registry:
            return self._deny(
                f"Cannot disclose confidential information to {recipient} (no NDA on file)",
                f"Execute NDA with {recipient} before disclosure",
            )

        return self._allow(f"NDA verified for {recipient}")


class IPProtectionPolicy(Policy):
    """Protect intellectual property."""

    # Protected IP types
    PROTECTED_TYPES = ["source_code", "algorithm", "patent", "trade_secret", "design"]

    def __init__(self):
        super().__init__(
            policy_id="LEG-003",
            name="IP Protection Policy",
            category=PolicyCategory.IP_PROTECTION,
            severity=PolicySeverity.CRITICAL,
            description="Prevents unauthorized IP transfer or disclosure",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate IP protection requirements."""
        content_type = payload.get("content_type", "")
        is_external = payload.get("external", False) or "external" in context.get("recipient", "")

        # Check if IP type is protected
        is_protected = any(pt in content_type.lower() for pt in self.PROTECTED_TYPES)

        if not is_protected:
            return self._allow("Not protected IP content")

        # External transfer of protected IP
        if is_external:
            return self._deny(
                f"Cannot transfer protected IP ({content_type}) externally",
                "Request IP transfer approval from legal and executive team",
            )

        # Check for proper authorization
        authorization = payload.get("ip_authorization")
        if not authorization:
            return self._escalate(
                f"Protected IP access requires authorization",
                "Submit IP access request to legal department",
            )

        return self._allow("IP access authorized")


class LitigationHoldPolicy(Policy):
    """Enforce litigation hold requirements."""

    def __init__(self):
        super().__init__(
            policy_id="LEG-004",
            name="Litigation Hold Policy",
            category=PolicyCategory.LITIGATION_HOLD,
            severity=PolicySeverity.CRITICAL,
            description="Prevents destruction of data under litigation hold",
        )
        self._holds: Dict[str, Dict] = {}  # hold_id -> hold details

    def add_hold(self, hold_id: str, scope: Dict[str, Any]):
        """Add a litigation hold."""
        self._holds[hold_id] = {
            "scope": scope,
            "created_at": datetime.now(),
        }

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Check if action violates litigation hold."""
        # Only check destructive actions
        destructive_actions = ["delete", "destroy", "purge", "archive", "modify"]
        if not any(da in action.lower() for da in destructive_actions):
            return self._allow("Not a destructive action")

        # Check against all active holds
        for hold_id, hold in self._holds.items():
            scope = hold["scope"]

            # Check if payload matches hold scope
            if self._matches_hold(payload, scope):
                return self._deny(
                    f"Action blocked by litigation hold {hold_id}",
                    "Contact legal department for guidance on held data",
                )

        return self._allow("No litigation holds apply")

    def _matches_hold(self, payload: Dict, scope: Dict) -> bool:
        """Check if payload matches hold scope."""
        for key, value in scope.items():
            if key in payload:
                if isinstance(value, list):
                    if payload[key] in value:
                        return True
                elif payload[key] == value:
                    return True
        return False


def get_legal_policies() -> List[Policy]:
    """Get all legal policies."""
    return [
        ContractReviewPolicy(),
        NDAEnforcementPolicy(),
        IPProtectionPolicy(),
        LitigationHoldPolicy(),
    ]
