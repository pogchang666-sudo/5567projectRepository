# COMP5567 HotStuff Student Starter 2026

Implement the missing consensus (Task A, 35 marks) and blockchain-system
(Task B, 30 marks) functions. The accompanying project specification defines
the full 100-point assessment. This distribution originally had no working
consensus or transfer implementation. The dashboard and HTTP service start;
calling an unimplemented operation returns a clear TODO message (HTTP 501).

> **Integrated working tree (2026-11-15):** Role A, B and C work has been
> merged. A1–A5 and B1–B4 are implemented, and the 73-test combined suite passes
> (public acceptance 17/17). B6 signed transactions are available in a dedicated
> mode. Optional A6/A7/B5 remain TODO. See
> [INTEGRATION.md](INTEGRATION.md) for sources, merge decisions and current evidence.

## Run

Python 3.10 or newer. From this folder:

```bash
python -m pip install -r requirements.txt
python backend/main.py
```

Open http://localhost:8000. Start runs one logical event every 0.8 seconds;
Next Step runs one event. A missing event pauses and remains available for
retry. Reset restores genesis, three balances of 100, and batch limit 5.
No reference solution is loaded or available through a mode switch.

## Run B6 signed transactions

From PowerShell, start the server in signed mode and open
[the dashboard](http://127.0.0.1:8000):

```powershell
$env:HOTSTUFF_SIGNED_TRANSACTIONS = '1'
python -m backend.main
```

In a second terminal at the repository root, submit a signed transfer with the
classroom client:

```powershell
python -m tools.signed_transfer Alice Bob 80 0
```

Run the same command before and after advancing the dashboard to commitment.
Before commitment both requests return the same ID and a null receipt. After
commitment the same command returns the final receipt. Alice's next nonce is 1.
Submit `python -m tools.signed_transfer Alice Charlie 80 1` and advance to
commitment again to demonstrate a rejected transfer that still consumes nonce 1.
The dashboard shows next nonces, balances and receipts. To restore the basic
unsigned demo, stop the server, remove the environment variable
(`Remove-Item Env:HOTSTUFF_SIGNED_TRANSACTIONS`), and restart.

B6 verifies Ed25519 signatures at admission and execution. The canonical bytes
are ASCII JSON with sorted keys and no separator whitespace. They contain
`domain` (`COMP5567/HotStuff/Classroom/v1`), `sender`, `receiver`, `amount` and
`nonce`. The transaction ID is the SHA-256 hex digest of those bytes. The HTTP
request carries the same transaction fields plus the hex signature. The server
accepts only the next committed nonce and at most one pending transfer per sender.
An identical signed request returns the existing ID and receipt, while a different
payload with a pending nonce or a request with a future nonce is rejected. Invalid
signatures and wrong nonces leave the balances and nonces unchanged. An authenticated
insufficient-funds result receives a final receipt and consumes its nonce once.

The client uses publicly reproducible classroom keys. Signed mode demonstrates
the protocol checks with those keys and in-memory state. Reset starts a new
simulation with all nonces at zero. Cross-restart replay protection would require
persistent state or a fresh signed domain. A6 recovery is separate from B6.

## Task map

| Item | Marks | Student functions |
| --- | ---: | --- |
| A1 Proposal | 6 | HotStuffDemo.propose |
| A2 Safe voting | 8 | HotStuffDemo.vote; Node.extends, can_vote |
| A3 QC | 6 | HotStuffDemo.form_qc |
| A4 Lock and commit | 8 | Node.receive_qc |
| A5 Normal view changes | 2 | HotStuffDemo.next_view; Node.enter_view |
| A6 Optional recovery | 2 | HotStuffDemo.timeout, recover; crash paths |
| A7 Optional malicious behavior | 3 | inject_attack and validation/delivery changes; equivocation (2), second attack (1) |
| B1 Admission | 5 | HotStuffDemo.submit |
| B2 Payload selection | 5 | HotStuffDemo.select_transactions |
| B3 Execution | 8 | Node.execute_committed; StateMachine.apply |
| B4 Receipts and deduplication | 7 | StateMachine.apply; finalize_transactions |
| B5 Optional batch limit | 2 | configure_batch and payload selection |
| B6 Optional signatures and replay | 3 | Add sign_transaction, verify_transaction, transaction_id; signatures (2), nonce/replay handling (1) |

Shared functions have distinct responsibilities assessed under each row;
the same mechanism is not awarded twice. Keep public interfaces where possible.
You may add helpers. Do not change quorum three or bypass commitment.

## Integration contracts

* Implement Task A with empty blocks first. propose() should call
  select_transactions(parent) only for a nonempty pool; otherwise use [].
* Use the supplied event names: propose, vote, qc, next_view, timeout.
  Event data contracts are described in each TODO docstring.
* form_qc() validates and registers a QC, then calls dispatch_qc(qc).
  The provided helper calls Node.receive_qc() on replicas and obtains ordered
  newly committed block IDs. receive_qc() must not execute transactions.
* dispatch_qc() calls Node.execute_committed() for newly committed nonempty
  payloads, then finalize_transactions(). Empty payloads do not require Task B.
* execute_committed() must reject uncommitted IDs before any state mutation.
  StateMachine.apply() is an execution primitive, not an admission API.
* Keep transactions pending until commit; exclude only the selected parent
  ancestry during packing. A receipt status is committed (successful execution)
  or rejected (failed execution); both can belong to a committed block.
* B5 already has POST /api/config/batch with {"max_txs_per_block": 2}.
  Complete the handler's configure_batch() TODO. Reset restores 5.
* A7 already has POST /api/attacks with {"kind": "equivocation", "node_id": 1}.
  Implement attack injection and recipient-aware delivery as needed. Demonstrate
  conflicting proposals plus duplicate_vote or invalid_qc. Other nodes' identity
  cannot be impersonated under the simulator's trusted identity model.
* B6 uses the signing helpers in `backend/transaction_security.py` and the
  classroom client in `tools/signed_transfer.py`. It does not alter the quorum
  or the consensus commit rule.

The queue, API validation, fault switches, initial state, snapshot generation,
frontend and dispatch_qc are supplied infrastructure, not completed task credit.
The dashboard agreement badge compares the live replicas' balances, committed
chains, receipts and nonces.

## Tests

These framework checks pass in the unmodified starter:

```bash
python -m unittest discover -s tests -p 'test_framework.py' -v
```

The following are acceptance tests. In the unmodified starter they fail with
TODO errors; in this integrated working tree they all pass. Do not skip or
remove assertions.

```bash
python -m unittest discover -s tests -p 'test_task_a.py' -v
python -m unittest discover -s tests -p 'test_task_b.py' -v
python -m unittest discover -s tests -v
```

Task A uses empty blocks. Isolated Task B tests inject a committed-history fixture
instead of shipping a reference consensus implementation. This fixture is for
unit tests only; production execution must go through the actual Task A commit.
test_integration.py requires A and B together and retains six baseline cases.

Run the relevant optional tests only when claiming the corresponding extension:

```bash
python -m unittest discover -s extensions_tests -p 'test_recovery.py' -v
python -m unittest discover -s extensions_tests -p 'test_batch.py' -v
python -m unittest extensions_tests.test_transaction_security -v
```

In this integrated working tree these optional tests still fail because A6
(timeout/recovery) and B5 (batch configuration) are TODO; they are not part of
the 73-test base suite. See
[results/integration/optional-tests.txt](results/integration/optional-tests.txt).

The five recovery/fault cases plus six integration cases preserve all eleven
original regression tests. The B6 suite checks tampering, wrong-account
signatures, replay, nonce validation and receipts across four replicas. See the
[B6 verification log](results/extension_b6/verification.txt) for the test output
and the signed HTTP and CLI run.
Passing public tests is necessary evidence, not a complete grading rubric.

## Submission and demonstration

Follow the specification: report at most six main-text pages, slides, source,
tests/results, README, changes and individual contributions. Present for four
minutes, operate the running system live for four minutes, then answer questions
for two minutes. A prerecorded replacement earns 0/10 live-demonstration marks.

Record your starter version and final commit. Cite reused material and AI help;
copying the completed public reference into the TODOs is not original work.
