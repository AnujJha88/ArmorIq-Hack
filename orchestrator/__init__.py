"""
Watchtower Orchestrator
====================
Multi-agent orchestration with cryptographic intent verification.

Components:
- Orchestrator: Central coordinator for pipelines
- Registry: Agent capability routing
- Context: Pipeline state management
- Agents: Task executors
- Policies: Rule enforcement
- Drift: TIRS-based drift detection
- Approvals: Human-in-the-loop workflows
- Persistence: State storage and audit
- Tools: Agent tool integrations
"""

from orchestrator.registry import (
    AgentRegistry,
    AgentCapability,
    AgentStatus,
    AgentInfo,
    get_registry
)

from orchestrator.context import (
    PipelineContext,
    Task,
    TaskResult,
    TaskStatus
)

from orchestrator.orchestrator import (
    Orchestrator,
    ExecutionConfig,
    HandoffVerification,
    get_orchestrator
)

from orchestrator.agents import (
    BaseAgent,
    SourcerAgent,
    ScreenerAgent,
    SchedulerAgent,
    NegotiatorAgent,
    OnboarderAgent,
    ComplianceAgent,
    create_all_agents
)

from orchestrator.policies import (
    PolicyEngine,
    PolicyAction,
    PolicySeverity,
    PolicyResult,
    Policy,
    get_policy_engine
)

from orchestrator.drift import (
    DriftDetector,
    DriftLevel,
    DriftAlert,
    AlertType,
    get_drift_detector
)

from orchestrator.approvals import (
    ApprovalManager,
    ApprovalWorkflow,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalType,
    get_approval_manager
)

from orchestrator.persistence import (
    StateStore,
    AuditLogger,
    AuditEvent,
    AuditEventType,
    get_state_store,
    get_audit_logger
)

from orchestrator.tools import (
    ToolRegistry,
    BaseTool,
    ToolCategory,
    RiskLevel,
    get_tool_registry
)

__all__ = [
    # Core
    'Orchestrator',
    'ExecutionConfig',
    'HandoffVerification',
    'get_orchestrator',

    # Registry
    'AgentRegistry',
    'AgentCapability',
    'AgentStatus',
    'AgentInfo',
    'get_registry',

    # Context
    'PipelineContext',
    'Task',
    'TaskResult',
    'TaskStatus',

    # Agents
    'BaseAgent',
    'SourcerAgent',
    'ScreenerAgent',
    'SchedulerAgent',
    'NegotiatorAgent',
    'OnboarderAgent',
    'ComplianceAgent',
    'create_all_agents',

    # Policies
    'PolicyEngine',
    'PolicyAction',
    'PolicySeverity',
    'PolicyResult',
    'Policy',
    'get_policy_engine',

    # Drift
    'DriftDetector',
    'DriftLevel',
    'DriftAlert',
    'AlertType',
    'get_drift_detector',

    # Approvals
    'ApprovalManager',
    'ApprovalWorkflow',
    'ApprovalRequest',
    'ApprovalStatus',
    'ApprovalType',
    'get_approval_manager',

    # Persistence
    'StateStore',
    'AuditLogger',
    'AuditEvent',
    'AuditEventType',
    'get_state_store',
    'get_audit_logger',

    # Tools
    'ToolRegistry',
    'BaseTool',
    'ToolCategory',
    'RiskLevel',
    'get_tool_registry',
]

__version__ = '2.0.0'
