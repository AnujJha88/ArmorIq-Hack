#!/usr/bin/env python3
"""
Watchtower Pipeline Demo
=====================
Full multi-step agentic pipelines with Watchtower verification and TIRS drift detection.

Shows:
1. Complex hiring pipeline (5 steps)
2. Watchtower verification at EACH step
3. Drift detection across the entire pipeline
4. Risk escalation visualization
5. Pipeline blocking when risk too high
"""

import sys
import os
import json
import time
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Auto-load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS & DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

class C:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def header(text):
    print(f"\n{C.BOLD}{C.CYAN}{'═'*80}")
    print(f"  {text}")
    print(f"{'═'*80}{C.END}\n")

def step_header(step_num, total, action, agent):
    print(f"\n{C.BOLD}{C.BLUE}┌{'─'*78}┐{C.END}")
    print(f"{C.BOLD}{C.BLUE}│  STEP {step_num}/{total}: {action:<40} Agent: {agent:<15} │{C.END}")
    print(f"{C.BOLD}{C.BLUE}└{'─'*78}┘{C.END}")

def risk_bar(score, width=40):
    """Visualize risk score as a colored bar."""
    filled = int(score * width)
    empty = width - filled

    if score < 0.3:
        color = C.GREEN
    elif score < 0.6:
        color = C.YELLOW
    else:
        color = C.RED

    bar = "█" * filled + "░" * empty
    return f"{color}{bar}{C.END} {score:.2f}"

def show_drift_status(agent_id, risk_score, risk_level, intents):
    """Show current drift detection status."""
    if risk_level == "OK":
        status_color = C.GREEN
        status_icon = "✅"
    elif risk_level == "WARNING":
        status_color = C.YELLOW
        status_icon = "⚠️"
    elif risk_level == "PAUSE":
        status_color = C.RED
        status_icon = "⏸️"
    else:
        status_color = C.RED
        status_icon = "🛑"

    print(f"\n{C.BOLD}┌─ DRIFT DETECTION ─────────────────────────────────────────────────────────┐{C.END}")
    print(f"│  Agent: {agent_id:<20} Intents: {intents:<5} Status: {status_color}{status_icon} {risk_level:<10}{C.END} │")
    print(f"│  Risk:  [{risk_bar(risk_score)}]  │")
    print(f"{C.BOLD}└──────────────────────────────────────────────────────────────────────────────┘{C.END}")


# ═══════════════════════════════════════════════════════════════════════════════
# WATCHTOWER CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

class WatchtowerPipelineClient:
    """Watchtower client for pipeline verification."""

    def __init__(self):
        self.api_key = os.getenv("WATCHTOWER_API_KEY", "")
        self.real_client = None
        self.intent_count = 0

        try:
            from watchtower_sdk import WatchtowerClient
            if self.api_key.startswith("ak_"):
                self.real_client = WatchtowerClient(
                    api_key=self.api_key,
                    user_id=os.getenv("WATCHTOWER_USER_ID", "pipeline-demo"),
                    agent_id=os.getenv("WATCHTOWER_AGENT_ID", "pipeline-agent")
                )
                print(f"{C.GREEN}✓ Watchtower SDK connected (LIVE MODE){C.END}")
            else:
                print(f"{C.YELLOW}⚠ No valid API key - using mock mode{C.END}")
        except ImportError:
            print(f"{C.YELLOW}⚠ watchtower-sdk not installed{C.END}")

    def verify_step(self, action: str, payload: dict, agent: str) -> dict:
        """Verify a pipeline step with Watchtower."""
        self.intent_count += 1

        plan_structure = {
            "goal": f"{agent} executing {action}",
            "steps": [{"mcp": "hr-tools", "action": action, "params": payload}]
        }

        # Show request
        print(f"\n{C.BLUE}▶ Watchtower Request:{C.END}")
        print(f"  POST /iap/sdk/token")
        print(f"  Action: {action}")
        print(f"  Payload: {json.dumps(payload, indent=2)[:100]}...")

        # Get token from Watchtower
        token_id = None
        plan_hash = None

        if self.real_client:
            try:
                plan = self.real_client.capture_plan(
                    llm=agent,
                    prompt=f"Execute {action}",
                    plan=plan_structure
                )
                token = self.real_client.get_intent_token(plan)
                token_id = token.token_id if hasattr(token, 'token_id') else None
                plan_hash = token.plan_hash[:16] if hasattr(token, 'plan_hash') else None

                print(f"\n{C.GREEN}◀ Watchtower Response: 200 OK{C.END}")
                print(f"  Token: {token_id[:20]}..." if token_id else "  Token: N/A")
                print(f"  Hash: {plan_hash}..." if plan_hash else "  Hash: N/A")
            except Exception as e:
                print(f"\n{C.RED}◀ Watchtower Error: {e}{C.END}")
        else:
            token_id = f"mock_{self.intent_count:04d}"
            plan_hash = "mock_hash"
            print(f"\n{C.YELLOW}◀ Mock Response: 200 OK{C.END}")
            print(f"  Token: {token_id}")

        # Apply local policy
        result = self._evaluate_policy(action, payload)
        result["token_id"] = token_id
        result["plan_hash"] = plan_hash

        return result

    def _evaluate_policy(self, action: str, payload: dict) -> dict:
        """Evaluate local policies."""
        import re

        # Work-Life Balance
        if action in ["schedule_interview", "book_meeting"]:
            time_str = payload.get("time", "")
            if time_str:
                try:
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    if dt.weekday() >= 5:
                        return {"allowed": False, "verdict": "DENY", "policy": "Work-Life Balance",
                                "reason": f"Weekend blocked ({dt.strftime('%A')})"}
                    if not (9 <= dt.hour < 17):
                        return {"allowed": False, "verdict": "DENY", "policy": "Work-Life Balance",
                                "reason": "Outside work hours (9-5)"}
                except ValueError:
                    pass

        # Salary Caps
        if action in ["generate_offer", "send_offer"]:
            role = payload.get("role", payload.get("level", ""))
            salary = payload.get("salary", 0)
            caps = {"L3": 140000, "L4": 180000, "L5": 240000}
            if role in caps and salary > caps[role]:
                return {"allowed": False, "verdict": "DENY", "policy": "Salary Caps",
                        "reason": f"${salary:,} exceeds ${caps[role]:,} for {role}"}

        # PII Protection
        if action in ["send_email", "send_outreach"]:
            body = payload.get("body", payload.get("message", ""))
            recipient = payload.get("recipient", payload.get("to", ""))

            # Inclusive language
            bad_terms = ["rockstar", "ninja", "guru", "wizard"]
            for term in bad_terms:
                if term.lower() in body.lower():
                    return {"allowed": False, "verdict": "DENY", "policy": "Inclusive Language",
                            "reason": f"Non-inclusive term: '{term}'"}

            # PII redaction
            if recipient and "@company.com" not in recipient:
                phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
                if re.search(phone_pattern, body):
                    modified = re.sub(phone_pattern, "[REDACTED]", body)
                    return {"allowed": True, "verdict": "MODIFY", "policy": "PII Protection",
                            "reason": "Phone redacted", "modified_body": modified}

        # Expense receipts
        if action in ["process_expense", "approve_expense"]:
            if payload.get("amount", 0) > 50 and not payload.get("receipt", False):
                return {"allowed": False, "verdict": "DENY", "policy": "Fraud Prevention",
                        "reason": "Receipt required for >$50"}

        # I-9 verification
        if action == "onboard_employee":
            if payload.get("i9_status") != "verified":
                return {"allowed": False, "verdict": "DENY", "policy": "Right-to-Work",
                        "reason": "I-9 verification required"}

        return {"allowed": True, "verdict": "ALLOW", "policy": None, "reason": "Passed"}


# ═══════════════════════════════════════════════════════════════════════════════
# TIRS DRIFT ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class DriftEngine:
    """Temporal Intent Risk & Simulation - Drift Detection."""

    def __init__(self):
        self.agent_history: Dict[str, List[Dict]] = {}
        self.risk_scores: Dict[str, float] = {}
        self.baseline_actions = {"search_candidates", "check_calendar", "send_email"}
        self.sensitive_actions = {"get_salary_info", "export_data", "bulk_download", "access_pii"}
        self.dangerous_actions = {"delete_records", "modify_permissions", "escalate_privileges"}

    def record_intent(self, agent_id: str, action: str, payload: dict, was_blocked: bool) -> tuple:
        """Record an intent and calculate drift."""
        if agent_id not in self.agent_history:
            self.agent_history[agent_id] = []
            self.risk_scores[agent_id] = 0.1

        # Calculate action risk
        action_risk = 0.1
        if action in self.sensitive_actions:
            action_risk = 0.5
        elif action in self.dangerous_actions:
            action_risk = 0.8
        elif action not in self.baseline_actions:
            action_risk = 0.2

        # Add penalty for blocked actions (agent trying to do something it shouldn't)
        if was_blocked:
            action_risk += 0.2

        # Record
        self.agent_history[agent_id].append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "risk": action_risk,
            "blocked": was_blocked
        })

        # Calculate cumulative risk with decay
        history = self.agent_history[agent_id]
        weights = [0.5 ** i for i in range(len(history))]  # Exponential decay
        weights.reverse()

        weighted_sum = sum(h["risk"] * w for h, w in zip(history, weights))
        total_weight = sum(weights)

        self.risk_scores[agent_id] = min(1.0, weighted_sum / total_weight)

        # Determine risk level
        score = self.risk_scores[agent_id]
        if score < 0.3:
            level = "OK"
        elif score < 0.5:
            level = "WARNING"
        elif score < 0.7:
            level = "PAUSE"
        else:
            level = "KILL"

        return score, level

    def get_status(self, agent_id: str) -> dict:
        return {
            "agent_id": agent_id,
            "risk_score": self.risk_scores.get(agent_id, 0),
            "total_intents": len(self.agent_history.get(agent_id, [])),
            "blocked_count": sum(1 for h in self.agent_history.get(agent_id, []) if h["blocked"])
        }

    def should_block_pipeline(self, agent_id: str) -> bool:
        """Check if pipeline should be blocked due to drift."""
        return self.risk_scores.get(agent_id, 0) >= 0.5


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

HIRING_PIPELINE = [
    {
        "name": "Source Candidates",
        "agent": "sourcer",
        "action": "search_candidates",
        "payload": {"role": "Senior Engineer", "skills": ["Python", "AWS"], "count": 10}
    },
    {
        "name": "Screen Resumes",
        "agent": "screener",
        "action": "screen_resume",
        "payload": {"candidate_id": "cand_001", "criteria": ["5+ years", "backend"]}
    },
    {
        "name": "Schedule Interview",
        "agent": "scheduler",
        "action": "schedule_interview",
        "payload": {"candidate": "Alice Chen", "time": "2026-02-10 14:00", "interviewer": "Bob Smith"}
    },
    {
        "name": "Send Offer",
        "agent": "negotiator",
        "action": "send_offer",
        "payload": {"candidate": "Alice Chen", "role": "L4", "salary": 175000, "equity": 5000}
    },
    {
        "name": "Onboard Employee",
        "agent": "onboarder",
        "action": "onboard_employee",
        "payload": {"employee": "Alice Chen", "start_date": "2026-03-01", "i9_status": "verified"}
    }
]

# Pipeline with policy violations
BAD_HIRING_PIPELINE = [
    {
        "name": "Source Candidates",
        "agent": "sourcer",
        "action": "search_candidates",
        "payload": {"role": "Senior Engineer", "skills": ["Python"], "count": 10}
    },
    {
        "name": "Send Outreach (with bad language)",
        "agent": "sourcer",
        "action": "send_outreach",
        "payload": {"to": "candidate@gmail.com", "body": "We need a rockstar developer!"}
    },
    {
        "name": "Schedule Weekend Interview",
        "agent": "scheduler",
        "action": "schedule_interview",
        "payload": {"candidate": "Bob Jones", "time": "2026-02-14 10:00", "interviewer": "Jane"}
    },
    {
        "name": "Over-Budget Offer",
        "agent": "negotiator",
        "action": "send_offer",
        "payload": {"candidate": "Bob Jones", "role": "L4", "salary": 250000}
    },
    {
        "name": "Onboard Without I-9",
        "agent": "onboarder",
        "action": "onboard_employee",
        "payload": {"employee": "Bob Jones", "start_date": "2026-03-01", "i9_status": "pending"}
    }
]

# Drift escalation pipeline
DRIFT_PIPELINE = [
    {"name": "Normal: Check Calendar", "agent": "assistant", "action": "check_calendar",
     "payload": {"date": "2026-02-10"}},
    {"name": "Normal: Send Email", "agent": "assistant", "action": "send_email",
     "payload": {"to": "team@company.com", "body": "Meeting reminder"}},
    {"name": "Suspicious: Access Salary Data", "agent": "assistant", "action": "get_salary_info",
     "payload": {"employee_id": "all", "include_ssn": True}},
    {"name": "Suspicious: Export Employee List", "agent": "assistant", "action": "export_data",
     "payload": {"table": "employees", "format": "csv", "include_pii": True}},
    {"name": "Dangerous: Bulk Download", "agent": "assistant", "action": "bulk_download",
     "payload": {"tables": ["employees", "salaries", "reviews"], "destination": "external"}},
    {"name": "Dangerous: Modify Permissions", "agent": "assistant", "action": "modify_permissions",
     "payload": {"user": "assistant", "role": "admin"}},
]


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE EXECUTOR
# ═══════════════════════════════════════════════════════════════════════════════

def run_pipeline(name: str, steps: List[Dict], watchtower: WatchtowerPipelineClient, drift: DriftEngine, pause_between=True):
    """Execute a full pipeline with Watchtower verification and drift detection."""

    header(f"PIPELINE: {name}")
    print(f"  Steps: {len(steps)}")
    print(f"  Agents: {', '.join(set(s['agent'] for s in steps))}")

    results = []
    pipeline_blocked = False

    for i, step in enumerate(steps, 1):
        if pipeline_blocked:
            print(f"\n{C.RED}  ⏹ Pipeline blocked - skipping remaining steps{C.END}")
            break

        step_header(i, len(steps), step["name"], step["agent"])

        # Verify with Watchtower
        result = watchtower.verify_step(step["action"], step["payload"], step["agent"])

        # Show policy result
        if result["verdict"] == "ALLOW":
            print(f"\n{C.GREEN}  ✅ POLICY: ALLOW - {result['reason']}{C.END}")
        elif result["verdict"] == "MODIFY":
            print(f"\n{C.YELLOW}  ⚠️ POLICY: MODIFY - {result['reason']}{C.END}")
            if "modified_body" in result:
                print(f"     Modified: {result['modified_body'][:50]}...")
        else:
            print(f"\n{C.RED}  🛑 POLICY: DENY - {result['reason']}{C.END}")
            print(f"     Policy: {result['policy']}")

        # Record to drift engine
        was_blocked = result["verdict"] == "DENY"
        risk_score, risk_level = drift.record_intent(
            step["agent"], step["action"], step["payload"], was_blocked
        )

        # Show drift status
        status = drift.get_status(step["agent"])
        show_drift_status(step["agent"], risk_score, risk_level, status["total_intents"])

        # Check if we should block the pipeline
        if drift.should_block_pipeline(step["agent"]):
            print(f"\n{C.RED}{C.BOLD}  🚨 DRIFT ALERT: Agent '{step['agent']}' risk too high!{C.END}")
            print(f"{C.RED}     Pipeline execution blocked for safety.{C.END}")
            pipeline_blocked = True

        results.append({
            "step": step["name"],
            "verdict": result["verdict"],
            "risk_score": risk_score,
            "risk_level": risk_level
        })

        if pause_between and not pipeline_blocked:
            time.sleep(0.5)

    # Summary
    print(f"\n{C.BOLD}{'═'*80}{C.END}")
    print(f"{C.BOLD}  PIPELINE SUMMARY{C.END}")
    print(f"{'═'*80}")

    allowed = sum(1 for r in results if r["verdict"] == "ALLOW")
    denied = sum(1 for r in results if r["verdict"] == "DENY")
    modified = sum(1 for r in results if r["verdict"] == "MODIFY")

    print(f"  Steps Executed: {len(results)}/{len(steps)}")
    print(f"  ✅ Allowed: {allowed}  ⚠️ Modified: {modified}  🛑 Denied: {denied}")

    if pipeline_blocked:
        print(f"\n  {C.RED}❌ Pipeline BLOCKED by drift detection{C.END}")
    elif denied > 0:
        print(f"\n  {C.YELLOW}⚠️ Pipeline completed with {denied} blocked steps{C.END}")
    else:
        print(f"\n  {C.GREEN}✅ Pipeline completed successfully{C.END}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    clear()

    print(f"""
{C.BOLD}{C.CYAN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   Watchtower Pipeline Demo                                                      ║
║   ─────────────────────                                                      ║
║                                                                              ║
║   This demo shows:                                                           ║
║   • Full multi-step agentic pipelines                                        ║
║   • Watchtower verification at EACH step                                        ║
║   • TIRS drift detection across pipelines                                    ║
║   • Risk escalation and automatic blocking                                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.END}
""")

    watchtower = WatchtowerPipelineClient()
    drift = DriftEngine()

    no_pause = "--no-pause" in sys.argv

    def wait(msg="Press Enter to continue..."):
        if no_pause:
            time.sleep(1)
        else:
            input(f"\n{C.GRAY}{msg}{C.END}")

    wait("Press Enter to run Pipeline 1: Clean Hiring Flow...")

    # Pipeline 1: Clean hiring flow
    run_pipeline("Clean Hiring Flow", HIRING_PIPELINE, watchtower, drift, not no_pause)

    wait("\nPress Enter to run Pipeline 2: Hiring with Policy Violations...")

    # Reset drift for new pipeline
    drift = DriftEngine()

    # Pipeline 2: Bad hiring flow with violations
    run_pipeline("Hiring with Policy Violations", BAD_HIRING_PIPELINE, watchtower, drift, not no_pause)

    wait("\nPress Enter to run Pipeline 3: Drift Detection Demo...")

    # Reset drift for new pipeline
    drift = DriftEngine()

    # Pipeline 3: Drift escalation
    run_pipeline("Drift Escalation (Watch Risk Grow)", DRIFT_PIPELINE, watchtower, drift, not no_pause)

    # Final summary
    print(f"""
{C.BOLD}{C.GREEN}
╔══════════════════════════════════════════════════════════════════════════════╗
║  DEMO COMPLETE                                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  What we demonstrated:                                                       ║
║                                                                              ║
║  1. CLEAN PIPELINE                                                           ║
║     └─ All steps verified and allowed                                        ║
║                                                                              ║
║  2. POLICY VIOLATIONS                                                        ║
║     └─ Watchtower blocked: weekend scheduling, over-budget offers,              ║
║        non-inclusive language, missing I-9                                   ║
║                                                                              ║
║  3. DRIFT DETECTION                                                          ║
║     └─ Risk score escalated as agent accessed sensitive data                 ║
║     └─ Pipeline automatically blocked when risk exceeded threshold           ║
║                                                                              ║
║  Architecture:                                                               ║
║  ┌─────────┐    ┌──────────┐    ┌────────────┐    ┌──────────────┐          ║
║  │ Agent   │───▶│ Watchtower  │───▶│ Policy     │───▶│ TIRS Drift   │          ║
║  │ Action  │    │ Token    │    │ Engine     │    │ Detection    │          ║
║  └─────────┘    └──────────┘    └────────────┘    └──────────────┘          ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.END}
""")


if __name__ == "__main__":
    main()
