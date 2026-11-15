#!/usr/bin/env python3
"""Fingerprint declared review inputs so a read-only claim is verifiable, not self-declared.

Two modes:
  single-run       : before/after computed back-to-back in one process (self-certifying; NOT proof)
  two-invocation   : call --stamp before the review, then --stamp after it; the record carries two
                     wall-clock stamps and is the only mode that shows a real time gap

Usage:
  py -3 source_fingerprint.py --stamp before --inputs A B --state fp.json
  ... review happens ...
  py -3 source_fingerprint.py --stamp after  --state fp.json --out source-hashes.json
  py -3 source_fingerprint.py --verify source-hashes.json
Exit 0 = stable/recorded; exit 1 = drift detected.
"""
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", ".venv"}
SKIP_SUFFIX = {".pyc", ".pyo"}


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iter_files(root: Path):
    if root.is_file():
        yield root; return
    for p in sorted(root.rglob("*")):
        if not p.is_file(): continue
        if any(part in SKIP_DIRS for part in p.parts): continue
        if p.suffix in SKIP_SUFFIX: continue
        yield p


def digest(paths):
    h = hashlib.sha256()
    entries = []
    for raw in paths:
        root = Path(raw)
        if not root.exists():
            entries.append({"input": raw, "status": "missing"})
            h.update(f"missing:{raw}".encode())
            continue
        for f in iter_files(root):
            try: data = f.read_bytes()
            except OSError: continue
            h.update(str(f).encode()); h.update(data)
        entries.append({"input": raw, "status": "hashed"})
    return h.hexdigest(), entries


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inputs", nargs="+")
    ap.add_argument("--stamp", choices=["before", "after"])
    ap.add_argument("--state", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--verify", type=Path)
    a = ap.parse_args()

    if a.verify:
        rec = json.loads(a.verify.read_text(encoding="utf-8"))
        now_hash, _ = digest(rec["inputs"])
        stable = now_hash == rec["after"]
        print(json.dumps({"record": str(a.verify), "recorded_after": rec["after"],
                          "recomputed": now_hash, "stable": stable}, indent=2))
        return 0 if stable else 1

    if a.stamp:
        if not a.state: ap.error("--state required with --stamp")
        if a.stamp == "before":
            if not a.inputs: ap.error("--inputs required for --stamp before")
            h, entries = digest(a.inputs)
            a.state.write_text(json.dumps({"inputs": a.inputs, "before": h, "before_at": now(),
                                           "entries": entries}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"recorded BEFORE at {now()} -> {h[:16]}  (state: {a.state})")
            return 0
        st = json.loads(a.state.read_text(encoding="utf-8"))
        after, _ = digest(st["inputs"])
        payload = {
            "algorithm": "sha256(concat(path + bytes) over sorted files)",
            "inputs": st["inputs"], "entries": st["entries"],
            "before": st["before"], "after": after,
            "stable": st["before"] == after,
            "mode": "two-invocation",
            "before_at": st["before_at"], "after_at": now(),
            "note": "two separate invocations bracket the review (--stamp before ... --stamp after)",
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        (a.out or a.state).write_text(text, encoding="utf-8")
        print(text)
        return 0 if payload["stable"] else 1

    if not a.inputs: ap.error("--inputs required unless --verify/--stamp")
    before, entries = digest(a.inputs)
    after, _ = digest(a.inputs)
    payload = {
        "algorithm": "sha256(concat(path + bytes) over sorted files)",
        "inputs": a.inputs, "entries": entries,
        "before": before, "after": after, "stable": before == after,
        "mode": "single-run",
        "note": "SINGLE-RUN: before/after computed back-to-back in one process. This does NOT prove "
                "the review was read-only; use --stamp before/--stamp after for a real time gap.",
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if a.out: a.out.write_text(text, encoding="utf-8")
    print(text)
    return 0 if payload["stable"] else 1


if __name__ == "__main__": raise SystemExit(main())
