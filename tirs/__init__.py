"""
TIRS: Temporal Intent Risk & Simulation
========================================
A temporal, simulation-backed intent risk layer for AI agents.

Components:
- drift_engine: Temporal behavior drift detection
- simulator: Plan dry-run before execution
- audit: Cryptographically signed forensic logs
- remediation: Auto-fix policy suggestions
- embeddings: Intent embedding generation
- core: Unified TIRS interface
"""

__version__ = "0.1.0"

# Lazy imports to avoid circular dependencies
def get_tirs():
    from .core import get_tirs as _get_tirs
    return _get_tirs()

def get_drift_engine():
    from .drift_engine import get_drift_engine as _get_drift_engine
    return _get_drift_engine()

def get_simulator():
    from .simulator import get_simulator as _get_simulator
    return _get_simulator()

def get_audit_ledger():
    from .audit import get_audit_ledger as _get_audit_ledger
    return _get_audit_ledger()

def get_remediation_engine():
    from .remediation import get_remediation_engine as _get_remediation_engine
    return _get_remediation_engine()
