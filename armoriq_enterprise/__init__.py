"""
ArmorIQ Enterprise Agentic System
=================================
A large-scale, production-grade agentic system with:
- Advanced TIRS Drift Detection
- 6 Domain Agents (Finance, Legal, IT, HR, Procurement, Operations)
- Universal Corporate Compliance Engine
- Google ADK Orchestration
"""

__version__ = "1.0.0"
__author__ = "ArmorIQ"

from .tirs import AdvancedTIRS, get_advanced_tirs
from .compliance import ComplianceEngine, get_compliance_engine
from .orchestrator import EnterpriseGateway, get_gateway

__all__ = [
    "AdvancedTIRS",
    "get_advanced_tirs",
    "ComplianceEngine",
    "get_compliance_engine",
    "EnterpriseGateway",
    "get_gateway",
]
