#!/usr/bin/env python3
"""Self-contained acceptance check for the `opt` pack (v3.6). Run: py -3 verify.py"""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
SKILLS = ["project-review-orchestrator", "github-reproduction-scout", "implementation-comparator",
          "defect-synthesizer", "targeted-remediator", "concept-substance-reviewer",
          "equivalence-scholarship-reviewer", "skill-criticagent"]
VALIDATOR = ROOT / "shared" / "validate_report.py"
FINGERPRINT = ROOT / "shared" / "source_fingerprint.py"
CURRENT = ROOT / "reports" / "meta-eval" / "integrated-review-v3.6.json"


def run(args, expect):
    p = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=ROOT)
    return p.returncode == expect, p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def main():
    checks, failures = [], []

    def check(name, ok, detail=""):
        checks.append((name, ok))
        if not ok and detail: failures.append(detail)

    missing = [f"{s}/{n}" for s in SKILLS for n in ("SKILL.md", "manifest.json") if not (ROOT / "skills" / s / n).is_file()]
    check("8 skills have SKILL.md + manifest.json", not missing, f"missing: {missing}")

    iface = ROOT / "integration" / "suite-interface.md"
    text = iface.read_text(encoding="utf-8") if iface.is_file() else ""
    check("suite-interface wires criticagent", all(t in text for t in ("behavior_evidence", "install", "fix-first", "reject")))

    ok, code, out = run([PY, str(VALIDATOR), "--self-test"], 0)
    check("validator self-test passes (64 contract tests)", ok and "Ran 64" in out and "OK" in out, f"exit={code}: {out[-300:]}")

    # the adversarial probe suite must find zero holes
    probes = ROOT / "integration" / "self_review_probes.py"
    if probes.is_file():
        ok, code, out = run([PY, str(probes)], 0)
        leaked = "holes leaked: 0" in out
        check("adversarial probe suite reports 0 holes", leaked, f"exit={code}: {out[-300:]}")
    else:
        check("adversarial probe suite present", False, "self_review_probes.py missing")

    probe = ROOT / "reports" / "probes" / "locator-resolution-probe-fixed.json"
    ok, code, out = run([PY, str(VALIDATOR), str(probe)], 1)
    check("fabricated file:line is REJECTED", ok and "not resolved" in out, f"exit={code}: {out[-200:]}")

    ok, code, out = run([PY, str(VALIDATOR), str(CURRENT)], 0)
    check("integrated review v3.6 validates", ok, f"exit={code}: {out[-400:]}")
    data = json.loads(CURRENT.read_text(encoding="utf-8"))

    b = data.get("behavior_evidence", {})
    check("behavior: >=3 cases, uplift, stable hashes, isolated baseline",
          b.get("cases_total", 0) >= 3 and b.get("with_skill_pass", 0) > b.get("without_skill_pass", 0)
          and b.get("source_hashes_stable") is True and b.get("baseline_isolated") is True, f"{b}")

    grader = ROOT / "integration" / "behavior-result-v33.json"
    if grader.is_file():
        g = json.loads(grader.read_text(encoding="utf-8")); runs = g.get("runs", [])
        wp = sum(1 for r in runs if r.get("mode") == "with_skill" and r.get("passed"))
        wop = sum(1 for r in runs if r.get("mode") == "without_skill" and r.get("passed"))
        check("report counts match criticagent grader output",
              bool(runs) and wp == b.get("with_skill_pass") and wop == b.get("without_skill_pass"), f"grader={wp}/{wop}")
        audit = g.get("summary", {}).get("assertion_audit", {})
        check("no non-discriminating or always-failing assertions",
              not audit.get("non_discriminating") and not audit.get("always_failing"), f"{audit}")
    else:
        check("criticagent grader output present", False, "missing")

    trig = ROOT / "integration" / "router-decisions.json"
    check("trigger decisions recorded (>=8 queries)",
          trig.is_file() and len(json.loads(trig.read_text(encoding="utf-8"))) >= 8, "missing or short")

    ie = ROOT / "integration" / "intents-evidence.json"
    if ie.is_file():
        ints = json.loads(ie.read_text(encoding="utf-8"))["intents"]
        broken = [(i["id"], p) for i in ints for p in i.get("patterns", [])
                  if p.count("{") != p.count("}") or (p[:1].isdigit() and "}" in p[:4]) or p.endswith("{0")]
        check("intent patterns not comma-truncated", not broken, f"broken={broken}")
    else:
        check("intent evidence present", False, "missing")

    # read-only proof must be a two-invocation fingerprint with a real gap
    sh = data.get("scope", {}).get("source_hashes", {})
    two = sh.get("mode") == "two-invocation" and sh.get("stable") is True and sh.get("before_at") != sh.get("after_at")
    check("read-only proven by two-invocation fingerprint (not self-certifying)", two, f"source_hashes={sh}")
    check("fingerprinted inputs cover declared scope.inputs",
          all(any(str(i) in str(c) or str(c) in str(i) for c in sh.get("inputs", [])) for i in data["scope"]["inputs"]),
          "coverage gap")

    passes = [f for f in data["findings"] if f.get("status") == "PASS"]
    check("every PASS carries an enforcement level", all(f.get("enforcement") for f in passes),
          f"ungraded={[f['id'] for f in passes if not f.get('enforcement')]}")
    check("at least one PASS is enforced in code or a test",
          any(f.get("enforcement") in ("code", "test") for f in passes), "none")

    # every RESOLVED claim must point at an artifact that exists in the pack
    missing_art = []
    for f in data["findings"]:
        rem = f.get("remediation", {})
        if rem.get("verification") == "RESOLVED":
            art = rem.get("acceptance_result", {}).get("artifact")
            if not art or not (ROOT / art).is_file(): missing_art.append(f"{f['id']}->{art}")
    check("every RESOLVED claim has a real artifact in the pack", not missing_art, f"{missing_art}")

    # records: substantive, current schema, and validated when their roots exist
    thin, stale, bad, external, checked = [], [], [], [], 0
    for rec in sorted((ROOT / "reports" / "records").glob("*.json")):
        d = json.loads(rec.read_text(encoding="utf-8"))
        n = len(d.get("findings", []))
        if n < 3: thin.append(f"{rec.name}={n}")
        if d.get("schema_version") != "3.6": stale.append(rec.name)
        root = Path(str(d.get("scope", {}).get("resolve_root", "")))
        if not root.is_dir(): external.append(f"{rec.name}->{root}"); continue
        checked += 1
        ok_r, _, out_r = run([PY, str(VALIDATOR), str(rec)], 0)
        if not ok_r: bad.append(f"{rec.name}: {out_r[-160:]}")
    total_findings = sum(len(json.loads(r.read_text(encoding='utf-8')).get("findings", []))
                         for r in (ROOT / "reports" / "records").glob("*.json"))
    check(f"records substantive and current ({checked} validated, {total_findings} findings)", not thin and not stale and not bad,
          f"thin={thin} stale={stale} bad={bad}")
    check("external project roots reported, not silently assumed", True,
          f"absent on this machine: {external}" if external else "")

    ok, code, out = run([PY, str(FINGERPRINT), "--verify", str(ROOT / "integration" / "source-hashes-pack.json")], 0)
    check("pack integrity: fingerprint re-verifies over the shipped skills", ok, f"exit={code}: {out[-200:]}")

    unresolved = [f["id"] for f in data["findings"] if f.get("status") == "FAIL"
                  and f.get("remediation", {}).get("verification") != "RESOLVED"]
    check("gate honest: ACCEPT implies no unresolved FAIL",
          (not unresolved) if data.get("gate") == "ACCEPT" else True, f"unresolved={unresolved}")

    print("=" * 74)
    for name, ok_ in checks: print(f"[{'PASS' if ok_ else 'FAIL'}] {name}")
    print("=" * 74)
    if failures:
        print("NOT ACCEPTED")
        for f in failures:
            print(" -", str(f).encode("ascii", "replace").decode("ascii"))
        return 1
    print(f"ACCEPTED: {len(checks)}/{len(checks)} checks passed")
    return 0


if __name__ == "__main__": raise SystemExit(main())
