"""Check the commit boundary and transaction order on one replica."""

import unittest

from backend.hotstuff import HotStuffDemo
from backend.models import Block, Transaction


class RoleCExecuteTests(unittest.TestCase):
    def test_crashed_replica_does_not_apply_a_committed_block(self):
        node = HotStuffDemo().nodes[0]
        node.blocks["X"] = Block("X", "B0", 1, 1, [Transaction("T1", "Alice", "Bob", 10)])
        node.committed_blocks.append("X")
        node.crashed = True

        node.execute_committed(["X"])
        self.assertEqual(node.machine.accounts, {"Alice": 100, "Bob": 100, "Charlie": 100})
        self.assertEqual(node.machine.receipts, {})

    def test_mixed_batch_leaves_balances_and_receipts_untouched(self):
        node = HotStuffDemo().nodes[0]
        node.blocks["X"] = Block("X", "B0", 1, 1, [Transaction("T1", "Alice", "Bob", 10)])
        node.blocks["Y"] = Block("Y", "X", 2, 2, [Transaction("T2", "Bob", "Charlie", 10)])
        node.committed_blocks.append("X")

        try:
            node.execute_committed(["X", "Y"])
        except ValueError:
            pass  # The public tests also allow explicit rejection.
        self.assertEqual(node.machine.accounts, {"Alice": 100, "Bob": 100, "Charlie": 100})
        self.assertEqual(node.machine.receipts, {})

    def test_block_and_payload_order_enable_later_transfers(self):
        node = HotStuffDemo().nodes[0]
        node.blocks["X"] = Block("X", "B0", 1, 1, [Transaction("T1", "Alice", "Bob", 10)])
        node.blocks["Y"] = Block("Y", "X", 2, 2, [
            Transaction("T2", "Bob", "Charlie", 110),
            Transaction("T3", "Charlie", "Alice", 210),
        ])
        node.committed_blocks.extend(["X", "Y"])

        node.execute_committed(["X", "Y"])
        self.assertEqual(node.machine.accounts, {"Alice": 300, "Bob": 0, "Charlie": 0})
        self.assertEqual({tx_id: r["status"] for tx_id, r in node.machine.receipts.items()},
                         {"T1": "committed", "T2": "committed", "T3": "committed"})
