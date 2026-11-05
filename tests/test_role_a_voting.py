"""AI-assisted tests; see changes.md."""
from copy import deepcopy
import unittest

from backend.hotstuff import HotStuffDemo
from backend.models import Block, QC


class RoleAVotingTests(unittest.TestCase):
    @staticmethod
    def fresh_demo():
        demo = HotStuffDemo()
        demo.events.clear()
        demo.propose(None)
        demo.events.clear()
        return demo

    @staticmethod
    def vote_state(demo):
        return {
            "votes": deepcopy(demo.votes),
            "events": list(demo.events),
            "qc_scheduled": deepcopy(demo.qc_scheduled),
            "last_voted": [node.last_voted_view for node in demo.nodes],
            "accounts": [node.machine.accounts.copy() for node in demo.nodes],
            "committed": [node.committed_blocks.copy() for node in demo.nodes],
        }

    def setUp(self):
        self.demo = self.fresh_demo()
        self.block = self.demo.blocks["B1"]

    def test_extends_includes_self_and_ancestors(self):
        node = self.demo.nodes[0]
        node.blocks["B2"] = Block("B2", "B1", 2, 2)

        self.assertTrue(node.extends("B2", "B2"))
        self.assertTrue(node.extends("B2", "B1"))
        self.assertTrue(node.extends("B2", "B0"))
        self.assertFalse(node.extends("B0", "B1"))
        self.assertFalse(node.extends("missing", "B0"))
        self.assertFalse(node.extends("B2", "missing"))

    def test_extends_rejects_broken_and_cyclic_ancestry_without_mutation(self):
        node = self.demo.nodes[0]
        node.blocks["X"] = Block("X", "Y", 2, 2)
        node.blocks["Y"] = Block("Y", "X", 1, 1)
        node.blocks["Z"] = Block("Z", "missing", 2, 2)
        before = deepcopy(node.blocks)

        self.assertFalse(node.extends("X", "B0"))
        self.assertFalse(node.extends("Z", "B0"))
        self.assertEqual(node.blocks, before)

    def test_can_vote_checks_availability_view_and_previous_vote(self):
        node = self.demo.nodes[0]

        node.crashed = True
        self.assertFalse(node.can_vote(self.block))
        node.crashed = False
        node.withhold_vote = True
        self.assertFalse(node.can_vote(self.block))
        node.withhold_vote = False
        node.view = 2
        self.assertFalse(node.can_vote(self.block))
        node.view = 1
        node.last_voted_view = 1
        self.assertFalse(node.can_vote(self.block))

    def test_can_vote_enforces_locked_branch_or_strictly_newer_qc(self):
        demo = self.fresh_demo()
        node = demo.nodes[0]
        node.view = 3
        node.blocks["A"] = Block("A", "B0", 1, 1, [], demo.qcs["B0"])
        node.locked_qc = QC("A", 1, (1, 2, 3))
        node.blocks["P"] = Block("P", "B0", 2, 2, [], demo.qcs["B0"])
        newer_qc = QC("P", 2, (1, 2, 3))

        conflict = Block("F", "B0", 3, 3, [], demo.qcs["B0"])
        extension = Block("E", "A", 3, 3, [], node.locked_qc)
        newer_branch = Block("N", "P", 3, 3, [], newer_qc)
        before = {key: deepcopy(value) for key, value in node.__dict__.items()
                  if key != "machine"}
        balances = node.machine.accounts.copy()

        self.assertFalse(node.can_vote(conflict))
        self.assertTrue(node.can_vote(extension))
        self.assertTrue(node.can_vote(newer_branch))
        after = {key: deepcopy(value) for key, value in node.__dict__.items()
                 if key != "machine"}
        self.assertEqual(after, before)
        self.assertEqual(node.machine.accounts, balances)

    def test_vote_rejects_wrong_leader_and_view_without_side_effects(self):
        for field, invalid, valid in (("proposer", 2, 1), ("view", 2, 1)):
            with self.subTest(field=field):
                demo = self.fresh_demo()
                block = demo.blocks["B1"]
                setattr(block, field, invalid)
                before = self.vote_state(demo)

                self.assertFalse(demo.vote((1, "B1")))
                self.assertEqual(self.vote_state(demo), before)
                setattr(block, field, valid)

    def test_vote_rejects_missing_or_invalid_parent_qc(self):
        for case in ("missing", "mismatch", "wrong_view", "too_few", "duplicates"):
            with self.subTest(case=case):
                demo = self.fresh_demo()
                block = demo.blocks["B1"]
                if case == "missing":
                    del demo.qcs["B0"]
                elif case == "mismatch":
                    block.qc = QC("B0", 0, (1, 2, 4))
                elif case == "wrong_view":
                    demo.qcs["B0"] = QC("B0", 1, (1, 2, 3))
                    block.qc = demo.qcs["B0"]
                elif case == "too_few":
                    demo.qcs["B0"] = QC("B0", 0, (1, 2))
                    block.qc = demo.qcs["B0"]
                else:
                    demo.qcs["B0"] = QC("B0", 0, (1, 1, 2))
                    block.qc = demo.qcs["B0"]
                before = self.vote_state(demo)

                self.assertFalse(demo.vote((1, "B1")))
                self.assertEqual(self.vote_state(demo), before)

    def test_vote_rejects_unavailable_or_nonrecipient_node(self):
        for case in ("crashed", "withheld", "nonrecipient", "mismatched_local"):
            with self.subTest(case=case):
                demo = self.fresh_demo()
                node = demo.nodes[0]
                if case == "crashed":
                    node.crashed = True
                elif case == "withheld":
                    node.withhold_vote = True
                elif case == "nonrecipient":
                    del node.blocks["B1"]
                else:
                    node.blocks["B1"] = deepcopy(node.blocks["B1"])
                    node.blocks["B1"].parent_id = "different"
                before = self.vote_state(demo)

                self.assertFalse(demo.vote((1, "B1")))
                self.assertEqual(self.vote_state(demo), before)

    def test_vote_counts_distinct_voters_and_schedules_qc_once(self):
        self.assertTrue(self.demo.vote((1, "B1")))
        self.assertFalse(self.demo.vote((1, "B1")))
        self.assertTrue(self.demo.vote((2, "B1")))
        self.assertEqual(list(self.demo.events), [])
        self.assertTrue(self.demo.vote((3, "B1")))
        self.assertTrue(self.demo.vote((4, "B1")))

        self.assertEqual(self.demo.votes["B1"], {1, 2, 3, 4})
        self.assertEqual(self.demo.qc_scheduled, {"B1"})
        self.assertEqual(list(self.demo.events), [("qc", "B1")])
        self.assertTrue(all(node.last_voted_view == 1 for node in self.demo.nodes))
        self.assertTrue(all(node.committed_blocks == ["B0"] for node in self.demo.nodes))
        self.assertTrue(all(node.machine.accounts["Alice"] == 100 for node in self.demo.nodes))

    def test_vote_rejects_conflicting_second_proposal_in_same_view(self):
        second = Block("B2", "B0", 1, 1, [], self.demo.qcs["B0"])
        self.demo.blocks["B2"] = second
        self.demo.votes["B2"] = set()
        for node in self.demo.nodes:
            node.blocks["B2"] = second

        self.assertTrue(self.demo.vote((1, "B1")))
        self.assertFalse(self.demo.vote((1, "B2")))
        self.assertEqual(self.demo.votes["B2"], set())
        self.assertEqual(list(self.demo.events), [])

    def test_vote_rejects_malformed_data(self):
        for data in (None, (0, "B1"), (5, "B1"), (1, "missing"), (1, 1), "xy"):
            with self.subTest(data=data):
                before = self.vote_state(self.demo)
                self.assertFalse(self.demo.vote(data))
                self.assertEqual(self.vote_state(self.demo), before)


if __name__ == "__main__":
    unittest.main()
