"""Receipt and balance checks for committed transactions."""

import unittest

from backend.blockchain import StateMachine
from backend.models import Transaction


class RoleCApplyTests(unittest.TestCase):
    def test_invalid_transfer_records_rejection_without_changing_balances(self):
        cases = [
            ("Unknown", "Bob", 1),
            ("Alice", "Unknown", 1),
            ("Alice", "Bob", True),
            ("Alice", "Bob", 0),
            ("Alice", "Bob", -1),
            ("Alice", "Bob", 1.5),
        ]
        for sender, receiver, amount in cases:
            with self.subTest(sender=sender, receiver=receiver, amount=amount):
                machine = StateMachine()
                receipt = machine.apply(Transaction("T1", sender, receiver, amount))
                self.assertEqual(machine.accounts, {"Alice": 100, "Bob": 100, "Charlie": 100})
                self.assertEqual(receipt["status"], "rejected")
                self.assertTrue(receipt["error"])
                self.assertEqual(machine.receipts["T1"], receipt)

    def test_rejected_transaction_stays_rejected_after_balance_increases(self):
        machine = StateMachine()
        transfer = Transaction("T1", "Alice", "Charlie", 101)
        original = machine.apply(transfer)
        self.assertEqual(original["status"], "rejected")

        credit = machine.apply(Transaction("T2", "Bob", "Alice", 1))
        self.assertEqual(credit["status"], "committed")
        self.assertIsNone(credit["error"])
        self.assertEqual(machine.apply(transfer), original)
        self.assertEqual(machine.accounts, {"Alice": 101, "Bob": 99, "Charlie": 100})
