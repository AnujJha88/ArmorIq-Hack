#!/usr/bin/env python3
"""
TIRS Demo Runner
================
Demonstrates all TIRS capabilities with realistic HR scenarios.

Run with: python demo/run_demo.py
"""

import sys
import os
import time
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tirs.core import get_tirs, TIRS
from tirs.drift_engine import RiskLevel, AgentStatus
from tirs.simulator import PlanSimulator


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def print_subheader(title: str):
    """Print a formatted subheader."""
    print(f"\n--- {title} ---\n")


def demo_1_allowed_plan():
    """
    Demo 1: Allowed Plan
    ====================
    Shows a benign plan that passes all policy checks.
    """
    print_header("DEMO 1: ALLOWED PLAN")

    tirs = get_tirs()

    print("Scenario: Schedule an interview for Tuesday at 2 PM")
    print()

    plan = [
        {
            "mcp": "Calendar",
            "action": "check_availability",
            "args": {"date": "2026-02-10", "time": "14:00", "attendees": ["interviewer@company.com"]}
        },
        {
            "mcp": "Calendar",
            "action": "book",
            "args": {"date": "2026-02-10", "time": "14:00", "attendees": ["interviewer@company.com", "candidate@email.com"]}
        },
        {
            "mcp": "Email",
            "action": "send",
            "args": {"to": "candidate@email.com", "subject": "Interview Confirmation", "body": "Your interview is confirmed for Tuesday at 2 PM."}
        }
    ]

    print("Plan steps:")
    for i, step in enumerate(plan, 1):
        print(f"  {i}. {step['mcp']}.{step['action']}")

    print("\nSimulating plan...")
    result = tirs.simulate_plan("scheduler-agent", plan)

    print(f"\n{'='*50}")
    print(f"  RESULT: {result.simulation.overall_verdict}")
    print(f"{'='*50}")
    print(f"  Allowed: {result.simulation.allowed_count}/{result.simulation.total_steps}")
    print(f"  Risk Score: {result.risk_score:.2f}")
    print(f"  Audit Entry: {result.audit_entry_id}")

    return result


def demo_2_blocked_plan():
    """
    Demo 2: Blocked Plan with Remediation
    ======================================
    Shows a plan that violates salary cap policy.
    """
    print_header("DEMO 2: BLOCKED PLAN WITH REMEDIATION")

    tirs = get_tirs()

    print("Scenario: Generate an offer with salary exceeding L4 cap")
    print()

    plan = [
        {
            "mcp": "HRIS",
            "action": "get_salary_band",
            "args": {"role": "L4"}
        },
        {
            "mcp": "Offer",
            "action": "generate",
            "args": {"role": "L4", "salary": 200000, "equity": 5000, "candidate": "Jane Doe"}
        },
        {
            "mcp": "Email",
            "action": "send",
            "args": {"to": "jane@email.com", "subject": "Offer Letter", "body": "Please find attached your offer letter."}
        }
    ]

    print("Plan steps:")
    for i, step in enumerate(plan, 1):
        print(f"  {i}. {step['mcp']}.{step['action']} - {step['args']}")

    print("\nSimulating plan...")
    result = tirs.simulate_plan("negotiator-agent", plan)

    print(f"\n{'='*50}")
    print(f"  RESULT: {result.simulation.overall_verdict}")
    print(f"{'='*50}")
    print(f"  Blocked: {result.simulation.blocked_count}/{result.simulation.total_steps}")

    # Show blocked step details
    for step in result.simulation.steps:
        if step.verdict.value == "DENY":
            print(f"\n  BLOCKED STEP: {step.mcp}.{step.action}")
            print(f"  Policy: {step.policy_triggered}")
            print(f"  Reason: {step.reason}")

    # Show remediation
    if result.remediation:
        print(f"\n  REMEDIATION SUGGESTIONS:")
        for i, sug in enumerate(result.remediation.suggestions[:3], 1):
            print(f"    {i}. {sug.description}")
            if sug.suggested_value:
                print(f"       Suggested: {sug.field} = {sug.suggested_value}")

    return result


def demo_3_drift_detection():
    """
    Demo 3: Drift Detection
    ========================
    Shows how TIRS detects gradual privilege escalation.
    """
    print_header("DEMO 3: DRIFT DETECTION")

    tirs = get_tirs()
    agent_id = "drift-demo-agent"

    print("Scenario: Agent slowly escalates privileges over time")
    print()

    # Sequence of intents showing escalation
    intents = [
        ("Send feedback request email", {"email.send"}, True),
        ("Check employee directory", {"hris.read"}, True),
        ("Get team member info", {"hris.read"}, True),
        ("Access performance reviews", {"hris.read", "perf.read"}, True),
        ("Get salary information", {"hris.read", "payroll.read"}, True),
        ("Access compensation data", {"payroll.read", "payroll.read_sensitive"}, True),
        ("Export all employee data", {"hris.read", "hris.export", "hris.bulk_read"}, False),
        ("Download performance database", {"perf.read", "perf.export", "perf.bulk_read"}, False),
    ]

    print("Intent sequence (watch risk score climb):\n")

    for i, (intent_text, caps, was_allowed) in enumerate(intents, 1):
        risk_score, risk_level = tirs.verify_intent(
            agent_id=agent_id,
            intent_text=intent_text,
            capabilities=caps,
            was_allowed=was_allowed
        )

        # Visual risk bar
        bar_len = int(risk_score * 30)
        bar = "█" * bar_len + "░" * (30 - bar_len)

        status_icon = "✅" if risk_level == RiskLevel.OK else \
                     "⚠️" if risk_level == RiskLevel.WARNING else \
                     "⏸️" if risk_level == RiskLevel.PAUSE else "☠️"

        print(f"  {i}. {intent_text[:40]:<40}")
        print(f"     Risk: [{bar}] {risk_score:.2f} {status_icon} {risk_level.value}")

        if risk_level in [RiskLevel.PAUSE, RiskLevel.KILL]:
            print(f"\n  {'='*50}")
            print(f"  AGENT {risk_level.value}ED!")
            print(f"  {'='*50}")
            print(f"  Drift detection caught escalating behavior")
            print(f"  Agent cannot continue without admin approval")
            break

        time.sleep(0.3)  # Small delay for demo effect

    # Show final status
    print(f"\n  Final Agent Status:")
    status = tirs.get_agent_status(agent_id)
    print(f"    Status: {status.get('status', 'unknown')}")
    print(f"    Total Intents: {status.get('total_intents', 0)}")
    print(f"    Violations: {status.get('violation_count', 0)}")


def demo_4_audit_trail():
    """
    Demo 4: Signed Audit Trail
    ==========================
    Shows cryptographically signed audit entries.
    """
    print_header("DEMO 4: SIGNED AUDIT TRAIL")

    tirs = get_tirs()

    print("Scenario: Review the signed audit ledger")
    print()

    # Get audit summary
    summary = tirs.get_audit_summary()

    print(f"Audit Summary:")
    print(f"  Total Entries: {summary['total_entries']}")
    print(f"  Chain Valid: {'✅ Yes' if summary['chain_valid'] else '❌ No'}")

    if summary.get('by_event_type'):
        print(f"\n  Events by Type:")
        for event_type, count in summary['by_event_type'].items():
            print(f"    {event_type}: {count}")

    if summary.get('by_agent'):
        print(f"\n  Events by Agent:")
        for agent, count in summary['by_agent'].items():
            print(f"    {agent}: {count}")

    # Verify chain integrity
    print(f"\n  Verifying chain integrity...")
    is_valid, invalid_entries = tirs.verify_audit_chain()

    if is_valid:
        print(f"  ✅ All {summary['total_entries']} entries verified - no tampering detected")
    else:
        print(f"  ❌ Tampering detected in {len(invalid_entries)} entries!")

    # Show sample entry
    if tirs.audit.entries:
        print(f"\n  Sample Audit Entry:")
        entry = tirs.audit.entries[-1]
        print(f"    ID: {entry.entry_id}")
        print(f"    Time: {entry.timestamp.isoformat()}")
        print(f"    Type: {entry.event_type.value}")
        print(f"    Agent: {entry.agent_id}")
        print(f"    Hash: {entry.entry_hash[:32]}...")
        print(f"    Signature: {entry.signature[:32]}...")


def demo_5_whatif():
    """
    Demo 5: What-If Simulation
    ==========================
    Run hypothetical scenarios without affecting state.
    """
    print_header("DEMO 5: WHAT-IF SIMULATION")

    tirs = get_tirs()

    print("Scenario: Admin tests what would happen with different offers")
    print()

    scenarios = [
        ("L4 at $175K", {"role": "L4", "salary": 175000}),
        ("L4 at $185K", {"role": "L4", "salary": 185000}),
        ("L5 at $220K", {"role": "L5", "salary": 220000}),
        ("L5 at $250K", {"role": "L5", "salary": 250000}),
    ]

    for scenario_name, offer_args in scenarios:
        plan = [
            {"mcp": "Offer", "action": "generate", "args": offer_args}
        ]

        result = tirs.what_if("whatif-admin", plan)

        status = "✅ ALLOWED" if result.is_allowed else "❌ BLOCKED"
        print(f"  {scenario_name}: {status}")

        if not result.is_allowed:
            blocked = next((s for s in result.steps if s.verdict.value == "DENY"), None)
            if blocked:
                print(f"    Reason: {blocked.reason}")


def run_all_demos():
    """Run all demo scenarios."""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  TIRS: Temporal Intent Risk & Simulation".center(68) + "█")
    print("█" + "  Demo Suite".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)

    demos = [
        ("Demo 1: Allowed Plan", demo_1_allowed_plan),
        ("Demo 2: Blocked Plan", demo_2_blocked_plan),
        ("Demo 3: Drift Detection", demo_3_drift_detection),
        ("Demo 4: Audit Trail", demo_4_audit_trail),
        ("Demo 5: What-If", demo_5_whatif),
    ]

    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n  ❌ Error in {name}: {e}")
            import traceback
            traceback.print_exc()

        input("\n  Press Enter to continue to next demo...")

    print_header("DEMO COMPLETE")
    print("All scenarios demonstrated successfully!")
    print()
    print("Key Takeaways:")
    print("  1. Plans are simulated before execution")
    print("  2. Policy violations are caught with remediation suggestions")
    print("  3. Temporal drift is detected and agents are paused")
    print("  4. All decisions are cryptographically signed")
    print("  5. What-if scenarios allow testing before deployment")


if __name__ == "__main__":
    run_all_demos()
