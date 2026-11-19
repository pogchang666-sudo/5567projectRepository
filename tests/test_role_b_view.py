import unittest
from copy import deepcopy

from backend.hotstuff import HotStuffDemo
from backend.models import QC


class RoleBViewChangeTests(unittest.TestCase):
    def setUp(self):
        self.demo = HotStuffDemo()
        self.demo.events.clear()

    def test_view_advances_and_the_leader_rotates(self):
        self.demo.next_view("QC")

        self.assertEqual(self.demo.view, 2)
        self.assertEqual(self.demo.leader_id, 2)
        self.assertEqual([node.view for node in self.demo.nodes], [2, 2, 2, 2])
        self.assertEqual(self.demo.nodes[0].role, "Replica")
        self.assertEqual(self.demo.nodes[1].role, "Leader")

    def test_entering_a_view_updates_the_local_role(self):
        node = self.demo.nodes[0]

        node.enter_view(5, 3)
        self.assertEqual(node.view, 5)
        self.assertEqual(node.role, "Replica")

        node.enter_view(5, 1)
        self.assertEqual(node.view, 5)
        self.assertEqual(node.role, "Leader")

    def test_crashed_replica_stays_frozen(self):
        node = self.demo.nodes[0]
        node.crashed = True
        before = (node.view, node.role)

        self.demo.next_view("QC")

        self.assertEqual((node.view, node.role), before)

    def test_view_change_preserves_protocol_state(self):
        node = self.demo.nodes[0]
        node.high_qc = QC("B2", 2, (1, 2, 3))
        node.locked_qc = QC("B1", 1, (1, 2, 3))
        node.last_voted_view = 2
        node.committed_blocks.append("B1")
        preserved = deepcopy(
            (node.high_qc, node.locked_qc, node.last_voted_view,
             list(node.committed_blocks), list(node.blocks))
        )

        self.demo.next_view("QC")

        self.assertEqual(
            (node.high_qc, node.locked_qc, node.last_voted_view,
             list(node.committed_blocks), list(node.blocks)),
            preserved,
        )

    def test_view_change_queues_the_next_proposal(self):
        self.demo.next_view("QC")

        self.assertEqual(self.demo.events[-1], ("propose", None))

    def test_repeated_view_changes_keep_rotating_the_leader(self):
        leaders = []
        for _ in range(4):
            self.demo.next_view("QC")
            leaders.append(self.demo.leader_id)

        self.assertEqual(leaders, [2, 3, 4, 1])
        self.assertEqual(self.demo.view, 5)


if __name__ == "__main__":
    unittest.main()
