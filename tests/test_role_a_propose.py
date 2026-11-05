"""AI-assisted tests; see changes.md."""
import unittest

from backend.hotstuff import HotStuffDemo
from backend.models import Block, QC, Transaction


class RoleAProposalTests(unittest.TestCase):
    def setUp(self):
        self.demo = HotStuffDemo()
        self.demo.events.clear()  # Directly invoke propose without step().

    def test_empty_proposal_uses_high_qc_and_preserves_state(self):
        balances = [node.machine.accounts.copy() for node in self.demo.nodes]

        self.demo.propose(None)

        block = self.demo.blocks["B1"]
        self.assertEqual((block.parent_id, block.view, block.proposer), ("B0", 1, 1))
        self.assertEqual(block.transactions, [])
        self.assertEqual(block.qc, self.demo.qcs["B0"])
        self.assertEqual(self.demo.votes["B1"], set())
        self.assertEqual(
            list(self.demo.events),
            [("vote", (node_id, "B1")) for node_id in range(1, 5)],
        )
        for node, before in zip(self.demo.nodes, balances):
            self.assertIn("B1", node.blocks)
            self.assertEqual(node.machine.accounts, before)
            self.assertEqual(node.committed_blocks, ["B0"])

    def test_proposal_follows_current_leaders_high_qc(self):
        parent = Block("B1", "B0", 1, 1, [], self.demo.qcs["B0"])
        parent_qc = QC("B1", 1, (1, 2, 3))
        self.demo.blocks["B1"] = parent
        self.demo.qcs["B1"] = parent_qc
        self.demo.view = 2
        for node in self.demo.nodes:
            node.view = 2
            node.blocks["B1"] = parent
            node.high_qc = parent_qc

        self.demo.propose(None)

        block = self.demo.blocks["B2"]
        self.assertEqual((block.parent_id, block.view, block.proposer), ("B1", 2, 2))
        self.assertEqual(block.qc, parent_qc)

    def test_crashed_nonleader_is_not_a_recipient(self):
        self.demo.nodes[3].crashed = True

        self.demo.propose(None)

        self.assertNotIn("B1", self.demo.nodes[3].blocks)
        self.assertEqual(
            list(self.demo.events),
            [("vote", (node_id, "B1")) for node_id in range(1, 4)],
        )

    def test_nonempty_pool_delegates_selection_without_consuming_pool(self):
        tx = Transaction("Tx1", "Alice", "Bob", 10)
        self.demo.transactions[tx.id] = tx
        self.demo.mempool.append(tx.id)
        calls = []

        def select_transactions(parent):
            calls.append(parent.id)
            return [tx]

        self.demo.select_transactions = select_transactions
        self.demo.propose(None)

        self.assertEqual(calls, ["B0"])
        self.assertEqual(self.demo.blocks["B1"].transactions, [tx])
        self.assertEqual(self.demo.mempool, ["Tx1"])

    def test_crashed_leader_schedules_timeout_without_proposal(self):
        self.demo.nodes[0].crashed = True

        self.demo.propose(None)

        self.assertEqual(list(self.demo.blocks), ["B0"])
        self.assertEqual(self.demo.votes, {})
        self.assertEqual(list(self.demo.events), [("timeout", 3)])

    def test_block_id_is_unique(self):
        self.demo.blocks["B1"] = Block("B1", "B0", 1, 1, [], self.demo.qcs["B0"])

        self.demo.propose(None)

        self.assertIn("B2", self.demo.blocks)
        self.assertEqual(self.demo.votes["B2"], set())


if __name__ == "__main__":
    unittest.main()
