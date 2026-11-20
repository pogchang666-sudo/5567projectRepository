"""AI-assisted A7 tests; see changes.md."""
from copy import deepcopy
import unittest

from backend.hotstuff import HotStuffDemo


class RoleAAttackTests(unittest.TestCase):
    def advance_until(self, demo, predicate, limit=100):
        for _ in range(limit):
            if predicate():
                return
            demo.step()
        self.fail("Expected protocol state was not reached")
    def test_equivocation_is_rejected_by_normal_voting_path(self):
        demo = HotStuffDemo()
        first_id, second_id = demo.inject_attack("equivocation", 1)
        first = demo.blocks[first_id]
        second = demo.blocks[second_id]

        self.assertNotEqual(first_id, second_id)
        self.assertEqual((first.view, first.parent_id, first.proposer),
                         (second.view, second.parent_id, second.proposer))
        self.assertTrue(all(action == "vote" for action, _ in demo.events))

        for _ in range(9):
            demo.step()

        self.assertIn(first_id, demo.qcs)
        self.assertNotIn(second_id, demo.qcs)
        self.assertEqual(demo.votes[first_id], {1, 2, 3, 4})
        self.assertEqual(demo.votes[second_id], set())
        self.assertTrue(all(node.committed_blocks == ["B0"] for node in demo.nodes))
        self.assertTrue(all(node.machine.accounts["Alice"] == 100 for node in demo.nodes))

    def test_conflicting_branch_is_never_committed(self):
        demo = HotStuffDemo()
        _, conflicting_id = demo.inject_attack("equivocation", 1)
        for _ in range(100):
            if all(len(node.committed_blocks) > 1 for node in demo.nodes):
                break
            demo.step()

        self.assertTrue(all(len(node.committed_blocks) > 1 for node in demo.nodes))
        self.assertNotIn(conflicting_id, demo.qcs)
        self.assertTrue(all(conflicting_id not in node.committed_blocks for node in demo.nodes))
        for node in demo.nodes[1:]:
            self.assertEqual(node.committed_blocks, demo.nodes[0].committed_blocks)
            self.assertEqual(node.machine.accounts, demo.nodes[0].machine.accounts)
            self.assertEqual(node.machine.receipts, demo.nodes[0].machine.receipts)

    def test_duplicate_vote_is_counted_once_with_one_qc(self):
        demo = HotStuffDemo()
        block_id = demo.inject_attack("duplicate_vote", 1)
        duplicate = ("vote", (1, block_id))
        self.assertEqual(list(demo.events).count(duplicate), 2)

        for _ in range(6):
            demo.step()

        self.assertEqual(demo.votes[block_id], {1, 2, 3, 4})
        self.assertEqual(demo.qcs[block_id].voters, (1, 2, 3, 4))
        quorum_logs = [entry for entry in demo.logs
                       if entry["message"] == f"Quorum reached for {block_id}"]
        self.assertEqual(len(quorum_logs), 1)
        self.assertTrue(all(node.committed_blocks == ["B0"] for node in demo.nodes))

    def test_invalid_attack_requests_do_not_mutate_state(self):
        for kind, node_id in (("invalid_qc", 1), ("equivocation", 2),
                              ("duplicate_vote", 0), ("duplicate_vote", True)):
            with self.subTest(kind=kind, node_id=node_id):
                demo = HotStuffDemo()
                before = deepcopy(demo.snapshot())
                events = list(demo.events)
                with self.assertRaises(ValueError):
                    demo.inject_attack(kind, node_id)
                self.assertEqual(demo.snapshot(), before)
                self.assertEqual(list(demo.events), events)

    def test_crashed_attacker_cannot_inject(self):
        demo = HotStuffDemo()
        demo.crash_leader()
        before = deepcopy(demo.snapshot())
        with self.assertRaises(ValueError):
            demo.inject_attack("duplicate_vote", 1)
        self.assertEqual(demo.snapshot(), before)

    def test_equivocation_after_timeout_uses_new_live_leader(self):
        demo = HotStuffDemo()
        demo.crash_leader()
        self.advance_until(demo, lambda: demo.view == 2)
        self.assertEqual(demo.leader_id, 2)

        first_id, second_id = demo.inject_attack("equivocation", 2)
        self.advance_until(demo, lambda: first_id in demo.qcs)

        self.assertEqual(demo.qcs[first_id].voters, (2, 3, 4))
        self.assertNotIn(second_id, demo.qcs)
        self.assertNotIn(first_id, demo.nodes[0].blocks)
        self.assertTrue(demo.recover())
        self.assertTrue(all(not node.crashed for node in demo.nodes))
        for node in demo.nodes[1:]:
            self.assertEqual(node.committed_blocks, demo.nodes[0].committed_blocks)
            self.assertEqual(node.machine.accounts, demo.nodes[0].machine.accounts)

    def test_recovery_preserves_vote_history_after_duplicate_attack(self):
        demo = HotStuffDemo()
        block_id = demo.inject_attack("duplicate_vote", 1)
        self.advance_until(demo, lambda: block_id in demo.qcs)
        demo.crash_leader()
        self.assertTrue(demo.recover())

        recovered = demo.nodes[0]
        self.assertEqual(recovered.last_voted_view, 1)
        before_votes = deepcopy(demo.votes[block_id])
        before_events = list(demo.events)
        self.assertFalse(demo.vote((1, block_id)))
        self.assertEqual(demo.votes[block_id], before_votes)
        self.assertEqual(list(demo.events), before_events)


if __name__ == "__main__":
    unittest.main()
