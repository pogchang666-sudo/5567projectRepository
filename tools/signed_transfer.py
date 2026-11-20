"""AI-assisted B6 client for the classroom test keys; see changes.md."""
import argparse
from hashlib import sha256
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from backend.transaction_security import PUBLIC_KEYS, sign_transaction


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sender", choices=PUBLIC_KEYS)
    parser.add_argument("receiver", choices=PUBLIC_KEYS)
    parser.add_argument("amount", type=int)
    parser.add_argument("nonce", type=int, help="sender's next nonce, starting at 0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    # The public classroom seeds are intentionally reproducible. Never use real keys here.
    seed = sha256(f"COMP5567 classroom test key v1:{args.sender}".encode()).digest()
    key = Ed25519PrivateKey.from_private_bytes(seed)
    try:
        signature = sign_transaction(key, args.sender, args.receiver, args.amount, args.nonce)
        body = dict(sender=args.sender, receiver=args.receiver, amount=args.amount,
                    nonce=args.nonce, signature=signature)
        request = Request(f"http://127.0.0.1:{args.port}/api/transactions",
                          data=json.dumps(body).encode(),
                          headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=5) as response:
            result = json.load(response)
    except HTTPError as exc:
        parser.exit(1, f"HTTP {exc.code}: {exc.read().decode()}\n")
    except (ValueError, URLError, TimeoutError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps({"transaction_id": result["transaction_id"],
                      "receipt": result["receipt"]}, indent=2))


if __name__ == "__main__":
    main()
