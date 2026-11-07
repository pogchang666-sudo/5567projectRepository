import unittest

from backend.hotstuff import HotStuffDemo
from backend.models import Block


class RoleBPayloadTests(unittest.TestCase):
    def setUp(self):
        self.demo = HotStuffDemo()
        self.demo.events.clear()
        self.genesis = self.demo.blocks["B0"]

    def submit(self, count):
        return [self.demo.submit("Alice", "Bob", 1) for _ in range(count)]

    def test_empty_pool_returns_an_empty_payload(self):
        self.assertEqual(self.demo.select_transactions(self.genesis), [])

    def test_default_limit_is_five(self):
        self.submit(7)

        self.assertEqual(len(self.demo.select_transactions(self.genesis)), 5)

    def test_selection_follows_pool_order(self):
        transactions = self.submit(4)

        selected = self.demo.select_transactions(self.genesis)

        self.assertEqual([tx.id for tx in selected], [tx.id for tx in transactions])

    def test_transactions_on_the_parent_chain_are_excluded(self):
        transactions = self.submit(7)
        block = Block("X", "B0", 1, 1, transactions[:5], self.demo.qcs["B0"])
        self.demo.blocks["X"] = block

        selected = self.demo.select_transactions(block)

        self.assertEqual([tx.id for tx in selected], [tx.id for tx in transactions[5:]])

    def test_an_abandoned_branch_does_not_exclude_transactions(self):
        transactions = self.submit(3)
        abandoned = Block("X", "B0", 1, 1, transactions, self.demo.qcs["B0"])
        self.demo.blocks["X"] = abandoned

        selected = self.demo.select_transactions(self.genesis)

        self.assertEqual([tx.id for tx in selected], [tx.id for tx in transactions])

    def test_selection_does_not_consume_the_pool(self):
        self.submit(6)

        self.demo.select_transactions(self.genesis)
        self.demo.select_transactions(self.genesis)

        self.assertEqual(len(self.demo.mempool), 6)

    def test_deep_ancestry_is_excluded(self):
        transactions = self.submit(6)
        first = Block("B1", "B0", 1, 1, transactions[:2], self.demo.qcs["B0"])
        second = Block("B2", "B1", 2, 2, transactions[2:4], first.qc)
        self.demo.blocks["B1"] = first
        self.demo.blocks["B2"] = second

        selected = self.demo.select_transactions(second)

        self.assertEqual([tx.id for tx in selected], [tx.id for tx in transactions[4:]])

    def test_empty_payload_blocks_are_still_proposable(self):
        self.assertEqual(self.demo.select_transactions(self.genesis), [])
        self.demo.propose(None)

        self.assertEqual(self.demo.blocks["B1"].transactions, [])


if __name__ == "__main__":
    unittest.main()
