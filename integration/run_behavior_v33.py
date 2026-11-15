#!/usr/bin/env python3
"""Run criticagent's grade_runs.py over the 3 v3.3 behavior cases. Exit 0 = all cases present and graded."""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRADER = r"D:\agent-library\catalog\skill-criticagent\scripts\grade_runs.py"
SKILL_DIR = Path(r"D:\agent-library\catalog\project-review-orchestrator")
EVALS = json.loads((SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8"))["evals"]
FILES = {"state-machine-recall": ("out-state-with.md", "out-state-without.md"),
         "environment-block-classification": ("out-env-with.md", "out-env-without.md"),
         "gate-decision": ("out-gate-with.md", "out-gate-without.md")}


def main():
    runs = {}
    for case in EVALS:
        w, wo = FILES[case["id"]]
        pw, pwo = HERE / w, HERE / wo
        if not (pw.is_file() and pwo.is_file()):
            print(f"MISSING outputs for {case['id']}: {pw.is_file()=} {pwo.is_file()=}"); return 2
        runs[case["prompt"]] = {"with_skill": str(pw), "without_skill": str(pwo)}
    manifest = {"runs": [{"prompt": p, "with_skill": {"output_file": m["with_skill"]},
                          "without_skill": {"output_file": m["without_skill"]}}
                         for p, m in runs.items()]}
    mp = HERE / "runs-manifest-v33.json"
    mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    out = HERE / "behavior-result-v33.json"
    p = subprocess.run([sys.executable, GRADER, str(SKILL_DIR), str(mp), "--summary-only", "--output", str(out)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    (HERE / "grader-log.txt").write_text((p.stdout or "") + "\n" + (p.stderr or ""), encoding="utf-8")
    if not out.is_file(): print("grader produced no output json"); return 1
    s = json.loads(out.read_text(encoding="utf-8")).get("summary", {})
    print(f"cases={s.get('with_skill',{}).get('total')} with={s.get('with_skill',{}).get('passed')} "
          f"without={s.get('without_skill',{}).get('passed')} "
          f"non_discriminating={s.get('assertion_audit',{}).get('non_discriminating_count')}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
