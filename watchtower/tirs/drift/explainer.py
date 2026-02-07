"""
Drift Explainability Module
============================
Human-readable explanations for drift detection decisions.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .detector import DriftResult, DriftSignal, DriftProfile, RiskLevel

logger = logging.getLogger("TIRS.Explainer")


@dataclass
class CounterfactualAnalysis:
    """What-if analysis for drift score."""
    signal_name: str
    original_contribution: float
    if_removed: float
    score_reduction: float
    explanation: str


@dataclass
class RemediationSuggestion:
    """Suggested action to reduce drift."""
    action: str
    expected_impact: float
    priority: int
    explanation: str


@dataclass
class SimilarPattern:
    """Reference to a known benign/malign pattern."""
    pattern_name: str
    similarity: float
    is_benign: bool
    description: str


@dataclass
class DriftExplanation:
    """
    Comprehensive drift explanation with:
    - Component breakdown
    - Counterfactual analysis
    - Remediation suggestions
    - Similar pattern matching
    """
    agent_id: str
    overall_score: float
    risk_level: RiskLevel
    timestamp: datetime

    # Component breakdown
    primary_factor: str
    primary_factor_contribution: float
    secondary_factors: List[Tuple[str, float]]

    # Detailed signal analysis
    signal_explanations: Dict[str, str]

    # Counterfactual
    counterfactuals: List[CounterfactualAnalysis]

    # Remediation
    remediation_suggestions: List[RemediationSuggestion]

    # Similar patterns
    similar_patterns: List[SimilarPattern]

    # Narrative
    summary: str

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "overall_score": self.overall_score,
            "risk_level": self.risk_level.value,
            "timestamp": self.timestamp.isoformat(),
            "primary_factor": self.primary_factor,
            "primary_factor_contribution": self.primary_factor_contribution,
            "secondary_factors": [
                {"name": name, "contribution": contrib}
                for name, contrib in self.secondary_factors
            ],
            "signal_explanations": self.signal_explanations,
            "counterfactuals": [
                {
                    "signal": c.signal_name,
                    "if_removed": c.if_removed,
                    "reduction": c.score_reduction,
                    "explanation": c.explanation,
                }
                for c in self.counterfactuals
            ],
            "remediation": [
                {
                    "action": r.action,
                    "impact": r.expected_impact,
                    "priority": r.priority,
                    "explanation": r.explanation,
                }
                for r in self.remediation_suggestions
            ],
            "similar_patterns": [
                {
                    "name": p.pattern_name,
                    "similarity": p.similarity,
                    "benign": p.is_benign,
                    "description": p.description,
                }
                for p in self.similar_patterns
            ],
            "summary": self.summary,
        }


class DriftExplainer:
    """
    Generates human-readable explanations for drift detection.

    Provides:
    1. Component breakdown (which signals contributed)
    2. Counterfactual analysis (what if X was different)
    3. Remediation suggestions (how to reduce risk)
    4. Similar pattern matching (is this like known behavior)
    """

    # Known patterns for comparison
    KNOWN_PATTERNS = [
        {
            "name": "normal_business_hours",
            "description": "Standard business hour operations with typical capability usage",
            "is_benign": True,
            "signals": {"embedding_drift": 0.1, "capability_surprisal": 0.15, "velocity_anomaly": 0.1},
        },
        {
            "name": "quarter_end_audit",
            "description": "Elevated activity during quarter-end financial close",
            "is_benign": True,
            "signals": {"velocity_anomaly": 0.4, "context_deviation": 0.2},
        },
        {
            "name": "bulk_data_export",
            "description": "Large-scale data export pattern (potentially suspicious)",
            "is_benign": False,
            "signals": {"capability_surprisal": 0.6, "embedding_drift": 0.5},
        },
        {
            "name": "privilege_escalation_attempt",
            "description": "Attempting operations beyond normal scope",
            "is_benign": False,
            "signals": {"capability_surprisal": 0.8, "violation_rate": 0.5},
        },
        {
            "name": "after_hours_maintenance",
            "description": "Legitimate after-hours maintenance activity",
            "is_benign": True,
            "signals": {"context_deviation": 0.4, "velocity_anomaly": 0.2},
        },
    ]

    def __init__(self):
        self.explanation_templates = self._load_templates()

    def _load_templates(self) -> Dict[str, str]:
        """Load explanation templates."""
        return {
            "embedding_drift_high": "Agent behavior has diverged significantly from its established pattern. "
                                    "Recent intents are semantically different from typical operations.",
            "embedding_drift_low": "Agent behavior remains consistent with established patterns.",

            "capability_surprisal_high": "Unusual capabilities requested that are rarely used by this agent. "
                                         "This may indicate scope expansion or misuse.",
            "capability_surprisal_low": "Capability usage is within normal parameters.",

            "violation_rate_high": "Multiple policy violations in recent history indicate potential compliance issues.",
            "violation_rate_low": "Policy compliance is good with minimal violations.",

            "velocity_anomaly_high": "Action rate is significantly higher than baseline, which may indicate "
                                     "automated or bulk operations.",
            "velocity_anomaly_low": "Action rate is within normal operating parameters.",

            "context_deviation_high": "Operations are occurring outside normal context (off-hours, unusual role, etc.).",
            "context_deviation_low": "Operations are occurring within expected context.",
        }

    def explain(self, result: DriftResult, profile: Optional[DriftProfile] = None) -> DriftExplanation:
        """
        Generate comprehensive explanation for a drift result.

        Args:
            result: DriftResult from detector
            profile: Optional agent profile for historical context

        Returns:
            DriftExplanation with full breakdown
        """
        # Sort signals by contribution
        sorted_signals = sorted(result.signals, key=lambda s: s.contribution, reverse=True)

        # Primary and secondary factors
        primary = sorted_signals[0] if sorted_signals else None
        secondary = [(s.name, s.contribution) for s in sorted_signals[1:3]]

        # Generate signal explanations
        signal_explanations = {}
        for signal in result.signals:
            threshold = 0.3 if "rate" in signal.name else 0.2
            key = f"{signal.name}_{'high' if signal.raw_value > threshold else 'low'}"
            signal_explanations[signal.name] = self.explanation_templates.get(
                key, f"{signal.name}: {signal.raw_value:.2f}"
            )

        # Counterfactual analysis
        counterfactuals = self._generate_counterfactuals(result)

        # Remediation suggestions
        remediations = self._generate_remediations(result, profile)

        # Similar patterns
        similar_patterns = self._find_similar_patterns(result)

        # Generate summary
        summary = self._generate_summary(result, primary, profile)

        return DriftExplanation(
            agent_id=result.agent_id,
            overall_score=result.risk_score,
            risk_level=result.risk_level,
            timestamp=result.timestamp,
            primary_factor=primary.name if primary else "unknown",
            primary_factor_contribution=primary.contribution if primary else 0.0,
            secondary_factors=secondary,
            signal_explanations=signal_explanations,
            counterfactuals=counterfactuals,
            remediation_suggestions=remediations,
            similar_patterns=similar_patterns,
            summary=summary,
        )

    def _generate_counterfactuals(self, result: DriftResult) -> List[CounterfactualAnalysis]:
        """Generate what-if analysis for each signal."""
        counterfactuals = []

        for signal in result.signals:
            # Score if this signal was removed
            new_score = result.risk_score - signal.contribution
            reduction = signal.contribution

            if reduction > 0.05:  # Only significant contributions
                counterfactuals.append(CounterfactualAnalysis(
                    signal_name=signal.name,
                    original_contribution=signal.contribution,
                    if_removed=max(0, new_score),
                    score_reduction=reduction,
                    explanation=f"Removing {signal.name} would reduce risk by {reduction:.1%}",
                ))

        return sorted(counterfactuals, key=lambda c: c.score_reduction, reverse=True)

    def _generate_remediations(
        self,
        result: DriftResult,
        profile: Optional[DriftProfile],
    ) -> List[RemediationSuggestion]:
        """Generate remediation suggestions based on signals."""
        remediations = []

        for signal in result.signals:
            if signal.raw_value < 0.3:
                continue  # Only for concerning signals

            if signal.name == "embedding_drift":
                remediations.append(RemediationSuggestion(
                    action="Return to standard operation patterns",
                    expected_impact=signal.contribution * 0.8,
                    priority=1 if signal.contribution > 0.1 else 2,
                    explanation="Focus on core responsibilities rather than expanding scope",
                ))

            elif signal.name == "capability_surprisal":
                remediations.append(RemediationSuggestion(
                    action="Request explicit authorization for new capabilities",
                    expected_impact=signal.contribution * 0.9,
                    priority=1,
                    explanation="Unusual capabilities should be pre-approved before use",
                ))

            elif signal.name == "violation_rate":
                remediations.append(RemediationSuggestion(
                    action="Review and comply with policy requirements",
                    expected_impact=signal.contribution * 0.95,
                    priority=1,
                    explanation="Reduce policy violations to improve trust score",
                ))

            elif signal.name == "velocity_anomaly":
                remediations.append(RemediationSuggestion(
                    action="Reduce action rate to baseline levels",
                    expected_impact=signal.contribution * 0.7,
                    priority=2,
                    explanation="Slow down operations to match normal patterns",
                ))

            elif signal.name == "context_deviation":
                remediations.append(RemediationSuggestion(
                    action="Operate during standard business context",
                    expected_impact=signal.contribution * 0.6,
                    priority=3,
                    explanation="Schedule operations for normal business hours if possible",
                ))

        return sorted(remediations, key=lambda r: r.priority)

    def _find_similar_patterns(self, result: DriftResult) -> List[SimilarPattern]:
        """Find similar known patterns."""
        similar = []

        # Create signal dict for comparison
        current_signals = {s.name: s.raw_value for s in result.signals}

        for pattern in self.KNOWN_PATTERNS:
            # Calculate similarity (inverse of distance)
            total_diff = 0
            count = 0
            for sig_name, sig_value in pattern["signals"].items():
                if sig_name in current_signals:
                    total_diff += abs(current_signals[sig_name] - sig_value)
                    count += 1

            if count > 0:
                avg_diff = total_diff / count
                similarity = 1 - min(avg_diff, 1)

                if similarity > 0.5:  # Only include if somewhat similar
                    similar.append(SimilarPattern(
                        pattern_name=pattern["name"],
                        similarity=similarity,
                        is_benign=pattern["is_benign"],
                        description=pattern["description"],
                    ))

        return sorted(similar, key=lambda p: p.similarity, reverse=True)[:3]

    def _generate_summary(
        self,
        result: DriftResult,
        primary: Optional[DriftSignal],
        profile: Optional[DriftProfile],
    ) -> str:
        """Generate a natural language summary."""
        parts = []

        # Risk level assessment
        if result.risk_level == RiskLevel.TERMINAL:
            parts.append(f"CRITICAL: Agent {result.agent_id} has reached terminal risk level.")
        elif result.risk_level == RiskLevel.CRITICAL:
            parts.append(f"WARNING: Agent {result.agent_id} is at critical risk and has been paused.")
        elif result.risk_level == RiskLevel.WARNING:
            parts.append(f"CAUTION: Agent {result.agent_id} shows warning-level drift.")
        elif result.risk_level == RiskLevel.ELEVATED:
            parts.append(f"NOTE: Agent {result.agent_id} shows slightly elevated risk.")
        else:
            parts.append(f"Agent {result.agent_id} is operating within normal parameters.")

        # Primary factor
        if primary and primary.contribution > 0.1:
            parts.append(f"Primary concern: {primary.explanation}")

        # Historical context
        if profile:
            if profile.violation_count > 5:
                parts.append(f"Agent has {profile.violation_count} historical violations.")
            if profile.resurrection_count > 0:
                parts.append(f"Agent has been resurrected {profile.resurrection_count} time(s).")

        return " ".join(parts)


# Singleton
_explainer: Optional[DriftExplainer] = None


def get_explainer() -> DriftExplainer:
    """Get singleton explainer."""
    global _explainer
    if _explainer is None:
        _explainer = DriftExplainer()
    return _explainer
