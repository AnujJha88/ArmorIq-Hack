"""
MCP Stubs for TIRS Simulation
=============================
Mock MCP endpoints for dry-run simulations.

These stubs simulate real MCP calls without side effects,
allowing TIRS to test plans before execution.
"""

from typing import Dict, Any

# Re-export stubs from simulator
from tirs.simulator import (
    MCPStub,
    HRISStub,
    EmailStub,
    CalendarStub,
    PayrollStub,
    OfferStub,
    PerformanceStub
)

__all__ = [
    "MCPStub",
    "HRISStub",
    "EmailStub",
    "CalendarStub",
    "PayrollStub",
    "OfferStub",
    "PerformanceStub",
    "get_stub",
    "get_all_stubs"
]


def get_stub(name: str) -> MCPStub:
    """Get a specific MCP stub by name."""
    stubs = {
        "HRIS": HRISStub,
        "Email": EmailStub,
        "Calendar": CalendarStub,
        "Payroll": PayrollStub,
        "Offer": OfferStub,
        "Performance": PerformanceStub
    }
    if name not in stubs:
        raise ValueError(f"Unknown MCP stub: {name}")
    return stubs[name]()


def get_all_stubs() -> Dict[str, MCPStub]:
    """Get all available MCP stubs."""
    return {
        "HRIS": HRISStub(),
        "Email": EmailStub(),
        "Calendar": CalendarStub(),
        "Payroll": PayrollStub(),
        "Offer": OfferStub(),
        "Performance": PerformanceStub()
    }
