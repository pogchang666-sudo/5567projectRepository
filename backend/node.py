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
        raise NotImplementedError('TODO A5 update local view and role for a live replica.')

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
        raise NotImplementedError('TODO A4 update certificate/lock state and decide committed block IDs.')



    def execute_committed(self, block_ids: list[str]):
        """B3 execute only blocks already in this replica's committed history.
        Reject uncommitted IDs before applying any transaction. Preserve block
        and payload order; call machine.apply() and rely on B4 receipt semantics
        for repeat delivery. A crashed replica must not execute new work.
        """
        if self.crashed:
            return

        # Validate the whole batch before the first debit.
        committed = set(self.committed_blocks)
        blocks = []
        for block_id in block_ids:
            if block_id not in committed or block_id not in self.blocks:
                raise ValueError(f"Block {block_id} is not committed on N{self.id}")
            blocks.append(self.blocks[block_id])

        for block in blocks:
            for tx in block.transactions:
                self.machine.apply(tx)
