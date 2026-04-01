"""
run_tests.py — PaperBrain Test Runner
Runs pytest and saves results to test_results/ folder.

Usage:
    python run_tests.py              # all tests
    python run_tests.py --unit       # unit tests only (fast, no API)
    python run_tests.py --qa         # QA evaluation only
    python run_tests.py --parallel   # run in parallel with pytest-xdist
"""

import os
import sys
import json
import subprocess
import argparse
from datetime import datetime

RESULTS_DIR = "test_results"


def run(args):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── Build pytest command ──────────────────────────
    cmd = [sys.executable, "-m", "pytest"]

    if args.unit:
        cmd += ["tests/test_auth.py", "tests/test_buckets.py", "tests/test_rag.py"]
    elif args.qa:
        cmd += ["tests/test_qa_eval.py"]
    else:
        cmd += ["tests/"]

    if args.parallel:
        cmd += ["-n", "auto"]

    # Output formats
    json_path = os.path.join(RESULTS_DIR, f"result_{timestamp}.json")
    txt_path  = os.path.join(RESULTS_DIR, f"result_{timestamp}.txt")

    # Add JSON report if pytest-json-report is available
    try:
        import pytest_jsonreport  # noqa
        cmd += [f"--json-report", f"--json-report-file={json_path}"]
    except ImportError:
        pass

    print(f"\n🧪 PaperBrain Test Suite")
    print(f"   Time     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Mode     : {'Unit' if args.unit else 'QA' if args.qa else 'All'}")
    print(f"   Parallel : {args.parallel}")
    print(f"   Saving to: {RESULTS_DIR}/\n")
    print("=" * 60)

    # ── Run pytest, capture output ────────────────────
    result = subprocess.run(cmd, capture_output=False, text=True)

    # ── Save plain text summary ───────────────────────
    summary = {
        "timestamp":   datetime.now().isoformat(),
        "mode":        "unit" if args.unit else "qa" if args.qa else "all",
        "parallel":    args.parallel,
        "exit_code":   result.returncode,
        "status":      "PASSED" if result.returncode == 0 else "FAILED",
    }

    with open(txt_path, "w") as f:
        f.write(f"PaperBrain Test Results\n")
        f.write(f"{'='*60}\n")
        f.write(f"Timestamp : {summary['timestamp']}\n")
        f.write(f"Mode      : {summary['mode']}\n")
        f.write(f"Status    : {summary['status']}\n")
        f.write(f"Exit Code : {summary['exit_code']}\n")
        f.write(f"{'='*60}\n")
        f.write("Run: " + " ".join(cmd) + "\n")

    # ── Also save/update latest.json ─────────────────
    latest_path = os.path.join(RESULTS_DIR, "latest.json")
    with open(latest_path, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 60)
    status_icon = "✅" if result.returncode == 0 else "❌"
    print(f"{status_icon} Status   : {summary['status']}")
    print(f"📄 TXT    : {txt_path}")
    print(f"📄 Latest : {latest_path}")
    if os.path.exists(json_path):
        print(f"📄 JSON   : {json_path}")
    print()

    return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PaperBrain Test Runner")
    parser.add_argument("--unit",     action="store_true", help="Unit tests only (no API calls)")
    parser.add_argument("--qa",       action="store_true", help="QA evaluation only")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    args = parser.parse_args()
    sys.exit(run(args))
