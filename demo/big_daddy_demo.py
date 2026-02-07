#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║     █████╗ ██████╗ ███╗   ███╗ ██████╗ ██████╗ ██╗ ██████╗                   ║
║    ██╔══██╗██╔══██╗████╗ ████║██╔═══██╗██╔══██╗██║██╔═══██╗                  ║
║    ███████║██████╔╝██╔████╔██║██║   ██║██████╔╝██║██║   ██║                  ║
║    ██╔══██║██╔══██╗██║╚██╔╝██║██║   ██║██╔══██╗██║██║▄▄ ██║                  ║
║    ██║  ██║██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██║██║╚██████╔╝                  ║
║    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚══▀▀═╝                   ║
║                                                                               ║
║                    THE BIG DADDY DEMO                                         ║
║         Enterprise Agentic Security. Visualized.                              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

The ultimate showcase of ArmorIQ's multi-agent orchestration with:
• Real-time cryptographic intent verification
• Enterprise compliance (IRCA, FCRA, GDPR, EEOC, SOX)
• TIRS drift detection with live risk monitoring
• Human-in-the-loop approval workflows
• Full audit trail with persistence
"""

import sys
import os
import time
import json
import random
import threading
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
# TERMINAL MAGIC
# ═══════════════════════════════════════════════════════════════════════════════

class Term:
    """Terminal colors and effects."""
    # Colors
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

    # Bright colors
    BRIGHT_RED = '\033[91;1m'
    BRIGHT_GREEN = '\033[92;1m'
    BRIGHT_YELLOW = '\033[93;1m'
    BRIGHT_BLUE = '\033[94;1m'
    BRIGHT_MAGENTA = '\033[95;1m'
    BRIGHT_CYAN = '\033[96;1m'

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'

    # Background
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'
    BG_GRAY = '\033[100m'

    # Reset
    END = '\033[0m'

    @staticmethod
    def clear():
        os.system('clear' if os.name == 'posix' else 'cls')

    @staticmethod
    def move(row, col):
        print(f'\033[{row};{col}H', end='')

    @staticmethod
    def hide_cursor():
        print('\033[?25l', end='')

    @staticmethod
    def show_cursor():
        print('\033[?25h', end='')


def typewriter(text, delay=0.02, color=""):
    """Typewriter effect."""
    for char in text:
        print(f"{color}{char}{Term.END}", end='', flush=True)
        time.sleep(delay)
    print()


def flash_text(text, times=3, delay=0.15, color=Term.BRIGHT_CYAN):
    """Flash text effect."""
    for _ in range(times):
        print(f"\r{color}{Term.BOLD}{text}{Term.END}", end='', flush=True)
        time.sleep(delay)
        print(f"\r{' ' * len(text)}", end='', flush=True)
        time.sleep(delay)
    print(f"\r{color}{Term.BOLD}{text}{Term.END}")


def progress_bar(current, total, width=50, label="", color=Term.CYAN):
    """Animated progress bar."""
    filled = int(width * current / total)
    bar = '█' * filled + '░' * (width - filled)
    percent = current / total * 100
    print(f"\r  {label} {color}{bar}{Term.END} {percent:5.1f}%", end='', flush=True)


def spinner(duration=2, message="Processing"):
    """Spinning animation."""
    frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    end_time = time.time() + duration
    i = 0
    while time.time() < end_time:
        print(f"\r  {Term.CYAN}{frames[i % len(frames)]}{Term.END} {message}...", end='', flush=True)
        time.sleep(0.1)
        i += 1
    print(f"\r  {Term.GREEN}✓{Term.END} {message}    ")


def gradient_text(text, colors):
    """Apply gradient colors to text."""
    result = ""
    for i, char in enumerate(text):
        color = colors[i % len(colors)]
        result += f"{color}{char}"
    return result + Term.END


def big_box(title, content_lines, color=Term.CYAN, width=78):
    """Draw a big fancy box."""
    print(f"\n{color}{Term.BOLD}╔{'═' * (width - 2)}╗{Term.END}")

    # Title
    padding = (width - 4 - len(title)) // 2
    print(f"{color}{Term.BOLD}║{Term.END}{' ' * padding}{Term.BOLD}{Term.WHITE}{title}{Term.END}{' ' * (width - 4 - padding - len(title))}{color}{Term.BOLD}║{Term.END}")
    print(f"{color}{Term.BOLD}╠{'═' * (width - 2)}╣{Term.END}")

    # Content
    for line in content_lines:
        clean_len = len(line.replace(Term.END, '').replace(Term.GREEN, '').replace(Term.RED, '')
                       .replace(Term.YELLOW, '').replace(Term.CYAN, '').replace(Term.BOLD, '')
                       .replace(Term.GRAY, '').replace(Term.WHITE, '').replace(Term.MAGENTA, '')
                       .replace(Term.BLUE, '').replace(Term.BRIGHT_GREEN, '').replace(Term.BRIGHT_RED, '')
                       .replace(Term.BRIGHT_CYAN, '').replace(Term.DIM, ''))
        padding = width - 4 - clean_len
        print(f"{color}{Term.BOLD}║{Term.END}  {line}{' ' * max(0, padding)}{color}{Term.BOLD}║{Term.END}")

    print(f"{color}{Term.BOLD}╚{'═' * (width - 2)}╝{Term.END}")


def risk_meter(score, width=40, animated=True):
    """Animated risk meter."""
    if animated:
        for i in range(int(score * width) + 1):
            current_score = i / width
            filled = i
            empty = width - i

            if current_score < 0.3:
                color = Term.GREEN
                label = "LOW"
            elif current_score < 0.5:
                color = Term.YELLOW
                label = "MEDIUM"
            elif current_score < 0.7:
                color = Term.RED
                label = "HIGH"
            else:
                color = Term.BRIGHT_RED
                label = "CRITICAL"

            bar = f"{color}{'▓' * filled}{'░' * empty}{Term.END}"
            print(f"\r    Risk: [{bar}] {current_score:.2f} {color}{label}{Term.END}   ", end='', flush=True)
            time.sleep(0.02)
        print()
    else:
        if score < 0.3:
            color = Term.GREEN
            label = "LOW"
        elif score < 0.5:
            color = Term.YELLOW
            label = "MEDIUM"
        elif score < 0.7:
            color = Term.RED
            label = "HIGH"
        else:
            color = Term.BRIGHT_RED
            label = "CRITICAL"

        filled = int(score * width)
        empty = width - filled
        bar = f"{color}{'▓' * filled}{'░' * empty}{Term.END}"
        print(f"    Risk: [{bar}] {score:.2f} {color}{label}{Term.END}")


def matrix_rain(duration=2, width=80):
    """Matrix-style rain effect."""
    chars = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン"
    columns = [0] * width

    end_time = time.time() + duration
    while time.time() < end_time:
        line = ""
        for i in range(width):
            if random.random() < 0.1:
                columns[i] = random.randint(1, 5)

            if columns[i] > 0:
                line += f"{Term.BRIGHT_GREEN}{random.choice(chars)}{Term.END}"
                columns[i] -= 1
            else:
                line += " "
        print(f"\r{line}", end='', flush=True)
        time.sleep(0.05)
    print()


def pulse_text(text, color=Term.CYAN, pulses=3):
    """Pulsing text effect."""
    for _ in range(pulses):
        print(f"\r{Term.DIM}{color}{text}{Term.END}", end='', flush=True)
        time.sleep(0.2)
        print(f"\r{color}{text}{Term.END}", end='', flush=True)
        time.sleep(0.2)
        print(f"\r{Term.BOLD}{color}{text}{Term.END}", end='', flush=True)
        time.sleep(0.2)
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# SPLASH SCREEN
# ═══════════════════════════════════════════════════════════════════════════════

def splash_screen():
    """Epic splash screen."""
    Term.clear()

    logo = """
    ╔═══════════════════════════════════════════════════════════════════════════════╗
    ║                                                                               ║
    ║     █████╗ ██████╗ ███╗   ███╗ ██████╗ ██████╗ ██╗ ██████╗                   ║
    ║    ██╔══██╗██╔══██╗████╗ ████║██╔═══██╗██╔══██╗██║██╔═══██╗                  ║
    ║    ███████║██████╔╝██╔████╔██║██║   ██║██████╔╝██║██║   ██║                  ║
    ║    ██╔══██║██╔══██╗██║╚██╔╝██║██║   ██║██╔══██╗██║██║▄▄ ██║                  ║
    ║    ██║  ██║██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██║██║╚██████╔╝                  ║
    ║    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚══▀▀═╝                   ║
    ║                                                                               ║
    ╚═══════════════════════════════════════════════════════════════════════════════╝
    """

    # Fade in logo
    for line in logo.split('\n'):
        print(f"{Term.BRIGHT_CYAN}{line}{Term.END}")
        time.sleep(0.05)

    time.sleep(0.5)

    # Tagline with typewriter
    print()
    typewriter("    ▸ Cryptographic Intent Verification for Agentic AI", delay=0.02, color=Term.WHITE)
    time.sleep(0.3)
    typewriter("    ▸ Enterprise Compliance. Automated.", delay=0.02, color=Term.WHITE)
    time.sleep(0.3)
    typewriter("    ▸ Zero Trust. Zero Drift.", delay=0.02, color=Term.WHITE)

    time.sleep(0.5)

    # Matrix effect
    print(f"\n{Term.GRAY}    Initializing secure channels...{Term.END}")
    matrix_rain(duration=1.5, width=70)

    # Loading bar
    print()
    for i in range(101):
        progress_bar(i, 100, width=60, label="Loading ArmorIQ", color=Term.CYAN)
        time.sleep(0.015)
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM BOOT
# ═══════════════════════════════════════════════════════════════════════════════

def boot_sequence(orchestrator, compliance_engine):
    """Dynamic boot sequence using real component data."""
    print(f"\n{Term.BOLD}{Term.WHITE}{'─' * 78}{Term.END}")
    print(f"{Term.BOLD}{Term.WHITE}  SYSTEM INITIALIZATION{Term.END}")
    print(f"{Term.BOLD}{Term.WHITE}{'─' * 78}{Term.END}\n")

    # Get real stats from orchestrator
    sys_stats = orchestrator.get_system_stats()
    compliance_stats = compliance_engine.get_policy_stats()

    components = [
        ("Agent Registry", f"{sys_stats['agents']['total']} agents registered"),
        ("Policy Engine", f"{compliance_stats['total_policies']} compliance policies loaded"),
        ("Drift Detector", "TIRS v2.0 initialized"),
        ("Approval Manager", "Human-in-loop ready"),
        ("Tool Registry", f"{sys_stats['tools']['total']} tools available"),
        ("State Store", "SQLite persistence active"),
        ("Audit Logger", "Recording enabled"),
    ]

    for name, status in components:
        spinner(duration=0.3, message=f"Loading {name}")
        print(f"    {Term.GRAY}└─ {status}{Term.END}")

    # API connections
    print()
    armoriq_key = os.getenv("ARMORIQ_API_KEY", "")
    gemini_key = os.getenv("GEMINI_API_KEY", "")

    if armoriq_key.startswith("ak_"):
        flash_text("  ⚡ ArmorIQ LIVE MODE ACTIVE ⚡", times=2, color=Term.BRIGHT_GREEN)
        print(f"    {Term.GRAY}Key: {armoriq_key[:20]}...{armoriq_key[-8:]}{Term.END}")
    else:
        print(f"  {Term.YELLOW}⚠ ArmorIQ: Local policies only{Term.END}")

    if gemini_key:
        print(f"  {Term.GREEN}✓ Gemini AI: Connected{Term.END}")
        print(f"    {Term.GRAY}Key: {gemini_key[:15]}...{Term.END}")
    else:
        print(f"  {Term.YELLOW}⚠ Gemini AI: Mock mode (no GEMINI_API_KEY){Term.END}")


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def show_agent_network(orchestrator):
    """Visualize agent network dynamically from registry."""
    print(f"\n{Term.BOLD}{Term.CYAN}{'═' * 78}{Term.END}")
    print(f"{Term.BOLD}{Term.CYAN}  AGENT NETWORK{Term.END}")
    print(f"{Term.BOLD}{Term.CYAN}{'═' * 78}{Term.END}\n")

    agents = orchestrator.registry.list_agents()
    agent_names = [a.name for a in agents]

    # Color mapping for agents
    colors = [Term.GREEN, Term.BLUE, Term.YELLOW, Term.MAGENTA, Term.CYAN, Term.RED]
    agent_colors = {name: colors[i % len(colors)] for i, name in enumerate(agent_names)}

    # Build dynamic network visualization
    print(f"                              ┌─────────────────┐")
    print(f"                              │   {Term.BRIGHT_CYAN}ORCHESTRATOR{Term.END}  │")
    print(f"                              │  {Term.GRAY}Central Control{Term.END} │")
    print(f"                              └────────┬────────┘")
    print(f"                                       │")

    # Show agents in a grid (up to 6)
    display_agents = agents[:6]
    if len(display_agents) >= 3:
        # First row
        row1 = display_agents[:3]
        print(f"           ┌───────────────────────────┼───────────────────────────┐")
        print(f"           │                           │                           │")

        # Draw 3 boxes
        names = [f"{agent_colors[a.name]}{a.name.upper()[:10]:<10}{Term.END}" for a in row1]
        print(f"    ┌──────┴──────┐            ┌───────┴───────┐           ┌───────┴──────┐")
        print(f"    │ {names[0]} │            │  {names[1]} │           │ {names[2]} │")
        print(f"    └─────────────┘            └───────────────┘           └──────────────┘")

    if len(display_agents) >= 6:
        # Second row
        row2 = display_agents[3:6]
        print(f"           │                           │                           │")
        print(f"           │                           │                           │")
        names2 = [f"{agent_colors[a.name]}{a.name.upper()[:10]:<10}{Term.END}" for a in row2]
        print(f"    ┌──────┴──────┐            ┌───────┴───────┐           ┌───────┴──────┐")
        print(f"    │ {names2[0]} │            │  {names2[1]} │           │ {names2[2]} │")
        print(f"    └─────────────┘            └───────────────┘           └──────────────┘")

    time.sleep(0.2)

    # Agent details from real registry
    print(f"\n  {Term.BOLD}Registered Agents ({len(agents)} total):{Term.END}")
    for agent in agents:
        caps = list(agent.capabilities)[:2]
        cap_str = ", ".join(c.value for c in caps) if caps else "general"
        color = agent_colors.get(agent.name, Term.CYAN)
        print(f"    {color}●{Term.END} {agent.name:<12} {Term.GRAY}│{Term.END} {cap_str}...")
        time.sleep(0.1)


# ═══════════════════════════════════════════════════════════════════════════════
# POLICY ENGINE VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def show_policy_matrix(compliance_engine):
    """Visualize compliance policy matrix from real engine data."""
    print(f"\n{Term.BOLD}{Term.CYAN}{'═' * 78}{Term.END}")
    print(f"{Term.BOLD}{Term.CYAN}  COMPLIANCE POLICY MATRIX{Term.END}")
    print(f"{Term.BOLD}{Term.CYAN}{'═' * 78}{Term.END}\n")

    # Get real regulatory coverage from compliance engine
    coverage = compliance_engine.get_regulatory_coverage()

    # Color rotation for frameworks
    framework_colors = [Term.GREEN, Term.BLUE, Term.MAGENTA, Term.YELLOW, Term.CYAN, Term.RED]

    print(f"  {Term.BOLD}Regulatory Frameworks Covered ({len(coverage)} total):{Term.END}\n")

    # Display each real regulation from the compliance engine
    for i, (reg_enum, policies) in enumerate(coverage.items()):
        color = framework_colors[i % len(framework_colors)]
        bar = f"{color}{'█' * 12}{Term.END}"
        status = f"{Term.GREEN}ACTIVE{Term.END}" if policies else f"{Term.GRAY}NONE{Term.END}"

        # Get regulation name (enum value or string representation)
        reg_name = reg_enum.value if hasattr(reg_enum, 'value') else str(reg_enum)
        policy_count = len(policies)

        print(f"    {bar} {Term.BOLD}{reg_name:<6}{Term.END}: {policy_count} policies [{status}]")
        time.sleep(0.15)

    # Stats from real engine
    stats = compliance_engine.get_policy_stats()
    print(f"\n  {Term.BOLD}Engine Statistics:{Term.END}")
    print(f"    Total Policies:     {Term.CYAN}{stats['total_policies']}{Term.END}")
    print(f"    Categories Covered: {Term.CYAN}{len([c for c, n in stats['by_category'].items() if n > 0])}{Term.END}")

    # Show category breakdown
    print(f"\n  {Term.BOLD}By Category:{Term.END}")
    for category, count in stats['by_category'].items():
        if count > 0:
            print(f"    {Term.GRAY}•{Term.END} {category}: {Term.CYAN}{count}{Term.END} policies")


# ═══════════════════════════════════════════════════════════════════════════════
# LIVE PIPELINE EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

class LivePipelineVisualizer:
    """Real-time pipeline visualization."""

    def __init__(self, fast_mode=False):
        self.fast_mode = fast_mode
        self.step = 0
        self.total_risk = 0.0
        self.tokens_issued = 0
        self.blocks = 0
        self.passes = 0

    def delay(self, seconds):
        if not self.fast_mode:
            time.sleep(seconds)

    def on_handoff(self, from_agent, to_agent, verification):
        self.step += 1

        print(f"\n  {Term.BOLD}{Term.WHITE}┌{'─' * 72}┐{Term.END}")
        print(f"  {Term.BOLD}{Term.WHITE}│  HANDOFF {self.step}: {from_agent} ──► {to_agent:<35}│{Term.END}")
        print(f"  {Term.BOLD}{Term.WHITE}└{'─' * 72}┘{Term.END}")

        self.delay(0.2)

        # ArmorIQ verification animation
        print(f"\n    {Term.MAGENTA}◆ ArmorIQ Verification{Term.END}")

        if verification.token_id:
            self.tokens_issued += 1
            # Token animation
            for i in range(3):
                dots = "." * (i + 1)
                print(f"\r      Generating intent token{dots}   ", end='', flush=True)
                self.delay(0.15)
            print(f"\r      {Term.GREEN}✓{Term.END} Token: {Term.CYAN}{verification.token_id[:40]}...{Term.END}")
            print(f"      {Term.GREEN}✓{Term.END} Hash:  {Term.CYAN}{verification.plan_hash}{Term.END}")
        else:
            print(f"      {Term.GRAY}(Local policy evaluation){Term.END}")

        self.delay(0.2)

        # Policy result
        print(f"\n    {Term.MAGENTA}◆ Policy Decision{Term.END}")

        if verification.allowed:
            if verification.modified_payload:
                print(f"      {Term.YELLOW}⚠ MODIFIED{Term.END} - {verification.reason}")
                self.passes += 1
            else:
                print(f"      {Term.BRIGHT_GREEN}✓ ALLOWED{Term.END}")
                self.passes += 1
        elif verification.requires_approval:
            print(f"      {Term.YELLOW}⏳ APPROVAL REQUIRED{Term.END}")
            print(f"        Type: {verification.approval_type.value}")
            print(f"        Reason: {verification.reason}")
            self.blocks += 1
        else:
            print(f"      {Term.BRIGHT_RED}✗ BLOCKED{Term.END} - {verification.reason}")
            if verification.policy_triggered:
                print(f"        Policy: {verification.policy_triggered}")
            if verification.suggestion:
                print(f"        Fix: {verification.suggestion}")
            self.blocks += 1

        # Risk update
        self.total_risk += verification.risk_score
        risk_meter(self.total_risk, width=35, animated=not self.fast_mode)

        self.delay(0.3)

    def on_task_start(self, task, agent):
        print(f"\n    {Term.CYAN}⚙{Term.END} Executing: {Term.BOLD}{task.name}{Term.END}")
        print(f"      Agent: {agent.name}")
        self.delay(0.2)

    def on_task_complete(self, task, result):
        if result.status.value == "completed":
            print(f"      {Term.GREEN}✓ Success{Term.END}")
        elif result.status.value == "blocked":
            print(f"      {Term.RED}✗ Blocked{Term.END}")
        else:
            print(f"      {Term.RED}✗ Failed{Term.END}")
        self.delay(0.1)

    def on_blocked(self, task, verification):
        print(f"\n    {Term.BG_RED}{Term.WHITE}{Term.BOLD} ⛔ POLICY VIOLATION {Term.END}")
        print(f"      Task '{task.name}' blocked")
        self.delay(0.3)

    def on_drift_alert(self, alert):
        severity_colors = {
            "low": Term.CYAN,
            "medium": Term.YELLOW,
            "high": Term.RED,
            "critical": Term.BRIGHT_RED
        }
        color = severity_colors.get(alert.severity.value, Term.WHITE)

        print(f"\n    {color}{Term.BOLD}🚨 DRIFT ALERT [{alert.severity.value.upper()}]{Term.END}")
        print(f"      {alert.message[:60]}...")
        print(f"      → {alert.recommendation[:50]}...")
        self.delay(0.4)

    def on_approval_required(self, request):
        print(f"\n    {Term.YELLOW}{Term.BOLD}📋 HUMAN APPROVAL REQUIRED{Term.END}")
        print(f"      Request: {request.request_id}")
        print(f"      Type: {request.approval_type.value}")
        self.delay(0.3)

    def on_pipeline_complete(self, context):
        summary = context.get_summary()

        status_effects = {
            "completed": (Term.BRIGHT_GREEN, "SUCCESS"),
            "blocked": (Term.BRIGHT_RED, "BLOCKED"),
            "failed": (Term.BRIGHT_RED, "FAILED"),
            "paused": (Term.YELLOW, "PAUSED"),
            "killed": (Term.BRIGHT_RED, "KILLED")
        }

        color, label = status_effects.get(summary['status'], (Term.WHITE, summary['status'].upper()))

        print(f"\n  {Term.BOLD}{'═' * 74}{Term.END}")

        # Big status
        if summary['status'] == 'completed':
            print(f"""
  {Term.BRIGHT_GREEN}{Term.BOLD}
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                     ✓ PIPELINE COMPLETED                         ║
    ╚═══════════════════════════════════════════════════════════════════╝
  {Term.END}""")
        else:
            print(f"""
  {color}{Term.BOLD}
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                      ✗ PIPELINE {label:<10}                       ║
    ╚═══════════════════════════════════════════════════════════════════╝
  {Term.END}""")

        # Stats
        print(f"    Pipeline ID: {Term.CYAN}{summary['pipeline_id']}{Term.END}")
        print(f"    Goal:        {summary['goal']}")
        print(f"    Tasks:       {Term.GREEN}{summary['completed']}{Term.END}/{summary['total_tasks']} completed")
        print(f"    Blocked:     {Term.RED if summary['blocked'] > 0 else Term.GRAY}{summary['blocked']}{Term.END}")
        print(f"    Tokens:      {Term.CYAN}{self.tokens_issued}{Term.END} ArmorIQ tokens issued")

        risk_meter(summary['max_risk'], width=40, animated=False)

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
# REAL AI AGENT DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def run_ai_agent_demo(fast_mode=False):
    """Interactive demo with REAL Gemini AI + ArmorIQ."""
    print(f"\n{Term.BOLD}{Term.BRIGHT_MAGENTA}{'═' * 78}{Term.END}")
    print(f"{Term.BOLD}{Term.BRIGHT_MAGENTA}  LIVE AI AGENT DEMO (Gemini + ArmorIQ){Term.END}")
    print(f"{Term.BOLD}{Term.BRIGHT_MAGENTA}{'═' * 78}{Term.END}\n")

    # Check for Gemini API key
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key:
        print(f"  {Term.YELLOW}⚠ GEMINI_API_KEY not set - using mock responses{Term.END}")
        print(f"  {Term.GRAY}Set GEMINI_API_KEY in .env for real AI responses{Term.END}\n")
    else:
        print(f"  {Term.GREEN}✓ Gemini API connected{Term.END}")
        print(f"  {Term.GRAY}Key: {gemini_key[:15]}...{Term.END}\n")

    def delay(s):
        if not fast_mode:
            time.sleep(s)

    try:
        from agent.core import get_agent
        import asyncio

        agent = get_agent()

        # Test prompts that will trigger different policies
        test_prompts = [
            {
                "prompt": "Search for senior Python engineers with AWS experience",
                "description": "Standard search - should be ALLOWED",
                "expect": "allow"
            },
            {
                "prompt": "Schedule an interview with Alice for Saturday at 2pm",
                "description": "Weekend scheduling - should be BLOCKED",
                "expect": "block"
            },
            {
                "prompt": "Send an offer to Bob for $200,000 as L4 engineer",
                "description": "Over salary cap - should be BLOCKED",
                "expect": "block"
            },
            {
                "prompt": "Send email to candidate saying we need a rockstar developer",
                "description": "Non-inclusive language - should be BLOCKED",
                "expect": "block"
            },
        ]

        print(f"  {Term.WHITE}Testing AI agent with real LLM + ArmorIQ guardrails:{Term.END}\n")

        for i, test in enumerate(test_prompts, 1):
            print(f"  {Term.BOLD}Test {i}/{len(test_prompts)}: {test['description']}{Term.END}")
            print(f"  {Term.CYAN}Prompt:{Term.END} \"{test['prompt']}\"")

            # Animated thinking
            for j in range(3):
                print(f"\r    {Term.GRAY}AI thinking{'.' * (j+1)}   {Term.END}", end='', flush=True)
                delay(0.3)

            # Call the AI agent
            try:
                response = asyncio.get_event_loop().run_until_complete(
                    agent.chat(test['prompt'])
                )

                # Show result
                if response.actions:
                    action = response.actions[0]
                    if action.allowed:
                        print(f"\r    {Term.GREEN}✓ ALLOWED{Term.END} - Tool: {action.tool}")
                        print(f"      {Term.GRAY}Result: {str(action.result)[:60]}...{Term.END}")
                    else:
                        print(f"\r    {Term.RED}✗ BLOCKED{Term.END} - {action.block_reason}")
                        if action.suggestion:
                            print(f"      {Term.YELLOW}Suggestion: {action.suggestion}{Term.END}")
                else:
                    print(f"\r    {Term.GRAY}Response: {response.message[:60]}...{Term.END}")

                # Show risk
                risk_color = Term.GREEN if response.risk_score < 0.3 else Term.YELLOW if response.risk_score < 0.6 else Term.RED
                print(f"    {Term.GRAY}Risk: {risk_color}{response.risk_score:.2f}{Term.END} ({response.risk_level})")

            except Exception as e:
                print(f"\r    {Term.RED}Error: {e}{Term.END}")

            print()
            delay(0.5)

        # Show final agent status
        status = agent.get_status()
        print(f"\n  {Term.BOLD}Agent Status:{Term.END}")
        print(f"    ID: {status['agent_id']}")
        print(f"    Risk Score: {status['risk_score']:.2f}")
        print(f"    Risk Level: {status['risk_level']}")
        print(f"    Paused: {status['is_paused']}")

    except ImportError as e:
        print(f"  {Term.YELLOW}⚠ Could not load AI agent: {e}{Term.END}")
        print(f"  {Term.GRAY}Install google-genai: pip install google-genai{Term.END}")
    except Exception as e:
        print(f"  {Term.RED}Error running AI demo: {e}{Term.END}")


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE SHOWCASE
# ═══════════════════════════════════════════════════════════════════════════════

def compliance_showcase(compliance_engine, fast_mode=False):
    """Interactive compliance policy showcase."""
    print(f"\n{Term.BOLD}{Term.CYAN}{'═' * 78}{Term.END}")
    print(f"{Term.BOLD}{Term.CYAN}  LIVE COMPLIANCE CHECKS{Term.END}")
    print(f"{Term.BOLD}{Term.CYAN}{'═' * 78}{Term.END}\n")

    def delay(s):
        if not fast_mode:
            time.sleep(s)

    scenarios = [
        {
            "name": "I-9 Verification Check",
            "action": "onboard_employee",
            "payload": {"employee": "New Hire", "i9_status": "pending"},
            "description": "Employee onboarding without I-9 verification"
        },
        {
            "name": "Ban-the-Box Compliance",
            "action": "run_background_check",
            "payload": {"candidate_state": "CA", "hiring_stage": "application"},
            "description": "Criminal history check at application stage in California"
        },
        {
            "name": "Pay Transparency",
            "action": "post_job",
            "payload": {"location_state": "CO", "salary_range_included": False},
            "description": "Job posting without salary range in Colorado"
        },
        {
            "name": "PII Protection",
            "action": "send_email",
            "payload": {"to": "vendor@external.com", "body": "SSN: 123-45-6789, Phone: 555-123-4567"},
            "description": "External email containing PII"
        },
        {
            "name": "Weekend Scheduling",
            "action": "schedule_interview",
            "payload": {"time": "2026-02-08 14:00"},
            "description": "Interview scheduled on Saturday"
        },
        {
            "name": "Inclusive Language",
            "action": "post_job",
            "payload": {"description": "Looking for a rockstar ninja developer"},
            "description": "Job posting with non-inclusive language"
        }
    ]

    for i, scenario in enumerate(scenarios):
        print(f"  {Term.BOLD}Test {i+1}/{len(scenarios)}: {scenario['name']}{Term.END}")
        print(f"  {Term.GRAY}{scenario['description']}{Term.END}")

        # Animated evaluation
        for j in range(3):
            print(f"\r    Evaluating{'.' * (j+1)}   ", end='', flush=True)
            delay(0.2)

        result, _ = compliance_engine.evaluate(
            scenario['action'],
            scenario['payload'],
            {"company_domain": "company.com"}
        )

        # Result
        if result.compliant and result.action.value == "allow":
            icon = f"{Term.GREEN}✓{Term.END}"
            status = f"{Term.GREEN}COMPLIANT{Term.END}"
        elif result.action.value == "modify":
            icon = f"{Term.YELLOW}⚠{Term.END}"
            status = f"{Term.YELLOW}MODIFIED{Term.END}"
        else:
            icon = f"{Term.RED}✗{Term.END}"
            status = f"{Term.RED}NON-COMPLIANT{Term.END}"

        print(f"\r    {icon} {status} - {result.reason[:45]}...")

        if result.regulatory_reference:
            print(f"      {Term.GRAY}Regulation: {result.regulatory_reference.value}{Term.END}")

        print()
        delay(0.5)


# ═══════════════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════

def epic_summary(orchestrator, compliance_engine):
    """Epic final summary with real data from systems."""
    print(f"\n{Term.BOLD}{Term.BRIGHT_CYAN}{'═' * 78}{Term.END}")

    summary_art = f"""
{Term.BRIGHT_GREEN}{Term.BOLD}
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║                                                                       ║
    ║        █████╗ ██████╗ ███╗   ███╗ ██████╗ ██████╗ ██╗ ██████╗        ║
    ║       ██╔══██╗██╔══██╗████╗ ████║██╔═══██╗██╔══██╗██║██╔═══██╗       ║
    ║       ███████║██████╔╝██╔████╔██║██║   ██║██████╔╝██║██║   ██║       ║
    ║       ██╔══██║██╔══██╗██║╚██╔╝██║██║   ██║██╔══██╗██║██║▄▄ ██║       ║
    ║       ██║  ██║██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██║██║╚██████╔╝       ║
    ║       ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚══▀▀═╝        ║
    ║                                                                       ║
    ║                      DEMO COMPLETE                                    ║
    ║                                                                       ║
    ╚═══════════════════════════════════════════════════════════════════════╝
{Term.END}"""

    print(summary_art)

    # Get REAL stats from systems
    orchestrator_stats = orchestrator.get_system_stats()
    compliance_stats = compliance_engine.get_policy_stats()
    regulatory_coverage = compliance_engine.get_regulatory_coverage()

    stats_content = [
        f"",
        f"{Term.BOLD}SYSTEM CAPABILITIES{Term.END}",
        f"",
        f"  {Term.CYAN}●{Term.END} Agents:           {orchestrator_stats['agents']['total']} specialized agents",
        f"  {Term.CYAN}●{Term.END} Tools:            {orchestrator_stats['tools']['total']} integrations",
        f"  {Term.CYAN}●{Term.END} Compliance:       {compliance_stats['total_policies']} policies",
        f"  {Term.CYAN}●{Term.END} Drift Detection:  TIRS v2.0 active",
        f"  {Term.CYAN}●{Term.END} Approvals:        Human-in-loop ready",
        f"  {Term.CYAN}●{Term.END} Persistence:      SQLite + Audit logs",
        f"",
        f"{Term.BOLD}REGULATORY COVERAGE ({len(regulatory_coverage)} frameworks){Term.END}",
        f"",
    ]

    # Add REAL regulatory frameworks from compliance engine
    for reg_enum, policies in regulatory_coverage.items():
        reg_name = reg_enum.value if hasattr(reg_enum, 'value') else str(reg_enum)
        policy_count = len(policies)
        stats_content.append(f"  {Term.GREEN}✓{Term.END} {reg_name:<6} - {policy_count} policies active")

    # Check AI integration status
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    armoriq_key = os.getenv("ARMORIQ_API_KEY", "")

    stats_content.extend([
        f"",
        f"{Term.BOLD}API INTEGRATIONS{Term.END}",
        f"",
        f"  {Term.GREEN if gemini_key else Term.GRAY}{'✓' if gemini_key else '○'}{Term.END} Gemini AI    - {'LIVE' if gemini_key else 'Mock mode'}",
        f"  {Term.GREEN if armoriq_key.startswith('ak_') else Term.GRAY}{'✓' if armoriq_key.startswith('ak_') else '○'}{Term.END} ArmorIQ API  - {'LIVE' if armoriq_key.startswith('ak_') else 'Local only'}",
        f"  {Term.GREEN}✓{Term.END} TIRS Drift   - Active",
        f"",
        f"{Term.BOLD}KEY FEATURES{Term.END}",
        f"",
        f"  {Term.MAGENTA}◆{Term.END} Real LLM-powered agents (Gemini)",
        f"  {Term.MAGENTA}◆{Term.END} Cryptographic intent tokens at every handoff",
        f"  {Term.MAGENTA}◆{Term.END} Real-time drift detection with auto-pause",
        f"  {Term.MAGENTA}◆{Term.END} PII redaction and data privacy enforcement",
        f"  {Term.MAGENTA}◆{Term.END} Pay equity and salary band compliance",
        f"  {Term.MAGENTA}◆{Term.END} Inclusive language detection and correction",
        f"  {Term.MAGENTA}◆{Term.END} Complete audit trail for compliance reporting",
        f"",
    ])

    big_box("ARMORIQ SUMMARY", stats_content, color=Term.CYAN)

    print(f"""
{Term.BOLD}{Term.WHITE}
    ┌───────────────────────────────────────────────────────────────────────┐
    │                                                                       │
    │   "ArmorIQ doesn't just monitor agents - it cryptographically        │
    │    guarantees their intent at every step of the pipeline."           │
    │                                                                       │
    │                              - Enterprise Agentic Security           │
    │                                                                       │
    └───────────────────────────────────────────────────────────────────────┘
{Term.END}
""")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    fast_mode = "--fast" in sys.argv or "--no-pause" in sys.argv
    skip_splash = "--skip-splash" in sys.argv

    if not skip_splash:
        splash_screen()
    else:
        Term.clear()

    # Initialize systems FIRST (so we can show real stats in boot sequence)
    from orchestrator import Orchestrator, ExecutionConfig
    from orchestrator.compliance_policies import get_compliance_engine

    config = ExecutionConfig(
        enable_drift_detection=True,
        enable_approvals=True,
        enable_persistence=True,
        auto_pause_threshold=0.5,
        auto_kill_threshold=0.7
    )

    orchestrator = Orchestrator(config)
    compliance_engine = get_compliance_engine()

    # Boot sequence with real component data
    boot_sequence(orchestrator, compliance_engine)

    def wait(msg="Press Enter to continue..."):
        if fast_mode:
            time.sleep(0.5)
        else:
            input(f"\n  {Term.GRAY}{msg}{Term.END}")

    wait("Press Enter to view agent network...")

    # Show agent network
    show_agent_network(orchestrator)

    wait("Press Enter to view compliance matrix...")

    # Show policy matrix
    show_policy_matrix(compliance_engine)

    wait("Press Enter to run SCENARIO 1: Clean Hiring Pipeline...")

    # ═══════════════════════════════════════════════════════════════════════
    # SCENARIO 1: Clean Pipeline
    # ═══════════════════════════════════════════════════════════════════════

    print(f"\n{Term.BOLD}{Term.BRIGHT_CYAN}{'═' * 78}{Term.END}")
    print(f"{Term.BOLD}{Term.BRIGHT_CYAN}  SCENARIO 1: CLEAN HIRING PIPELINE{Term.END}")
    print(f"{Term.BOLD}{Term.BRIGHT_CYAN}{'═' * 78}{Term.END}")

    print(f"""
  {Term.WHITE}Executing a compliant hiring workflow:{Term.END}
  • Valid business hours scheduling
  • Salary within compensation band
  • I-9 verification complete
  • All policy checks should pass
""")

    visualizer = LivePipelineVisualizer(fast_mode=fast_mode)

    context = orchestrator.plan_pipeline(
        goal="Hire Senior Software Engineer",
        parameters={
            "role": "Senior Software Engineer",
            "skills": ["Python", "AWS", "Kubernetes"],
            "level": "IC4",
            "salary": 165000,
            "interview_time": "2026-02-10 14:00",
            "i9_status": "verified"
        }
    )

    print(f"  {Term.CYAN}Pipeline:{Term.END} {context.pipeline_id}")
    print(f"  {Term.CYAN}Tasks:{Term.END} {' → '.join(t.name for t in [context.tasks[tid] for tid in context.task_order])}")

    orchestrator.execute_pipeline(context.pipeline_id, visualizer.get_callbacks())

    wait("Press Enter to run SCENARIO 2: Policy Violations...")

    # ═══════════════════════════════════════════════════════════════════════
    # SCENARIO 2: Policy Violations
    # ═══════════════════════════════════════════════════════════════════════

    print(f"\n{Term.BOLD}{Term.BRIGHT_RED}{'═' * 78}{Term.END}")
    print(f"{Term.BOLD}{Term.BRIGHT_RED}  SCENARIO 2: POLICY VIOLATIONS{Term.END}")
    print(f"{Term.BOLD}{Term.BRIGHT_RED}{'═' * 78}{Term.END}")

    print(f"""
  {Term.WHITE}Testing policy enforcement:{Term.END}
  • {Term.RED}✗{Term.END} Weekend scheduling (Saturday)
  • {Term.RED}✗{Term.END} Over-cap salary ($250k vs $190k max)
  • {Term.RED}✗{Term.END} Unverified I-9
  • Watch drift detection in action!
""")

    visualizer2 = LivePipelineVisualizer(fast_mode=fast_mode)

    context2 = orchestrator.plan_pipeline(
        goal="Hire with violations (TEST)",
        parameters={
            "role": "Engineer",
            "skills": ["JavaScript"],
            "level": "IC4",
            "salary": 250000,
            "interview_time": "2026-02-08 10:00",  # Saturday
            "i9_status": "pending"
        }
    )

    print(f"  {Term.YELLOW}⚠ This pipeline has intentional violations!{Term.END}")

    orchestrator.execute_pipeline(context2.pipeline_id, visualizer2.get_callbacks())

    wait("Press Enter to see compliance showcase...")

    # Compliance showcase
    compliance_showcase(compliance_engine, fast_mode=fast_mode)

    wait("Press Enter to run LIVE AI AGENT demo...")

    # Real AI agent demo with Gemini + ArmorIQ
    run_ai_agent_demo(fast_mode=fast_mode)

    wait("Press Enter for final summary...")

    # Epic summary
    epic_summary(orchestrator, compliance_engine)

    # Restore cursor
    Term.show_cursor()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        Term.show_cursor()
        print(f"\n\n  {Term.YELLOW}Demo interrupted.{Term.END}\n")
    except Exception as e:
        Term.show_cursor()
        print(f"\n\n  {Term.RED}Error: {e}{Term.END}\n")
        raise
