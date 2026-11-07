"""Deterministic event queue. One step is one visible protocol action.

Transport and the timeout pacemaker are simulated by this coordinator. Votes,
locks, blocks, committed chains and account execution remain per-node state.
"""
from collections import deque
from copy import deepcopy
from dataclasses import asdict

from .blockchain import INITIAL_BALANCES
from .models import Block, QC, Transaction
from .node import Node


class HotStuffDemo:
    NODE_COUNT = 4
    QUORUM = 3
    TIMEOUT_TICKS = 3

    def __init__(self):
        self.reset()

    @property
    def leader_id(self):
        return (self.view - 1) % self.NODE_COUNT + 1

    def log(self, message: str, kind: str = "info"):
        self.log_sequence += 1
        self.logs.append({"id": self.log_sequence, "step": self.steps,
                          "view": self.view, "kind": kind, "message": message})

    def reset(self):
        genesis = Block("B0", None, 0, 0)
        genesis_qc = QC("B0", 0, (1, 2, 3, 4))
        self.view = 1
        self.nodes = [Node(i, genesis, genesis_qc) for i in range(1, 5)]
        self.blocks = {genesis.id: genesis}
        self.qcs = {genesis.id: genesis_qc}
        self.transactions: dict[str, Transaction] = {}
        self.mempool: list[str] = []
        self.votes: dict[str, set[int]] = {}
        self.qc_scheduled: set[str] = set()
        self.events = deque([("propose", None)])
        self.logs = deque(maxlen=400)
        self.log_sequence = 0
        self.steps = 0
        self.running = False
        self.max_txs_per_block = 5
        self.phase = "Ready for proposal"
        self.log("Genesis B0 committed · Enter View 1 · Leader N1", "view")

    def submit(self, sender: str, receiver: str, amount: int) -> Transaction:
        """B1 implement transaction admission and mempool insertion.
        Return a Transaction; validate account names and a strict integer amount
        in [1, 1000000]. Invalid requests must not modify state. Allocate Tx1,
        Tx2, ... for the basic task. B6 may extend this interface for signed input.
        Do not execute transfers here."""
        # AI-assisted implementation; see changes.md.
        if not isinstance(sender, str) or not isinstance(receiver, str):
            raise ValueError("Sender and receiver must be account names")
        if sender not in INITIAL_BALANCES or receiver not in INITIAL_BALANCES:
            raise ValueError("Unknown sender or receiver account")
        if type(amount) is not int or not 1 <= amount <= 1_000_000:
            raise ValueError("Amount must be an integer in [1, 1000000]")

        tx_number = len(self.transactions) + 1
        while f"Tx{tx_number}" in self.transactions:
            tx_number += 1
        tx = Transaction(f"Tx{tx_number}", sender, receiver, amount)
        self.transactions[tx.id] = tx
        self.mempool.append(tx.id)
        self.log(f"{tx.id} accepted: {sender} → {receiver} · {amount}", "transaction")
        return tx

    def step(self):
        """Provided event dispatcher; a missing TODO pauses without losing work."""
        checkpoint = deepcopy(self.__dict__)
        try:
            if not self.events:
                self.events.append(("propose", None))
            action, data = self.events.popleft()
            self.steps += 1
            {"propose": self.propose, "vote": self.vote, "qc": self.form_qc,
             "next_view": self.next_view, "timeout": self.timeout}[action](data)
        except NotImplementedError as exc:
            self.__dict__.clear()
            self.__dict__.update(checkpoint)
            self.running = False
            self.phase = str(exc)
            self.log(str(exc), "todo")
            raise

    def propose(self, _):
        """A1 implement a leader proposal for the current view.
        Select a justified parent, allocate a unique block ID, populate the
        proposal and distribute it to live replicas. Register an empty vote set
        and enqueue ("vote", (node_id, block_id)) for the intended recipients.
        Call select_transactions(parent) only when the mempool is nonempty;
        otherwise use an empty payload, allowing independent Task A work.
        A6: handle a crashed leader using the timeout event. No balances change."""
        # AI-assisted implementation; see changes.md.
        leader = self.nodes[self.leader_id - 1]
        if leader.crashed:
            self.events.append(("timeout", self.TIMEOUT_TICKS))
            self.phase = f"Leader N{leader.id} crashed; timeout scheduled"
            self.log(self.phase, "fault")
            return

        parent = self.blocks[leader.high_qc.block_id]
        justification = self.qcs[parent.id]
        transactions = self.select_transactions(parent) if self.mempool else []

        block_number = len(self.blocks)
        while f"B{block_number}" in self.blocks:
            block_number += 1
        block_id = f"B{block_number}"
        block = Block(block_id, parent.id, self.view, self.leader_id,
                      transactions, justification)
        self.blocks[block_id] = block
        self.votes[block_id] = set()

        for node in self.nodes:
            if not node.crashed:
                node.blocks[block_id] = deepcopy(block)
                self.events.append(("vote", (node.id, block_id)))

        self.phase = f"{block_id} proposed by N{self.leader_id}"
        self.log(f"{self.phase} · view {self.view} · parent {parent.id}", "proposal")

    def vote(self, data):
        """A2 implement proposal validation and one safe vote per replica/view.
        data is (node_id, block_id). Validate current leader, view, parent and
        its registered QC, then consult Node.can_vote(). Track voting state and
        distinct voters. Once a quorum is reached, enqueue a single ("qc", id)
        event. Reject invalid proposals without changing voting or account state.
        A6: schedule a timeout if this round cannot obtain a QC."""
        # AI-assisted implementation; see changes.md.
        try:
            node_id, block_id = data
        except (TypeError, ValueError):
            return False
        if type(node_id) is not int or not isinstance(block_id, str):
            return False
        if not 1 <= node_id <= self.NODE_COUNT:
            return False

        node = self.nodes[node_id - 1]
        block = self.blocks.get(block_id)
        local_block = node.blocks.get(block_id)
        if not isinstance(block, Block) or not isinstance(local_block, Block):
            return False
        if local_block != block:
            return False
        if block.proposer != self.leader_id or block.view != self.view:
            return False
        if not isinstance(block.parent_id, str):
            return False

        parent = self.blocks.get(block.parent_id)
        local_parent = node.blocks.get(block.parent_id)
        if not isinstance(parent, Block) or not isinstance(local_parent, Block):
            return False
        if local_parent != parent or parent.id == block.id or parent.view >= block.view:
            return False

        qc = self.qcs.get(parent.id)
        if not isinstance(qc, QC) or block.qc != qc:
            return False
        if qc.block_id != parent.id or qc.view != parent.view:
            return False
        if not isinstance(qc.voters, tuple):
            return False
        if any(type(voter) is not int or not 1 <= voter <= self.NODE_COUNT
               for voter in qc.voters):
            return False
        if len(set(qc.voters)) != len(qc.voters) or len(qc.voters) < self.QUORUM:
            return False
        if not node.can_vote(block):
            return False

        node.last_voted_view = block.view
        voters = self.votes.setdefault(block_id, set())
        voters.add(node_id)
        self.phase = f"N{node_id} voted {block_id} · {len(voters)} votes"
        self.log(self.phase, "vote")

        if len(voters) >= self.QUORUM and block_id not in self.qc_scheduled:
            self.qc_scheduled.add(block_id)
            self.events.append(("qc", block_id))
            self.log(f"Quorum reached for {block_id}", "qc")
        return True

    def form_qc(self, block_id):
        """A3 construct a certificate from distinct valid matching votes.
        Validate the block, view and authorized voters; fewer than QUORUM must
        never create a QC. Register the valid certificate, call dispatch_qc(qc),
        and enqueue ("next_view", "QC"). A6 handles a crashed collector.
        Do not implement transaction processing in this function."""
        block = self.blocks.get(block_id)
        if not isinstance(block, Block):
            raise ValueError(f"Unknown block: {block_id}")

        voters = sorted(voter for voter in self.votes.get(block_id, set())
                        if type(voter) is int and 1 <= voter <= self.NODE_COUNT)
        if len(voters) < self.QUORUM:
            raise ValueError(
                f"{block_id} has {len(voters)} distinct votes, quorum is {self.QUORUM}")

        qc = QC(block_id, block.view, tuple(voters))
        self.qcs[block_id] = qc
        self.log(f"QC for {block_id} · view {block.view} · voters {voters}", "qc")

        self.dispatch_qc(qc)
        self.events.append(("next_view", "QC"))
        return qc

    def timeout(self, remaining):
        """A6 implement logical timeout countdown and leader replacement.
        remaining is the number of logical ticks left. Eventually schedule
        ("next_view", "timeout") while preserving the quorum and safety state."""
        raise NotImplementedError('TODO A6 implement logical timeout countdown and leader replacement.')

    def next_view(self, reason):
        """A5 implement view increment, leader rotation and replica updates.
        Preserve QCs, locks and committed history. Call each node's enter_view
        as appropriate and enqueue the next proposal event."""
        self.view += 1
        for node in self.nodes:
            node.enter_view(self.view, self.leader_id)
        self.phase = f"View {self.view} · leader N{self.leader_id}"
        self.log(f"Enter view {self.view} after {reason} · leader N{self.leader_id}", "view")
        self.events.append(("propose", None))

    def crash_leader(self):
        leader = self.nodes[self.leader_id - 1]
        if not leader.crashed:
            leader.crashed = True
            self.log(f"Leader N{leader.id} crashed", "fault")

    def set_byzantine(self, node_id: int | None):
        if node_id is not None and node_id not in range(1, 5):
            raise ValueError("Node ID must be 1–4")
        for node in self.nodes:
            node.withhold_vote = node.id == node_id
        self.log(f"N{node_id} Byzantine: withholds votes only" if node_id else
                 "All nodes vote normally", "fault")

    def recover(self):
        """A6 restore crashed replicas from a trusted live peer.
        Catch up blocks, QCs, locks, committed chain and application state.
        Preserve voting history so a replica cannot vote twice in one view.
        Restore balances and receipts, and B6 nonces if implemented. If no live
        peer is available, reject recovery without inventing state. No disk
        persistence is required. Clear simulated faults and rejoin safely."""
        raise NotImplementedError('TODO A6 restore crashed replicas from a trusted live peer.')

    def snapshot(self):
        source = max(self.nodes, key=lambda n: len(n.committed_blocks))
        committed = set(source.committed_blocks)
        node_states = []
        for node in self.nodes:
            node_states.append({
                "id": node.id, "view": node.view, "role": node.role,
                "crashed": node.crashed, "withhold_vote": node.withhold_vote,
                "high_qc": asdict(node.high_qc), "locked_qc": asdict(node.locked_qc),
                "latest_block": max(node.blocks.values(), key=lambda b: b.view).id,
                "committed_blocks": node.committed_blocks.copy(),
                "accounts": node.machine.accounts.copy(),
            })
        blocks = [{**asdict(block), "certificate": asdict(self.qcs[block.id]) if block.id in self.qcs else None,
                   "committed": block.id in committed,
                   "votes": sorted(self.votes.get(block.id, []))}
                  for block in self.blocks.values()]
        transactions = [{**asdict(tx), **source.machine.receipts.get(tx.id, {"status": "pending", "error": None})}
                        for tx in self.transactions.values()]
        live = [n for n in self.nodes if not n.crashed]
        consistent = bool(live) and all(n.machine.accounts == live[0].machine.accounts
                                       and n.committed_blocks == live[0].committed_blocks for n in live)
        return {"view": self.view, "leader_id": self.leader_id, "running": self.running,
                "steps": self.steps, "phase": self.phase, "nodes": node_states,
                "blocks": blocks, "mempool": [asdict(self.transactions[t]) for t in self.mempool],
                "transactions": transactions, "accounts": source.machine.accounts.copy(),
                "committed_chain": source.committed_blocks.copy(), "consistent": consistent,
                "logs": list(self.logs), "quorum": self.QUORUM,
                "next_event": self.events[0][0] if self.events else "propose"}



    def select_transactions(self, parent: Block) -> list[Transaction]:
        """B2 select eligible pending transactions without consuming them.
        Return at most max_txs_per_block (default 5), excluding transaction IDs
        on the selected parent chain. An abandoned branch does not exclude an ID.
        Empty input returns an empty list. Keep IDs in the pool until commit.
        """
        if not isinstance(parent, Block):
            return []

        on_parent_chain: set[str] = set()
        current: str | None = parent.id
        visited: set[str] = set()
        while isinstance(current, str) and current not in visited:
            visited.add(current)
            block = self.blocks.get(current)
            if not isinstance(block, Block):
                break
            on_parent_chain.update(transaction.id for transaction in block.transactions)
            current = block.parent_id

        selected: list[Transaction] = []
        for tx_id in self.mempool:
            if tx_id in on_parent_chain:
                continue
            transaction = self.transactions.get(tx_id)
            if not isinstance(transaction, Transaction):
                continue
            selected.append(transaction)
            if len(selected) >= self.max_txs_per_block:
                break
        return selected

    def finalize_transactions(self, committed_ids: list[str]):
        """B4 finalize pool entries after per-replica execution.
        committed_ids is ordered and contains newly committed blocks. Remove
        their transaction IDs from the pool, including rejected executions,
        and record useful transaction events. Repeated finalization is harmless.
        This method does not execute transfers or decide consensus.
        """
        raise NotImplementedError("TODO B4 implement finalize_transactions")

    def configure_batch(self, limit):
        """B5 set a positive integer batch limit and return the accepted value.
        Reject bool, zero, negatives and non-integers without changing state.
        Reset restores the default value 5 in this starter contract.
        """
        raise NotImplementedError("TODO B5 implement configure_batch")

    def inject_attack(self, kind: str, node_id: int):
        """A7 inject an active Byzantine action in the current experiment.
        Implement equivocation by the current leader plus duplicate_vote OR
        invalid_qc. Extend message delivery as needed so honest replicas receive
        the attack through normal validation paths. Log the action and supply
        assertions. Do not count the supplied withholding switch as this task.
        A malicious replica controls only its own simulator identity.
        """
        raise NotImplementedError("TODO A7 implement inject_attack")

    def dispatch_qc(self, qc: QC):
        """Provided integration wiring. Caller must validate/register the QC.

        Task A reports committed IDs; Task B executes their payload and cleans
        the pool. Empty payloads bypass Task B, not consensus validation.
        """
        newly_committed = set()
        for node in self.nodes:
            committed = node.receive_qc(qc)
            newly_committed.update(committed)
            if committed and any(node.blocks[b].transactions for b in committed):
                node.execute_committed(committed)
        ordered = sorted(newly_committed, key=lambda b: self.blocks[b].view)
        for block_id in ordered:
            self.log(f"{block_id} committed", "commit")
        if any(self.blocks[b].transactions for b in ordered):
            self.finalize_transactions(ordered)
        return ordered
