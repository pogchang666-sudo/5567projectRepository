"""AI-assisted B6 canonical payload, transaction IDs and Ed25519; see changes.md."""
from hashlib import sha256
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .models import Transaction


DOMAIN = "COMP5567/HotStuff/Classroom/v1"
MAX_NONCE = (1 << 53) - 1
# Public halves of the classroom keys used by tools/signed_transfer.py.
PUBLIC_KEYS = {
    "Alice": Ed25519PublicKey.from_public_bytes(bytes.fromhex(
        "d351920d4ac32016f7cccb97e570412cf9f95c3fe45d6ca196b623e09d553586")),
    "Bob": Ed25519PublicKey.from_public_bytes(bytes.fromhex(
        "5e3d957ada3a369f6f3b23b18056c385ee5ab36c7f17a23f2819fe063ff83998")),
    "Charlie": Ed25519PublicKey.from_public_bytes(bytes.fromhex(
        "ef776d6f0cea02c24c008d7034ccfa2cd18e510173c87ed773d20e734abfae8c")),
}


def _payload(sender: str, receiver: str, amount: int, nonce: int) -> bytes:
    if not isinstance(sender, str) or not isinstance(receiver, str):
        raise ValueError("Sender and receiver must be account names")
    if sender not in PUBLIC_KEYS or receiver not in PUBLIC_KEYS:
        raise ValueError("Unknown sender or receiver account")
    if type(amount) is not int or not 1 <= amount <= 1_000_000:
        raise ValueError("Amount must be an integer in [1, 1000000]")
    if type(nonce) is not int or not 0 <= nonce <= MAX_NONCE:
        raise ValueError(f"Nonce must be an integer in [0, {MAX_NONCE}]")
    fields = dict(domain=DOMAIN, sender=sender, receiver=receiver, amount=amount, nonce=nonce)
    return json.dumps(fields, sort_keys=True, separators=(",", ":")).encode("ascii")


def sign_transaction(key: Ed25519PrivateKey, sender: str, receiver: str,
                     amount: int, nonce: int) -> str:
    return key.sign(_payload(sender, receiver, amount, nonce)).hex()


def transaction_id(sender: str, receiver: str, amount: int, nonce: int) -> str:
    return sha256(_payload(sender, receiver, amount, nonce)).hexdigest()


def verify_transaction(tx: Transaction) -> bool:
    """Verify the sender signature and bind the provided ID to the signed payload."""
    if not isinstance(tx.signature, str) or len(tx.signature) != 128:
        return False
    try:
        payload = _payload(tx.sender, tx.receiver, tx.amount, tx.nonce)
        if tx.id != sha256(payload).hexdigest():
            return False
        PUBLIC_KEYS[tx.sender].verify(bytes.fromhex(tx.signature), payload)
    except (InvalidSignature, ValueError):
        return False
    return True
