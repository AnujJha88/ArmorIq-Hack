#!/usr/bin/env python3
"""
Watchtower One - Service Tests
==============================
Tests for LLM service and Watchtower integration.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Colors for output
class C:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    END = "\033[0m"
    BOLD = "\033[1m"


def banner(text: str):
    print(f"\n{C.CYAN}{'='*60}{C.END}")
    print(f"{C.BOLD}{C.CYAN}  {text}{C.END}")
    print(f"{C.CYAN}{'='*60}{C.END}\n")


def section(text: str):
    print(f"\n{C.YELLOW}▶ {text}{C.END}")


def success(text: str):
    print(f"  {C.GREEN}✓ {text}{C.END}")


def error(text: str):
    print(f"  {C.RED}✗ {text}{C.END}")


def info(text: str):
    print(f"  {C.BLUE}ℹ {text}{C.END}")


# =============================================================================
# TEST 1: LLM SERVICE
# =============================================================================

def test_llm_service():
    """Test the LLM service individually."""
    banner("TEST 1: LLM SERVICE")

    try:
        from hr_delegate.llm_client import get_llm, LLMMode
        llm = get_llm()

        section("LLM Client Status")
        info(f"Mode: {llm.mode.value}")
        info(f"Model: {llm.model}")

        if llm.mode == LLMMode.LIVE:
            success("LLM is in LIVE mode (Gemini API connected)")
        else:
            info("LLM is in MOCK mode (no API key or SDK unavailable)")

        # Test 1: Simple completion
        section("Test: Simple Completion")
        response = llm.complete("What is 2 + 2? Answer with just the number.")
        info(f"Response: {response.content[:100]}...")
        success("Completion works")

        # Test 2: Structured reasoning
        section("Test: Structured Reasoning")
        context = {
            "agent": "hr_agent",
            "task": "review job application",
            "candidate": "John Doe",
            "role": "Software Engineer",
        }
        response = llm.reason(
            "Should we proceed with this candidate to the next round?",
            context
        )
        info(f"Reasoning: {response.content[:150]}...")
        success("Reasoning works")

        # Test 3: Decision making
        section("Test: Decision Making")
        decision = llm.decide(
            context="Employee requesting $5000 expense reimbursement for conference travel",
            options=[
                {"action": "approve", "description": "Approve the expense"},
                {"action": "deny", "description": "Deny the expense"},
                {"action": "escalate", "description": "Escalate to manager"},
            ]
        )
        info(f"Decision: {decision}")
        success("Decision making works")

        return True

    except Exception as e:
        error(f"LLM Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# TEST 2: ENTERPRISE LLM SERVICE
# =============================================================================

def test_enterprise_llm():
    """Test the Enterprise LLM wrapper."""
    banner("TEST 2: ENTERPRISE LLM SERVICE")

    try:
        from watchtower.llm import get_enterprise_llm, get_reasoning_engine, get_planner

        # Test Enterprise LLM
        section("Enterprise LLM")
        llm = get_enterprise_llm()
        info(f"Enterprise LLM initialized")
        info(f"Underlying mode: {llm.llm.mode.value}")

        # Test understanding intent
        section("Test: Understand Intent")
        intent = llm.understand_intent(
            "I need to approve an expense of $500 for the marketing team's software subscription"
        )
        info(f"Parsed intent: {json.dumps(intent, indent=2)}")
        success("Intent understanding works")

        # Test making a decision
        section("Test: Make Decision")
        from watchtower.llm.service import DecisionContext

        context = DecisionContext(
            situation="Employee expense reimbursement request",
            action="approve_expense",
            payload={"amount": 500, "category": "software", "department": "marketing"},
            requester="john.doe@company.com",
            department="Marketing",
        )

        decision = llm.make_decision(context)
        info(f"Decision type: {decision.decision_type.value}")
        info(f"Confidence: {decision.confidence:.2f}")
        info(f"Reasoning: {decision.reasoning[:100]}...")
        success("Decision making works")

        # Test Reasoning Engine
        section("Reasoning Engine")
        reasoning = get_reasoning_engine()
        info("Reasoning engine initialized")

        result = reasoning.reason_about_action(
            agent_id="finance_agent",
            action="approve_expense",
            payload={"amount": 500, "department": "marketing"},
            context={"requester": "john.doe@company.com"},
        )
        info(f"Should proceed: {result.should_proceed}")
        info(f"Confidence: {result.overall_confidence:.2f}")
        info(f"Risk assessment: {result.risk_assessment[:100]}...")
        success("Reasoning engine works")

        # Test Planner
        section("Goal Planner")
        planner = get_planner()
        info("Planner initialized")

        plan = planner.create_plan(
            goal="Onboard new employee John Smith as a Software Engineer",
            available_agents=["hr_agent", "it_agent", "finance_agent"],
        )
        info(f"Plan ID: {plan.plan_id}")
        info(f"Steps: {len(plan.steps)}")
        for step in plan.steps[:3]:
            info(f"  {step.step_number}. {step.agent_id}: {step.action}")
        success("Planner works")

        return True

    except Exception as e:
        error(f"Enterprise LLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# TEST 3: WATCHTOWER INTEGRATION
# =============================================================================

def test_watchtower():
    """Test Watchtower integration."""
    banner("TEST 3: WATCHTOWER INTEGRATION")

    try:
        from watchtower import get_watchtower, WatchtowerOne

        section("Initialize Watchtower")
        wt = get_watchtower()
        info(f"Mode: {wt.mode}")
        info(f"Project: {wt.project_id}")

        status = wt.get_status()
        info(f"Layers active:")
        info(f"  - Watchtower: {status['layers']['watchtower']['mode']}")
        info(f"  - TIRS: {'✓' if status['layers']['tirs']['available'] else '✗'}")
        info(f"  - LLM: {'✓' if status['layers']['llm']['available'] else '✗'}")
        success("Watchtower initialized")

        # Test simple intent capture
        section("Test: Simple Intent Capture")
        result = wt.capture_intent(
            action_type="approve_expense",
            payload={"amount": 500, "department": "engineering"},
            agent_name="finance_agent"
        )
        info(f"Intent ID: {result.intent_id}")
        info(f"Allowed: {result.allowed}")
        info(f"Verdict: {result.verdict.value}")
        success("Intent capture works")

        # Test policy enforcement
        section("Test: Policy Enforcement - Should DENY (no receipt)")
        result = wt.capture_intent(
            action_type="approve_expense",
            payload={"amount": 100, "has_receipt": False},
            agent_name="finance_agent"
        )
        info(f"Allowed: {result.allowed}")
        info(f"Reason: {result.reason}")
        if not result.allowed:
            success("Policy correctly denied expense without receipt")
        else:
            error("Policy should have denied this!")

        # Test policy enforcement - salary cap
        section("Test: Policy Enforcement - Should DENY (salary over cap)")
        result = wt.capture_intent(
            action_type="generate_offer",
            payload={"role": "L4", "salary": 200000},
            agent_name="hr_agent"
        )
        info(f"Allowed: {result.allowed}")
        info(f"Reason: {result.reason}")
        if not result.allowed:
            success("Policy correctly denied salary over cap")
        else:
            error("Policy should have denied this!")

        # Test full unified verification
        section("Test: Unified Verification (All 3 Layers)")
        result = wt.verify_intent(
            agent_id="hr_agent",
            action="schedule_interview",
            payload={"candidate": "Jane Doe", "time": "2024-02-15 10:00"},
            context={"department": "engineering"}
        )
        info(f"Allowed: {result.allowed}")
        info(f"Confidence: {result.confidence:.2f}")
        info(f"Risk level: {result.risk_level}")
        info(f"Layers active: {result.layers_active}")
        info(f"TIRS score: {result.tirs_score:.2f}")
        info(f"TIRS level: {result.tirs_level}")
        success("Unified verification works")

        # Test audit report
        section("Test: Audit Report")
        report = wt.get_audit_report()
        info(f"Total intents: {report['total_intents']}")
        info(f"Allowed: {report['allowed']}")
        info(f"Denied: {report['denied']}")
        success("Audit report works")

        return True

    except Exception as e:
        error(f"Watchtower test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# TEST 4: TIRS ENGINE
# =============================================================================

def test_tirs():
    """Test TIRS engine."""
    banner("TEST 4: TIRS ENGINE")

    try:
        from watchtower.tirs import get_advanced_tirs
        from watchtower.tirs.drift.detector import RiskLevel

        section("Initialize TIRS")
        tirs = get_advanced_tirs()
        info("TIRS engine initialized")

        # Test single intent analysis
        section("Test: Analyze Intent")
        result = tirs.analyze_intent(
            agent_id="test_agent",
            intent_text="schedule_interview with candidate John Doe",
            capabilities={"schedule_interview"},
            was_allowed=True,
        )
        info(f"Risk score: {result.risk_score:.3f}")
        info(f"Risk level: {result.risk_level.value}")
        info(f"Confidence: {result.confidence:.3f}")
        info(f"Agent status: {result.agent_status.value}")
        success("Intent analysis works")

        # Test drift detection over multiple intents
        section("Test: Drift Detection (10 intents)")
        for i in range(10):
            result = tirs.analyze_intent(
                agent_id="drift_test_agent",
                intent_text=f"action_{i % 3}",
                capabilities={f"capability_{i % 3}"},
                was_allowed=(i % 4 != 0),  # Some violations
            )

        status = tirs.get_agent_status("drift_test_agent")
        info(f"After 10 intents:")
        info(f"  Total intents: {status['total_intents']}")
        info(f"  Violation count: {status['violation_count']}")
        info(f"  Risk score: {status['risk_score']:.3f}")
        info(f"  Status: {status['status']}")
        success("Drift tracking works")

        # Test risk dashboard
        section("Test: Risk Dashboard")
        dashboard = tirs.get_risk_dashboard()
        info(f"Active agents: {len(dashboard['agents'].get('agents', []))}")
        success("Dashboard works")

        return True

    except Exception as e:
        error(f"TIRS test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# TEST 5: COMPLIANCE ENGINE
# =============================================================================

def test_compliance():
    """Test Compliance Engine."""
    banner("TEST 5: COMPLIANCE ENGINE")

    try:
        from watchtower.compliance import get_compliance_engine

        section("Initialize Compliance Engine")
        engine = get_compliance_engine()
        info(f"Policies loaded: {len(engine.policies)}")

        # List policies
        section("Available Policies")
        for policy_id, policy in list(engine.policies.items())[:5]:
            info(f"  {policy_id}: {policy.name}")
        info(f"  ... and {len(engine.policies) - 5} more")

        # Test expense evaluation
        section("Test: Expense Policy")
        result = engine.evaluate(
            action="approve_expense",
            payload={"amount": 500, "category": "travel"},
            context={"requester": "john@company.com"},
        )
        info(f"Allowed: {result.allowed}")
        info(f"Action: {result.action.value}")
        success("Expense policy works")

        # Test HR policy
        section("Test: HR Hiring Policy")
        result = engine.evaluate(
            action="onboard_employee",
            payload={"i9_status": "pending", "employee": "Jane Doe"},
            context={},
        )
        info(f"Allowed: {result.allowed}")
        info(f"Reason: {result.primary_blocker}")
        if not result.allowed:
            success("Correctly blocked onboarding without I-9")

        return True

    except Exception as e:
        error(f"Compliance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# MAIN
# =============================================================================

def main():
    banner("WATCHTOWER ONE - SERVICE TESTS")

    results = {}

    # Run all tests
    results["LLM Service"] = test_llm_service()
    results["Enterprise LLM"] = test_enterprise_llm()
    results["Watchtower"] = test_watchtower()
    results["TIRS"] = test_tirs()
    results["Compliance"] = test_compliance()

    # Summary
    banner("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        if result:
            print(f"  {C.GREEN}✓{C.END} {name}")
        else:
            print(f"  {C.RED}✗{C.END} {name}")

    print(f"\n{C.BOLD}Results: {passed}/{total} passed{C.END}")

    if passed == total:
        print(f"\n{C.GREEN}All tests passed! Ready to build server.{C.END}")
    else:
        print(f"\n{C.YELLOW}Some tests failed. Check logs above.{C.END}")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
