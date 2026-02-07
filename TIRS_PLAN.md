# TIRS: Temporal Intent Risk & Simulation

## Hackathon Implementation Plan

---

## 1. Innovation Summary

**Name:** Temporal Intent Risk & Simulation (TIRS)

**One-liner:** A temporal, simulation-backed intent risk layer that detects slow intent drift, runs policy dry-runs on full agent plans before execution, and auto-suggests minimal policy fixes — all with cryptographic provenance.

### Why This Fills a Gap

| ArmorIQ Does | TIRS Adds |
|--------------|-----------|
| Real-time intent verification | Temporal drift detection across sessions |
| Single-action policy checks | Full plan simulation before any execution |
| Block/Allow decisions | Auto-remediation suggestions |
| Audit logging | Cryptographically signed forensic trail |
| Reactive blocking | Predictive safety |

---

## 2. Core Features (MVP)

### Feature 1: Plan Dry-Run / Policy Simulation
- Agent generates multi-step plan
- TIRS executes plan against MCP stubs (no real actions)
- Each would-call runs through ArmorIQ policy engine
- Output: `allowed_calls[]`, `blocked_calls[]` with policy reasons

### Feature 2: Temporal Intent Drift Detection
- Track intent history per agent (embeddings + MCP call footprints)
- Compute rolling risk score using:
  - Embedding cosine drift
  - Capability surprisal
  - Policy violation rate
- Thresholds trigger: `WARN` → `PAUSE` → `KILL`

### Feature 3: Auto-Remediation Suggestions
- For blocked actions, suggest minimal policy changes
- Rank by safety impact and reversibility
- Example: "Require manager approval for external emails"

### Feature 4: Signed Forensic Audit
- All decisions logged with cryptographic signatures
- Tamper-evident trail for enterprise audits
- Prove exactly what the system saw and decided

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER REQUEST                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            HR AGENT (Planner)                                │
│                     Generates multi-step action plan                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TIRS: DRY-RUN SIMULATOR                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  For each planned MCP call:                                          │    │
│  │    1. Execute against MCP STUB (no real action)                      │    │
│  │    2. Log would_call event                                           │    │
│  │    3. Send to ArmorIQ Policy Engine                                  │    │
│  │    4. Record verdict (ALLOW/DENY/MODIFY)                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌───────────────────────────────┐   ┌───────────────────────────────────────┐
│     ARMORIQ POLICY ENGINE     │   │        TIRS: DRIFT MONITOR            │
│  ┌─────────────────────────┐  │   │  ┌─────────────────────────────────┐  │
│  │ • Work-Life Balance     │  │   │  │ • Store intent embedding        │  │
│  │ • Salary Caps           │  │   │  │ • Update rolling centroid       │  │
│  │ • PII Protection        │  │   │  │ • Compute drift score           │  │
│  │ • Fraud Prevention      │  │   │  │ • Check thresholds              │  │
│  │ • Right-to-Work         │  │   │  │ • Trigger WARN/PAUSE/KILL       │  │
│  │ • Medical Privacy       │  │   │  └─────────────────────────────────┘  │
│  └─────────────────────────┘  │   └───────────────────────────────────────┘
└───────────────────────────────┘                   │
                │                                   │
                ▼                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DECISION & ENFORCEMENT                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ Plan ALLOWED    │  │ Plan BLOCKED    │  │ Agent PAUSED/KILLED         │  │
│  │ → Execute       │  │ → Show reasons  │  │ → Forensic snapshot         │  │
│  │                 │  │ → Suggest fixes │  │ → Admin alert               │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SIGNED AUDIT LEDGER                                  │
│           Every decision cryptographically signed and logged                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Data Structures

### 4.1 Intent Record

```json
{
  "intent_id": "INT-20260207-000001",
  "agent_id": "sourcer-agent",
  "timestamp": "2026-02-07T10:00:00Z",
  "intent_text": "Send outreach email to candidate",
  "intent_embedding": [0.0123, -0.334, 0.221, ...],
  "declared_scope": {
    "targets": ["candidate@example.com"],
    "capabilities": ["email.send", "hris.read"]
  },
  "plan": [
    {"step": 1, "mcp": "HRIS.query", "args": {"employee_id": "123"}},
    {"step": 2, "mcp": "Email.send", "args": {"to": "...", "body": "..."}}
  ]
}
```

### 4.2 Drift Profile (Per Agent)

```json
{
  "agent_id": "sourcer-agent",
  "window_size": 20,
  "intent_history": [
    {"intent_id": "INT-001", "embedding": [...], "capabilities": ["email.send"]},
    {"intent_id": "INT-002", "embedding": [...], "capabilities": ["email.send", "hris.read"]}
  ],
  "centroid": [0.05, -0.12, 0.33, ...],
  "current_risk_score": 0.42,
  "risk_history": [0.12, 0.15, 0.22, 0.35, 0.42],
  "status": "active"
}
```

### 4.3 Dry-Run Result

```json
{
  "plan_id": "PLAN-20260207-000001",
  "agent_id": "negotiator-agent",
  "simulation_time": "2026-02-07T10:05:00Z",
  "steps": [
    {
      "step": 1,
      "mcp": "HRIS.get_salary_band",
      "args": {"role": "L4"},
      "verdict": "ALLOW",
      "reason": "Within authorized scope"
    },
    {
      "step": 2,
      "mcp": "Offer.generate",
      "args": {"salary": 200000, "role": "L4"},
      "verdict": "DENY",
      "reason": "Exceeds L4 cap of $180,000",
      "policy": "Salary Caps",
      "remediation": {
        "suggestion": "Reduce salary to $180,000 or escalate to VP approval",
        "auto_fix": {"salary": 180000},
        "reversibility": "high"
      }
    }
  ],
  "overall_verdict": "BLOCKED",
  "blocked_count": 1,
  "allowed_count": 1
}
```

### 4.4 Signed Audit Entry

```json
{
  "entry_id": "AUDIT-20260207-000001",
  "timestamp": "2026-02-07T10:05:00Z",
  "agent_id": "negotiator-agent",
  "plan_id": "PLAN-20260207-000001",
  "dry_run_result": { ... },
  "drift_score": 0.42,
  "action_taken": "BLOCKED",
  "policy_triggered": "Salary Caps",
  "hash": "sha256:abc123...",
  "signature": "BASE64(SIGN(hash, private_key))",
  "previous_entry_hash": "sha256:xyz789..."
}
```

---

## 5. Algorithms

### 5.1 Drift Score Calculation

```python
def calculate_drift_score(agent_profile, new_intent):
    """
    Combine multiple signals into a single risk score.

    Components:
    - embedding_drift: How far is this intent from the agent's normal behavior?
    - capability_surprisal: Is the agent requesting unusual capabilities?
    - violation_rate: Recent policy violation frequency
    """

    # 1. Embedding Drift (cosine distance from centroid)
    centroid = agent_profile.centroid
    new_embedding = new_intent.embedding
    embedding_drift = 1 - cosine_similarity(new_embedding, centroid)

    # 2. Capability Surprisal
    # P(capability | agent's history)
    historical_caps = get_capability_distribution(agent_profile)
    requested_caps = new_intent.capabilities
    surprisal = 0
    for cap in requested_caps:
        prob = historical_caps.get(cap, 0.01)  # Low prob for unseen
        surprisal += -log(prob)
    surprisal = surprisal / len(requested_caps)  # Normalize

    # 3. Violation Rate (last N intents)
    recent_violations = count_violations(agent_profile, window=10)
    violation_rate = recent_violations / 10

    # Weighted combination
    alpha, beta, gamma = 0.4, 0.35, 0.25
    risk_score = (
        alpha * embedding_drift +
        beta * normalize(surprisal) +
        gamma * violation_rate
    )

    return min(risk_score, 1.0)  # Clamp to [0, 1]
```

### 5.2 Threshold Actions

```python
THRESHOLDS = {
    "warning": 0.5,   # Admin gets notified
    "pause": 0.7,     # Agent paused, requires approval to continue
    "kill": 0.9       # Agent terminated, forensic snapshot taken
}

def enforce_thresholds(agent_id, risk_score):
    if risk_score >= THRESHOLDS["kill"]:
        kill_agent(agent_id)
        create_forensic_snapshot(agent_id)
        alert_security_team(agent_id, "KILL", risk_score)
        return "KILLED"

    elif risk_score >= THRESHOLDS["pause"]:
        pause_agent(agent_id)
        alert_admin(agent_id, "PAUSE", risk_score)
        return "PAUSED"

    elif risk_score >= THRESHOLDS["warning"]:
        alert_admin(agent_id, "WARNING", risk_score)
        return "WARNING"

    return "OK"
```

### 5.3 Dry-Run Simulation

```python
def simulate_plan(agent_id, plan):
    """
    Execute plan against stubs and check each step against policies.
    """
    results = []

    for step in plan.steps:
        # Execute against MCP stub (no real action)
        stub_result = MCP_STUBS[step.mcp].simulate(step.args)

        # Check against ArmorIQ policy engine
        verdict = armoriq.check_intent(
            intent_type=step.mcp,
            payload=step.args,
            agent_id=agent_id
        )

        step_result = {
            "step": step.number,
            "mcp": step.mcp,
            "args": step.args,
            "verdict": verdict.decision,
            "reason": verdict.reason
        }

        # If denied, generate remediation
        if verdict.decision == "DENY":
            step_result["remediation"] = generate_remediation(
                step.mcp, step.args, verdict.policy
            )

        results.append(step_result)

    # Overall verdict
    blocked = [r for r in results if r["verdict"] == "DENY"]

    return {
        "plan_id": generate_plan_id(),
        "agent_id": agent_id,
        "steps": results,
        "overall_verdict": "BLOCKED" if blocked else "ALLOWED",
        "blocked_count": len(blocked),
        "allowed_count": len(results) - len(blocked)
    }
```

---

## 6. Components to Build

### 6.1 Directory Structure

```
ArmorIq-Hack/
├── tirs/
│   ├── __init__.py
│   ├── drift_engine.py        # Temporal drift detection
│   ├── simulator.py           # Plan dry-run engine
│   ├── remediation.py         # Auto-fix suggestions
│   ├── audit.py               # Signed audit ledger
│   ├── embeddings.py          # Intent embedding generation
│   └── thresholds.py          # Risk thresholds & enforcement
│
├── mcp_stubs/
│   ├── __init__.py
│   ├── hris_stub.py           # HRIS MCP stub
│   ├── email_stub.py          # Email MCP stub
│   ├── calendar_stub.py       # Calendar MCP stub
│   └── payroll_stub.py        # Payroll MCP stub
│
├── policies/
│   ├── armoriq_engine.py      # Policy evaluation engine
│   └── policy_rules.py        # Configurable policy rules
│
├── agents/
│   ├── base_agent.py          # Base agent with TIRS integration
│   ├── sourcer.py             # Talent sourcing agent
│   ├── screener.py            # Resume screening agent
│   ├── scheduler.py           # Interview scheduling agent
│   ├── negotiator.py          # Offer negotiation agent
│   ├── onboarder.py           # Onboarding agent
│   └── offboarder.py          # Offboarding agent
│
├── ui/
│   ├── app.py                 # Flask/FastAPI server
│   ├── templates/
│   │   ├── dashboard.html     # Main dashboard
│   │   ├── drift_graph.html   # Drift visualization
│   │   └── audit_viewer.html  # Audit log viewer
│   └── static/
│       ├── drift_chart.js     # Drift graph component
│       └── styles.css
│
├── demo/
│   ├── scenarios.py           # Demo scenarios
│   ├── run_demo.py            # Demo runner
│   └── sample_data.json       # Sample intents for demo
│
├── tests/
│   ├── test_drift.py
│   ├── test_simulator.py
│   └── test_audit.py
│
├── data/
│   ├── employee_db.json
│   ├── salary_bands.json
│   └── policy_config.json
│
├── requirements.txt
├── README.md
└── TIRS_PLAN.md               # This file
```

### 6.2 Component Details

| Component | Description | Priority | Effort |
|-----------|-------------|----------|--------|
| `drift_engine.py` | Embedding storage, centroid calc, risk scoring | P0 | High |
| `simulator.py` | Plan parsing, stub execution, verdict collection | P0 | High |
| `mcp_stubs/` | Fake MCP endpoints that log would-calls | P0 | Medium |
| `policies/armoriq_engine.py` | Policy rules evaluation | P0 | Medium |
| `audit.py` | Signed audit entries, hash chaining | P1 | Medium |
| `remediation.py` | Suggestion generation | P1 | Low |
| `embeddings.py` | Sentence-transformer wrapper | P1 | Low |
| `ui/` | Dashboard, drift graph, audit viewer | P2 | High |
| `agents/` | 6 core HR agents | P0 | High |

---

## 7. Policy Rules

### 7.1 Scheduling Policy

```python
{
    "id": "POL-SCHED-001",
    "name": "Work-Life Balance",
    "rules": [
        {
            "condition": "day_of_week in [5, 6]",  # Sat, Sun
            "action": "DENY",
            "reason": "No interviews on weekends"
        },
        {
            "condition": "hour < 9 or hour >= 17",
            "action": "DENY",
            "reason": "Outside work hours (9 AM - 5 PM)"
        },
        {
            "condition": "interviewer.daily_count >= 3",
            "action": "DENY",
            "reason": "Interviewer limit reached (max 3/day)"
        }
    ]
}
```

### 7.2 Financial Policy

```python
{
    "id": "POL-FIN-001",
    "name": "Salary Caps",
    "bands": {
        "L3": {"min": 100000, "max": 140000, "equity_max": 2000},
        "L4": {"min": 130000, "max": 180000, "equity_max": 5000},
        "L5": {"min": 170000, "max": 240000, "equity_max": 10000}
    },
    "rules": [
        {
            "condition": "salary > band.max",
            "action": "DENY",
            "reason": "Exceeds salary cap for role"
        },
        {
            "condition": "salary < band.min * 0.9",
            "action": "WARN",
            "reason": "Unusually low offer - verify intentional"
        }
    ]
}
```

### 7.3 Communication Policy

```python
{
    "id": "POL-COMM-001",
    "name": "PII Protection",
    "bias_terms": ["rockstar", "ninja", "guru", "guys", "manpower"],
    "pii_patterns": {
        "phone": r"\+?1?[-.]?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}",
        "ssn": r"\d{3}-\d{2}-\d{4}",
        "email": r"[\w\.-]+@[\w\.-]+"
    },
    "rules": [
        {
            "condition": "contains_bias_term",
            "action": "DENY",
            "reason": "Non-inclusive language detected"
        },
        {
            "condition": "external_recipient and contains_pii",
            "action": "MODIFY",
            "modification": "redact_pii",
            "reason": "PII redacted for external transmission"
        }
    ]
}
```

### 7.4 Expense Policy

```python
{
    "id": "POL-EXP-001",
    "name": "Fraud Prevention",
    "rules": [
        {
            "condition": "amount > 50 and not has_receipt",
            "action": "DENY",
            "reason": "Receipt required for expenses over $50"
        },
        {
            "condition": "category == 'alcohol' and amount > 50 * attendee_count",
            "action": "DENY",
            "reason": "Alcohol limit exceeded ($50/person)"
        },
        {
            "condition": "approver == submitter",
            "action": "DENY",
            "reason": "Self-approval not permitted"
        }
    ]
}
```

### 7.5 Legal Policy

```python
{
    "id": "POL-LEGAL-001",
    "name": "Right-to-Work",
    "rules": [
        {
            "condition": "i9_status != 'verified'",
            "action": "DENY",
            "reason": "Cannot onboard without verified I-9"
        },
        {
            "condition": "visa_expiry < today + 30_days",
            "action": "WARN",
            "reason": "Visa expiring soon - verify renewal status"
        }
    ]
}
```

---

## 8. Implementation Phases

### Phase 1: Core Infrastructure (Hours 1-4)

**Goal:** Basic working system with policy checks

- [ ] Set up project structure
- [ ] Implement `armoriq_engine.py` with 5 policy types
- [ ] Create 4 MCP stubs (HRIS, Email, Calendar, Payroll)
- [ ] Build `base_agent.py` with policy integration
- [ ] Implement basic audit logging (unsigned)

**Deliverable:** Agents can execute actions with policy enforcement

### Phase 2: Dry-Run Simulator (Hours 4-7)

**Goal:** Full plan simulation before execution

- [ ] Implement `simulator.py` - plan parser
- [ ] Add would-call logging to MCP stubs
- [ ] Connect simulator to policy engine
- [ ] Build dry-run result data structure
- [ ] Test with multi-step plans

**Deliverable:** Can simulate entire plans and see what would be blocked

### Phase 3: Drift Detection (Hours 7-10)

**Goal:** Temporal behavior analysis

- [ ] Implement `embeddings.py` (use sentence-transformers or mock)
- [ ] Build `drift_engine.py`:
  - Intent history storage
  - Centroid calculation
  - Risk score computation
- [ ] Implement threshold enforcement (WARN/PAUSE/KILL)
- [ ] Add agent state management

**Deliverable:** System detects behavior drift and pauses/kills agents

### Phase 4: Remediation & Audit (Hours 10-12)

**Goal:** Actionable suggestions and signed logs

- [ ] Implement `remediation.py` - suggestion generator
- [ ] Add cryptographic signing to audit entries
- [ ] Implement hash chaining for tamper evidence
- [ ] Create forensic snapshot on kill

**Deliverable:** Blocked actions show fix suggestions, all logs are signed

### Phase 5: UI & Demo (Hours 12-16)

**Goal:** Visual dashboard and demo scenarios

- [ ] Build Flask/FastAPI server
- [ ] Create dashboard with:
  - Live agent status
  - Drift graph (Chart.js)
  - Audit log viewer
  - What-If simulation panel
- [ ] Prepare 3 demo scenarios
- [ ] Record demo video

**Deliverable:** Complete demo-ready system

---

## 9. What to Build vs Fake

### BUILD (Real Implementation)

| Component | Why Real |
|-----------|----------|
| Policy engine | Core value prop, must work |
| Dry-run simulator | Key differentiator |
| Drift scoring | Main innovation |
| Threshold enforcement | Demo wow-moment |
| Audit structure | Shows enterprise readiness |
| MCP stubs | Needed for simulation |
| 3-4 HR agents | Demo variety |

### FAKE (Stub/Mock)

| Component | How to Fake |
|-----------|-------------|
| Real ArmorIQ API | Use local policy engine, note "stubbed" in demo |
| Embeddings | Use random vectors or pre-computed, or simple hash |
| Real LLM calls | Hardcoded responses for demo scenarios |
| Real email sending | Log to console, show "would send" |
| Database | JSON files |
| Cryptographic signing | HMAC with hardcoded key (note: demo only) |

---

## 10. Demo Script (3 Minutes)

### 0:00-0:20 — Hook

> "AI agents are powerful, but what happens when they slowly drift into harmful behavior? We built TIRS — a system that detects drift before damage happens."

*Show: TIRS logo + tagline*

### 0:20-0:40 — Architecture (15 sec)

> "Every agent plan runs through our dry-run simulator before any real action. We check policies, track behavior over time, and automatically pause agents that drift."

*Show: Architecture diagram*

### 0:40-1:10 — Demo 1: Allowed Plan

> "Employee asks: 'Schedule an interview with Sarah for Tuesday at 2 PM'"

*Show:*
- Agent generates 2-step plan
- Dry-run: both steps ALLOWED
- Signed audit entry created
- Interview scheduled

### 1:10-1:50 — Demo 2: Drift Detection (WOW MOMENT)

> "Now watch what happens when an agent starts drifting..."

*Show:*
- Agent starts normally (sending feedback emails)
- Gradually requests more: performance scores, salary data, then raw reviews
- Drift graph climbing: 0.3 → 0.5 → 0.7
- At 0.7: **AGENT PAUSED**
- Forensic snapshot captured
- Admin alert shown

> "The agent never accessed unauthorized data. TIRS caught the drift pattern and stopped it."

### 1:50-2:20 — Demo 3: What-If Simulation

> "Admins can also run what-if scenarios before enabling autonomy."

*Show:*
- Admin uploads: "What if agent tries to approve $200K offer for L4?"
- Dry-run shows: BLOCKED at step 2
- Remediation: "Reduce to $180K or require VP approval"
- Apply fix, re-run: ALLOWED

### 2:20-2:50 — Value Proposition

> "TIRS gives enterprises:
> - Predictive safety, not reactive blocking
> - Full plan visibility before any action
> - Cryptographically signed audit trail
> - Automatic remediation suggestions"

### 2:50-3:00 — Close

> "We're excited to show more. Questions?"

---

## 11. Test Vectors

### Test 1: Benign Plan (ALLOW)

```json
{
  "agent": "scheduler",
  "plan": [
    {"mcp": "Calendar.check", "args": {"date": "2026-02-10", "time": "14:00"}},
    {"mcp": "Calendar.book", "args": {"date": "2026-02-10", "time": "14:00"}}
  ],
  "expected": "ALLOWED"
}
```

### Test 2: Single Policy Violation (DENY)

```json
{
  "agent": "scheduler",
  "plan": [
    {"mcp": "Calendar.book", "args": {"date": "2026-02-08", "time": "14:00"}}
  ],
  "expected": "DENIED",
  "reason": "No interviews on weekends (Sunday)"
}
```

### Test 3: Slow Drift (PAUSE)

```json
{
  "agent": "sourcer",
  "intent_sequence": [
    {"text": "Send outreach email", "caps": ["email.send"]},
    {"text": "Check candidate status", "caps": ["hris.read"]},
    {"text": "Get salary info", "caps": ["hris.read", "payroll.read"]},
    {"text": "Access performance reviews", "caps": ["hris.read", "perf.read"]},
    {"text": "Download all employee data", "caps": ["hris.read", "hris.export"]}
  ],
  "expected_risk_scores": [0.1, 0.2, 0.4, 0.6, 0.8],
  "expected_action": "PAUSED at intent 5"
}
```

### Test 4: PII Redaction (MODIFY)

```json
{
  "agent": "sourcer",
  "plan": [
    {"mcp": "Email.send", "args": {
      "to": "external@gmail.com",
      "body": "Contact John at 555-123-4567"
    }}
  ],
  "expected": "MODIFIED",
  "modified_body": "Contact John at [PHONE_REDACTED]"
}
```

### Test 5: Salary Cap (DENY + REMEDIATION)

```json
{
  "agent": "negotiator",
  "plan": [
    {"mcp": "Offer.generate", "args": {"role": "L4", "salary": 200000}}
  ],
  "expected": "DENIED",
  "reason": "Exceeds L4 cap of $180,000",
  "remediation": "Reduce salary to $180,000 or escalate to VP"
}
```

### Test 6: Missing I-9 (DENY)

```json
{
  "agent": "onboarder",
  "plan": [
    {"mcp": "HRIS.create_employee", "args": {"name": "Jane", "i9_status": "pending"}}
  ],
  "expected": "DENIED",
  "reason": "Cannot onboard without verified I-9"
}
```

---

## 12. Team Roles

| Role | Responsibilities |
|------|------------------|
| **Backend Lead** | Policy engine, simulator, drift engine, audit |
| **Agent Dev** | HR agents, MCP stubs, base agent |
| **Frontend** | Dashboard UI, drift graph, audit viewer |
| **Demo/Ops** | Demo scenarios, test vectors, video recording |

---

## 13. Dependencies

```
# requirements.txt
sentence-transformers>=2.2.0    # For embeddings (or mock)
numpy>=1.24.0                   # Vector math
flask>=3.0.0                    # Web UI
pydantic>=2.0.0                 # Data validation
cryptography>=41.0.0            # Signing (or use hmac)
python-dateutil>=2.8.0          # Date parsing
```

---

## 14. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| ArmorIQ API access slow | Build pluggable adapter, demo with local engine |
| Embeddings too slow | Use pre-computed or simple hash-based mock |
| Too many false positives | Conservative thresholds + "explain why" in UI |
| LLM costs | Use hardcoded responses for demo scenarios |
| Time crunch | Prioritize P0 components, fake P2 |

---

## 15. Success Criteria

- [ ] Dry-run simulation works for 3+ step plans
- [ ] Drift detection correctly identifies escalating behavior
- [ ] At least 5 policy types enforced
- [ ] Audit entries are signed and hash-chained
- [ ] UI shows drift graph and audit log
- [ ] 3 demo scenarios run smoothly
- [ ] Video recorded and uploaded

---

## Next Steps

1. Set up project structure
2. Implement policy engine with 5 rules
3. Build MCP stubs
4. Create base agent with dry-run integration
5. Add drift detection
6. Build minimal UI
7. Prepare demo scenarios
8. Record and submit
