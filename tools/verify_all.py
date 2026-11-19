#!/usr/bin/env python3
"""Run the integrated test suite, optionally start the demo dashboard.

Usage (from the project root, with the project virtual environment active):

    python tools/verify_all.py
    python tools/verify_all.py --serve
"""
import argparse
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    if sys.version_info < (3, 10):
        print(
            "Python 3.10 or newer is required "
            f"(current: {sys.version.split()[0]}).",
            file=sys.stderr,
        )
        return 1

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--serve",
        action="store_true",
        help="start the FastAPI demo after the tests pass",
    )
    args = parser.parse_args()

    command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"]
    print("Running:", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=ROOT)
    if completed.returncode:
        print("Tests failed; not starting the dashboard.", file=sys.stderr)
        return completed.returncode

    print("All discovered tests passed.", flush=True)
    if not args.serve:
        return 0

    try:
        import fastapi  # noqa: F401
        import uvicorn  # noqa: F401
    except ImportError:
        print(
            "fastapi/uvicorn are not installed. Run: "
            "python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    print("Open http://127.0.0.1:8000/ in your browser. Press Ctrl+C to stop.", flush=True)
    return subprocess.run(
        [sys.executable, "-B", "-m", "backend.main"], cwd=ROOT
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
