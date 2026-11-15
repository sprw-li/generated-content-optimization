#!/usr/bin/env python3
"""Validate report structure and state/gate consistency; never judges science."""
import argparse, copy, json, re, tempfile, unittest
from pathlib import Path

STATUSES = {"PASS", "FAIL", "UNVERIFIED", "N/A", "REJECTED"}
EXECUTIONS = {"EXECUTED_PASS", "EXECUTED_FAIL", "ENVIRONMENT_BLOCKED", "NOT_RUN", "NOT_APPLICABLE"}
TYPES = {"concept", "engineering", "experiment", "reproduction", "theory", "mixed", "planning"}
SEVERITIES = {"blocker", "high", "medium", "low", "info"}
CLAIM_KINDS = {"present", "absent", "other"}
NAMED_FIX = re.compile(r"(`[^`]+`|[A-Za-z0-9_./\\-]+\.\w+:?\d*|\bpy -3\b|\bpytest\b|\btest_\w+|npm run|pwsh|powershell)", re.I)
EXEC_CMD = re.compile(r"^\s*(py -3|python|pytest|npm|node|pwsh|powershell|git|uv|\.venv[\\/])", re.I)
GATES = {"ACCEPT", "CONDITIONAL", "REJECT", "INCOMPLETE"}
VERIFY = {"RESOLVED", "NOT_RUN", "FAILED", "ENVIRONMENT_BLOCKED"}
SOURCES = {"official-reference", "independent-reproduction", "comparable-method", "topic-only"}
COMPARISONS = {"MATCH", "DIFF", "INCOMPARABLE", "UNVERIFIED"}
LITERATURE_TYPES = {"arxiv", "google-scholar", "patent", "conference-proceeding", "technical-report", "blog-post"}
LITERATURE_RELEVANCE = {"core", "related", "peripheral"}
MILESTONE_STATUS = {"completed", "delayed", "at-risk", "planned"}
QUALITY_GRADES = {"A", "B", "C", "D", "F"}
BEHAVIOR_VERDICTS = {"install", "fix-first", "reject", "not_applicable"}
ENFORCEMENT = {"code", "test", "prose", "not_applicable"}


MIN_NA_REASON = 30
MIN_REJECTED_REASON = 30
CLAIM_CLASSES = {"defect", "novelty", "equivalence", "capability", "other"}
ANCHOR_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,}|[0-9][0-9.]*")
ANCHOR_STOP = {"with", "from", "that", "this", "when", "then", "than", "have", "been", "into",
               "only", "also", "must", "should", "which", "there", "their", "other", "same",
               "does", "each", "them", "they", "more", "less", "true", "false", "none", "null"}


def anchor_tokens(text):
    return {m.group(0).casefold() for m in ANCHOR_TOKEN.finditer(text or "")
            if len(m.group(0)) >= 4 and m.group(0).casefold() not in ANCHOR_STOP}


def anchor_strength(observation, body, full_file_text=None):
    """Return (shared_count, has_rare_shared). A single shared common word is not anchoring."""
    obs, src = anchor_tokens(observation), anchor_tokens(body)
    shared = obs & src
    if not shared: return 0, False
    corpus = (full_file_text or body).casefold()
    rare = any(corpus.count(t) <= 2 for t in shared)
    return len(shared), rare


def _locator_path(locator, resolve_root):
    if not resolve_root or not isinstance(locator, str): return None
    m = re.match(r"^(.+?):(\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*)$", locator)
    if not m: return None
    p = Path(m.group(1))
    path = p if p.is_absolute() else Path(resolve_root) / m.group(1)
    return (path, m.group(2)) if path.is_file() else None


def cited_text(locator, resolve_root):
    """Return the literal text of the cited lines, or None if not a resolvable file:line."""
    got = _locator_path(locator, resolve_root)
    if not got: return None
    path, rng = got
    try: lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError: return None
    out = []
    for part in rng.split(","):
        lo, _, hi = part.partition("-")
        lo = int(lo); hi = int(hi) if hi else lo
        out.extend(lines[max(0, lo - 1):hi])
    return "\n".join(out)


def cited_file_text(locator, resolve_root):
    """Return the WHOLE cited file (for rarity scoring), or None."""
    got = _locator_path(locator, resolve_root)
    if not got: return None
    try: return got[0].read_text(encoding="utf-8", errors="replace")
    except OSError: return None


def resolve_locator(locator, resolve_root):
    """Resolve a path[:line[-line]][,line...] locator against resolve_root. Returns error strings."""
    if not resolve_root or not isinstance(locator, str): return []
    if locator.startswith(("http://", "https://")): return []
    # strip multi-range suffixes: file.py:12-34,56-78 -> file.py with ranges [[12,34],[56,78]]
    ranges = []
    body = locator.strip()
    m = re.match(r"^(.+?):(\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*)$", body)
    if m:
        raw = m.group(1)
        for part in m.group(2).split(","):
            lo, _, hi = part.partition("-")
            ranges.append((int(lo), int(hi) if hi else None))
    else:
        raw = body
        if " " in raw or ("/" not in raw and "\\" not in raw): return []
    candidate = Path(raw)
    path = candidate if candidate.is_absolute() else Path(resolve_root) / raw
    if not path.is_file(): return [f"evidence locator not resolved: {raw} (missing under resolve_root)"]
    if not ranges: return []
    try:
        total = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError as exc:
        return [f"evidence locator unreadable: {raw} ({exc})"]
    errors = []
    for lo, hi in ranges:
        if lo < 1 or lo > total: errors.append(f"evidence locator line out of range: {raw}:{lo} (file has {total} lines)")
        if hi and hi > total: errors.append(f"evidence locator end line out of range: {raw}:{hi} (file has {total} lines)")
    return errors


def validate(report):
    errors = []
    if not isinstance(report, dict): return ["report must be an object"]
    if report.get("schema_version") != "3.6": errors.append("schema_version must be 3.6")
    project = report.get("project", {})
    if not isinstance(project, dict): return errors + ["project must be an object"]
    for key in ("name", "snapshot"):
        if not isinstance(project.get(key), str) or not project[key].strip(): errors.append(f"project.{key} required")
    if project.get("type") not in TYPES: errors.append("project.type invalid")
    if project.get("evidence_scope") not in {"single-project", "isolated-multi-project"}: errors.append("project.evidence_scope required")
    scope = report.get("scope", {})
    if not isinstance(scope, dict): errors.append("scope required")
    else:
        for key in ("inputs", "exclusions"):
            if not isinstance(scope.get(key), list) or not all(isinstance(x, str) and x.strip() for x in scope[key]):
                errors.append(f"scope.{key} must be a string array")
        if not scope.get("inputs"): errors.append("scope.inputs cannot be empty")
        if not isinstance(scope.get("readonly"), bool): errors.append("scope.readonly must be explicit true/false")
        if not scope.get("coverage_note"): errors.append("scope.coverage_note required")
        if scope.get("resolve_root") is not None and (not isinstance(scope["resolve_root"], str) or not scope["resolve_root"].strip()):
            errors.append("scope.resolve_root must be a non-empty string when present")
        if scope.get("readonly") is True:
            sh = scope.get("source_hashes")
            if not isinstance(sh, dict):
                errors.append("scope.source_hashes required when readonly is true (run source_fingerprint.py)")
            else:
                for key in ("algorithm", "before", "after", "stable"):
                    if sh.get(key) in (None, ""): errors.append(f"scope.source_hashes.{key} required")
                if sh.get("stable") is not True:
                    errors.append("readonly review requires scope.source_hashes.stable=true (drift detected)")
                if sh.get("mode") not in {"single-run", "two-invocation"}:
                    errors.append("scope.source_hashes.mode required: single-run (back-to-back, self-certifying) "
                                  "or two-invocation (fingerprint taken before and after the review)")
                if sh.get("mode") == "two-invocation":
                    if sh.get("before_at") == sh.get("after_at") or not sh.get("before_at") or not sh.get("after_at"):
                        errors.append("two-invocation source_hashes require distinct before_at/after_at timestamps")
                # the fingerprinted inputs must cover what the review claims to have read
                covered = [str(x) for x in (sh.get("inputs") or [])]
                rr = scope.get("resolve_root")

                def norm(pth):
                    p = Path(str(pth))
                    if not p.is_absolute() and rr: p = Path(str(rr)) / str(pth)
                    try: return str(p.resolve()).replace("\\", "/").rstrip("/").casefold()
                    except OSError: return str(p).replace("\\", "/").rstrip("/").casefold()

                def within(inp, cov):
                    i, c = norm(inp), norm(cov)
                    return i == c or i.startswith(c + "/") or c.startswith(i + "/")

                for inp in (scope.get("inputs") or []):
                    if not any(within(inp, c) for c in covered):
                        errors.append(f"source_hashes.inputs does not cover scope.inputs entry: {inp}")
    if report.get("gate") not in GATES: errors.append("invalid gate")
    findings = report.get("findings")
    if not isinstance(findings, list): return errors + ["findings must be a list"]
    # fail-closed: citing local file:line without declaring a resolution root makes every
    # file-level check (existence, line range, anchoring) silently skippable.
    uses_local_fileline = False
    for f in findings:
        if not isinstance(f, dict): continue
        for e in f.get("evidence", []):
            if not isinstance(e, dict): continue
            loc = str(e.get("locator", ""))
            if loc.startswith(("http://", "https://")): continue
            if re.search(r":\d+", loc): uses_local_fileline = True
    if uses_local_fileline and not (isinstance(scope, dict) and scope.get("resolve_root")):
        errors.append("scope.resolve_root is required: the report cites local file:line evidence, and without a "
                      "resolution root no existence/line-range/anchoring check can run")
    ids = set()
    for i, finding in enumerate(findings):
        p = f"findings[{i}]"
        if not isinstance(finding, dict): errors.append(f"{p} must be object"); continue
        fid = finding.get("id", "")
        if not re.fullmatch(r"DEF-[0-9]+", fid): errors.append(f"{p}.id invalid")
        if fid in ids: errors.append(f"{p}.id duplicate")
        ids.add(fid)
        status, execution = finding.get("status"), finding.get("execution")
        if status not in STATUSES: errors.append(f"{p}.status invalid")
        if execution not in EXECUTIONS: errors.append(f"{p}.execution invalid")
        if finding.get("severity") not in SEVERITIES: errors.append(f"{p}.severity invalid")
        if not finding.get("statement"): errors.append(f"{p}.statement required")
        evidence = finding.get("evidence")
        if not isinstance(evidence, list): errors.append(f"{p}.evidence must be array"); evidence = []
        if status in {"PASS", "FAIL"} and not evidence: errors.append(f"{p} PASS/FAIL requires evidence")
        if status == "N/A" and not finding.get("na_reason"):
            errors.append(f"{p} N/A requires na_reason")
        elif status == "N/A" and len(str(finding.get("na_reason") or "").strip()) < MIN_NA_REASON:
            errors.append(f"{p} na_reason too short (<{MIN_NA_REASON} chars): say which check does not apply and why")
        expected = {"PASS": "EXECUTED_PASS", "FAIL": "EXECUTED_FAIL", "N/A": "NOT_APPLICABLE"}
        if status in expected and execution != expected[status]: errors.append(f"{p} {status} execution conflict")
        if status == "UNVERIFIED" and execution not in {"ENVIRONMENT_BLOCKED", "NOT_RUN"}: errors.append(f"{p} UNVERIFIED execution conflict")
        if status == "REJECTED":
            reason = str(finding.get("rejected_reason") or "").strip()
            if not reason: errors.append(f"{p} REJECTED requires rejected_reason")
            elif len(reason) < MIN_REJECTED_REASON:
                errors.append(f"{p} rejected_reason too short (<{MIN_REJECTED_REASON} chars): state what was searched")
            elif not (finding.get("searched_scope") or re.search(r"`[^`]+`|[A-Za-z0-9_./\\-]+\.\w+|[A-Za-z0-9_]+[/\\]", reason)):
                errors.append(f"{p} rejected_reason must name a concrete search target (path/pattern/glob), "
                              f"not just say a search happened")
            if execution not in {"NOT_RUN", "ENVIRONMENT_BLOCKED"}:
                errors.append(f"{p} REJECTED means unevidenced guess; execution must be NOT_RUN or ENVIRONMENT_BLOCKED")
            if evidence: errors.append(f"{p} REJECTED must not carry evidence (it was removed as a guess)")
            if finding.get("severity") in {"blocker", "high"}:
                errors.append(f"{p} REJECTED must not carry blocker/high severity: a serious suspicion has to be "
                              f"resolved or evidenced, not removed from the counts")
        claim_kind = finding.get("claim_kind")
        if claim_kind is not None and claim_kind not in CLAIM_KINDS: errors.append(f"{p}.claim_kind invalid")
        if claim_kind == "absent":
            ss = finding.get("searched_scope")
            if not isinstance(ss, list) or not ss:
                errors.append(f"{p} absent claim requires searched_scope (which sources/patterns were searched)")
        claim_class = finding.get("claim_class")
        if claim_class is not None and claim_class not in CLAIM_CLASSES: errors.append(f"{p}.claim_class invalid")
        if claim_class in {"novelty", "equivalence"}:
            strong = [s for s in (report.get("github_sources", []) + report.get("literature_sources", []))
                      if isinstance(s, dict)
                      and s.get("level") != "topic-only"
                      and s.get("read_status") != "summary-only"
                      and s.get("type") != "blog-post"]
            if not strong:
                errors.append(f"{p} claim_class={claim_class} requires a closest-work citation that was actually read "
                              f"(level != topic-only, read_status != summary-only); a bare link is not comparable work")
        enforcement = finding.get("enforcement")
        if enforcement is not None and enforcement not in ENFORCEMENT: errors.append(f"{p}.enforcement invalid")
        if status == "PASS":
            if enforcement is None:
                errors.append(f"{p} PASS requires enforcement (code|test|prose|not_applicable): a label without substance is a FAIL")
            elif enforcement in {"code", "test"}:
                def real_fileline(e):
                    loc = str(e.get("locator", "")) if isinstance(e, dict) else ""
                    return bool(re.search(r":\d+", loc)) and not loc.startswith(("http://", "https://"))
                if not any(real_fileline(e) for e in evidence):
                    errors.append(f"{p} enforcement={enforcement} requires a LOCAL file:line evidence locator "
                                  f"(a URL is not source evidence and skips every file-level check)")
        for j, item in enumerate(evidence):
            if not isinstance(item, dict) or not item.get("locator") or not item.get("observation"):
                errors.append(f"{p}.evidence[{j}] incomplete")
                continue
            if isinstance(scope, dict) and scope.get("resolve_root"):
                for msg in resolve_locator(item["locator"], scope["resolve_root"]):
                    errors.append(f"{p}.evidence[{j}] {msg}")
                # anchoring: the cited lines must literally support the observation
                if not item.get("semantic_only"):
                    body = cited_text(item["locator"], scope["resolve_root"])
                    if body is not None:
                        obs = anchor_tokens(item["observation"])
                        src = anchor_tokens(body)
                        if src and not obs:
                            errors.append(f"{p}.evidence[{j}] observation carries no verifiable token — "
                                          f"quote an identifier/number from the cited lines, or set semantic_only + anchor_note")
                        elif obs and not (obs & src):
                            errors.append(f"{p}.evidence[{j}] observation is not anchored in the cited lines "
                                          f"(no shared token) — fix the locator, quote a token, or set semantic_only + anchor_note")
                        elif obs:
                            n, rare = anchor_strength(item["observation"], body, cited_file_text(item["locator"], scope["resolve_root"]))
                            if n < 2 and not rare:
                                errors.append(f"{p}.evidence[{j}] anchoring too weak: only 1 shared token and it is common in the file "
                                              f"— quote a distinctive identifier or cite the range that carries the claim")
                elif not item.get("anchor_note"):
                    errors.append(f"{p}.evidence[{j}] semantic_only requires anchor_note explaining why no literal anchor exists")
                elif len(str(item["anchor_note"]).strip()) < 40:
                    errors.append(f"{p}.evidence[{j}] anchor_note too short (<40 chars): explain what the observation describes "
                                  f"and why no literal token exists at the cited location")
        remediation = finding.get("remediation", {})
        if not isinstance(remediation, dict): remediation = {}; errors.append(f"{p}.remediation required")
        if remediation.get("verification") not in VERIFY: errors.append(f"{p}.remediation.verification invalid")
        if remediation.get("verification") == "RESOLVED":
            result = remediation.get("acceptance_result")
            if not isinstance(result, dict): errors.append(f"{p} RESOLVED requires acceptance_result")
            else:
                if not result.get("command"): errors.append(f"{p} acceptance_result.command required")
                if result.get("exit_code") != 0: errors.append(f"{p} RESOLVED exit_code must be 0")
                observed = str(result.get("observed") or "")
                if not observed: errors.append(f"{p} acceptance_result.observed required")
                elif len(observed) < 20:
                    errors.append(f"{p} acceptance_result.observed too short (<20 chars): quote what the run actually printed")
                # a self-declared pass is not evidence; require the run artifact to exist on disk
                if isinstance(scope, dict) and scope.get("resolve_root"):
                    art = result.get("artifact")
                    if not art:
                        errors.append(f"{p} RESOLVED requires acceptance_result.artifact (path to the run log/output) "
                                      f"when a resolve_root is declared; a self-declared pass is not evidence")
                    else:
                        pth = Path(str(art))
                        if not pth.is_absolute(): pth = Path(scope["resolve_root"]) / str(art)
                        if not pth.is_file():
                            errors.append(f"{p} acceptance_result.artifact does not exist: {art}")
        if finding.get("severity") in {"blocker", "high", "medium"} and status != "REJECTED":
            action = str(remediation.get("action") or "")
            if not NAMED_FIX.search(action):
                errors.append(f"{p} remediation.action must name a file, a guard or a test (not 'consider improving X')")
            acceptance = str(remediation.get("acceptance") or "")
            if not EXEC_CMD.match(acceptance):
                errors.append(f"{p} remediation.acceptance must be an executable command")
    sources = report.get("github_sources", [])
    if not isinstance(sources, list): errors.append("github_sources must be array"); sources = []
    for i, src in enumerate(sources):
        p = f"github_sources[{i}]"
        if not isinstance(src, dict): errors.append(f"{p} must be object"); continue
        if src.get("level") not in SOURCES: errors.append(f"{p}.level invalid")
        for key in ("url", "version", "retrieved", "read_status"):
            if not src.get(key): errors.append(f"{p}.{key} required")
        if src.get("read_status") not in {"summary-only", "text-read", "code-read", "executed"}: errors.append(f"{p}.read_status invalid")
        if src.get("level") == "independent-reproduction" and src.get("read_status") == "summary-only":
            errors.append(f"{p} independent-reproduction cannot be summary-only")
    literature = report.get("literature_sources", [])
    if not isinstance(literature, list): errors.append("literature_sources must be array"); literature = []
    for i, lit in enumerate(literature):
        p = f"literature_sources[{i}]"
        if not isinstance(lit, dict): errors.append(f"{p} must be object"); continue
        if lit.get("type") not in LITERATURE_TYPES: errors.append(f"{p}.type invalid")
        for key in ("title", "url_or_doi", "retrieved"):
            if not lit.get(key): errors.append(f"{p}.{key} required")
        if lit.get("relevance") and lit["relevance"] not in LITERATURE_RELEVANCE: errors.append(f"{p}.relevance invalid")
    comparisons = report.get("comparisons", [])
    if not isinstance(comparisons, list): errors.append("comparisons must be array"); comparisons = []
    for i, comparison in enumerate(comparisons):
        p = f"comparisons[{i}]"
        if not isinstance(comparison, dict): errors.append(f"{p} must be object"); continue
        if comparison.get("result") not in COMPARISONS: errors.append(f"{p}.result invalid")
        if not comparison.get("contract"): errors.append(f"{p}.contract required")
        if comparison.get("result") == "MATCH" and comparison.get("execution") != "EXECUTED_PASS": errors.append(f"{p} MATCH requires EXECUTED_PASS")
        if comparison.get("result") == "DIFF" and comparison.get("execution") != "EXECUTED_FAIL": errors.append(f"{p} DIFF requires EXECUTED_FAIL")
        if comparison.get("result") == "INCOMPARABLE" and not comparison.get("reason"): errors.append(f"{p} INCOMPARABLE requires reason")
        if comparison.get("result") == "UNVERIFIED" and comparison.get("execution") not in {"NOT_RUN", "ENVIRONMENT_BLOCKED"}: errors.append(f"{p} UNVERIFIED execution conflict")
        perf = comparison.get("performance_evidence", {})
        if perf and isinstance(perf, dict):
            if perf.get("regression_percent") is not None and not isinstance(perf["regression_percent"], (int, float)):
                errors.append(f"{p} performance_evidence.regression_percent must be numeric")
    quality = report.get("quality_metrics", {})
    if quality and isinstance(quality, dict):
        for key in ("code_maintainability", "reproducibility_score"):
            if quality.get(key) and quality[key] not in QUALITY_GRADES: errors.append(f"quality_metrics.{key} invalid grade")
        if quality.get("documentation_completeness") is not None:
            val = quality["documentation_completeness"]
            if not isinstance(val, (int, float)) or val < 0 or val > 1: errors.append("quality_metrics.documentation_completeness must be 0-1")
        if quality.get("test_coverage_percent") is not None:
            val = quality["test_coverage_percent"]
            if not isinstance(val, int) or val < 0 or val > 100: errors.append("quality_metrics.test_coverage_percent must be 0-100 integer")
        if quality.get("overall_maturity") is not None:
            val = quality["overall_maturity"]
            if not isinstance(val, int) or val < 0 or val > 100: errors.append("quality_metrics.overall_maturity must be 0-100 integer")
    milestones = report.get("milestone_tracking", [])
    if not isinstance(milestones, list): errors.append("milestone_tracking must be array"); milestones = []
    for i, ms in enumerate(milestones):
        p = f"milestone_tracking[{i}]"
        if not isinstance(ms, dict): errors.append(f"{p} must be object"); continue
        if not ms.get("name"): errors.append(f"{p}.name required")
        if ms.get("status") not in MILESTONE_STATUS: errors.append(f"{p}.status invalid")
        if ms.get("status") == "delayed" and not ms.get("delay_reason"): errors.append(f"{p} delayed requires delay_reason")
    strategy = report.get("strategy_evidence", {})
    if strategy and isinstance(strategy, dict):
        decisions = strategy.get("decisions", [])
        if not isinstance(decisions, list): errors.append("strategy_evidence.decisions must be array"); decisions = []
        for i, dec in enumerate(decisions):
            p = f"strategy_evidence.decisions[{i}]"
            if not isinstance(dec, dict): errors.append(f"{p} must be object"); continue
            if not dec.get("decision"): errors.append(f"{p}.decision required")
            if not dec.get("rationale"): errors.append(f"{p}.rationale required")
            if not dec.get("alternatives_considered"): errors.append(f"{p}.alternatives_considered required")
    behavior = report.get("behavior_evidence")
    if behavior is not None:
        p = "behavior_evidence"
        if not isinstance(behavior, dict): errors.append(f"{p} must be an object")
        else:
            for key in ("cases_total", "with_skill_pass", "without_skill_pass"):
                val = behavior.get(key)
                if not isinstance(val, int) or val < 0: errors.append(f"{p}.{key} must be a non-negative integer")
            total = behavior.get("cases_total")
            for key in ("with_skill_pass", "without_skill_pass"):
                val = behavior.get(key)
                if isinstance(val, int) and isinstance(total, int) and val > total:
                    errors.append(f"{p}.{key} cannot exceed cases_total")
            tc, tt = behavior.get("trigger_correct"), behavior.get("trigger_total")
            if isinstance(tc, int) and isinstance(tt, int) and tc > tt: errors.append(f"{p}.trigger_correct cannot exceed trigger_total")
            if behavior.get("verdict") not in BEHAVIOR_VERDICTS: errors.append(f"{p}.verdict invalid")
            if behavior.get("verdict") == "not_applicable" and not behavior.get("verdict_reason"):
                errors.append(f"{p} not_applicable requires verdict_reason")
            if behavior.get("verdict") == "install":
                if not behavior.get("execution_evidence"):
                    errors.append(f"{p} install requires execution_evidence (a claimed path is not evidence)")
                if behavior.get("source_hashes_stable") is not True:
                    errors.append(f"{p} install requires source_hashes_stable true")
                if behavior.get("baseline_isolated") is not True:
                    errors.append(f"{p} install requires baseline_isolated true")
                wp, wop = behavior.get("with_skill_pass"), behavior.get("without_skill_pass")
                if isinstance(wp, int) and isinstance(wop, int) and wp <= wop:
                    errors.append(f"{p} install requires uplift (with_skill_pass > without_skill_pass)")
                # claimed execution must point at artifacts that actually exist
                if isinstance(scope, dict) and scope.get("resolve_root"):
                    for k, ev in enumerate(behavior["execution_evidence"]):
                        ev_s = str(ev)
                        if not re.search(r"[A-Za-z0-9_./\\-]+\.[A-Za-z0-9]{1,6}\b", ev_s): continue
                        cand = Path(ev_s)
                        if not cand.is_absolute(): cand = Path(scope["resolve_root"]) / ev_s
                        if not cand.exists():
                            errors.append(f"{p}.execution_evidence[{k}] does not exist: {ev_s} "
                                          f"(claims of execution must point at real artifacts)")
            if behavior.get("verdict") == "install" and report.get("gate") == "REJECT":
                errors.append(f"{p} install contradicts gate REJECT")
            tags = behavior.get("case_tags")
            if tags is not None:
                if not isinstance(tags, list) or len(tags) < 3:
                    errors.append(f"{p}.case_tags must list one tag per case (>=3)")
                elif len({str(t).strip().casefold() for t in tags}) < 2:
                    errors.append(f"{p}.case_tags must cover >=2 distinct scenarios, got all identical")
            elif behavior.get("verdict") in {"install", "fix-first"}:
                errors.append(f"{p} verdict={behavior.get('verdict')} requires case_tags proving scenario coverage")
    # semantic_only must stay a minority: otherwise the anchoring rule is bypassed wholesale
    if isinstance(scope, dict) and scope.get("resolve_root"):
        filable = sem = 0
        for f in findings:
            if not isinstance(f, dict): continue
            for e in f.get("evidence", []):
                if not isinstance(e, dict): continue
                if cited_text(e.get("locator", ""), scope["resolve_root"]) is None: continue
                filable += 1
                if e.get("semantic_only"): sem += 1
        if filable >= 5 and sem * 100 > filable * 30:
            errors.append(f"semantic_only citations are {sem}/{filable} (>30%): the anchoring rule is being bypassed "
                          f"wholesale — anchor more citations literally instead of declaring them semantic")
    gate = report.get("gate")
    if isinstance(behavior, dict):
        if behavior.get("verdict") == "reject" and gate not in {"REJECT", "INCOMPLETE"}:
            errors.append("behavior verdict reject requires gate REJECT or INCOMPLETE")
        if behavior.get("verdict") == "fix-first" and gate == "ACCEPT":
            errors.append("behavior verdict fix-first prohibits gate ACCEPT")
    in_flight = report.get("in_flight_fixes", [])
    if not isinstance(in_flight, list): errors.append("in_flight_fixes must be array"); in_flight = []
    for i, item in enumerate(in_flight):
        p = f"in_flight_fixes[{i}]"
        if not isinstance(item, dict): errors.append(f"{p} must be object"); continue
        for key in ("finding_id", "change", "verified_against"):
            if not item.get(key): errors.append(f"{p}.{key} required")
        if item.get("finding_id") and item["finding_id"] not in ids:
            errors.append(f"{p}.finding_id must reference an existing finding")
        if item.get("verified_against") and not NAMED_FIX.search(str(item["verified_against"])):
            errors.append(f"{p}.verified_against must name a file, diff or command")
    blockers = [f for f in findings if isinstance(f, dict) and f.get("status") == "FAIL" and f.get("severity") in {"blocker", "high"}]
    unresolved = [f for f in blockers if f.get("remediation", {}).get("verification") != "RESOLVED"]
    if unresolved and gate not in {"REJECT", "INCOMPLETE"}: errors.append("unresolved blocker/high FAIL requires REJECT or INCOMPLETE")
    if any(isinstance(f, dict) and f.get("status") == "UNVERIFIED" for f in findings) and gate == "ACCEPT": errors.append("UNVERIFIED findings prohibit ACCEPT")
    if any(isinstance(c, dict) and c.get("result") == "UNVERIFIED" for c in comparisons) and gate == "ACCEPT": errors.append("UNVERIFIED comparisons prohibit ACCEPT")
    if gate == "ACCEPT" and not any(isinstance(f, dict) and f.get("status") == "PASS" for f in findings): errors.append("ACCEPT requires at least one executed PASS finding")
    substantive = [f for f in findings if isinstance(f, dict) and f.get("status") == "PASS" and f.get("enforcement") in {"code", "test"}]
    if gate == "ACCEPT" and not substantive:
        errors.append("ACCEPT requires at least one PASS enforced in code or a test; prose-only PASS is not enough")
    open_fails = [f for f in findings if isinstance(f, dict) and f.get("status") == "FAIL"
                  and f.get("remediation", {}).get("verification") != "RESOLVED"]
    if gate in {"ACCEPT", "CONDITIONAL"} and open_fails:
        errors.append(f"gate={gate} prohibits any unresolved FAIL finding: "
                      + ", ".join(str(f.get("id")) for f in open_fails)
                      + " (use REJECT/INCOMPLETE, or resolve them with a real artifact)")
    return errors


_FIXTURE_DIR = Path(tempfile.mkdtemp(prefix="vr-fixture-"))
(_FIXTURE_DIR / "p.py").write_text(
    "def alpha_handler():\n    value = compute()\n    gamma_value = value\n    return gamma_value\n", encoding="utf-8")
(_FIXTURE_DIR / "run.log").write_text("command: py -3 -m pytest\nobserved: 3 passed\nexit_code: 0\n", encoding="utf-8")


def fixture():
    return {"schema_version": "3.6", "project": {"name": "fixture", "type": "engineering", "snapshot": "snapshot-1", "evidence_scope": "single-project"},
      "scope": {"inputs": [str(_FIXTURE_DIR)], "exclusions": [], "readonly": True,
                "coverage_note": "Only declared inputs", "resolve_root": str(_FIXTURE_DIR),
                "source_hashes": {"algorithm": "sha256", "inputs": [str(_FIXTURE_DIR)], "before": "aaa", "after": "bbb",
                                  "stable": True, "mode": "two-invocation", "before_at": "T0", "after_at": "T1"}},
      "findings": [{"id": "DEF-001", "statement": "checked rule passes", "status": "PASS", "execution": "EXECUTED_PASS",
        "severity": "info", "enforcement": "test",
        "evidence": [{"locator": "p.py:1-4", "observation": "alpha_handler computes gamma_value from value"}],
        "remediation": {"action": "", "acceptance": "", "verification": "NOT_RUN"}}],
      "github_sources": [], "literature_sources": [], "comparisons": [], "gate": "ACCEPT"}


class ContractTests(unittest.TestCase):
    def assert_invalid(self, mutate):
        report = fixture(); mutate(report)
        self.assertTrue(validate(report))
    def test_valid(self): self.assertEqual(validate(fixture()), [])
    def test_environment_is_not_failure(self):
        self.assert_invalid(lambda r: r["findings"][0].update(status="FAIL", execution="ENVIRONMENT_BLOCKED", gate="REJECT"))
    def test_resolved_needs_real_result(self):
        self.assert_invalid(lambda r: r["findings"][0]["remediation"].update(verification="RESOLVED", acceptance_result={"command": "test", "exit_code": 1, "observed": "failed"}))
    def test_unresolved_high_cannot_accept(self):
        self.assert_invalid(lambda r: r["findings"][0].update(status="FAIL", execution="EXECUTED_FAIL", severity="high"))
    def test_incomparable_needs_reason(self):
        self.assert_invalid(lambda r: r["comparisons"].append({"result": "INCOMPARABLE", "contract": "numeric", "execution": "NOT_RUN"}))
    def test_match_needs_execution(self):
        self.assert_invalid(lambda r: r["comparisons"].append({"result": "MATCH", "contract": "numeric", "execution": "NOT_RUN"}))
    def test_github_summary_not_reproduction(self):
        self.assert_invalid(lambda r: r["github_sources"].append({"level": "independent-reproduction", "url": "https://github.com/a/b", "version": "main", "retrieved": "2026-11-11", "read_status": "summary-only"}))
    def test_readonly_is_explicit(self):
        self.assert_invalid(lambda r: r["scope"].update(readonly="yes"))
    def test_na_needs_reason(self):
        self.assert_invalid(lambda r: r["findings"][0].update(status="N/A", execution="NOT_APPLICABLE"))
    def test_only_na_cannot_accept(self):
        self.assert_invalid(lambda r: r["findings"][0].update(status="N/A", execution="NOT_APPLICABLE", na_reason="not an experiment"))
    def test_unverified_comparison_cannot_accept(self):
        self.assert_invalid(lambda r: r["comparisons"].append({"result": "UNVERIFIED", "contract": "numeric", "execution": "NOT_RUN"}))
    def test_fabricated_locator_is_rejected_when_resolving(self):
        with tempfile.TemporaryDirectory() as tmp:
            def mutate(r):
                r["scope"]["resolve_root"] = tmp
                r["findings"][0]["evidence"] = [{"locator": "definitely_missing.py:99999-100000", "observation": "fabricated"}]
            self.assert_invalid(mutate)
    def test_real_locator_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            sample = Path(tmp) / "sample.txt"
            sample.write_text("alpha line one\nbeta line two\n", encoding="utf-8")
            report = fixture()
            report["scope"]["resolve_root"] = tmp
            report["findings"][0]["evidence"] = [{"locator": "sample.txt:1-2", "observation": "both alpha and beta lines are present"}]
            self.assertEqual(validate(report), [])
    def test_locator_line_out_of_range_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "sample.txt").write_text("only one line\n", encoding="utf-8")
            def mutate(r):
                r["scope"]["resolve_root"] = tmp
                r["findings"][0]["evidence"] = [{"locator": "sample.txt:500", "observation": "claims line 500"}]
            self.assert_invalid(mutate)
    def test_url_locator_not_treated_as_path(self):
        report = fixture()
        report["scope"]["resolve_root"] = "D:/nonexistent-root"
        report["findings"][0].update(status="PASS", enforcement="prose")
        report["findings"][0]["evidence"] = [{"locator": "https://example.com/x:12", "observation": "remote reference"}]
        report["gate"] = "CONDITIONAL"
        self.assertEqual(validate(report), [])
    def test_bare_path_locator_must_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            def mutate(r):
                r["scope"]["resolve_root"] = tmp
                r["findings"][0]["evidence"] = [{"locator": "sub/dir/missing.json", "observation": "claims a file"}]
            self.assert_invalid(mutate)
    def test_prose_locator_is_ignored(self):
        report = fixture()
        report["scope"]["resolve_root"] = "D:/nonexistent-root"
        report["findings"][0].update(enforcement="prose", status="PASS", execution="EXECUTED_PASS")
        report["findings"][0]["evidence"] = [{"locator": "session seq 5206", "observation": "archive ended without result"}]
        report["gate"] = "CONDITIONAL"
        self.assertEqual(validate(report), [])
    def _behavior(self, **overrides):
        base = {"cases_total": 3, "with_skill_pass": 3, "without_skill_pass": 1, "verdict": "install",
                "execution_evidence": ["runs/001/outputs"], "source_hashes_stable": True, "baseline_isolated": True,
                "case_tags": ["recall", "classification", "decision"]}
        base.update(overrides)
        return base
    def test_install_behavior_accepted(self):
        report = fixture(); report["behavior_evidence"] = self._behavior()
        self.assertEqual(validate(report), [])
    def test_claim_without_execution_evidence_is_rejected(self):
        report = fixture(); report["behavior_evidence"] = self._behavior(execution_evidence=[])
        self.assertTrue(validate(report))
    def test_no_uplift_cannot_install(self):
        report = fixture(); report["behavior_evidence"] = self._behavior(with_skill_pass=1, without_skill_pass=1)
        self.assertTrue(validate(report))
    def test_dirty_source_hashes_cannot_install(self):
        report = fixture(); report["behavior_evidence"] = self._behavior(source_hashes_stable=False)
        self.assertTrue(validate(report))
    def test_contaminated_baseline_cannot_install(self):
        report = fixture(); report["behavior_evidence"] = self._behavior(baseline_isolated=False)
        self.assertTrue(validate(report))
    def test_pass_counts_cannot_exceed_total(self):
        report = fixture(); report["behavior_evidence"] = self._behavior(with_skill_pass=9)
        self.assertTrue(validate(report))
    def test_behavior_reject_requires_reject_gate(self):
        report = fixture(); report["behavior_evidence"] = self._behavior(verdict="reject")
        self.assertTrue(validate(report))
    def test_fix_first_prohibits_accept(self):
        report = fixture(); report["behavior_evidence"] = self._behavior(verdict="fix-first")
        self.assertTrue(validate(report))
    def test_not_applicable_needs_reason(self):
        report = fixture(); report["behavior_evidence"] = {"cases_total": 1, "with_skill_pass": 0, "without_skill_pass": 0, "verdict": "not_applicable"}
        self.assertTrue(validate(report))
    # --- v3.3 gap fixes ---
    def test_rejected_removes_unevidenced_rating(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "guess with no evidence", "status": "REJECTED",
            "execution": "NOT_RUN", "severity": "low", "evidence": [],
            "rejected_reason": "已 grep 全库并在 `src/defs.py` 与 `tests/` 下逐文件查找该符号，任何窗口均无匹配，故作为无证据猜测移除",
            "remediation": {"action": "", "acceptance": "", "verification": "NOT_RUN"}})
        self.assertEqual(validate(report), [])
    def test_rejected_must_not_absorb_serious_suspicion(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "serious suspicion hidden as guess", "status": "REJECTED",
            "execution": "NOT_RUN", "severity": "high", "evidence": [],
            "rejected_reason": "已 grep 全库并在 `src/defs.py` 与 `tests/` 下逐文件查找该符号，任何窗口均无匹配",
            "remediation": {"action": "", "acceptance": "", "verification": "NOT_RUN"}})
        self.assertTrue(validate(report))
    def test_rejected_requires_reason(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "guess", "status": "REJECTED", "execution": "NOT_RUN",
            "severity": "high", "evidence": [], "remediation": {"action": "", "acceptance": "", "verification": "NOT_RUN"}})
        self.assertTrue(validate(report))
    def test_rejected_must_not_carry_evidence(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "guess", "status": "REJECTED", "execution": "NOT_RUN",
            "severity": "high", "rejected_reason": "x",
            "evidence": [{"locator": "a.py:1", "observation": "o"}],
            "remediation": {"action": "", "acceptance": "", "verification": "NOT_RUN"}})
        self.assertTrue(validate(report))
    def test_absent_claim_requires_searched_scope(self):
        report = fixture()
        report["findings"][0]["claim_kind"] = "absent"
        self.assertTrue(validate(report))
    def test_absent_claim_with_searched_scope_ok(self):
        report = fixture()
        report["findings"][0]["claim_kind"] = "absent"
        report["findings"][0]["searched_scope"] = ["grep 'def foo' src/", "pytest --collect-only"]
        self.assertEqual(validate(report), [])
    def test_medium_fix_must_name_file_guard_or_test(self):
        report = fixture()
        report["findings"][0].update(status="FAIL", execution="EXECUTED_FAIL", severity="medium")
        report["findings"][0]["remediation"] = {"action": "consider improving robustness", "acceptance": "py -3 -m pytest", "verification": "NOT_RUN"}
        report["gate"] = "REJECT"
        self.assertTrue(validate(report))
    def test_medium_fix_naming_file_passes(self):
        report = fixture()
        report["findings"][0].update(status="FAIL", execution="EXECUTED_FAIL", severity="medium")
        report["findings"][0]["remediation"] = {"action": "add guard in `src/parse.py:42`", "acceptance": "py -3 -m pytest tests/test_parse.py", "verification": "NOT_RUN"}
        report["gate"] = "REJECT"
        self.assertEqual(validate(report), [])
    def test_acceptance_must_be_executable(self):
        report = fixture()
        report["findings"][0].update(status="FAIL", execution="EXECUTED_FAIL", severity="medium")
        report["findings"][0]["remediation"] = {"action": "fix `a.py:1`", "acceptance": "looks good to me", "verification": "NOT_RUN"}
        report["gate"] = "REJECT"
        self.assertTrue(validate(report))
    def test_readonly_requires_source_hashes(self):
        report = fixture(); del report["scope"]["source_hashes"]
        self.assertTrue(validate(report))
    def test_readonly_rejects_source_drift(self):
        report = fixture(); report["scope"]["source_hashes"]["stable"] = False
        self.assertTrue(validate(report))
    def test_in_flight_must_reference_existing_finding(self):
        report = fixture(); report["in_flight_fixes"] = [{"finding_id": "DEF-999", "change": "x", "verified_against": "git diff a.py"}]
        self.assertTrue(validate(report))
    def test_in_flight_does_not_unblock_gate(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "open high", "status": "FAIL", "execution": "EXECUTED_FAIL",
            "severity": "high", "evidence": [{"locator": "a.py:1", "observation": "o"}],
            "remediation": {"action": "fix `a.py:1`", "acceptance": "py -3 -m pytest", "verification": "NOT_RUN"}})
        report["in_flight_fixes"] = [{"finding_id": "DEF-002", "change": "fix in open PR", "verified_against": "git diff a.py"}]
        # still ACCEPT -> must be rejected: in-flight fixes must not launder an open blocker
        self.assertTrue(validate(report))
    def test_accept_prohibits_unresolved_medium(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "open medium", "status": "FAIL", "execution": "EXECUTED_FAIL",
            "severity": "medium", "evidence": [{"locator": "a.py:1", "observation": "o"}],
            "remediation": {"action": "fix `a.py:1`", "acceptance": "py -3 -m pytest", "verification": "NOT_RUN"}})
        self.assertTrue(validate(report))
    def test_accept_ok_when_all_fails_resolved(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "fixed medium", "status": "PASS", "execution": "EXECUTED_PASS",
            "severity": "medium", "evidence": [{"locator": "p.py:1-4", "observation": "alpha_handler computes gamma_value"}],
            "remediation": {"action": "fixed `p.py:1-4`", "acceptance": "py -3 -m pytest", "verification": "RESOLVED",
                            "acceptance_result": {"command": "py -3 -m pytest", "exit_code": 0,
                                                  "observed": "3 passed in 0.01s per the recorded run log",
                                                  "artifact": "run.log"}}})
        report["findings"][-1]["enforcement"] = "test"
        self.assertEqual(validate(report), [])
    def test_resolved_requires_real_artifact(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "claimed fixed", "status": "PASS", "execution": "EXECUTED_PASS",
            "severity": "medium", "enforcement": "test",
            "evidence": [{"locator": "p.py:1-4", "observation": "alpha_handler computes gamma_value"}],
            "remediation": {"action": "fixed `p.py:1-4`", "acceptance": "py -3 -m pytest", "verification": "RESOLVED",
                            "acceptance_result": {"command": "py -3 -m pytest", "exit_code": 0,
                                                  "observed": "self-declared pass with no artifact on disk"}}})
        self.assertTrue(validate(report))
    def test_resolved_rejects_missing_artifact_file(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "claimed fixed", "status": "PASS", "execution": "EXECUTED_PASS",
            "severity": "medium", "enforcement": "test",
            "evidence": [{"locator": "p.py:1-4", "observation": "alpha_handler computes gamma_value"}],
            "remediation": {"action": "fixed `p.py:1-4`", "acceptance": "py -3 -m pytest", "verification": "RESOLVED",
                            "acceptance_result": {"command": "py -3 -m pytest", "exit_code": 0,
                                                  "observed": "claims a log that does not exist anywhere",
                                                  "artifact": "nope/missing.log"}}})
        self.assertTrue(validate(report))
    def test_conditional_cannot_hide_unresolved_medium(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "open medium", "status": "FAIL", "execution": "EXECUTED_FAIL",
            "severity": "medium", "evidence": [{"locator": "p.py:1-4", "observation": "alpha_handler computes gamma_value"}],
            "remediation": {"action": "fix `p.py:1-4`", "acceptance": "py -3 -m pytest", "verification": "NOT_RUN"}})
        report["gate"] = "CONDITIONAL"
        self.assertTrue(validate(report))
    def test_local_fileline_requires_resolve_root(self):
        report = fixture(); del report["scope"]["resolve_root"]
        self.assertTrue(validate(report))
    def test_url_cannot_satisfy_enforcement(self):
        report = fixture()
        report["findings"][0]["evidence"] = [{"locator": "https://example.com/impl.py:42", "observation": "authoritative implementation"}]
        self.assertTrue(validate(report))
    # --- v3.4 PASS grading ---
    def test_pass_requires_enforcement(self):
        report = fixture(); report["findings"][0].pop("enforcement")
        self.assertTrue(validate(report))
    def test_code_enforcement_requires_file_line(self):
        report = fixture()
        report["findings"][0]["enforcement"] = "code"
        report["findings"][0]["evidence"] = [{"locator": "some description without a line", "observation": "o"}]
        self.assertTrue(validate(report))
    def test_prose_only_pass_cannot_accept(self):
        report = fixture()
        report["findings"][0]["enforcement"] = "prose"
        report["findings"][0]["evidence"] = [{"locator": "README.md", "observation": "文档声称如此"}]
        self.assertTrue(validate(report))
    def test_prose_pass_ok_when_a_test_pass_exists(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "documented only", "status": "PASS", "execution": "EXECUTED_PASS",
            "severity": "low", "enforcement": "prose", "evidence": [{"locator": "README.md", "observation": "prose"}],
            "remediation": {"action": "", "acceptance": "", "verification": "NOT_RUN"}})
        self.assertEqual(validate(report), [])
    def test_invalid_enforcement_value(self):
        report = fixture(); report["findings"][0]["enforcement"] = "vibes"
        self.assertTrue(validate(report))
    # --- v3.5: evidence anchoring + reason strength + claim class + case coverage ---
    def test_unanchored_observation_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "s.py").write_text("def alpha_handler():\n    return gamma_value\n", encoding="utf-8")
            report = fixture()
            report["scope"]["resolve_root"] = tmp
            report["findings"][0]["evidence"] = [{"locator": "s.py:1-2", "observation": "完全无关的伪造观察文字"}]
            self.assertTrue(validate(report))
    def test_semantic_only_escape_needs_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "s.py").write_text("def alpha_handler():\n    return gamma_value\n", encoding="utf-8")
            report = fixture()
            report["scope"]["resolve_root"] = tmp
            report["findings"][0]["evidence"] = [{"locator": "s.py:1-2", "observation": "整体性质描述", "semantic_only": True}]
            self.assertTrue(validate(report))
            report["findings"][0]["evidence"][0]["anchor_note"] = "该观察描述的是文件整体性质与跨文件约束，所引行的字面 token 无法代表该结论，因此显式声明为语义引用而非字面锚定"
            self.assertEqual(validate(report), [])
    def test_na_reason_must_be_substantive(self):
        report = fixture()
        report["findings"][0].update(status="N/A", execution="NOT_APPLICABLE", na_reason="不适用")
        report["gate"] = "INCOMPLETE"
        self.assertTrue(validate(report))
    def test_na_reason_substantive_passes(self):
        report = fixture()
        report["findings"][0].update(status="N/A", execution="NOT_APPLICABLE",
            na_reason="该项目类型为 concept，不含实验代码，因此 seed/噪声底检查不适用")
        report["gate"] = "INCOMPLETE"
        self.assertEqual(validate(report), [])
    def test_rejected_reason_must_name_search(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "guess", "status": "REJECTED", "execution": "NOT_RUN",
            "severity": "high", "evidence": [], "rejected_reason": "没有找到相关内容所以先记为猜测并移除",
            "remediation": {"action": "", "acceptance": "", "verification": "NOT_RUN"}})
        self.assertTrue(validate(report))
    def test_rejected_reason_naming_search_passes(self):
        report = fixture()
        report["findings"].append({"id": "DEF-002", "statement": "guess", "status": "REJECTED", "execution": "NOT_RUN",
            "severity": "low", "evidence": [],
            "rejected_reason": "已 grep 全库并在 `src/defs.py` 与 `tests/` 下逐文件查找该符号，任何窗口均无匹配，故作为无证据猜测移除",
            "remediation": {"action": "", "acceptance": "", "verification": "NOT_RUN"}})
        self.assertEqual(validate(report), [])
    def test_novelty_claim_requires_external_citation(self):
        report = fixture()
        report["findings"][0]["claim_class"] = "novelty"
        self.assertTrue(validate(report))
    def test_novelty_claim_with_source_passes(self):
        report = fixture()
        report["findings"][0]["claim_class"] = "novelty"
        report["github_sources"] = [{"level": "comparable-method", "url": "https://github.com/a/b",
            "version": "main", "retrieved": "2026-11-15", "read_status": "text-read"}]
        self.assertEqual(validate(report), [])
    def test_behavior_case_tags_required_for_verdict(self):
        report = fixture()
        report["behavior_evidence"] = {"cases_total": 3, "with_skill_pass": 3, "without_skill_pass": 0,
            "verdict": "install", "execution_evidence": ["x"], "source_hashes_stable": True, "baseline_isolated": True}
        self.assertTrue(validate(report))
    def test_behavior_case_tags_must_vary(self):
        report = fixture()
        report["behavior_evidence"] = {"cases_total": 3, "with_skill_pass": 3, "without_skill_pass": 0,
            "verdict": "install", "execution_evidence": ["x"], "source_hashes_stable": True, "baseline_isolated": True,
            "case_tags": ["recall", "recall", "recall"]}
        self.assertTrue(validate(report))
    def test_behavior_case_tags_varied_passes(self):
        report = fixture()
        report["behavior_evidence"] = {"cases_total": 3, "with_skill_pass": 3, "without_skill_pass": 0,
            "verdict": "install", "execution_evidence": ["x"], "source_hashes_stable": True, "baseline_isolated": True,
            "case_tags": ["recall", "classification", "decision"]}
        self.assertEqual(validate(report), [])
    def test_multi_range_locator_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = [f"marker{i:03d} payload" for i in range(1, 51)]
            (Path(tmp) / "s.py").write_text("\n".join(body) + "\n", encoding="utf-8")
            report = fixture()
            report["scope"]["resolve_root"] = tmp
            report["findings"][0].update(enforcement="code", status="PASS", execution="EXECUTED_PASS")
            report["findings"][0]["evidence"] = [{"locator": "s.py:5-10,40-45", "observation": "marker005 and marker040 payloads"}]
            self.assertEqual(validate(report), [])
    def test_multi_range_locator_catches_bad_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "s.py").write_text("\n".join(str(i) for i in range(1, 21)) + "\n", encoding="utf-8")
            report = fixture()
            report["scope"]["resolve_root"] = tmp
            report["findings"][0].update(enforcement="code", status="PASS", execution="EXECUTED_PASS")
            report["findings"][0]["evidence"] = [{"locator": "s.py:5-10,900-999", "observation": "second range past EOF"}]
            self.assertTrue(validate(report))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests)
        result = unittest.TextTestRunner(verbosity=1).run(suite)
        return 0 if result.wasSuccessful() else 1
    if not args.report: parser.error("report required unless --self-test")
    try: report = json.loads(args.report.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc: print(f"INVALID: {exc}"); return 2
    errors = validate(report)
    if errors: print("INVALID\n" + "\n".join(f"- {e}" for e in errors)); return 1
    print(f"PASS: {args.report}; findings={len(report['findings'])}; gate={report['gate']}"); return 0

if __name__ == "__main__": raise SystemExit(main())
