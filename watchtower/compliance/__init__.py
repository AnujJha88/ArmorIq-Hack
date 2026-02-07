"""
Universal Compliance Engine
===========================
Enterprise-wide policy evaluation across all domains.
"""

from .engine import ComplianceEngine, ComplianceResult, get_compliance_engine
from .policies.base import Policy, PolicyCategory, PolicyAction, PolicySeverity

__all__ = [
    "ComplianceEngine",
    "ComplianceResult",
    "get_compliance_engine",
    "Policy",
    "PolicyCategory",
    "PolicyAction",
    "PolicySeverity",
]
