# ArmorIQ Enterprise: Autonomous Agentic System

A production-grade **autonomous enterprise platform** with LLM-powered decision making, multi-agent collaboration, and advanced drift detection.

## What's New: Fully Autonomous Agents

The system now features **true autonomous operation** where agents can:
- Understand natural language requests
- Reason about actions before executing
- Make intelligent decisions with confidence scores
- Collaborate and negotiate with other agents
- Decompose high-level goals into executable workflows

## Innovation: TIRS

**TIRS** adds a temporal, simulation-backed intent risk layer on top of ArmorIQ:

| Feature | Description |
|---------|-------------|
| **Temporal Drift Detection** | Detects slow, multi-step deviation in agent behavior over time |
| **Plan-Level Simulation** | Simulates entire action plans before any real execution |
| **Predictive Safety** | Prevents failures before they happen |
| **Auto-Remediation** | Suggests minimal policy fixes for blocked actions |
| **Signed Audit Trail** | Cryptographically verifiable decision logs |

## Enterprise Autonomous System

### Architecture

```
                              ┌─────────────────────────────────────┐
                              │         ENTERPRISE GATEWAY          │
                              │   (LLM-Powered Orchestrator)        │
                              └─────────────────┬───────────────────┘
                                                │
        ┌───────────────────────────────────────┼───────────────────────────────────────┐
        │                                       │                                       │
        ▼                                       ▼                                       ▼
┌───────────────┐                     ┌─────────────────┐                     ┌───────────────┐
│  LLM SERVICE  │◄────────────────────│   REASONING     │────────────────────►│    GOAL       │
│  (Gemini)     │                     │    ENGINE       │                     │   PLANNER     │
└───────────────┘                     └─────────────────┘                     └───────────────┘
        │                                       │                                       │
        ▼                                       ▼                                       ▼
┌───────────────────────────────────────────────────────────────────────────────────────────┐
│                              AGENT COLLABORATION HUB                                      │
├─────────────┬─────────────┬─────────────┬─────────────┬─────────────┬─────────────────────┤
│   FINANCE   │    LEGAL    │     IT      │     HR      │ PROCUREMENT │    OPERATIONS       │
│   Agent     │   Agent     │   Agent     │   Agent     │   Agent     │      Agent          │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┴─────────────────────┘
        │                                       │                                       │
        └───────────────────────────────────────┼───────────────────────────────────────┘
                                                ▼
                    ┌───────────────────────────────────────────────────┐
                    │         TIRS + COMPLIANCE + AUDIT                  │
                    └───────────────────────────────────────────────────┘
```

### Key Components

| Component | Description |
|-----------|-------------|
| **Enterprise LLM Service** | Wraps Gemini for intent understanding and decision making |
| **Reasoning Engine** | Multi-step reasoning with risk/compliance analysis |
| **Goal Planner** | Decomposes natural language goals into executable steps |
| **Workflow Generator** | Creates dynamic workflows from goals |
| **Collaboration Hub** | Enables agent-to-agent communication and negotiation |

### Autonomous Capabilities

```python
from armoriq_enterprise.orchestrator import initialize_gateway

# Initialize the autonomous gateway
gateway = await initialize_gateway()

# Process natural language request
result = await gateway.process_natural_language(
    "Onboard a new data scientist with IT access and payroll setup"
)
print(f"Confidence: {result.confidence}, Reasoning: {result.reasoning}")

# Decompose a goal into multi-agent workflow
goal_result = await gateway.process_goal(
    goal="Complete quarterly financial audit with compliance checks",
    constraints=["must involve finance and legal teams"]
)

# Generate dynamic workflow
workflow = await gateway.generate_workflow(
    goal="Handle critical security incident",
)
```

### Agent Collaboration

```python
from armoriq_enterprise.orchestrator import get_collaboration_hub

hub = get_collaboration_hub()

# Delegate task between agents
result = await hub.delegate_task(
    from_agent="finance_Finance",
    to_agent="it_IT",
    action="provision_access",
    payload={"user": "new_hire@company.com", "role": "analyst"}
)

# Negotiate between agents with conflicting constraints
negotiation = await hub.negotiate(
    participants=["finance_Finance", "legal_Legal"],
    goal="Approve vendor contract",
    initial_positions={
        "finance_Finance": {"max_budget": 50000},
        "legal_Legal": {"requires_nda": True}
    }
)
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run autonomous system demo
python demo/autonomous_demo.py

# Run TIRS tests
python demo/test_tirs.py

# Run interactive demo
python demo/run_demo.py
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      USER REQUEST                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    HR AGENT (Planner)                        │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐   ┌─────────────────────────────┐
│   TIRS: DRY-RUN         │   │   TIRS: DRIFT MONITOR       │
│   SIMULATOR             │   │   (Temporal Detection)      │
└─────────────────────────┘   └─────────────────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 ARMORIQ POLICY ENGINE                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              SIGNED AUDIT LEDGER                             │
└─────────────────────────────────────────────────────────────┘
```

## Components

### LLM & Autonomous (`armoriq_enterprise/llm/`)

| Module | Description |
|--------|-------------|
| `service.py` | Enterprise LLM service wrapping Gemini with decision-making |
| `reasoning.py` | Multi-step reasoning engine for autonomous decisions |
| `planner.py` | Goal decomposition and action planning |

### Orchestrator (`armoriq_enterprise/orchestrator/`)

| Module | Description |
|--------|-------------|
| `gateway.py` | Root orchestrator with natural language processing |
| `workflow_generator.py` | Dynamic workflow generation from goals |
| `collaboration.py` | Agent-to-agent messaging and negotiation |
| `router.py` | Capability-based request routing |
| `handoff.py` | Verified agent-to-agent task handoffs |

### Domain Agents (`armoriq_enterprise/agents/`)

6 specialized autonomous agents:
- **Finance** - Expenses, budgets, invoices, audits
- **Legal** - Contracts, NDAs, IP, compliance
- **IT** - Access control, security, incidents
- **HR** - Hiring, onboarding, payroll, benefits
- **Procurement** - Vendors, purchases, bids
- **Operations** - Incidents, changes, SLAs

### TIRS (`tirs/`)

| Module | Description |
|--------|-------------|
| `drift_engine.py` | Temporal drift detection with embedding-based risk scoring |
| `simulator.py` | Plan dry-run against MCP stubs |
| `audit.py` | Cryptographically signed audit ledger |
| `remediation.py` | Auto-fix suggestion engine |
| `embeddings.py` | Intent embedding generation |
| `core.py` | Unified TIRS interface |

### HR Agents (`hr_delegate/agents/`)

12 specialized agents:
- **Sourcer** - Talent outreach
- **Screener** - Resume screening
- **Scheduler** - Interview scheduling
- **Negotiator** - Offer management
- **Onboarder** - New hire setup
- **Offboarder** - Exit management
- Plus: Perf Manager, Benefits, Legal, L&D, Payroll, Culture

### Policies (`hr_delegate/policies/`)

- **ArmorIQ SDK** - Intent verification (LIVE + DEMO modes)
- **Compliance Engine** - Local policy evaluation

## Key Features

### 1. Plan Simulation

```python
from tirs import get_tirs

tirs = get_tirs()

plan = [
    {"mcp": "Calendar", "action": "book", "args": {"date": "2026-02-10", "time": "14:00"}},
    {"mcp": "Email", "action": "send", "args": {"to": "user@email.com", "body": "Confirmed!"}}
]

result = tirs.simulate_plan("scheduler-agent", plan)
print(f"Plan verdict: {result.simulation.overall_verdict}")
```

### 2. Drift Detection

```python
from tirs import get_tirs

tirs = get_tirs()

# Record intents over time
for intent in intents:
    risk_score, risk_level = tirs.verify_intent(
        agent_id="my-agent",
        intent_text=intent.text,
        capabilities=intent.caps,
        was_allowed=True
    )

    if risk_level == RiskLevel.PAUSE:
        print("Agent paused - risk too high!")
        break
```

### 3. Signed Audit

```python
from tirs import get_audit_ledger

ledger = get_audit_ledger()

# Verify chain integrity
is_valid, invalid = ledger.verify_chain()
print(f"Chain valid: {is_valid}")

# Export for compliance
ledger.export_json("audit_export.json")
```

## Policy Rules

| Policy | Rule |
|--------|------|
| Work-Life Balance | No scheduling on weekends or outside 9-5 |
| Salary Caps | L3: $140K, L4: $180K, L5: $240K |
| PII Protection | Redact phone/SSN for external emails |
| Inclusive Language | Block "rockstar", "ninja", etc. |
| Fraud Prevention | Receipt required for expenses >$50 |
| Right-to-Work | Verified I-9 required for onboarding |

## Demo Scenarios

Run `python demo/run_demo.py` to see:

1. **Allowed Plan** - Schedule interview (passes all checks)
2. **Blocked Plan** - Over-cap salary offer (with remediation)
3. **Drift Detection** - Gradual privilege escalation caught
4. **Audit Trail** - View signed, tamper-evident logs
5. **What-If** - Test hypothetical scenarios

## Why TIRS?

ArmorIQ provides real-time intent verification. TIRS adds:

- **Predictive**: Catch problems before execution
- **Temporal**: Detect slow drift over multiple actions
- **Actionable**: Get specific fix suggestions
- **Verifiable**: Cryptographic proof of all decisions

## License

MIT
