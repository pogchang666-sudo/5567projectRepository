"""Run the basic suite (or the demo) with the local role C edits and role B."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
BASE = "826658987936c16b4b92b48484ec15f05e84304d"
ROLE_B = "ab002f7a42cce8af8b0f4ede4b2fdbb6b451d21f"


def run(*args, cwd=ROOT, **kwargs):
    return subprocess.run(args, cwd=cwd, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help="open the demo server after the tests")
    args = parser.parse_args()
    # Use the working copy so this works before role C has its first commit.
    patch = run("git", "diff", "--no-ext-diff", "--binary", BASE, "--", "backend",
                stdout=subprocess.PIPE).stdout
    with tempfile.TemporaryDirectory(prefix="hotstuff-role-c-") as tmp:
        joint = Path(tmp)
        run("git", "clone", "--quiet", "--shared", "--no-checkout", str(ROOT), str(joint))
        run("git", "checkout", "--quiet", "--detach", ROLE_B, cwd=joint)
        if patch:
            run("git", "apply", "--3way", "-", input=patch, cwd=joint)
        for test in (ROOT / "tests").glob("test_role_c_*.py"):
            shutil.copy2(test, joint / "tests" / test.name)
        run(sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v", cwd=joint)
        if args.serve:
            print("Open http://127.0.0.1:8000/ in your browser. Press Ctrl+C to stop.", flush=True)
            run(sys.executable, "-B", "-m", "backend.main", cwd=joint)


if __name__ == "__main__":
    main()
