# Student change log

Starter version: 2026-09-29
Final commit: TO FILL

| Student | Task item | Files and functions | Tests or evidence |
| --- | --- | --- | --- |
| A（柳逸凡） | A1 Proposal | `backend/hotstuff.py::HotStuffDemo.propose()` | `test_role_a_propose.py`：6/6 |
| A（柳逸凡） | A2 Safe voting | `HotStuffDemo.vote()`；`Node.extends()`、`Node.can_vote()` | `test_role_a_voting.py`：10/10；公开 lock/one-vote 用例通过 |
| A（柳逸凡） | B1 Admission | `backend/hotstuff.py::HotStuffDemo.submit()` | `test_role_a_submit.py`：5/5；公开 admission/invalid-input 用例通过 |
| B（姓名待填） | A3 Quorum certificate | `backend/hotstuff.py::HotStuffDemo.form_qc()` | `test_role_b_qc.py`：7/7；公开 quorum 用例通过 |
| B（姓名待填） | A4 Lock and commit | `backend/node.py::Node.receive_qc()` | `test_role_b_commit.py`：8/8；公开 one-QC 与三链用例通过 |
| B（姓名待填） | A5 Normal view change | `HotStuffDemo.next_view()`；`Node.enter_view()` | `test_role_b_view.py`：6/6 |
| B（姓名待填） | B2 Block payload | `HotStuffDemo.select_transactions()` | `test_role_b_payload.py`：8/8；公开 pool/ancestry 用例通过 |

角色 A 定向测试合计 21/21；framework 3/3；原始输出见 `results/role_a/`。
角色 B 定向测试合计 29/29；HTTP 演示记录见 `results/role_b/`。

## Completed extensions

None. A1 的崩溃 leader timeout 调度不构成 A6 完成。

## Incomplete requirements

角色 A 的 A1、A2、B1 与角色 B 的 A3、A4、A5、B2 已完成模块实现与独立测试。B3、B4（`Node.execute_committed`、`StateMachine.apply`、`finalize_transactions`）尚未实现，端到端集成待其完成；HTTP 记录显示提交带交易区块时停在 `TODO B3`。A6/A7/B5/B6 未实现。完整公开集当前 11/17 通过，6 个错误均来自 B3/B4。

## AI assistance disclosure

- 2026-11-04：WorkBuddy AI 辅助 `HotStuffDemo.propose()` 的单函数实现/调试与 `test_role_a_propose.py`。
- 2026-11-05：WorkBuddy AI 分别辅助 `Node.extends()`、`Node.can_vote()`、`HotStuffDemo.vote()` 的单函数实现/调试与 `test_role_a_voting.py`；辅助 `HotStuffDemo.submit()` 的单函数实现/调试与 `test_role_a_submit.py`。

所有 AI 辅助代码和测试文件均已标注 AI-assisted；详细说明见 `role_a/REPORT_MATERIAL.md`。AI 未实现 B/C 函数、A7、B6，也未完成整个 Task A、Task B 或完整项目。
