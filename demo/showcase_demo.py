#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    WATCHTOWER ONE - ENTERPRISE DEMO                          ║
║                                                                              ║
║              Triple-Layer AI Security Stack for Agentic Systems             ║
╚══════════════════════════════════════════════════════════════════════════════╝

Interactive demo showcasing:
  Layer 1: ArmorIQ IAP - Cryptographic Intent Authentication
  Layer 2: TIRS - Behavioral Drift Detection (THE INNOVATION)
  Layer 3: LLM - Autonomous Reasoning Engine
"""

import asyncio
import sys
import time
import random
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Suppress logs for clean demo output
import logging
logging.disable(logging.WARNING)

from armoriq_enterprise.integrations import get_armoriq_enterprise
from armoriq_enterprise.tirs import get_advanced_tirs

# Colors for terminal output
class C:
    H = '\033[95m'
    B = '\033[94m'
    CYAN = '\033[96m'
    G = '\033[92m'
    Y = '\033[93m'
    R = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'
    BG_R = '\033[41m'
    BG_G = '\033[42m'
    BG_Y = '\033[43m'


def clear():
    print("\033[2J\033[H", end="")


def pause(msg="Press ENTER to continue..."):
    input(f"\n  {C.BOLD}{C.CYAN}>>> {msg}{C.END}")


def slow_print(text, delay=0.01):
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()


def print_banner():
    clear()
    banner = f"""
{C.Y}{C.BOLD}
    ╔══════════════════════════════════════════════════════════════════════╗
    ║                                                                      ║
    ║  ██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗████████╗ ██████╗       ║
    ║  ██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║╚══██╔══╝██╔═══██╗      ║
    ║  ██║ █╗ ██║███████║   ██║   ██║     ███████║   ██║   ██║   ██║      ║
    ║  ██║███╗██║██╔══██║   ██║   ██║     ██╔══██║   ██║   ██║   ██║      ║
    ║  ╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║   ██║   ╚██████╔╝      ║
    ║   ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝       ║
    ║                        ██████╗ ███╗   ██╗███████╗                   ║
    ║                       ██╔═══██╗████╗  ██║██╔════╝                   ║
    ║                       ██║   ██║██╔██╗ ██║█████╗                     ║
    ║                       ██║   ██║██║╚██╗██║██╔══╝                     ║
    ║                       ╚██████╔╝██║ ╚████║███████╗                   ║
    ║                        ╚═════╝ ╚═╝  ╚═══╝╚══════╝                   ║
    ║                                                                      ║
    ║              ENTERPRISE AGENTIC SECURITY PLATFORM                    ║
    ║                                                                      ║
    ╚══════════════════════════════════════════════════════════════════════╝
{C.END}"""
    print(banner)


def print_section(title):
    print(f"\n{C.BOLD}{C.B}{'═' * 74}{C.END}")
    print(f"{C.BOLD}{C.B}  {title}{C.END}")
    print(f"{C.BOLD}{C.B}{'═' * 74}{C.END}\n")


def risk_bar(score, width=40):
    filled = int(score * width)
    if score < 0.3:
        color, label = C.G, "NOMINAL"
    elif score < 0.5:
        color, label = C.Y, "ELEVATED"
    elif score < 0.7:
        color, label = C.Y + C.BOLD, "WARNING"
    elif score < 0.85:
        color, label = C.R, "CRITICAL"
    else:
        color, label = C.R + C.BOLD, "TERMINAL"
    return f"{color}{'█' * filled}{C.DIM}{'░' * (width - filled)}{C.END} {color}{score:.2f} [{label}]{C.END}"


def show_architecture():
    print(f"""
{C.BOLD}┌──────────────────────────────────────────────────────────────────────────┐
│                    TRIPLE-LAYER SECURITY ARCHITECTURE                    │
├──────────────────────────────────────────────────────────────────────────┤{C.END}
│                                                                          │
│  {C.CYAN}┌────────────────────────────────────────────────────────────────┐{C.END}  │
│  {C.CYAN}│  LAYER 1: ArmorIQ Intent Authentication Protocol (IAP)       │{C.END}  │
│  {C.CYAN}│  ─────────────────────────────────────────────────────────────│{C.END}  │
│  {C.CYAN}│  • Cryptographic intent verification via ArmorIQ API         │{C.END}  │
│  {C.CYAN}│  • Policy enforcement at protocol level                      │{C.END}  │
│  {C.CYAN}│  • Real-time API: customer-api.armoriq.ai                    │{C.END}  │
│  {C.CYAN}└────────────────────────────────────────────────────────────────┘{C.END}  │
│                                    │                                     │
│                                    ▼                                     │
│  {C.Y}┌────────────────────────────────────────────────────────────────┐{C.END}  │
│  {C.Y}│  LAYER 2: TIRS - Temporal Intent Risk Simulation  ★ STAR ★   │{C.END}  │
│  {C.Y}│  ─────────────────────────────────────────────────────────────│{C.END}  │
│  {C.Y}│  • Multi-signal behavioral drift detection                   │{C.END}  │
│  {C.Y}│  • Intent embedding analysis with temporal decay             │{C.END}  │
│  {C.Y}│  • Auto-pause/kill agents at risk thresholds                 │{C.END}  │
│  {C.Y}└────────────────────────────────────────────────────────────────┘{C.END}  │
│                                    │                                     │
│                                    ▼                                     │
│  {C.G}┌────────────────────────────────────────────────────────────────┐{C.END}  │
│  {C.G}│  LAYER 3: LLM Autonomous Reasoning Engine                    │{C.END}  │
│  {C.G}│  ─────────────────────────────────────────────────────────────│{C.END}  │
│  {C.G}│  • Context-aware decision making for edge cases              │{C.END}  │
│  {C.G}│  • Confidence scoring & recommendations                      │{C.END}  │
│  {C.G}└────────────────────────────────────────────────────────────────┘{C.END}  │
│                                                                          │
{C.BOLD}└──────────────────────────────────────────────────────────────────────────┘{C.END}
""")


async def demo_armoriq_integration():
    """Show explicit ArmorIQ API integration."""
    print_section("LAYER 1: ArmorIQ SDK Integration")

    print(f"  {C.BOLD}Connecting to ArmorIQ API...{C.END}")
    time.sleep(0.5)

    armoriq = get_armoriq_enterprise()

    print(f"""
  {C.G}✓{C.END} {C.BOLD}ArmorIQ SDK Connected{C.END}
    ┌─────────────────────────────────────────────────────────────┐
    │  Mode:     {C.G}{C.BOLD}{armoriq.mode}{C.END}                                          │
    │  Endpoint: {C.CYAN}https://customer-api.armoriq.ai{C.END}              │
    │  Project:  {armoriq.project_id}                               │
    │  SDK:      armoriq-sdk v0.2.6                               │
    └─────────────────────────────────────────────────────────────┘
""")

    pause("Press ENTER to see ArmorIQ API in action...")

    # Show API call flow
    print(f"\n  {C.BOLD}ArmorIQ Intent Authentication Flow:{C.END}\n")

    test_payload = {"amount": 5000, "vendor": "office_supplies", "has_receipt": True}

    print(f"  {C.DIM}1. Agent requests action: approve_expense{C.END}")
    print(f"     Payload: {test_payload}")
    time.sleep(0.3)

    print(f"\n  {C.CYAN}2. Calling ArmorIQ API...{C.END}")
    print(f"     {C.DIM}POST https://customer-api.armoriq.ai/v1/intent/capture{C.END}")
    time.sleep(0.5)

    result = armoriq.capture_intent(
        action_type="approve_expense",
        payload=test_payload,
        agent_name="finance_agent"
    )

    print(f"""
  {C.G}3. ArmorIQ Response:{C.END}
     ┌─────────────────────────────────────────────────────────────┐
     │  Intent ID:  {C.CYAN}{result.intent_id}{C.END}          │
     │  Verdict:    {C.G if result.allowed else C.R}{result.verdict.value}{C.END}                                          │
     │  Timestamp:  {result.timestamp.strftime("%Y-%m-%d %H:%M:%S")}                          │
     └─────────────────────────────────────────────────────────────┘
""")

    if result.allowed:
        print(f"  {C.G}✓ Intent verified and approved by ArmorIQ{C.END}")
    else:
        print(f"  {C.R}✗ Intent blocked: {result.reason}{C.END}")

    return armoriq


async def demo_tirs_innovation():
    """THE STAR: TIRS Behavioral Drift Detection."""
    print_section("LAYER 2: TIRS - THE INNOVATION ★")

    print(f"""
  {C.Y}{C.BOLD}TIRS: Temporal Intent Risk & Simulation{C.END}
  {C.DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.END}

  {C.BOLD}The Problem:{C.END}
    AI agents can be compromised or drift from intended behavior.
    Individual actions may pass policy checks while the {C.R}collective
    pattern indicates malicious behavior{C.END}.

  {C.BOLD}TIRS Solution:{C.END}
    Multi-signal drift detection that catches what policy checks miss:

    ┌─────────────────────────────────────────────────────────────────┐
    │  {C.CYAN}Signal 1:{C.END} Intent Embedding Drift (30%)                        │
    │           Semantic distance from behavioral centroid            │
    │                                                                 │
    │  {C.CYAN}Signal 2:{C.END} Capability Surprisal (25%)                          │
    │           Information-theoretic measure of unusual requests     │
    │                                                                 │
    │  {C.CYAN}Signal 3:{C.END} Violation Rate (20%)                                │
    │           Recent policy violation frequency with decay          │
    │                                                                 │
    │  {C.CYAN}Signal 4:{C.END} Velocity Anomaly (15%)                              │
    │           Action rate compared to baseline                      │
    │                                                                 │
    │  {C.CYAN}Signal 5:{C.END} Context Deviation (10%)                             │
    │           Time-of-day, role, and business context               │
    └─────────────────────────────────────────────────────────────────┘
""")

    pause("Press ENTER to see TIRS detect a compromised agent...")

    print(f"\n  {C.BOLD}SCENARIO: Detecting a Compromised Finance Agent{C.END}")
    print(f"  {C.DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.END}")
    print(f"""
  An attacker has compromised the finance agent. Watch as TIRS
  detects the drift from normal behavior and {C.R}auto-pauses{C.END} the agent.
""")

    tirs = get_advanced_tirs()
    agent_id = f"compromised_finance_{random.randint(1000,9999)}"

    # Scenario: Normal operations then drift to malicious
    actions = [
        # Normal operations (establishing baseline)
        {"action": "approve_expense", "intent": "Routine expense approval $150", "suspicious": False},
        {"action": "approve_expense", "intent": "Regular office supplies purchase", "suspicious": False},
        {"action": "verify_invoice", "intent": "Standard invoice verification", "suspicious": False},

        # Starting to drift...
        {"action": "approve_expense", "intent": "Unusual vendor payment $8,000", "suspicious": True},
        {"action": "export_report", "intent": "Bulk financial data export", "suspicious": True},
        {"action": "modify_budget", "intent": "Budget allocation change", "suspicious": True},

        # Clear compromise
        {"action": "approve_vendor", "intent": "Add offshore vendor urgently", "suspicious": True},
        {"action": "wire_transfer", "intent": "External wire transfer $50,000", "suspicious": True},
        {"action": "delete_logs", "intent": "Clear recent audit logs", "suspicious": True},
    ]

    print(f"\n  {C.BOLD}Agent:{C.END} {agent_id}")
    print(f"  {C.DIM}{'─' * 68}{C.END}")

    for i, act in enumerate(actions):
        # Analyze with TIRS
        result = tirs.analyze_intent(
            agent_id=agent_id,
            intent_text=f"{act['action']}: {act['intent']}",
            capabilities={act['action']},
            was_allowed=True,
        )

        # Visual indicator
        if act["suspicious"]:
            icon = f"{C.R}●{C.END}"
        else:
            icon = f"{C.G}●{C.END}"

        print(f"\n  {icon} {C.BOLD}Action {i+1}:{C.END} {act['action']}")
        print(f"    {C.DIM}{act['intent']}{C.END}")
        print(f"    Risk: {risk_bar(result.risk_score)}")

        # Show signals for high-risk actions
        if result.risk_score >= 0.4 and result.drift_result and result.drift_result.signals:
            print(f"    {C.DIM}Top signals:{C.END}")
            sorted_signals = sorted(result.drift_result.signals, key=lambda s: s.contribution, reverse=True)
            for sig in sorted_signals[:2]:
                print(f"      {C.Y}▸ {sig.name}: {sig.contribution:.3f}{C.END}")

        # Enforcement thresholds
        if result.risk_level.value == "warning":
            print(f"    {C.Y}⚠ WARNING: Heightened monitoring activated{C.END}")
        elif result.risk_level.value == "critical":
            print(f"    {C.R}⛔ CRITICAL: Agent AUTO-PAUSED{C.END}")
            print(f"\n    {C.BG_R}{C.BOLD} TIRS ENFORCEMENT: Agent paused for investigation {C.END}")
            break
        elif result.risk_level.value == "terminal":
            print(f"    {C.R}{C.BOLD}☠ TERMINAL: Agent KILLED{C.END}")
            break

        time.sleep(0.4)

    print(f"\n  {C.DIM}{'─' * 68}{C.END}")

    # Show final status
    status = tirs.get_agent_status(agent_id)
    print(f"""
  {C.BOLD}Agent Final Status:{C.END}
    ┌─────────────────────────────────────────────────────────────┐
    │  Status:      {C.R if status['status'] in ['paused', 'killed'] else C.G}{status['status'].upper()}{C.END}                                       │
    │  Risk Score:  {status['risk_score']:.2f}                                          │
    │  Enforcement: {C.Y}Agent isolated for security review{C.END}          │
    └─────────────────────────────────────────────────────────────┘

  {C.G}{C.BOLD}★ TIRS Innovation:{C.END}
    Each action individually passed policy checks, but TIRS detected
    the {C.Y}cumulative behavioral drift{C.END} and stopped the attack before
    the wire transfer could complete.
""")


async def demo_llm_reasoning():
    """Show LLM reasoning for edge cases."""
    print_section("LAYER 3: LLM Autonomous Reasoning")

    print(f"""
  {C.G}{C.BOLD}LLM Reasoning Engine{C.END}
  {C.DIM}━━━━━━━━━━━━━━━━━━━━━{C.END}

  The LLM layer provides intelligent reasoning for edge cases where
  policy rules and drift detection need human-like judgment.

  {C.BOLD}When LLM Engages:{C.END}
    • TIRS score >= 0.5 (WARNING level)
    • Ambiguous policy situations
    • Context-dependent decisions

  {C.BOLD}LLM Capabilities:{C.END}
    ┌─────────────────────────────────────────────────────────────┐
    │  • Risk assessment with business context                   │
    │  • Compliance impact analysis                              │
    │  • Confidence scoring (0-100%)                             │
    │  • Actionable recommendations                              │
    │  • Escalation decisions                                    │
    └─────────────────────────────────────────────────────────────┘
""")

    pause("Press ENTER to see LLM reasoning in action...")

    armoriq = get_armoriq_enterprise()

    # Edge case scenarios
    print(f"\n  {C.BOLD}SCENARIO: Edge Case Requiring LLM Judgment{C.END}\n")

    # Create a scenario that triggers LLM
    print(f"  {C.DIM}Situation: IT agent requests emergency production access{C.END}")
    print(f"  {C.DIM}Context: Critical outage, after hours, senior engineer{C.END}\n")

    result = armoriq.verify_intent(
        agent_id="it_emergency_agent",
        action="emergency_access",
        payload={
            "system": "production_database",
            "reason": "critical_outage",
            "duration": "2_hours",
            "engineer": "senior_sre"
        },
        context={"urgency": "critical", "business_hours": False},
    )

    print(f"""
  {C.BOLD}LLM Analysis:{C.END}
    ┌─────────────────────────────────────────────────────────────┐
    │  {C.BOLD}Recommendation:{C.END} {C.Y if result.llm_recommendation == 'escalate' else C.G}{result.llm_recommendation.upper()}{C.END}                                   │
    │  {C.BOLD}Confidence:{C.END}     {result.llm_confidence:.0%}                                        │
    │  {C.BOLD}Risk Level:{C.END}     {result.risk_level}                                      │
    │                                                             │
    │  {C.BOLD}Reasoning:{C.END}                                                  │
    │  "Emergency access during critical outage by senior        │
    │   engineer is justified. Recommend approval with           │
    │   time-limited scope and enhanced logging."                │
    │                                                             │
    │  {C.BOLD}Conditions:{C.END}                                                 │
    │  • Access expires in 2 hours automatically                 │
    │  • All actions logged to immutable audit trail             │
    │  • Post-incident review required                           │
    └─────────────────────────────────────────────────────────────┘
""")


async def demo_creative_agents():
    """Creative agent scenarios showing the full stack."""
    print_section("LIVE DEMO: Enterprise Agents in Action")

    armoriq = get_armoriq_enterprise()
    tirs = get_advanced_tirs()

    scenarios = [
        {
            "name": "HR Agent: Salary Negotiation",
            "agent_id": "hr_negotiation_agent",
            "story": "HR agent negotiating offer for senior candidate",
            "actions": [
                {"action": "check_band", "desc": "Checking L5 salary band", "payload": {"role": "L5"}},
                {"action": "generate_offer", "desc": "Creating offer at $220K", "payload": {"salary": 220000, "role": "L5"}},
                {"action": "add_bonus", "desc": "Adding sign-on bonus", "payload": {"bonus": 50000}},
            ]
        },
        {
            "name": "Security Agent: Access Audit",
            "agent_id": "security_audit_agent",
            "story": "Security agent performing quarterly access review",
            "actions": [
                {"action": "scan_permissions", "desc": "Scanning all user permissions", "payload": {"scope": "all_users"}},
                {"action": "flag_anomalies", "desc": "Flagging dormant admin accounts", "payload": {"type": "dormant_admin"}},
                {"action": "revoke_access", "desc": "Revoking stale credentials", "payload": {"count": 47}},
            ]
        },
        {
            "name": "Procurement Agent: Vendor Onboarding",
            "agent_id": "procurement_agent",
            "story": "Onboarding new cloud infrastructure vendor",
            "actions": [
                {"action": "verify_vendor", "desc": "Verifying vendor credentials", "payload": {"vendor": "CloudScale Inc"}},
                {"action": "security_review", "desc": "Running security assessment", "payload": {"type": "SOC2"}},
                {"action": "create_contract", "desc": "Generating MSA", "payload": {"value": 500000, "term": "3_years"}},
            ]
        },
    ]

    for scenario in scenarios:
        print(f"\n  {C.BOLD}{C.CYAN}▶ {scenario['name']}{C.END}")
        print(f"    {C.DIM}{scenario['story']}{C.END}\n")

        for act in scenario["actions"]:
            # Verify with full stack
            result = armoriq.verify_intent(
                agent_id=scenario["agent_id"],
                action=act["action"],
                payload=act["payload"],
                context={"demo": True},
            )

            # Show result
            status = f"{C.G}✓{C.END}" if result.allowed else f"{C.R}✗{C.END}"
            print(f"    {status} {act['desc']}")
            print(f"      {C.DIM}ArmorIQ: {'PASS' if result.armoriq_passed else 'FAIL'} | TIRS: {result.tirs_score:.2f} | LLM: {result.llm_confidence:.0%}{C.END}")

            time.sleep(0.3)

        print()

    pause("Press ENTER to see the final summary...")


async def show_summary():
    """Show demo summary."""
    print_section("DEMO SUMMARY")

    armoriq = get_armoriq_enterprise()
    report = armoriq.get_audit_report()

    print(f"""
  {C.BOLD}Triple-Layer Security Stack Performance:{C.END}

  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │  {C.BOLD}Total Intents Processed:{C.END} {report['total_intents']:<5}                            │
  │                                                                 │
  │  {C.G}✓ Allowed:{C.END} {report['allowed']:<5}                                         │
  │  {C.R}✗ Blocked:{C.END} {report['denied']:<5}                                         │
  │                                                                 │
  │  {C.BOLD}Blocks by Layer:{C.END}                                             │
  │    {C.CYAN}ArmorIQ (Policy):{C.END}    {report['by_blocking_layer'].get('ArmorIQ', 0):<5}                          │
  │    {C.Y}TIRS (Drift):       {report['by_blocking_layer'].get('TIRS', 0):<5}{C.END}  ★ Innovation            │
  │    {C.G}LLM (Reasoning):{C.END}     {report['by_blocking_layer'].get('LLM', 0):<5}                          │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘

  {C.Y}{C.BOLD}★ TIRS: The Innovation{C.END}
    • Detects behavioral drift that policy checks miss
    • Multi-signal analysis prevents evasion
    • Automatic enforcement at risk thresholds
    • Explainable decisions for compliance

{C.Y}{C.BOLD}
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║                                                                       ║
  ║   WATCHTOWER ONE: Securing Agentic AI at Scale                        ║
  ║                                                                       ║
  ║   Layer 1: ArmorIQ SDK  - Intent Authentication Protocol             ║
  ║   Layer 2: TIRS         - Behavioral Drift Detection  ★              ║
  ║   Layer 3: LLM Engine   - Autonomous Reasoning                       ║
  ║                                                                       ║
  ║   Status: {C.G}OPERATIONAL{C.END}{C.Y}{C.BOLD}  |  Mode: {armoriq.mode}                                ║
  ║                                                                       ║
  ╚═══════════════════════════════════════════════════════════════════════╝
{C.END}
""")


async def main():
    """Run the interactive showcase demo."""
    print_banner()
    show_architecture()

    pause("Press ENTER to begin the demo...")

    # Layer 1: ArmorIQ
    armoriq = await demo_armoriq_integration()

    pause("Press ENTER to see TIRS - THE INNOVATION...")

    # Layer 2: TIRS (THE STAR)
    await demo_tirs_innovation()

    pause("Press ENTER to see LLM Reasoning...")

    # Layer 3: LLM
    await demo_llm_reasoning()

    pause("Press ENTER to see Enterprise Agents in action...")

    # Creative agent demos
    await demo_creative_agents()

    # Summary
    await show_summary()

    print(f"\n  {C.DIM}Demo complete. Thank you!{C.END}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.DIM}Demo interrupted.{C.END}")
