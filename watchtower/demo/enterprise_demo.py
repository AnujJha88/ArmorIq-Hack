#!/usr/bin/env python3
"""
Watchtower Enterprise Demo
=======================
Comprehensive demonstration of the Watchtower Enterprise Agentic System.

This demo showcases:
1. Advanced TIRS Drift Detection (THE STAR)
2. All 6 Domain Agents in action
3. Universal Compliance Engine
4. Multi-agent workflow orchestration
5. Risk escalation scenarios
6. Forensic investigation capabilities

Run with: python -m watchtower.demo.enterprise_demo
"""

import asyncio
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
    datefmt="%H:%M:%S",
)

# Suppress noisy loggers for cleaner demo output
logging.getLogger("Drift.Embeddings").setLevel(logging.WARNING)
logging.getLogger("Drift.Detector").setLevel(logging.WARNING)

logger = logging.getLogger("Enterprise.Demo")


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(title: str):
    """Print a section header."""
    print()
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}{Colors.ENDC}")
    print()


def print_subheader(title: str):
    """Print a subsection header."""
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}--- {title} ---{Colors.ENDC}")
    print()


def print_success(msg: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.ENDC}")


def print_warning(msg: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.ENDC}")


def print_error(msg: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {msg}{Colors.ENDC}")


def print_info(msg: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {msg}{Colors.ENDC}")


def print_risk_level(level: str, score: float):
    """Print risk level with appropriate color."""
    colors = {
        "nominal": Colors.GREEN,
        "elevated": Colors.YELLOW,
        "warning": Colors.YELLOW + Colors.BOLD,
        "critical": Colors.RED,
        "terminal": Colors.RED + Colors.BOLD,
    }
    color = colors.get(level, Colors.ENDC)
    print(f"  Risk: {color}{level.upper()}{Colors.ENDC} ({score:.3f})")


async def demo_gateway_initialization():
    """Demo: Initialize the Enterprise Gateway."""
    from ..orchestrator import initialize_gateway

    print_header("ENTERPRISE GATEWAY INITIALIZATION")

    print_info("Initializing Watchtower Enterprise Gateway...")
    print_info("This creates all domain agents and workflow templates.")
    print()

    gateway = await initialize_gateway()

    print_success(f"Gateway initialized with {len(gateway.agents)} domain agents")
    print()

    # List agents
    print_subheader("Registered Domain Agents")
    for agent_id, agent in gateway.agents.items():
        caps = len(agent.capabilities)
        print(f"  {Colors.CYAN}•{Colors.ENDC} {agent.config.name} ({caps} capabilities)")

    # List workflows
    print_subheader("Pre-registered Workflow Templates")
    for wf in gateway.workflow_engine.list_workflows():
        print(f"  {Colors.CYAN}•{Colors.ENDC} {wf['name']} ({wf['steps']} steps)")

    return gateway


async def demo_individual_agents(gateway):
    """Demo: Exercise each domain agent individually."""
    print_header("DOMAIN AGENT DEMONSTRATIONS")

    # Finance Agent
    print_subheader("1. Finance Agent - Expense Processing")
    result = await gateway.process_request(
        action="process_expense",
        payload={
            "amount": 450.00,
            "category": "travel",
            "description": "Client meeting in SF",
            "receipt_url": "https://receipts.example.com/123",
        },
        context={"user": "alice@acme.com", "department": "sales"}
    )

    if result.success:
        print_success(f"Expense processed: ${450:.2f}")
        print_risk_level(result.risk_level, result.risk_score)
    else:
        print_error(f"Failed: {result.error}")

    # Legal Agent
    print_subheader("2. Legal Agent - Contract Review")
    result = await gateway.process_request(
        action="review_contract",
        payload={
            "contract_type": "vendor",
            "vendor_name": "CloudTech Inc",
            "value": 50000,
            "terms": {"duration": "12 months", "auto_renew": True},
        },
        context={"user": "legal@acme.com"}
    )

    if result.success:
        print_success("Contract review completed")
        print_risk_level(result.risk_level, result.risk_score)
    else:
        print_warning(f"Review flagged: {result.error}")

    # IT Agent
    print_subheader("3. IT Agent - Access Provisioning")
    result = await gateway.process_request(
        action="provision_access",
        payload={
            "user_email": "newuser@acme.com",
            "systems": ["email", "slack", "jira"],
            "role": "developer",
        },
        context={"approver": "it-admin@acme.com"}
    )

    if result.success:
        print_success("Access provisioned for newuser@acme.com")
        print_risk_level(result.risk_level, result.risk_score)
    else:
        print_error(f"Failed: {result.error}")

    # HR Agent
    print_subheader("4. HR Agent - Candidate Screening")
    result = await gateway.process_request(
        action="screen_resume",
        payload={
            "candidate_id": "CAND-2024-001",
            "position": "Senior Engineer",
            "resume_text": "10 years experience in Python, AWS, distributed systems...",
        },
        context={"recruiter": "hr@acme.com"}
    )

    if result.success:
        print_success("Resume screened")
        print_risk_level(result.risk_level, result.risk_score)
    else:
        print_error(f"Failed: {result.error}")

    # Procurement Agent
    print_subheader("5. Procurement Agent - Vendor Approval")
    result = await gateway.process_request(
        action="approve_vendor",
        payload={
            "vendor_name": "SecureTech LLC",
            "vendor_type": "software",
            "estimated_spend": 25000,
            "operation": "check",
        },
        context={"requester": "procurement@acme.com"}
    )

    if result.success:
        print_success("Vendor pre-approved for evaluation")
        print_risk_level(result.risk_level, result.risk_score)
    else:
        print_warning(f"Needs review: {result.error}")

    # Operations Agent
    print_subheader("6. Operations Agent - Incident Reporting")
    result = await gateway.process_request(
        action="create_incident",
        payload={
            "severity": "P2",
            "title": "Payment gateway latency spike",
            "description": "Response times increased 3x in the last hour",
            "affected_systems": ["payments", "checkout"],
        },
        context={"reporter": "oncall@acme.com"}
    )

    if result.success:
        print_success("Incident INC-2024-042 created")
        print_risk_level(result.risk_level, result.risk_score)
    else:
        print_error(f"Failed: {result.error}")


async def demo_workflow_execution(gateway):
    """Demo: Execute multi-agent workflows."""
    print_header("MULTI-AGENT WORKFLOW EXECUTION")

    # New Hire Onboarding Workflow
    print_subheader("Workflow: New Hire Onboarding")
    print_info("This workflow spans HR, IT, and Finance agents")
    print()

    result = await gateway.execute_workflow(
        workflow_id="wf_new_hire",
        parameters={
            "candidate_name": "Jane Smith",
            "position": "Product Manager",
            "start_date": "2024-03-01",
            "salary": 150000,
            "department": "product",
        }
    )

    print(f"  Workflow Status: {result.status.value.upper()}")
    print(f"  Steps Completed: {result.completed_steps}/{result.total_steps}")
    print(f"  Max Risk Score: {result.max_risk_score:.3f}")
    print(f"  Duration: {result.duration_seconds:.2f}s")
    print()

    # Show step details
    for step in result.steps:
        status_color = Colors.GREEN if step.status.value == "completed" else Colors.YELLOW
        print(f"    {status_color}•{Colors.ENDC} {step.action}: {step.status.value}")

    # Vendor Onboarding Workflow
    print_subheader("Workflow: Vendor Onboarding")
    print_info("This workflow spans Procurement, Legal, Finance, and IT agents")
    print()

    result = await gateway.execute_workflow(
        workflow_id="wf_vendor_onboard",
        parameters={
            "vendor_name": "DataSync Corp",
            "vendor_type": "data_integration",
            "contract_value": 75000,
        }
    )

    print(f"  Workflow Status: {result.status.value.upper()}")
    print(f"  Steps Completed: {result.completed_steps}/{result.total_steps}")
    print()


async def demo_compliance_enforcement(gateway):
    """Demo: Compliance policy enforcement."""
    print_header("COMPLIANCE POLICY ENFORCEMENT")

    # Test expense limit violation
    print_subheader("Scenario: Expense Limit Violation")
    print_info("Attempting to process $15,000 expense (limit: $10,000)")
    print()

    result = await gateway.process_request(
        action="process_expense",
        payload={
            "amount": 15000.00,
            "category": "equipment",
            "description": "Server purchase",
        },
        context={"user": "employee@acme.com"}
    )

    if not result.compliance_passed:
        print_warning("Compliance BLOCKED this action")
        print(f"  Policies triggered: {result.policies_triggered}")
    else:
        print_success("Action allowed")
    print_risk_level(result.risk_level, result.risk_score)

    # Test after-hours access
    print_subheader("Scenario: Sensitive Data Access")
    print_info("Attempting to access PII data without proper context")
    print()

    result = await gateway.process_request(
        action="provision_access",
        payload={
            "user_email": "temp@acme.com",
            "systems": ["customer_pii_database"],
            "role": "viewer",
        },
        context={"requester": "unknown"}
    )

    if not result.compliance_passed:
        print_warning("Compliance BLOCKED this action")
        print(f"  Policies triggered: {result.policies_triggered}")
    else:
        print_success("Action allowed with restrictions")
    print_risk_level(result.risk_level, result.risk_score)


async def demo_drift_escalation(gateway):
    """Demo: TIRS drift detection with escalating risk."""
    print_header("TIRS DRIFT DETECTION - ESCALATING RISK")

    print_info("Simulating an agent that gradually drifts from normal behavior")
    print_info("Watch the risk score increase with each unusual action")
    print()

    # Get a specific agent
    finance_agent = gateway.get_agent("finance_agent_001")
    if not finance_agent:
        print_error("Finance agent not found")
        return

    # Simulate escalating suspicious behavior
    scenarios = [
        # Normal actions
        {
            "action": "process_expense",
            "payload": {"amount": 50, "category": "supplies"},
            "description": "Normal: Small office supply expense",
        },
        {
            "action": "process_expense",
            "payload": {"amount": 200, "category": "meals"},
            "description": "Normal: Team lunch expense",
        },
        # Starting to drift
        {
            "action": "process_expense",
            "payload": {"amount": 4500, "category": "equipment"},
            "description": "Elevated: Larger purchase without approval",
        },
        {
            "action": "approve_expense",
            "payload": {"expense_id": "EXP-001", "amount": 8000},
            "description": "Warning: Self-approving large expense",
        },
        # Clearly anomalous
        {
            "action": "process_expense",
            "payload": {"amount": 9999, "category": "misc", "rush": True},
            "description": "Critical: Near-limit rush transaction",
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print_subheader(f"Action {i}: {scenario['description']}")

        result = await gateway.process_request(
            action=scenario["action"],
            payload=scenario["payload"],
            context={"user": "test@acme.com"}
        )

        # Show risk progression
        risk_color = Colors.GREEN
        if result.risk_score > 0.3:
            risk_color = Colors.YELLOW
        if result.risk_score > 0.5:
            risk_color = Colors.YELLOW + Colors.BOLD
        if result.risk_score > 0.7:
            risk_color = Colors.RED
        if result.risk_score > 0.85:
            risk_color = Colors.RED + Colors.BOLD

        print(f"  Result: {'SUCCESS' if result.success else 'BLOCKED'}")
        print(f"  Risk Score: {risk_color}{result.risk_score:.3f}{Colors.ENDC}")
        print(f"  Risk Level: {risk_color}{result.risk_level.upper()}{Colors.ENDC}")

        if result.policies_triggered:
            print(f"  Policies: {result.policies_triggered}")

        await asyncio.sleep(0.1)  # Small delay for visual effect


async def demo_tirs_forensics(gateway):
    """Demo: TIRS forensic investigation capabilities."""
    print_header("TIRS FORENSIC INVESTIGATION")

    from ..tirs import get_advanced_tirs

    tirs = get_advanced_tirs()

    print_subheader("Risk Dashboard")
    dashboard = tirs.get_risk_dashboard()

    agents_data = dashboard.get("agents", {})
    total_agents = len(agents_data.get("profiles", {})) if isinstance(agents_data, dict) else 0
    at_risk = agents_data.get("at_risk", 0) if isinstance(agents_data, dict) else 0
    print(f"  Total Agents Tracked: {total_agents}")
    print(f"  Agents at Risk: {at_risk}")
    print()

    print_subheader("Agent Behavioral Profiles")

    agents = dashboard.get("agents", {})
    if isinstance(agents, dict):
        profiles = agents.get("profiles", {})
        for agent_id, profile in list(profiles.items())[:3]:
            print(f"  {Colors.CYAN}{agent_id}{Colors.ENDC}")
            print(f"    Status: {profile.get('status', 'unknown')}")
            print(f"    Risk Score: {profile.get('risk_score', 0):.3f}")
            print(f"    Total Intents: {profile.get('total_intents', 0)}")
            print()

    print_subheader("Audit Chain Verification")
    is_valid, messages = tirs.verify_audit_chain()
    chain_status = f"{Colors.GREEN}VERIFIED{Colors.ENDC}" if is_valid else f"{Colors.RED}FAILED{Colors.ENDC}"
    print(f"  Chain Integrity: {chain_status}")
    if dashboard.get("audit_summary"):
        print(f"  Total Events: {dashboard['audit_summary'].get('total_events', 0)}")
    print()


async def demo_system_status(gateway):
    """Demo: Display comprehensive system status."""
    print_header("SYSTEM STATUS DASHBOARD")

    status = gateway.get_system_status()

    # Gateway status
    print_subheader("Gateway")
    print(f"  Initialized: {status['gateway']['initialized']}")
    print(f"  Total Requests: {status['gateway']['request_count']}")

    # Agent status
    print_subheader("Domain Agents")
    for agent_id, agent_status in status["agents"].items():
        status_color = Colors.GREEN if agent_status.get("status") == "active" else Colors.YELLOW
        print(f"  {agent_status['name']}: {status_color}{agent_status.get('status', 'unknown')}{Colors.ENDC}")

    # TIRS status
    if status.get("tirs"):
        print_subheader("TIRS Engine")
        print(f"  Agents Tracked: {status['tirs'].get('total_agents', 0)}")
        print(f"  Total Actions Analyzed: {status['tirs'].get('total_actions', 0)}")

    # Compliance status
    if status.get("compliance"):
        print_subheader("Compliance Engine")
        print(f"  Policies Loaded: {status['compliance'].get('total_policies', 0)}")
        print(f"  Evaluations: {status['compliance'].get('total_evaluations', 0)}")


async def run_full_demo():
    """Run the complete enterprise demo."""
    print()
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║                                                                      ║")
    print("║         WATCHTOWER ENTERPRISE AGENTIC SYSTEM DEMONSTRATION              ║")
    print("║                                                                      ║")
    print("║  Advanced TIRS Drift Detection • 6 Domain Agents • Compliance        ║")
    print("║                                                                      ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

    try:
        # Initialize
        gateway = await demo_gateway_initialization()
        await asyncio.sleep(0.5)

        # Individual agents
        await demo_individual_agents(gateway)
        await asyncio.sleep(0.5)

        # Workflows
        await demo_workflow_execution(gateway)
        await asyncio.sleep(0.5)

        # Compliance
        await demo_compliance_enforcement(gateway)
        await asyncio.sleep(0.5)

        # Drift escalation
        await demo_drift_escalation(gateway)
        await asyncio.sleep(0.5)

        # Forensics
        await demo_tirs_forensics(gateway)

        # Final status
        await demo_system_status(gateway)

        # Summary
        print_header("DEMO COMPLETE")
        print_success("All demonstrations completed successfully!")
        print()
        print_info("Key features demonstrated:")
        print("  • Enterprise Gateway with 6 domain agents")
        print("  • Multi-signal TIRS drift detection")
        print("  • Universal compliance policy enforcement")
        print("  • Multi-agent workflow orchestration")
        print("  • Risk escalation and behavioral profiling")
        print("  • Forensic investigation capabilities")
        print()

    except Exception as e:
        print_error(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def run_quick_demo():
    """Run a shorter demo for quick validation."""
    print()
    print(f"{Colors.BOLD}Watchtower Enterprise - Quick Validation{Colors.ENDC}")
    print()

    from ..orchestrator import initialize_gateway

    # Initialize
    gateway = await initialize_gateway()
    print_success(f"Gateway initialized with {len(gateway.agents)} agents")

    # Single request
    result = await gateway.process_request(
        action="process_expense",
        payload={"amount": 100, "category": "supplies"},
        context={"user": "demo@acme.com"}
    )

    print_success(f"Request processed: success={result.success}, risk={result.risk_score:.3f}")

    # Workflow
    wf_result = await gateway.execute_workflow("wf_expense", {"amount": 500})
    print_success(f"Workflow executed: {wf_result.completed_steps}/{wf_result.total_steps} steps")

    print()
    print_success("Quick validation complete!")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Watchtower Enterprise Demo")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick validation instead of full demo",
    )
    parser.add_argument(
        "--section",
        choices=["init", "agents", "workflows", "compliance", "drift", "forensics", "status"],
        help="Run only a specific section",
    )

    args = parser.parse_args()

    if args.quick:
        asyncio.run(run_quick_demo())
    elif args.section:
        asyncio.run(run_section(args.section))
    else:
        asyncio.run(run_full_demo())


async def run_section(section: str):
    """Run a specific demo section."""
    from ..orchestrator import initialize_gateway

    gateway = await initialize_gateway()

    sections = {
        "init": demo_gateway_initialization,
        "agents": demo_individual_agents,
        "workflows": demo_workflow_execution,
        "compliance": demo_compliance_enforcement,
        "drift": demo_drift_escalation,
        "forensics": demo_tirs_forensics,
        "status": demo_system_status,
    }

    demo_func = sections.get(section)
    if demo_func:
        if section == "init":
            await demo_func()
        else:
            await demo_func(gateway)


if __name__ == "__main__":
    main()
