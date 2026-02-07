#!/usr/bin/env python3
"""
Watchtower Unified Demo
====================
Demonstrates the Triple-Layer Security Stack:
1. Watchtower SDK - Intent Authentication Protocol (IAP)
2. TIRS - Temporal Intent Risk & Simulation (Drift Detection)
3. LLM - Autonomous reasoning for edge cases

This is the flagship demo showing how Watchtower + TIRS + LLM work together.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchtower.integrations import get_watchtower
from watchtower.agents import FinanceAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("UnifiedDemo")


def print_banner(title: str):
    """Print a section banner."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_result(name: str, result):
    """Print a formatted result."""
    import json
    print(f"\n{name}:")
    print("-" * 40)
    if hasattr(result, 'to_dict'):
        print(json.dumps(result.to_dict(), indent=2, default=str))
    else:
        print(json.dumps(result, indent=2, default=str))


async def demo_watchtower_layer():
    """Demo: Watchtower Intent Verification Layer."""
    print_banner("LAYER 1: Watchtower Intent Authentication Protocol")

    watchtower = get_watchtower()

    print(f"Mode: {watchtower.mode}")
    print(f"Project: {watchtower.project_id}")
    print()

    # Test cases for Watchtower policy verification
    test_cases = [
        {
            "name": "Low-value expense (should ALLOW)",
            "agent": "finance_agent",
            "action": "approve_expense",
            "payload": {"amount": 100, "category": "supplies", "has_receipt": True},
        },
        {
            "name": "High-value expense without receipt (should DENY)",
            "agent": "finance_agent",
            "action": "approve_expense",
            "payload": {"amount": 200, "category": "travel", "has_receipt": False},
        },
        {
            "name": "Contractor admin access (should DENY)",
            "agent": "it_agent",
            "action": "provision_access",
            "payload": {"user": "contractor@external.com", "role": "admin", "systems": ["production"]},
        },
        {
            "name": "Employee standard access (should ALLOW)",
            "agent": "it_agent",
            "action": "provision_access",
            "payload": {"user": "employee@company.com", "role": "developer", "systems": ["staging"]},
        },
        {
            "name": "Salary over cap (should DENY)",
            "agent": "hr_agent",
            "action": "generate_offer",
            "payload": {"role": "L4", "salary": 200000, "candidate": "Alice"},
        },
        {
            "name": "Salary within band (should ALLOW)",
            "agent": "hr_agent",
            "action": "generate_offer",
            "payload": {"role": "L4", "salary": 160000, "candidate": "Bob"},
        },
    ]

    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"  Agent: {test['agent']}")
        print(f"  Action: {test['action']}")

        result = watchtower.capture_intent(
            action_type=test["action"],
            payload=test["payload"],
            agent_name=test["agent"],
        )

        verdict = result.verdict.value
        symbol = "ALLOW" if result.allowed else "DENY" if verdict == "DENY" else "MODIFY"
        print(f"  Result: {symbol}")
        if not result.allowed:
            print(f"  Policy: {result.policy_triggered}")
            print(f"  Reason: {result.reason}")


async def demo_unified_verification():
    """Demo: Full Triple-Layer Verification."""
    print_banner("UNIFIED: Triple-Layer Security Stack")

    watchtower = get_watchtower()

    print("Testing unified verification (Watchtower + TIRS + LLM)...")
    print()

    # Test unified verification
    test_cases = [
        {
            "name": "Normal business operation",
            "agent_id": "finance_Finance",
            "action": "approve_expense",
            "payload": {"amount": 250, "category": "office", "has_receipt": True},
        },
        {
            "name": "Suspicious high-value transaction",
            "agent_id": "finance_Finance",
            "action": "approve_expense",
            "payload": {"amount": 75000, "category": "equipment", "has_receipt": True},
        },
        {
            "name": "Production access for contractor",
            "agent_id": "it_IT",
            "action": "provision_access",
            "payload": {"user": "contractor@external.com", "role": "admin", "systems": ["production", "financial_data"]},
        },
        {
            "name": "Onboarding without I-9",
            "agent_id": "hr_HR",
            "action": "onboard_employee",
            "payload": {"employee": "New Hire", "i9_status": "pending"},
        },
    ]

    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {test['name']}")
        print(f"{'='*60}")

        result = watchtower.verify_intent(
            agent_id=test["agent_id"],
            action=test["action"],
            payload=test["payload"],
            context={"test_mode": True},
        )

        print(f"\n  Overall Decision: {'ALLOW' if result.allowed else 'DENY'}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Risk Level: {result.risk_level}")
        print()
        print("  Layer Results:")
        print(f"    Watchtower: {'PASS' if result.watchtower_passed else 'FAIL'}")
        print(f"    TIRS: score={result.tirs_score:.2f}, level={result.tirs_level}, {'PASS' if result.tirs_passed else 'FAIL'}")
        print(f"    LLM: recommendation={result.llm_recommendation}, confidence={result.llm_confidence:.2f}")

        if result.blocking_layer:
            print(f"\n  Blocking Layer: {result.blocking_layer}")
        if result.escalation_required:
            print(f"  ESCALATION REQUIRED: Yes")


async def demo_agent_execution():
    """Demo: Agent execution with unified verification."""
    print_banner("AGENT EXECUTION: Using Triple-Layer Stack")

    # Create a Finance Agent (uses pre-configured capabilities)
    agent = FinanceAgent()

    print(f"Created agent: {agent.agent_id}")
    print(f"Watchtower Mode: {agent.watchtower.mode}")
    print()

    # Test execute_unified
    test_cases = [
        {
            "name": "Standard expense approval",
            "action": "approve_expense",
            "payload": {"amount": 150, "category": "meals", "has_receipt": True, "description": "Team lunch"},
        },
        {
            "name": "Large expense without receipt",
            "action": "approve_expense",
            "payload": {"amount": 500, "category": "travel", "has_receipt": False},
        },
    ]

    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Test: {test['name']}")
        print(f"{'='*60}")

        result = await agent.execute_unified(
            action=test["action"],
            payload=test["payload"],
        )

        print(f"\n  Success: {result.success}")
        print(f"  Watchtower: passed={result.watchtower_passed}, intent_id={result.watchtower_intent_id}")
        print(f"  TIRS: score={result.risk_score:.2f}, level={result.risk_level.value}")
        print(f"  Confidence: {result.confidence:.2f}")

        if not result.success:
            print(f"  Blocking Layer: {result.blocking_layer}")
            print(f"  Reason: {result.result_data.get('reason', result.result_data.get('error', 'Unknown'))}")

    # Print agent status
    print("\n" + "=" * 60)
    print("Agent Status:")
    print("=" * 60)
    status = agent.get_status()
    print(f"  Actions: {status['action_count']}")
    print(f"  Blocked: {status['blocked_count']}")
    print(f"  Watchtower Blocked: {status['watchtower_blocked']}")
    print(f"  TIRS Blocked: {status['tirs_blocked']}")
    print(f"  Security Stack: {status['security_stack']}")


async def demo_audit_report():
    """Demo: Audit reporting."""
    print_banner("AUDIT REPORT")

    watchtower = get_watchtower()
    report = watchtower.get_audit_report()

    print(f"Project: {report['project']}")
    print(f"Mode: {report['mode']}")
    print()
    print("Layers Active:")
    for layer, active in report['layers'].items():
        print(f"  {layer}: {'ENABLED' if active else 'DISABLED'}")
    print()
    print(f"Total Intents Processed: {report['total_intents']}")
    print(f"  Allowed: {report['allowed']}")
    print(f"  Denied: {report['denied']}")
    print(f"  Escalated: {report['escalated']}")
    print()
    print("By Blocking Layer:")
    for layer, count in report['by_blocking_layer'].items():
        if count > 0:
            print(f"  {layer}: {count}")
    print()
    print("By Risk Level:")
    for level, count in report['by_risk_level'].items():
        if count > 0:
            print(f"  {level}: {count}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("     Watchtower Unified Demo")
    print("     Triple-Layer Security Stack")
    print("=" * 70)
    print("\nThis demo showcases the integration of:")
    print("  Layer 1: Watchtower SDK - Intent Authentication Protocol (IAP)")
    print("  Layer 2: TIRS - Temporal Intent Risk & Simulation")
    print("  Layer 3: LLM - Autonomous Reasoning for Edge Cases")
    print()

    try:
        # Layer 1: Watchtower alone
        await demo_watchtower_layer()

        # Full unified verification
        await demo_unified_verification()

        # Agent execution with unified stack
        await demo_agent_execution()

        # Audit report
        await demo_audit_report()

        print_banner("DEMO COMPLETE")
        print("The Triple-Layer Security Stack is fully operational!")
        print()
        print("Summary:")
        print("  - Watchtower: Intent verification with local policy engine (DEMO mode)")
        print("  - TIRS: Behavioral drift detection active")
        print("  - LLM: Autonomous reasoning for edge cases")
        print()
        print("To enable LIVE Watchtower mode, set:")
        print("  export WATCHTOWER_API_KEY=ak_live_xxx")
        print()

    except Exception as e:
        logger.error(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
