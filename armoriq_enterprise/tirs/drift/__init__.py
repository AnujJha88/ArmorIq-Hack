"""
TIRS Drift Detection Module
===========================
Multi-signal drift detection with temporal awareness.
"""

from .detector import DriftDetector, DriftSignal, SignalWeight
from .embeddings import EmbeddingEngine, get_embedding_engine
from .temporal import TemporalDecay, VelocityTracker
from .contextual import ContextualThresholds, BusinessContext

__all__ = [
    "DriftDetector",
    "DriftSignal",
    "SignalWeight",
    "EmbeddingEngine",
    "get_embedding_engine",
    "TemporalDecay",
    "VelocityTracker",
    "ContextualThresholds",
    "BusinessContext",
]
