"""
Enterprise Orchestrator
=======================
ADK-style orchestration for multi-agent workflows.
Now with dynamic workflow generation and agent collaboration.
"""

from .gateway import EnterpriseGateway, get_gateway, initialize_gateway
from .router import CapabilityRouter
from .handoff import HandoffVerifier, HandoffResult
from .workflows import (
    WorkflowEngine,
    SequentialWorkflow,
    ParallelWorkflow,
    LoopWorkflow,
    ConditionalWorkflow,
)
from .workflow_generator import (
    DynamicWorkflowGenerator,
    WorkflowDesign,
    WorkflowPattern,
    WorkflowTemplates,
    get_workflow_generator,
)
from .collaboration import (
    CollaborationHub,
    AgentMessage,
    MessageType,
    Negotiation,
    NegotiationStatus,
    SharedContext,
    get_collaboration_hub,
)

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
    "LoopWorkflow",
    "ConditionalWorkflow",
    "DynamicWorkflowGenerator",
    "WorkflowDesign",
    "WorkflowPattern",
    "WorkflowTemplates",
    "get_workflow_generator",
    "CollaborationHub",
    "AgentMessage",
    "MessageType",
    "Negotiation",
    "NegotiationStatus",
    "SharedContext",
    "get_collaboration_hub",
]
