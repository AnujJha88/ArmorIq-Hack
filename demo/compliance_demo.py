#!/usr/bin/env python3
"""
Enterprise Compliance Demo
==========================
Demonstrates real-world compliance policy enforcement based on:
- US Employment Law (FLSA, EEOC, ADA)
- Hiring Compliance (I-9, FCRA, Ban-the-Box)
- Data Privacy (GDPR, CCPA)
- Financial Controls (SOX-inspired)
- DEI Standards (OFCCP, Pay Equity)
"""

import sys
import os
import json
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
    END = '\033[0m'
    WHITE = '\033[97m'
    MAGENTA = '\033[35m'


def clear():
    os.system('clear' if os.name == 'posix' else 'cls')


def header(text):
    print(f"\n{C.BOLD}{C.CYAN}{'═' * 80}")
    print(f"  {text}")
    print(f"{'═' * 80}{C.END}\n")


def section(text):
    print(f"\n{C.BOLD}{C.BLUE}{'▶'} {text}{C.END}")
    print(f"{C.BLUE}{'─' * 70}{C.END}")


def box(title, lines, color=C.CYAN):
    width = 76
    print(f"\n{color}┌{'─' * (width - 2)}┐{C.END}")
    print(f"{color}│{C.END} {C.BOLD}{title}{C.END}{' ' * (width - 4 - len(title))}{color}│{C.END}")
    print(f"{color}├{'─' * (width - 2)}┤{C.END}")
    for line in lines:
        clean_len = len(line.replace(C.GREEN, '').replace(C.RED, '').replace(C.YELLOW, '').replace(C.CYAN, '').replace(C.BOLD, '').replace(C.END, '').replace(C.GRAY, ''))
        padding = width - 4 - clean_len
        print(f"{color}│{C.END}  {line}{' ' * max(0, padding)}{color}│{C.END}")
    print(f"{color}└{'─' * (width - 2)}┘{C.END}")


def result_display(result, show_details=True):
    """Display a compliance result."""
    if result.compliant:
        if result.action.value == "allow":
            status = f"{C.GREEN}✓ COMPLIANT{C.END}"
        elif result.action.value == "modify":
            status = f"{C.YELLOW}⚠ MODIFIED{C.END}"
        elif result.action.value == "warn":
            status = f"{C.YELLOW}⚠ WARNING{C.END}"
        else:
            status = f"{C.YELLOW}⚠ REQUIRES ACTION{C.END}"
    else:
        status = f"{C.RED}✗ NON-COMPLIANT{C.END}"

    print(f"\n  {status}")
    print(f"  {C.GRAY}Policy:{C.END} {result.policy_name}")
    if result.regulatory_reference:
        print(f"  {C.GRAY}Regulation:{C.END} {result.regulatory_reference.value}")
    print(f"  {C.GRAY}Reason:{C.END} {result.reason}")

    if show_details:
        if result.required_approval:
            print(f"  {C.YELLOW}Requires:{C.END} {result.required_approval.value} approval")

        if result.required_documentation:
            print(f"  {C.CYAN}Required Documentation:{C.END}")
            for doc in result.required_documentation[:3]:
                print(f"    • {doc}")

        if result.remediation_steps:
            print(f"  {C.CYAN}Remediation Steps:{C.END}")
            for step in result.remediation_steps[:4]:
                print(f"    → {step[:70]}")

        if result.risk_score > 0:
            risk_color = C.GREEN if result.risk_score < 0.2 else C.YELLOW if result.risk_score < 0.4 else C.RED
            print(f"  {C.GRAY}Risk Score:{C.END} {risk_color}{result.risk_score:.2f}{C.END}")


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLIANCE SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════

def demo_i9_compliance(engine):
    """Demonstrate I-9 Employment Eligibility verification."""
    header("I-9 EMPLOYMENT ELIGIBILITY (IRCA)")

    print(f"""
  {C.CYAN}Legal Requirement:{C.END} Immigration Reform and Control Act (IRCA)

  Every employer must verify employment eligibility:
  • Complete I-9 within 3 business days of hire
  • Employee completes Section 1 on/before first day
  • Acceptable documents: List A, or List B + List C
  • Retain for 3 years after hire or 1 year after termination
""")

    # Scenario 1: No I-9
    section("Scenario 1: Onboarding without I-9")
    print(f"  {C.GRAY}Action:{C.END} onboard_employee")
    print(f"  {C.GRAY}Payload:{C.END} employee='John Smith', start_date='2026-02-15'")

    result, _ = engine.evaluate(
        "onboard_employee",
        {"employee": "John Smith", "start_date": "2026-02-15"},
        {}
    )
    result_display(result)

    # Scenario 2: With documents but not verified
    section("Scenario 2: Documents provided, pending verification")
    print(f"  {C.GRAY}Action:{C.END} onboard_employee")
    print(f"  {C.GRAY}Payload:{C.END} i9_documents=['drivers_license', 'social_security_card']")

    result, _ = engine.evaluate(
        "onboard_employee",
        {
            "employee": "Jane Doe",
            "start_date": "2026-02-15",
            "i9_documents": ["drivers_license", "social_security_card"]  # List B + C
        },
        {}
    )
    result_display(result)

    # Scenario 3: Fully verified
    section("Scenario 3: I-9 Complete and Verified")
    print(f"  {C.GRAY}Action:{C.END} onboard_employee")
    print(f"  {C.GRAY}Payload:{C.END} i9_status='verified'")

    result, _ = engine.evaluate(
        "onboard_employee",
        {"employee": "Bob Wilson", "start_date": "2026-02-15", "i9_status": "verified"},
        {}
    )
    result_display(result)


def demo_background_check_fcra(engine):
    """Demonstrate FCRA-compliant background checks."""
    header("BACKGROUND CHECK COMPLIANCE (FCRA)")

    print(f"""
  {C.CYAN}Legal Requirement:{C.END} Fair Credit Reporting Act (FCRA)

  Before running background check:
  • Provide standalone disclosure document
  • Obtain written authorization from candidate
  • Provide 'Summary of Rights Under FCRA'

  Ban-the-Box Laws (many states):
  • Cannot ask criminal history on initial application
  • Can only inquire after conditional offer
""")

    # Scenario 1: Ban-the-Box violation
    section("Scenario 1: Criminal History Check at Application Stage (California)")
    print(f"  {C.GRAY}Action:{C.END} run_background_check")
    print(f"  {C.GRAY}Payload:{C.END} candidate_state='CA', hiring_stage='application'")

    result, _ = engine.evaluate(
        "run_background_check",
        {
            "candidate_state": "CA",
            "hiring_stage": "application",
            "check_type": "criminal"
        },
        {}
    )
    result_display(result)

    # Scenario 2: Missing consent
    section("Scenario 2: Background Check Without Proper Consent")
    print(f"  {C.GRAY}Action:{C.END} run_background_check")
    print(f"  {C.GRAY}Payload:{C.END} disclosure_provided=True, candidate_consent=False")

    result, _ = engine.evaluate(
        "run_background_check",
        {
            "candidate_state": "TX",
            "hiring_stage": "post_offer",
            "disclosure_provided": True,
            "candidate_consent": False  # Missing!
        },
        {}
    )
    result_display(result)

    # Scenario 3: Fully compliant
    section("Scenario 3: FCRA-Compliant Background Check")
    print(f"  {C.GRAY}Action:{C.END} run_background_check")
    print(f"  {C.GRAY}Payload:{C.END} disclosure_provided=True, candidate_consent=True, hiring_stage='post_offer'")

    result, _ = engine.evaluate(
        "run_background_check",
        {
            "candidate_state": "TX",
            "hiring_stage": "post_offer",
            "disclosure_provided": True,
            "candidate_consent": True,
            "check_type": "standard"
        },
        {}
    )
    result_display(result)


def demo_compensation_compliance(engine):
    """Demonstrate pay equity and compensation band compliance."""
    header("COMPENSATION COMPLIANCE (Pay Equity & Transparency)")

    print(f"""
  {C.CYAN}Legal Requirements:{C.END}
  • Pay Transparency Laws (CO, CA, NY, WA, etc.)
  • Salary History Bans (CA, MA, NY, etc.)
  • Equal Pay Act / Pay Equity

  {C.CYAN}Internal Policy:{C.END}
  • Compensation bands by level
  • Approval hierarchies for above-band offers
  • Total compensation limits
""")

    # Scenario 1: Salary history violation
    section("Scenario 1: Offer Based on Salary History (California)")
    print(f"  {C.GRAY}Action:{C.END} generate_offer")
    print(f"  {C.GRAY}Payload:{C.END} candidate_state='CA', based_on_salary_history=True")

    result, _ = engine.evaluate(
        "generate_offer",
        {
            "candidate_state": "CA",
            "based_on_salary_history": True,
            "salary": 160000
        },
        {}
    )
    result_display(result)

    # Scenario 2: Job posting without salary (Colorado)
    section("Scenario 2: Job Posting Without Salary Range (Colorado)")
    print(f"  {C.GRAY}Action:{C.END} post_job")
    print(f"  {C.GRAY}Payload:{C.END} location_state='CO', salary_range_included=False")

    result, _ = engine.evaluate(
        "post_job",
        {
            "title": "Senior Software Engineer",
            "location_state": "CO",
            "salary_range_included": False
        },
        {}
    )
    result_display(result)

    # Scenario 3: Within band offer
    section("Scenario 3: Offer Within Compensation Band")
    print(f"  {C.GRAY}Action:{C.END} generate_offer")
    print(f"  {C.GRAY}Payload:{C.END} level='IC4', salary=155000")

    result, _ = engine.evaluate(
        "generate_offer",
        {
            "level": "IC4",
            "salary": 155000,  # Within IC4 band: 130k-190k
            "candidate_state": "TX"
        },
        {}
    )
    result_display(result)
    if result.metadata:
        print(f"\n  {C.CYAN}Band Details:{C.END}")
        print(f"    Level: {result.metadata.get('level')}")
        print(f"    Range: ${result.metadata.get('band_min', 0):,} - ${result.metadata.get('band_max', 0):,}")
        print(f"    Midpoint: ${result.metadata.get('band_mid', 0):,}")
        print(f"    Percentile: {result.metadata.get('percentile', 0)}%")

    # Scenario 4: Over band offer
    section("Scenario 4: Offer Exceeds Compensation Band")
    print(f"  {C.GRAY}Action:{C.END} generate_offer")
    print(f"  {C.GRAY}Payload:{C.END} level='IC4', salary=210000 (band max: $190k)")

    result, _ = engine.evaluate(
        "generate_offer",
        {
            "level": "IC4",
            "salary": 210000,  # 10% over IC4 band max of 190k
            "candidate_state": "TX"
        },
        {}
    )
    result_display(result)


def demo_data_privacy(engine):
    """Demonstrate GDPR/CCPA data privacy compliance."""
    header("DATA PRIVACY COMPLIANCE (GDPR / CCPA)")

    print(f"""
  {C.CYAN}GDPR (EU Residents):{C.END}
  • Consent required for data processing
  • Cross-border transfer restrictions
  • Right to access, correct, delete

  {C.CYAN}CCPA (California Residents):{C.END}
  • Right to know what data is collected
  • Right to delete personal information
  • Right to opt-out of sale of data

  {C.CYAN}General PII Protection:{C.END}
  • Detect and redact SSN, credit cards, etc.
  • Restrict external sharing of personal data
""")

    # Scenario 1: PII in external email
    section("Scenario 1: PII Detected in External Email")
    print(f"  {C.GRAY}Action:{C.END} send_email")
    print(f"  {C.GRAY}Payload:{C.END} to='vendor@external.com', body contains SSN and phone")

    result, _ = engine.evaluate(
        "send_email",
        {
            "to": "vendor@external.com",
            "subject": "Candidate Information",
            "body": "Please process John Smith. SSN: 123-45-6789, Phone: 555-123-4567"
        },
        {"company_domain": "company.com"}
    )
    result_display(result)

    if result.modified_payload:
        print(f"\n  {C.CYAN}Redacted Content:{C.END}")
        print(f"    {result.modified_payload.get('body', '')[:80]}...")

    # Scenario 2: GDPR cross-border transfer
    section("Scenario 2: EU Data Transfer Without SCCs")
    print(f"  {C.GRAY}Action:{C.END} transfer_data")
    print(f"  {C.GRAY}Payload:{C.END} data_subject_location='EU', destination='US', no legal mechanism")

    result, _ = engine.evaluate(
        "transfer_data",
        {
            "data_subject_location": "EU",
            "destination": "US",
            "is_eu_resident": True,
            "standard_contractual_clauses": False,
            "adequacy_decision": False
        },
        {}
    )
    result_display(result)

    # Scenario 3: Bulk data export
    section("Scenario 3: Bulk Sensitive Data Export")
    print(f"  {C.GRAY}Action:{C.END} export_data")
    print(f"  {C.GRAY}Payload:{C.END} data_type='salary', record_count=500")

    result, _ = engine.evaluate(
        "export_data",
        {
            "data_type": "salary_compensation",
            "record_count": 500
        },
        {}
    )
    result_display(result)


def demo_working_time(engine):
    """Demonstrate working time and scheduling compliance."""
    header("WORKING TIME & SCHEDULING COMPLIANCE")

    print(f"""
  {C.CYAN}Work-Life Balance Policy:{C.END}
  • Business hours: 8 AM - 6 PM
  • Core hours: 10 AM - 4 PM
  • No weekend scheduling without approval

  {C.CYAN}Candidate Experience:{C.END}
  • Prefer core hours for interviews
  • Respect candidate time zones
""")

    # Scenario 1: Weekend interview
    section("Scenario 1: Interview Scheduled on Weekend")
    print(f"  {C.GRAY}Action:{C.END} schedule_interview")
    print(f"  {C.GRAY}Payload:{C.END} time='2026-02-08 14:00' (Saturday)")

    result, _ = engine.evaluate(
        "schedule_interview",
        {"time": "2026-02-08 14:00", "candidate": "John Smith"},
        {}
    )
    result_display(result)

    # Scenario 2: After hours meeting
    section("Scenario 2: Meeting Scheduled After Business Hours")
    print(f"  {C.GRAY}Action:{C.END} schedule_meeting")
    print(f"  {C.GRAY}Payload:{C.END} time='2026-02-10 19:30' (7:30 PM)")

    result, _ = engine.evaluate(
        "schedule_meeting",
        {"time": "2026-02-10 19:30", "title": "Team Sync"},
        {}
    )
    result_display(result)

    # Scenario 3: Core hours interview
    section("Scenario 3: Interview During Core Hours")
    print(f"  {C.GRAY}Action:{C.END} schedule_interview")
    print(f"  {C.GRAY}Payload:{C.END} time='2026-02-10 14:00' (Tuesday, 2 PM)")

    result, _ = engine.evaluate(
        "schedule_interview",
        {"time": "2026-02-10 14:00", "candidate": "Jane Doe"},
        {}
    )
    result_display(result)


def demo_dei_compliance(engine):
    """Demonstrate DEI and inclusive language compliance."""
    header("DEI & INCLUSIVE LANGUAGE COMPLIANCE")

    print(f"""
  {C.CYAN}EEOC Non-Discrimination:{C.END}
  • Cannot consider protected characteristics
  • Race, color, religion, sex, national origin
  • Age, disability, genetic information

  {C.CYAN}Inclusive Language:{C.END}
  • Avoid gendered language
  • Remove ableist terms
  • Eliminate cultural bias terms
  • Use inclusive job requirements
""")

    # Scenario 1: Biased job posting
    section("Scenario 1: Job Posting with Non-Inclusive Language")
    print(f"  {C.GRAY}Action:{C.END} post_job")
    print(f"  {C.GRAY}Content:{C.END} 'Looking for a rockstar ninja who can crush it...'")

    result, _ = engine.evaluate(
        "post_job",
        {
            "title": "Senior Developer",
            "description": "We're looking for a rockstar ninja who can crush it! Must be young, energetic, and a digital native. Join our tribe of coding wizards!",
            "requirements": "Native English speaker required. Must be able to work crazy hours."
        },
        {}
    )
    result_display(result)

    if result.modified_payload:
        print(f"\n  {C.CYAN}Corrected Description:{C.END}")
        print(f"    {result.modified_payload.get('description', '')[:100]}...")

    # Scenario 2: Protected characteristic in rejection
    section("Scenario 2: Rejection Citing Protected Characteristic")
    print(f"  {C.GRAY}Action:{C.END} reject_candidate")
    print(f"  {C.GRAY}Payload:{C.END} reason mentions age")

    result, _ = engine.evaluate(
        "reject_candidate",
        {
            "candidate": "John Smith",
            "reason": "Candidate seems too old for this role",
            "notes": "Might not fit with our young team culture"
        },
        {}
    )
    result_display(result)

    # Scenario 3: Compliant communication
    section("Scenario 3: Compliant Job-Related Feedback")
    print(f"  {C.GRAY}Action:{C.END} evaluate_candidate")
    print(f"  {C.GRAY}Payload:{C.END} Objective, job-related criteria only")

    result, _ = engine.evaluate(
        "evaluate_candidate",
        {
            "candidate": "Jane Doe",
            "reason": "Strong technical skills demonstrated in coding exercise",
            "notes": "Excellent communication, meets all required qualifications"
        },
        {}
    )
    result_display(result)


def demo_financial_controls(engine):
    """Demonstrate financial controls and approval hierarchies."""
    header("FINANCIAL CONTROLS & APPROVAL HIERARCHY")

    print(f"""
  {C.CYAN}Signing Bonus Limits by Level:{C.END}
  • IC4: $25,000
  • IC5: $50,000
  • M3: $50,000
  • VP: $100,000

  {C.CYAN}Approval Thresholds (Total Commitment):{C.END}
  • $50k+: Manager
  • $100k+: Director
  • $250k+: VP
  • $500k+: C-Level
  • $1M+: Board
""")

    # Scenario 1: Signing bonus over limit
    section("Scenario 1: Signing Bonus Exceeds Level Limit")
    print(f"  {C.GRAY}Action:{C.END} generate_offer")
    print(f"  {C.GRAY}Payload:{C.END} level='IC4', signing_bonus=$40,000 (limit: $25k)")

    result, _ = engine.evaluate(
        "generate_offer",
        {
            "level": "IC4",
            "salary": 160000,
            "signing_bonus": 40000,  # Over IC4 limit of 25k
            "equity_value": 20000
        },
        {}
    )
    result_display(result)

    # Scenario 2: Large total commitment
    section("Scenario 2: Large Total Commitment Requires Executive Approval")
    print(f"  {C.GRAY}Action:{C.END} generate_offer")
    print(f"  {C.GRAY}Payload:{C.END} signing_bonus=$75k, equity=$200k, relocation=$50k = $325k total")

    result, _ = engine.evaluate(
        "generate_offer",
        {
            "level": "D1",
            "salary": 350000,
            "signing_bonus": 75000,
            "equity_value": 200000,
            "relocation": 50000
        },
        {}
    )
    result_display(result)

    # Scenario 3: Within all limits
    section("Scenario 3: Offer Within All Financial Controls")
    print(f"  {C.GRAY}Action:{C.END} generate_offer")
    print(f"  {C.GRAY}Payload:{C.END} level='IC4', signing_bonus=$20k, no relocation")

    result, _ = engine.evaluate(
        "generate_offer",
        {
            "level": "IC4",
            "salary": 160000,
            "signing_bonus": 20000,  # Under IC4 limit
            "equity_value": 15000
        },
        {}
    )
    result_display(result)


def show_coverage(engine):
    """Show regulatory coverage."""
    header("REGULATORY FRAMEWORK COVERAGE")

    coverage = engine.get_regulatory_coverage()

    print(f"  {C.CYAN}This compliance engine covers:{C.END}\n")

    for framework, policies in coverage.items():
        print(f"  {C.BOLD}{framework}{C.END}")
        for policy in policies:
            print(f"    • {policy}")
        print()


def main():
    clear()

    print(f"""
{C.BOLD}{C.CYAN}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   Enterprise Compliance Policy Engine Demo                                   ║
║   ─────────────────────────────────────────                                  ║
║                                                                              ║
║   Real-world compliance based on:                                            ║
║   • US Employment Law (FLSA, EEOC, ADA, FMLA)                               ║
║   • Hiring Compliance (I-9/IRCA, FCRA, Ban-the-Box)                         ║
║   • Data Privacy (GDPR, CCPA)                                               ║
║   • Financial Controls (SOX-inspired)                                        ║
║   • DEI Standards (OFCCP, Pay Equity, Inclusive Language)                   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.END}
""")

    from orchestrator.compliance_policies import get_compliance_engine

    print(f"{C.GRAY}Initializing Compliance Engine...{C.END}")
    engine = get_compliance_engine()

    stats = engine.get_policy_stats()
    print(f"{C.GREEN}✓ Loaded {stats['total_policies']} compliance policies{C.END}\n")

    no_pause = "--no-pause" in sys.argv

    def wait(msg="Press Enter to continue..."):
        if no_pause:
            print()
        else:
            input(f"\n{C.GRAY}{msg}{C.END}")

    # Show coverage
    show_coverage(engine)
    wait("Press Enter to see I-9 Compliance scenarios...")

    # Run demos
    demo_i9_compliance(engine)
    wait("Press Enter to see Background Check (FCRA) scenarios...")

    demo_background_check_fcra(engine)
    wait("Press Enter to see Compensation Compliance scenarios...")

    demo_compensation_compliance(engine)
    wait("Press Enter to see Data Privacy scenarios...")

    demo_data_privacy(engine)
    wait("Press Enter to see Working Time scenarios...")

    demo_working_time(engine)
    wait("Press Enter to see DEI Compliance scenarios...")

    demo_dei_compliance(engine)
    wait("Press Enter to see Financial Controls scenarios...")

    demo_financial_controls(engine)

    # Final statistics
    header("COMPLIANCE ENGINE STATISTICS")

    stats = engine.get_policy_stats()
    print(f"  Total Policies: {stats['total_policies']}")
    print(f"  Total Evaluations: {stats['total_evaluations']}")
    print(f"  Total Violations Detected: {stats['total_violations']}")

    print(f"\n  {C.CYAN}Policies by Category:{C.END}")
    for cat, count in stats['by_category'].items():
        if count > 0:
            print(f"    {cat}: {count}")

    # Summary
    print(f"""
{C.BOLD}{C.GREEN}
╔══════════════════════════════════════════════════════════════════════════════╗
║  DEMO COMPLETE                                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  Compliance Policies Demonstrated:                                           ║
║                                                                              ║
║  1. I-9 EMPLOYMENT ELIGIBILITY (IRCA)                                        ║
║     • Document verification (List A or List B + C)                           ║
║     • 3-day completion requirement                                           ║
║     • Employment blocked until verified                                      ║
║                                                                              ║
║  2. BACKGROUND CHECK (FCRA)                                                  ║
║     • Standalone disclosure requirement                                      ║
║     • Written consent before check                                           ║
║     • Ban-the-Box state compliance                                           ║
║                                                                              ║
║  3. COMPENSATION (Pay Equity & Transparency)                                 ║
║     • Salary history ban (CA, NY, MA, etc.)                                  ║
║     • Pay transparency (CO, NY, WA, etc.)                                    ║
║     • Level-based compensation bands                                         ║
║     • Approval hierarchies for exceptions                                    ║
║                                                                              ║
║  4. DATA PRIVACY (GDPR / CCPA)                                               ║
║     • PII detection and redaction                                            ║
║     • Cross-border transfer restrictions                                     ║
║     • Bulk export approval requirements                                      ║
║                                                                              ║
║  5. WORKING TIME (FLSA)                                                      ║
║     • Business hours enforcement                                             ║
║     • Weekend/holiday restrictions                                           ║
║     • Core hours for interviews                                              ║
║                                                                              ║
║  6. DEI & INCLUSIVE HIRING (EEOC/OFCCP)                                      ║
║     • Biased language detection                                              ║
║     • Protected characteristic checks                                        ║
║     • Diverse slate requirements                                             ║
║                                                                              ║
║  7. FINANCIAL CONTROLS (SOX-inspired)                                        ║
║     • Signing bonus limits by level                                          ║
║     • Relocation package limits                                              ║
║     • Approval hierarchies by amount                                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{C.END}
""")


if __name__ == "__main__":
    main()
