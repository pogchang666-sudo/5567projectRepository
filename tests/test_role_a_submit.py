"""AI-assisted tests; see changes.md."""
from copy import deepcopy
import unittest

from backend.hotstuff import HotStuffDemo


class RoleASubmitTests(unittest.TestCase):
    def setUp(self):
        self.demo = HotStuffDemo()

    def admission_state(self):
        return {
            "transactions": deepcopy(self.demo.transactions),
            "mempool": self.demo.mempool.copy(),
            "accounts": [node.machine.accounts.copy() for node in self.demo.nodes],
            "receipts": [deepcopy(node.machine.receipts) for node in self.demo.nodes],
            "events": list(self.demo.events),
            "log_sequence": self.demo.log_sequence,
        }

    def test_valid_admission_allocates_sequential_ids_without_execution(self):
        first = self.demo.submit("Alice", "Bob", 10)
        second = self.demo.submit("Alice", "Bob", 10)

        self.assertEqual((first.id, second.id), ("Tx1", "Tx2"))
        self.assertNotEqual(first, second)
        self.assertEqual(self.demo.mempool, ["Tx1", "Tx2"])
        self.assertEqual(self.demo.transactions, {"Tx1": first, "Tx2": second})
        self.assertTrue(all(node.machine.accounts["Alice"] == 100 for node in self.demo.nodes))
        self.assertTrue(all(not node.machine.receipts for node in self.demo.nodes))

    def test_amount_boundaries_are_accepted(self):
        self.assertEqual(self.demo.submit("Alice", "Bob", 1).amount, 1)
        self.assertEqual(self.demo.submit("Bob", "Charlie", 1_000_000).amount, 1_000_000)

    def test_invalid_amounts_raise_without_any_mutation(self):
        for amount in (0, -1, 1.5, True, False, 1_000_001, None, "1"):
            with self.subTest(amount=amount):
                before = self.admission_state()
                with self.assertRaises(ValueError):
                    self.demo.submit("Alice", "Bob", amount)
                self.assertEqual(self.admission_state(), before)

    def test_invalid_accounts_raise_without_any_mutation(self):
        for sender, receiver in (("Unknown", "Bob"), ("Alice", "Unknown"),
                                 (None, "Bob"), ("Alice", [])):
            with self.subTest(sender=sender, receiver=receiver):
                before = self.admission_state()
                with self.assertRaises(ValueError):
                    self.demo.submit(sender, receiver, 1)
                self.assertEqual(self.admission_state(), before)

    def test_rejected_request_does_not_consume_transaction_id(self):
        self.demo.submit("Alice", "Bob", 1)
        with self.assertRaises(ValueError):
            self.demo.submit("Alice", "Bob", 0)

        tx = self.demo.submit("Charlie", "Alice", 2)
        self.assertEqual(tx.id, "Tx2")
        self.assertEqual(self.demo.mempool, ["Tx1", "Tx2"])


if __name__ == "__main__":
    unittest.main()
