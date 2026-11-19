# Integration notes

Date: 2026-11-15. This is the merged working tree for the COMP5567 HotStuff
project. It combines the Role A baseline in the repository root with the
uploaded Role B and Role C branches.

## Sources

| Source | Path | Contents |
| --- | --- | --- |
| Role A baseline | repository root (`backend/`, `tests/`, `role_a/`, `results/role_a/`) | A1, A2, B1 |
| Role B upload | `5567projectRepository-role-b/` | A3, A4, A5, B2 |
| Role C upload | `5567projectRepository-role-c/` | B3, B4 |

The two uploaded directories were left untouched for provenance. The canonical
runnable project is the repository root.

## Merge decisions

B and C modified disjoint functions, so no semantic conflict needed to be
resolved:

| Function | Merged implementation | Source |
| --- | --- | --- |
| `HotStuffDemo.form_qc()` | QC from at least three distinct valid voters; register, dispatch, queue `next_view` | B |
| `Node.receive_qc()` | HighQC/LockedQC updates and consecutive-view three-chain commit | B |
| `HotStuffDemo.next_view()` | Advance view, rotate leader, queue next proposal | B |
| `Node.enter_view()` | Update live replica's view/role; frozen if crashed | B |
| `HotStuffDemo.select_transactions()` | Select up to the batch limit, excluding the selected parent ancestry | B |
| `StateMachine.apply()` | Validate and execute one transaction; committed/rejected receipt; ID idempotency | C |
| `Node.execute_committed()` | Validate the whole batch, then execute committed payloads in order | C |
| `HotStuffDemo.finalize_transactions()` | Remove committed transactions (including rejected) from the pool | C |

`backend/hotstuff.py` and `backend/node.py` were taken from Role B (they already
contain the Role A code), then the three Role C functions were applied.
`backend/blockchain.py` only received Role C's `StateMachine.apply()`.

Role B and Role C test files were copied to `tests/`. Raw evidence was copied to
`results/role_b/` and `results/role_c/`; current merged evidence is in
`results/integration/`. This directory also adds `tools/verify_all.py` as the
single test/demo entry point, replacing the branch-specific
`tools/verify_role_c.py` (which depends on git history that the uploaded root
does not have).

## Verification

Environment: Python 3.12.14, no third-party packages needed for unit tests.

```bash
python -B -m unittest discover -s tests -v
```

Result: **73/73 pass**, including the 17 public acceptance tests.

| Subset | Result |
| --- | --- |
| Framework | 3/3 |
| Public Task A | 3/3 |
| Public Task B | 5/5 |
| Public integration | 6/6 |
| Role A targeted | 21/21 |
| Role B targeted | 29/29 |
| Role C targeted | 6/6 |

The end-to-end simulation in `results/integration/simulation.json` verifies:

- `Alice -> Bob 10` commits with accounts `90/110/100`;
- `Alice -> Bob 80` followed by `Alice -> Charlie 80` yields one committed and
  one `rejected` receipt (`Insufficient funds`), accounts `20/180/100`;
- both runs end with an empty mempool and `consistent: true`.

Optional extension tests (`A6` recovery/timeout and `B5` batch limit) are not
part of the base suite and currently report 1 pass, 1 failure and 5 errors.

## Remaining work

- A6: `HotStuffDemo.timeout()`, `HotStuffDemo.recover()`;
- A7: `HotStuffDemo.inject_attack()` and attack validation;
- B5: `HotStuffDemo.configure_batch()`;
- B6: signatures, transaction IDs and nonce/replay handling;
- Fill in B's name and AI-assistance disclosure in `changes.md`;
- Record the final commit hash when the merged tree is committed to git.

## Running

See `README.md` for the full setup. In short:

```bash
python -m pip install -r requirements.txt
python backend/main.py
# open http://localhost:8000
```

On this macOS working copy, a project-local Python 3.12.16 runtime is installed
at `.python/`, with the ready-to-use virtual environment at `.venv/`. Both
directories are listed in `.gitignore` and should not be included in the
submission archive. Activate the environment with:

```bash
source .venv/bin/activate
python backend/main.py
```

Tests and optional demo startup:

```bash
python tools/verify_all.py
python tools/verify_all.py --serve
```
