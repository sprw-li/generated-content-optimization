# Overall Gate: `FAIL`

**Gate name: FAIL**

## Why

The gate is dominated by the single high-severity FAIL. That finding was actually executed, and its remediation is not yet verified, so the failure must be treated as still open: an unverified fix cannot downgrade a high-severity failure, and passing findings elsewhere cannot offset it.

The 2 PASS findings are legitimate positive evidence, but only within their own scope; they neither close the FAIL nor lift the aggregate to PASS.

The UNVERIFIED finding (environment-blocked) is not a PASS — absence of evidence is not a pass. On its own it would force `BLOCKED` (adjudication impossible), but it cannot outrank a confirmed high-severity FAIL. Precedence is therefore: FAIL > BLOCKED > PASS. Note what is *not* claimed: `BLOCKED` would understate a defect that is real and unremediated, and `PASS` would count unevidenced items as clean.

## Exit path

Re-run the blocked check once the environment is available, and verify the high-severity fix. If the fix verifies and the blocked item now passes, the gate recomputes to `PASS`; if the FAIL reproduces, it remains `FAIL`.
