import subprocess
import os

AGENTS_DIR = r"d:\fun stuff\vibe coding shit\thing 2\hr_delegate\agents"

def run_test(name, cmd_args):
    print(f"\n--- TESTING {name} ---")
    try:
        result = subprocess.run(f"python {cmd_args}", cwd=AGENTS_DIR, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("=== HR SWARM SAFETY VERIFICATION ===")

    # 1. Scheduler (Time Block)
    run_test("SCHEDULER (Weekend Block)", "scheduler.py cand_001 \"2026-02-14 10:00\"")
    
    # 2. Negotiator (Salary Cap)
    run_test("NEGOTIATOR (Salary Cap)", "negotiator.py cand_001 L3 200000")
    
    # 3. Sourcer (PII/Bias)
    run_test("SOURCER (Bias/PII)", "sourcer.py example@gmail.com \"We need a rockstar guys. Call Alice at 555-0101.\"")
    
    # 4. Screener (Blind Screening)
    run_test("SCREENER (Redaction)", "screener.py ./resumes/alice.pdf")
    
    # 5. Onboarder (Budget)
    run_test("ONBOARDER (Role Budget)", "onboarder.py emp_001 Sales MacbookPro")
    
    # 6. Perf Manager (Sentiment)
    run_test("PERF_MANAGER (Abusive Lang)", "perf_manager.py emp_001 \"He is too lazy and aggressive.\"")
    
    # 7. Benefits (HIPAA)
    run_test("BENEFITS (HIPAA)", "benefits_coord.py emp_001 SickLeave 5 \"Surgery for heart condition.\"")
    
    # 8. Legal (Visa Expiry)
    # mock expiry in past
    run_test("LEGAL (Visa Block)", "legal_compliance.py cand_001 verified \"2025-01-01\"")
    
    # 9. L&D (Training Budget)
    run_test("L&D (Conf Limit)", "lnd_manager.py emp_001 conference 5000")
    
    # 10. Payroll (Receipt Check)
    run_test("PAYROLL (Missing Receipt)", "payroll_agent.py claim_123 75 false")
    
    # 11. Culture (Insurance)
    run_test("CULTURE (No Insurance)", "culture_agent.py HappyHour DiveBar false")
    
    # 12. Offboarder (Revocation Time)
    # Testing logic assumes logic checking is inside agent/engine
    run_test("OFFBOARDER (Security)", "offboarder.py emp_001 \"2026-02-10 18:00\"")

if __name__ == "__main__":
    main()
