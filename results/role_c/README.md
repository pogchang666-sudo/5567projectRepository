# C 的 B3/B4 验证记录

`role-c` 从 `main@8266589` 分出。B 的共识提交和交易选择代码在 `role-b@ab002f7`。以下命令在仓库根目录的 VS Code PowerShell 终端执行。

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_role_c_*.py" -v
.\.venv\Scripts\python.exe tools/verify_role_c.py
```

第一条命令单独测试 C，结果为 [6/6](targeted-tests.txt)。第二条命令在临时目录组合本地 C 代码和上述 B 版本，不改变当前分支，基础测试 [73/73 通过](integration-tests.txt)。不组合 B 时，当前工作区的基础测试为 [36/44](main-base-tests.txt)，8 个错误均来自基线中尚未实现的共识或交易选择函数。可选扩展不在这 73 项内。

| 验收项 | 可复查的用例或证据 |
| --- | --- |
| C-T1 未提交不执行 | `test_mixed_batch_leaves_balances_and_receipts_untouched`：输入一批区块，其中一个还未提交，整批不产生回执。 |
| C-T2 顺序执行 | `test_block_and_payload_order_enable_later_transfers`：第二块中的两笔转账依赖之前到账的余额，最终 Alice/Bob/Charlie 为 300/0/0。 |
| C-T3 余额不足 | 双笔转账实验中，第二笔的回执为 `rejected`，错误为 `Insufficient funds`，Charlie 余额不变。 |
| C-T4 重复执行 | `test_insufficient_balance_and_same_id_retry`、`test_rejected_transaction_stays_rejected_after_balance_increases`：成功和失败的 ID 都复用首次回执。 |
| C-T5 副本一致 | 双笔实验中四个副本的提交链、账户余额和回执相同，每个副本的余额总和保持 300。 |
| C-T6 清理交易池 | `test_finalization_cleans_both_outcomes_and_preserves_pending_order`：两种结果均出池，其他待处理交易保留原顺序，再次清理不新增事件。 |

[四副本双笔转账记录](four-replica-transfers.json)：从 Alice 向 Bob、Charlie 各转 80。提交前四副本余额均为 100/100/100，两笔都在池中；第 20 步提交 B1，第一笔成功、第二笔被拒，余额变为 20/180/100，池为空。重放后余额、回执及交易池不变。

要在本地界面重现：运行 `.\.venv\Scripts\python.exe tools/verify_role_c.py --serve`，测试结束后打开 <http://127.0.0.1:8000/>。在初始状态连续提交上述两笔交易，然后单步推进至 B1 提交。可选 B6（签名、nonce、稳定 ID）未实现，演示仅覆盖基础任务。
