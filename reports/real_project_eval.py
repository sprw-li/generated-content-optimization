#!/usr/bin/env python3
"""Reproduce the five project records from the packaged copy.

Paths resolve relative to THIS file so the pack works wherever it is copied.
The full finding set lives in records/<name>.json; this script re-validates them and
re-checks that every citation still resolves against the reviewed project root.
"""
import json, subprocess, sys
from pathlib import Path

REPORTS = Path(__file__).resolve().parent          # <pack>/reports
ROOT = REPORTS.parent                               # <pack>
VALIDATOR = ROOT / "shared" / "validate_report.py"
RECORDS = REPORTS / "records"

SKILLS = ["project-review-orchestrator", "github-reproduction-scout", "implementation-comparator",
          "defect-synthesizer", "targeted-remediator", "concept-substance-reviewer",
          "equivalence-scholarship-reviewer", "skill-criticagent"]


def main():
    if not VALIDATOR.is_file():
        print(f"validator not found at {VALIDATOR}"); return 2
    checked, skipped, failed = 0, [], []
    for rec in sorted(RECORDS.glob("*.json")):
        d = json.loads(rec.read_text(encoding="utf-8"))
        root = Path(str(d.get("scope", {}).get("resolve_root", "")))
        if not root.is_dir():
            skipped.append(f"{rec.name} (reviewed root absent: {root})")
            continue
        p = subprocess.run([sys.executable, str(VALIDATOR), str(rec)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        checked += 1
        status = "PASS" if p.returncode == 0 else "FAIL"
        print(f"[{status}] {rec.name}: findings={len(d.get('findings', []))} gate={d.get('gate')}")
        if p.returncode != 0:
            failed.append(f"{rec.name}: {(p.stdout or '').strip()[-200:]}")
    print(f"\nrecords validated against live project roots: {checked}")
    if skipped:
        print("skipped (reviewed projects are NOT shipped in this pack):")
        for s in skipped: print("  -", s)
    if failed:
        print("\nFAILURES:"); [print("  -", f) for f in failed]; return 1
    if checked == 0:
        print("\nNo reviewed project roots present on this machine — nothing could be re-checked. "
              "This is reported, not hidden."); return 0
    print("\nAll re-checkable records satisfy the current contract.")
    return 0


if __name__ == "__main__": raise SystemExit(main())
