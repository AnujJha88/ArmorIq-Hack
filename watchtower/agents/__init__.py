"""
Enterprise Domain Agents
========================
Explicit domain agents for all enterprise functions.
"""

from .base_agent import EnterpriseAgent, AgentCapability
from .finance_agent import FinanceAgent
from .legal_agent import LegalAgent
from .it_agent import ITAgent
from .hr_agent import HRAgent
from .procurement_agent import ProcurementAgent
from .operations_agent import OperationsAgent

__all__ = [
    "EnterpriseAgent",
    "AgentCapability",
    "FinanceAgent",
    "LegalAgent",
    "ITAgent",
    "HRAgent",
    "ProcurementAgent",
    "OperationsAgent",
]


def create_all_agents():
    """Create instances of all domain agents."""
    return [
        FinanceAgent(),
        LegalAgent(),
        ITAgent(),
        HRAgent(),
        ProcurementAgent(),
        OperationsAgent(),
    ]
