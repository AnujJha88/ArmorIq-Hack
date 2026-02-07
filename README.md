# ArmorIQ + TIRS: Secure HR Agent Swarm

An AI-powered HR automation platform with **Temporal Intent Risk & Simulation (TIRS)** for predictive safety and compliance.

## Innovation: TIRS

**TIRS** adds a temporal, simulation-backed intent risk layer on top of ArmorIQ:

| Feature | Description |
|---------|-------------|
| **Temporal Drift Detection** | Detects slow, multi-step deviation in agent behavior over time |
| **Plan-Level Simulation** | Simulates entire action plans before any real execution |
| **Predictive Safety** | Prevents failures before they happen |
| **Auto-Remediation** | Suggests minimal policy fixes for blocked actions |
| **Signed Audit Trail** | Cryptographically verifiable decision logs |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
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
