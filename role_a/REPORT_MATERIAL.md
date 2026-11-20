# 角色 A 报告素材（工作稿，非最终报告）

版本：2026-11-20，基于 `extension-b@f3b22d01`。A1、A2、B1 已集成；A6、B5 与 A7 已完成联合回归。

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

### A7 `inject_attack()`

A7 选择 equivocation＋duplicate_vote。当前 leader 构造两个同 view、同父块但 ID 不同的提案，并分发给存活副本；既有每 view 一票规则使第二分支无法形成 QC 或提交。重复投票仅重放攻击者自己的 vote 事件，集合去重和 `last_voted_view` 保证只记一次、只形成一个 QC。

攻击不直接写 QC、提交或余额，非法注入在状态修改前拒绝。A7 未修改 `vote()` 或 A6。集成后新增超时后新 leader 冲突提案、恢复后重复投票拒绝两项交叉测试，验证 pacemaker、recover 与攻击校验兼容。

证据：`extensions_tests/test_role_a_attacks.py`、`results/role_a/a6-a7-tests.txt`。

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
| 公开与基础集成 | public acceptance、A/B/C 定向测试 | **public 17/17；combined base 73/73**；`a6-a7-base-regression.txt` |
| A7＋联合扩展 | 冲突提案、重复投票、非法注入、A6/B5、超时攻击与恢复历史 | **A7 7/7；extensions 14/14；总计 87/87**；`a6-a7-tests.txt` |

公开测试是必要而非充分证据；当前工作副本的基础与已集成扩展测试共 87/87 通过。

## 4. 局限性与讨论（A 负责部分）

- A1 的非空 payload 集成依赖 B2；完整 QC、三链提交和 view change 依赖 B 的 A3～A5；最终执行、回执和清池依赖 C。
- A6 的 timeout/recover 已接入并通过与 A7 的交叉测试。A7 当前仅覆盖 equivocation 与 duplicate_vote；B6 尚未集成到本工作副本。
- 系统在单进程中模拟四副本，以节点 ID 作为可信身份；不包含真实网络、门限签名或磁盘持久化。逻辑 step 不是分布式吞吐指标。

## AI 使用披露（须保留并与全组披露合并）

- 2026-11-04：WorkBuddy AI 辅助 `HotStuffDemo.propose()` 的单函数实现/调试及 `test_role_a_propose.py`。
- 2026-11-05：WorkBuddy AI 分别辅助 `Node.extends()`、`Node.can_vote()`、`HotStuffDemo.vote()` 的单函数实现/调试及 `test_role_a_voting.py`；辅助 `HotStuffDemo.submit()` 的单函数实现/调试及 `test_role_a_submit.py`。
- 2026-11-20：WorkBuddy AI 辅助 A7 `HotStuffDemo.inject_attack()` 的单函数实现/调试及 `extensions_tests/test_role_a_attacks.py`（含 A6×A7 交叉测试）；未修改 A6 或 `vote()`。

所有上述代码和测试文件均有 AI-assisted 标注，`changes.md` 同步登记。本次集成未实现 B6，也未替代成员完成答辩准备。成员 A 须逐行审查并能在报告/Q&A 中解释全部辅助函数。

## 个人贡献陈述（当前工作稿，最终提交前更新）

本人负责 A1、A2、B1 及对应测试和报告，并主责 A7。已完成提案、安全投票、交易接入，以及 equivocation 和 duplicate_vote 攻击注入。角色 A 基础定向测试 21 项、A7 与交叉场景测试 7 项均通过；A6、B5 集成后总回归 87/87。A7 复用正常投票、QC 和提交路径，未修改 A6 或共享 `vote()`，并通过超时后攻击和恢复后投票历史两项联合验证。

## 个人贡献证据（工作记录）

- 成员：A（柳逸凡）；学号：［待填写］。
- 代码：`backend/hotstuff.py` 的 `propose()`、`vote()`、`submit()`、`inject_attack()`；`backend/node.py` 的 `extends()`、`can_vote()`。
- 测试：基础 21 项；A7 与 A6×A7 交叉测试 7 项。
- 结果：`results/role_a/a6-a7-base-regression.txt`、`a6-a7-tests.txt`。
