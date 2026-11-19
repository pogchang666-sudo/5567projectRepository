"""Check pool cleanup and repeat delivery after per-replica execution."""

import unittest

from backend.hotstuff import HotStuffDemo
from backend.models import Block


class RoleCFinalizeTests(unittest.TestCase):
    def test_finalization_cleans_both_outcomes_and_preserves_pending_order(self):
        demo = HotStuffDemo()
        first = demo.submit("Alice", "Bob", 1)
        success = demo.submit("Alice", "Bob", 80)
        last = demo.submit("Alice", "Bob", 1)
        rejected = demo.submit("Alice", "Charlie", 80)
        block = Block("X", "B0", 1, 1, [success, rejected])
        demo.blocks[block.id] = block
        for node in demo.nodes:
            node.blocks[block.id] = block
            node.committed_blocks.append(block.id)
            for tx in block.transactions:
                node.machine.apply(tx)

        log_count = len(demo.logs)
        demo.finalize_transactions([block.id])
        logs_after_first_call = list(demo.logs)
        events = logs_after_first_call[log_count:]
        self.assertEqual([e["kind"] for e in events], ["transaction", "transaction"])
        self.assertIn(success.id, events[0]["message"])
        self.assertIn("committed", events[0]["message"])
        self.assertIn(rejected.id, events[1]["message"])
        self.assertIn("rejected", events[1]["message"])
        demo.finalize_transactions([block.id])

        self.assertEqual(demo.mempool, [first.id, last.id])
        self.assertEqual(list(demo.logs), logs_after_first_call)
        for node in demo.nodes:
            self.assertEqual(node.machine.accounts, {"Alice": 20, "Bob": 180, "Charlie": 100})
            self.assertEqual(node.machine.receipts[rejected.id]["status"], "rejected")
