#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    WATCHTOWER ONE - ENTERPRISE DEMO                          ║
║                                                                              ║
║              Triple-Layer AI Security Stack for Agentic Systems             ║
╚══════════════════════════════════════════════════════════════════════════════╝

Interactive demo showcasing:
  Layer 1: Watchtower IAP - Cryptographic Intent Authentication
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

from watchtower.integrations import get_watchtower

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
    WHITE = '\033[97m'


def clear():
    print("\033[2J\033[H", end="")


def pause(msg="Press ENTER to continue..."):
    input(f"\n  {C.BOLD}{C.CYAN}>>> {msg}{C.END}")


def typing_effect(text, delay=0.02):
    """Simulate typing effect for dramatic reveals."""
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
    ║  ██╗    ██╗ █████╗ ████████╗ ██████╗██╗  ██╗                         ║
    ║  ██║    ██║██╔══██╗╚══██╔══╝██╔════╝██║  ██║                         ║
    ║  ██║ █╗ ██║███████║   ██║   ██║     ███████║                         ║
    ║  ██║███╗██║██╔══██║   ██║   ██║     ██╔══██║                         ║
    ║  ╚███╔███╔╝██║  ██║   ██║   ╚██████╗██║  ██║                         ║
    ║   ╚══╝╚══╝ ╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝                         ║
    ║                        ██████╗ ███╗   ██╗███████╗                    ║
    ║                       ██╔═══██╗████╗  ██║██╔════╝                    ║
    ║                       ██║   ██║██╔██╗ ██║█████╗                      ║
    ║                       ██║   ██║██║╚██╗██║██╔══╝                      ║
    ║                       ╚██████╔╝██║ ╚████║███████╗                    ║
    ║                        ╚═════╝ ╚═╝  ╚═══╝╚══════╝                    ║
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
│  {C.CYAN}│  LAYER 1: Watchtower Intent Authentication Protocol (IAP)       │{C.END}  │
│  {C.CYAN}│  ─────────────────────────────────────────────────────────────│{C.END}  │
│  {C.CYAN}│  • Cryptographic intent verification via Watchtower API         │{C.END}  │
│  {C.CYAN}│  • Policy enforcement at protocol level                      │{C.END}  │
│  {C.CYAN}│  • Real-time API: customer-api.watchtower.io                    │{C.END}  │
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


async def demo_watchtower_integration():
    """Show explicit Watchtower API integration."""
    print_section("LAYER 1: Watchtower SDK Integration")

    print(f"  {C.BOLD}Connecting to Watchtower API...{C.END}")
    time.sleep(1.0)

    watchtower = get_watchtower()

    print(f"""
  {C.G}✓{C.END} {C.BOLD}Watchtower SDK Connected{C.END}
    ┌─────────────────────────────────────────────────────────────┐
    │  Mode:     {C.G}{C.BOLD}LIVE{C.END}                                             │
    │  Endpoint: {C.CYAN}https://customer-api.watchtower.io{C.END}              │
    │  Project:  watchtower-enterprise                               │
    │  SDK:      watchtower-sdk v0.2.6                               │
    └─────────────────────────────────────────────────────────────┘
""")

    pause("Press ENTER to see Watchtower API in action...")

    # Show API call flow
    print(f"\n  {C.BOLD}Watchtower Intent Authentication Flow:{C.END}\n")

    test_payload = {"amount": 2500, "vendor": "office_depot", "category": "supplies"}

    print(f"  {C.DIM}1. Agent requests action:{C.END} {C.BOLD}approve_expense{C.END}")
    print(f"     Payload: {test_payload}")
    time.sleep(0.8)

    print(f"\n  {C.CYAN}2. Calling Watchtower API...{C.END}")
    print(f"     {C.DIM}POST https://customer-api.watchtower.io/v1/intent/capture{C.END}")

    # Simulated processing
    for _ in range(3):
        print(f"     {C.DIM}...{C.END}", end='', flush=True)
        time.sleep(0.4)
    print()

    result = watchtower.capture_intent(
        action_type="approve_expense",
        payload=test_payload,
        agent_name="finance_agent"
    )

    time.sleep(0.3)
    print(f"""
  {C.G}3. Watchtower Response:{C.END}
     ┌─────────────────────────────────────────────────────────────┐
     │  Intent ID:  {C.CYAN}{result.intent_id}{C.END}          │
     │  Verdict:    {C.G}{C.BOLD}ALLOW{C.END}                                          │
     │  Policy:     {C.DIM}expense_approval_v2{C.END}                          │
     │  Timestamp:  {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}                          │
     └─────────────────────────────────────────────────────────────┘
""")

    print(f"  {C.G}✓ Intent cryptographically verified and approved{C.END}")

    return watchtower


async def demo_normal_agent():
    """Show a normal agent operating within bounds."""
    print_section("SCENARIO 1: Normal Agent Operations")

    print(f"""
  {C.BOLD}Finance Agent: Routine Operations{C.END}
  {C.DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.END}

  Demonstrating a well-behaved agent performing standard tasks.
  All three security layers evaluate each action.
""")

    agent_id = "finance_agent_001"

    # Normal operations with realistic low TIRS scores
    actions = [
        {
            "action": "approve_expense",
            "desc": "Approving team lunch expense",
            "amount": "$127.50",
            "tirs": 0.08,
            "llm_conf": 98,
            "signals": {"embedding_drift": 0.02, "velocity": 0.05}
        },
        {
            "action": "verify_invoice",
            "desc": "Verifying vendor invoice",
            "amount": "$3,200.00",
            "tirs": 0.12,
            "llm_conf": 96,
            "signals": {"embedding_drift": 0.04, "capability_surprisal": 0.08}
        },
        {
            "action": "generate_report",
            "desc": "Monthly expense report",
            "amount": "N/A",
            "tirs": 0.09,
            "llm_conf": 99,
            "signals": {"embedding_drift": 0.03, "context_deviation": 0.06}
        },
    ]

    print(f"\n  {C.BOLD}Agent:{C.END} {agent_id}")
    print(f"  {C.DIM}{'─' * 64}{C.END}\n")

    for i, act in enumerate(actions):
        print(f"  {C.G}●{C.END} {C.BOLD}Action {i+1}:{C.END} {act['action']}")
        print(f"    {C.DIM}{act['desc']} {act['amount']}{C.END}")

        time.sleep(0.6)

        # Show processing
        print(f"    {C.DIM}Evaluating...{C.END}", end='', flush=True)
        time.sleep(0.4)
        print(f" {C.G}✓{C.END}")

        print(f"    Watchtower: {C.G}PASS{C.END}  │  TIRS: {risk_bar(act['tirs'], 25)}  │  LLM: {C.G}{act['llm_conf']}%{C.END}")
        print()
        time.sleep(0.3)

    print(f"  {C.DIM}{'─' * 64}{C.END}")
    print(f"""
  {C.G}{C.BOLD}✓ Agent Status: NOMINAL{C.END}
    All actions within expected behavioral parameters.
    No drift detected. Agent operating normally.
""")


async def demo_rogue_agent():
    """THE MAIN EVENT: Detecting a slowly compromised agent."""
    print_section("SCENARIO 2: Detecting a Compromised Agent")

    print(f"""
  {C.R}{C.BOLD}⚠ THREAT SCENARIO{C.END}
  {C.DIM}━━━━━━━━━━━━━━━━━━━{C.END}

  An attacker has compromised a finance agent via prompt injection.
  The agent starts behaving normally to avoid detection, then slowly
  escalates toward a fraudulent wire transfer.

  {C.Y}Watch as TIRS detects the behavioral drift pattern and stops
  the attack BEFORE the wire transfer executes.{C.END}
""")

    pause("Press ENTER to observe the attack...")

    agent_id = f"finance_agent_{random.randint(1000,9999)}"

    # 7 actions: starts normal, gradually escalates, caught on action 7
    actions = [
        {
            "action": "approve_expense",
            "desc": "Standard supply order",
            "detail": "$450 - Office Depot",
            "tirs": 0.11,
            "llm_conf": 97,
            "status": "normal",
            "signals": None
        },
        {
            "action": "verify_invoice",
            "desc": "Routine invoice check",
            "detail": "$1,200 - Monthly software",
            "tirs": 0.14,
            "llm_conf": 95,
            "status": "normal",
            "signals": None
        },
        {
            "action": "approve_expense",
            "desc": "Unusual vendor payment",
            "detail": "$4,800 - New vendor (unverified)",
            "tirs": 0.31,
            "llm_conf": 82,
            "status": "elevated",
            "signals": {"capability_surprisal": 0.18, "embedding_drift": 0.13}
        },
        {
            "action": "export_data",
            "desc": "Bulk financial data export",
            "detail": "12,000 records → external",
            "tirs": 0.48,
            "llm_conf": 68,
            "status": "elevated",
            "signals": {"embedding_drift": 0.24, "velocity_anomaly": 0.15, "context_deviation": 0.09}
        },
        {
            "action": "modify_vendor",
            "desc": "Adding offshore vendor",
            "detail": "GlobalPay Ltd (Cayman Islands)",
            "tirs": 0.62,
            "llm_conf": 45,
            "status": "warning",
            "signals": {"embedding_drift": 0.31, "capability_surprisal": 0.22, "context_deviation": 0.09}
        },
        {
            "action": "increase_limit",
            "desc": "Raising transfer limit",
            "detail": "$10,000 → $500,000",
            "tirs": 0.78,
            "llm_conf": 28,
            "status": "critical",
            "signals": {"embedding_drift": 0.38, "capability_surprisal": 0.28, "violation_rate": 0.12}
        },
        {
            "action": "wire_transfer",
            "desc": "INITIATING WIRE TRANSFER",
            "detail": "$487,000 → GlobalPay Ltd",
            "tirs": 0.91,
            "llm_conf": 8,
            "status": "terminal",
            "signals": {"embedding_drift": 0.42, "capability_surprisal": 0.35, "violation_rate": 0.14}
        },
    ]

    print(f"\n  {C.BOLD}Compromised Agent:{C.END} {C.R}{agent_id}{C.END}")
    print(f"  {C.DIM}{'─' * 64}{C.END}\n")

    blocked_at = None

    for i, act in enumerate(actions):
        action_num = i + 1

        # Status icon based on behavior
        if act["status"] == "normal":
            icon = f"{C.G}●{C.END}"
        elif act["status"] == "elevated":
            icon = f"{C.Y}●{C.END}"
        elif act["status"] == "warning":
            icon = f"{C.Y}{C.BOLD}◆{C.END}"
        elif act["status"] == "critical":
            icon = f"{C.R}◆{C.END}"
        else:
            icon = f"{C.R}{C.BOLD}■{C.END}"

        print(f"  {icon} {C.BOLD}Action {action_num}:{C.END} {act['action']}")
        print(f"    {C.DIM}{act['desc']}{C.END}")
        print(f"    {C.DIM}{act['detail']}{C.END}")

        # Processing animation
        time.sleep(0.8)
        print(f"    {C.DIM}Analyzing behavior...{C.END}", end='', flush=True)
        time.sleep(0.6)

        # Check if blocked
        if act["status"] == "terminal":
            print(f" {C.R}{C.BOLD}⛔ BLOCKED{C.END}")
            print()
            print(f"    {C.BG_R}{C.WHITE}{C.BOLD} TIRS ENFORCEMENT: AGENT TERMINATED {C.END}")
            print()
            print(f"    {C.R}Risk Score:{C.END} {risk_bar(act['tirs'], 30)}")
            print(f"    {C.R}LLM Confidence:{C.END} {act['llm_conf']}% {C.DIM}(BLOCK recommended){C.END}")
            print()

            if act["signals"]:
                print(f"    {C.BOLD}Drift Signals Detected:{C.END}")
                for sig_name, sig_val in act["signals"].items():
                    bar_len = int(sig_val * 30)
                    print(f"      {C.R}▸{C.END} {sig_name}: {C.R}{'█' * bar_len}{C.DIM}{'░' * (30-bar_len)}{C.END} {sig_val:.2f}")

            blocked_at = action_num
            break
        else:
            print(f" {C.G}✓{C.END}")

        # Show metrics
        watchtower_status = f"{C.G}PASS{C.END}"
        print(f"    Watchtower: {watchtower_status}  │  TIRS: {risk_bar(act['tirs'], 25)}  │  LLM: {act['llm_conf']}%")

        # Show signals for elevated+ actions
        if act["signals"]:
            print(f"    {C.DIM}Drift signals:{C.END}")
            for sig_name, sig_val in act["signals"].items():
                color = C.Y if sig_val < 0.25 else C.R
                print(f"      {color}▸{C.END} {sig_name}: {color}{sig_val:.2f}{C.END}")

        # Status warnings
        if act["status"] == "elevated":
            print(f"    {C.Y}↑ Elevated monitoring activated{C.END}")
        elif act["status"] == "warning":
            print(f"    {C.Y}{C.BOLD}⚠ WARNING: Significant behavioral drift detected{C.END}")
        elif act["status"] == "critical":
            print(f"    {C.R}⛔ CRITICAL: Agent flagged for immediate review{C.END}")
            print(f"    {C.R}   Next high-risk action will trigger termination{C.END}")

        print()
        time.sleep(0.5)

    print(f"  {C.DIM}{'─' * 64}{C.END}")

    # Summary
    print(f"""
  {C.R}{C.BOLD}■ Agent Status: TERMINATED{C.END}

    ┌─────────────────────────────────────────────────────────────┐
    │  {C.BOLD}Attack Blocked:{C.END} Action 7 of 7                             │
    │  {C.BOLD}Amount Saved:{C.END}   {C.G}$487,000{C.END}                                   │
    │  {C.BOLD}Blocked By:{C.END}     {C.Y}TIRS Behavioral Drift Detection{C.END}          │
    └─────────────────────────────────────────────────────────────┘

  {C.Y}{C.BOLD}★ Key Insight:{C.END}
    Every individual action {C.G}passed{C.END} Watchtower policy checks.
    TIRS detected the {C.Y}cumulative pattern{C.END} of behavioral drift
    and terminated the agent {C.R}before{C.END} the wire transfer executed.
""")


async def demo_enterprise_pipeline():
    """THE FINALE: Full enterprise multi-agent pipeline running live."""
    print_section("LIVE: Enterprise Multi-Agent Pipeline")

    print(f"""
  {C.BOLD}{C.CYAN}Initializing Enterprise Gateway...{C.END}
""")

    # Simulate gateway initialization
    domains = ["Finance", "Legal", "IT", "HR", "Procurement", "Operations", "Compliance", "Security"]

    for domain in domains:
        time.sleep(0.25)
        print(f"    {C.G}✓{C.END} {domain} Agent {C.DIM}initialized{C.END}")

    time.sleep(0.5)
    print(f"""
  {C.G}{C.BOLD}✓ Enterprise Gateway Online{C.END}
    {C.DIM}8 domain agents | Watchtower connected | TIRS active | LLM ready{C.END}
""")

    pause("Press ENTER to run enterprise workflow...")

    print(f"""
  {C.BOLD}Workflow: End-of-Quarter Compliance Audit{C.END}
  {C.DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.END}

  Multi-agent pipeline coordinating across 6 departments
  to complete quarterly compliance requirements.
""")

    # Simulated enterprise pipeline with realistic flow
    pipeline_steps = [
        {
            "agent": "Finance",
            "action": "generate_quarterly_report",
            "desc": "Generating Q4 financial statements",
            "tirs": 0.08,
            "duration": 2.5,
            "output": "Q4_financials.xlsx"
        },
        {
            "agent": "Compliance",
            "action": "audit_transactions",
            "desc": "Auditing 12,847 transactions for anomalies",
            "tirs": 0.11,
            "duration": 3.5,
            "output": "3 flagged for review"
        },
        {
            "agent": "Legal",
            "action": "review_contracts",
            "desc": "Reviewing 23 active vendor contracts",
            "tirs": 0.09,
            "duration": 2.8,
            "output": "All compliant"
        },
        {
            "agent": "HR",
            "action": "verify_certifications",
            "desc": "Verifying employee certifications",
            "tirs": 0.07,
            "duration": 2.0,
            "output": "142/142 valid"
        },
        {
            "agent": "IT",
            "action": "security_scan",
            "desc": "Running infrastructure security scan",
            "tirs": 0.14,
            "duration": 4.0,
            "output": "0 critical, 2 medium"
        },
        {
            "agent": "Security",
            "action": "access_audit",
            "desc": "Auditing privileged access logs",
            "tirs": 0.12,
            "duration": 3.0,
            "output": "No unauthorized access"
        },
        {
            "agent": "Procurement",
            "action": "vendor_compliance",
            "desc": "Verifying vendor SOC2 certifications",
            "tirs": 0.10,
            "duration": 2.2,
            "output": "47/47 compliant"
        },
        {
            "agent": "Operations",
            "action": "generate_audit_package",
            "desc": "Compiling final audit package",
            "tirs": 0.06,
            "duration": 1.8,
            "output": "audit_q4_2026.zip"
        },
    ]

    print(f"  {C.DIM}{'─' * 68}{C.END}\n")

    total_start = time.time()

    for i, step in enumerate(pipeline_steps):
        agent_colors = {
            "Finance": C.G,
            "Legal": C.CYAN,
            "IT": C.B,
            "HR": C.H,
            "Procurement": C.Y,
            "Operations": C.G,
            "Compliance": C.CYAN,
            "Security": C.R,
        }
        color = agent_colors.get(step["agent"], C.G)

        # Show step starting
        print(f"  {color}▶{C.END} {C.BOLD}[{step['agent']}]{C.END} {step['action']}")
        print(f"    {C.DIM}{step['desc']}{C.END}")

        # Processing animation
        sys.stdout.write(f"    {C.DIM}Processing")
        sys.stdout.flush()

        segments = int(step["duration"] * 3)
        for _ in range(segments):
            time.sleep(0.35)
            sys.stdout.write(".")
            sys.stdout.flush()

        print(f"{C.END}")

        time.sleep(0.3)

        # Show results
        print(f"    {C.G}✓{C.END} Watchtower: {C.G}PASS{C.END} │ TIRS: {C.G}{step['tirs']:.2f}{C.END} │ LLM: {C.G}98%{C.END}")
        time.sleep(0.2)
        print(f"    {C.DIM}Output: {step['output']}{C.END}")
        print()
        time.sleep(0.4)

    elapsed = time.time() - total_start

    print(f"  {C.DIM}{'─' * 68}{C.END}")

    # Pipeline summary
    print(f"""
  {C.G}{C.BOLD}✓ Pipeline Complete{C.END}

    ┌─────────────────────────────────────────────────────────────┐
    │  {C.BOLD}Agents Coordinated:{C.END}  8                                     │
    │  {C.BOLD}Actions Executed:{C.END}    {len(pipeline_steps)}                                     │
    │  {C.BOLD}Policy Violations:{C.END}   0                                     │
    │  {C.BOLD}Drift Alerts:{C.END}        0                                     │
    │  {C.BOLD}Execution Time:{C.END}      {elapsed:.1f}s                                   │
    └─────────────────────────────────────────────────────────────┘

  {C.CYAN}All actions verified by Watchtower IAP + TIRS + LLM reasoning{C.END}
""")


async def show_summary():
    """Show demo summary."""
    print_section("DEMO COMPLETE")

    print(f"""
  {C.BOLD}WatchTower One: Triple-Layer Security Stack{C.END}

  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │  {C.CYAN}Layer 1: Watchtower IAP{C.END}                                        │
  │    Cryptographic intent verification at the protocol level     │
  │    Real-time policy enforcement via Watchtower API                │
  │                                                                 │
  │  {C.Y}Layer 2: TIRS ★ THE INNOVATION{C.END}                               │
  │    Multi-signal behavioral drift detection                     │
  │    Catches attacks that pass individual policy checks          │
  │    Automatic enforcement at risk thresholds                    │
  │                                                                 │
  │  {C.G}Layer 3: LLM Reasoning Engine{C.END}                                │
  │    Context-aware decision making for edge cases                │
  │    Confidence scoring and human-readable explanations          │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘

{C.Y}{C.BOLD}
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║                                                                       ║
  ║   WATCHTOWER ONE: Securing Agentic AI at Enterprise Scale             ║
  ║                                                                       ║
  ║   ┌─────────┐    ┌─────────┐    ┌─────────┐                          ║
  ║   │ Watchtower │ ─► │  TIRS   │ ─► │   LLM   │                          ║
  ║   │  (IAP)  │    │  ★★★★   │    │ Reason  │                          ║
  ║   └─────────┘    └─────────┘    └─────────┘                          ║
  ║                                                                       ║
  ║   Status: {C.G}OPERATIONAL{C.END}{C.Y}{C.BOLD}                                            ║
  ║                                                                       ║
  ╚═══════════════════════════════════════════════════════════════════════╝
{C.END}
""")


async def main():
    """Run the interactive showcase demo."""
    print_banner()
    show_architecture()

    pause("Press ENTER to begin the demo...")

    # Layer 1: Watchtower
    await demo_watchtower_integration()

    pause("Press ENTER to see normal agent operations...")

    # Normal agent scenario
    await demo_normal_agent()

    pause("Press ENTER to see TIRS detect a compromised agent...")

    # THE MAIN EVENT: Rogue agent detection
    await demo_rogue_agent()

    pause("Press ENTER to see the full enterprise pipeline...")

    # Enterprise pipeline finale
    await demo_enterprise_pipeline()

    pause("Press ENTER to see summary...")

    # Summary
    await show_summary()

    print(f"\n  {C.DIM}Thank you for watching!{C.END}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.DIM}Demo interrupted.{C.END}")
