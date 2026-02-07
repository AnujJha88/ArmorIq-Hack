# Watchtower One Enterprise Agentic System

A large-scale, production-grade enterprise agentic system with advanced drift detection, compliance enforcement, and multi-agent orchestration.

## Architecture Overview

```
                              ┌─────────────────────────────────────┐
                              │         ENTERPRISE GATEWAY          │
                              │   (ADK-Style Root Orchestrator)     │
                              └─────────────────┬───────────────────┘
                                                │
        ┌───────────────────────────────────────┼───────────────────────────────────────┐
        │                                       │                                       │
        ▼                                       ▼                                       ▼
┌───────────────┐                     ┌─────────────────┐                     ┌───────────────┐
│  COMPLIANCE   │◄────────────────────│   TIRS ENGINE   │────────────────────►│    AUDIT      │
│    ENGINE     │   Policy Check      │ (Drift Detection)│   Forensics        │    LEDGER     │
└───────────────┘                     └─────────────────┘                     └───────────────┘
        │                                       │                                       │
        ▼                                       ▼                                       ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                              AGENT MESH (Multi-Agent System)                              │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│   FINANCE   │    LEGAL    │     IT      │     HR      │ PROCUREMENT │    OPERATIONS       │
│   Agent     │   Agent     │   Agent     │   Agent     │   Agent     │      Agent          │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
```

## Features

### 1. Advanced TIRS Drift Detection (THE STAR)

The Temporal Intent Risk & Simulation (TIRS) engine provides multi-signal drift detection:

| Signal | Weight | Description |
|--------|--------|-------------|
| Embedding Drift | 30% | Semantic divergence from behavioral centroid |
| Capability Surprisal | 25% | Information-theoretic surprisal score |
| Violation Rate | 20% | Recent policy violation frequency |
| Velocity Anomaly | 15% | Action rate vs established baseline |
| Context Deviation | 10% | Time/role/department mismatches |

**Risk Levels:**
- `NOMINAL` (0.0-0.3): Normal operation
- `ELEVATED` (0.3-0.5): Heightened monitoring
- `WARNING` (0.5-0.7): Alert + throttling
- `CRITICAL` (0.7-0.85): Auto-pause
- `TERMINAL` (0.85+): Auto-kill

**Key Capabilities:**
- Temporal decay with configurable half-life
- Context-aware thresholds (time-of-day, role, season)
- Human-readable drift explanations
- Counterfactual analysis ("what if X was removed?")
- Forensic snapshots with hash chain
- Cryptographic audit trail
- Resurrection workflow with admin approval

### 2. Universal Compliance Engine

28 policies across 7 domains:

| Domain | Policies | Frameworks |
|--------|----------|------------|
| Financial | Expense limits, budget controls, invoice approval, SOX | SOX |
| Legal | Contract review, NDA enforcement, IP protection, litigation hold | - |
| Security | Access control, data classification, change management | ISO 27001 |
| HR | Hiring compliance, compensation bands, termination | FCRA, EEOC, IRCA |
| Procurement | Vendor approval, spending limits, bid requirements | - |
| Operations | SLA compliance, ITIL processes, maintenance windows | ITIL |
| Data Privacy | PII protection, consent, retention, cross-border | GDPR, CCPA, HIPAA |

### 3. Domain Agents

| Agent | Capabilities | Description |
|-------|-------------|-------------|
| **Finance** | 8 | Expenses, budgets, invoices, audits, payments |
| **Legal** | 5 | Contracts, NDAs, IP review, litigation |
| **IT** | 6 | Access control, security, incidents, assets |
| **HR** | 8 | Hiring, onboarding, payroll, benefits, offboarding |
| **Procurement** | 5 | Vendors, purchases, bids, inventory |
| **Operations** | 4 | Incidents, changes, SLAs, maintenance |

### 4. Workflow Orchestration

Pre-built workflow patterns:
- **Sequential**: Steps execute one after another
- **Parallel**: Independent steps execute concurrently
- **Loop**: Repeat until condition met

Pre-registered workflows:
- `wf_new_hire`: New employee onboarding (HR → IT → Finance)
- `wf_vendor_onboard`: Vendor onboarding (Procurement → Legal → Finance → IT)
- `wf_expense`: Expense processing (Finance)

## Installation

```bash
# Install dependencies
pip install numpy

# Optional: For better embeddings
pip install sentence-transformers
```

## Quick Start

```python
import asyncio
from watchtower.orchestrator import initialize_gateway

async def main():
    # Initialize the gateway
    gateway = await initialize_gateway()

    # Process a single request
    result = await gateway.process_request(
        action="process_expense",
        payload={"amount": 500, "category": "travel"},
        context={"user": "alice@acme.com"}
    )

    print(f"Success: {result.success}")
    print(f"Risk Score: {result.risk_score}")
    print(f"Risk Level: {result.risk_level}")

    # Execute a workflow
    wf_result = await gateway.execute_workflow(
        workflow_id="wf_new_hire",
        parameters={"candidate_name": "Jane Smith", "position": "Engineer"}
    )

    print(f"Workflow: {wf_result.status.value}")
    print(f"Steps: {wf_result.completed_steps}/{wf_result.total_steps}")

asyncio.run(main())
```

## Running the Demo

```bash
# Quick validation
python -m watchtower.demo.enterprise_demo --quick

# Full demonstration
python -m watchtower.demo.enterprise_demo

# Specific section
python -m watchtower.demo.enterprise_demo --section agents
python -m watchtower.demo.enterprise_demo --section workflows
python -m watchtower.demo.enterprise_demo --section compliance
python -m watchtower.demo.enterprise_demo --section drift
python -m watchtower.demo.enterprise_demo --section forensics
```

## Project Structure

```
watchtower/
├── __init__.py                 # Main package exports
├── README.md                   # This file
│
├── agents/                     # Domain Agents
│   ├── base_agent.py          # Base class with TIRS/compliance hooks
│   ├── finance_agent.py       # Finance operations
│   ├── legal_agent.py         # Legal operations
│   ├── it_agent.py            # IT operations
│   ├── hr_agent.py            # HR operations
│   ├── procurement_agent.py   # Procurement operations
│   └── operations_agent.py    # Operations management
│
├── compliance/                 # Compliance Engine
│   ├── engine.py              # Central policy evaluation
│   ├── policies/              # Policy implementations
│   │   ├── base.py            # Base policy class
│   │   ├── financial.py       # SOX, expense limits
│   │   ├── legal.py           # Contracts, NDAs
│   │   ├── security.py        # Access control
│   │   ├── hr.py              # Employment law
│   │   ├── procurement.py     # Vendor policies
│   │   ├── operations.py      # SLA, ITIL
│   │   └── data_privacy.py    # GDPR, HIPAA, CCPA
│   └── frameworks/            # Regulatory frameworks
│       ├── sox.py
│       ├── gdpr.py
│       ├── hipaa.py
│       ├── pci_dss.py
│       └── iso27001.py
│
├── tirs/                       # TIRS Drift Detection
│   ├── engine.py              # Main TIRS engine
│   ├── drift/                 # Drift detection
│   │   ├── detector.py        # Multi-signal detector
│   │   ├── embeddings.py      # Intent embeddings
│   │   ├── temporal.py        # Temporal decay
│   │   ├── contextual.py      # Context-aware thresholds
│   │   └── explainer.py       # Drift explanations
│   ├── risk/                  # Risk scoring
│   │   ├── scorer.py          # Composite scoring
│   │   ├── thresholds.py      # Dynamic thresholds
│   │   └── profiles.py        # Behavioral profiles
│   ├── enforcement/           # Enforcement actions
│   │   ├── actions.py         # PAUSE, KILL, etc.
│   │   ├── remediation.py     # Auto-remediation
│   │   └── appeals.py         # Resurrection workflow
│   └── forensics/             # Forensic capabilities
│       ├── snapshot.py        # State capture
│       ├── timeline.py        # Event timeline
│       └── audit.py           # Cryptographic audit
│
├── orchestrator/              # ADK Orchestration
│   ├── gateway.py             # Root orchestrator
│   ├── router.py              # Capability routing
│   ├── handoff.py             # Agent handoffs
│   └── workflows/             # Workflow patterns
│       ├── engine.py          # Workflow engine
│       ├── sequential.py      # Sequential execution
│       ├── parallel.py        # Parallel execution
│       └── loop.py            # Loop execution
│
└── demo/                      # Demonstration
    └── enterprise_demo.py     # Full demo script
```

## API Reference

### EnterpriseGateway

```python
gateway = await initialize_gateway()

# Process a request
result = await gateway.process_request(action, payload, context)

# Execute a workflow
wf_result = await gateway.execute_workflow(workflow_id, parameters)

# Get system status
status = gateway.get_system_status()

# List agents
agents = gateway.list_agents()
```

### TIRS Engine

```python
from watchtower.tirs import get_advanced_tirs

tirs = get_advanced_tirs()

# Analyze intent
result = tirs.analyze_intent(
    agent_id="finance_agent",
    intent_text="Process $5000 expense",
    capabilities={"process_expense"},
    was_allowed=True
)

# Get risk dashboard
dashboard = tirs.get_risk_dashboard()

# Resurrect agent
success, msg = tirs.resurrect_agent(agent_id, admin_id, reason)

# Export forensics
tirs.export_agent_forensics(agent_id, output_dir)
```

### Compliance Engine

```python
from watchtower.compliance import get_compliance_engine

compliance = get_compliance_engine()

# Evaluate action
result = compliance.evaluate(
    action="process_expense",
    payload={"amount": 15000},
    context={"user": "alice@acme.com"}
)

print(f"Allowed: {result.allowed}")
print(f"Policies triggered: {[r.policy_id for r in result.results]}")
```

## Enforcement Actions

| Action | Trigger | Effect |
|--------|---------|--------|
| MONITOR | Risk < 0.3 | Passive observation |
| THROTTLE | Risk 0.5-0.7 | Rate limit to 1 action/min |
| PAUSE | Risk 0.7-0.85 | Suspend execution, await approval |
| QUARANTINE | Manual | Isolate for investigation |
| KILL | Risk > 0.85 | Terminate agent, require resurrection |

## Resurrection Workflow

1. Agent is killed due to high risk
2. Forensic snapshot captured automatically
3. Admin submits resurrection appeal
4. Appeal reviewed (requires justification)
5. If approved, agent resurrected with monitoring
6. Resurrection count tracked (max 3 allowed)

## License

MIT License - see LICENSE file for details.
