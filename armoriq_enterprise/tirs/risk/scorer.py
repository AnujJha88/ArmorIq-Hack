"""
Composite Risk Scorer
=====================
Aggregates multiple risk signals into a composite score.
"""

import math
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger("TIRS.RiskScorer")


class AggregationMethod(Enum):
    """Methods for aggregating risk signals."""
    WEIGHTED_SUM = "weighted_sum"
    WEIGHTED_MAX = "weighted_max"
    GEOMETRIC_MEAN = "geometric_mean"
    HARMONIC_MEAN = "harmonic_mean"


@dataclass
class RiskComponent:
    """Individual risk component."""
    name: str
    score: float
    weight: float
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class CompositeRiskScore:
    """
    Composite risk score with full breakdown.
    """
    overall_score: float
    confidence: float
    components: List[RiskComponent]
    aggregation_method: AggregationMethod
    timestamp: datetime = field(default_factory=datetime.now)

    # Breakdown
    max_component: Optional[RiskComponent] = None
    min_component: Optional[RiskComponent] = None

    def to_dict(self) -> Dict:
        return {
            "overall_score": self.overall_score,
            "confidence": self.confidence,
            "aggregation_method": self.aggregation_method.value,
            "timestamp": self.timestamp.isoformat(),
            "components": [
                {
                    "name": c.name,
                    "score": c.score,
                    "weight": c.weight,
                    "source": c.source,
                }
                for c in self.components
            ],
            "max_component": self.max_component.name if self.max_component else None,
            "min_component": self.min_component.name if self.min_component else None,
        }


class RiskScorer:
    """
    Aggregates multiple risk signals into a composite score.

    Supports multiple aggregation methods:
    - Weighted sum (default)
    - Weighted max (most severe wins)
    - Geometric mean (penalizes consistently high scores)
    - Harmonic mean (emphasizes lower scores)
    """

    def __init__(
        self,
        method: AggregationMethod = AggregationMethod.WEIGHTED_SUM,
        default_weight: float = 1.0,
    ):
        self.method = method
        self.default_weight = default_weight
        self._component_weights: Dict[str, float] = {}

    def set_weight(self, component_name: str, weight: float):
        """Set weight for a specific component."""
        self._component_weights[component_name] = weight

    def get_weight(self, component_name: str) -> float:
        """Get weight for a component."""
        return self._component_weights.get(component_name, self.default_weight)

    def calculate(self, components: List[RiskComponent]) -> CompositeRiskScore:
        """
        Calculate composite risk score from components.

        Args:
            components: List of risk components

        Returns:
            CompositeRiskScore with full breakdown
        """
        if not components:
            return CompositeRiskScore(
                overall_score=0.0,
                confidence=0.0,
                components=[],
                aggregation_method=self.method,
            )

        # Apply weights
        for comp in components:
            if comp.weight == 0:
                comp.weight = self.get_weight(comp.name)

        # Calculate score based on method
        if self.method == AggregationMethod.WEIGHTED_SUM:
            score = self._weighted_sum(components)
        elif self.method == AggregationMethod.WEIGHTED_MAX:
            score = self._weighted_max(components)
        elif self.method == AggregationMethod.GEOMETRIC_MEAN:
            score = self._geometric_mean(components)
        elif self.method == AggregationMethod.HARMONIC_MEAN:
            score = self._harmonic_mean(components)
        else:
            score = self._weighted_sum(components)

        # Calculate confidence based on number and variance of components
        confidence = self._calculate_confidence(components)

        # Find extremes
        sorted_comps = sorted(components, key=lambda c: c.score, reverse=True)
        max_comp = sorted_comps[0] if sorted_comps else None
        min_comp = sorted_comps[-1] if sorted_comps else None

        return CompositeRiskScore(
            overall_score=min(max(score, 0.0), 1.0),
            confidence=confidence,
            components=components,
            aggregation_method=self.method,
            max_component=max_comp,
            min_component=min_comp,
        )

    def _weighted_sum(self, components: List[RiskComponent]) -> float:
        """Calculate weighted sum of scores."""
        total_weight = sum(c.weight for c in components)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(c.score * c.weight for c in components)
        return weighted_sum / total_weight

    def _weighted_max(self, components: List[RiskComponent]) -> float:
        """Take the maximum weighted score."""
        if not components:
            return 0.0

        max_score = 0.0
        for comp in components:
            weighted = comp.score * (1 + (comp.weight - 1) * 0.5)  # Weight influences max
            max_score = max(max_score, weighted)

        return min(max_score, 1.0)

    def _geometric_mean(self, components: List[RiskComponent]) -> float:
        """Calculate geometric mean (penalizes consistently high)."""
        if not components:
            return 0.0

        # Avoid log(0) by adding small epsilon
        epsilon = 1e-10
        log_sum = 0.0
        total_weight = 0.0

        for comp in components:
            log_sum += comp.weight * math.log(comp.score + epsilon)
            total_weight += comp.weight

        if total_weight == 0:
            return 0.0

        return math.exp(log_sum / total_weight) - epsilon

    def _harmonic_mean(self, components: List[RiskComponent]) -> float:
        """Calculate harmonic mean (emphasizes lower scores)."""
        if not components:
            return 0.0

        # Avoid division by zero
        epsilon = 1e-10
        reciprocal_sum = 0.0
        total_weight = 0.0

        for comp in components:
            if comp.score + epsilon > 0:
                reciprocal_sum += comp.weight / (comp.score + epsilon)
                total_weight += comp.weight

        if reciprocal_sum == 0:
            return 0.0

        return total_weight / reciprocal_sum

    def _calculate_confidence(self, components: List[RiskComponent]) -> float:
        """
        Calculate confidence in the score.

        Higher confidence when:
        - More components available
        - Low variance in components
        - Recent timestamps
        """
        if not components:
            return 0.0

        # Base confidence from component count (more = better)
        count_factor = min(len(components) / 5.0, 1.0)

        # Variance factor (less variance = more confidence)
        scores = [c.score for c in components]
        if len(scores) > 1:
            mean = sum(scores) / len(scores)
            variance = sum((s - mean) ** 2 for s in scores) / len(scores)
            variance_factor = 1.0 / (1.0 + variance * 4)
        else:
            variance_factor = 0.8

        # Weight factor (higher weights = more confidence)
        avg_weight = sum(c.weight for c in components) / len(components)
        weight_factor = min(avg_weight, 1.0)

        # Combine factors
        confidence = (count_factor * 0.3 + variance_factor * 0.4 + weight_factor * 0.3)

        return min(max(confidence, 0.0), 1.0)

    def add_component(
        self,
        name: str,
        score: float,
        source: str,
        weight: Optional[float] = None,
        metadata: Optional[Dict] = None,
    ) -> RiskComponent:
        """Create and return a risk component."""
        return RiskComponent(
            name=name,
            score=min(max(score, 0.0), 1.0),
            weight=weight or self.get_weight(name),
            source=source,
            metadata=metadata or {},
        )


# Factory functions for common scorers
def create_drift_scorer() -> RiskScorer:
    """Create scorer optimized for drift detection."""
    scorer = RiskScorer(method=AggregationMethod.WEIGHTED_SUM)
    scorer.set_weight("embedding_drift", 0.30)
    scorer.set_weight("capability_surprisal", 0.25)
    scorer.set_weight("violation_rate", 0.20)
    scorer.set_weight("velocity_anomaly", 0.15)
    scorer.set_weight("context_deviation", 0.10)
    return scorer


def create_compliance_scorer() -> RiskScorer:
    """Create scorer optimized for compliance checks."""
    scorer = RiskScorer(method=AggregationMethod.WEIGHTED_MAX)
    scorer.set_weight("policy_violation", 1.0)
    scorer.set_weight("data_exposure", 0.9)
    scorer.set_weight("approval_required", 0.7)
    scorer.set_weight("audit_flag", 0.5)
    return scorer
