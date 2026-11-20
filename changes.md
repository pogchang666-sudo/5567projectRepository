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
| Combined base suite | 73 | 73/73 |
| A6 recovery/fault cases | 5 | 5/5 |
| B5 batch configuration | 2 | 2/2 |
| A7 attacks（含 2 项 A6×A7 交叉场景） | 7 | 7/7 |
| **Total** | **87** | **87/87** |

Evidence: `results/role_a/a6-a7-base-regression.txt` and `a6-a7-tests.txt`.
The joint scenarios cover equivocation after timeout and vote-history preservation
after recovery.

## Completed extensions

- A6：`timeout()`、`recover()`，来自 `extension-b@f3b22d01`。
- B5：`configure_batch()`，来自同一扩展分支。
- A7：`inject_attack()` 支持 equivocation 与 duplicate_vote；复用正常 vote/QC/commit 路径，未修改 A6 或共享 `vote()`。

## Incomplete requirements

B6：`sign_transaction()`、`verify_transaction()`、`transaction_id()`、nonce/重放处理尚未集成到本工作副本。

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
- 角色 A（2026-11-20）：WorkBuddy AI 辅助 A7 `HotStuffDemo.inject_attack()` 的单函数实现/调试及 `extensions_tests/test_role_a_attacks.py`（含 A6×A7 交叉测试）；复用现有 vote/QC/commit 校验，未修改 `vote()`、`timeout()`、`recover()`、`form_qc()` 或 `receive_qc()`。

角色 B 上传的 change log 未附 AI 使用声明；最终提交前需由 B 补充其实际使用情况。
角色 A/C 的 AI 辅助代码和测试均保留 `AI-assisted` 标记。本次 A7 集成未修改 A6/B5
函数，也未实现 B6 或替代成员完成答辩准备。
