# Results and evidence

This directory keeps the evidence from the individual roles and the merged
workspace. Raw role evidence was not rewritten; it records the state of each
branch at the time it was produced.

| Directory | Contents |
| --- | --- |
| `role_a/` | Role A (A1, A2, B1) targeted tests and HTTP logs |
| `role_b/` | Role B (A3, A4, A5, B2) HTTP walkthrough; the last record stops at the then-missing B3 |
| `role_c/` | Role C (B3, B4) targeted and combined B+C test logs, plus a four-replica transfer record |
| `integration/` | Evidence from the merged working tree: 73/73 tests, optional-test status and an end-to-end simulation |

## Current reproduction

From the repository root:

```bash
python -B -m unittest discover -s tests -v
python tools/verify_all.py
```

The first command runs the 73-test base suite; the second runs the same suite
and can start the dashboard with `--serve`.

`results/role_c/README.md` describes `tools/verify_role_c.py`, a script that
recreated the B+C combination through git branches. That script is not part of
this merged working tree (the uploaded root has no `.git`); use
`tools/verify_all.py` instead. The role C logs remain valid historical evidence.
