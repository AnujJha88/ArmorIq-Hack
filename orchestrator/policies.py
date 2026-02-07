"""
Advanced Policy Engine
======================
Dynamic policy enforcement with Watchtower integration.
"""

import re
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Tuple
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger("Orchestrator.Policies")


class PolicySeverity(Enum):
    """How severe a policy violation is."""
    INFO = "info"          # Log only
    WARNING = "warning"    # Warn but allow
    BLOCK = "block"        # Block action
    CRITICAL = "critical"  # Block and alert


class PolicyAction(Enum):
    """What to do when policy is triggered."""
    ALLOW = "allow"
    MODIFY = "modify"      # Modify payload and allow
    WARN = "warn"          # Allow with warning
    BLOCK = "block"
    ESCALATE = "escalate"  # Require human approval


@dataclass
class PolicyResult:
    """Result of policy evaluation."""
    action: PolicyAction
    policy_id: str
    policy_name: str
    severity: PolicySeverity
    reason: str
    suggestion: Optional[str] = None
    modified_payload: Optional[Dict] = None
    metadata: Dict = field(default_factory=dict)
    risk_delta: float = 0.0  # How much to add to risk score


class Policy(ABC):
    """Base class for all policies."""

    def __init__(self, policy_id: str, name: str, description: str, severity: PolicySeverity):
        self.policy_id = policy_id
        self.name = name
        self.description = description
        self.severity = severity
        self.enabled = True
        self.evaluations = 0
        self.triggers = 0

    @abstractmethod
    def evaluate(self, action: str, payload: Dict[str, Any], context: Dict[str, Any]) -> PolicyResult:
        """Evaluate the policy against an action."""
        pass

    @abstractmethod
    def applies_to(self, action: str) -> bool:
        """Check if this policy applies to the given action."""
        pass

    def to_dict(self) -> Dict:
        return {
            "policy_id": self.policy_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity.value,
            "enabled": self.enabled,
            "evaluations": self.evaluations,
            "triggers": self.triggers
        }


# ═══════════════════════════════════════════════════════════════════════════════
# WORK-LIFE BALANCE POLICIES
# ═══════════════════════════════════════════════════════════════════════════════

class WorkHoursPolicy(Policy):
    """Enforce work hour restrictions."""

    def __init__(self):
        super().__init__(
            policy_id="work_hours",
            name="Work Hours Policy",
            description="Block scheduling outside business hours",
            severity=PolicySeverity.BLOCK
        )
        self.work_start = 9   # 9 AM
        self.work_end = 17    # 5 PM
        self.blocked_days = [5, 6]  # Saturday, Sunday

    def applies_to(self, action: str) -> bool:
        return action in [
            "schedule_interview", "schedule_meeting", "create_event",
            "send_calendar_invite"
        ]

    def evaluate(self, action: str, payload: Dict[str, Any], context: Dict[str, Any]) -> PolicyResult:
        self.evaluations += 1

        time_str = payload.get("time") or payload.get("start_time") or payload.get("datetime")
        if not time_str:
            return PolicyResult(
                action=PolicyAction.ALLOW,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.INFO,
                reason="No time specified"
            )

        try:
            dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                dt = datetime.fromisoformat(time_str)
            except ValueError:
                return PolicyResult(
                    action=PolicyAction.ALLOW,
                    policy_id=self.policy_id,
                    policy_name=self.name,
                    severity=PolicySeverity.INFO,
                    reason="Could not parse time"
                )

        # Check day of week
        if dt.weekday() in self.blocked_days:
            self.triggers += 1
            day_name = dt.strftime("%A")
            return PolicyResult(
                action=PolicyAction.BLOCK,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.BLOCK,
                reason=f"Cannot schedule on {day_name} (weekend)",
                suggestion="Choose a weekday (Monday-Friday)",
                risk_delta=0.15
            )

        # Check time of day
        if not (self.work_start <= dt.hour < self.work_end):
            self.triggers += 1
            return PolicyResult(
                action=PolicyAction.BLOCK,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.BLOCK,
                reason=f"Cannot schedule at {dt.strftime('%I:%M %p')} (outside {self.work_start}AM-{self.work_end-12}PM)",
                suggestion=f"Choose a time between {self.work_start}:00 AM and {self.work_end-12}:00 PM",
                risk_delta=0.1
            )

        return PolicyResult(
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            severity=PolicySeverity.INFO,
            reason="Time is within business hours"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# COMPENSATION POLICIES
# ═══════════════════════════════════════════════════════════════════════════════

class SalaryCapPolicy(Policy):
    """Enforce salary caps by level."""

    def __init__(self):
        super().__init__(
            policy_id="salary_cap",
            name="Salary Cap Policy",
            description="Enforce compensation limits by level",
            severity=PolicySeverity.BLOCK
        )
        self.caps = {
            "L3": {"base": 140000, "total": 160000},
            "L4": {"base": 180000, "total": 220000},
            "L5": {"base": 240000, "total": 300000},
            "L6": {"base": 320000, "total": 420000},
        }

    def applies_to(self, action: str) -> bool:
        return action in ["generate_offer", "negotiate_offer", "update_salary", "create_offer"]

    def evaluate(self, action: str, payload: Dict[str, Any], context: Dict[str, Any]) -> PolicyResult:
        self.evaluations += 1

        level = payload.get("level", "L4")
        salary = payload.get("salary", 0)
        equity = payload.get("equity", 0)
        bonus = payload.get("signing_bonus", 0)

        if level not in self.caps:
            return PolicyResult(
                action=PolicyAction.ALLOW,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.INFO,
                reason=f"Unknown level: {level}"
            )

        caps = self.caps[level]

        # Check base salary
        if salary > caps["base"]:
            self.triggers += 1
            return PolicyResult(
                action=PolicyAction.BLOCK,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.BLOCK,
                reason=f"Base salary ${salary:,} exceeds {level} cap of ${caps['base']:,}",
                suggestion=f"Reduce base salary to ${caps['base']:,} or below",
                risk_delta=0.2,
                metadata={"cap": caps["base"], "requested": salary}
            )

        # Check total compensation
        total_comp = salary + equity + bonus
        if total_comp > caps["total"]:
            self.triggers += 1
            return PolicyResult(
                action=PolicyAction.ESCALATE,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.WARNING,
                reason=f"Total comp ${total_comp:,} exceeds {level} guideline of ${caps['total']:,}",
                suggestion="Requires VP-level approval",
                risk_delta=0.1,
                metadata={"cap": caps["total"], "requested": total_comp}
            )

        return PolicyResult(
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            severity=PolicySeverity.INFO,
            reason=f"Compensation within {level} guidelines"
        )


class EquityVestingPolicy(Policy):
    """Enforce equity vesting requirements."""

    def __init__(self):
        super().__init__(
            policy_id="equity_vesting",
            name="Equity Vesting Policy",
            description="Ensure standard vesting schedule",
            severity=PolicySeverity.WARNING
        )
        self.standard_cliff_months = 12
        self.standard_vesting_months = 48

    def applies_to(self, action: str) -> bool:
        return action in ["generate_offer", "negotiate_offer", "create_offer"]

    def evaluate(self, action: str, payload: Dict[str, Any], context: Dict[str, Any]) -> PolicyResult:
        self.evaluations += 1

        equity = payload.get("equity", 0)
        if equity == 0:
            return PolicyResult(
                action=PolicyAction.ALLOW,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.INFO,
                reason="No equity in offer"
            )

        cliff_months = payload.get("cliff_months", self.standard_cliff_months)
        vesting_months = payload.get("vesting_months", self.standard_vesting_months)

        if cliff_months < self.standard_cliff_months:
            self.triggers += 1
            return PolicyResult(
                action=PolicyAction.ESCALATE,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.WARNING,
                reason=f"Non-standard cliff ({cliff_months} months < {self.standard_cliff_months})",
                suggestion="Use standard 1-year cliff or get approval",
                risk_delta=0.1
            )

        if vesting_months != self.standard_vesting_months:
            self.triggers += 1
            return PolicyResult(
                action=PolicyAction.WARN,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.WARNING,
                reason=f"Non-standard vesting ({vesting_months} months != {self.standard_vesting_months})",
                suggestion="Document rationale for non-standard vesting"
            )

        return PolicyResult(
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            severity=PolicySeverity.INFO,
            reason="Standard vesting schedule"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PII & DATA PROTECTION POLICIES
# ═══════════════════════════════════════════════════════════════════════════════

class PIIProtectionPolicy(Policy):
    """Protect personally identifiable information."""

    def __init__(self):
        super().__init__(
            policy_id="pii_protection",
            name="PII Protection Policy",
            description="Redact PII from external communications",
            severity=PolicySeverity.BLOCK
        )
        self.patterns = {
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "email_personal": r"\b[a-zA-Z0-9._%+-]+@(gmail|yahoo|hotmail|outlook)\.[a-zA-Z]{2,}\b",
            "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
            "bank_account": r"\b\d{8,17}\b",  # Simple pattern, real one more complex
        }

    def applies_to(self, action: str) -> bool:
        return action in [
            "send_email", "send_slack", "send_message",
            "export_data", "generate_report", "create_document"
        ]

    def evaluate(self, action: str, payload: Dict[str, Any], context: Dict[str, Any]) -> PolicyResult:
        self.evaluations += 1

        # Check if external communication
        recipient = payload.get("to") or payload.get("recipient") or payload.get("channel", "")
        is_external = "@company.com" not in recipient and "#" not in recipient

        if not is_external:
            return PolicyResult(
                action=PolicyAction.ALLOW,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.INFO,
                reason="Internal communication, no PII check needed"
            )

        # Check content for PII
        body = payload.get("body") or payload.get("message") or payload.get("content", "")
        found_pii = []
        modified_body = body

        for pii_type, pattern in self.patterns.items():
            matches = re.findall(pattern, body)
            if matches:
                found_pii.append(pii_type)
                modified_body = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", modified_body)

        if found_pii:
            self.triggers += 1

            # Modify payload with redacted content
            modified_payload = dict(payload)
            if "body" in modified_payload:
                modified_payload["body"] = modified_body
            elif "message" in modified_payload:
                modified_payload["message"] = modified_body
            elif "content" in modified_payload:
                modified_payload["content"] = modified_body

            return PolicyResult(
                action=PolicyAction.MODIFY,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.WARNING,
                reason=f"Redacted PII: {', '.join(found_pii)}",
                modified_payload=modified_payload,
                risk_delta=0.1,
                metadata={"pii_types": found_pii}
            )

        return PolicyResult(
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            severity=PolicySeverity.INFO,
            reason="No PII detected in external communication"
        )


class DataExportPolicy(Policy):
    """Control data exports."""

    def __init__(self):
        super().__init__(
            policy_id="data_export",
            name="Data Export Policy",
            description="Require approval for bulk data exports",
            severity=PolicySeverity.BLOCK
        )
        self.bulk_threshold = 100  # records

    def applies_to(self, action: str) -> bool:
        return action in ["export_data", "bulk_download", "generate_report"]

    def evaluate(self, action: str, payload: Dict[str, Any], context: Dict[str, Any]) -> PolicyResult:
        self.evaluations += 1

        record_count = payload.get("record_count", 0) or payload.get("limit", 0)
        data_type = payload.get("data_type", "unknown")

        sensitive_types = ["salary", "ssn", "personal", "compensation", "performance"]

        if any(st in data_type.lower() for st in sensitive_types):
            self.triggers += 1
            return PolicyResult(
                action=PolicyAction.ESCALATE,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.BLOCK,
                reason=f"Export of sensitive data type: {data_type}",
                suggestion="Requires Data Privacy Officer approval",
                risk_delta=0.25
            )

        if record_count > self.bulk_threshold:
            self.triggers += 1
            return PolicyResult(
                action=PolicyAction.ESCALATE,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.WARNING,
                reason=f"Bulk export of {record_count} records exceeds threshold",
                suggestion=f"Exports over {self.bulk_threshold} records require approval",
                risk_delta=0.15
            )

        return PolicyResult(
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            severity=PolicySeverity.INFO,
            reason="Export within limits"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# INCLUSIVE LANGUAGE POLICIES
# ═══════════════════════════════════════════════════════════════════════════════

class InclusiveLanguagePolicy(Policy):
    """Enforce inclusive language in communications."""

    def __init__(self):
        super().__init__(
            policy_id="inclusive_language",
            name="Inclusive Language Policy",
            description="Flag non-inclusive terminology",
            severity=PolicySeverity.BLOCK
        )
        self.replacements = {
            "rockstar": "high performer",
            "ninja": "expert",
            "guru": "specialist",
            "wizard": "expert",
            "manpower": "workforce",
            "mankind": "humanity",
            "man-hours": "person-hours",
            "chairman": "chairperson",
            "blacklist": "blocklist",
            "whitelist": "allowlist",
            "master": "main",
            "slave": "secondary",
            "guys": "team",
            "crazy": "unexpected",
            "insane": "remarkable",
        }

    def applies_to(self, action: str) -> bool:
        return action in [
            "send_email", "send_slack", "send_message",
            "generate_offer", "create_job_posting", "write_review"
        ]

    def evaluate(self, action: str, payload: Dict[str, Any], context: Dict[str, Any]) -> PolicyResult:
        self.evaluations += 1

        text_fields = ["body", "message", "content", "description", "title", "subject"]
        combined_text = ""
        for field in text_fields:
            if field in payload:
                combined_text += " " + str(payload[field])

        combined_text_lower = combined_text.lower()
        found_terms = []
        suggestions = []

        for term, replacement in self.replacements.items():
            if term in combined_text_lower:
                found_terms.append(term)
                suggestions.append(f"'{term}' → '{replacement}'")

        if found_terms:
            self.triggers += 1

            # Create modified payload with replacements
            modified_payload = dict(payload)
            for field in text_fields:
                if field in modified_payload:
                    text = str(modified_payload[field])
                    for term, replacement in self.replacements.items():
                        text = re.sub(rf"\b{term}\b", replacement, text, flags=re.IGNORECASE)
                    modified_payload[field] = text

            return PolicyResult(
                action=PolicyAction.MODIFY,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.WARNING,
                reason=f"Non-inclusive terms found: {', '.join(found_terms)}",
                suggestion=f"Suggested replacements: {'; '.join(suggestions)}",
                modified_payload=modified_payload,
                risk_delta=0.05,
                metadata={"terms": found_terms, "suggestions": suggestions}
            )

        return PolicyResult(
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            severity=PolicySeverity.INFO,
            reason="Language passes inclusivity check"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE POLICIES
# ═══════════════════════════════════════════════════════════════════════════════

class I9VerificationPolicy(Policy):
    """Ensure I-9 verification before onboarding."""

    def __init__(self):
        super().__init__(
            policy_id="i9_verification",
            name="I-9 Verification Policy",
            description="Block onboarding without I-9 verification",
            severity=PolicySeverity.CRITICAL
        )

    def applies_to(self, action: str) -> bool:
        return action in ["onboard_employee", "start_onboarding", "create_accounts", "provision_access"]

    def evaluate(self, action: str, payload: Dict[str, Any], context: Dict[str, Any]) -> PolicyResult:
        self.evaluations += 1

        i9_status = payload.get("i9_status") or context.get("i9_verified")

        if i9_status == "verified" or i9_status is True:
            return PolicyResult(
                action=PolicyAction.ALLOW,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.INFO,
                reason="I-9 verification complete"
            )

        if i9_status == "pending":
            self.triggers += 1
            return PolicyResult(
                action=PolicyAction.BLOCK,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.CRITICAL,
                reason="I-9 verification pending - cannot proceed with onboarding",
                suggestion="Complete I-9 verification before onboarding",
                risk_delta=0.3
            )

        self.triggers += 1
        return PolicyResult(
            action=PolicyAction.ESCALATE,
            policy_id=self.policy_id,
            policy_name=self.name,
            severity=PolicySeverity.CRITICAL,
            reason="I-9 status unknown - requires verification",
            suggestion="Verify I-9 status with Compliance team",
            risk_delta=0.25
        )


class BackgroundCheckPolicy(Policy):
    """Ensure background checks before access."""

    def __init__(self):
        super().__init__(
            policy_id="background_check",
            name="Background Check Policy",
            description="Require background check for access provisioning",
            severity=PolicySeverity.BLOCK
        )

    def applies_to(self, action: str) -> bool:
        return action in ["provision_access", "create_accounts", "grant_permissions"]

    def evaluate(self, action: str, payload: Dict[str, Any], context: Dict[str, Any]) -> PolicyResult:
        self.evaluations += 1

        bg_status = payload.get("background_check") or context.get("background_check_status")

        if bg_status == "clear" or bg_status == "passed":
            return PolicyResult(
                action=PolicyAction.ALLOW,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.INFO,
                reason="Background check passed"
            )

        if bg_status == "in_progress":
            self.triggers += 1
            return PolicyResult(
                action=PolicyAction.BLOCK,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.BLOCK,
                reason="Background check in progress - cannot provision access yet",
                suggestion="Wait for background check to complete",
                risk_delta=0.2
            )

        if bg_status == "failed" or bg_status == "flagged":
            self.triggers += 1
            return PolicyResult(
                action=PolicyAction.ESCALATE,
                policy_id=self.policy_id,
                policy_name=self.name,
                severity=PolicySeverity.CRITICAL,
                reason="Background check flagged - requires HR review",
                suggestion="Escalate to HR for review",
                risk_delta=0.4
            )

        return PolicyResult(
            action=PolicyAction.ALLOW,
            policy_id=self.policy_id,
            policy_name=self.name,
            severity=PolicySeverity.INFO,
            reason="No background check requirement specified"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# POLICY ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class PolicyEngine:
    """
    Central policy enforcement engine.

    Evaluates all applicable policies against actions and
    returns the most restrictive result.
    """

    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.evaluation_history: List[Dict] = []
        self._register_default_policies()
        logger.info(f"Policy Engine initialized with {len(self.policies)} policies")

    def _register_default_policies(self):
        """Register all built-in policies."""
        default_policies = [
            WorkHoursPolicy(),
            SalaryCapPolicy(),
            EquityVestingPolicy(),
            PIIProtectionPolicy(),
            DataExportPolicy(),
            InclusiveLanguagePolicy(),
            I9VerificationPolicy(),
            BackgroundCheckPolicy(),
        ]

        for policy in default_policies:
            self.register(policy)

    def register(self, policy: Policy):
        """Register a policy."""
        self.policies[policy.policy_id] = policy
        logger.info(f"Registered policy: {policy.name} ({policy.policy_id})")

    def unregister(self, policy_id: str):
        """Unregister a policy."""
        if policy_id in self.policies:
            del self.policies[policy_id]

    def enable(self, policy_id: str):
        """Enable a policy."""
        if policy_id in self.policies:
            self.policies[policy_id].enabled = True

    def disable(self, policy_id: str):
        """Disable a policy."""
        if policy_id in self.policies:
            self.policies[policy_id].enabled = False

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Tuple[PolicyResult, List[PolicyResult]]:
        """
        Evaluate all applicable policies.

        Returns:
            Tuple of (final_result, all_results)
            final_result is the most restrictive policy result
        """
        context = context or {}
        all_results = []

        # Find applicable policies
        for policy in self.policies.values():
            if not policy.enabled:
                continue

            if policy.applies_to(action):
                result = policy.evaluate(action, payload, context)
                all_results.append(result)

                # Record history
                self.evaluation_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": action,
                    "policy_id": policy.policy_id,
                    "result": result.action.value,
                    "reason": result.reason
                })

        if not all_results:
            # No policies apply, allow by default
            return PolicyResult(
                action=PolicyAction.ALLOW,
                policy_id="default",
                policy_name="Default Allow",
                severity=PolicySeverity.INFO,
                reason="No policies apply"
            ), []

        # Sort by restrictiveness: BLOCK > ESCALATE > WARN > MODIFY > ALLOW
        priority = {
            PolicyAction.BLOCK: 5,
            PolicyAction.ESCALATE: 4,
            PolicyAction.WARN: 3,
            PolicyAction.MODIFY: 2,
            PolicyAction.ALLOW: 1
        }

        all_results.sort(key=lambda r: priority.get(r.action, 0), reverse=True)

        # Return most restrictive
        final = all_results[0]

        # Aggregate risk delta
        total_risk = sum(r.risk_delta for r in all_results)
        final.risk_delta = total_risk

        # If any policy modified, include that
        for result in all_results:
            if result.action == PolicyAction.MODIFY and result.modified_payload:
                final.modified_payload = result.modified_payload
                break

        return final, all_results

    def get_policy_stats(self) -> Dict:
        """Get statistics on policy evaluations."""
        return {
            "total_policies": len(self.policies),
            "enabled_policies": len([p for p in self.policies.values() if p.enabled]),
            "total_evaluations": sum(p.evaluations for p in self.policies.values()),
            "total_triggers": sum(p.triggers for p in self.policies.values()),
            "policies": [p.to_dict() for p in self.policies.values()]
        }


# Singleton
_policy_engine = None

def get_policy_engine() -> PolicyEngine:
    global _policy_engine
    if _policy_engine is None:
        _policy_engine = PolicyEngine()
    return _policy_engine
