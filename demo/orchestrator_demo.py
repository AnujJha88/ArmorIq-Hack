#!/usr/bin/env python3
"""
Watchtower Orchestrator Demo
=========================
Full multi-agent orchestration with Watchtower verification at every handoff.

This demo shows:
1. Agent registry and capability routing
2. Pipeline planning from high-level goals
3. Watchtower verification at EVERY agent handoff
4. Shared context flowing through the pipeline
5. Policy enforcement and drift detection
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

def section(text):
    print(f"\n{C.BOLD}{C.BLUE}▶ {text}{C.END}")
    print(f"{C.BLUE}{'─'*70}{C.END}")

def risk_bar(score, width=30):
    filled = int(score * width)
    empty = width - filled
    if score < 0.3:
        color = C.GREEN
    elif score < 0.6:
        color = C.YELLOW
    else:
        color = C.RED
    return f"{color}{'█' * filled}{'░' * empty}{C.END} {score:.2f}"


# ═══════════════════════════════════════════════════════════════════════════════
# DEMO CALLBACKS
# ═══════════════════════════════════════════════════════════════════════════════

class DemoCallbacks:
    """Callbacks for visualizing orchestration."""

    def __init__(self, pause_between=True):
        self.pause_between = pause_between
        self.step_num = 0
        self.total_steps = 0

    def on_handoff(self, from_agent, to_agent, verification):
        """Called when verifying agent handoff."""
        self.step_num += 1

        print(f"\n{C.BOLD}┌{'─'*78}┐{C.END}")
        print(f"{C.BOLD}│  HANDOFF {self.step_num}: {from_agent} → {to_agent:<30}│{C.END}")
        print(f"{C.BOLD}└{'─'*78}┘{C.END}")

        # Watchtower verification
        print(f"\n{C.BLUE}▶ Watchtower Verification:{C.END}")
        if verification.token_id:
            print(f"  Token: {verification.token_id[:24]}...")
            print(f"  Hash:  {verification.plan_hash}...")
        else:
            print(f"  Token: (local policy only)")

        if verification.allowed:
            if verification.modified_payload:
                print(f"\n{C.YELLOW}  ⚠️ MODIFIED: {verification.reason}{C.END}")
                print(f"     Policy: {verification.policy_triggered}")
            else:
                print(f"\n{C.GREEN}  ✅ ALLOWED{C.END}")
        else:
            print(f"\n{C.RED}  🛑 BLOCKED: {verification.reason}{C.END}")
            print(f"     Policy: {verification.policy_triggered}")
            if verification.suggestion:
                print(f"     Suggestion: {verification.suggestion}")

        if self.pause_between:
            time.sleep(0.3)

    def on_task_start(self, task, agent):
        """Called when task execution starts."""
        print(f"\n{C.CYAN}  ⚙️ Executing: {task.name}{C.END}")
        print(f"     Agent: {agent.name} ({agent.agent_id})")
        print(f"     Capability: {task.capability}")

    def on_task_complete(self, task, result):
        """Called when task completes."""
        if result.status.value == "completed":
            print(f"{C.GREEN}     ✓ Completed{C.END}")
            if result.output:
                output_str = json.dumps(result.output, indent=2)[:100]
                print(f"     Output: {output_str}...")
        elif result.status.value == "blocked":
            print(f"{C.RED}     ✗ Blocked: {result.blocked_reason}{C.END}")
        else:
            print(f"{C.RED}     ✗ Failed: {result.error}{C.END}")

        print(f"     Risk: [{risk_bar(result.risk_score)}]")

        if self.pause_between:
            time.sleep(0.5)

    def on_blocked(self, task, verification):
        """Called when task is blocked by policy."""
        print(f"\n{C.RED}{C.BOLD}  ⚠️ POLICY VIOLATION{C.END}")
        print(f"{C.RED}     Task '{task.name}' blocked by {verification.policy_triggered}{C.END}")

    def on_pipeline_complete(self, context):
        """Called when pipeline finishes."""
        print(f"\n{C.BOLD}{'═'*80}{C.END}")
        print(f"{C.BOLD}  PIPELINE COMPLETE{C.END}")
        print(f"{'═'*80}")

        summary = context.get_summary()
        print(f"  Pipeline ID: {summary['pipeline_id']}")
        print(f"  Goal: {summary['goal']}")
        print(f"  Status: {summary['status'].upper()}")
        print(f"  Tasks: {summary['completed']}/{summary['total_tasks']} completed")
        print(f"  Blocked: {summary['blocked']} | Failed: {summary['failed']}")
        print(f"  Max Risk: [{risk_bar(summary['max_risk'])}]")
        print(f"  Watchtower Tokens: {summary['intent_tokens']}")

    def get_callbacks(self):
        return {
            "on_handoff": self.on_handoff,
            "on_task_start": self.on_task_start,
            "on_task_complete": self.on_task_complete,
            "on_blocked": self.on_blocked,
            "on_pipeline_complete": self.on_pipeline_complete
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def show_registry(orchestrator):
    """Show registered agents."""
    section("Registered Agents")

    for agent in orchestrator.registry.list_agents():
        caps = ", ".join(c.value for c in list(agent.capabilities)[:3])
        print(f"  {C.CYAN}{agent.name:<15}{C.END} ({agent.agent_id})")
        print(f"    Capabilities: {caps}...")
        print(f"    Status: {agent.status.value}")
        print()


def show_context_flow(context):
    """Show data flowing through context."""
    section("Shared Context Data")

    for key, value in context.data.items():
        value_str = json.dumps(value, indent=2) if isinstance(value, (dict, list)) else str(value)
        if len(value_str) > 80:
            value_str = value_str[:80] + "..."
        print(f"  {C.YELLOW}{key}{C.END}: {value_str}")


def main():
    no_pause = "--no-pause" in sys.argv

    clear()

    print(f"""
{C.BOLD}{C.CYAN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   Watchtower Orchestrator Demo                                                  ║
║   ─────────────────────────                                                  ║
║                                                                              ║
║   Multi-agent orchestration with Watchtower verification at every handoff      ║
║                                                                              ║
║   Features:                                                                  ║
║   • Agent Registry - Track capabilities and route tasks                     ║
║   • Pipeline Planning - Break goals into agent tasks                        ║
║   • Watchtower Handoffs - Verify EVERY agent-to-agent transfer                 ║
║   • Shared Context - Data flows between agents                              ║
║   • Drift Detection - Track cumulative risk                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.END}
""")

    # Import orchestrator
    from orchestrator import Orchestrator

    print(f"{C.GRAY}Initializing orchestrator...{C.END}")
    orchestrator = Orchestrator()

    api_key = os.getenv("WATCHTOWER_API_KEY", "")
    if api_key.startswith("ak_"):
        print(f"{C.GREEN}✓ Watchtower SDK connected (LIVE MODE){C.END}")
        print(f"{C.GRAY}  API Key: {api_key[:15]}...{api_key[-8:]}{C.END}")
    else:
        print(f"{C.YELLOW}⚠ Using local policies only{C.END}")

    def wait(msg="Press Enter to continue..."):
        if no_pause:
            time.sleep(1)
        else:
            input(f"\n{C.GRAY}{msg}{C.END}")

    wait("Press Enter to see registered agents...")

    # Show agents
    show_registry(orchestrator)

    wait("Press Enter to run Pipeline 1: Clean Hiring Flow...")

    # ═══════════════════════════════════════════════════════════════════════════
    # PIPELINE 1: Clean hiring flow
    # ═══════════════════════════════════════════════════════════════════════════
    header("PIPELINE 1: Full Hiring Pipeline (Clean)")

    callbacks = DemoCallbacks(pause_between=not no_pause)

    context = orchestrator.plan_pipeline(
        goal="Hire a Senior Python Engineer",
        parameters={
            "role": "Senior Python Engineer",
            "skills": ["Python", "AWS", "Docker"],
            "level": "L4",
            "salary": 175000,
            "interview_time": "2026-02-10 14:00",
            "i9_status": "verified"
        }
    )

    print(f"  Pipeline ID: {context.pipeline_id}")
    print(f"  Goal: {context.goal}")
    print(f"  Tasks: {context.total_tasks}")
    print(f"  Task Order: {' → '.join(t.name for t in [context.tasks[tid] for tid in context.task_order])}")

    wait("\nPress Enter to execute pipeline...")

    result = orchestrator.execute_pipeline(context.pipeline_id, callbacks.get_callbacks())

    # Show context data
    show_context_flow(result)

    wait("\nPress Enter to run Pipeline 2: With Policy Violations...")

    # ═══════════════════════════════════════════════════════════════════════════
    # PIPELINE 2: Policy violations
    # ═══════════════════════════════════════════════════════════════════════════
    header("PIPELINE 2: Hiring with Policy Violations")

    callbacks2 = DemoCallbacks(pause_between=not no_pause)

    context2 = orchestrator.plan_pipeline(
        goal="Hire quickly (with violations)",
        parameters={
            "role": "Engineer",
            "skills": ["JavaScript"],
            "level": "L4",
            "salary": 250000,  # Over cap!
            "interview_time": "2026-02-14 10:00",  # Weekend!
            "i9_status": "pending"  # Not verified!
        }
    )

    print(f"  Pipeline ID: {context2.pipeline_id}")
    print(f"  Goal: {context2.goal}")
    print(f"  Tasks: {context2.total_tasks}")
    print(f"\n{C.YELLOW}  ⚠️ This pipeline has intentional policy violations!{C.END}")

    wait("\nPress Enter to execute pipeline...")

    result2 = orchestrator.execute_pipeline(context2.pipeline_id, callbacks2.get_callbacks())

    # ═══════════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"""
{C.BOLD}{C.GREEN}
╔══════════════════════════════════════════════════════════════════════════════╗
║  DEMO COMPLETE                                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  What we demonstrated:                                                       ║
║                                                                              ║
║  1. AGENT REGISTRY                                                           ║
║     └─ 6 agents with distinct capabilities                                   ║
║     └─ Automatic routing based on task requirements                          ║
║                                                                              ║
║  2. PIPELINE PLANNING                                                        ║
║     └─ High-level goal → Task breakdown                                      ║
║     └─ Dependency management between tasks                                   ║
║                                                                              ║
║  3. WATCHTOWER HANDOFF VERIFICATION                                             ║
║     └─ Every agent-to-agent transfer verified                                ║
║     └─ Intent tokens issued for each handoff                                 ║
║     └─ Policies enforced: Salary Caps, Work-Life, I-9, PII                   ║
║                                                                              ║
║  4. SHARED CONTEXT                                                           ║
║     └─ Data flows between agents (candidates → screening → offer)            ║
║     └─ Audit trail of all actions                                            ║
║                                                                              ║
║  5. DRIFT DETECTION                                                          ║
║     └─ Cumulative risk tracked across pipeline                               ║
║     └─ Blocked steps increase agent risk score                               ║
║                                                                              ║
║  Architecture:                                                               ║
║                                                                              ║
║  ┌────────────────────────────────────────────────────────────────────────┐  ║
║  │                         ORCHESTRATOR                                   │  ║
║  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │  ║
║  │  │ Sourcer │──│Screener │──│Scheduler│──│Negotiat.│──│Onboarder│     │  ║
║  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘     │  ║
║  │       │            │            │            │            │          │  ║
║  │       ▼            ▼            ▼            ▼            ▼          │  ║
║  │  ┌─────────────────────────────────────────────────────────────┐     │  ║
║  │  │                    Watchtower Verification                      │     │  ║
║  │  │  Token → Policy Check → Drift Detection → Allow/Block       │     │  ║
║  │  └─────────────────────────────────────────────────────────────┘     │  ║
║  └────────────────────────────────────────────────────────────────────────┘  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.END}
""")


if __name__ == "__main__":
    main()
