#!/usr/bin/env python3
"""Executable convergence checks for the eight-member evidence-review suite."""
import hashlib, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve()
# <pack>/shared/check_convergence.py -> <pack>/skills
if HERE.parent.name == "shared" and (HERE.parent.parent / "skills").is_dir():
    ROOT = HERE.parent.parent / "skills"
# <catalog>/<skill>/scripts/check_convergence.py -> <catalog>
else:
    ROOT = HERE.parents[2]
if not (ROOT / "project-review-orchestrator").is_dir():
    for cand in (ROOT.parent / "skills", ROOT / "skills", ROOT.parent):
        if (cand / "project-review-orchestrator").is_dir():
            ROOT = cand; break
IDS = ["project-review-orchestrator", "github-reproduction-scout", "implementation-comparator", "defect-synthesizer", "targeted-remediator", "concept-substance-reviewer", "equivalence-scholarship-reviewer"]
SPECIALIST = "skill-criticagent"
# Sibling skill dir works both in the standalone pack (opt/skills/*) and in the library catalog.
_legacy = Path("D:/agent-library/catalog") / SPECIALIST
CRITIC_ROOT = (ROOT / SPECIALIST) if (ROOT / SPECIALIST).is_dir() else _legacy


def main():
    errors = []
    canonical = None
    for skill_id in IDS:
        directory = ROOT / skill_id
        for name in ("SKILL.md", "manifest.json", "references/protocol.md", "scripts/validate_report.py", "schemas/report.schema.json"):
            if not (directory / name).is_file(): errors.append(f"{skill_id}: missing {name}")
        manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8-sig"))
        if len(manifest.get("examples", [])) < 3: errors.append(f"{skill_id}: fewer than 3 examples")
        if not manifest.get("whenNot"): errors.append(f"{skill_id}: whenNot missing")
        text = (directory / "SKILL.md").read_text(encoding="utf-8-sig")
        if "v3.6" not in text: errors.append(f"{skill_id}: version not updated")
        current = hashlib.sha256((directory / "scripts/validate_report.py").read_bytes()).hexdigest()
        canonical = canonical or current
        if current != canonical: errors.append(f"{skill_id}: validator drift")
    # eighth member: skill-domain behavior specialist
    if not (CRITIC_ROOT / "SKILL.md").is_file(): errors.append("skill-criticagent: SKILL.md missing")
    if not (CRITIC_ROOT / "references" / "suite-interface.md").is_file(): errors.append("skill-criticagent: suite-interface.md missing")
    else:
        iface = (CRITIC_ROOT / "references" / "suite-interface.md").read_text(encoding="utf-8-sig")
        for token in ("behavior_evidence", "install", "fix-first", "reject"):
            if token not in iface: errors.append(f"skill-criticagent suite-interface missing {token}")
    if not (CRITIC_ROOT / "scripts" / "grade_runs.py").is_file(): errors.append("skill-criticagent: grade_runs.py missing")
    result = subprocess.run([sys.executable, str(ROOT / IDS[0] / "scripts/validate_report.py"), "--self-test"], capture_output=True, text=True)
    print(result.stdout, end=""); print(result.stderr, end="")
    if result.returncode: errors.append("validator contract tests failed")
    elif "Ran 64 tests" not in result.stderr: errors.append("contract test count changed; update convergence expectation")
    if errors:
        print("NON-CONVERGED\n" + "\n".join("- " + e for e in errors)); return 1
    print(f"CONVERGED: {len(IDS)} review skills + {SPECIALIST} specialist; resources present; no validator drift; 64 contract tests passed")
    return 0

if __name__ == "__main__": raise SystemExit(main())
