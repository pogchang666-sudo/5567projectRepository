# Student change log

Starter version: 2026-09-29
Integration date: 2026-11-15
Final commit: TO FILL (the uploaded working tree has no `.git` directory)

| Student | Task item | Files and functions | Tests or evidence |
| --- | --- | --- | --- |
| A（柳逸凡） | A1 Proposal | `backend/hotstuff.py::HotStuffDemo.propose()` | `test_role_a_propose.py`：6/6 |
| A（柳逸凡） | A2 Safe voting | `HotStuffDemo.vote()`；`Node.extends()`、`Node.can_vote()` | `test_role_a_voting.py`：10/10；公开 lock/one-vote 用例通过 |
| A（柳逸凡） | B1 Admission | `backend/hotstuff.py::HotStuffDemo.submit()` | `test_role_a_submit.py`：5/5；公开 admission/invalid-input 用例通过 |
| B（姓名待填） | A3 Quorum certificate | `backend/hotstuff.py::HotStuffDemo.form_qc()` | `test_role_b_qc.py`：7/7；公开 quorum 用例通过 |
| B（姓名待填） | A4 Lock and commit | `backend/node.py::Node.receive_qc()` | `test_role_b_commit.py`：8/8；公开 one-QC 与三链用例通过 |
| B（姓名待填） | A5 Normal view change | `HotStuffDemo.next_view()`；`Node.enter_view()` | `test_role_b_view.py`：6/6 |
| B（姓名待填） | B2 Block payload | `HotStuffDemo.select_transactions()` | `test_role_b_payload.py`：8/8；公开 pool/ancestry 用例通过 |
| C（姓名待填） | B3 Execution | `StateMachine.apply()`；`Node.execute_committed()` | `test_role_c_apply.py`：2/2；`test_role_c_execute.py`：3/3 |
| C（姓名待填） | B4 Receipts and cleanup | `HotStuffDemo.finalize_transactions()` | `test_role_c_finalize.py`：1/1；四副本转账记录见 `results/role_c/` |

## Verification summary

| Suite | Tests | Result |
| --- | ---: | --- |
| Framework | 3 | 3/3 |
| Public acceptance (framework + Task A + Task B + integration) | 17 | 17/17 |
| Role A targeted | 21 | 21/21 |
| Role B targeted | 29 | 29/29 |
| Role C targeted | 6 | 6/6 |
| **Combined base suite** | **73** | **73/73** |

Evidence: `results/integration/full-tests.txt` and `results/integration/simulation.json`.
The end-to-end simulation executes both a successful transfer and an
insufficient-funds rejection; all four replicas stay consistent.

## Completed extensions

B6 adds Ed25519 signatures at admission and execution, stable transaction IDs,
per-account nonces and final receipt replay. See the signed-mode instructions
in `README.md` and `extensions_tests/test_transaction_security.py`.
A6 (timeout/recovery), A7 (malicious behavior), and B5 (batch limit) remain open.
The optional recovery/batch
tests currently report 1 pass, 1 failure and 5 errors; they are not part of the
73-test base suite. See `results/integration/optional-tests.txt`.

## Incomplete requirements

The base tasks A1–A5 and B1–B4 are implemented and the 73-test combined suite
passes. Remaining optional work:

- A6: `HotStuffDemo.timeout()`、`HotStuffDemo.recover()`；
- A7: `HotStuffDemo.inject_attack()` 与攻击路径校验；
- B5: `HotStuffDemo.configure_batch()`。

## Integration note

Role B's A3/A4/A5/B2 changes and Role C's B3/B4 changes touch disjoint
functions. The merged root uses Role B's `backend/hotstuff.py` and
`backend/node.py` as the base, then applies Role C's `StateMachine.apply()`,
`Node.execute_committed()` and `HotStuffDemo.finalize_transactions()`.
Role B/C test files and raw evidence were copied in; the two uploaded source
directories are preserved unchanged for provenance. See `INTEGRATION.md`.

## AI assistance disclosure

- 2026-11-04：WorkBuddy AI 辅助 `HotStuffDemo.propose()` 的单函数实现/调试与 `test_role_a_propose.py`。
- 2026-11-05：WorkBuddy AI 分别辅助 `Node.extends()`、`Node.can_vote()`、`HotStuffDemo.vote()` 的单函数实现/调试与 `test_role_a_voting.py`；辅助 `HotStuffDemo.submit()` 的单函数实现/调试与 `test_role_a_submit.py`。
- 角色 C（2026-11-08）：项目使用了部分 AI 生成的代码。C 部分涉及 `StateMachine.apply()` 的转账校验和回执去重、`Node.execute_committed()` 的提交校验和顺序执行，以及 `HotStuffDemo.finalize_transactions()` 的交易池清理；对应测试也使用了 AI 辅助。

角色 B 上传的 change log 未附 AI 使用声明；最终提交前需由 B 补充其实际使用情况。
角色 A 的 AI 辅助代码与测试保留 `AI-assisted` 标记；角色 C 的 AI 辅助函数已在
`StateMachine.apply()`、`Node.execute_committed()` 和 `finalize_transactions()`
处标注。角色 A 的详细说明见 `role_a/REPORT_MATERIAL.md`。

- B6（2026-11-20）：本分支使用了 AI 生成和验证的扩展代码，涵盖
  `backend/transaction_security.py` 的载荷、签名验证和 ID，
  `HotStuffDemo.submit()`、`_admit_signed()`、`_receipt_source()` 和
  `snapshot()` 的接收、回执和状态展示，
  `StateMachine.apply()` 的再次验签和 nonce，
  请求/交易模型、初始化、API、界面、签名客户端及 B6 测试。
