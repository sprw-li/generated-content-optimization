#!/usr/bin/env python3
"""Adversarial probes against the v3.5 contract: try to LAUNDER a bad report past the validator.

Each probe builds a report that a human reviewer would reject, and asks whether the
machine lets it through. A probe that PASSES validation is a HOLE in our own rules.
"""
import json, subprocess, sys, tempfile
from pathlib import Path

V35 = Path(__file__).resolve().parent
VALIDATOR = V35 / "shared" / "validate_report.py"


def base(resolve_root="."):
    return {
        "schema_version": "3.6",
        "project": {"name": "probe", "type": "engineering", "snapshot": "probe", "evidence_scope": "single-project"},
        "scope": {"inputs": ["probe"], "exclusions": [], "readonly": True,
                  "coverage_note": "adversarial probe", "resolve_root": resolve_root,
                  "source_hashes": {"algorithm": "sha256", "inputs": ["."], "before": "a", "after": "b", "stable": True, "mode": "two-invocation", "before_at": "T0", "after_at": "T1"}},
        "findings": [], "github_sources": [], "literature_sources": [], "comparisons": [],
        "gate": "ACCEPT",
    }


def finding(fid="DEF-001", **kw):
    f = {"id": fid, "statement": "claimed pass", "status": "PASS", "execution": "EXECUTED_PASS",
         "severity": "info", "enforcement": "test",
         "evidence": [{"locator": "p.py:1-3", "observation": "alpha_handler returns gamma_value"}],
         "remediation": {"action": "", "acceptance": "", "verification": "NOT_RUN"}}
    f.update(kw)
    return f


PROBES = []


def probe(name, why):
    def deco(fn):
        PROBES.append((name, why, fn)); return fn
    return deco


@probe("semantic_only 洗白全部引用",
       "若每条 evidence 都声明 semantic_only + 任意 anchor_note，锚定检查是否被整体系数绕过")
def p1(root):
    r = base(root)
    f = finding()
    f["evidence"] = [{"locator": "p.py:1-3", "observation": "完全无关的伪造文字",
                      "semantic_only": True, "anchor_note": "随便写一句"}]
    r["findings"] = [f]
    return r


@probe("省略 resolve_root 逃避全部文件级检查",
       "council 指出：不写 resolve_root，则文件存在性/行号/锚定检查全部静默失效")
def p8(root):
    r = base(None)
    r["scope"].pop("resolve_root", None)
    r["findings"] = [finding(evidence=[{"locator": "totally/fabricated/file.py:99999", "observation": "alpha_handler gamma_value"}])]
    return r


@probe("URL 冒充 file:line 满足 enforcement",
       "council 指出：enforcement=code/test 只查冒号数字，URL 可满足且跳过全部检查")
def p9(root):
    r = base(root)
    r["findings"] = [finding(evidence=[{"locator": "https://example.com/fake_evidence:12",
                                        "observation": "authoritative implementation proves correctness"}])]
    return r


@probe("CONDITIONAL 掩盖未解决 medium FAIL",
       "council 指出：unresolved 只筛 blocker/high，medium FAIL 可用 CONDITIONAL 掩盖")
def p10(root):
    r = base(root)
    r["findings"] = [finding(),
                     finding(fid="DEF-002", status="FAIL", execution="EXECUTED_FAIL", severity="medium", enforcement=None,
                             evidence=[{"locator": "p.py:1-4", "observation": "alpha_handler computes gamma_value"}],
                             remediation={"action": "fix `p.py:1-4`", "acceptance": "py -3 -m pytest", "verification": "NOT_RUN"})]
    r["gate"] = "CONDITIONAL"
    return r


@probe("REJECTED 收纳高危缺陷",
       "council 指出：把 high FAIL 改写成 REJECTED 即可从 blocker 统计中消失")
def p11(root):
    r = base(root)
    r["findings"] = [finding(),
                     finding(fid="DEF-002", status="REJECTED", execution="NOT_RUN", severity="high", enforcement=None,
                             evidence=[],
                             rejected_reason="已 grep 全库并在 `src/defs.py` 下逐文件查找该符号，任何窗口均无匹配",
                             remediation={"action": "", "acceptance": "", "verification": "NOT_RUN"})]
    return r


@probe("RESOLVED 自报无产物",
       "council 指出：RESOLVED 只查字段存在，不要求磁盘上有真实运行产物")
def p12(root):
    r = base(root)
    r["findings"] = [finding(),
                     finding(fid="DEF-002", status="PASS", execution="EXECUTED_PASS", severity="high", enforcement="test",
                             evidence=[{"locator": "p.py:1-4", "observation": "alpha_handler computes gamma_value"}],
                             remediation={"action": "fix `p.py:1-4`", "acceptance": "py -3 -m pytest", "verification": "RESOLVED",
                                          "acceptance_result": {"command": "py -3 -m pytest", "exit_code": 0,
                                                                "observed": "self-declared pass, nothing on disk"}})]
    return r


@probe("source_hashes 单次自证",
       "council 指出：before/after 同一进程背靠背计算，stable 恒真，不证明审查期间无写入")
def p13(root):
    r = base(root)
    r["findings"] = [finding()]
    r["scope"]["source_hashes"] = {"algorithm": "sha256", "inputs": [root], "before": "aaa", "after": "aaa", "stable": True}
    return r


@probe("source_hashes 不覆盖 scope.inputs",
       "council 指出：指纹可对任意输入计算，不必覆盖报告声称读过的输入")
def p14(root):
    r = base(root)
    r["findings"] = [finding()]
    r["scope"]["inputs"] = ["D:/some/other/place/entirely"]
    r["scope"]["source_hashes"] = {"algorithm": "sha256", "inputs": [root], "before": "a", "after": "b",
                                   "stable": True, "mode": "two-invocation", "before_at": "T0", "after_at": "T1"}
    return r


@probe("novelty 用无关引用满足",
       "claim_class=novelty 只要求存在任一外部来源，无关引用是否也算")
def p2(root):
    r = base(root)
    f = finding()
    f["claim_class"] = "novelty"
    r["findings"] = [f]
    r["github_sources"] = [{"level": "topic-only", "url": "https://example.com/irrelevant",
                            "version": "n/a", "retrieved": "2026-11-15", "read_status": "summary-only"}]
    return r


@probe("behavior 计数与执行证据不符",
       "verdict=install 时是否核对 execution_evidence 指向的文件真的存在")
def p3(root):
    r = base(root)
    r["findings"] = [finding()]
    r["behavior_evidence"] = {"cases_total": 3, "with_skill_pass": 3, "without_skill_pass": 0,
                              "trigger_correct": 3, "trigger_total": 3, "verdict": "install",
                              "execution_evidence": ["reports/definitely-missing-file.json"],
                              "source_hashes_stable": True, "baseline_isolated": True,
                              "case_tags": ["a", "b", "c"]}
    return r


@probe("case_tags 用同义异名冒充多样",
       "tags 只要字符串不同即可通过，不检查是否真的不同场景")
def p4(root):
    r = base(root)
    r["findings"] = [finding()]
    r["behavior_evidence"] = {"cases_total": 3, "with_skill_pass": 3, "without_skill_pass": 0,
                              "verdict": "install", "execution_evidence": ["x"],
                              "source_hashes_stable": True, "baseline_isolated": True,
                              "case_tags": ["recall", "recall ", "recall\t"]}
    return r


@probe("na_reason 用长而复读的文字凑数",
       "30 字符门槛是否可用无信息文字满足")
def p5(root):
    r = base(root)
    f = finding(status="N/A", execution="NOT_APPLICABLE", enforcement=None,
                na_reason="这里填足够多的字符凑过长度检查但是完全没有说明任何理由内容")
    r["findings"] = [f]
    r["gate"] = "INCOMPLETE"
    return r


@probe("rejected 用不含搜索动作的长理由",
       "rejected_reason 是否只查长度与关键词，可被『检索』二字满足")
def p6(root):
    r = base(root)
    f = finding(fid="DEF-001", status="REJECTED", execution="NOT_RUN", enforcement=None, evidence=[],
                rejected_reason="我已经充分检索过了但是这一段文字并没有指出究竟查了哪个位置所以无法核查")
    r["findings"] = [f]
    r["gate"] = "REJECT"
    return r


@probe("anchoring 只共享一个常见词即可",
       "shared token 门槛=1，观察与所引行共享一个通用词即算锚定")
def p7(root):
    r = base(root)
    f = finding()
    f["evidence"] = [{"locator": "p.py:1-3", "observation": "this file has value but nothing else matters"}]
    r["findings"] = [f]
    return r


def main():
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "p.py").write_text("def alpha_handler():\n    value = compute()\n    gamma_value = value\n    return gamma_value\n", encoding="utf-8")
        holes, lines = [], []
        for name, why, fn in PROBES:
            r = fn(tmp)
            p = Path(tmp) / "probe.json"
            p.write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
            res = subprocess.run([sys.executable, str(VALIDATOR), str(p)], capture_output=True, text=True,
                                 encoding="utf-8", errors="replace")
            leaked = res.returncode == 0
            detail = [l for l in (res.stdout + res.stderr).splitlines() if l.startswith("-")]
            lines.append(f"[{'HOLE' if leaked else 'blocked'}] {name}")
            lines.append(f"        why tried: {why}")
            lines.append(f"        reason: {detail[0][2:][:140] if detail else ('LEAKED' if leaked else '(no detail)')}")
            lines.append("")
            if leaked: holes.append(name)
            print(f"[{'HOLE' if leaked else 'blocked'}] probe {len(lines)//4} of {len(PROBES)}")
        lines.append(f"probes: {len(PROBES)}  holes leaked: {len(holes)}")
        for h in holes: lines.append(f"  LEAK: {h}")
        report_dir = Path(__file__).resolve().parent
        if report_dir.name != "integration": report_dir = report_dir / "integration"
        report = report_dir / "adversarial-probe-report.txt"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"probes: {len(PROBES)}  holes leaked: {len(holes)}")
        print(f"full report: {report}")
        return 0


if __name__ == "__main__": raise SystemExit(main())
