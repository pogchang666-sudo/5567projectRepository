"""AI-assisted B6 regression tests; see changes.md."""
from dataclasses import replace
from hashlib import sha256
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from pydantic import ValidationError

from backend.blockchain import StateMachine
from backend.hotstuff import HotStuffDemo
from backend.main import TransferRequest
from backend.models import Transaction


def signed(sender="Alice", receiver="Bob", amount=80, nonce=0, *, signer=None,
           domain="COMP5567/HotStuff/Classroom/v1"):
    body = dict(sender=sender, receiver=receiver, amount=amount, nonce=nonce)
    payload = json.dumps(dict(body, domain=domain), sort_keys=True,
                         separators=(",", ":")).encode("ascii")
    seed = sha256(f"COMP5567 classroom test key v1:{signer or sender}".encode()).digest()
    key = Ed25519PrivateKey.from_private_bytes(seed)
    return dict(body, signature=key.sign(payload).hex()), sha256(payload).hexdigest()


class TransactionSecurityTests(unittest.TestCase):
    def setUp(self):
        self.demo = HotStuffDemo(require_signatures=True)

    def commit_pending(self):
        for _ in range(100):
            if not self.demo.mempool:
                return
            self.demo.step()
        self.fail("The pending transaction did not reach consensus commitment")

    def test_stable_identity_and_retry_before_and_after_consensus(self):
        req, expected_id = signed()
        req = TransferRequest.model_validate(req).model_dump()
        tx = self.demo.submit(**req)
        self.assertEqual(tx.id, expected_id)
        # A different hex representation of the same signature has the same ID.
        retry = dict(req, signature=req["signature"].upper())
        self.assertEqual(self.demo.submit(**retry), tx)
        self.assertEqual(self.demo.mempool, [expected_id])
        self.assertTrue(all(n.machine.nonces["Alice"] == 0 for n in self.demo.nodes))

        self.commit_pending()
        self.assertEqual(self.demo.submit(**retry), tx)
        self.assertEqual(self.demo.mempool, [])
        for node in self.demo.nodes:
            self.assertEqual(node.machine.accounts, {"Alice": 20, "Bob": 180, "Charlie": 100})
            self.assertEqual(node.machine.nonces["Alice"], 1)
            self.assertEqual(node.machine.receipts[expected_id],
                             {"status": "committed", "error": None})

    def test_admission_rejects_invalid_signature_even_for_an_existing_id(self):
        req, _ = signed()
        self.demo.submit(**req)
        wrong_account, _ = signed(signer="Bob")
        other_domain, _ = signed(domain="other-chain")
        for bad in (wrong_account, other_domain, dict(req, amount=81),
                    dict(req, signature="bad"), dict(req, nonce=True)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.demo.submit(**bad)
        with self.assertRaises(ValueError):
            self.demo.submit("Alice", "Bob", 5)
        self.assertEqual(len(self.demo.mempool), 1)
        self.assertEqual(len(self.demo.transactions), 1)

    def test_request_model_rejects_coerced_nonce_and_checks_basic_mode_boundary(self):
        req, _ = signed()
        for bad_nonce in (True, "0", -1):
            with self.subTest(nonce=bad_nonce), self.assertRaises(ValidationError):
                TransferRequest.model_validate(dict(req, nonce=bad_nonce))
        basic = HotStuffDemo()
        with self.assertRaises(ValueError):
            basic.submit(**req)
        self.assertEqual(basic.submit("Alice", "Bob", 1).id, "Tx1")

    def test_future_and_conflicting_nonces_rejected_at_admission(self):
        future, _ = signed(nonce=1)
        with self.assertRaises(ValueError):
            self.demo.submit(**future)
        req, _ = signed()
        self.demo.submit(**req)
        conflict, _ = signed(amount=79)
        with self.assertRaises(ValueError):
            self.demo.submit(**conflict)
        self.commit_pending()
        with self.assertRaises(ValueError):
            self.demo.submit(**conflict)
        self.assertEqual(self.demo.submit(**future).nonce, 1)

    def test_execution_revalidates_and_does_not_poison_receipt_cache(self):
        m = StateMachine(require_signatures=True)
        req, expected_id = signed()
        tx = Transaction(id=expected_id, **req)
        future, future_id = signed(nonce=1)
        for forged in (replace(tx, amount=81), replace(tx, id="other-id"),
                       replace(tx, signature=None), Transaction(id=future_id, **future)):
            with self.subTest(forged=forged):
                self.assertEqual(m.apply(forged)["status"], "rejected")
        self.assertEqual(m.nonces["Alice"], 0)
        self.assertEqual(m.accounts["Alice"], 100)
        self.assertEqual(m.receipts, {})
        self.assertEqual(m.apply(tx)["status"], "committed")
        self.assertEqual(m.apply(replace(tx, signature="00" * 64))["status"], "rejected")
        self.assertEqual(m.apply(Transaction(id=future_id, **future))["error"], "Insufficient funds")
        self.assertEqual(m.nonces["Alice"], 2)

    def test_authenticated_insufficient_funds_consumes_nonce_once(self):
        req, expected_id = signed(amount=101)
        self.demo.submit(**req)
        self.commit_pending()
        self.assertEqual(self.demo.submit(**req).id, expected_id)
        self.assertEqual(self.demo.mempool, [])
        for node in self.demo.nodes:
            self.assertEqual(node.machine.nonces, {"Alice": 1, "Bob": 0, "Charlie": 0})
            self.assertEqual(node.machine.accounts, {"Alice": 100, "Bob": 100, "Charlie": 100})
            self.assertEqual(node.machine.receipts[expected_id],
                             {"status": "rejected", "error": "Insufficient funds"})
        self.demo.reset()
        self.assertEqual(self.demo.snapshot()["nodes"][0]["nonces"]["Alice"], 0)
        with self.assertRaises(ValueError):
            self.demo.submit("Alice", "Bob", 1)
