import subprocess
import os

# Compute agents directory relative to this file
AGENTS_DIR = os.path.join(os.path.dirname(__file__), "agents")

def run_test(name, cmd_args):
    print(f"\n--- TESTING {name} ---")
    print(f"Command: python {cmd_args}")
    try:
        # Use shell=True for simple argument passing in this demo
        result = subprocess.run(f"python {cmd_args}", cwd=AGENTS_DIR, shell=True, capture_output=True, text=True)
        print("OUTPUT:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
    except Exception as e:
        print(f"Execution Failed: {e}")

def main():
    # 1. Scheduler: Weekend Block
    # Feb 14, 2026 is a Saturday
    run_test("SCHEDULER (Weekend)", "scheduler.py cand_001 \"2026-02-14 10:00\"")

    # 2. Negotiator: Salary Cap Block
    # L3 Cap is 140k. We ask for 200k.
    run_test("NEGOTIATOR (Salary Cap)", "negotiator.py cand_001 L3 200000")

    # 3. Sourcer: PII & Bias
    # External email -> Redact Phone
    # "rockstar" -> Bias Block
    body = "We are looking for a rockstar developer. Call Alice at 555-0101."
    run_test("SOURCER (Bias/PII)", f"sourcer.py example@gmail.com \"{body}\"")

if __name__ == "__main__":
    main()
