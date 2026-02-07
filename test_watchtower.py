#!/usr/bin/env python3
"""
Quick Watchtower API Test
======================
Tests connection to Watchtower before running full demo.
"""

import os
import sys
from pathlib import Path

# Load .env file
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    print(f"Loading {env_path}...")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                if key == "WATCHTOWER_API_KEY":
                    print(f"  {key}: {value[:15]}...{value[-8:]}")
                elif value:
                    print(f"  {key}: {value[:30]}...")
else:
    print("No .env file found!")
    sys.exit(1)

print("\n" + "="*60)
print("Testing Watchtower SDK Connection")
print("="*60 + "\n")

# Check API key
api_key = os.getenv("WATCHTOWER_API_KEY", "")
if not api_key:
    print("ERROR: WATCHTOWER_API_KEY not set")
    sys.exit(1)

if not api_key.startswith("ak_"):
    print(f"ERROR: Invalid API key format. Must start with 'ak_live_' or 'ak_test_'")
    print(f"       Got: {api_key[:20]}...")
    sys.exit(1)

print(f"API Key: {api_key[:15]}...{api_key[-8:]}")
print(f"Format: {'LIVE' if 'live' in api_key else 'TEST'} mode")

# Try to import SDK
print("\nImporting watchtower-sdk...")
try:
    from watchtower_sdk import WatchtowerClient
    print("  watchtower-sdk imported successfully")
except ImportError as e:
    print(f"  ERROR: {e}")
    print("  Run: pip install watchtower-sdk")
    sys.exit(1)

# Initialize client
print("\nInitializing Watchtower client...")
try:
    client = WatchtowerClient(
        api_key=api_key,
        user_id=os.getenv("WATCHTOWER_USER_ID", "test-user"),
        agent_id=os.getenv("WATCHTOWER_AGENT_ID", "test-agent")
    )
    print("  Client initialized")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

# Test capture_plan
print("\nTesting capture_plan()...")
try:
    plan = client.capture_plan(
        llm="test-agent",
        prompt="Test action",
        plan={
            "goal": "Test connection",
            "steps": [{
                "mcp": "test",
                "action": "ping",
                "params": {"test": True}
            }]
        }
    )
    print(f"  Plan captured: {plan}")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

# Test get_intent_token
print("\nTesting get_intent_token()...")
try:
    token = client.get_intent_token(plan)
    print(f"  Token ID: {token.token_id if hasattr(token, 'token_id') else 'N/A'}")
    print(f"  Plan Hash: {token.plan_hash[:20] if hasattr(token, 'plan_hash') else 'N/A'}...")
    print(f"  Expires: {token.expires_at if hasattr(token, 'expires_at') else '60s'}")
except Exception as e:
    print(f"  ERROR: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("SUCCESS! Watchtower SDK is working correctly.")
print("="*60)
print("\nRun the full demo with:")
print("  python3 demo/dev_demo.py")
print("  python3 demo/dev_demo.py --no-pause")
