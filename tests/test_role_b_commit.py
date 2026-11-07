import unittest

from backend.hotstuff import HotStuffDemo
from backend.models import Block, QC


class RoleBCommitTests(unittest.TestCase):
    @staticmethod
    def certified_chain(views):
        """B0 <- B1 <- B2 ... with the given block views, fully certified."""
        demo = HotStuffDemo()
        demo.events.clear()
        blocks = {"B0": demo.blocks["B0"]}
        certificates = {"B0": demo.qcs["B0"]}
        parent_id, parent_qc = "B0", demo.qcs["B0"]
        for index, view in enumerate(views, start=1):
            block = Block(f"B{index}", parent_id, view, index, [], parent_qc)
            demo.blocks[block.id] = block
            blocks[block.id] = block
            for node in demo.nodes:
                node.blocks[block.id] = block
            parent_id, parent_qc = block.id, QC(block.id, view, (1, 2, 3))
            certificates[block.id] = parent_qc
        return demo, certificates

    def test_one_certificate_never_commits_its_own_block(self):
        demo, certificates = self.certified_chain([1])
        node = demo.nodes[0]

        committed = node.receive_qc(certificates["B1"])

        self.assertEqual(committed, [])
        self.assertEqual(node.high_qc.block_id, "B1")
        self.assertEqual(node.committed_blocks, ["B0"])

    def test_three_chain_commits_the_grandparent(self):
        demo, certificates = self.certified_chain([1, 2, 3])
        node = demo.nodes[0]

        committed = node.receive_qc(certificates["B3"])

        self.assertEqual(committed, ["B1"])
        self.assertEqual(node.committed_blocks, ["B0", "B1"])
        self.assertNotIn("B2", node.committed_blocks)
        self.assertNotIn("B3", node.committed_blocks)

    def test_lock_follows_the_parent_certificate(self):
        demo, certificates = self.certified_chain([1, 2])
        node = demo.nodes[0]

        node.receive_qc(certificates["B2"])

        self.assertEqual(node.high_qc.block_id, "B2")
        self.assertEqual(node.locked_qc.block_id, "B1")

    def test_non_consecutive_views_commit_nothing(self):
        demo, certificates = self.certified_chain([1, 5, 9])
        node = demo.nodes[0]

        committed = node.receive_qc(certificates["B3"])

        self.assertEqual(committed, [])
        self.assertEqual(node.committed_blocks, ["B0"])

    def test_crashed_replica_makes_no_progress(self):
        demo, certificates = self.certified_chain([1, 2, 3])
        node = demo.nodes[0]
        node.crashed = True

        committed = node.receive_qc(certificates["B3"])

        self.assertEqual(committed, [])
        self.assertEqual(node.high_qc.block_id, "B0")
        self.assertEqual(node.committed_blocks, ["B0"])

    def test_repeated_delivery_is_idempotent(self):
        demo, certificates = self.certified_chain([1, 2, 3])
        node = demo.nodes[0]

        self.assertEqual(node.receive_qc(certificates["B3"]), ["B1"])
        self.assertEqual(node.receive_qc(certificates["B3"]), [])
        self.assertEqual(node.committed_blocks, ["B0", "B1"])

    def test_uncommitted_ancestors_are_committed_oldest_first(self):
        demo, certificates = self.certified_chain([1, 2, 3, 4])
        node = demo.nodes[0]

        committed = node.receive_qc(certificates["B4"])

        self.assertEqual(committed, ["B1", "B2"])
        self.assertEqual(node.committed_blocks, ["B0", "B1", "B2"])

    def test_certificate_for_an_unknown_block_is_ignored(self):
        demo, _ = self.certified_chain([1])

        self.assertEqual(demo.nodes[0].receive_qc(QC("B9", 1, (1, 2, 3))), [])


if __name__ == "__main__":
    unittest.main()
