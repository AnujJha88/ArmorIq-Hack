#!/usr/bin/env python3
"""
Watchtower Developer Demo
======================
Shows exactly what code runs, what gets sent to Watchtower, and what comes back.
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Auto-load .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS
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

def header(text):
    print(f"\n{C.BOLD}{C.CYAN}{'═'*80}")
    print(f"  {text}")
    print(f"{'═'*80}{C.END}\n")

def code_block(title, code):
    print(f"{C.YELLOW}┌─ {title} {'─'*(73-len(title))}┐{C.END}")
    for line in code.strip().split('\n'):
        print(f"{C.YELLOW}│{C.END} {C.DIM}{line}{C.END}")
    print(f"{C.YELLOW}└{'─'*78}┘{C.END}")

def request_block(method, url, payload):
    print(f"\n{C.BLUE}▶ REQUEST TO WATCHTOWER{C.END}")
    print(f"{C.BLUE}┌{'─'*78}┐{C.END}")
    print(f"{C.BLUE}│{C.END} {C.BOLD}{method}{C.END} {url}")
    print(f"{C.BLUE}│{C.END}")
    print(f"{C.BLUE}│{C.END} {C.GRAY}Payload:{C.END}")
    for line in json.dumps(payload, indent=2).split('\n'):
        print(f"{C.BLUE}│{C.END}   {line}")
    print(f"{C.BLUE}└{'─'*78}┘{C.END}")

def response_block(status, data):
    color = C.GREEN if status == 200 else C.RED
    print(f"\n{color}◀ WATCHTOWER RESPONSE{C.END}")
    print(f"{color}┌{'─'*78}┐{C.END}")
    print(f"{color}│{C.END} Status: {C.BOLD}{status}{C.END}")
    print(f"{color}│{C.END}")
    if isinstance(data, dict):
        for line in json.dumps(data, indent=2).split('\n'):
            print(f"{color}│{C.END}   {line}")
    else:
        print(f"{color}│{C.END}   {data}")
    print(f"{color}└{'─'*78}┘{C.END}")

def local_block(title, result):
    color = C.GREEN if result.get('allowed', True) else C.RED
    print(f"\n{color}⚙ LOCAL POLICY ENGINE: {title}{C.END}")
    print(f"{color}┌{'─'*78}┐{C.END}")
    for k, v in result.items():
        print(f"{color}│{C.END}   {k}: {v}")
    print(f"{color}└{'─'*78}┘{C.END}")

def divider():
    print(f"\n{C.GRAY}{'─'*80}{C.END}\n")

# ═══════════════════════════════════════════════════════════════════════════════
# MOCK WATCHTOWER CLIENT FOR VISIBILITY
# ═══════════════════════════════════════════════════════════════════════════════

class DevWatchtowerClient:
    """Wrapper that shows all Watchtower API interactions."""

    def __init__(self):
        self.api_key = os.getenv("WATCHTOWER_API_KEY", "")
        self.backend = "https://customer-api.watchtower.io"
        self.iap_endpoint = os.getenv("WATCHTOWER_IAP_ENDPOINT", "https://iap.watchtower.io")

        # Try to import real SDK
        self.real_client = None
        try:
            from watchtower_sdk import WatchtowerClient
            if self.api_key.startswith("ak_"):
                self.real_client = WatchtowerClient(
                    api_key=self.api_key,
                    user_id=os.getenv("WATCHTOWER_USER_ID", "dev-demo"),
                    agent_id=os.getenv("WATCHTOWER_AGENT_ID", "dev-agent")
                )
                print(f"{C.GREEN}✓ Watchtower SDK connected (LIVE MODE){C.END}")
                print(f"{C.GRAY}  API Key: {self.api_key[:15]}...{self.api_key[-8:]}{C.END}")
            else:
                print(f"{C.YELLOW}⚠ No valid API key - using mock responses{C.END}")
        except ImportError:
            print(f"{C.YELLOW}⚠ watchtower-sdk not installed - using mock responses{C.END}")

    def capture_and_verify(self, action: str, payload: dict, agent: str) -> dict:
        """Show the full flow of capturing and verifying an intent."""

        # Step 1: Show the plan structure we're building
        plan_structure = {
            "goal": f"{agent} executing {action}",
            "steps": [{
                "mcp": "hr-tools",
                "action": action,
                "params": payload
            }]
        }

        code_block("YOUR CODE - Building Plan", f"""
watchtower = WatchtowerWrapper()

# Define what the agent wants to do
result = watchtower.capture_intent(
    action_type="{action}",
    payload={json.dumps(payload, indent=8)},
    agent_name="{agent}"
)
""")

        # Step 2: Show request to Watchtower
        request_payload = {
            "llm": agent,
            "prompt": f"Execute {action}",
            "plan": plan_structure
        }

        request_block("POST", f"{self.backend}/iap/sdk/token", request_payload)

        # Step 3: Get response from Watchtower (real or mock)
        if self.real_client:
            try:
                plan = self.real_client.capture_plan(
                    llm=agent,
                    prompt=f"Execute {action}: {json.dumps(payload)[:50]}",
                    plan=plan_structure
                )
                token = self.real_client.get_intent_token(plan)

                response_data = {
                    "token_id": token.token_id if hasattr(token, 'token_id') else "tok_xxx",
                    "plan_hash": token.plan_hash[:16] + "..." if hasattr(token, 'plan_hash') else "hash_xxx",
                    "expires_in": "60s",
                    "status": "ISSUED"
                }
                response_block(200, response_data)

            except Exception as e:
                response_block(400, {"error": str(e)})
                return {"allowed": False, "reason": str(e)}
        else:
            # Mock response
            response_data = {
                "token_id": f"tok_mock_{datetime.now().strftime('%H%M%S')}",
                "plan_hash": "mock_hash_abc123...",
                "expires_in": "60s",
                "status": "ISSUED (MOCK)"
            }
            response_block(200, response_data)

        # Step 4: Local policy evaluation
        result = self._evaluate_local_policy(action, payload)
        local_block(f"{result['verdict']}", result)

        return result

    def _evaluate_local_policy(self, action: str, payload: dict) -> dict:
        """Evaluate against local policies (same as WatchtowerWrapper)."""

        # Work-Life Balance
        if action in ["schedule_interview", "book_meeting"]:
            time_str = payload.get("time", payload.get("datetime", ""))
            if time_str:
                try:
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    if dt.weekday() >= 5:
                        return {
                            "allowed": False,
                            "verdict": "DENY",
                            "policy": "Work-Life Balance",
                            "reason": f"Weekend scheduling blocked ({dt.strftime('%A')})",
                            "suggestion": "Choose a weekday (Mon-Fri)"
                        }
                    if not (9 <= dt.hour < 17):
                        return {
                            "allowed": False,
                            "verdict": "DENY",
                            "policy": "Work-Life Balance",
                            "reason": f"Outside work hours (9AM-5PM)",
                            "suggestion": "Schedule between 9:00-17:00"
                        }
                except ValueError:
                    pass

        # Salary Caps
        if action in ["generate_offer", "create_offer", "make_offer"]:
            role = payload.get("role", "")
            salary = payload.get("salary", 0)
            caps = {"L3": 140000, "L4": 180000, "L5": 240000}
            if role in caps and salary > caps[role]:
                return {
                    "allowed": False,
                    "verdict": "DENY",
                    "policy": "Salary Caps",
                    "reason": f"${salary:,} exceeds ${caps[role]:,} cap for {role}",
                    "suggestion": f"Reduce to ${caps[role]:,} or request VP approval"
                }

        # PII Protection
        if action in ["send_email", "send_message"]:
            body = payload.get("body", "")
            recipient = payload.get("recipient", payload.get("to", ""))

            # Check for non-inclusive terms first
            bad_terms = ["rockstar", "ninja", "guru", "wizard"]
            for term in bad_terms:
                if term.lower() in body.lower():
                    return {
                        "allowed": False,
                        "verdict": "DENY",
                        "policy": "Inclusive Language",
                        "reason": f"Non-inclusive term: '{term}'",
                        "suggestion": f"Replace '{term}' with professional alternative"
                    }

            # PII redaction for external
            import re
            if recipient and not recipient.endswith("@company.com"):
                phone_pattern = r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"
                if re.search(phone_pattern, body):
                    redacted = re.sub(phone_pattern, "[REDACTED]", body)
                    return {
                        "allowed": True,
                        "verdict": "MODIFY",
                        "policy": "PII Protection",
                        "reason": "Phone number redacted for external recipient",
                        "original_body": body,
                        "modified_body": redacted
                    }

        # Expense receipts
        if action in ["approve_expense", "process_expense"]:
            amount = payload.get("amount", 0)
            has_receipt = payload.get("has_receipt", payload.get("receipt", False))
            if amount > 50 and not has_receipt:
                return {
                    "allowed": False,
                    "verdict": "DENY",
                    "policy": "Fraud Prevention",
                    "reason": f"Receipt required for expenses over $50",
                    "suggestion": "Attach receipt documentation"
                }

        return {
            "allowed": True,
            "verdict": "ALLOW",
            "policy": None,
            "reason": "All policy checks passed"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN DEMO
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    import time

    # Check for --no-pause flag
    no_pause = "--no-pause" in sys.argv or "-n" in sys.argv

    def wait(msg="Press Enter for next test..."):
        if no_pause:
            time.sleep(1)
        else:
            input(f"\n{C.GRAY}{msg}{C.END}")

    os.system('clear' if os.name == 'posix' else 'cls')

    print(f"""
{C.BOLD}{C.CYAN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   Watchtower Developer Demo                                                     ║
║   ──────────────────────                                                     ║
║                                                                              ║
║   This demo shows:                                                           ║
║   • Your code (what you write)                                               ║
║   • Request to Watchtower API (what gets sent)                                  ║
║   • Response from Watchtower (what comes back)                                  ║
║   • Local policy evaluation (business rules)                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.END}
""")

    client = DevWatchtowerClient()

    wait("Press Enter to start demo...")

    # ═══════════════════════════════════════════════════════════════════════════
    # TEST 1: Valid Interview
    # ═══════════════════════════════════════════════════════════════════════════
    header("TEST 1: Schedule Interview (Monday 2PM) → Expected: ALLOW")

    client.capture_and_verify(
        action="schedule_interview",
        payload={
            "candidate": "John Smith",
            "time": "2026-02-09 14:00",
            "interviewer": "Jane Doe"
        },
        agent="scheduler-agent"
    )

    wait()

    # ═══════════════════════════════════════════════════════════════════════════
    # TEST 2: Weekend Block
    # ═══════════════════════════════════════════════════════════════════════════
    header("TEST 2: Schedule Interview (Saturday) → Expected: DENY")

    client.capture_and_verify(
        action="schedule_interview",
        payload={
            "candidate": "John Smith",
            "time": "2026-02-14 10:00",
            "interviewer": "Jane Doe"
        },
        agent="scheduler-agent"
    )

    wait()

    # ═══════════════════════════════════════════════════════════════════════════
    # TEST 3: Salary Cap
    # ═══════════════════════════════════════════════════════════════════════════
    header("TEST 3: Generate Offer ($200K for L4) → Expected: DENY")

    client.capture_and_verify(
        action="generate_offer",
        payload={
            "candidate": "Alice Johnson",
            "role": "L4",
            "salary": 200000,
            "equity": 5000
        },
        agent="negotiator-agent"
    )

    wait()

    # ═══════════════════════════════════════════════════════════════════════════
    # TEST 4: Valid Offer
    # ═══════════════════════════════════════════════════════════════════════════
    header("TEST 4: Generate Offer ($175K for L4) → Expected: ALLOW")

    client.capture_and_verify(
        action="generate_offer",
        payload={
            "candidate": "Bob Williams",
            "role": "L4",
            "salary": 175000,
            "equity": 4000
        },
        agent="negotiator-agent"
    )

    wait()

    # ═══════════════════════════════════════════════════════════════════════════
    # TEST 5: PII Redaction
    # ═══════════════════════════════════════════════════════════════════════════
    header("TEST 5: Email with Phone Number → Expected: MODIFY (redact PII)")

    client.capture_and_verify(
        action="send_email",
        payload={
            "recipient": "candidate@gmail.com",
            "subject": "Your Application",
            "body": "Hi! Call me at 555-123-4567 to discuss."
        },
        agent="sourcer-agent"
    )

    wait()

    # ═══════════════════════════════════════════════════════════════════════════
    # TEST 6: Inclusive Language
    # ═══════════════════════════════════════════════════════════════════════════
    header("TEST 6: Email with 'rockstar' → Expected: DENY")

    client.capture_and_verify(
        action="send_email",
        payload={
            "recipient": "team@company.com",
            "subject": "Job Opening",
            "body": "We're looking for a rockstar developer!"
        },
        agent="sourcer-agent"
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════
    print(f"""
{C.BOLD}{C.GREEN}
╔══════════════════════════════════════════════════════════════════════════════╗
║  DEMO COMPLETE                                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Flow Summary:                                                               ║
║  ┌────────────────────────────────────────────────────────────────────────┐  ║
║  │  YOUR CODE                                                             │  ║
║  │    │                                                                   │  ║
║  │    ▼                                                                   │  ║
║  │  watchtower.capture_intent(action, payload, agent)                        │  ║
║  │    │                                                                   │  ║
║  │    ├──► Watchtower SDK builds plan structure                              │  ║
║  │    │                                                                   │  ║
║  │    ├──► POST /iap/sdk/token  (get cryptographic intent token)          │  ║
║  │    │         ▲                                                         │  ║
║  │    │         │                                                         │  ║
║  │    │    ◄────┘  Response: token_id, plan_hash, expires                 │  ║
║  │    │                                                                   │  ║
║  │    ├──► Local Policy Engine evaluates business rules                   │  ║
║  │    │                                                                   │  ║
║  │    ▼                                                                   │  ║
║  │  Result: ALLOW / DENY / MODIFY                                         │  ║
║  └────────────────────────────────────────────────────────────────────────┘  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.END}
""")


if __name__ == "__main__":
    main()
