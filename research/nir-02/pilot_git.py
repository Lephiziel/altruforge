#!/usr/bin/env python3
"""Exercise two Git operations in temporary local repositories."""

import json
import os
import platform
import subprocess
import tempfile
from pathlib import Path


TASK_REF = "refs/heads/task"


def git(cwd, *args, check=True):
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    env.update(
        LC_ALL="C",
        GIT_ALLOW_PROTOCOL="file",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
    )
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=check,
    )


def commit(cwd, text):
    (cwd / "example.txt").write_text(text, encoding="utf-8")
    git(cwd, "add", "example.txt")
    git(cwd, "commit", "-m", text.strip())
    return git(cwd, "rev-parse", "HEAD").stdout.strip()


def remote_head(cwd):
    result = git(cwd, "ls-remote", "--exit-code", "--refs", "origin", TASK_REF)
    return result.stdout.split()[0]


def check_push_rejection(result, reason):
    expected = f"!\tHEAD:{TASK_REF}\t[rejected] ({reason})"
    if result.returncode == 0 or expected not in result.stdout.splitlines():
        raise RuntimeError(
            f"Expected Git to reject the push with '{reason}'.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def main():
    with tempfile.TemporaryDirectory(prefix="altruforge-pilot-") as tmp:
        root = Path(tmp)
        bare = root / "remote.git"
        worker = root / "worker"
        refspec = f"HEAD:{TASK_REF}"
        git(root, "init", "--bare", str(bare))
        git(root, "init", str(worker))
        git(worker, "config", "user.email", "experiment@example.invalid")
        git(worker, "config", "user.name", "Experiment")
        git(worker, "remote", "add", "origin", str(bare))
        git(worker, "checkout", "-b", "task")

        initial = commit(worker, "initial\n")
        git(worker, "push", "origin", refspec)

        candidate = commit(worker, "candidate\n")
        intent = {
            "expected_old": initial,
            "candidate_head": candidate,
            "status": "intent",
        }
        ledger = root / "ledger.json"
        ledger.write_text(json.dumps(intent), encoding="utf-8")
        git(worker, "push", "origin", refspec)

        # Leave the intent record unchanged to model missing local completion.
        restored = json.loads(ledger.read_text(encoding="utf-8"))
        matches_intent = remote_head(worker) == restored["candidate_head"]
        pending_intent = restored["status"] == "intent"
        if not (matches_intent and pending_intent):
            raise RuntimeError("Expected the remote candidate and a pending intent.")

        other = root / "other"
        git(root, "clone", "--branch", "task", str(bare), str(other))
        git(other, "config", "user.email", "experiment@example.invalid")
        git(other, "config", "user.name", "Experiment")
        drift = commit(other, "concurrent change\n")
        git(other, "push", "origin", refspec)
        if drift == candidate or remote_head(worker) != drift:
            raise RuntimeError("Expected the remote ref to advance in the second clone.")

        ordinary = git(worker, "push", "--porcelain", "origin", refspec, check=False)
        check_push_rejection(ordinary, "fetch first")
        if remote_head(worker) != drift:
            raise RuntimeError("The ordinary push changed the remote ref.")

        lease = f"--force-with-lease={TASK_REF}:{candidate}"
        retry = git(worker, "push", "--porcelain", lease, "origin", refspec, check=False)
        check_push_rejection(retry, "stale info")
        if remote_head(worker) != drift:
            raise RuntimeError("The stale lease push changed the remote ref.")

        result = {
            "git_version": git(root, "--version").stdout.strip(),
            "python_version": platform.python_version(),
            "platform": f"{platform.system()} {platform.machine()}",
            "scope": "local bare Git with simulated missing local acknowledgement",
            "observations": [
                {
                    "case": "remote_push_completed_without_local_ack",
                    "observed_head_matches_intent": matches_intent,
                    "ledger_still_intent": pending_intent,
                },
                {
                    "case": "remote_ref_drift",
                    "ordinary_push_rejection": "fetch first",
                    "explicit_lease_push_rejection": "stale info",
                    "concurrent_change_preserved": True,
                },
            ],
        }
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
