"""
Data Privacy Compliance Policies
================================
GDPR, CCPA, HIPAA, PII protection, consent management.
"""

from typing import Dict, Any, List, Set
from datetime import datetime
from .base import (
    Policy, PolicyCategory, PolicyAction, PolicySeverity, PolicyResult,
)


class PIIProtectionPolicy(Policy):
    """Personally Identifiable Information protection."""

    # PII field patterns
    PII_FIELDS = [
        "ssn", "social_security", "tax_id",
        "credit_card", "card_number", "cvv",
        "bank_account", "routing_number",
        "driver_license", "passport",
        "date_of_birth", "dob", "birthday",
        "phone", "email", "address",
        "salary", "compensation",
    ]

    def __init__(self):
        super().__init__(
            policy_id="PRIV-001",
            name="PII Protection Policy",
            category=PolicyCategory.PII_PROTECTION,
            severity=PolicySeverity.CRITICAL,
            description="Protects personally identifiable information",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate PII handling requirements."""
        # Check for PII in payload
        pii_found = []
        for key in payload.keys():
            key_lower = key.lower()
            for pii_field in self.PII_FIELDS:
                if pii_field in key_lower:
                    pii_found.append(key)
                    break

        if not pii_found:
            return self._allow("No PII detected")

        # Check if action involves external transfer
        is_external = context.get("external", False) or "external" in action.lower()
        is_export = "export" in action.lower() or "download" in action.lower()
        is_log = "log" in action.lower() or "audit" in action.lower()

        # External transfer of PII
        if is_external:
            return self._deny(
                f"Cannot transfer PII externally: {pii_found}",
                "Remove PII fields or use data masking",
            )

        # Bulk export
        if is_export:
            return self._escalate(
                f"PII export requires approval: {pii_found}",
                "Submit data export request for approval",
            )

        # Logging PII (should be masked)
        if is_log:
            return self._modify(
                f"PII must be masked in logs: {pii_found}",
                {**payload, "pii_masked": True, "mask_fields": pii_found},
                "Apply PII masking before logging",
            )

        return self._allow("PII handling compliant")


class GDPRPolicy(Policy):
    """GDPR compliance policy."""

    def __init__(self):
        super().__init__(
            policy_id="PRIV-002",
            name="GDPR Compliance Policy",
            category=PolicyCategory.CROSS_BORDER,
            severity=PolicySeverity.CRITICAL,
            description="Enforces GDPR data protection requirements",
        )
        self._consents: Dict[str, Set[str]] = {}  # subject_id -> set of purposes

    def record_consent(self, subject_id: str, purpose: str):
        """Record consent for a purpose."""
        if subject_id not in self._consents:
            self._consents[subject_id] = set()
        self._consents[subject_id].add(purpose)

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate GDPR requirements."""
        # Check if EU data subject
        is_eu = context.get("region") == "EU" or payload.get("subject_region") == "EU"
        if not is_eu:
            return self._allow("Not EU data subject")

        subject_id = payload.get("subject_id") or payload.get("user_id")
        purpose = payload.get("purpose", "unknown")

        # Right to be forgotten
        if "delete" in action.lower() and payload.get("gdpr_request"):
            if not payload.get("verified_identity"):
                return self._escalate(
                    "GDPR deletion request requires identity verification",
                    "Verify requestor identity before processing",
                )
            return self._allow("GDPR deletion request - process within 30 days")

        # Data portability
        if "export" in action.lower() and payload.get("gdpr_portability"):
            return self._modify(
                "GDPR portability request - provide in machine-readable format",
                {**payload, "format": "json", "include_all_data": True},
            )

        # Check consent
        if subject_id:
            consents = self._consents.get(subject_id, set())
            if purpose not in consents and purpose != "legitimate_interest":
                return self._deny(
                    f"No consent for purpose '{purpose}' from subject {subject_id}",
                    "Obtain consent before processing",
                )

        # Cross-border transfer
        destination = payload.get("destination_region")
        if destination and destination not in ["EU", "EEA"]:
            adequacy = payload.get("adequacy_decision", False)
            sccs = payload.get("standard_contractual_clauses", False)

            if not adequacy and not sccs:
                return self._deny(
                    f"Cross-border transfer to {destination} requires adequacy decision or SCCs",
                    "Implement appropriate safeguards before transfer",
                )

        return self._allow("GDPR requirements met")


class CCPAPolicy(Policy):
    """California Consumer Privacy Act compliance."""

    def __init__(self):
        super().__init__(
            policy_id="PRIV-003",
            name="CCPA Compliance Policy",
            category=PolicyCategory.CONSENT,
            severity=PolicySeverity.HIGH,
            description="Enforces CCPA consumer privacy rights",
        )
        self._opt_outs: Set[str] = set()  # Consumers who opted out of sale

    def record_opt_out(self, consumer_id: str):
        """Record consumer opt-out."""
        self._opt_outs.add(consumer_id)

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate CCPA requirements."""
        # Check if California consumer
        is_california = context.get("state") == "CA" or payload.get("consumer_state") == "CA"
        if not is_california:
            return self._allow("Not California consumer")

        consumer_id = payload.get("consumer_id") or payload.get("user_id")

        # Right to know
        if payload.get("ccpa_disclosure_request"):
            return self._modify(
                "CCPA disclosure request - provide data categories within 45 days",
                {**payload, "disclosure_required": True, "deadline_days": 45},
            )

        # Right to delete
        if "delete" in action.lower() and payload.get("ccpa_deletion_request"):
            return self._allow("CCPA deletion request - process within 45 days")

        # Opt-out of sale
        if consumer_id and consumer_id in self._opt_outs:
            if "sell" in action.lower() or "share" in action.lower():
                return self._deny(
                    f"Consumer {consumer_id} opted out of data sale",
                    "Do not sell this consumer's personal information",
                )

        # Notice at collection
        if "collect" in action.lower():
            if not payload.get("notice_provided"):
                return self._modify(
                    "CCPA requires notice at collection",
                    {**payload, "require_notice": True},
                    "Provide privacy notice before collection",
                )

        return self._allow("CCPA requirements met")


class HIPAAPolicy(Policy):
    """HIPAA healthcare data protection."""

    # PHI identifiers
    PHI_IDENTIFIERS = [
        "patient_name", "medical_record", "health_plan",
        "diagnosis", "treatment", "medication",
        "lab_result", "vital_signs", "immunization",
    ]

    def __init__(self):
        super().__init__(
            policy_id="PRIV-004",
            name="HIPAA Compliance Policy",
            category=PolicyCategory.PII_PROTECTION,
            severity=PolicySeverity.CRITICAL,
            description="Protects Protected Health Information (PHI)",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate HIPAA requirements."""
        # Check for PHI
        phi_found = []
        for key in payload.keys():
            key_lower = key.lower()
            for phi_field in self.PHI_IDENTIFIERS:
                if phi_field in key_lower:
                    phi_found.append(key)
                    break

        if not phi_found:
            return self._allow("No PHI detected")

        # PHI requires encryption
        is_encrypted = payload.get("encrypted", False)
        if not is_encrypted:
            return self._modify(
                f"PHI must be encrypted: {phi_found}",
                {**payload, "encrypt_required": True},
                "Enable encryption for PHI data",
            )

        # Minimum necessary
        if len(phi_found) > 3:
            return self._warn(
                f"HIPAA minimum necessary: Consider limiting PHI fields ({len(phi_found)} found)",
            )

        # Access logging
        if not context.get("audit_logged"):
            return self._modify(
                "PHI access must be logged",
                {**payload, "require_audit_log": True},
            )

        # Business Associate Agreement check
        if context.get("third_party") and not payload.get("baa_signed"):
            return self._deny(
                "PHI disclosure to third party requires Business Associate Agreement",
                "Execute BAA before sharing PHI",
            )

        return self._allow("HIPAA requirements met")


class DataRetentionPolicy(Policy):
    """Data retention and deletion policy."""

    # Retention periods by data type (days)
    RETENTION_PERIODS = {
        "transaction": 2555,  # 7 years for financial
        "employee": 2555,     # 7 years for employment records
        "customer": 1095,     # 3 years
        "marketing": 365,     # 1 year
        "logs": 90,           # 90 days
        "temporary": 30,      # 30 days
    }

    def __init__(self):
        super().__init__(
            policy_id="PRIV-005",
            name="Data Retention Policy",
            category=PolicyCategory.RETENTION,
            severity=PolicySeverity.MEDIUM,
            description="Enforces data retention and deletion requirements",
        )

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyResult:
        """Evaluate data retention requirements."""
        data_type = payload.get("data_type", "customer")
        age_days = payload.get("age_days", 0)

        retention = self.RETENTION_PERIODS.get(data_type, 1095)

        # Check if data should be deleted
        if "delete" in action.lower():
            if age_days < retention:
                return self._warn(
                    f"Deleting {data_type} data before retention period ({retention} days)",
                )
            return self._allow("Data beyond retention period - deletion allowed")

        # Check if data is past retention
        if age_days > retention:
            return self._warn(
                f"{data_type} data ({age_days} days old) exceeds retention period ({retention} days)",
            )

        return self._allow("Data within retention period")


def get_data_privacy_policies() -> List[Policy]:
    """Get all data privacy policies."""
    return [
        PIIProtectionPolicy(),
        GDPRPolicy(),
        CCPAPolicy(),
        HIPAAPolicy(),
        DataRetentionPolicy(),
    ]
