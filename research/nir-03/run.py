"""Run the Forgejo contract probes and the exploratory P0.1 trial matrix."""

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path
import platform
import select
import signal
import socket
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import time

from characterize import characterize
from lab import ACTOR, BASE, HEAD, OWNER, Fixture, Journal, Lab, digest, git, git_result, now
from oracle import assess, pr_view, snapshot
from worker import RESPONSE_LOST, STRATEGIES, read_ledger, seal


SCENARIOS = {
    "control": (),
    "kill-before-create": ("before_create",),
    "kill-after-create": ("after_create",),
    "drop-response": (),
    "drift-before-recovery": ("after_create",),
    "kill-while-recovering": ("after_create", "before_verdict"),
    "kill-after-receipt": ("after_receipt",),
}


def ensure(condition, description):
    if not condition:
        raise RuntimeError(description)


class CreateRelay:
    """One fixed POST route. Read-only probes bypass the relay."""

    def __init__(self, lab, repo, record, drop):
        self.lab = lab
        self.repo = repo
        self.path = f"{lab.repo_path(repo)}/pulls"
        self.record = record
        self.drop = drop
        self.requests = 0
        self.created = []
        self.dropped = False
        self.drop_finished = threading.Event()
        self.error = None
        relay = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                try:
                    relay.forward(self)
                except Exception as exc:
                    relay.error = str(exc)
                    record("relay_error", error=str(exc))
                    self.send_error(502)

            def log_message(self, *_):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.origin = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.02})

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()

    def forward(self, handler):
        handler.connection.settimeout(12)
        ensure(handler.path == self.path, "relay received an unscoped route")
        ensure(handler.headers.get("Authorization") == self.lab.auth(OWNER), "unexpected relay caller")
        size = int(handler.headers["Content-Length"])
        ensure(0 < size <= 4096, "unexpected body size")
        payload = json.loads(handler.rfile.read(size))
        self.requests += 1
        self.record("forge_forward", request=self.requests, method="POST", path=self.path, data=payload)
        status, response = self.lab.call(self.path, "POST", payload)
        view = pr_view(response) if status == 201 else response
        self.record("forge_response", request=self.requests, status=status, data=view)
        if status == 201:
            self.created.append(view)
        if self.drop and self.requests == 1:
            self.drop_confirmed_response(handler, status, view)
            return
        data = json.dumps(response).encode()
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)

    def drop_confirmed_response(self, handler, status, pr):
        ensure(status == 201, "response-drop boundary did not receive HTTP 201")
        remote = snapshot(self.lab, self.repo)
        ensure(remote["prs"] == [pr], "oracle could not confirm the effect before response loss")
        self.record("response_drop_barrier", request=self.requests, remote=remote)
        handler.connection.shutdown(socket.SHUT_RDWR)
        handler.close_connection = True
        self.dropped = True
        self.record("response_dropped", request=self.requests, forwarded_response_bytes=0)
        self.drop_finished.set()


def short_ledger(path):
    return {key: value for key, value in read_ledger(path).items() if key != "intent"}


def kill_at_barrier(process, name, message, db_path, relay, record, attempt_number):
    before = short_ledger(db_path)
    remote = snapshot(relay.lab, relay.repo)
    ensure(before["verdict"] is None, "verdict persisted before kill barrier")
    ensure(before["submissions"] == relay.requests, "ledger and relay dispatch counts differ")
    if name == "before_create":
        ensure(not relay.requests and not remote["prs"] and before["submissions"] == 0,
               "the before-create barrier was reached after dispatch")
    else:
        ensure(len(relay.created) == len(remote["prs"]) == 1, "expected one observable PR effect")
        ensure(remote["prs"][0]["id"] == relay.created[0]["id"], "wrong PR at the kill barrier")
        if name == "after_create":
            ensure(before["receipt"] is None and message["status"] == 201
                   and message["receipt"]["id"] == remote["prs"][0]["id"],
                   "receipt is missing or already durable at the wrong boundary")
        if name == "after_receipt":
            ensure(before["receipt"] == message["receipt"] and before["receipt"] is not None,
                   "receipt was not durable at the kill barrier")
    record("kill_barrier_confirmed", attempt=attempt_number, boundary=name, remote=remote, ledger=before)
    process.kill()
    code = process.wait(timeout=5)
    ensure(code == -signal.SIGKILL, f"worker exited with {code}, expected SIGKILL")
    after = short_ledger(db_path)
    ensure(after == before, "ledger changed after stopping the worker at a barrier")
    record("sigkill_confirmed", attempt=attempt_number, boundary=name, pid=process.pid, exit=code, ledger=after)
    return code


def run_worker(strategy, number, kill, db_path, relay, record):
    command = [
        sys.executable, str(Path(__file__).with_name("worker.py")), "--ledger", str(db_path),
        "--strategy", strategy, "--relay", relay.origin,
    ]
    env = {**os.environ, "NIR03_PUBLISHER_AUTH": relay.lab.auth(OWNER), "PYTHONDONTWRITEBYTECODE": "1"}
    stderr_path = db_path.with_suffix(f".attempt-{number}.stderr")
    with stderr_path.open("w+") as stderr, subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr, text=True, env=env,
    ) as process:
        record("worker_started", attempt=number, pid=process.pid, command=command)
        try:
            while True:
                ready, _, _ = select.select([process.stdout], [], [], 40)
                ensure(ready, "worker barrier timed out")
                line = process.stdout.readline()
                if not line:
                    break
                message = json.loads(line)
                name = message["barrier"]
                record("worker_barrier", attempt=number, message=message)
                if name == kill:
                    return kill_at_barrier(process, name, message, db_path, relay, record, number)
                if name == "transport_lost":
                    ensure(relay.drop_finished.wait(timeout=2) and message["error"] == "RemoteDisconnected",
                           "worker observed a transport loss outside the planned response-drop fault")
                process.stdin.write("continue\n")
                process.stdin.flush()
            code = process.wait(timeout=5)
            stderr.seek(0)
            record("worker_exit", attempt=number, exit=code, stderr=stderr.read(), ledger=short_ledger(db_path))
            ensure(kill is None, f"worker exited before reaching {kill}")
            return code
        finally:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=5)
                stderr.seek(0)
                record("worker_cleanup", attempt=number, exit=process.returncode, stderr=stderr.read())


def wait_until_seeded(lab, repo, record):
    """Start the trial only after Forgejo exposes the newly populated repository."""
    path = f"{lab.repo_path(repo)}/pulls?state=all&limit=50&page=1"
    deadline = time.monotonic() + 5
    while True:
        status, body = lab.call(path, user=None)
        if status == 200:
            record("seed_visibility", status=status)
            return
        record("seed_visibility", status=status, response=body)
        ensure(status == 404 and time.monotonic() < deadline, "repository did not become visible after seed push")
        time.sleep(0.05)


def trial(lab, fixture, journal, scenario, strategy):
    repo = f"{strategy}-{scenario}"

    def record(event, **fields):
        journal.record(event, trial=repo, **fields)

    record("trial_started", scenario=scenario, strategy=strategy)
    repo_id = lab.create_repo(repo)
    db_path = lab.root / f"{repo}.sqlite"
    intent = {
        "origin": lab.origin, "repo": repo, "repo_id": repo_id,
        "task": "p0.1/verified-fixture", "run": repo, "publisher": OWNER,
        "base_ref": BASE, "base_sha": fixture.base,
        "candidate_ref": HEAD, "candidate_sha": fixture.candidate,
        "evidence": fixture.evidence, "evidence_sha256": digest(fixture.evidence),
    }
    intent["key"] = digest(intent)
    seal(db_path, intent)
    record("intent_sealed", intent=intent)
    for sha, ref in ((fixture.base, BASE), (fixture.candidate, HEAD)):
        pushed = lab.push(repo, fixture.source, sha, ref, f"--force-with-lease={ref}:")
        record("install_ref", actor=OWNER, ref=ref, git=git_result(pushed))
        pushed.check_returncode()
    wait_until_seeded(lab, repo, record)
    initial = snapshot(lab, repo)
    record("initial_remote", remote=initial)
    ensure(not initial["prs"] and initial["refs"] == {BASE: fixture.base, HEAD: fixture.candidate},
           "trial did not start from the assigned fixture")

    drop = scenario == "drop-response"
    kills = SCENARIOS[scenario]
    expected_head = fixture.candidate
    with CreateRelay(lab, repo, record, drop) as relay:
        started = time.monotonic_ns()
        first = run_worker(strategy, 1, kills[0] if kills else None, db_path, relay, record)
        expected_exit = -signal.SIGKILL if kills else RESPONSE_LOST if drop else 0
        ensure(first == expected_exit and not relay.error and relay.dropped == drop, "unexpected first attempt")
        if scenario == "drift-before-recovery":
            pushed = lab.push(repo, fixture.actor_source, fixture.drift_a, HEAD, user=ACTOR)
            record("contributor_push", actor=ACTOR, git=git_result(pushed))
            pushed.check_returncode()
            expected_head = fixture.drift_a
            drifted = snapshot(lab, repo)
            record("contributor_change_confirmed", remote=drifted)
            ensure(drifted["refs"].get(HEAD) == expected_head, "contributor's Git mutation not visible")

        recovery_start = None
        if kills or drop:
            recovery_start = time.monotonic_ns()
            if len(kills) == 2:
                code = run_worker(strategy, 2, kills[1], db_path, relay, record)
                ensure(code == -signal.SIGKILL, "recovery did not reach its assigned interruption")
            code = run_worker(strategy, len(kills) + 1 if kills else 2, None, db_path, relay, record)
            ensure(code == 0 and not relay.error, "last recovery attempt failed unexpectedly")
        finished = time.monotonic_ns()
        final = snapshot(lab, repo)
        persisted = read_ledger(db_path)
        result = assess(intent, persisted, final, relay.created, expected_head)
    result.update(
        scenario=scenario, strategy=strategy, trial=repo, post_requests=relay.requests,
        eligible=scenario != "drift-before-recovery",
        completion_or_stop_ms=round((finished - started) / 1e6, 3),
        recovery_attempts_ms=round((finished - recovery_start) / 1e6, 3) if recovery_start else None,
    )
    result["successful_recovery_ms"] = result["recovery_attempts_ms"] if result["successful"] else None
    record("oracle_final", remote=final, ledger=short_ledger(db_path), outcome=result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--forgejo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="new directory for execution records")
    parser.add_argument("--contract-only", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True)
    results = []
    lab_error = None
    with Journal(args.out / "trace.jsonl") as journal, TemporaryDirectory(prefix="nir03-") as work:
        try:
            journal.record(
                "environment", started_utc=now(), platform=platform.platform(),
                python=sys.version, sqlite=sqlite3.sqlite_version, git=git("--version").stdout.strip(),
                args=sys.argv, contract_only=args.contract_only,
                assigned=[{"scenario": scenario, "strategy": strategy}
                          for scenario in SCENARIOS for strategy in STRATEGIES] if not args.contract_only else [],
            )
            root = Path(work)
            fixture = Fixture.create(root)
            journal.record("fixture", evidence=fixture.evidence, evidence_sha256=digest(fixture.evidence),
                           drift_commits=[fixture.drift_a, fixture.drift_b])
            with Lab(args.forgejo, root, journal) as lab:
                characterize(lab, fixture, journal)
                if not args.contract_only:
                    for scenario in SCENARIOS:
                        for strategy in STRATEGIES:
                            try:
                                results.append(trial(lab, fixture, journal, scenario, strategy))
                            except Exception as exc:
                                result = {"scenario": scenario, "strategy": strategy,
                                          "error": str(exc), "trial": f"{strategy}-{scenario}"}
                                journal.record("trial_error", **result)
                                results.append(result)
        except Exception as exc:
            lab_error = str(exc)
            journal.record("lab_error", error=lab_error)
    errors = int(lab_error is not None) + sum("error" in result for result in results)
    (args.out / "outcomes.json").write_text(
        json.dumps({"lab_error": lab_error, "errors": errors, "trials": results}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{len(results)} assigned trials recorded, {errors} infrastructure errors. Records: {args.out}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
