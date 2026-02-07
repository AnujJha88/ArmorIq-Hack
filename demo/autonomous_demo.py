#!/usr/bin/env python3
"""
Watchtower Enterprise Autonomous System Demo
==========================================
Demonstrates the fully autonomous agentic system with:
- LLM-powered decision making
- Natural language understanding
- Goal decomposition
- Dynamic workflow generation
- Agent collaboration
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from watchtower.orchestrator import (
    get_gateway,
    initialize_gateway,
    get_workflow_generator,
    get_collaboration_hub,
)
from watchtower.llm import get_enterprise_llm, get_reasoning_engine, get_planner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("Demo")


def print_banner(title: str):
    """Print a section banner."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_result(name: str, result: dict):
    """Print a formatted result."""
    import json
    print(f"\n{name}:")
    print("-" * 40)
    print(json.dumps(result, indent=2, default=str))


async def demo_natural_language_processing():
    """Demo: Natural language request processing."""
    print_banner("DEMO 1: Natural Language Processing")

    gateway = await initialize_gateway()

    # Test natural language requests
    requests = [
        "Process an expense report for $500 for a team dinner",
        "Check if we can onboard a new software engineer",
        "Create a support ticket for the broken printer",
    ]

    for request in requests:
        logger.info(f"Processing: '{request}'")
        result = await gateway.process_natural_language(request)
        print_result(f"Request: {request[:40]}...", result.to_dict())


async def demo_goal_decomposition():
    """Demo: Goal decomposition into multi-agent workflow."""
    print_banner("DEMO 2: Goal Decomposition")

    gateway = await initialize_gateway()

    # High-level goal
    goal = "Onboard a new data scientist named Alice including background check, IT access, and payroll setup"

    logger.info(f"Processing goal: {goal}")

    result = await gateway.process_goal(
        goal=goal,
        context={"urgency": "normal"},
        constraints=["must complete background check before IT access"],
    )

    print_result("Goal Decomposition Result", result)


async def demo_autonomous_decision_making():
    """Demo: Autonomous decision making with reasoning."""
    print_banner("DEMO 3: Autonomous Decision Making")

    gateway = await initialize_gateway()

    # Test different scenarios with varying risk levels
    scenarios = [
        {
            "action": "approve_expense",
            "payload": {"amount": 100, "category": "supplies", "description": "Office supplies"},
            "description": "Low-value expense",
        },
        {
            "action": "approve_expense",
            "payload": {"amount": 75000, "category": "equipment", "description": "Server purchase"},
            "description": "High-value expense",
        },
        {
            "action": "provision_access",
            "payload": {"user": "contractor@external.com", "role": "admin", "systems": ["production"]},
            "description": "Admin access for contractor",
        },
    ]

    for scenario in scenarios:
        logger.info(f"Scenario: {scenario['description']}")

        # Process with autonomous reasoning
        result = await gateway.process_request(
            action=scenario["action"],
            payload=scenario["payload"],
            context={"autonomous_mode": True},
        )

        print_result(scenario["description"], {
            "success": result.success,
            "action": result.action,
            "reasoning": result.reasoning,
            "confidence": result.confidence,
            "risk_level": result.risk_level,
        })


async def demo_workflow_generation():
    """Demo: Dynamic workflow generation from natural language."""
    print_banner("DEMO 4: Dynamic Workflow Generation")

    gateway = await initialize_gateway()
    generator = get_workflow_generator()

    # Get agent capabilities
    capabilities = gateway._get_agent_capabilities()

    # Generate workflows for different goals
    goals = [
        "Handle a critical security incident affecting customer data",
        "Complete quarterly financial audit",
        "Process vendor contract renewal",
    ]

    for goal in goals:
        logger.info(f"Generating workflow for: {goal}")

        design = generator.generate(
            goal=goal,
            available_agents=capabilities,
        )

        print_result(f"Workflow: {design.name}", {
            "pattern": design.pattern.value,
            "steps": len(design.steps),
            "estimated_duration_ms": design.estimated_duration_ms,
            "estimated_risk": design.estimated_risk,
            "parallel_groups": len(design.parallel_groups),
        })


async def demo_agent_collaboration():
    """Demo: Agent collaboration and negotiation."""
    print_banner("DEMO 5: Agent Collaboration")

    gateway = await initialize_gateway()
    hub = get_collaboration_hub()

    # Test task delegation
    logger.info("Testing task delegation: Finance -> IT")

    result = await hub.delegate_task(
        from_agent="finance_Finance",
        to_agent="it_IT",
        action="provision_access",
        payload={"user": "new_accountant@company.com", "role": "finance_user"},
        context={"reason": "New hire onboarding"},
    )

    print_result("Task Delegation Result", result)

    # Test negotiation
    logger.info("Testing negotiation: Finance vs Legal on contract terms")

    negotiation = await hub.negotiate(
        participants=["finance_Finance", "legal_Legal"],
        goal="Approve vendor contract",
        initial_positions={
            "finance_Finance": {
                "max_budget": 50000,
                "payment_terms": "net_30",
                "requires_budget_approval": True,
            },
            "legal_Legal": {
                "requires_liability_cap": True,
                "requires_nda": True,
                "min_contract_duration": "1_year",
            },
        },
    )

    print_result("Negotiation Result", negotiation.to_dict())


async def demo_llm_reasoning():
    """Demo: LLM reasoning engine capabilities."""
    print_banner("DEMO 6: LLM Reasoning Engine")

    reasoning_engine = get_reasoning_engine()
    llm = get_enterprise_llm()

    # Test intent understanding
    logger.info("Testing intent understanding")

    available_actions = [
        "process_expense", "approve_expense", "create_budget",
        "provision_access", "revoke_access", "create_ticket",
    ]

    test_requests = [
        "I need to submit a receipt for $200 from last week's client lunch",
        "Can you help me get access to the production database?",
        "The coffee machine in the break room is broken again",
    ]

    for request in test_requests:
        intent = llm.understand_intent(request, available_actions)
        print_result(f"Intent: '{request[:30]}...'", {
            "primary_action": intent.get("primary_action"),
            "confidence": intent.get("confidence"),
            "extracted_parameters": intent.get("extracted_parameters"),
        })


async def demo_system_status():
    """Demo: System status and statistics."""
    print_banner("DEMO 7: System Status")

    gateway = await initialize_gateway()
    status = gateway.get_system_status()

    print_result("Gateway Status", {
        "initialized": status["gateway"]["initialized"],
        "autonomous_mode": status["gateway"]["autonomous_mode"],
        "llm_mode": status["gateway"]["llm_mode"],
        "request_count": status["gateway"]["request_count"],
        "goals_processed": status["gateway"]["goals_processed"],
    })

    print_result("Agents Status", {
        agent["agent_id"]: {
            "status": agent["status"],
            "capabilities": len(agent["capabilities"]),
            "autonomous_mode": agent.get("autonomous_mode", False),
        }
        for agent in status["agents"].values()
    })

    if status.get("collaboration"):
        print_result("Collaboration Stats", status["collaboration"])


async def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("     Watchtower Enterprise Autonomous System Demo")
    print("=" * 70)
    print("\nThis demo showcases the fully autonomous agentic system with:")
    print("  - LLM-powered decision making")
    print("  - Natural language understanding")
    print("  - Goal decomposition and planning")
    print("  - Dynamic workflow generation")
    print("  - Agent collaboration and negotiation")
    print()

    try:
        await demo_llm_reasoning()
        await demo_natural_language_processing()
        await demo_autonomous_decision_making()
        await demo_goal_decomposition()
        await demo_workflow_generation()
        await demo_agent_collaboration()
        await demo_system_status()

        print_banner("DEMO COMPLETE")
        print("All autonomous features demonstrated successfully!")

    except Exception as e:
        logger.error(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
