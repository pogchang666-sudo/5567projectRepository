import unittest

from backend.hotstuff import HotStuffDemo
from backend.models import Block


class RoleBQuorumCertificateTests(unittest.TestCase):
    @staticmethod
    def demo_with_votes(voters, view=1, payload=None):
        demo = HotStuffDemo()
        demo.events.clear()
        block = Block("B1", "B0", view, 1, payload or [], demo.qcs["B0"])
        demo.blocks["B1"] = block
        for node in demo.nodes:
            node.blocks["B1"] = block
        demo.votes["B1"] = set(voters)
        return demo, block

    def test_three_distinct_voters_form_a_certificate(self):
        demo, block = self.demo_with_votes({1, 2, 3})
        certificate = demo.form_qc("B1")

        self.assertEqual(demo.qcs["B1"], certificate)
        self.assertEqual(certificate.block_id, "B1")
        self.assertEqual(certificate.view, block.view)
        self.assertEqual(certificate.voters, (1, 2, 3))

    def test_two_votes_never_form_a_certificate(self):
        demo, _ = self.demo_with_votes({1, 2})

        with self.assertRaises(ValueError):
            demo.form_qc("B1")
        self.assertNotIn("B1", demo.qcs)

    def test_unknown_block_is_rejected(self):
        demo, _ = self.demo_with_votes({1, 2, 3})

        with self.assertRaises(ValueError):
            demo.form_qc("B9")
        self.assertNotIn("B9", demo.qcs)

    def test_voters_outside_the_replica_set_do_not_count(self):
        demo, _ = self.demo_with_votes({1, 2, 0, 9})

        with self.assertRaises(ValueError):
            demo.form_qc("B1")
        self.assertNotIn("B1", demo.qcs)

    def test_certificate_voters_are_sorted_and_unique(self):
        demo, _ = self.demo_with_votes({4, 2, 3, 1})

        certificate = demo.form_qc("B1")

        self.assertEqual(certificate.voters, (1, 2, 3, 4))
        self.assertEqual(len(set(certificate.voters)), len(certificate.voters))

    def test_certificate_is_dispatched_to_every_replica(self):
        demo, _ = self.demo_with_votes({1, 2, 3})

        demo.form_qc("B1")

        self.assertEqual([node.high_qc.block_id for node in demo.nodes], ["B1"] * 4)
        self.assertEqual(demo.events[-1], ("next_view", "QC"))

    def test_forming_a_certificate_executes_no_transactions(self):
        demo = HotStuffDemo()
        demo.events.clear()
        transaction = demo.submit("Alice", "Bob", 10)
        block = Block("B1", "B0", 1, 1, [transaction], demo.qcs["B0"])
        demo.blocks["B1"] = block
        for node in demo.nodes:
            node.blocks["B1"] = block
        demo.votes["B1"] = {1, 2, 3}

        demo.form_qc("B1")

        for node in demo.nodes:
            self.assertEqual(
                node.machine.accounts,
                {"Alice": 100, "Bob": 100, "Charlie": 100},
            )
            self.assertEqual(node.machine.receipts, {})


if __name__ == "__main__":
    unittest.main()
