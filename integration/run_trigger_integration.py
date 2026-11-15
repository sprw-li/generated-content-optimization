#!/usr/bin/env python3
"""Run criticagent's trigger grader against a suite skill, using REAL router output as decisions."""
import json, re, subprocess, sys
from pathlib import Path

PY = sys.executable
ROUTER = r"D:\agent-library\router.py"
GRADER = r"D:\agent-library\catalog\skill-criticagent\scripts\grade_triggers.py"
TARGET = "project-review-orchestrator"

# should_trigger ground truth = would a user asking this want the project-review orchestrator?
CASES = [
    ("全项目审查这几个目录，分别给证据和改进顺序", True),
    ("把这个会话作为独立项目评审", True),
    ("只读审查项目，不要自动修改", True),
    ("对五个项目做多项目评审并给总门禁", True),
    ("帮我看看这个 skill 写得行不行，值不值得装", False),
    ("验证这套评审 skill 本身", False),
    ("比较本地 qNEHVI 和 BoTorch 是否等价", False),
    ("三 seeds 能否宣称性能提升", False),
]


def decide(query):
    out = subprocess.run([PY, ROUTER, "route", "--agent", "dsh", query], capture_output=True, text=True, encoding="utf-8", errors="replace")
    for line in (out.stdout or "").splitlines():
        m = re.match(r"\s*1\.\s+(\S+)\s+\[", line)
        if m: return m.group(1)
    return "none"


def main():
    decisions = []
    for query, should in CASES:
        first = decide(query)
        decisions.append({"query": query, "should_trigger": should, "decisions": [first]})
        print(f"{'TRIGGER ' if should else 'NEAR-MISS'} | first={first:<32} | {query}")
    path = Path("router-decisions.json")
    path.write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n--- grading {TARGET} with criticagent grade_triggers.py ---")
    result = subprocess.run([PY, GRADER, f"D:/agent-library/catalog/{TARGET}", str(path), "--summary-only", "--report-only"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(result.stdout or ""); print(result.stderr or "")
    return 0


if __name__ == "__main__": raise SystemExit(main())
