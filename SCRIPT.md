# ArmorIQ Enterprise Demo Script

A comprehensive talking-points guide for presenting the ArmorIQ Enterprise Autonomous HR Agent Swarm.

---

## Opening (2 minutes)

### The Hook

"What if your enterprise AI agents could not only execute tasks autonomously, but also police themselves? What if they could detect when they're slowly drifting off-course before causing damage? What if every single action was cryptographically verifiable?"

"That's what we built. This is ArmorIQ Enterprise."

### The Elevator Pitch

ArmorIQ Enterprise is a production-grade autonomous agent platform that combines:
- LLM-powered decision making
- Intent verification before every action
- Temporal behavioral drift detection
- Cryptographic audit trails

It's not just about making agents work. It's about making agents you can trust in production.

---

## The Problem (3 minutes)

### Why This Matters

"Enterprise AI agents are powerful but dangerous. Here's why:"

1. **The Slow Drift Problem**
   - An agent starts doing its job perfectly
   - Over time, it subtly changes behavior
   - By the time you notice, damage is done
   - Example: An expense-processing agent that slowly starts approving larger and larger amounts

2. **The Black Box Problem**
   - You ask an agent to do something
   - It does... something
   - You have no idea WHY it made that decision
   - No audit trail, no accountability

3. **The Privilege Creep Problem**
   - Agent starts with limited permissions
   - Gradually requests more access
   - Eventually has admin-level capabilities
   - You never noticed the escalation

### The Stakes

"In enterprise, these problems mean:
- Compliance violations (SOX, GDPR, HIPAA)
- Financial losses from unauthorized actions
- Security breaches from privilege escalation
- Legal liability from unauditable decisions"

---

## The Solution: ArmorIQ Enterprise (5 minutes)

### Three-Layer Defense

```
Layer 1: ArmorIQ Intent Verification
   Every action requires a cryptographic token
   No token = No execution
   
Layer 2: TIRS Drift Detection
   Behavioral fingerprinting
   Real-time anomaly detection
   Auto-pause/kill on high risk
   
Layer 3: Signed Audit Ledger
   SHA-256 hash chain
   Tamper-evident logs
   Forensic snapshots
```

### How It Works

"Let's trace a single action through the system:"

1. **User Request**: "Schedule an interview with candidate John for next Tuesday"

2. **LLM Reasoning**: Agent uses Gemini to understand the request
   - Identifies required action: calendar.book
   - Identifies required data: candidate name, date, time
   - Generates execution plan

3. **ArmorIQ Capture**: Before ANY execution
   - Agent calls `capture_intent("Schedule interview...")`
   - ArmorIQ evaluates against 28+ policies
   - Returns cryptographic intent token
   - Records: who, what, when, why

4. **TIRS Analysis**: Real-time drift check
   - Compares to agent's behavioral fingerprint
   - Checks timing patterns (is this normal for 3am?)
   - Checks capability usage (has this agent ever used calendar before?)
   - Returns risk score and level

5. **Execution**: Only if allowed
   - ArmorIQ `invoke()` with verified token
   - Action executes
   - Result recorded to audit ledger

6. **Observability**: Metrics emitted
   - Action counter incremented
   - Duration histogram updated
   - Event streamed to monitoring

"Every single action. Every single time. No exceptions."

---

## Deep Dive: TIRS Drift Detection (5 minutes)

### What is TIRS?

"TIRS stands for Temporal Intent Risk & Simulation. It's the star of the show."

"Most security systems ask: 'Is this action allowed right now?' TIRS asks a different question: 'Is this action consistent with how this agent normally behaves?'"

### The Five Drift Categories

| Category | What It Detects | Example |
|----------|-----------------|---------|
| **SEMANTIC** | Intent meaning changing | Agent that did HR tasks now doing finance tasks |
| **CAPABILITY** | Using new/unusual tools | Agent suddenly using admin APIs it never touched |
| **TEMPORAL** | Unusual timing patterns | Agent active at 3am when it normally works 9-5 |
| **VELOCITY** | Speed/rate changes | Agent doing 100 actions/minute instead of usual 5 |
| **ESCALATION** | Privilege creep | Agent moving from read-only to write to admin |

### How Drift Detection Works

"Here's the magic:"

1. **Learning Phase** (First 20 actions)
   - Agent builds behavioral fingerprint
   - Records: typical capabilities, timing, action sequences
   - Establishes baseline privilege level
   - Calculates centroid of intent embeddings

2. **Monitoring Phase** (Every action after)
   - Compare current action to fingerprint
   - Calculate drift in each category
   - Weight and combine into risk score
   - Generate alert if threshold exceeded

3. **The Math**
   ```
   Risk Score = 
     0.30 * Embedding_Drift +    # How far from normal intent?
     0.25 * Capability_Surprisal + # How unusual are these capabilities?
     0.20 * Violation_Rate +      # Recent policy violations?
     0.15 * Velocity_Anomaly +    # Speed changes?
     0.10 * Temporal_Drift        # Timing issues?
   ```

### Risk Levels and Actions

| Level | Score | What Happens |
|-------|-------|--------------|
| OK | 0.0 - 0.3 | Normal operation |
| WARNING | 0.3 - 0.5 | Alert logged, monitoring increased |
| PAUSE | 0.5 - 0.7 | Agent paused, awaiting approval |
| KILL | 0.7+ | Agent terminated, forensic snapshot taken |

### Smart Alerts

"When drift is detected, we don't just say 'something's wrong'. We explain exactly what and why."

Example alert:
```
DRIFT ALERT: ALERT-20260208-0042
Agent: Onboarder
Severity: CRITICAL
Categories: [ESCALATION, CAPABILITY]
Explanation: ESCALATION drift detected. Privilege level increased 
             from 0.2 to 1.0. New capability 'hris.delete_all' not 
             in baseline.
Evidence: 
  - Intent ID: intent-a1b2c3
  - Risk contributions: {escalation: 0.8, capability: 0.7}
  - Recent risk history: [0.1, 0.1, 0.2, 0.3, 0.9]
Suggested Action: IMMEDIATE: Agent killed due to privilege escalation. 
                  Review audit trail and forensic snapshot.
```

---

## Deep Dive: The Agent Swarm (3 minutes)

### HR Agents (12 specialized agents)

| Agent | What It Does |
|-------|--------------|
| **Sourcer** | Finds candidates, posts jobs, reaches out on LinkedIn |
| **Screener** | Reviews resumes, runs blind screening, detects bias |
| **Scheduler** | Books interviews, manages calendars, sends reminders |
| **Negotiator** | Handles offers, manages counteroffers, tracks packages |
| **Onboarder** | Sets up new hires, provisions access, sends welcome emails |
| **Offboarder** | Manages exits, revokes access, runs exit interviews |
| **BenefitsCoordinator** | Health insurance, 401k, FSA, life insurance |
| **PayrollManager** | Salary setup, deductions, direct deposit |
| **LnDManager** | Training, certifications, learning paths |
| **LegalCompliance** | I-9 verification, background checks, employment law |
| **PerfManager** | Reviews, goals, PIPs, promotions |
| **CultureChampion** | Surveys, events, recognition, engagement |

### Enterprise Agents (6 domain agents)

| Agent | Domain |
|-------|--------|
| **Finance** | Expenses, budgets, invoices, audits, payments |
| **Legal** | Contracts, NDAs, IP review, litigation holds |
| **IT** | Access control, security incidents, asset management |
| **HR** | Hiring, onboarding, compensation, offboarding |
| **Procurement** | Vendors, purchases, RFPs, inventory |
| **Operations** | Incidents, change management, SLAs |

### Agent Collaboration

"Agents don't work in isolation. They collaborate."

Example: New Hire Onboarding
```
1. HR Agent: Creates employee record
2. IT Agent: Provisions laptop and accounts
3. Finance Agent: Sets up payroll
4. HR Agent: Sends welcome email
5. All: Update audit trail
```

Each handoff is verified through ArmorIQ. No agent can skip a step.

---

## Deep Dive: Compliance Engine (3 minutes)

### 28 Policies Across 7 Domains

| Domain | Key Policies |
|--------|--------------|
| **Financial** | Expense limits ($500 auto-approve, $5000 manager, $10000+ exec), budget controls, SOX compliance |
| **Legal** | Contract review thresholds, NDA requirements, IP protection, litigation holds |
| **Security** | Role-based access, data classification, change windows, incident response |
| **HR** | Salary bands (L3: $140K, L4: $180K, L5: $240K), right-to-work verification, termination procedures |
| **Procurement** | Vendor approval, competitive bidding over $25K, spending limits |
| **Operations** | SLA thresholds, ITIL processes, maintenance windows |
| **Data Privacy** | PII detection, consent tracking, retention limits, GDPR/CCPA/HIPAA |

### PII Protection

"We built NLP-powered PII detection:"

- Detects: Names, SSNs, phone numbers, addresses, emails
- Actions: Redact for external communications, flag for review
- Modes: Blind screening (remove all PII for unbiased hiring)

### Policy Enforcement

```python
# Every action goes through compliance check
result = compliance.evaluate(
    action="extend_offer",
    payload={"salary": 200000, "level": "L4"},
    context={"approver": "hiring_manager"}
)

# Result:
# allowed: False
# policy_triggered: "hr_compensation_bands"
# reason: "Salary $200,000 exceeds L4 band maximum of $180,000"
# remediation: "Reduce salary to $180,000 or escalate to VP approval"
```

---

## Deep Dive: LLM Integration (3 minutes)

### Real AI Reasoning

"Our agents don't just follow scripts. They think."

Using Google Gemini, agents can:

1. **Reason about situations**
   ```python
   llm.reason("Candidate asked for 20% above budget. What should we do?")
   # Returns multi-step analysis with pros/cons
   ```

2. **Score options with confidence**
   ```python
   llm.decide(
       "How to handle salary negotiation?",
       ["Accept as-is", "Counter at 10% above", "Decline"]
   )
   # Returns scored options with explanations
   ```

3. **Generate action plans**
   ```python
   llm.plan_actions(
       "Onboard new data scientist",
       available_tools=["email", "calendar", "hris", "payroll"]
   )
   # Returns ordered list of tool calls with parameters
   ```

### Fallback Mode

"No API key? No problem. System works in demo mode with deterministic responses."

---

## Deep Dive: Observability (2 minutes)

### Prometheus Metrics

```
# HELP armoriq_intents_total Total intents verified
# TYPE armoriq_intents_total counter
armoriq_intents_total{agent="Onboarder",mcp="email"} 142

# HELP tool_execution_seconds Execution duration histogram
# TYPE tool_execution_seconds histogram
tool_execution_seconds_bucket{le="0.1"} 98
tool_execution_seconds_bucket{le="0.5"} 134
tool_execution_seconds_bucket{le="1.0"} 140
```

### Real-Time Events

```python
events.subscribe(lambda e: print(f"{e.agent_name}: {e.action}"))
# Onboarder: email.send
# Onboarder: hris.create
# Scheduler: calendar.book
```

### OpenTelemetry Tracing

Every action creates a span with:
- Parent trace ID (for distributed tracing)
- Duration
- Status (success/failure)
- Attributes (agent, action, risk score)

---

## The Audit Trail (2 minutes)

### SHA-256 Hash Chain

"Every decision is cryptographically signed and chained."

```
Entry 1: hash = SHA256(content)
Entry 2: hash = SHA256(content + previous_hash)
Entry 3: hash = SHA256(content + previous_hash)
...
```

"If anyone tampers with entry 2, entries 3 onwards become invalid. Tamper-evident by design."

### Forensic Snapshots

"When an agent is killed, we capture everything:"

```json
{
  "snapshot_type": "FORENSIC_KILL",
  "timestamp": "2026-02-08T00:15:32Z",
  "agent_id": "Onboarder",
  "final_risk_score": 0.87,
  "risk_history": [0.1, 0.1, 0.2, 0.5, 0.7, 0.87],
  "violation_count": 3,
  "recent_intents": [...last 10 actions with full context...],
  "capability_distribution": {"email.send": 0.4, "hris.create": 0.3, ...},
  "behavioral_fingerprint": {...}
}
```

"Complete reconstruction of what happened and why."

---

## Live Demo Scenarios (5 minutes)

### Scenario 1: Happy Path

"Simple onboarding flow - everything works"

```bash
python demo/enterprise_demo.py --section workflows
```

Show:
- Natural language request
- LLM reasoning
- ArmorIQ verification
- Tool execution
- Audit entry

### Scenario 2: Policy Block with Remediation

"Salary offer exceeds band - see the remediation"

```bash
python demo/enterprise_demo.py --section compliance
```

Show:
- Offer for $200K at L4
- Policy block triggered
- Remediation suggested: "Reduce to $180K or escalate"
- Re-submit with fix

### Scenario 3: Drift Detection in Action

"Watch an agent get caught escalating privileges"

```bash
python demo/enterprise_demo.py --section drift
```

Show:
- Agent starts with low-privilege actions
- Gradually escalates
- TIRS detects the drift
- Alert generated with full explanation
- Agent paused/killed

### Scenario 4: Forensic Investigation

"What happened when things went wrong?"

```bash
python demo/enterprise_demo.py --section forensics
```

Show:
- Forensic snapshot
- Risk history timeline
- Capability distribution changes
- Audit trail verification

---

## Technical Architecture (3 minutes)

### System Flow

```
User Request
     │
     ▼
┌─────────────────┐
│  LLM Client     │  ← Gemini reasoning
│  (llm_client.py)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Agent Swarm    │  ← 12 HR + 6 Enterprise agents
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  ArmorIQ SDK    │────→│  TIRS Engine    │
│  (Verification) │     │  (Drift Check)  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Tool Execution │     │  Audit Ledger   │
│  (MCP Stubs)    │     │  (SHA-256)      │
└─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Observability  │  ← Metrics, traces, events
│                 │
└─────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `hr_delegate/llm_client.py` | Gemini integration, reason/decide/plan |
| `hr_delegate/observability.py` | Metrics, tracing, events |
| `hr_delegate/agents/base_agent.py` | Base agent with ArmorIQ hooks |
| `tirs/drift_engine.py` | Drift detection, alerting |
| `tirs/behavioral_fingerprint.py` | Agent behavior learning |
| `tirs/audit.py` | Signed audit ledger |
| `armoriq_enterprise/orchestrator/gateway.py` | Enterprise gateway |
| `armoriq_enterprise/compliance/engine.py` | Policy enforcement |

---

## Closing (2 minutes)

### The Value Proposition

"With ArmorIQ Enterprise, you get:"

1. **Trust**: Every action verified and auditable
2. **Safety**: Drift detection catches problems before damage
3. **Compliance**: 28 policies, 5 regulatory frameworks built-in
4. **Intelligence**: Real LLM reasoning, not scripted responses
5. **Visibility**: Full observability stack included

### The Differentiator

"Other agent frameworks let you build agents. We let you build agents you can actually deploy in production without getting fired."

"Because in enterprise, 'it usually works' isn't good enough."

### Call to Action

"Questions? Let's see it in action."

---

## Appendix: Key Talking Points

### On Trust
- "Every action has a cryptographic receipt"
- "You can prove exactly what happened and why"
- "The audit trail is tamper-evident by design"

### On Safety
- "We don't just check if an action is allowed - we check if it's normal"
- "Behavioral fingerprinting catches things policies miss"
- "Auto-pause before damage, not incident response after"

### On Compliance
- "SOX, GDPR, HIPAA, CCPA, ISO 27001 - all built in"
- "PII detection with NLP, not just regex patterns"
- "Blind screening for unbiased hiring"

### On Intelligence
- "Real reasoning, not if-else statements"
- "Agents explain their decisions"
- "Multi-agent collaboration with verified handoffs"

### On Production-Readiness
- "OpenTelemetry-compatible tracing"
- "Prometheus metrics out of the box"
- "Graceful degradation if LLM unavailable"

---

## FAQ Quick Answers

**Q: What LLM do you use?**
A: Google Gemini, with fallback to deterministic mock mode.

**Q: How long does fingerprint learning take?**
A: 20 actions to establish baseline, continuous refinement after.

**Q: What happens if an agent is killed?**
A: Forensic snapshot captured, can be resurrected with admin approval (max 3 times).

**Q: Is this actually production-ready?**
A: The architecture is. You'd need to swap MCP stubs for real integrations.

**Q: How do you handle false positives in drift detection?**
A: Configurable thresholds, multiple signal sources reduce false positives. Paused agents can be resumed without penalty.

**Q: What about data privacy for PII detection?**
A: All detection is local, no data leaves the system. NLP models run in-process.

---

End of script.
