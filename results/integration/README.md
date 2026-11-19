# Integrated verification (2026-11-15)

This directory contains evidence produced from the merged working tree in the
repository root, after Role A, Role B and Role C were combined.

## Environment

- Python 3.12.14
- `python -B -m unittest` (no third-party packages needed for unit tests)
- No `.git` directory is present in the uploaded working tree

## Command and result

```bash
python -B -m unittest discover -s tests -v
```

Result: **73 tests, 0 failures, 0 errors** — see [full-tests.txt](full-tests.txt).

Breakdown:

| Suite | Tests | Result |
| --- | ---: | --- |
| Framework | 3 | pass |
| Public Task A | 3 | pass |
| Public Task B | 5 | pass |
| Public integration | 6 | pass |
| Role A targeted | 21 | pass |
| Role B targeted | 29 | pass |
| Role C targeted | 6 | pass |

Public acceptance set only: **17/17 pass**.

## End-to-end simulation

[simulation.json](simulation.json) records two runs of the real event loop:

1. One transfer: `Alice -> Bob 10`; 20 steps; committed chain `B0, B1`;
   accounts `Alice 90 / Bob 110 / Charlie 100`; receipt `committed`; mempool empty.
2. Insufficient funds: `Alice -> Bob 80` then `Alice -> Charlie 80`; the first
   receipt is `committed`, the second is `rejected` with `Insufficient funds`;
   accounts `Alice 20 / Bob 180 / Charlie 100`; mempool empty.

Both runs report `consistent: true` across the four replicas.

## Optional tests

```bash
python -B -m unittest discover -s extensions_tests -v
```

Result: **1 pass, 1 failure, 5 errors** — see [optional-tests.txt](optional-tests.txt).
These are the optional A6 (recovery/timeout) and B5 (batch limit) extensions,
which are still TODO and are not part of the 73-test base suite.
