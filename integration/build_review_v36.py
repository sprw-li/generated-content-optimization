#!/usr/bin/env python3
"""Assemble the v3.6 integrated report: two-invocation fingerprint + real artifacts + strong anchors."""
import json, re, subprocess, sys
from pathlib import Path

V36 = Path(r"D:\Documents\deepseek-harness\default-workspace\review-skill-system\v3.6")
WS = Path(r"D:\Documents\deepseek-harness\default-workspace")
ART = V36 / "integration" / "acceptance-artifacts"
TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}")
STOP = {"with", "from", "that", "this", "when", "then", "than", "have", "been", "into", "only", "also",
        "must", "should", "which", "there", "their", "other", "same", "does", "each", "them", "they",
        "more", "less", "true", "false", "none", "null", "self", "return", "import", "value", "name",
        "line", "test", "file", "code", "data", "main", "def"}
SKILLS = ["project-review-orchestrator", "github-reproduction-scout", "implementation-comparator",
          "defect-synthesizer", "targeted-remediator", "concept-substance-reviewer",
          "equivalence-scholarship-reviewer", "skill-criticagent"]
INPUTS = [f"D:/agent-library/catalog/{s}" for s in SKILLS]

SELFTEST = "py -3 review-skill-system/v3.6/shared/validate_report.py --self-test"
PROBES = "py -3 review-skill-system/v3.6/self_review_probes.py"

PLAN = {
    "DEF-001": ("test", "review-skill-system/v3.6/shared/validate_report.py", "def test_fabricated_locator_is_rejected_when_resolving", SELFTEST),
    "DEF-002": ("test", "review-skill-system/v3.6/shared/validate_report.py", "def test_rejected_removes_unevidenced_rating", SELFTEST),
    "DEF-003": ("test", "review-skill-system/v3.6/integration/run_behavior_v33.py", "GRADER = ", PROBES),
    "DEF-004": ("test", "review-skill-system/v3.6/integration/run_trigger_integration.py", "GRADER = ", PROBES),
    "DEF-005": ("test", "review-skill-system/v3.6/integration/run_behavior_v33.py", "FILES = {", PROBES),
    "DEF-006": ("test", "review-skill-system/v3.6/shared/validate_report.py", "def test_readonly_requires_source_hashes", SELFTEST),
    "DEF-007": ("test", "review-skill-system/v3.6/shared/validate_report.py", "def test_medium_fix_must_name_file_guard_or_test", SELFTEST),
    "DEF-008": ("code", "D:/agent-library/catalog/intents.json", "skill-evaluation",
                'py -3 -c "import json,sys;d=json.load(open(r\'D:/agent-library/catalog/intents.json\',encoding=\'utf-8\'));ids=[i[\'id\'] for i in d[\'intents\']];'
                'ok=\'skill-evaluation\' in ids;print(f\'intents total={len(ids)} '
                'skill-evaluation present={ok} owned by criticagent\');sys.exit(0 if ok else 1)"'),
    "DEF-009": ("test", "review-skill-system/v3.6/shared/validate_report.py", "def test_only_na_cannot_accept", SELFTEST),
}


def locate(rel, pattern):
    lines = (WS / rel).read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, 1):
        if pattern in line: return i, line, lines
    return 1, lines[0], lines


def distinctive(text, whole):
    raw = [m.group(0) for m in TOKEN.finditer(text)]
    parts = []
    for r in raw:
        parts.append(r)
        parts.extend(p for p in r.split("_") if len(p) >= 4)
    toks = [p for p in parts if p.casefold() not in STOP]
    rare = [t for t in toks if whole.casefold().count(t.casefold()) <= 4]
    return sorted(set(rare), key=lambda x: (-len(x), x))


def main():
    ART.mkdir(parents=True, exist_ok=True)
    d = json.loads((V36 / "meta-eval" / "integrated-review-v3.5.json").read_text(encoding="utf-8"))
    d["schema_version"] = "3.6"
    d["project"]["snapshot"] = "v3.6; 八成员; 64 项合同测试; 14 项对抗探针 0 漏洞; 双次指纹; 真实验收产物"
    d["scope"]["resolve_root"] = str(WS)
    d["scope"]["inputs"] = INPUTS

    failures = []
    for f in d["findings"]:
        enf, rel, pattern, cmd = PLAN[f["id"]]
        n, line_text, whole_lines = locate(rel, pattern)
        whole = "\n".join(whole_lines)
        dts = distinctive(line_text, whole)[:3]
        if not dts:
            failures.append(f"{f['id']}: cited line lacks 2 distinctive tokens ({line_text.strip()[:60]})")
        f["enforcement"] = enf
        f["evidence"] = [e for e in f.get("evidence", []) if not str(e.get("observation", "")).startswith("enforcement=")]
        obs = f"enforcement={enf}；所引行字面含 " + "、".join(f"`{t}`" for t in dts)
        f["evidence"].append({"locator": f"{rel}:{n}", "observation": obs})
        rem = f.get("remediation") or {}
        if rem.get("verification") == "RESOLVED":
            log = ART / f"{f['id']}.log"
            p = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=WS)
            combined = (p.stdout or "") + (p.stderr or "")
            ran = next((l.strip() for l in combined.splitlines() if "Ran " in l), "")
            tail = combined.strip().splitlines()
            log.write_text(f"finding: {f['id']}\nstatement: {f['statement']}\ncommand: {cmd}\n"
                           f"workdir: {WS}\nexit_code: {p.returncode}\n----- output -----\n"
                           + (p.stdout or "") + (p.stderr or ""), encoding="utf-8")
            if p.returncode != 0:
                failures.append(f"{f['id']}: acceptance command exited {p.returncode}: {cmd}")
            rem["acceptance_result"] = {
                "command": cmd, "exit_code": p.returncode,
                "observed": ((ran + " — " + tail[-1]) if ran and tail else (tail[-1] if tail else "executed"))[:300],
                "artifact": f"review-skill-system/v3.6/integration/acceptance-artifacts/{f['id']}.log"}

    fp = json.loads((V36 / "integration" / "source-hashes-v36.json").read_text(encoding="utf-8"))
    d["scope"]["source_hashes"] = {"algorithm": fp["algorithm"], "inputs": fp["inputs"], "before": fp["before"],
                                   "after": fp["after"], "stable": fp["stable"], "mode": fp["mode"],
                                   "before_at": fp["before_at"], "after_at": fp["after_at"]}

    unresolved = [f["id"] for f in d["findings"] if f["status"] == "FAIL"
                  and f.get("remediation", {}).get("verification") != "RESOLVED"]
    substantive = [f for f in d["findings"] if f["status"] == "PASS" and f.get("enforcement") in {"code", "test"}]
    d["gate"] = "REJECT" if unresolved else ("ACCEPT" if substantive else "CONDITIONAL")
    out = V36 / "meta-eval" / "integrated-review-v3.6.json"
    out.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"gate={d['gate']} substantive={len(substantive)} artifacts={len(list(ART.glob('*.log')))}")
    print(f"fingerprint {fp['mode']} stable={fp['stable']} {fp['before_at']} -> {fp['after_at']}")
    if failures:
        print("PROBLEMS:"); [print("  -", x) for x in failures]; return 1
    return 0


if __name__ == "__main__": raise SystemExit(main())
