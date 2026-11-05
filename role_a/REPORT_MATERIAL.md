# 角色 A 报告素材（工作稿，非最终报告）

版本：2026-11-05，base `1d7d70b`。A1、A2、B1 均有实现与实测；完整 Task A/B 仍需组内集成。

## 2.1 Task A：提案与安全投票

### A1 `propose()`

当前实现从 `leader_id` 定位领导者，以该节点 `high_qc.block_id` 选择父区块，并从协调器已注册的 `qcs` 取得父证明。领导者崩溃时不构造提案，仅排入三 tick timeout；这只是提案侧入口，不代表 A6 完成。

新区块 ID 从当前区块数量开始递增并跳过冲突。空 mempool 使用空 payload；非空时调用 `select_transactions(parent)`，由 B2 负责选择及池保留策略。区块携带当前 view、leader、父 ID、父 QC 和有序 payload。协调器注册区块与空投票集合后，仅向未崩溃副本分发区块副本并入队 vote；函数不修改余额或提交历史。

### A2 `Node.extends()`

该函数从 `block_id` 沿本地 parent links 向回查找 `ancestor_id`，包含自身。使用 `visited` 防止循环；未知区块、非 Block 节点、断链或畸形谱系均返回 False。函数不修改节点状态。

### A2 `Node.can_vote()`

该函数依次检查区块类型、崩溃/withhold 状态、本地 view 与 `last_voted_view`，并要求提案 QC、LockedQC 及锁定区块有效。安全条件为“扩展 LockedQC 分支”或“提案 QC.view 严格大于 LockedQC.view”。直接子块在本地注册前也可识别为扩展；函数只返回布尔值，不记录投票。

### A2 `HotStuffDemo.vote()`

协调器先验证节点和区块存在且为预期接收者，再检查当前 leader/view、父块及其本地可用性、父 view 小于提案 view、已注册且完全匹配的父 QC。QC 还必须匹配父块/view，并包含至少三个不同、合法且无重复的节点 ID。

验证通过后调用 `can_vote()`；仅成功时更新 `last_voted_view` 并向 `votes[block_id]` 添加不同投票者。首次达到 quorum 时，通过 `qc_scheduled` 保证只入队一次 `("qc", block_id)`。无效提案在写入投票前返回 False；本函数不形成 QC、不提交区块、不执行交易。

证据：`backend/hotstuff.py`、`backend/node.py`、`tests/test_role_a_voting.py`、`results/role_a/role_a_all.txt`。

## 2.3 Task B：交易接收与交易池

`submit()` 要求 sender/receiver 为 `INITIAL_BALANCES` 中的账户名；金额使用 `type(amount) is int` 严格校验并限制在 `[1, 1_000_000]`，因此 bool、浮点数、None 和字符串均被拒绝。所有验证先于状态修改，失败统一抛出 ValueError。

有效交易按当前字典长度递增并跳过冲突，分配唯一 `TxN`，随后写入 `transactions` 并按顺序追加 `mempool`。相同请求的重复基础提交获得新 ID，不属于 B6 重放保护。该函数不检查最终资金、不修改账户余额或回执；payload 选择由 B2 负责，提交后的执行和清池由 C 负责。

证据：`backend/hotstuff.py::submit`、`tests/test_role_a_submit.py`、`results/role_a/http_submit.json`。

## 3.1 成员 A：测试与结果

环境：Windows，Python 3.13.14；`.venv` 中 FastAPI 0.162.0、Uvicorn 0.54.0。仓库根目录运行：

```bash
.venv/Scripts/python -m unittest discover -s tests -p 'test_role_a_*.py' -v
.venv/Scripts/python -m unittest discover -s tests -p 'test_framework.py' -v
.venv/Scripts/python backend/main.py
```

| 测试 ID | 覆盖内容 | 真实结果 / 证据 |
|---|---|---|
| A-T1 | HighQC、父 QC、唯一 ID、存活副本、空/非空池、崩溃 leader | **6/6 通过**；`test_role_a_propose.py` |
| A-T2 | 错 leader/view、无效/缺失父 QC、不可用及非接收节点、畸形输入 | 包含于 **A2 10/10 通过**；无效路径无投票/事件/账户副作用 |
| A-T3 | 同 view 重复投票、冲突提案、不同投票者与 QC 唯一调度 | 包含于 **A2 10/10 通过** |
| A-T4 | extends 自身/祖先/断链/循环；locked-branch 与严格 newer-QC；纯判断 | 包含于 **A2 10/10 通过** |
| A-T5 | 合法/边界金额、无效账户/金额、连续 ID、失败不耗 ID、接收不执行 | **5/5 通过**；`test_role_a_submit.py` |
| 合计 | 角色 A 三个定向测试文件 | **21/21 通过**；`results/role_a/role_a_all.txt` |
| 公开独立用例 | admission、lock/one-vote、invalid transaction inputs | **3/3 通过**；framework 另 **3/3 通过** |
| 完整公开集 | framework、Task A、Task B、integration | **6/17 通过，11 个错误均为 B/C TODO**；`public_after_role_a.txt` |
| HTTP | 4 次投票后等待 A3；交易接入 | STEP 5 后 next=qc，A3 TODO 时 STEP 保持 5；Tx1 入池且余额仍 100/100/100；`http_role_a.txt`、`http_submit.json` |

公开测试是必要而非充分证据；完整 Task A/B 尚不能声明完成。

## 4. 局限性与讨论（A 负责部分）

- A1 的非空 payload 集成依赖 B2；完整 QC、三链提交和 view change 依赖 B 的 A3～A5；最终执行、回执和清池依赖 C。
- 崩溃 leader 的提案侧仅调度 timeout；timeout/recover 未完成，不能声称 A6。A7、B6 均未实现。
- 系统在单进程中模拟四副本，以节点 ID 作为可信身份；不包含真实网络、门限签名或磁盘持久化。逻辑 step 不是分布式吞吐指标。

## AI 使用披露（须保留并与全组披露合并）

- 2026-11-04：WorkBuddy AI 辅助 `HotStuffDemo.propose()` 的单函数实现/调试及 `test_role_a_propose.py`。
- 2026-11-05：WorkBuddy AI 分别辅助 `Node.extends()`、`Node.can_vote()`、`HotStuffDemo.vote()` 的单函数实现/调试及 `test_role_a_voting.py`；辅助 `HotStuffDemo.submit()` 的单函数实现/调试及 `test_role_a_submit.py`。

所有上述代码和测试文件均有 AI-assisted 标注，`changes.md` 同步登记。AI 未实现 B/C 负责函数、A7 或 B6，也未完成整个 Task A、Task B 或完整项目。成员 A 须逐行审查并能在报告/Q&A 中解释全部辅助函数。

## 个人贡献陈述（当前工作稿，最终提交前更新）

本人负责 A1、A2、B1 及对应测试和报告。已完成 HighQC 选父与提案分发、本地谱系判断、安全投票规则、不同投票者记录、QC 唯一调度，以及交易严格校验、TxN 分配和入池。编写了 21 项定向测试并全部通过；相关公开独立用例、框架回归和 HTTP 路径均已验证。测试覆盖锁规则、每 view 一票、无效 QC、重复投票、严格金额类型、无效输入零副作用及接收不执行。完整 QC、提交、payload 和交易执行仍按小组接口等待联调，不将角色 A 模块完成表述为完整 Task A/B 完成。

## 个人贡献证据（工作记录）

- 成员：A（柳逸凡）；学号：［待填写］。
- 代码：`backend/hotstuff.py` 的 `propose()`、`vote()`、`submit()`；`backend/node.py` 的 `extends()`、`can_vote()`。
- 测试：`test_role_a_propose.py` 6 项、`test_role_a_voting.py` 10 项、`test_role_a_submit.py` 5 项。
- 结果：`results/role_a/`；最终 commit 哈希待本人审查后提交，不虚构。
