# 角色 A 交接说明

日期：2026-11-05。Base：`1d7d70b2c480cd67b60c4b2e581bdbdc31220dd2`（starter 2026-09-29）。建议分支：`role-a`；最终 commit 以该分支 HEAD 为准。

## 1. 已完成内容

| 模块 | 函数 | 实现要点 |
|---|---|---|
| A1 | `backend/hotstuff.py::propose()` | HighQC 选父、父 QC、唯一区块 ID、空/非空池接口、存活副本分发、vote 事件 |
| A2 | `backend/node.py::extends()` | 本地 parent 链、含自身、断链/循环/畸形谱系拒绝、无副作用 |
| A2 | `backend/node.py::can_vote()` | availability、当前 view、每 view 一票、locked-branch 或严格 newer-QC |
| A2 | `backend/hotstuff.py::vote()` | leader/view/parent/QC 和本地提案一致性验证、不同投票者、QC 唯一调度 |
| B1 | `backend/hotstuff.py::submit()` | 账户/严格整数/金额边界校验、唯一 TxN、入池但不执行 |

新增测试：`test_role_a_propose.py` 6 项、`test_role_a_voting.py` 10 项、`test_role_a_submit.py` 5 项，共 **21/21 通过**。公开独立用例及 framework 合计 **6/6 通过**；完整公开集为 **6/17**，其余 11 个错误均来自 B/C TODO。

原始证据：`results/role_a/`。HTTP 已验证四副本投票后在 A3 等待，以及 Tx1 入池且余额保持 100/100/100。

## 2. 需要 B 完成

1. `select_transactions(parent)`：读取 `transactions`/`mempool`；默认最多 5 笔；仅排除所选父链已有 ID；废弃分支可重打包；选择时不清池。
2. `form_qc(block_id)`：消费 `votes[block_id]: set[int]`；同一区块/view 至少 3 个不同有效投票者；注册 QC 后调用 `dispatch_qc(qc)`，再入队 `("next_view", "QC")`。
3. `Node.receive_qc(qc)`：更新 HighQC/LockedQC；仅连续 view 的直接关联认证三链提交；祖先优先；单 QC 不提交自身；不执行交易。
4. `next_view()`、`Node.enter_view()`：保留 QC/锁/提交/投票历史，轮换 leader并排入下一提案；崩溃副本冻结。
5. 先跑通空区块 Task A，再做 B5/A6；A7 启动时由 B 审查 A2 与 QC/提交路径。

当前交接点：A 已产生提案和投票，首次达到 3 票时只入队一次 `("qc", block_id)`；B 从该事件继续。不得降低 quorum=3。

## 3. 需要 C 完成

1. `Node.execute_committed()`：仅处理本地已提交 ID；任何状态变化前先验证全部 ID；按区块及 payload 顺序执行；崩溃副本不执行。
2. `StateMachine.apply()`：检查账户、严格正整数和余额；成功/失败均生成最终回执；同一交易 ID 幂等；余额不足不改余额。
3. `finalize_transactions(committed_ids)`：仅清理已提交交易（含 rejected），重复调用幂等；不执行转账、不决定共识。
4. 与 B 的 `dispatch_qc()` 路径集成，不得把“有 QC/有提案”当作“已提交”。
5. B6 启动前向 A 冻结 canonical payload、签名、nonce、稳定 ID、Transaction/请求字段及错误语义；A 再配合 `submit()` 接收入口。

当前交接点：A 的 `submit()` 只负责有效入池且不改余额；交易在提交前留在 mempool。B2 选择、C 执行/清池尚未接入。

## 4. 需要 D 完成

1. 获取并审查 `role-a` 分支，记录实际 commit；合并 B/C 对应分支。
2. 只处理构建、依赖、配置和打包冲突；涉及算法语义的问题交回函数所有者，不重写算法。
3. 按 `role_a/REPORT_MATERIAL.md` 和 `results/role_a/` 整合 A 的报告事实；收齐 B/C 素材后统一排版、PPT 和贡献表。
4. 最终运行全部公开测试及扩展声明对应测试，检查 README、changes、结果和 ZIP 内容；不得包含 `.venv`、依赖目录或演示视频。

## 5. 集成顺序与验收

```text
B 完成 A3～A5 → 空区块 Task A 全绿
→ B 完成 B2、C 完成 B3/B4 → Task B 与 integration 全绿
→ 全组确认基础功能 → 再决定 A6/A7/B5/B6
```

最终验收：公开测试不删/跳断言；正确副本的提交链、余额、回执一致；总余额 300；两票不能形成 QC；单 QC 不提交自身；失败交易也有最终回执且不重复执行。

复现命令（仓库根目录）：

```bash
.venv/Scripts/python -m unittest discover -s tests -p 'test_role_a_*.py' -v
.venv/Scripts/python -m unittest discover -s tests -p 'test_framework.py' -v
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python backend/main.py
```

## 6. AI 使用披露（必须保留）

AI 分别辅助了上述 5 个函数的实现/调试及 3 个测试文件。源代码和测试文件均有 `AI-assisted` 标注；详情见 `changes.md` 与 `role_a/REPORT_MATERIAL.md`。AI 未实现 B/C 函数、A7、B6，也未完成整个 Task A/B。整合时不得删除披露；各成员答辩前须能解释所负责的代码。
