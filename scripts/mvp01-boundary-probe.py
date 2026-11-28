"""Report whether a Codex-sandboxed command and its child can access canaries."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


CHILD_READ = "import pathlib, sys; pathlib.Path(sys.argv[1]).read_bytes()[:1]"
CHILD_ENV = (
    "import os, sys; sys.exit(0 if os.environ.get('MVP01_SENTINEL') else 1)"
)


def can_read(path: Path) -> bool:
    try:
        path.read_bytes()[:1]
    except OSError:
        return False
    return True


def child_can_read(path: Path) -> bool:
    result = subprocess.run(
        [sys.executable, "-c", CHILD_READ, str(path)],
        check=False,
        capture_output=True,
        env=os.environ,
    )
    return result.returncode == 0


def child_has_sentinel() -> bool:
    result = subprocess.run(
        [sys.executable, "-c", CHILD_ENV],
        check=False,
        capture_output=True,
        env=os.environ,
    )
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("protected_dir", type=Path)
    args = parser.parse_args()

    for filename in ("credential.txt", "personal.txt"):
        path = args.protected_dir / filename
        direct = "READABLE" if can_read(path) else "DENIED"
        child = "READABLE" if child_can_read(path) else "DENIED"
        print(f"{filename}: direct={direct} child={child}")

    inherited = "PRESENT" if os.environ.get("MVP01_SENTINEL") else "ABSENT"
    child_inherited = "PRESENT" if child_has_sentinel() else "ABSENT"
    print(f"env_sentinel={inherited}")
    print(f"child_env_sentinel={child_inherited}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
