"""Long-running child and marker for MVP-01 interruption experiments."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path


child = subprocess.Popen(
    [sys.executable, "-c", "import time; time.sleep(120)", "mvp01-child-canary-91b"]
)
Path("child.pid").write_text(f"{child.pid}\n", encoding="utf-8")
Path("checkpoint.txt").write_text("CHECKPOINT_READY\n", encoding="utf-8")
print("JOB_STARTED", flush=True)
raise SystemExit(child.wait())
