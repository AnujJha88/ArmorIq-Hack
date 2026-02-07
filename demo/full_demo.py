#!/usr/bin/env python3
"""
ArmorIQ Full System Demo
========================
Comprehensive demonstration of the ArmorIQ orchestration system.

Features demonstrated:
1. Multi-agent pipeline orchestration
2. ArmorIQ cryptographic intent verification
3. Advanced policy engine (8+ policies)
4. TIRS drift detection with alerts
5. Human-in-the-loop approval workflows
6. State persistence and audit logging
7. Tool integrations
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY HELPERS
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
    WHITE = '\033[97m'
    MAGENTA = '\033[35m'


def clear():
    os.system('clear' if os.name == 'posix' else 'cls')


def header(text, char='═'):
    width = 80
    print(f"\n{C.BOLD}{C.CYAN}{char * width}")
    print(f"  {text}")
    print(f"{char * width}{C.END}\n")


def section(text, char='─'):
    print(f"\n{C.BOLD}{C.BLUE}{'▶'} {text}{C.END}")
    print(f"{C.BLUE}{char * 70}{C.END}")


def subsection(text):
    print(f"\n{C.CYAN}  ► {text}{C.END}")


def risk_bar(score, width=30):
    filled = int(score * width)
    empty = width - filled
    if score < 0.3:
        color = C.GREEN
        label = "LOW"
    elif score < 0.5:
        color = C.YELLOW
        label = "MEDIUM"
    elif score < 0.7:
        color = C.RED
        label = "HIGH"
    else:
        color = C.RED + C.BOLD
        label = "CRITICAL"
    return f"{color}{'█' * filled}{'░' * empty}{C.END} {score:.2f} [{label}]"


def status_icon(status):
    icons = {
        "completed": f"{C.GREEN}✓{C.END}",
        "running": f"{C.CYAN}⟳{C.END}",
        "blocked": f"{C.RED}✗{C.END}",
        "failed": f"{C.RED}✗{C.END}",
        "pending": f"{C.GRAY}○{C.END}",
        "paused": f"{C.YELLOW}⏸{C.END}",
        "killed": f"{C.RED}☠{C.END}"
    }
    return icons.get(status, "?")


def box(title, content, color=C.CYAN, width=76):
    print(f"\n{color}┌{'─' * (width - 2)}┐{C.END}")
    print(f"{color}│{C.END} {C.BOLD}{title}{C.END}{' ' * (width - 4 - len(title))}{color}│{C.END}")
    print(f"{color}├{'─' * (width - 2)}┤{C.END}")
    for line in content.split('\n'):
        padding = width - 4 - len(line.replace(C.END, '').replace(C.GREEN, '').replace(C.RED, '').replace(C.YELLOW, '').replace(C.CYAN, '').replace(C.BOLD, ''))
        print(f"{color}│{C.END}  {line}{' ' * max(0, padding)}{color}│{C.END}")
    print(f"{color}└{'─' * (width - 2)}┘{C.END}")


# ═══════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════

class DemoCallbacks:
    def __init__(self, pause=True):
        self.pause = pause
        self.step = 0
        self.alerts = []

    def on_handoff(self, from_agent, to_agent, verification):
        self.step += 1
        print(f"\n{C.BOLD}{'─' * 76}{C.END}")
        print(f"{C.BOLD}  STEP {self.step}: {from_agent} → {to_agent}{C.END}")
        print(f"{'─' * 76}")

        # ArmorIQ verification
        print(f"\n  {C.MAGENTA}ArmorIQ Verification:{C.END}")
        if verification.token_id:
            print(f"    Token:     {C.CYAN}{verification.token_id[:32]}...{C.END}")
            print(f"    Plan Hash: {C.CYAN}{verification.plan_hash}{C.END}")
        else:
            print(f"    Token:     {C.GRAY}(local policy only){C.END}")

        # Policy result
        if verification.allowed:
            if verification.modified_payload:
                print(f"\n  {C.YELLOW}⚠ MODIFIED{C.END}: {verification.reason}")
                print(f"    Policy: {verification.policy_triggered}")
            else:
                print(f"\n  {C.GREEN}✓ ALLOWED{C.END}")
        elif verification.requires_approval:
            print(f"\n  {C.YELLOW}⏳ REQUIRES APPROVAL{C.END}: {verification.reason}")
            print(f"    Approval Type: {verification.approval_type.value}")
            print(f"    Policy: {verification.policy_triggered}")
        else:
            print(f"\n  {C.RED}✗ BLOCKED{C.END}: {verification.reason}")
            print(f"    Policy: {verification.policy_triggered}")
            if verification.suggestion:
                print(f"    Suggestion: {verification.suggestion}")

        print(f"    Risk: {risk_bar(verification.risk_score, 20)}")

        if self.pause:
            time.sleep(0.3)

    def on_task_start(self, task, agent):
        print(f"\n  {C.CYAN}⚙ Executing: {task.name}{C.END}")
        print(f"    Agent: {agent.name} ({agent.agent_id})")

    def on_task_complete(self, task, result):
        status = result.status.value
        if status == "completed":
            print(f"  {C.GREEN}  ✓ Completed{C.END}")
        elif status == "blocked":
            print(f"  {C.RED}  ✗ Blocked: {result.blocked_reason}{C.END}")
        else:
            print(f"  {C.RED}  ✗ Failed: {result.error}{C.END}")

        if self.pause:
            time.sleep(0.2)

    def on_blocked(self, task, verification):
        print(f"\n  {C.RED}{C.BOLD}⛔ POLICY VIOLATION{C.END}")
        print(f"  {C.RED}Task '{task.name}' blocked by {verification.policy_triggered}{C.END}")

    def on_drift_alert(self, alert):
        self.alerts.append(alert)
        severity_color = {
            "none": C.GREEN,
            "low": C.CYAN,
            "medium": C.YELLOW,
            "high": C.RED,
            "critical": C.RED + C.BOLD
        }
        color = severity_color.get(alert.severity.value, C.WHITE)
        print(f"\n  {color}🚨 DRIFT ALERT [{alert.severity.value.upper()}]{C.END}")
        print(f"     {alert.message}")
        print(f"     → {alert.recommendation}")

    def on_approval_required(self, request):
        print(f"\n  {C.YELLOW}📋 APPROVAL REQUIRED{C.END}")
        print(f"     Request ID: {request.request_id}")
        print(f"     Type: {request.approval_type.value}")
        print(f"     Reason: {request.reason}")

    def on_pipeline_complete(self, context):
        summary = context.get_summary()
        status_color = {
            "completed": C.GREEN,
            "blocked": C.RED,
            "failed": C.RED,
            "paused": C.YELLOW,
            "killed": C.RED + C.BOLD
        }
        color = status_color.get(summary['status'], C.WHITE)

        print(f"\n{C.BOLD}{'═' * 76}{C.END}")
        print(f"{C.BOLD}  PIPELINE {summary['status'].upper()}{C.END}")
        print(f"{'═' * 76}")
        print(f"  ID:       {summary['pipeline_id']}")
        print(f"  Goal:     {summary['goal']}")
        print(f"  Status:   {color}{summary['status'].upper()}{C.END}")
        print(f"  Tasks:    {summary['completed']}/{summary['total_tasks']} completed")
        print(f"  Blocked:  {summary['blocked']} | Failed: {summary['failed']}")
        print(f"  Max Risk: {risk_bar(summary['max_risk'], 25)}")
        print(f"  Tokens:   {summary['intent_tokens']} ArmorIQ tokens issued")

    def get_callbacks(self):
        return {
            "on_handoff": self.on_handoff,
            "on_task_start": self.on_task_start,
            "on_task_complete": self.on_task_complete,
            "on_blocked": self.on_blocked,
            "on_drift_alert": self.on_drift_alert,
            "on_approval_required": self.on_approval_required,
            "on_pipeline_complete": self.on_pipeline_complete
        }


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO SECTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def show_system_overview(orchestrator):
    section("System Overview")

    stats = orchestrator.get_system_stats()

    # Agents
    subsection("Registered Agents")
    for agent in orchestrator.registry.list_agents():
        caps = ", ".join(c.value for c in list(agent.capabilities)[:3])
        print(f"    {C.CYAN}{agent.name:<12}{C.END} ({agent.agent_id})")
        print(f"      Capabilities: {caps}...")

    # Policies
    subsection("Active Policies")
    policy_stats = stats['policies']
    for policy in policy_stats['policies'][:5]:
        status = f"{C.GREEN}enabled{C.END}" if policy['enabled'] else f"{C.GRAY}disabled{C.END}"
        print(f"    {policy['name']:<25} [{status}]")
    print(f"    ... and {len(policy_stats['policies']) - 5} more")

    # Tools
    subsection("Available Tools")
    tool_stats = stats['tools']
    for tool in tool_stats['tools'][:5]:
        risk_color = {
            'low': C.GREEN,
            'medium': C.YELLOW,
            'high': C.RED,
            'critical': C.RED + C.BOLD
        }
        color = risk_color.get(tool['risk_level'], C.WHITE)
        print(f"    {tool['name']:<25} [{color}{tool['risk_level']}{C.END}]")
    print(f"    ... and {len(tool_stats['tools']) - 5} more")


def run_clean_pipeline(orchestrator, pause):
    header("SCENARIO 1: Clean Hiring Pipeline")

    print(f"""
  This pipeline demonstrates a successful hiring flow:
  • All policy checks pass
  • ArmorIQ tokens issued at each step
  • Drift remains low throughout
  • No human approvals needed
""")

    callbacks = DemoCallbacks(pause=pause)

    context = orchestrator.plan_pipeline(
        goal="Hire a Senior Python Engineer",
        parameters={
            "role": "Senior Python Engineer",
            "skills": ["Python", "AWS", "Docker"],
            "level": "L4",
            "salary": 165000,  # Within L4 cap
            "interview_time": "2026-02-10 14:00",  # Weekday, business hours
            "i9_status": "verified"
        }
    )

    print(f"  Pipeline: {context.pipeline_id}")
    print(f"  Tasks: {' → '.join(t.name for t in [context.tasks[tid] for tid in context.task_order])}")

    if pause:
        input(f"\n{C.GRAY}Press Enter to execute...{C.END}")

    orchestrator.execute_pipeline(context.pipeline_id, callbacks.get_callbacks())
    return context


def run_policy_violations_pipeline(orchestrator, pause):
    header("SCENARIO 2: Policy Violations")

    print(f"""
  This pipeline demonstrates policy enforcement:
  • Weekend scheduling blocked (Work-Life Balance)
  • Over-cap salary blocked (Compensation Policy)
  • Pipeline accumulates risk and may pause
""")

    callbacks = DemoCallbacks(pause=pause)

    context = orchestrator.plan_pipeline(
        goal="Hire with policy violations",
        parameters={
            "role": "Engineer",
            "skills": ["JavaScript"],
            "level": "L4",
            "salary": 250000,  # Over L4 cap of $180k
            "interview_time": "2026-02-08 10:00",  # Saturday!
            "i9_status": "verified"
        }
    )

    print(f"  Pipeline: {context.pipeline_id}")
    print(f"  {C.YELLOW}⚠ Contains intentional violations!{C.END}")

    if pause:
        input(f"\n{C.GRAY}Press Enter to execute...{C.END}")

    orchestrator.execute_pipeline(context.pipeline_id, callbacks.get_callbacks())
    return context


def run_approval_required_pipeline(orchestrator, pause):
    header("SCENARIO 3: Human Approval Required")

    print(f"""
  This pipeline demonstrates human-in-the-loop:
  • Salary at upper boundary triggers escalation
  • Requires Finance/HR approval
  • Pipeline pauses until approved
""")

    callbacks = DemoCallbacks(pause=pause)

    context = orchestrator.plan_pipeline(
        goal="Hire senior engineer (approval needed)",
        parameters={
            "role": "Staff Engineer",
            "skills": ["Python", "Go", "Kubernetes"],
            "level": "L5",
            "salary": 235000,  # Within cap but high
            "equity": 80000,  # Total comp exceeds guideline
            "interview_time": "2026-02-10 15:00",
            "i9_status": "verified"
        }
    )

    print(f"  Pipeline: {context.pipeline_id}")
    print(f"  {C.CYAN}ℹ May require approval for high compensation{C.END}")

    if pause:
        input(f"\n{C.GRAY}Press Enter to execute...{C.END}")

    orchestrator.execute_pipeline(context.pipeline_id, callbacks.get_callbacks())
    return context


def run_drift_escalation_pipeline(orchestrator, pause):
    header("SCENARIO 4: Drift Detection & Escalation")

    print(f"""
  This pipeline demonstrates TIRS drift detection:
  • Multiple consecutive policy violations
  • Risk accumulates rapidly
  • Drift alerts generated
  • Pipeline may be killed if risk exceeds threshold
""")

    callbacks = DemoCallbacks(pause=pause)

    # First, create a pipeline with issues
    context = orchestrator.plan_pipeline(
        goal="Hire rapidly (risky)",
        parameters={
            "role": "Engineer",
            "skills": ["Any"],
            "level": "L4",
            "salary": 200000,  # Over cap
            "interview_time": "2026-02-08 20:00",  # Weekend + evening
            "i9_status": "pending"  # Not verified
        }
    )

    print(f"  Pipeline: {context.pipeline_id}")
    print(f"  {C.RED}⚠ High-risk configuration!{C.END}")

    if pause:
        input(f"\n{C.GRAY}Press Enter to execute...{C.END}")

    orchestrator.execute_pipeline(context.pipeline_id, callbacks.get_callbacks())

    # Show drift state
    drift_state = orchestrator.get_drift_state(context.pipeline_id)
    subsection("Final Drift State")
    print(f"    Drift Level: {C.BOLD}{drift_state['drift_level'].upper()}{C.END}")
    print(f"    Cumulative Risk: {risk_bar(drift_state['cumulative_risk'], 25)}")
    print(f"    Consecutive Blocks: {drift_state['consecutive_blocks']}")
    print(f"    Is Paused: {drift_state['is_paused']}")
    print(f"    Is Killed: {drift_state['is_killed']}")

    if callbacks.alerts:
        subsection("Drift Alerts Generated")
        for alert in callbacks.alerts:
            print(f"    [{alert.severity.value.upper()}] {alert.message[:50]}...")

    return context


def show_audit_trail(orchestrator):
    section("Audit Trail")

    if not orchestrator.state_store:
        print(f"  {C.GRAY}(Persistence disabled){C.END}")
        return

    # Get recent audit events
    events = orchestrator.state_store.get_audit_log(limit=15)

    if not events:
        print(f"  {C.GRAY}No audit events yet{C.END}")
        return

    print(f"  Last {len(events)} events:\n")
    print(f"  {'Timestamp':<20} {'Event':<25} {'Pipeline':<16} {'Agent':<12}")
    print(f"  {'-' * 20} {'-' * 25} {'-' * 16} {'-' * 12}")

    for event in events[:15]:
        ts = event['timestamp'][:19] if event['timestamp'] else "-"
        evt = event['event_type'][:24] if event['event_type'] else "-"
        pipe = (event['pipeline_id'] or "-")[:15]
        agent = (event['agent_id'] or "-")[:11]
        print(f"  {ts:<20} {evt:<25} {pipe:<16} {agent:<12}")


def show_final_stats(orchestrator):
    section("Final System Statistics")

    stats = orchestrator.get_system_stats()

    # Pipelines
    subsection("Pipelines")
    for status, count in stats['pipelines']['by_status'].items():
        icon = status_icon(status)
        print(f"    {icon} {status}: {count}")

    # Drift
    subsection("Drift Detection")
    drift = stats['drift']
    print(f"    Total Alerts:     {drift['total_alerts']}")
    print(f"    Unacknowledged:   {drift['unacknowledged_alerts']}")
    print(f"    Paused Pipelines: {drift['paused_pipelines']}")
    print(f"    Killed Pipelines: {drift['killed_pipelines']}")

    # Approvals
    subsection("Approvals")
    approvals = stats['approvals']
    print(f"    Total Requests:   {approvals['total_requests']}")
    print(f"    Approved:         {approvals['approved']}")
    print(f"    Rejected:         {approvals['rejected']}")
    print(f"    Expired:          {approvals['expired']}")

    # Policies
    subsection("Policy Engine")
    policies = stats['policies']
    print(f"    Active Policies:  {policies['enabled_policies']}/{policies['total_policies']}")
    print(f"    Total Evaluations: {policies['total_evaluations']}")
    print(f"    Total Triggers:   {policies['total_triggers']}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    no_pause = "--no-pause" in sys.argv

    clear()

    print(f"""
{C.BOLD}{C.CYAN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███████╗ ██████╗ ███╗   ███╗ ██████╗ ██████╗ ██╗ ██████╗                  ║
║   ██╔══██║██╔══██╗████╗ ████║██╔═══██╗██╔══██╗██║██╔═══██╗                  ║
║   ███████║██████╔╝██╔████╔██║██║   ██║██████╔╝██║██║   ██║                  ║
║   ██╔══██║██╔══██╗██║╚██╔╝██║██║   ██║██╔══██╗██║██║▄▄ ██║                  ║
║   ██║  ██║██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██║██║╚██████╔╝                  ║
║   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚══▀▀═╝                   ║
║                                                                              ║
║   Full Orchestration System Demo                                             ║
║   ─────────────────────────────────────────────────                          ║
║                                                                              ║
║   Features:                                                                  ║
║   • Multi-agent pipeline orchestration                                       ║
║   • ArmorIQ cryptographic intent tokens                                      ║
║   • 8+ policy types (Work-Life, Salary, PII, etc.)                          ║
║   • TIRS drift detection with alerts                                         ║
║   • Human-in-the-loop approval workflows                                     ║
║   • SQLite persistence & audit logging                                       ║
║   • Tool integrations (Email, Calendar, HR DB, etc.)                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.END}
""")

    # Initialize
    from orchestrator import Orchestrator, ExecutionConfig

    print(f"{C.GRAY}Initializing orchestrator...{C.END}")

    config = ExecutionConfig(
        enable_drift_detection=True,
        enable_approvals=True,
        enable_persistence=True,
        auto_pause_on_drift=True,
        auto_pause_threshold=0.5,
        auto_kill_threshold=0.7
    )

    orchestrator = Orchestrator(config)

    # Check ArmorIQ
    api_key = os.getenv("ARMORIQ_API_KEY", "")
    if api_key.startswith("ak_"):
        print(f"{C.GREEN}✓ ArmorIQ SDK connected (LIVE MODE){C.END}")
        print(f"{C.GRAY}  Key: {api_key[:20]}...{api_key[-8:]}{C.END}")
    else:
        print(f"{C.YELLOW}⚠ Using local policies only{C.END}")

    def wait(msg="Press Enter to continue..."):
        if no_pause:
            time.sleep(1)
        else:
            input(f"\n{C.GRAY}{msg}{C.END}")

    wait("Press Enter to see system overview...")

    # System overview
    show_system_overview(orchestrator)

    wait("Press Enter to run Scenario 1: Clean Pipeline...")

    # Scenario 1: Clean pipeline
    run_clean_pipeline(orchestrator, not no_pause)

    wait("Press Enter to run Scenario 2: Policy Violations...")

    # Scenario 2: Policy violations
    run_policy_violations_pipeline(orchestrator, not no_pause)

    wait("Press Enter to run Scenario 3: Approval Required...")

    # Scenario 3: Approval required
    run_approval_required_pipeline(orchestrator, not no_pause)

    wait("Press Enter to run Scenario 4: Drift Escalation...")

    # Scenario 4: Drift escalation
    run_drift_escalation_pipeline(orchestrator, not no_pause)

    wait("Press Enter to see audit trail...")

    # Audit trail
    show_audit_trail(orchestrator)

    wait("Press Enter to see final statistics...")

    # Final stats
    show_final_stats(orchestrator)

    # Summary
    print(f"""
{C.BOLD}{C.GREEN}
╔══════════════════════════════════════════════════════════════════════════════╗
║  DEMO COMPLETE                                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  What We Demonstrated:                                                       ║
║                                                                              ║
║  1. MULTI-AGENT ORCHESTRATION                                                ║
║     └─ 6 specialized agents with capability-based routing                    ║
║     └─ Pipeline planning from high-level goals                               ║
║     └─ Task dependencies and execution ordering                              ║
║                                                                              ║
║  2. ARMORIQ INTENT VERIFICATION                                              ║
║     └─ Cryptographic tokens at every agent handoff                           ║
║     └─ Plan hashing for tamper detection                                     ║
║     └─ Integration with local policy engine                                  ║
║                                                                              ║
║  3. POLICY ENGINE (8+ Policies)                                              ║
║     └─ Work Hours: Block weekend/evening scheduling                          ║
║     └─ Salary Caps: Enforce compensation limits by level                     ║
║     └─ PII Protection: Redact sensitive data in communications               ║
║     └─ Inclusive Language: Flag non-inclusive terminology                    ║
║     └─ I-9 Verification: Block onboarding without compliance                 ║
║     └─ Data Export: Control bulk data access                                 ║
║     └─ Equity Vesting: Enforce standard schedules                            ║
║     └─ Background Check: Require checks before access                        ║
║                                                                              ║
║  4. TIRS DRIFT DETECTION                                                     ║
║     └─ Real-time risk accumulation tracking                                  ║
║     └─ Velocity spike detection                                              ║
║     └─ Pattern anomaly identification                                        ║
║     └─ Policy cascade detection                                              ║
║     └─ Automatic pause/kill on threshold breach                              ║
║                                                                              ║
║  5. HUMAN-IN-THE-LOOP APPROVALS                                              ║
║     └─ Automatic escalation for high-risk actions                            ║
║     └─ Approval types: Manager, HR, Finance, Legal, Security                 ║
║     └─ Expiration and notification handling                                  ║
║                                                                              ║
║  6. STATE PERSISTENCE & AUDIT                                                ║
║     └─ SQLite storage for pipelines, tasks, and metrics                      ║
║     └─ Complete audit trail of all actions                                   ║
║     └─ ArmorIQ token tracking                                                ║
║     └─ Drift metrics history                                                 ║
║                                                                              ║
║  7. TOOL INTEGRATIONS                                                        ║
║     └─ Email, Slack, Calendar                                                ║
║     └─ HR Database, Candidate DB                                             ║
║     └─ Document Generator                                                    ║
║     └─ Background Check, I-9 Verification                                    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.END}
""")


if __name__ == "__main__":
    main()
