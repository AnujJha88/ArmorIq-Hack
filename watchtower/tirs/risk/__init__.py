"""
TIRS Risk Scoring Module
========================
Composite risk scoring with dynamic thresholds.
"""

from .scorer import RiskScorer, CompositeRiskScore
from .thresholds import DynamicThresholds, ThresholdAdjuster
from .profiles import BehavioralProfile, ProfileMatcher

__all__ = [
    "RiskScorer",
    "CompositeRiskScore",
    "DynamicThresholds",
    "ThresholdAdjuster",
    "BehavioralProfile",
    "ProfileMatcher",
]
