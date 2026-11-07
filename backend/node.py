from .blockchain import StateMachine
from .models import Block, QC


class Node:
    def __init__(self, node_id: int, genesis: Block, genesis_qc: QC):
        self.id = node_id
        self.view = 1
        self.role = "Leader" if node_id == 1 else "Replica"
        self.high_qc = genesis_qc
        self.locked_qc = genesis_qc
        self.blocks = {genesis.id: genesis}
        self.committed_blocks = [genesis.id]
        self.machine = StateMachine()
        self.last_voted_view = 0
        self.crashed = False
        self.withhold_vote = False

    def enter_view(self, view: int, leader_id: int):
        """A5 update local view and role for a live replica.
        A crashed replica remains frozen. Never erase voting history or locks."""
        if self.crashed:
            return
        self.view = view
        self.role = "Leader" if self.id == leader_id else "Replica"

    def extends(self, block_id: str, ancestor_id: str) -> bool:
        """A2 test whether block_id descends from ancestor_id, including itself.
        Use local parent links. Unknown or malformed ancestry must not be
        accepted as an extension. Return a Boolean without modifying state."""
        # AI-assisted implementation; see changes.md.
        if not isinstance(block_id, str) or not isinstance(ancestor_id, str):
            return False
        if not isinstance(self.blocks.get(ancestor_id), Block):
            return False

        current_id = block_id
        visited = set()
        while isinstance(current_id, str) and current_id not in visited:
            block = self.blocks.get(current_id)
            if not isinstance(block, Block):
                return False
            if current_id == ancestor_id:
                return True
            visited.add(current_id)
            current_id = block.parent_id
        return False

    def can_vote(self, block: Block) -> bool:
        """A2 decide whether this replica may vote for a proposal.
        Enforce availability, current view, one vote per view and the safe-node
        lock rule. Return a Boolean; vote() records the actual cast vote.
        The coordinator validates the proposal leader and parent certificate."""
        # AI-assisted implementation; see changes.md.
        if not isinstance(block, Block) or self.crashed or self.withhold_vote:
            return False
        if block.view != self.view or self.last_voted_view >= block.view:
            return False
        if not isinstance(block.qc, QC) or not isinstance(self.locked_qc, QC):
            return False
        if not isinstance(self.blocks.get(self.locked_qc.block_id), Block):
            return False

        # A direct child is already an extension even before local registration.
        extends_locked = (block.parent_id == self.locked_qc.block_id or
                          self.extends(block.id, self.locked_qc.block_id))
        newer_qc = block.qc.view > self.locked_qc.view
        return extends_locked or newer_qc

    def receive_qc(self, qc: QC) -> list[str]:
        """A4 update certificate/lock state and decide committed block IDs.
        Return newly committed IDs in ancestor-first order; a crashed node
        returns no progress. Check the linked, consecutive-view three-chain
        contract. Preserve existing commits and prevent repeated commitment.
        Do not execute transactions here: dispatch_qc() invokes Task B.
        A7 may add certificate validation at this boundary as needed."""
        if self.crashed or not isinstance(qc, QC):
            return []
        block = self.blocks.get(qc.block_id)
        if not isinstance(block, Block) or qc.view != block.view:
            return []

        if qc.view > self.high_qc.view:
            self.high_qc = qc

        parent = self.blocks.get(block.parent_id) if block.parent_id else None
        if (isinstance(parent, Block) and isinstance(block.qc, QC)
                and block.qc.block_id == parent.id and block.qc.view == parent.view
                and block.qc.view > self.locked_qc.view):
            self.locked_qc = block.qc

        grand = (self.blocks.get(parent.parent_id)
                 if isinstance(parent, Block) and parent.parent_id else None)
        if not isinstance(grand, Block):
            return []

        certified = (isinstance(block.qc, QC) and block.qc.block_id == parent.id
                     and block.qc.view == parent.view
                     and isinstance(parent.qc, QC) and parent.qc.block_id == grand.id
                     and parent.qc.view == grand.view)
        consecutive = block.view == parent.view + 1 == grand.view + 2
        if not (certified and consecutive):
            return []

        committed = self._uncommitted_prefix(grand.id)
        if committed:
            self.committed_blocks.extend(committed)
        return committed

    def _uncommitted_prefix(self, block_id: str) -> list[str]:
        """Ancestors of block_id that are not committed yet, oldest first."""
        chain: list[str] = []
        seen: set[str] = set()
        current: str | None = block_id
        while isinstance(current, str) and current not in seen \
                and current not in self.committed_blocks:
            seen.add(current)
            chain.append(current)
            block = self.blocks.get(current)
            if not isinstance(block, Block):
                break
            current = block.parent_id
        chain.reverse()
        return chain



    def execute_committed(self, block_ids: list[str]):
        """B3 execute only blocks already in this replica's committed history.
        Reject uncommitted IDs before applying any transaction. Preserve block
        and payload order; call machine.apply() and rely on B4 receipt semantics
        for repeat delivery. A crashed replica must not execute new work.
        """
        raise NotImplementedError("TODO B3 implement execute_committed")
