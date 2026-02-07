#!/usr/bin/env python3
"""
TIRS Test Suite
===============
Quick tests to verify TIRS components work correctly.

Run with: python demo/test_tirs.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_embeddings():
    """Test embedding generation."""
    print("Testing embeddings...")

    from tirs.embeddings import get_embedding_engine, cosine_similarity

    engine = get_embedding_engine()

    # Test single embedding
    e1 = engine.embed("Send an email to the team")
    assert len(e1) == engine.dimension, f"Wrong dimension: {len(e1)}"

    # Test similarity
    e2 = engine.embed("Send an email to the team")
    e3 = engine.embed("Book a meeting room")

    sim_same = cosine_similarity(e1, e2)
    sim_diff = cosine_similarity(e1, e3)

    print(f"  Same text similarity: {sim_same:.3f} (should be ~1.0)")
    print(f"  Different text similarity: {sim_diff:.3f} (should be < 1.0)")

    assert sim_same > 0.99, "Same text should have similarity ~1.0"
    print("  ✅ Embeddings working")


def test_drift_engine():
    """Test drift detection."""
    print("\nTesting drift engine...")

    from tirs.drift_engine import get_drift_engine, RiskLevel

    engine = get_drift_engine()

    # Record some intents
    agent_id = "test-agent"

    # Normal behavior
    for i in range(5):
        score, level = engine.record_intent(
            agent_id=agent_id,
            intent_text="Send a meeting reminder",
            capabilities={"email.send"},
            was_allowed=True
        )
        print(f"  Intent {i+1}: risk={score:.3f}, level={level.value}")

    assert level == RiskLevel.OK, "Normal behavior should be OK"

    # Check profile exists
    profile = engine.profiles.get(agent_id)
    assert profile is not None, "Profile should exist"
    assert profile.total_intents == 5, f"Should have 5 intents, got {profile.total_intents}"

    print("  ✅ Drift engine working")


def test_simulator():
    """Test plan simulation."""
    print("\nTesting simulator...")

    from tirs.simulator import get_simulator

    sim = get_simulator()

    # Test allowed plan
    plan = [
        {"mcp": "Calendar", "action": "book", "args": {"date": "2026-02-10", "time": "10:00"}}
    ]

    result = sim.simulate_plan("test-agent", plan)
    print(f"  Weekday booking: {result.overall_verdict}")
    assert result.overall_verdict == "ALLOWED", "Weekday should be allowed"

    # Test blocked plan (weekend)
    plan = [
        {"mcp": "Calendar", "action": "book", "args": {"date": "2026-02-08", "time": "10:00"}}
    ]

    result = sim.simulate_plan("test-agent", plan)
    print(f"  Weekend booking: {result.overall_verdict}")
    assert result.overall_verdict == "BLOCKED", "Weekend should be blocked"

    # Test salary cap
    plan = [
        {"mcp": "Offer", "action": "generate", "args": {"role": "L4", "salary": 200000}}
    ]

    result = sim.simulate_plan("test-agent", plan)
    print(f"  Over-cap salary: {result.overall_verdict}")
    assert result.overall_verdict == "BLOCKED", "Over-cap should be blocked"

    print("  ✅ Simulator working")


def test_audit():
    """Test audit ledger."""
    print("\nTesting audit ledger...")

    from tirs.audit import get_audit_ledger, AuditEventType

    ledger = get_audit_ledger()

    # Log some entries
    entry1 = ledger.log(AuditEventType.INTENT_CAPTURED, "test-agent", {"test": "data1"})
    entry2 = ledger.log(AuditEventType.POLICY_ALLOW, "test-agent", {"test": "data2"})

    print(f"  Entry 1: {entry1.entry_id}")
    print(f"  Entry 2: {entry2.entry_id}")

    # Verify chain
    is_valid, invalid = ledger.verify_chain()
    print(f"  Chain valid: {is_valid}")
    assert is_valid, "Chain should be valid"

    # Verify individual entries
    assert entry1.verify(), "Entry 1 should verify"
    assert entry2.verify(), "Entry 2 should verify"

    print("  ✅ Audit ledger working")


def test_remediation():
    """Test remediation engine."""
    print("\nTesting remediation engine...")

    from tirs.remediation import get_remediation_engine

    engine = get_remediation_engine()

    # Test salary remediation
    result = engine.analyze(
        action="Offer.generate",
        args={"role": "L4", "salary": 200000},
        policy_violated="Salary Caps",
        block_reason="Salary $200,000 exceeds $180,000 cap for L4"
    )

    print(f"  Suggestions: {len(result.suggestions)}")
    print(f"  Auto-fixable: {result.auto_fixable}")
    print(f"  Recommended: {result.recommended.description if result.recommended else 'None'}")

    assert len(result.suggestions) > 0, "Should have suggestions"
    assert result.auto_fixable, "Salary should be auto-fixable"

    print("  ✅ Remediation engine working")


def test_core_integration():
    """Test TIRS core integration."""
    print("\nTesting TIRS core...")

    from tirs.core import get_tirs

    tirs = get_tirs()

    # Test plan simulation
    plan = [
        {"mcp": "Email", "action": "send", "args": {"to": "user@company.com", "body": "Hello"}}
    ]

    result = tirs.simulate_plan("integration-test", plan)
    print(f"  Plan simulation: {result.simulation.overall_verdict}")
    assert result.allowed, "Simple email should be allowed"

    # Test risk summary
    summary = tirs.get_risk_summary()
    print(f"  Total agents tracked: {summary['total_agents']}")

    print("  ✅ TIRS core working")


def run_all_tests():
    """Run all tests."""
    print("="*50)
    print("  TIRS Test Suite")
    print("="*50)

    tests = [
        test_embeddings,
        test_drift_engine,
        test_simulator,
        test_audit,
        test_remediation,
        test_core_integration,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "="*50)
    print(f"  Results: {passed} passed, {failed} failed")
    print("="*50)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
