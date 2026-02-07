"""
Advanced TIRS (Temporal Intent Risk & Simulation) Engine
=========================================================
Multi-signal drift detection with:
- Temporal decay (exponential, configurable half-life)
- Context-aware thresholds (time, role, season)
- Explainable risk scores (component breakdown)
- Distributed persistence support
"""

from .engine import AdvancedTIRS, get_advanced_tirs
from .drift.detector import DriftDetector, DriftSignal
from .drift.explainer import DriftExplainer, DriftExplanation
from .risk.scorer import RiskScorer, CompositeRiskScore
from .enforcement.actions import EnforcementAction, ActionType
from .forensics.snapshot import ForensicSnapshot

__all__ = [
    "AdvancedTIRS",
    "get_advanced_tirs",
    "DriftDetector",
    "DriftSignal",
    "DriftExplainer",
    "DriftExplanation",
    "RiskScorer",
    "CompositeRiskScore",
    "EnforcementAction",
    "ActionType",
    "ForensicSnapshot",
]
