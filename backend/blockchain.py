from .models import Transaction
from .transaction_security import verify_transaction


INITIAL_BALANCES = {"Alice": 100, "Bob": 100, "Charlie": 100}


class StateMachine:
    def __init__(self, *, require_signatures: bool = False):
        # AI-assisted B6 state; see changes.md.
        self.accounts = INITIAL_BALANCES.copy()
        self.require_signatures = require_signatures
        self.nonces = dict.fromkeys(self.accounts, 0)
        # Receipts also make execution idempotent across catch-up and retries.
        self.receipts: dict[str, dict] = {}

    def apply(self, tx: Transaction) -> dict:
        """B3 B4 validate and deterministically execute one committed transaction.
        Called only through the committed-execution path (or isolated unit tests).
        Check known accounts, a strict positive integer amount and available
        funds. A failed transfer changes no balance. Return/store a receipt with
        status committed or rejected and error None or an explanatory string.
        Reusing a transaction ID returns its prior receipt without another debit.
        In signed mode, check authenticity before consulting cached receipts.
        Only a verified transaction with the next nonce consumes that nonce."""
        # AI-assisted implementation; see changes.md.
        if self.require_signatures:
            if not verify_transaction(tx):
                return {"status": "rejected", "error": "Invalid signature or signed transaction"}
        elif tx.signature is not None or tx.nonce is not None:
            return {"status": "rejected", "error": "Signed transaction mode is disabled"}

        if tx.id in self.receipts:
            return self.receipts[tx.id]

        if self.require_signatures:
            if tx.nonce != self.nonces[tx.sender]:
                return {"status": "rejected", "error": "Unexpected nonce"}
            # An authenticated execution uses its nonce even when funds are insufficient.
            self.nonces[tx.sender] += 1

        error = None
        if tx.sender not in self.accounts or tx.receiver not in self.accounts:
            error = "Unknown sender or receiver account"
        elif type(tx.amount) is not int or tx.amount <= 0:
            error = "Amount must be a positive integer"
        elif self.accounts[tx.sender] < tx.amount:
            error = "Insufficient funds"
        else:
            self.accounts[tx.sender] -= tx.amount
            self.accounts[tx.receiver] += tx.amount

        receipt = {"status": "committed" if error is None else "rejected", "error": error}
        self.receipts[tx.id] = receipt
        return receipt

