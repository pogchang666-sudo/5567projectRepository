# 接口冻结草案（待 A/B/C 确认）

来源：starter `1d7d70b2c480cd67b60c4b2e581bdbdc31220dd2`，`starter_version=2026-09-29`。事实已核对源码；“冻结”状态待组内确认。

## 1. 环境与模型

- Python ≥3.10；本机 3.13.14。依赖：`fastapi>=0.115,<1`、`uvicorn>=0.30,<1`。
- `Transaction(id: str, sender: str, receiver: str, amount: int)`，frozen dataclass。
- `QC(block_id: str, view: int, voters: tuple[int, ...])`，frozen dataclass。
- `Block(id, parent_id, view, proposer, transactions=[], qc=None)`；`qc` 是父区块证明，不是自身证明。
- 固定 4 副本、`QUORUM=3`；`leader_id=(view-1)%4+1`；初始 B0/QC(B0)、view 1、每账户 100。

## 2. 共享数据与事件

| 数据 | starter 类型 / 约定 |
|---|---|
| `blocks` | `dict[block_id, Block]`，协调器注册提案 |
| `qcs` | `dict[block_id, QC]`，仅注册有效证书 |
| `transactions` | `dict[tx_id, Transaction]` |
| `mempool` | `list[tx_id]`；提交前保留，含已进入未提交提案的交易 |
| `votes` | `dict[block_id, set[node_id]]`；A 写，B 读；同一区块/view 去重 |
| `qc_scheduled` | `set[block_id]`；防止重复 QC 调度 |
| `node.blocks` | 各副本本地区块及 parent links |
| `node.high_qc/locked_qc` | B 在 QC/提交路径维护；A 在投票规则中读取 |
| `node.last_voted_view` | A 写；保证每副本每 view 最多一票 |

事件只使用：`("propose", None)`、`("vote", (node_id, block_id))`、`("qc", block_id)`、`("next_view", "QC"|"timeout")`、`("timeout", remaining)`。不得另建并行消息通道。

## 3. 函数签名与交接

| 所有者 | 函数 | 输入/返回与交接 |
|---|---|---|
| A | `HotStuffDemo.propose(self, _)` | 无显式返回；用 leader HighQC 选 parent；仅非空池调用 B2；向存活副本分发并入队 vote |
| A | `HotStuffDemo.vote(self, data)` | `data=(node_id, block_id)`；验证并记录投票；首次达 quorum 入队一次 qc |
| A | `Node.extends(self, block_id: str, ancestor_id: str) -> bool` | 本地 parent 链判断，含自身；异常谱系 False；无副作用 |
| A | `Node.can_vote(self, block: Block) -> bool` | availability/view/每 view 一票/safe-node；无副作用 |
| A | `HotStuffDemo.submit(self, sender: str, receiver: str, amount: int) -> Transaction` | 无效抛 ValueError 且零副作用；有效分配 TxN 并入池；B2 读取 |
| B | `form_qc(self, block_id)` | 消费 votes；≥3 个不同有效投票者；注册 QC→`dispatch_qc(qc)`→next_view |
| B | `Node.receive_qc(self, qc: QC) -> list[str]` | 更新 HighQC/LockedQC；返回祖先优先的新提交 ID；不执行交易 |
| B | `next_view(self, reason)`；`Node.enter_view(self, view: int, leader_id: int)` | 保留协议状态、轮换 leader、入队下一提案；崩溃副本冻结 |
| B | `select_transactions(self, parent: Block) -> list[Transaction]` | 默认≤5；排除所选父链 ID；不清池；允许空列表 |
| C | `Node.execute_committed(self, block_ids: list[str])` | 仅执行本地已提交 ID；先验证再改状态；按区块/payload 顺序 |
| C | `StateMachine.apply(self, tx: Transaction) -> dict` | committed/rejected 回执；同 ID 幂等；不是接入口 |
| C | `finalize_transactions(self, committed_ids: list[str])` | 清除已提交（含 rejected）交易；重复调用幂等；不执行/不决定共识 |

## 4. 不得破坏的集成契约

1. `propose()` 空池直接使用 `[]`，使 Task A 可脱离 Task B。
2. `form_qc()` 验证并注册 QC 后调用已给 `dispatch_qc()`；`receive_qc()` 不执行交易。
3. `dispatch_qc()` 仅对新提交的非空区块调用 C 的执行与 finalize；不得用 QC 代替 commit。
4. 投票/锁定规则不碰交易；`submit()` 不碰余额；失败执行也可属于已提交区块。
5. 无效输入/提案不得留下部分状态；quorum 永远为 3；公开测试断言不得删除或跳过。
6. A7/B6 的额外字段与验证须先协商；跨所有者函数由对应负责人修改。

确认栏：A［待确认］ B［待确认］ C［待确认］；D 记录集成要求［待确认］。
