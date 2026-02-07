"""
Auto-Remediation Engine
=======================
Generates minimal policy change suggestions for blocked actions.

Key Features:
- Suggest smallest fix to allow an action safely
- Rank suggestions by safety impact and reversibility
- Generate policy-as-code suggestions
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("TIRS.Remediation")


class SuggestionType(Enum):
    """Types of remediation suggestions."""
    MODIFY_VALUE = "modify_value"           # Change a parameter value
    ADD_REQUIREMENT = "add_requirement"     # Add missing requirement
    ESCALATE = "escalate"                   # Require higher approval
    ALTERNATIVE = "alternative"             # Use different approach
    CAPABILITY_GRANT = "capability_grant"   # Grant new capability
    POLICY_EXCEPTION = "policy_exception"   # Create one-time exception


class Reversibility(Enum):
    """How easily a change can be undone."""
    HIGH = "high"       # Easy to undo, no side effects
    MEDIUM = "medium"   # Some effort to undo
    LOW = "low"         # Difficult or risky to undo


class SafetyImpact(Enum):
    """Safety impact of applying the suggestion."""
    MINIMAL = "minimal"     # Very safe
    LOW = "low"             # Minor risk
    MODERATE = "moderate"   # Some risk, needs review
    HIGH = "high"           # Significant risk


@dataclass
class Suggestion:
    """A single remediation suggestion."""
    suggestion_type: SuggestionType
    description: str
    field: Optional[str] = None
    current_value: Optional[Any] = None
    suggested_value: Optional[Any] = None
    policy_code: Optional[str] = None
    reversibility: Reversibility = Reversibility.HIGH
    safety_impact: SafetyImpact = SafetyImpact.MINIMAL
    requires_approval: bool = False
    approval_level: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "type": self.suggestion_type.value,
            "description": self.description,
            "field": self.field,
            "current_value": self.current_value,
            "suggested_value": self.suggested_value,
            "policy_code": self.policy_code,
            "reversibility": self.reversibility.value,
            "safety_impact": self.safety_impact.value,
            "requires_approval": self.requires_approval,
            "approval_level": self.approval_level
        }

    @property
    def score(self) -> float:
        """
        Calculate suggestion score for ranking.

        Higher score = better suggestion (safer, more reversible).
        """
        # Reversibility score (higher is better)
        rev_scores = {Reversibility.HIGH: 1.0, Reversibility.MEDIUM: 0.6, Reversibility.LOW: 0.3}

        # Safety score (inverted - minimal impact is best)
        safety_scores = {
            SafetyImpact.MINIMAL: 1.0,
            SafetyImpact.LOW: 0.7,
            SafetyImpact.MODERATE: 0.4,
            SafetyImpact.HIGH: 0.1
        }

        # Approval penalty
        approval_penalty = 0.2 if self.requires_approval else 0

        return rev_scores[self.reversibility] * safety_scores[self.safety_impact] - approval_penalty


@dataclass
class RemediationResult:
    """Complete remediation analysis for a blocked action."""
    action: str
    policy_violated: str
    block_reason: str
    suggestions: List[Suggestion]
    auto_fixable: bool
    recommended: Optional[Suggestion] = None

    def to_dict(self) -> Dict:
        return {
            "action": self.action,
            "policy_violated": self.policy_violated,
            "block_reason": self.block_reason,
            "auto_fixable": self.auto_fixable,
            "recommended": self.recommended.to_dict() if self.recommended else None,
            "all_suggestions": [s.to_dict() for s in self.suggestions]
        }


class RemediationEngine:
    """
    Generate remediation suggestions for blocked actions.

    Analyzes policy violations and suggests minimal, safe fixes.
    """

    def __init__(self):
        logger.info("RemediationEngine initialized")

        # Policy-specific remediation rules
        self.remediation_rules: Dict[str, callable] = {
            "Salary Caps": self._remediate_salary,
            "Work-Life Balance": self._remediate_scheduling,
            "PII Protection": self._remediate_pii,
            "Inclusive Language": self._remediate_language,
            "Fraud Prevention": self._remediate_fraud,
            "Data Protection": self._remediate_data_protection,
            "Data Privacy": self._remediate_privacy,
            "Right-to-Work": self._remediate_legal,
        }

    def analyze(
        self,
        action: str,
        args: Dict[str, Any],
        policy_violated: str,
        block_reason: str
    ) -> RemediationResult:
        """
        Analyze a blocked action and generate remediation suggestions.

        Args:
            action: The blocked action (e.g., "Offer.generate")
            args: The action arguments
            policy_violated: Name of the policy that blocked
            block_reason: Reason for blocking

        Returns:
            RemediationResult with ranked suggestions
        """
        logger.info(f"Analyzing remediation for: {action}")
        logger.info(f"  Policy: {policy_violated}")
        logger.info(f"  Reason: {block_reason}")

        suggestions = []

        # Get policy-specific suggestions
        if policy_violated in self.remediation_rules:
            policy_suggestions = self.remediation_rules[policy_violated](action, args, block_reason)
            suggestions.extend(policy_suggestions)

        # Add generic escalation option
        suggestions.append(Suggestion(
            suggestion_type=SuggestionType.ESCALATE,
            description=f"Request exception approval from manager",
            reversibility=Reversibility.MEDIUM,
            safety_impact=SafetyImpact.MODERATE,
            requires_approval=True,
            approval_level="manager"
        ))

        # Sort by score (best first)
        suggestions.sort(key=lambda s: s.score, reverse=True)

        # Determine if auto-fixable
        auto_fixable = any(
            s.suggestion_type == SuggestionType.MODIFY_VALUE and
            s.safety_impact in [SafetyImpact.MINIMAL, SafetyImpact.LOW]
            for s in suggestions
        )

        # Get top recommendation
        recommended = suggestions[0] if suggestions else None

        return RemediationResult(
            action=action,
            policy_violated=policy_violated,
            block_reason=block_reason,
            suggestions=suggestions,
            auto_fixable=auto_fixable,
            recommended=recommended
        )

    def _remediate_salary(self, action: str, args: Dict, reason: str) -> List[Suggestion]:
        """Generate remediation for salary cap violations."""
        suggestions = []

        role = args.get("role", "L3")
        current_salary = args.get("salary", 0)
        caps = {"L3": 140000, "L4": 180000, "L5": 240000}
        cap = caps.get(role, 100000)

        # Suggest reducing to cap
        suggestions.append(Suggestion(
            suggestion_type=SuggestionType.MODIFY_VALUE,
            description=f"Reduce salary to maximum for {role}",
            field="salary",
            current_value=current_salary,
            suggested_value=cap,
            reversibility=Reversibility.HIGH,
            safety_impact=SafetyImpact.MINIMAL,
            policy_code=f"offer.salary <= SALARY_BANDS['{role}'].max"
        ))

        # Suggest role upgrade if applicable
        if role != "L5":
            next_role = {"L3": "L4", "L4": "L5"}.get(role)
            if next_role:
                suggestions.append(Suggestion(
                    suggestion_type=SuggestionType.ALTERNATIVE,
                    description=f"Upgrade role to {next_role} to accommodate higher salary",
                    field="role",
                    current_value=role,
                    suggested_value=next_role,
                    reversibility=Reversibility.MEDIUM,
                    safety_impact=SafetyImpact.MODERATE,
                    requires_approval=True,
                    approval_level="hiring_manager"
                ))

        # VP exception
        suggestions.append(Suggestion(
            suggestion_type=SuggestionType.POLICY_EXCEPTION,
            description="Request VP approval for above-band offer",
            reversibility=Reversibility.MEDIUM,
            safety_impact=SafetyImpact.MODERATE,
            requires_approval=True,
            approval_level="vp"
        ))

        return suggestions

    def _remediate_scheduling(self, action: str, args: Dict, reason: str) -> List[Suggestion]:
        """Generate remediation for scheduling violations."""
        suggestions = []

        if "weekend" in reason.lower():
            suggestions.append(Suggestion(
                suggestion_type=SuggestionType.MODIFY_VALUE,
                description="Reschedule to a weekday",
                field="date",
                current_value=args.get("date"),
                suggested_value="(next available weekday)",
                reversibility=Reversibility.HIGH,
                safety_impact=SafetyImpact.MINIMAL
            ))

        if "hours" in reason.lower():
            suggestions.append(Suggestion(
                suggestion_type=SuggestionType.MODIFY_VALUE,
                description="Reschedule to work hours (9 AM - 5 PM)",
                field="time",
                current_value=args.get("time"),
                suggested_value="10:00",
                reversibility=Reversibility.HIGH,
                safety_impact=SafetyImpact.MINIMAL
            ))

        return suggestions

    def _remediate_pii(self, action: str, args: Dict, reason: str) -> List[Suggestion]:
        """Generate remediation for PII violations."""
        suggestions = []

        suggestions.append(Suggestion(
            suggestion_type=SuggestionType.MODIFY_VALUE,
            description="Automatically redact PII from content",
            field="body",
            current_value="(contains PII)",
            suggested_value="(PII redacted)",
            reversibility=Reversibility.HIGH,
            safety_impact=SafetyImpact.MINIMAL,
            policy_code="email.body = redact_pii(email.body)"
        ))

        suggestions.append(Suggestion(
            suggestion_type=SuggestionType.ALTERNATIVE,
            description="Send to internal recipient instead",
            field="to",
            reversibility=Reversibility.HIGH,
            safety_impact=SafetyImpact.MINIMAL
        ))

        return suggestions

    def _remediate_language(self, action: str, args: Dict, reason: str) -> List[Suggestion]:
        """Generate remediation for inclusive language violations."""
        suggestions = []

        # Extract the offending term from reason
        term = None
        if "'" in reason:
            term = reason.split("'")[1]

        replacements = {
            "rockstar": "talented professional",
            "ninja": "skilled engineer",
            "guru": "expert",
            "guys": "team"
        }

        if term and term in replacements:
            suggestions.append(Suggestion(
                suggestion_type=SuggestionType.MODIFY_VALUE,
                description=f"Replace '{term}' with '{replacements[term]}'",
                field="body",
                current_value=term,
                suggested_value=replacements[term],
                reversibility=Reversibility.HIGH,
                safety_impact=SafetyImpact.MINIMAL
            ))

        suggestions.append(Suggestion(
            suggestion_type=SuggestionType.MODIFY_VALUE,
            description="Review and revise non-inclusive language",
            field="body",
            reversibility=Reversibility.HIGH,
            safety_impact=SafetyImpact.MINIMAL
        ))

        return suggestions

    def _remediate_fraud(self, action: str, args: Dict, reason: str) -> List[Suggestion]:
        """Generate remediation for fraud prevention violations."""
        suggestions = []

        if "receipt" in reason.lower():
            suggestions.append(Suggestion(
                suggestion_type=SuggestionType.ADD_REQUIREMENT,
                description="Attach receipt for expense claim",
                field="has_receipt",
                current_value=False,
                suggested_value=True,
                reversibility=Reversibility.HIGH,
                safety_impact=SafetyImpact.MINIMAL
            ))

        if "alcohol" in reason.lower():
            suggestions.append(Suggestion(
                suggestion_type=SuggestionType.MODIFY_VALUE,
                description="Reduce alcohol expense to per-person limit",
                field="amount",
                reversibility=Reversibility.HIGH,
                safety_impact=SafetyImpact.LOW
            ))

        return suggestions

    def _remediate_data_protection(self, action: str, args: Dict, reason: str) -> List[Suggestion]:
        """Generate remediation for data protection violations."""
        suggestions = []

        suggestions.append(Suggestion(
            suggestion_type=SuggestionType.ESCALATE,
            description="Request admin approval for data export",
            reversibility=Reversibility.MEDIUM,
            safety_impact=SafetyImpact.MODERATE,
            requires_approval=True,
            approval_level="data_admin"
        ))

        suggestions.append(Suggestion(
            suggestion_type=SuggestionType.ALTERNATIVE,
            description="Use filtered query instead of bulk export",
            reversibility=Reversibility.HIGH,
            safety_impact=SafetyImpact.MINIMAL
        ))

        return suggestions

    def _remediate_privacy(self, action: str, args: Dict, reason: str) -> List[Suggestion]:
        """Generate remediation for privacy violations."""
        suggestions = []

        suggestions.append(Suggestion(
            suggestion_type=SuggestionType.ESCALATE,
            description="Request data subject's consent",
            reversibility=Reversibility.MEDIUM,
            safety_impact=SafetyImpact.LOW,
            requires_approval=True,
            approval_level="data_subject"
        ))

        suggestions.append(Suggestion(
            suggestion_type=SuggestionType.ALTERNATIVE,
            description="Access only your own data",
            reversibility=Reversibility.HIGH,
            safety_impact=SafetyImpact.MINIMAL
        ))

        return suggestions

    def _remediate_legal(self, action: str, args: Dict, reason: str) -> List[Suggestion]:
        """Generate remediation for legal/compliance violations."""
        suggestions = []

        if "i-9" in reason.lower() or "i9" in reason.lower():
            suggestions.append(Suggestion(
                suggestion_type=SuggestionType.ADD_REQUIREMENT,
                description="Complete I-9 verification before onboarding",
                field="i9_status",
                current_value="pending",
                suggested_value="verified",
                reversibility=Reversibility.HIGH,
                safety_impact=SafetyImpact.MINIMAL
            ))

        return suggestions

    def apply_suggestion(self, args: Dict, suggestion: Suggestion) -> Dict:
        """
        Apply a suggestion to generate fixed arguments.

        Args:
            args: Original action arguments
            suggestion: Suggestion to apply

        Returns:
            Modified arguments with fix applied
        """
        if suggestion.suggestion_type != SuggestionType.MODIFY_VALUE:
            logger.warning(f"Cannot auto-apply suggestion type: {suggestion.suggestion_type}")
            return args

        if not suggestion.field or suggestion.suggested_value is None:
            return args

        new_args = args.copy()
        new_args[suggestion.field] = suggestion.suggested_value

        logger.info(f"Applied fix: {suggestion.field} = {suggestion.suggested_value}")

        return new_args


# Singleton instance
_remediation_engine: Optional[RemediationEngine] = None


def get_remediation_engine() -> RemediationEngine:
    """Get the singleton remediation engine."""
    global _remediation_engine
    if _remediation_engine is None:
        _remediation_engine = RemediationEngine()
    return _remediation_engine
