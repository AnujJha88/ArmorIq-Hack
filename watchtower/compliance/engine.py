"""
Universal Compliance Engine
===========================
Central policy evaluation for all domains.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .policies.base import Policy, PolicyResult, PolicyAction, PolicyCategory, PolicySeverity
from .policies.financial import get_financial_policies
from .policies.legal import get_legal_policies
from .policies.security import get_security_policies
from .policies.hr import get_hr_policies
from .policies.procurement import get_procurement_policies
from .policies.operations import get_operations_policies
from .policies.data_privacy import get_data_privacy_policies

logger = logging.getLogger("Compliance.Engine")


@dataclass
class ComplianceResult:
    """Aggregated result from compliance evaluation."""
    allowed: bool
    action: PolicyAction
    severity: PolicySeverity

    # All results
    results: List[PolicyResult]

    # Summary
    policies_evaluated: int
    policies_passed: int
    policies_failed: int
    policies_warned: int

    # Primary failure (if any)
    primary_blocker: Optional[PolicyResult] = None

    # Aggregated suggestions
    suggestions: List[str] = field(default_factory=list)

    # Risk contribution
    total_risk_delta: float = 0.0

    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    evaluation_time_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "allowed": self.allowed,
            "action": self.action.value,
            "severity": self.severity.name,
            "policies_evaluated": self.policies_evaluated,
            "policies_passed": self.policies_passed,
            "policies_failed": self.policies_failed,
            "policies_warned": self.policies_warned,
            "primary_blocker": self.primary_blocker.to_dict() if self.primary_blocker else None,
            "suggestions": self.suggestions,
            "total_risk_delta": self.total_risk_delta,
            "timestamp": self.timestamp.isoformat(),
            "evaluation_time_ms": self.evaluation_time_ms,
        }


class ComplianceEngine:
    """
    Universal Compliance Engine.

    Central policy evaluation for all domains:
    - Financial (SOX, expenses, budgets)
    - Legal (contracts, NDAs, IP)
    - Security (access, data classification)
    - HR (hiring, compensation, termination)
    - Procurement (vendors, spending)
    - Operations (SLAs, ITIL)
    - Data Privacy (GDPR, CCPA, HIPAA)
    """

    def __init__(self, load_defaults: bool = True):
        self.policies: Dict[str, Policy] = {}
        self._evaluation_count = 0
        self._violation_count = 0

        if load_defaults:
            self._load_default_policies()

        logger.info("=" * 60)
        logger.info("  UNIVERSAL COMPLIANCE ENGINE INITIALIZED")
        logger.info("=" * 60)
        logger.info(f"  Loaded {len(self.policies)} policies across domains")
        logger.info("=" * 60)

    def _load_default_policies(self):
        """Load all default policies."""
        policy_loaders = [
            ("Financial", get_financial_policies),
            ("Legal", get_legal_policies),
            ("Security", get_security_policies),
            ("HR", get_hr_policies),
            ("Procurement", get_procurement_policies),
            ("Operations", get_operations_policies),
            ("Data Privacy", get_data_privacy_policies),
        ]

        for domain, loader in policy_loaders:
            try:
                policies = loader()
                for policy in policies:
                    self.register_policy(policy)
                logger.info(f"  Loaded {len(policies)} {domain} policies")
            except Exception as e:
                logger.error(f"  Failed to load {domain} policies: {e}")

    def register_policy(self, policy: Policy):
        """Register a policy."""
        self.policies[policy.policy_id] = policy

    def unregister_policy(self, policy_id: str):
        """Unregister a policy."""
        if policy_id in self.policies:
            del self.policies[policy_id]

    def enable_policy(self, policy_id: str):
        """Enable a policy."""
        if policy_id in self.policies:
            self.policies[policy_id].enabled = True

    def disable_policy(self, policy_id: str):
        """Disable a policy."""
        if policy_id in self.policies:
            self.policies[policy_id].enabled = False

    def evaluate(
        self,
        action: str,
        payload: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        categories: Optional[List[PolicyCategory]] = None,
    ) -> ComplianceResult:
        """
        Evaluate all applicable policies.

        Args:
            action: The action being performed
            payload: The action payload
            context: Additional context
            categories: Optional list of categories to evaluate (None = all)

        Returns:
            ComplianceResult with aggregated evaluation
        """
        import time
        start_time = time.time()

        context = context or {}
        results = []
        suggestions = []

        # Get applicable policies
        applicable = self._get_applicable_policies(action, categories)

        for policy in applicable:
            if not policy.enabled:
                continue

            try:
                result = policy.evaluate(action, payload, context)
                results.append(result)

                if result.suggestion:
                    suggestions.append(f"[{policy.policy_id}] {result.suggestion}")

            except Exception as e:
                logger.error(f"Policy {policy.policy_id} evaluation error: {e}")

        # Aggregate results
        evaluation_time = (time.time() - start_time) * 1000
        return self._aggregate_results(results, suggestions, evaluation_time)

    def _get_applicable_policies(
        self,
        action: str,
        categories: Optional[List[PolicyCategory]] = None,
    ) -> List[Policy]:
        """Get policies applicable to an action."""
        if categories:
            category_set = set(categories)
            return [p for p in self.policies.values() if p.category in category_set]

        return list(self.policies.values())

    def _aggregate_results(
        self,
        results: List[PolicyResult],
        suggestions: List[str],
        evaluation_time_ms: float,
    ) -> ComplianceResult:
        """Aggregate policy results."""
        self._evaluation_count += 1

        if not results:
            return ComplianceResult(
                allowed=True,
                action=PolicyAction.ALLOW,
                severity=PolicySeverity.LOW,
                results=[],
                policies_evaluated=0,
                policies_passed=0,
                policies_failed=0,
                policies_warned=0,
                suggestions=suggestions,
                evaluation_time_ms=evaluation_time_ms,
            )

        # Count by outcome
        passed = sum(1 for r in results if r.action == PolicyAction.ALLOW)
        failed = sum(1 for r in results if r.action in [PolicyAction.DENY, PolicyAction.ESCALATE])
        warned = sum(1 for r in results if r.action == PolicyAction.WARN)

        if failed > 0:
            self._violation_count += 1

        # Determine overall action
        deny_results = [r for r in results if r.action == PolicyAction.DENY]
        escalate_results = [r for r in results if r.action == PolicyAction.ESCALATE]
        modify_results = [r for r in results if r.action == PolicyAction.MODIFY]

        if deny_results:
            action = PolicyAction.DENY
            allowed = False
            # Sort by severity to get primary blocker
            primary = max(deny_results, key=lambda r: r.severity.value)
        elif escalate_results:
            action = PolicyAction.ESCALATE
            allowed = False
            primary = max(escalate_results, key=lambda r: r.severity.value)
        elif modify_results:
            action = PolicyAction.MODIFY
            allowed = True
            primary = modify_results[0]
        else:
            action = PolicyAction.ALLOW
            allowed = True
            primary = None

        # Get highest severity
        max_severity = max((r.severity for r in results), key=lambda s: s.value)

        # Sum risk deltas
        total_risk = sum(r.risk_delta for r in results)

        return ComplianceResult(
            allowed=allowed,
            action=action,
            severity=max_severity,
            results=results,
            policies_evaluated=len(results),
            policies_passed=passed,
            policies_failed=failed,
            policies_warned=warned,
            primary_blocker=primary,
            suggestions=suggestions,
            total_risk_delta=total_risk,
            evaluation_time_ms=evaluation_time_ms,
        )

    def evaluate_with_context(
        self,
        action: str,
        payload: Dict[str, Any],
        agent_id: str,
        user_id: Optional[str] = None,
        department: Optional[str] = None,
        role: Optional[str] = None,
        environment: str = "production",
    ) -> ComplianceResult:
        """
        Evaluate with full context.

        Convenience method that builds context dict.
        """
        context = {
            "agent_id": agent_id,
            "user_id": user_id,
            "department": department,
            "role": role,
            "environment": environment,
            "timestamp": datetime.now().isoformat(),
        }
        return self.evaluate(action, payload, context)

    def get_policy(self, policy_id: str) -> Optional[Policy]:
        """Get a policy by ID."""
        return self.policies.get(policy_id)

    def list_policies(self, category: Optional[PolicyCategory] = None) -> List[Dict]:
        """List all policies."""
        policies = self.policies.values()
        if category:
            policies = [p for p in policies if p.category == category]

        return [p.to_dict() for p in policies]

    def get_stats(self) -> Dict:
        """Get compliance engine statistics."""
        by_category = {}
        by_severity = {}
        total_violations = 0

        for policy in self.policies.values():
            cat = policy.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            sev = policy.severity.name
            by_severity[sev] = by_severity.get(sev, 0) + 1

            total_violations += policy.violation_count

        return {
            "total_policies": len(self.policies),
            "by_category": by_category,
            "by_severity": by_severity,
            "total_evaluations": self._evaluation_count,
            "total_violations": total_violations,
            "violation_rate": total_violations / max(self._evaluation_count, 1),
        }

    def get_violations_summary(self) -> List[Dict]:
        """Get summary of policy violations."""
        violations = []
        for policy in self.policies.values():
            if policy.violation_count > 0:
                violations.append({
                    "policy_id": policy.policy_id,
                    "name": policy.name,
                    "category": policy.category.value,
                    "severity": policy.severity.name,
                    "violation_count": policy.violation_count,
                    "evaluation_count": policy.evaluation_count,
                    "violation_rate": policy.violation_count / max(policy.evaluation_count, 1),
                })

        return sorted(violations, key=lambda v: v["violation_count"], reverse=True)


# Singleton
_engine: Optional[ComplianceEngine] = None


def get_compliance_engine() -> ComplianceEngine:
    """Get the singleton compliance engine."""
    global _engine
    if _engine is None:
        _engine = ComplianceEngine()
    return _engine


def reset_engine():
    """Reset the singleton (for testing)."""
    global _engine
    _engine = None
