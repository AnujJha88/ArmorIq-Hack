"""
Enterprise Orchestrator
=======================
ADK-style orchestration for multi-agent workflows.
"""

from .gateway import EnterpriseGateway, get_gateway, initialize_gateway
from .router import CapabilityRouter
from .handoff import HandoffVerifier, HandoffResult
from .workflows import WorkflowEngine, SequentialWorkflow, ParallelWorkflow

__all__ = [
    "EnterpriseGateway",
    "get_gateway",
    "initialize_gateway",
    "CapabilityRouter",
    "HandoffVerifier",
    "HandoffResult",
    "WorkflowEngine",
    "SequentialWorkflow",
    "ParallelWorkflow",
]
