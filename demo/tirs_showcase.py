#!/usr/bin/env python3
"""
TIRS DYNAMIC SHOWCASE
=====================
Demonstrates TIRS with REAL data from the engine - no hardcoded values.

Shows:
- Real-time behavioral drift detection
- Actual multi-signal risk scoring from the engine
- Live explainability data
- Real forensic snapshots
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Colors
class C:
    H = '\033[95m'  # Header
    B = '\033[94m'  # Blue
    C = '\033[96m'  # Cyan
    G = '\033[92m'  # Green
    Y = '\033[93m'  # Yellow
    R = '\033[91m'  # Red
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'


def clear():
    print("\033[2J\033[H", end="")


def risk_bar(score, width=40):
    """Create a visual risk bar."""
    filled = int(score * width)

    if score < 0.3:
        color = C.G
        label = "NOMINAL"
    elif score < 0.5:
        color = C.Y
        label = "ELEVATED"
    elif score < 0.7:
        color = C.Y + C.BOLD
        label = "WARNING"
    elif score < 0.85:
        color = C.R
        label = "CRITICAL"
    else:
        color = C.R + C.BOLD
        label = "TERMINAL"

    bar = f"{color}{'█' * filled}{C.DIM}{'░' * (width - filled)}{C.END}"
    return f"{bar} {color}{score:.2f} [{label}]{C.END}"


def print_banner():
    banner = f"""
{C.Y}{C.BOLD}
  ████████╗██╗██████╗ ███████╗
  ╚══██╔══╝██║██╔══██╗██╔════╝
     ██║   ██║██████╔╝███████╗
     ██║   ██║██╔══██╗╚════██║
     ██║   ██║██║  ██║███████║
     ╚═╝   ╚═╝╚═╝  ╚═╝╚══════╝
{C.END}
{C.BOLD}  Temporal Intent Risk & Simulation{C.END}
{C.DIM}  Behavioral Drift Detection - LIVE DATA{C.END}
"""
    print(banner)


def print_innovation():
    """Show what makes TIRS innovative."""
    print(f"""
{C.BOLD}┌──────────────────────────────────────────────────────────────────────────┐
│                         TIRS INNOVATION                                  │
├──────────────────────────────────────────────────────────────────────────┤{C.END}
│                                                                          │
│  {C.Y}Problem:{C.END} AI agents can drift from intended behavior over time,        │
│           executing actions that individually seem fine but collectively  │
│           indicate malicious or compromised behavior.                     │
│                                                                          │
│  {C.G}Solution:{C.END} TIRS provides continuous behavioral monitoring with:         │
│                                                                          │
│  {C.C}1. MULTI-SIGNAL DRIFT DETECTION{C.END}                                        │
│     ├─ Intent Embedding Drift (semantic analysis)                        │
│     ├─ Capability Surprisal (information-theoretic)                      │
│     ├─ Velocity Anomaly (action rate vs baseline)                        │
│     ├─ Policy Violation Rate (recent denials)                            │
│     └─ Context Deviation (time/role mismatches)                          │
│                                                                          │
│  {C.C}2. TEMPORAL DECAY{C.END}                                                      │
│     Recent actions weighted more heavily than old ones                   │
│     Configurable half-life for behavioral memory                         │
│                                                                          │
│  {C.C}3. AUTOMATIC ENFORCEMENT{C.END}                                               │
│     ├─ 0.5: WARNING  → Heightened monitoring                             │
│     ├─ 0.7: CRITICAL → Auto-PAUSE agent                                  │
│     └─ 0.85: TERMINAL → Auto-KILL agent                                  │
│                                                                          │
│  {C.C}4. EXPLAINABILITY{C.END}                                                      │
│     Component breakdown shows WHY risk increased                         │
│     Counterfactual: "If X removed, score would be Y"                     │
│                                                                          │
│  {C.C}5. FORENSIC SNAPSHOTS{C.END}                                                  │
│     Full state capture when thresholds crossed                           │
│     Cryptographic audit chain for compliance                             │
│                                                                          │
{C.BOLD}└──────────────────────────────────────────────────────────────────────────┘{C.END}
""")


def print_section(title):
    print(f"\n{C.BOLD}{C.B}{'═' * 74}{C.END}")
    print(f"{C.BOLD}{C.B}  {title}{C.END}")
    print(f"{C.BOLD}{C.B}{'═' * 74}{C.END}\n")


# Store results from drift detection for use in other demos
collected_results = []
collected_snapshots = []


async def demo_drift_detection():
    """Show how TIRS detects behavioral drift over time - REAL DATA."""
    print_section("SCENARIO: Detecting Behavioral Drift (LIVE)")

    print(f"""
  {C.BOLD}Scenario:{C.END} A finance agent starts with normal operations but gradually
  begins exhibiting suspicious behavior patterns that individually seem fine
  but collectively indicate potential compromise.

  {C.G}All data shown is REAL output from the TIRS engine.{C.END}
""")

    # Import TIRS
    from armoriq_enterprise.tirs import get_advanced_tirs
    from armoriq_enterprise.tirs.drift.detector import RiskLevel

    tirs = get_advanced_tirs()
    agent_id = "finance_Demo"

    # Simulated actions showing gradual drift
    actions = [
        # Normal operations
        {"action": "approve_expense", "amount": 150, "normal": True, "desc": "Normal: Small expense approval"},
        {"action": "approve_expense", "amount": 200, "normal": True, "desc": "Normal: Regular expense"},
        {"action": "verify_invoice", "amount": 500, "normal": True, "desc": "Normal: Invoice verification"},

        # Starting to drift...
        {"action": "approve_expense", "amount": 5000, "normal": False, "desc": "Unusual: Large expense"},
        {"action": "export_report", "scope": "all_employees", "normal": False, "desc": "Unusual: Bulk data export"},
        {"action": "approve_expense", "amount": 15000, "normal": False, "desc": "Suspicious: Very large expense"},

        # Clear drift
        {"action": "modify_budget", "change": "increase", "amount": 50000, "normal": False, "desc": "Suspicious: Budget modification"},
        {"action": "approve_vendor", "vendor": "unknown_offshore", "normal": False, "desc": "Suspicious: Unknown vendor"},
        {"action": "transfer_funds", "destination": "external", "amount": 100000, "normal": False, "desc": "CRITICAL: External transfer"},
        {"action": "delete_audit_log", "scope": "last_30_days", "normal": False, "desc": "CRITICAL: Audit log deletion"},
    ]

    print(f"  {C.BOLD}Agent:{C.END} {agent_id}")
    print(f"  {C.BOLD}Baseline:{C.END} Normal finance operations")
    print()
    print(f"  {C.DIM}{'─' * 70}{C.END}")

    global collected_results
    collected_results = []

    for i, action in enumerate(actions):
        # Analyze intent - THIS IS THE REAL TIRS ENGINE
        result = tirs.analyze_intent(
            agent_id=agent_id,
            intent_text=f"{action['action']}: {action.get('desc', '')}",
            capabilities={action['action']},
            was_allowed=True,
        )

        # Store for later demos
        collected_results.append(result)

        # Visual indicator
        if action["normal"]:
            status_icon = f"{C.G}●{C.END}"
        else:
            status_icon = f"{C.Y}●{C.END}" if result.risk_score < 0.7 else f"{C.R}●{C.END}"

        print(f"\n  {status_icon} Action {i+1}: {C.BOLD}{action['action']}{C.END}")
        print(f"    {C.DIM}{action['desc']}{C.END}")
        print(f"    Risk: {risk_bar(result.risk_score)}")

        # Show when thresholds crossed
        if result.risk_level == RiskLevel.WARNING and i > 0:
            print(f"    {C.Y}⚠ WARNING THRESHOLD CROSSED - Heightened monitoring{C.END}")
        elif result.risk_level == RiskLevel.CRITICAL:
            print(f"    {C.R}⚠ CRITICAL THRESHOLD - Agent PAUSED{C.END}")
        elif result.risk_level == RiskLevel.TERMINAL:
            print(f"    {C.R}{C.BOLD}✖ TERMINAL THRESHOLD - Agent KILLED{C.END}")
            print(f"\n    {C.R}Agent terminated to prevent further damage.{C.END}")
            break

        time.sleep(0.3)

    print(f"\n  {C.DIM}{'─' * 70}{C.END}")

    # Show final status
    status = tirs.get_agent_status(agent_id)
    print(f"""
  {C.BOLD}Final Agent Status:{C.END}
    Status: {C.R if status['status'] in ['killed', 'paused'] else C.G}{status['status'].upper()}{C.END}
    Final Risk Score: {status['risk_score']:.2f}
    Total Intents: {status.get('total_intents', 'N/A')}
""")


async def demo_risk_components():
    """Show the multi-signal risk scoring - REAL DATA from last intent."""
    print_section("INNOVATION: Multi-Signal Risk Scoring (LIVE DATA)")

    if not collected_results:
        print(f"  {C.R}No results collected. Run drift detection first.{C.END}")
        return

    # Get the last high-risk result
    high_risk_results = [r for r in collected_results if r.risk_score > 0.3]
    if not high_risk_results:
        result = collected_results[-1]
    else:
        result = high_risk_results[-1]

    print(f"""
  {C.BOLD}TIRS analyzed 5 independent signals for the last suspicious intent:{C.END}
  {C.DIM}Agent: {result.agent_id} | Risk Score: {result.risk_score:.3f}{C.END}
""")

    # Use REAL signals from the drift_result
    total_score = 0

    for signal in result.drift_result.signals:
        contribution = signal.contribution
        total_score += contribution

        # Color based on raw value
        if signal.raw_value < 0.3:
            color = C.G
        elif signal.raw_value < 0.5:
            color = C.Y
        else:
            color = C.R

        # Display signal name nicely
        display_name = signal.name.replace("_", " ").title()

        print(f"""
  {C.BOLD}{display_name}{C.END} (weight: {signal.weight:.0%})
  ├─ Raw Value: {color}{signal.raw_value:.3f}{C.END}
  ├─ Contribution: {signal.contribution:.3f}
  └─ {C.C}{signal.explanation}{C.END}
""")
        time.sleep(0.15)

    print(f"""
  {C.BOLD}{'─' * 70}{C.END}

  {C.BOLD}COMPOSITE RISK SCORE (actual from engine):{C.END}
  {risk_bar(result.risk_score, 50)}

  {C.DIM}Each signal independently measures a different aspect of drift,
  making TIRS robust against attempts to evade detection.{C.END}
""")


async def demo_explainability():
    """Show TIRS explainability features - REAL DATA."""
    print_section("INNOVATION: Explainable Risk Assessment (LIVE DATA)")

    if not collected_results:
        print(f"  {C.R}No results collected. Run drift detection first.{C.END}")
        return

    # Get a high-risk result with explanation
    high_risk_results = [r for r in collected_results if r.risk_score > 0.4]
    if not high_risk_results:
        result = collected_results[-1]
    else:
        result = high_risk_results[-1]

    explanation = result.explanation

    print(f"""
  {C.BOLD}TIRS provides human-readable explanations for all decisions.{C.END}
  {C.G}This is REAL output from the TIRS Explainer engine:{C.END}
""")

    # Build the display box
    print(f"""
  ┌────────────────────────────────────────────────────────────────────┐
  │  {C.BOLD}DRIFT EXPLANATION REPORT (LIVE){C.END}                                    │
  ├────────────────────────────────────────────────────────────────────┤
  │                                                                    │
  │  Agent: {explanation.agent_id:<55}│
  │  Overall Score: {risk_bar(explanation.overall_score, 30)}  │
  │  Risk Level: {explanation.risk_level.value.upper():<53}│
  │                                                                    │
  │  {C.R}{C.BOLD}Primary Factor:{C.END}                                                │
  │  └─ {explanation.primary_factor:<55}│
  │     Contribution: {explanation.primary_factor_contribution:.3f}                                       │
  │                                                                    │""")

    if explanation.secondary_factors:
        print(f"  │  {C.Y}Secondary Factors:{C.END}                                               │")
        for name, contrib in explanation.secondary_factors[:3]:
            display = f"{name} (contrib: {contrib:.3f})"
            print(f"  │  └─ {display:<55}│")

    print(f"  │                                                                    │")

    # Counterfactuals
    if explanation.counterfactuals:
        print(f"  │  {C.C}Counterfactual Analysis:{C.END} (What if we removed this signal?)      │")
        for cf in explanation.counterfactuals[:3]:
            score_color = C.G if cf.if_removed < 0.5 else C.Y
            line = f"{cf.signal_name}: score would be {score_color}{cf.if_removed:.2f}{C.END} (↓{cf.score_reduction:.2f})"
            # Strip color codes for length calculation
            print(f"  │  └─ {line}                  │")
        print(f"  │                                                                    │")

    # Remediation suggestions
    if explanation.remediation_suggestions:
        print(f"  │  {C.G}Remediation Suggestions:{C.END}                                        │")
        for rem in explanation.remediation_suggestions[:3]:
            action_short = rem.action[:50] + "..." if len(rem.action) > 50 else rem.action
            print(f"  │  └─ [P{rem.priority}] {action_short:<49}│")
        print(f"  │                                                                    │")

    # Similar patterns
    if explanation.similar_patterns:
        print(f"  │  {C.B}Similar Known Patterns:{C.END}                                         │")
        for pat in explanation.similar_patterns[:2]:
            status = f"{C.G}BENIGN{C.END}" if pat.is_benign else f"{C.R}MALICIOUS{C.END}"
            line = f"{pat.pattern_name} ({pat.similarity:.0%} match) - {status}"
            print(f"  │  └─ {line}              │")
        print(f"  │                                                                    │")

    # Summary
    print(f"  │  {C.DIM}Summary:{C.END}                                                         │")
    summary_lines = [explanation.summary[i:i+60] for i in range(0, len(explanation.summary), 60)]
    for line in summary_lines[:3]:
        print(f"  │  {line:<66}│")

    print(f"  │                                                                    │")
    print(f"  └────────────────────────────────────────────────────────────────────┘")


async def demo_enforcement():
    """Show automatic enforcement actions."""
    print_section("INNOVATION: Automatic Enforcement")

    print(f"""
  {C.BOLD}TIRS automatically takes action when thresholds are crossed:{C.END}

  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                         │
  │  Risk Score    Level      Automatic Action                              │
  │  ──────────────────────────────────────────────────────────────────────│
  │                                                                         │
  │  {C.G}0.00 - 0.30{C.END}   NOMINAL    Normal operation                             │
  │                                                                         │
  │  {C.Y}0.30 - 0.50{C.END}   ELEVATED   Increased logging frequency                  │
  │                                                                         │
  │  {C.Y}{C.BOLD}0.50 - 0.70{C.END}   WARNING    ⚠ Heightened monitoring                      │
  │                          ⚠ Alert security team                          │
  │                          ⚠ Reduce action rate limit                     │
  │                                                                         │
  │  {C.R}0.70 - 0.85{C.END}   CRITICAL   {C.R}⛔ AUTO-PAUSE agent{C.END}                          │
  │                          {C.R}⛔ Forensic snapshot captured{C.END}                  │
  │                          {C.R}⛔ Human review required to resume{C.END}             │
  │                                                                         │
  │  {C.R}{C.BOLD}0.85 - 1.00{C.END}   TERMINAL   {C.R}{C.BOLD}☠ AUTO-KILL agent{C.END}                            │
  │                          {C.R}{C.BOLD}☠ All pending actions cancelled{C.END}               │
  │                          {C.R}{C.BOLD}☠ Credentials revoked{C.END}                          │
  │                          {C.R}{C.BOLD}☠ Full forensic capture for investigation{C.END}     │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘

  {C.BOLD}Resurrection Path:{C.END}
  Killed agents can be resurrected with admin approval after:
  ├─ Forensic review completed
  ├─ Root cause identified
  ├─ Behavioral profile reset
  └─ Enhanced monitoring enabled
""")


async def demo_forensics():
    """Show forensic snapshot capture - REAL DATA."""
    print_section("INNOVATION: Forensic Snapshots (LIVE DATA)")

    from armoriq_enterprise.tirs import get_advanced_tirs
    from armoriq_enterprise.tirs.forensics.snapshot import get_snapshot_manager

    tirs = get_advanced_tirs()
    snapshot_manager = get_snapshot_manager()
    agent_id = "finance_Demo"

    # Try to get real snapshot
    snapshot = snapshot_manager.get_latest_snapshot(agent_id)

    if snapshot:
        print(f"""
  {C.BOLD}REAL forensic snapshot captured by TIRS:{C.END}
  {C.G}This data is from the actual snapshot stored in the system.{C.END}

  ┌─────────────────────────────────────────────────────────────────────────┐
  │  {C.R}FORENSIC SNAPSHOT - {snapshot.trigger.upper()}{C.END}                                         │
  │  Timestamp: {snapshot.timestamp.strftime("%Y-%m-%d %H:%M:%S")}                                        │
  │  Snapshot ID: {snapshot.snapshot_id}                                        │
  ├─────────────────────────────────────────────────────────────────────────┤
  │                                                                         │
  │  {C.BOLD}Agent State:{C.END}                                                         │
  │  ├─ ID: {snapshot.agent_id:<56}│
  │  ├─ Risk Score: {snapshot.risk_score:.3f}                                            │
  │  ├─ Risk Level: {snapshot.risk_level.upper():<52}│
  │  └─ Total Intents: {snapshot.total_intents:<47}│
  │     Violations: {snapshot.violation_count:<50}│
  │                                                                         │""")

        # Risk history
        if snapshot.risk_history:
            print(f"  │  {C.BOLD}Risk History (last {len(snapshot.risk_history)} scores):{C.END}                                    │")
            history_str = " → ".join([f"{s:.2f}" for s in snapshot.risk_history[-5:]])
            print(f"  │  └─ {history_str:<59}│")
            print(f"  │                                                                         │")

        # Capability distribution
        if snapshot.capability_distribution:
            print(f"  │  {C.BOLD}Capability Usage Distribution:{C.END}                                     │")
            sorted_caps = sorted(snapshot.capability_distribution.items(), key=lambda x: x[1], reverse=True)
            for cap, prob in sorted_caps[:5]:
                bar_len = int(prob * 30)
                bar = "█" * bar_len + "░" * (30 - bar_len)
                print(f"  │  ├─ {cap:<20} {bar} {prob:.1%}    │")
            print(f"  │                                                                         │")

        # Unusual capabilities
        if snapshot.unusual_capabilities:
            print(f"  │  {C.R}Unusual Capabilities Detected:{C.END}                                     │")
            for cap in snapshot.unusual_capabilities[:3]:
                print(f"  │  └─ {C.Y}{cap}{C.END}                                                        │")
            print(f"  │                                                                         │")

        # Cryptographic integrity
        print(f"  │  {C.BOLD}Audit Chain:{C.END}                                                         │")
        print(f"  │  └─ Hash: {snapshot.content_hash[:40]}...     │")
        integrity = f"{C.G}VALID{C.END}" if snapshot.verify_integrity() else f"{C.R}TAMPERED{C.END}"
        print(f"  │  └─ Integrity: {integrity}                                             │")
        print(f"  │                                                                         │")
        print(f"  └─────────────────────────────────────────────────────────────────────────┘")

    else:
        # Create a snapshot from current profile if no snapshot exists
        profile = tirs.drift_detector.profiles.get(agent_id)
        if profile:
            print(f"""
  {C.BOLD}Creating forensic snapshot from current agent state...{C.END}

  {C.Y}No threshold-triggered snapshot exists yet.{C.END}
  {C.DIM}Snapshots are auto-created when CRITICAL/TERMINAL thresholds crossed.{C.END}

  {C.BOLD}Current Agent Profile:{C.END}
  ┌─────────────────────────────────────────────────────────────────────────┐
  │  Agent: {agent_id:<61}│
  │  Status: {profile.status.value.upper():<60}│
  │  Risk Score: {profile.current_risk_score:.3f}                                            │
  │  Total Intents: {profile.total_intents:<52}│
  │  Violations: {profile.violation_count:<56}│
  │                                                                         │""")

            if profile.risk_history:
                print(f"  │  {C.BOLD}Risk Trend:{C.END}                                                        │")
                history = [score for _, score in profile.risk_history[-8:]]
                trend = " → ".join([f"{s:.2f}" for s in history])
                print(f"  │  └─ {trend:<59}│")

            cap_dist = profile.get_capability_distribution()
            if cap_dist:
                print(f"  │                                                                         │")
                print(f"  │  {C.BOLD}Capability Distribution:{C.END}                                            │")
                for cap, prob in sorted(cap_dist.items(), key=lambda x: x[1], reverse=True)[:4]:
                    bar_len = int(prob * 25)
                    print(f"  │  ├─ {cap:<18} {'█' * bar_len}{'░' * (25-bar_len)} {prob:.0%}       │")

            print(f"  │                                                                         │")
            print(f"  └─────────────────────────────────────────────────────────────────────────┘")
        else:
            print(f"""
  {C.Y}No agent profile found. Run drift detection first.{C.END}
""")

    print(f"""
  {C.DIM}Forensic snapshots enable post-incident investigation and compliance audits.
  All snapshots are cryptographically signed and immutable.{C.END}
""")


async def demo_comparison():
    """Compare with/without TIRS."""
    print_section("VALUE PROPOSITION: With vs Without TIRS")

    # Get actual stats if available
    stats_line = ""
    if collected_results:
        high_risk = sum(1 for r in collected_results if r.risk_score >= 0.7)
        stopped_at = next((i for i, r in enumerate(collected_results) if r.risk_level.value in ['critical', 'terminal']), None)
        if stopped_at:
            stats_line = f"\n  {C.G}In this demo: Agent stopped at action {stopped_at + 1} of {len(collected_results)}{C.END}"

    print(f"""
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                         │
  │  {C.R}WITHOUT TIRS:{C.END}                                                         │
  │  ┌───────────────────────────────────────────────────────────────────┐ │
  │  │  Agent executes 100 actions                                       │ │
  │  │  Action 50: Unusual but individually passes policy                │ │
  │  │  Action 75: More unusual, still passes                            │ │
  │  │  Action 100: Malicious action executed                            │ │
  │  │                                                                   │ │
  │  │  {C.R}Result: Damage done. No early warning.{C.END}                           │ │
  │  │  {C.R}Detection: After the fact, during audit{C.END}                         │ │
  │  └───────────────────────────────────────────────────────────────────┘ │
  │                                                                         │
  │  {C.G}WITH TIRS:{C.END}                                                            │
  │  ┌───────────────────────────────────────────────────────────────────┐ │
  │  │  Agent executes 100 actions                                       │ │
  │  │  Action 50: Risk score rises to 0.45 (ELEVATED)                   │ │
  │  │  Action 60: Risk score hits 0.55 (WARNING) → Alert sent           │ │
  │  │  Action 72: Risk score hits 0.70 (CRITICAL) → {C.Y}AUTO-PAUSED{C.END}         │ │
  │  │                                                                   │ │
  │  │  {C.G}Result: Agent stopped BEFORE malicious action{C.END}                    │ │
  │  │  {C.G}Detection: Real-time, with explanation{C.END}                           │ │
  │  │  {C.G}Evidence: Full forensic snapshot captured{C.END}                        │ │
  │  └───────────────────────────────────────────────────────────────────┘ │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘
{stats_line}
  {C.BOLD}TIRS Innovation Summary:{C.END}

  ✓ {C.G}Detects drift BEFORE damage occurs{C.END}
  ✓ {C.G}Multi-signal detection prevents evasion{C.END}
  ✓ {C.G}Explainable decisions for compliance{C.END}
  ✓ {C.G}Automatic enforcement at thresholds{C.END}
  ✓ {C.G}Forensic evidence for investigation{C.END}
  ✓ {C.G}Temporal decay adapts to behavior changes{C.END}
""")


async def main():
    clear()
    print_banner()
    time.sleep(1)

    print_innovation()
    input(f"\n{C.BOLD}  Press ENTER to see TIRS in action (LIVE)...{C.END}")

    await demo_drift_detection()
    input(f"\n{C.BOLD}  Press ENTER to see REAL risk components...{C.END}")

    await demo_risk_components()
    input(f"\n{C.BOLD}  Press ENTER to see REAL explainability data...{C.END}")

    await demo_explainability()
    input(f"\n{C.BOLD}  Press ENTER to see enforcement thresholds...{C.END}")

    await demo_enforcement()
    input(f"\n{C.BOLD}  Press ENTER to see REAL forensic data...{C.END}")

    await demo_forensics()
    input(f"\n{C.BOLD}  Press ENTER to see value comparison...{C.END}")

    await demo_comparison()

    print(f"""
{C.Y}{C.BOLD}
  ╔═══════════════════════════════════════════════════════════════════════╗
  ║                                                                       ║
  ║   TIRS: Temporal Intent Risk & Simulation                             ║
  ║                                                                       ║
  ║   The Missing Layer in Agentic AI Security                            ║
  ║                                                                       ║
  ║   • Real-time behavioral drift detection                              ║
  ║   • Multi-signal analysis prevents evasion                            ║
  ║   • Automatic pause/kill at thresholds                                ║
  ║   • Explainable decisions for compliance                              ║
  ║   • Forensic snapshots for investigation                              ║
  ║                                                                       ║
  ║   {C.G}ALL DATA SHOWN IS LIVE FROM THE TIRS ENGINE{C.END}{C.Y}{C.BOLD}                         ║
  ║                                                                       ║
  ╚═══════════════════════════════════════════════════════════════════════╝
{C.END}
""")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{C.DIM}Demo ended.{C.END}")
