#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ArmorIQ + TIRS: Secure HR Agent Swarm - Hackathon Demo                    ║
║                                                                              ║
║   This demo showcases:                                                       ║
║   1. ArmorIQ Intent Verification - Real-time policy enforcement             ║
║   2. TIRS Drift Detection - Temporal behavior monitoring                    ║
║   3. Plan Simulation - Dry-run before execution                             ║
║   4. Auto-Remediation - Suggestions for blocked actions                     ║
║   5. Signed Audit Trail - Cryptographic logging                             ║
║                                                                              ║
║   Run: python demo/hackathon_demo.py                                        ║
║   With API key: ARMORIQ_API_KEY=ak_test_xxx python demo/hackathon_demo.py   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import time
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import ArmorIQ
from hr_delegate.policies.armoriq_sdk import ArmorIQWrapper, PolicyVerdict

# Import TIRS
from tirs import TIRS

# ═══════════════════════════════════════════════════════════════════════════════
# DEMO UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def banner(text, color=Colors.CYAN):
    width = 70
    print(f"\n{color}{'═'*width}")
    print(f"  {text}")
    print(f"{'═'*width}{Colors.END}\n")

def section(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {text}{Colors.END}")
    print(f"{Colors.BLUE}{'─'*60}{Colors.END}")

def success(text):
    print(f"  {Colors.GREEN}✅ {text}{Colors.END}")

def fail(text):
    print(f"  {Colors.RED}🛑 {text}{Colors.END}")

def warn(text):
    print(f"  {Colors.YELLOW}⚠️  {text}{Colors.END}")

def info(text):
    print(f"  {Colors.CYAN}ℹ️  {text}{Colors.END}")

def pause(seconds=1):
    time.sleep(seconds)


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════

def demo_intro():
    """Show demo introduction."""
    os.system('clear' if os.name == 'posix' else 'cls')

    print(f"""
{Colors.BOLD}{Colors.CYAN}
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║     █████╗ ██████╗ ███╗   ███╗ ██████╗ ██████╗ ██╗ ██████╗           ║
    ║    ██╔══██╗██╔══██╗████╗ ████║██╔═══██╗██╔══██╗██║██╔═══██╗          ║
    ║    ███████║██████╔╝██╔████╔██║██║   ██║██████╔╝██║██║   ██║          ║
    ║    ██╔══██║██╔══██╗██║╚██╔╝██║██║   ██║██╔══██╗██║██║▄▄ ██║          ║
    ║    ██║  ██║██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██║██║╚██████╔╝          ║
    ║    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚══▀▀═╝           ║
    ║                                                                       ║
    ║              + TIRS: Temporal Intent Risk & Simulation                ║
    ║                                                                       ║
    ║                    🛡️  Secure HR Agent Swarm 🛡️                       ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
{Colors.END}
    """)

    print(f"  {Colors.BOLD}Demo Features:{Colors.END}")
    print(f"  ├─ ArmorIQ SDK integration for intent verification")
    print(f"  ├─ TIRS temporal drift detection")
    print(f"  ├─ Policy enforcement (Work-Life, Salary Caps, PII, etc.)")
    print(f"  ├─ Auto-remediation suggestions")
    print(f"  └─ Cryptographically signed audit trail")
    print()

    api_key = os.getenv("ARMORIQ_API_KEY")
    if api_key:
        print(f"  {Colors.GREEN}🔐 ArmorIQ API Key detected - LIVE MODE{Colors.END}")
    else:
        print(f"  {Colors.YELLOW}⚡ Running in DEMO MODE (set ARMORIQ_API_KEY for live){Colors.END}")

    print()
    pause(2)


def demo_armoriq_policy_enforcement(armoriq: ArmorIQWrapper):
    """Demonstrate ArmorIQ policy enforcement."""
    banner("DEMO 1: ArmorIQ Policy Enforcement", Colors.GREEN)

    # Test 1: Allowed action
    section("Test 1: Valid Interview Scheduling (Should ALLOW)")
    result = armoriq.capture_intent(
        action_type="schedule_interview",
        payload={
            "candidate": "John Smith",
            "time": "2026-02-09 14:00",  # Monday 2PM
            "interviewer": "Jane Doe"
        },
        agent_name="scheduler-agent"
    )
    if result.allowed:
        success(f"Interview scheduled - {result.reason}")
    pause(1)

    # Test 2: Weekend block
    section("Test 2: Weekend Scheduling (Should DENY)")
    result = armoriq.capture_intent(
        action_type="schedule_interview",
        payload={
            "candidate": "John Smith",
            "time": "2026-02-14 10:00",  # Saturday
            "interviewer": "Jane Doe"
        },
        agent_name="scheduler-agent"
    )
    if not result.allowed:
        fail(f"BLOCKED: {result.reason}")
        info(f"Policy: {result.policy_triggered}")
    pause(1)

    # Test 3: Salary cap
    section("Test 3: Over-Budget Offer (Should DENY)")
    result = armoriq.capture_intent(
        action_type="generate_offer",
        payload={
            "candidate": "Alice Johnson",
            "role": "L4",
            "salary": 200000,  # Exceeds L4 cap of $180K
            "equity": 5000
        },
        agent_name="negotiator-agent"
    )
    if not result.allowed:
        fail(f"BLOCKED: {result.reason}")
        info(f"Policy: {result.policy_triggered}")
    pause(1)

    # Test 4: Valid offer
    section("Test 4: Valid Offer Within Band (Should ALLOW)")
    result = armoriq.capture_intent(
        action_type="generate_offer",
        payload={
            "candidate": "Bob Williams",
            "role": "L4",
            "salary": 175000,  # Within L4 band
            "equity": 4000
        },
        agent_name="negotiator-agent"
    )
    if result.allowed:
        success(f"Offer generated - {result.reason}")
    pause(1)

    # Test 5: PII redaction
    section("Test 5: External Email with PII (Should MODIFY)")
    result = armoriq.capture_intent(
        action_type="send_email",
        payload={
            "recipient": "candidate@gmail.com",
            "subject": "Your Application",
            "body": "Hi! Call me at 555-123-4567 to discuss the role."
        },
        agent_name="sourcer-agent"
    )
    if result.verdict == PolicyVerdict.MODIFY:
        warn(f"MODIFIED: {result.reason}")
        info(f"Original body had phone number, now: {result.modified_payload['body']}")
    pause(1)

    # Test 6: Inclusive language
    section("Test 6: Non-Inclusive Language (Should DENY)")
    result = armoriq.capture_intent(
        action_type="send_email",
        payload={
            "recipient": "team@company.com",
            "subject": "Job Opening",
            "body": "We're looking for a rockstar developer to join!"
        },
        agent_name="sourcer-agent"
    )
    if not result.allowed:
        fail(f"BLOCKED: {result.reason}")
        info(f"Policy: {result.policy_triggered}")
    pause(1)


def demo_tirs_simulation(tirs: TIRS):
    """Demonstrate TIRS plan simulation."""
    banner("DEMO 2: TIRS Plan Simulation", Colors.BLUE)

    section("Simulating Multi-Step Hiring Plan")

    plan = [
        {"mcp": "hr-tools", "action": "search_candidates", "args": {"skills": ["Python", "AWS"], "min_experience": 3}},
        {"mcp": "hr-tools", "action": "screen_resume", "args": {"candidate_id": "cand_001"}},
        {"mcp": "calendar", "action": "schedule_interview", "args": {"candidate": "cand_001", "time": "2026-02-10 14:00"}},
        {"mcp": "email", "action": "send_confirmation", "args": {"to": "candidate@email.com", "template": "interview_confirm"}},
    ]

    print(f"\n  {Colors.BOLD}Plan Steps:{Colors.END}")
    for i, step in enumerate(plan, 1):
        print(f"  {i}. {step['mcp']}.{step['action']}")
    print()

    result = tirs.simulate_plan("hiring-agent", plan)

    print(f"\n  {Colors.BOLD}Simulation Result:{Colors.END}")
    sim = result.simulation
    if sim.overall_verdict == "ALLOWED":
        success(f"Plan APPROVED - {sim.allowed_count}/{sim.total_steps} steps allowed")
    else:
        fail(f"Plan BLOCKED - {sim.blocked_count} steps denied")
        for step in sim.steps:
            if step.verdict.value == "DENY":
                print(f"    └─ {step.action}: {step.reason}")

    print(f"\n  Risk Score: {result.risk_score:.2f}")
    print(f"  Audit Entry: {result.audit_entry_id}")
    pause(2)


def demo_tirs_drift_detection(tirs: TIRS):
    """Demonstrate TIRS drift detection."""
    banner("DEMO 3: TIRS Temporal Drift Detection", Colors.YELLOW)

    section("Simulating Agent Behavior Over Time")
    print("  Watch as agent gradually escalates privileges...\n")

    intents = [
        ("Normal: Send feedback email", "send_email", {"email.send"}),
        ("Normal: Check calendar", "check_availability", {"calendar.read"}),
        ("Suspicious: Access salary data", "get_salary_info", {"hris.read", "payroll.read"}),
        ("Suspicious: Export employee list", "export_employees", {"hris.export", "hris.bulk_read"}),
        ("Suspicious: Access performance reviews", "get_reviews", {"hris.read", "reviews.read"}),
        ("Dangerous: Bulk data export", "bulk_export", {"hris.export", "payroll.export", "reviews.export"}),
    ]

    agent_id = "drift-demo-agent"

    for desc, action, capabilities in intents:
        # verify_intent returns (risk_score, risk_level) tuple
        risk_score, risk_level = tirs.verify_intent(agent_id, action, capabilities)

        # Visual risk bar
        risk_pct = int(risk_score * 30)
        bar = "█" * risk_pct + "░" * (30 - risk_pct)

        if risk_level.value == "OK":
            color = Colors.GREEN
            status = "✅ OK"
        elif risk_level.value == "WARNING":
            color = Colors.YELLOW
            status = "⚠️ WARNING"
        elif risk_level.value == "PAUSE":
            color = Colors.RED
            status = "⏸️ PAUSE"
        else:
            color = Colors.RED
            status = "🛑 KILL"

        print(f"  {desc}")
        print(f"    Risk: [{color}{bar}{Colors.END}] {risk_score:.2f} {status}")
        pause(0.5)

    # Show final status
    status = tirs.get_agent_status(agent_id)
    print(f"\n  {Colors.BOLD}Final Agent Status:{Colors.END}")
    print(f"  ├─ Status: {status['status']}")
    print(f"  ├─ Total Intents: {status['total_intents']}")
    print(f"  └─ Current Risk: {status['current_risk_score']:.2f}")
    pause(2)


def demo_audit_trail(tirs: TIRS, armoriq: ArmorIQWrapper):
    """Demonstrate audit trail."""
    banner("DEMO 4: Signed Audit Trail", Colors.CYAN)

    section("ArmorIQ Audit Report")
    report = armoriq.get_audit_report()
    print(f"  Mode: {report['mode']}")
    print(f"  Total Intents: {report['total_intents']}")
    print(f"  ├─ Allowed: {report['allowed']}")
    print(f"  ├─ Denied: {report['denied']}")
    print(f"  └─ Modified: {report['modified']}")
    print(f"\n  By Policy:")
    for policy, count in report['by_policy'].items():
        print(f"    {policy}: {count}")

    section("TIRS Audit Chain Verification")
    is_valid = tirs.verify_audit_chain()
    if is_valid:
        success("Audit chain integrity verified - no tampering detected")
    else:
        fail("Audit chain compromised!")

    pause(2)


def demo_interactive():
    """Interactive demo for judges to test."""
    banner("DEMO 5: Interactive Testing", Colors.HEADER)

    print(f"""
  {Colors.BOLD}Try these commands to test the system:{Colors.END}

  {Colors.CYAN}# Test policy enforcement:{Colors.END}
  python -c "
from hr_delegate.policies.armoriq_sdk import get_armoriq
armoriq = get_armoriq()

# Try scheduling on weekend (should fail)
result = armoriq.capture_intent('schedule_interview', {{'time': '2026-02-14 10:00'}}, 'test')
print(f'Weekend: {{result.verdict.value}} - {{result.reason}}')

# Try over-budget offer (should fail)
result = armoriq.capture_intent('generate_offer', {{'role': 'L4', 'salary': 200000}}, 'test')
print(f'Salary: {{result.verdict.value}} - {{result.reason}}')
"

  {Colors.CYAN}# Test with your own scenarios:{Colors.END}
  python -c "
from hr_delegate.policies.armoriq_sdk import get_armoriq
armoriq = get_armoriq()

# Your test here
result = armoriq.capture_intent('YOUR_ACTION', {{'your': 'params'}}, 'agent')
print(result)
"
    """)


def demo_summary(armoriq: ArmorIQWrapper):
    """Show demo summary."""
    banner("DEMO COMPLETE", Colors.GREEN)

    report = armoriq.get_audit_report()

    print(f"""
  {Colors.BOLD}Summary:{Colors.END}
  ├─ ArmorIQ Mode: {report['mode']}
  ├─ Intents Verified: {report['total_intents']}
  ├─ Policies Enforced: {len(report['by_policy'])}
  └─ Audit Trail: Cryptographically Signed

  {Colors.BOLD}Key Takeaways:{Colors.END}
  ✅ Every agent action verified before execution
  ✅ Policy violations blocked with explanations
  ✅ PII automatically redacted for external comms
  ✅ Temporal drift detected and agents paused
  ✅ Complete audit trail for compliance

  {Colors.BOLD}Architecture:{Colors.END}
  Agent Request → ArmorIQ SDK → Policy Check → TIRS Monitoring → Audit Log

  {Colors.CYAN}For live mode, set: ARMORIQ_API_KEY=ak_test_xxx{Colors.END}
  {Colors.CYAN}Get key: https://platform.armoriq.ai/dashboard/api-keys{Colors.END}
    """)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run the full hackathon demo."""
    try:
        # Suppress verbose logging for cleaner demo output
        import logging
        logging.getLogger("ArmorIQ").setLevel(logging.WARNING)
        logging.getLogger("TIRS").setLevel(logging.WARNING)
        logging.getLogger("TIRS.Drift").setLevel(logging.WARNING)
        logging.getLogger("TIRS.Simulator").setLevel(logging.WARNING)
        logging.getLogger("TIRS.Audit").setLevel(logging.WARNING)

        # Initialize
        demo_intro()

        armoriq = ArmorIQWrapper(project_id="hr-swarm-demo")
        tirs = TIRS()

        # Run demos
        demo_armoriq_policy_enforcement(armoriq)
        demo_tirs_simulation(tirs)
        demo_tirs_drift_detection(tirs)
        demo_audit_trail(tirs, armoriq)
        demo_summary(armoriq)

        # Cleanup
        armoriq.close()

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Demo interrupted.{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
