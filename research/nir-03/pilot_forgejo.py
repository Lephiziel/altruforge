#!/usr/bin/env python3
"""Run the frozen P0.1 recovery matrix against a disposable local Forgejo."""

from __future__ import annotations

import argparse
import http.client
import http.server
import json
import os
import platform
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


OWNER = "researcher"
SCENARIOS = (
    "no_fault",
    "before_dispatch",
    "effect_before_completion",
    "delayed_acknowledgement",
    "remote_drift",
)
POLICIES = (
    "blind_retry",
    "checkpoint_replay",
    "fail_stop",
    "contract_aware",
    "candidate_reconciliation",
)


def run(command: list[str], cwd: Path | None = None, env: dict | None = None):
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result


def sanitized_git_env(token_file: Path, askpass: Path) -> dict[str, str]:
    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(token_file.parent),
        "LC_ALL": "C",
        "GIT_ALLOW_PROTOCOL": "http:file",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": str(askpass),
        "NIR03_TOKEN_FILE": str(token_file),
        "NIR03_FORGE_USER": OWNER,
    }


def api(base_url: str, token: str, method: str, path: str, body=None, timeout=5):
    payload = None if body is None else json.dumps(body).encode()
    headers = {"Authorization": f"token {token}", "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/v1/{path.lstrip('/')}",
        data=payload,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        raw = error.read()
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = None
        return error.code, parsed


def create_repo(base_url: str, token: str, name: str):
    status, repo = api(
        base_url,
        token,
        "POST",
        "/user/repos",
        {"name": name, "private": True, "auto_init": True, "default_branch": "main"},
    )
    if status not in (200, 201):
        raise RuntimeError(f"repository creation failed with HTTP {status}")
    return repo


def create_pull(base_url: str, token: str, repo: str, branch: str, marker: str, timeout=5):
    return api(
        base_url,
        token,
        "POST",
        f"/repos/{OWNER}/{repo}/pulls",
        {
            "head": f"{OWNER}:{branch}",
            "base": "main",
            "title": f"Disposable P0.1 candidate {marker}",
            "body": f"Synthetic NIR-03 experiment. Run marker: {marker}\nCandidate identity is recorded in the experiment artifact.",
            "draft": True,
        },
        timeout=timeout,
    )


def find_pulls(base_url: str, token: str, repo: str, branch: str):
    query = urllib.parse.urlencode(
        {"state": "all", "head": f"{OWNER}:{branch}", "base": "main"}
    )
    status, pulls = api(
        base_url, token, "GET", f"/repos/{OWNER}/{repo}/pulls?{query}"
    )
    if status != 200 or not isinstance(pulls, list):
        return status, []
    exact = [
        item
        for item in pulls
        if item.get("head", {}).get("ref") == branch
        and item.get("base", {}).get("ref") == "main"
    ]
    return status, exact


def branch_sha(base_url: str, token: str, repo: str, branch: str):
    status, value = api(
        base_url, token, "GET", f"/repos/{OWNER}/{repo}/branches/{branch}"
    )
    if status == 404:
        return status, None
    if status != 200:
        return status, None
    return status, value.get("commit", {}).get("id")


def write_status(base_url: str, token: str, repo: str, sha: str):
    return api(
        base_url,
        token,
        "POST",
        f"/repos/{OWNER}/{repo}/statuses/{sha}",
        {
            "state": "success",
            "context": "nir03/p01-experiment",
            "description": "Synthetic exact-commit verification receipt",
        },
    )


class DelayedAckProxy(http.server.ThreadingHTTPServer):
    daemon_threads = True


def delayed_proxy(base_url: str, token: str, delay: float):
    target = urllib.parse.urlsplit(base_url)

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802 - stdlib handler name
            size = int(self.headers.get("Content-Length", "0"))
            payload = self.rfile.read(size)
            connection = http.client.HTTPConnection(
                target.hostname, target.port, timeout=5
            )
            headers = {
                key: value
                for key, value in self.headers.items()
                if key.lower() not in {"host", "connection", "content-length"}
            }
            connection.request("POST", self.path, payload, headers)
            response = connection.getresponse()
            body = response.read()
            status = response.status
            response_headers = response.getheaders()
            connection.close()
            time.sleep(delay)
            try:
                self.send_response(status)
                for key, value in response_headers:
                    if key.lower() not in {
                        "connection",
                        "content-length",
                        "transfer-encoding",
                        "content-type",
                    }:
                        continue
                    if key.lower() != "transfer-encoding":
                        self.send_header(key, value)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def log_message(self, _format, *_args):
            return

    proxy = DelayedAckProxy(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=proxy.serve_forever, daemon=True)
    thread.start()
    return f"http://127.0.0.1:{proxy.server_address[1]}", proxy, thread


def worker_main(args):
    print("armed", flush=True)
    signal_text = sys.stdin.readline().strip()
    if signal_text != "dispatch":
        return 0
    token = Path(args.token_file).read_text().strip()
    try:
        status, _value = create_pull(
            args.base_url, token, args.repo, args.branch, args.marker, args.worker_timeout
        )
        print(f"effect:{status}", flush=True)
        sys.stdin.readline()
        return 0
    except (TimeoutError, urllib.error.URLError, OSError) as error:
        print(f"transport_error:{type(error).__name__}", flush=True)
        return 0


def start_worker(base_url: str, token_file: Path, repo: str, branch: str, marker: str, worker_timeout=5):
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--base-url",
        base_url,
        "--token-file",
        str(token_file),
        "--repo",
        repo,
        "--branch",
        branch,
        "--marker",
        marker,
        "--worker-timeout",
        str(worker_timeout),
    ]
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONIOENCODING": "utf-8"},
    )
    ready = process.stdout.readline().strip()
    if ready != "armed":
        process.kill()
        raise RuntimeError("fault worker failed to arm")
    return process


def git_call(command: list[str], cwd: Path, env: dict[str, str]):
    result = run(["git", *command], cwd, env)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def prepare_repo(base_url: str, token: str, token_file: Path, askpass: Path, repo: str, scenario: str, root: Path):
    create_repo(base_url, token, repo)
    work = root / "worker"
    env = sanitized_git_env(token_file, askpass)
    cloned = run(["git", "clone", f"{base_url}/{OWNER}/{repo}.git", str(work)], env=env)
    if cloned.returncode:
        raise RuntimeError(f"clone failed ({cloned.returncode}): {cloned.stderr.strip()}")
    for key, value in (("user.name", "NIR-03 Experiment"), ("user.email", "nir03@example.invalid")):
        git_call(["config", key, value], work, env)
    base_sha = git_call(["rev-parse", "HEAD"], work, env)["stdout"]
    git_call(["checkout", "-b", "feature"], work, env)
    (work / "candidate.txt").write_text("synthetic candidate\n", encoding="utf-8")
    git_call(["add", "candidate.txt"], work, env)
    commit = git_call(["commit", "-m", "synthetic candidate"], work, env)
    if commit["returncode"]:
        raise RuntimeError("candidate commit failed")
    candidate_sha = git_call(["rev-parse", "HEAD"], work, env)["stdout"]
    git_call(["checkout", "main"], work, env)
    seeded = git_call(
        ["push", "origin", "HEAD:refs/heads/feature"], work, env
    )
    if seeded["returncode"]:
        raise RuntimeError("feature ref seeding failed")
    git_call(["checkout", "feature"], work, env)
    git_call(["reset", "--hard", candidate_sha], work, env)

    if scenario != "remote_drift":
        candidate_push = git_call(
            [
                "push",
                f"--force-with-lease=refs/heads/feature:{base_sha}",
                "origin",
                "HEAD:refs/heads/feature",
            ],
            work,
            env,
        )
        if candidate_push["returncode"]:
            raise RuntimeError("candidate ref push failed before fault injection")

    drift_sha = None
    competitor = None
    if scenario == "remote_drift":
        competitor = root / "competitor"
        cl = run(
            ["git", "clone", f"{base_url}/{OWNER}/{repo}.git", str(competitor)],
            env=env,
        )
        if cl.returncode:
            raise RuntimeError(f"competitor clone failed: {cl.stderr.strip()}")
        for key, value in (("user.name", "Concurrent Writer"), ("user.email", "writer@example.invalid")):
            git_call(["config", key, value], competitor, env)
        git_call(["checkout", "-b", "competitor", "origin/feature"], competitor, env)
        (competitor / "concurrent.txt").write_text("concurrent update\n", encoding="utf-8")
        git_call(["add", "concurrent.txt"], competitor, env)
        if git_call(["commit", "-m", "concurrent update"], competitor, env)["returncode"]:
            raise RuntimeError("competitor commit failed")
        drift_sha = git_call(["rev-parse", "HEAD"], competitor, env)["stdout"]
        pushed = git_call(["push", "origin", "HEAD:refs/heads/feature"], competitor, env)
        if pushed["returncode"]:
            raise RuntimeError("concurrent ref drift setup failed")

    return work, env, base_sha, candidate_sha, drift_sha


def exact_pull(pulls: list[dict], candidate: str, marker: str):
    return [
        p
        for p in pulls
        if p.get("head", {}).get("sha") == candidate
        and p.get("base", {}).get("ref") == "main"
        and p.get("draft") is True
        and marker in p.get("body", "")
        and p.get("merged") is False
    ]


def execute_trial(base_url: str, token_file: Path, askpass: Path, scenario: str, policy: str, root: Path, index: int):
    token = token_file.read_text().strip()
    repo = f"p01-{index:02d}-{uuid.uuid4().hex[:10]}"
    run_id = f"nir03-p01-{index:02d}-{uuid.uuid4().hex[:12]}"
    marker = f"run:{run_id}"
    work, git_env, base_sha, candidate_sha, drift_sha = prepare_repo(
        base_url, token, token_file, askpass, repo, scenario, root
    )
    status_created, _status_body = write_status(
        base_url, token, repo, candidate_sha
    )
    if status_created not in (200, 201):
        raise RuntimeError(f"exact-candidate verification status failed with HTTP {status_created}")
    ledger_path = root / "intent.json"
    ledger = {
        "run_id": run_id,
        "repository": f"{OWNER}/{repo}",
        "branch": "feature",
        "base_sha": base_sha,
        "candidate_sha": candidate_sha,
        "marker": marker,
        "state": "pr_create_intent",
    }
    ledger_path.write_text(json.dumps(ledger, sort_keys=True) + "\n", encoding="utf-8")
    initial_effect = None
    worker_exit = None
    delayed_proxy_server = None

    if scenario == "remote_drift":
        lease_push = git_call(
            [
                "push",
                f"--force-with-lease=refs/heads/feature:{base_sha}",
                "origin",
                "HEAD:refs/heads/feature",
            ],
            work,
            git_env,
        )
        initial_effect = {
            "operation": "git_push_with_explicit_lease",
            "returncode": lease_push["returncode"],
            "rejected_as_stale": "stale info" in lease_push["stderr"],
        }
    elif scenario == "before_dispatch":
        worker = start_worker(base_url, token_file, repo, "feature", marker)
        worker.kill()
        worker_exit = worker.wait(timeout=5)
        initial_effect = {"operation": "draft_pr_create", "dispatched": False}
    elif scenario == "effect_before_completion":
        worker = start_worker(base_url, token_file, repo, "feature", marker)
        worker.stdin.write("dispatch\n")
        worker.stdin.flush()
        event = worker.stdout.readline().strip()
        worker.kill()
        worker_exit = worker.wait(timeout=5)
        initial_effect = {
            "operation": "draft_pr_create",
            "http_status": int(event.split(":", 1)[1]) if event.startswith("effect:") else None,
            "worker_killed": True,
        }
    elif scenario == "delayed_acknowledgement":
        proxy_url, delayed_proxy_server, proxy_thread = delayed_proxy(base_url, token, 1.0)
        worker = start_worker(proxy_url, token_file, repo, "feature", marker, worker_timeout=0.2)
        worker.stdin.write("dispatch\n")
        worker.stdin.flush()
        event = worker.stdout.readline().strip()
        worker_exit = worker.wait(timeout=5)
        time.sleep(1.1)
        delayed_proxy_server.shutdown()
        delayed_proxy_server.server_close()
        proxy_thread.join(timeout=2)
        initial_effect = {
            "operation": "draft_pr_create",
            "client_observation": event,
            "worker_exit": worker_exit,
            "proxy_delayed_seconds": 1.0,
        }
    else:
        initial_effect = {"operation": "none_before_first_attempt"}

    status, pulls = find_pulls(base_url, token, repo, "feature")
    strategy_action = "normal_first_attempt"
    recovered_status = None

    if scenario == "remote_drift":
        strategy_action = "conflict_observed"
        if policy in ("blind_retry", "checkpoint_replay"):
            retry = git_call(["push", "origin", "HEAD:refs/heads/feature"], work, git_env)
            recovered_status = {"git_returncode": retry["returncode"], "no_force_used": True}
        elif policy == "fail_stop":
            strategy_action = "stopped_after_ambiguous_ref_conflict"
        else:
            observed, observed_sha = branch_sha(base_url, token, repo, "feature")
            strategy_action = "conflict" if observed == 200 and observed_sha != candidate_sha else "unexpected_branch_state"
            if policy == "candidate_reconciliation":
                # Exercise the same native conditional update the contract baseline uses.
                cas = git_call(
                    [
                        "push",
                        f"--force-with-lease=refs/heads/feature:{base_sha}",
                        "origin",
                        "HEAD:refs/heads/feature",
                    ],
                    work,
                    git_env,
                )
                recovered_status = {"lease_returncode": cas["returncode"], "stale_rejection": "stale info" in cas["stderr"]}
        outcome = "conflict" if strategy_action in ("conflict", "stopped_after_ambiguous_ref_conflict", "conflict_observed") else "unknown"
    elif scenario == "no_fault":
        created, _value = create_pull(base_url, token, repo, "feature", marker)
        recovered_status = {"http_status": created}
        strategy_action = "normal_create"
    elif policy == "fail_stop":
        strategy_action = "stopped_without_recovery_write"
        outcome = "unknown"
    elif scenario == "effect_before_completion" or scenario == "delayed_acknowledgement":
        if policy in ("blind_retry", "checkpoint_replay"):
            recovered_status, _value = create_pull(base_url, token, repo, "feature", marker)
            strategy_action = "replayed_pr_create"
        else:
            status, pulls = find_pulls(base_url, token, repo, "feature")
            existing = exact_pull(pulls, candidate_sha, marker)
            if existing:
                strategy_action = "adopted_exact_existing_pr"
            elif not pulls:
                recovered_status, _value = create_pull(base_url, token, repo, "feature", marker)
                strategy_action = "created_after_absence_probe"
            else:
                strategy_action = "conflicting_pr_found"
    elif scenario == "before_dispatch":
        if policy in ("contract_aware", "candidate_reconciliation"):
            status, pulls = find_pulls(base_url, token, repo, "feature")
            if exact_pull(pulls, candidate_sha, marker):
                strategy_action = "unexpected_existing_exact_pr"
            else:
                recovered_status, _value = create_pull(base_url, token, repo, "feature", marker)
                strategy_action = "created_after_absence_probe"
        else:
            recovered_status, _value = create_pull(base_url, token, repo, "feature", marker)
            strategy_action = "replayed_pr_create"

    # A separate observer reads state regardless of the policy's own knowledge.
    observed_http, observed_branch = branch_sha(base_url, token, repo, "feature")
    pulls_http, pulls = find_pulls(base_url, token, repo, "feature")
    exact = exact_pull(pulls, candidate_sha, marker)
    status_http, candidate_statuses = api(
        base_url, token, "GET", f"/repos/{OWNER}/{repo}/statuses/{candidate_sha}"
    )
    wrong_sha_http, base_statuses = api(
        base_url, token, "GET", f"/repos/{OWNER}/{repo}/statuses/{base_sha}"
    )
    status_attribution = (
        status_http == 200
        and isinstance(candidate_statuses, list)
        and any(s.get("context") == "nir03/p01-experiment" for s in candidate_statuses)
        and wrong_sha_http == 200
        and isinstance(base_statuses, list)
        and not any(s.get("context") == "nir03/p01-experiment" for s in base_statuses)
    )
    if scenario == "remote_drift":
        outcome = "conflict" if observed_branch == drift_sha else "unsafe_or_unknown"
    elif policy == "fail_stop" and scenario != "no_fault":
        outcome = "unknown"
    else:
        outcome = "complete" if exact and status_attribution else "unknown"
    if policy == "candidate_reconciliation":
        ledger["state"] = outcome
        ledger["expected_effects"] = ["feature_ref_at_candidate_sha", "exact_draft_pr", "candidate_sha_status"]
    else:
        ledger["state"] = "complete" if exact else "pending"
    ledger_path.write_text(json.dumps(ledger, sort_keys=True) + "\n", encoding="utf-8")

    exact_count = len(exact)
    branch_preserved = observed_branch == (drift_sha if scenario == "remote_drift" else candidate_sha)
    unsafe_completion = ledger["state"] == "complete" and not (exact and branch_preserved and status_attribution)
    no_merge = not any(item.get("merged") is True for item in pulls)
    return {
        "scenario": scenario,
        "policy": policy,
        "repository": f"{OWNER}/{repo}",
        "run_marker": marker,
        "base_sha": base_sha,
        "candidate_sha": candidate_sha,
        "concurrent_sha": drift_sha,
        "worker_exit": worker_exit,
        "initial_effect": initial_effect,
        "recovery_action": strategy_action,
        "recovery_observation": recovered_status,
        "observer": {
            "branch_http": observed_http,
            "branch_sha": observed_branch,
            "pulls_http": pulls_http,
            "matching_pull_count": len(pulls),
            "exact_candidate_draft_count": exact_count,
            "candidate_status_http": status_http,
            "base_status_http": wrong_sha_http,
            "status_attributed_only_to_candidate": status_attribution,
            "merged": not no_merge,
        },
        "ledger_outcome": ledger["state"],
        "unsafe_completion": unsafe_completion,
        "unauthorized_or_duplicate_effect": len(pulls) != exact_count or exact_count > 1 or not no_merge or (scenario == "remote_drift" and observed_branch != drift_sha),
        "eligible_resolution": scenario != "remote_drift" and outcome == "complete",
        "outcome": outcome,
        "trial_index": index,
    }


def run_study(args):
    parsed = urllib.parse.urlsplit(args.base_url)
    if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit("refusing non-loopback Forgejo URL")
    token_file = Path(args.token_file).resolve()
    if not token_file.is_file() or token_file.stat().st_mode & 0o077:
        raise SystemExit("token file must exist with mode 0600 or stricter")
    output = Path(args.output)
    if output.exists():
        raise SystemExit("output already exists; use a fresh path so assigned trials cannot be overwritten")
    token = token_file.read_text().strip()
    status, version = api(args.base_url, token, "GET", "/version")
    if status != 200 or not isinstance(version, dict):
        raise SystemExit(f"Forgejo version probe failed with HTTP {status}")
    if not version.get("version", "").startswith("17.0.2"):
        raise SystemExit(f"expected Forgejo 17.0.2, observed {version.get('version')!r}")

    root = Path(args.disposable_root).resolve()
    if root.exists():
        raise SystemExit("disposable root already exists; choose a new empty directory")
    root.mkdir(parents=True, mode=0o700)
    askpass = root / "git-askpass.py"
    askpass.write_text(
        "#!/usr/bin/env python3\n"
        "import os, pathlib, sys\n"
        "prompt=sys.argv[1].lower()\n"
        "print(os.environ['NIR03_FORGE_USER'] if 'username' in prompt else pathlib.Path(os.environ['NIR03_TOKEN_FILE']).read_text().strip())\n",
        encoding="utf-8",
    )
    askpass.chmod(0o700)

    trials = []
    index = 0
    for scenario in SCENARIOS:
        for policy in POLICIES:
            index += 1
            trial_root = root / f"trial-{index:02d}"
            trial_root.mkdir(mode=0o700)
            trials.append(
                execute_trial(
                    args.base_url,
                    token_file,
                    askpass,
                    scenario,
                    policy,
                    trial_root,
                    index,
                )
            )
    result = {
        "study": "NIR-03 P0.1 exploratory Forgejo pilot",
        "protocol_revision": "frozen-before-execution",
        "forgejo_version": version["version"],
        "git_version": run(["git", "--version"]) .stdout.strip(),
        "python_version": platform.python_version(),
        "platform": f"{platform.system()} {platform.machine()}",
        "forge_url_scope": "loopback only",
        "actions_enabled": False,
        "automatic_merge_enabled": False,
        "assigned_trial_count": len(trials),
        "scenario_count": len(SCENARIOS),
        "policy_count": len(POLICIES),
        "trials": trials,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"assigned": len(trials), "output": str(output), "forgejo": version["version"]}))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--token-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--disposable-root", default="/tmp/altruforge-nir03-study")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--repo", default="")
    parser.add_argument("--branch", default="feature")
    parser.add_argument("--marker", default="")
    parser.add_argument("--worker-timeout", type=float, default=5)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.worker:
        raise SystemExit(worker_main(arguments))
    run_study(arguments)
