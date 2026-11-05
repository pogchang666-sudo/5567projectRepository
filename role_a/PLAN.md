# 角色 A：依赖与行动路径

日期：2026-11-04。依据：project 下 3 份 PDF、2 份 DOCX 及 starter `1d7d70b`。

## 1. 职责边界

| 工作 | 分值 | 角色 A 所有权 | 不负责的边界 |
|---|---:|---|---|
| A1 提案 | 6 | `HotStuffDemo.propose()` | 不形成 QC、不提交区块 |
| A2 安全投票 | 8 | `vote()`、`Node.extends()`、`Node.can_vote()` | 不统计/生成 QC，不执行交易 |
| B1 交易接收 | 5 | `submit()`：校验、Tx ID、入池 | 不选 payload、不清池、不改余额 |
| 模块测试 | — | A-T1～A-T5、代码与真实输出 | 无专职测试角色；D 不代测 |
| 报告素材 | — | 2.1、2.3、3.1、A 的局限/贡献/AI 披露 | D 只整合排版，不代写技术事实 |
| A7（可选，基础完成后） | 3 | 主责 `inject_attack()` 与攻击测试；B 审查 | 跨 B 函数的修改须协商，由所有者实施 |
| B6 配合（可选） | 3 | 配合 C 改造 `submit()` 的验签/重放入口 | C 主责签名、nonce、稳定 ID 与执行安全 |

A6、B5 属 B；B2～B5 的其他部分按 DOCX 分工执行。最终交付给 D：独立代码/提交、测试文件与结果、报告素材、已知限制、个人半页贡献陈述及组贡献表证据。

## 2. 先判断依赖

| 工作 | 开发是否等待他人 | 具体依赖 / 可先做部分 |
|---|---|---|
| A1 空区块提案 | 否 | 用 HighQC、现有 Block/QC、事件队列即可完成；本次已完成。 |
| A1 非空 payload | **联调依赖 B** | `propose()` 仅在 mempool 非空时调用 B 的 `select_transactions(parent)`；约定返回有序 payload 且不清池。当前已用测试替身验证接口。 |
| A1 完整空链 | **联调依赖 B** | A2 投票后，B 的 `form_qc()`、`receive_qc()`、`next_view()`/`enter_view()` 才能形成 QC、三链提交并换 view；空链不依赖 C。 |
| A2 三函数 | 否（单测）；**端到端依赖 B** | 可用自制区块/QC fixture 开发。B 消费 `votes[block_id]: set[int]`；达 quorum 时 A 只入队一次 `("qc", block_id)`，B 负责生成 QC。锁/QC 的持续推进由 B 维护。 |
| B1 `submit()` | 否（单测）；**联调依赖 B、C** | B 读取 `transactions`/`mempool` 选 payload；C 在提交后清理已处理 ID。A 只负责有效入池、无效零副作用、接收不改余额。 |
| A-T1～A-T5 | 模块测试不等他人；**集成证据等 B/C** | A 自己编写并运行。完整转账、余额、回执、端到端失败案例须 B/C 合并后取得。 |
| 接口冻结草案 | 否；**最终冻结等 A/B/C** | 已按 starter 写成草案；A/B/C 确认，D 记录集成要求。 |
| 报告工作稿 | 否；**最终事实等自身实现与真实联调** | 可先写 A1 实测内容。A2/B1 机制、A-T2～A-T5 结果不得预写“通过”；D 的最终排版不阻塞 A 供稿。 |
| A7 | **是，置后** | 等全部基础功能完成；依赖 B 对 QC/提交路径审查，跨 `form_qc()`/`receive_qc()` 的改动须所有者配合。必须自写攻击测试。 |
| B6 配合 | **是，置后** | 等 C 提供 canonical payload、签名/nonce/稳定 ID、Transaction/请求字段及错误语义；再改 A 的接收入口并联调重放。 |
| 演示/最终提交 | **是** | 等 A/B/C 基础功能与集成测试；D 合并、报告/PPT/打包。全员准备 Q&A，演示必须实时操作。 |

## 3. 实施顺序与验收

### P0｜合规、版本、接口（已完成）
- [x] 克隆 starter，记录 base `1d7d70b2c480cd67b60c4b2e581bdbdc31220dd2`、starter version `2026-09-29`。
- [x] 基线：framework 3/3 通过；Task A 3 个、Task B 5 个验收测试均因 TODO 失败。
- [x] 建立 `.venv` 并安装依赖；`pip check` 无冲突，HTTP 启动/首步提案已验证。
- [x] 形成 `INTERFACE_FREEZE_DRAFT.md`；待 A/B/C 签字确认。
- 验收：不改 quorum=3、事件名、公开签名、API/UI；AI 仅辅助单函数且代码/报告留痕。

### P1｜A1 提案（已完成）
- [x] HighQC 选父、唯一 ID、当前 leader/view、父 QC、存活副本分发、投票集合/事件。
- [x] 空池绕过 B2；非空池委托 B2；崩溃 leader 仅调度 timeout，不声称 A6 完成。
- 验收：`test_role_a_propose.py` 6/6；余额/提交历史不变。

### P2｜A2 安全投票（2026-11-05 已完成）
- [x] `extends()`：本地 parent 链、含自身、断链/循环保护、纯函数。
- [x] `can_vote()`：availability、当前 view、每 view 一票、locked-branch/newer-QC，且无状态修改。
- [x] `vote()`：leader/view/parent/注册 QC 验证；记录不同投票人；首次达 3 票只入队一次 QC。
- 验收：`test_role_a_voting.py` 10/10；错 leader/view、无效 QC、重复投票、不安全分支、不可用节点及零副作用均覆盖。

### P3｜B1 交易接收（2026-11-05 已完成）
- [x] 账户与严格整数校验、金额边界、连续唯一 TxN、交易字典与 mempool 插入。
- [x] 所有验证先于状态修改；无效请求抛 ValueError；接收不执行、不改余额。
- 验收：`test_role_a_submit.py` 5/5；公开 admission/invalid-input 用例通过。

### P4｜A/B/C 集成（等待对应代码，按序执行）
1. 与 B：空区块跑通 STEP 1/6/7/13/20；QC(B3) 才提交 B1；检查每 view 一票与 QC 事件唯一。
2. 与 B+C：正常转账、7 笔分批、废弃分支重打包、余额不足、重复执行、回执/清池、副本一致性。
3. 运行全部公开测试，不删/跳断言；保留真实输出到 `results/role_a/`。
4. 向 D 提交修改函数清单、测试命令/输出、已知限制和 commit。

验收：公开 framework/Task A/Task B/integration 全绿；正确副本的提交链、余额、回执一致；总余额 300；两票不能形成 QC。

### P5｜可选扩展（仅在 P4 全绿后）
- A7：先 equivocation，再 duplicate_vote 或 invalid_qc；拒绝无效证据、无冲突提交；B 审查并留存测试证据。withholding 不计 A7。
- B6：C 冻结安全接口后，A 在 `submit()` 入口验签/处理相同重试；错误签名/nonce 零副作用；联调提交前后重放。若声称恢复支持，还需 B 的 A6 保留 nonce/回执。

### P6｜报告与演示
- 建议 11/19 前交基础报告素材，11/22 前交最终实测证据；11/28 前完成彩排。
- 11/29 实时演示；12/2 23:59 前由 D 完成 Canvas 打包提交。
- A 的报告验收：2.1/2.3 与实际代码一致；3.1 含命令、通过数、日志路径、commit；局限和 AI 披露真实；无未替换占位符；全组正文≤6页。

## 4. 复现命令（仓库根目录）

```bash
# 首次配置（Windows / Git Bash）
python -m venv .venv
.venv/Scripts/python -m pip install --index-url https://pypi.org/simple -r requirements.txt

# 测试与启动
.venv/Scripts/python -m unittest discover -s tests -p 'test_framework.py' -v
.venv/Scripts/python -m unittest discover -s tests -p 'test_role_a_*.py' -v
.venv/Scripts/python -m unittest discover -s tests -p 'test_task_a.py' -v
.venv/Scripts/python -m unittest discover -s tests -p 'test_task_b.py' -v
.venv/Scripts/python -m unittest discover -s tests -v
.venv/Scripts/python backend/main.py
```

公开测试是必要而非充分证据；当前声明 A1、A2、B1 的模块实现与独立测试完成，不声明完整 Task A/B、A6/A7/B6 或完整项目完成。
