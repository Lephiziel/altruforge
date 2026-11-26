#!/usr/bin/env python3
"""Full-path S1 infrastructure smoke test; never part of the S1 dataset."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import http.server
import json
import os
import pathlib
import subprocess
import sys
import threading
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import runner  # noqa: E402


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", required=True)
    p.add_argument("--owner-token-file", required=True)
    p.add_argument("--observer-token-file", required=True)
    p.add_argument("--output-dir", required=True)
    a = p.parse_args()
    out = pathlib.Path(a.output_dir)
    out.mkdir(mode=0o700, parents=True, exist_ok=False)
    captures = out / "captures"
    captures.mkdir(mode=0o700)
    owner_token = pathlib.Path(a.owner_token_file).read_text().strip()
    repo = "nir03-s1r2-infra-smoke"
    label = "nir03-s1r2-infra-smoke-R5-recovery"
    direct = a.base_url.rstrip("/")

    status, raw = runner.api(
        direct,
        owner_token,
        "POST",
        "/user/repos",
        {"name": repo, "private": True, "auto_init": False, "default_branch": "main"},
    )
    if status not in (200, 201):
        raise RuntimeError(f"smoke repository creation failed: HTTP {status}")
    grant_status, _ = runner.api(
        direct,
        owner_token,
        "PUT",
        f"/repos/researcher/{repo}/collaborators/s1-observer",
        {"permission": "read"},
    )
    if grant_status not in (200, 201, 204):
        raise RuntimeError(f"read-only collaborator grant failed: HTTP {grant_status}")

    identity = {}

    def predispatch(base_sha, candidate_sha, competitor_sha, object_format):
        verification = hashlib.sha256(
            f"NIR03-S1-VERIFIED\n{label}\n{candidate_sha}\n".encode()
        ).hexdigest()
        intent = {
            "schema": "nir03-s1-infra-smoke-intent-v1",
            "label": label,
            "repository": repo,
            "base_sha": base_sha,
            "candidate_sha": candidate_sha,
            "verification_id": verification,
            "object_format": object_format,
            "expected_effects": ["feature ref", "exact PR", "exact status"],
            "created_at": utc(),
        }
        runner.atomic(out / "intent.json", intent)
        identity.update(intent)

    base_sha, candidate_sha, _, object_format, branch_visibility = runner.make_fixture_and_push(
        direct,
        owner_token,
        a.owner_token_file,
        repo,
        label,
        "R5",
        predispatch=predispatch,
    )
    verify = identity["verification_id"]

    branch = runner.api(direct, owner_token, "GET", f"/repos/researcher/{repo}/branches/feature")
    if branch[0] != 200 or runner.parsed(branch)["commit"]["id"] != candidate_sha:
        raise RuntimeError(
            f"pushed candidate ref mismatch: HTTP {branch[0]}, "
            f"response={runner.parsed(branch)!r}, expected={candidate_sha}"
        )
    main = runner.api(direct, owner_token, "GET", f"/repos/researcher/{repo}/branches/main")
    if main[0] != 200 or runner.parsed(main)["commit"]["id"] != base_sha:
        raise RuntimeError("pushed main ref did not match base identity")
    status, _ = runner.make_status(direct, owner_token, repo, candidate_sha, verify)
    if status not in (200, 201):
        raise RuntimeError(f"smoke status creation failed: HTTP {status}")

    events, proxy_events, barriers, rules = [], [], [], []
    target = urllib.parse.urlsplit(direct)
    proxy = runner.Proxy(("127.0.0.1", 0), runner.ProxyHandler)
    proxy.target = target
    proxy.events = proxy_events
    proxy.barriers = barriers
    proxy.rules = rules
    threading.Thread(target=proxy.serve_forever, daemon=True).start()
    proxy_url = f"http://127.0.0.1:{proxy.server_address[1]}"

    worker_row = {"barriers": [], "protocol_deviations": []}
    for stage in ("read", "dispatch", "classify"):
        runner.run_interrupted_worker(
            stage,
            proxy_url,
            a.owner_token_file,
            repo,
            candidate_sha,
            label,
            out / "intent.json",
            worker_row,
        )
    if len(worker_row["barriers"]) != 3 or not all(
        x["kill_confirmed"] for x in worker_row["barriers"]
    ):
        raise RuntimeError(f"worker barriers or SIGKILL confirmation failed: {worker_row}")

    recovered = runner.recovery_reads(proxy_url, owner_token, repo, candidate_sha)
    if recovered.get("branch_sha") != candidate_sha or recovered.get("exact_pr_count") != 1:
        raise RuntimeError(f"recovery failed to observe exact ref and one PR: {recovered}")

    # Verify observer-facing 503 capture, then restore the endpoint and collect a terminal view.
    rules.append(
        {
            "name": "smoke-pulls-503",
            "method": "GET",
            "match": "/pulls?",
            "mode": "503",
            "active": True,
            "once": True,
        }
    )
    outage_capture = runner.observe(
        proxy_url,
        a.observer_token_file,
        repo,
        candidate_sha,
        base_sha,
        captures,
        label + "-outage",
    )
    rules.clear()
    terminal_capture = runner.observe(
        proxy_url,
        a.observer_token_file,
        repo,
        candidate_sha,
        base_sha,
        captures,
        label + "-terminal",
    )
    terminal = runner.derive_terminal(
        proxy_url, owner_token, repo, candidate_sha, label, verify, base_sha
    )
    if terminal["classification"] != "complete" or terminal["exact_pr_count"] != 1:
        raise RuntimeError(f"terminal recovery did not classify exact completion: {terminal}")

    capture_docs = [json.loads(pathlib.Path(x).read_text()) for x in (outage_capture, terminal_capture)]
    outage_pulls = next(
        x for x in capture_docs[0]["observations"] if x["name"] == "pulls"
    )
    if outage_pulls.get("http_status") != 503:
        raise RuntimeError("independent observer failed to capture injected HTTP 503")
    for doc in capture_docs:
        for observation in doc["observations"]:
            body = pathlib.Path(observation["raw_body_file"]).read_bytes()
            if hashlib.sha256(body).hexdigest() != observation["raw_body_sha256"]:
                raise RuntimeError("raw response digest mismatch")

    result = {
        "schema": "nir03-s1-infrastructure-smoke-v1",
        "label": label,
        "scenario": "R5-infrastructure-only",
        "policy": "candidate-reconciliation-infrastructure-only",
        "run_id": label,
        "status": "smoke-passed",
        "separate_from_registered_dataset": True,
        "repository": repo,
        "base_sha": base_sha,
        "candidate_sha": candidate_sha,
        "verification_id": verify,
        "object_format": identity["object_format"],
        "branch_visibility_poll_evidence": branch_visibility,
        "observer_captures": [outage_capture, terminal_capture],
        "terminal_recovery": terminal,
        "worker_barriers": worker_row["barriers"],
        "barriers": worker_row["barriers"],
        "worker_deviations": worker_row["protocol_deviations"],
        "worker_process_terminations_confirmed": all(
            x["kill_confirmed"] for x in worker_row["barriers"]
        ),
        "observer_read_only_grant_http": grant_status,
        "fault_proxy_events": proxy_events,
        "fault_proxy_barriers": barriers,
        "created_at": utc(),
    }

    # Independent smoke-only R4: forward a create to Forgejo, drop its ack,
    # and require a separate observer to find exactly one applied PR.
    repo2 = "nir03-s1r2-infra-smoke-ambiguous"
    label2 = "nir03-s1r2-infra-smoke-R4-ambiguous"
    status, _ = runner.api(
        direct,
        owner_token,
        "POST",
        "/user/repos",
        {"name": repo2, "private": True, "auto_init": False, "default_branch": "main"},
    )
    if status not in (200, 201):
        raise RuntimeError(f"ambiguous smoke repository creation failed: HTTP {status}")
    grant2, _ = runner.api(
        direct,
        owner_token,
        "PUT",
        f"/repos/researcher/{repo2}/collaborators/s1-observer",
        {"permission": "read"},
    )
    if grant2 not in (200, 201, 204):
        raise RuntimeError(f"ambiguous smoke read grant failed: HTTP {grant2}")
    identity2 = {}

    def predispatch2(base_id, candidate_id, competitor_id, fmt):
        verification = hashlib.sha256(
            f"NIR03-S1-VERIFIED\n{label2}\n{candidate_id}\n".encode()
        ).hexdigest()
        intent2 = {
            "schema": "nir03-s1-infra-smoke-intent-v1",
            "label": label2,
            "repository": repo2,
            "base_sha": base_id,
            "candidate_sha": candidate_id,
            "verification_id": verification,
            "object_format": fmt,
            "expected_effects": ["feature ref", "exact PR", "exact status"],
            "created_at": utc(),
        }
        runner.atomic(out / "ambiguous-intent.json", intent2)
        identity2.update(intent2)

    base2, candidate2, _, _, visibility2 = runner.make_fixture_and_push(
        direct,
        owner_token,
        a.owner_token_file,
        repo2,
        label2,
        "R4",
        predispatch=predispatch2,
    )
    status, _ = runner.make_status(direct, owner_token, repo2, candidate2, identity2["verification_id"])
    if status not in (200, 201):
        raise RuntimeError(f"ambiguous smoke status creation failed: HTTP {status}")
    rules.append(
        {
            "name": "smoke-forward-and-drop-create-ack",
            "method": "POST",
            "match": f"/repos/researcher/{repo2}/pulls",
            "mode": "forward-drop",
            "active": True,
            "once": True,
        }
    )
    transport_error = None
    try:
        runner.api(proxy_url, owner_token, "POST", f"/repos/researcher/{repo2}/pulls", runner.pr_body(label2), timeout=3)
    except Exception as exc:
        transport_error = type(exc).__name__
    ambiguous_barrier = next((x for x in barriers if x.get("barrier") == "upstream_effect_committed_ack_dropped" and x.get("path", "").endswith("/pulls")), None)
    if not ambiguous_barrier or ambiguous_barrier.get("status") not in (200, 201):
        raise RuntimeError(f"ambiguous effect barrier missing or not successful: {ambiguous_barrier}")
    ambiguous_capture = runner.observe(
        proxy_url,
        a.observer_token_file,
        repo2,
        candidate2,
        base2,
        captures,
        label2 + "-terminal",
    )
    ambiguous_terminal = runner.derive_terminal(
        proxy_url, owner_token, repo2, candidate2, label2, identity2["verification_id"], base2
    )
    if ambiguous_terminal["classification"] != "complete" or ambiguous_terminal["exact_pr_count"] != 1:
        raise RuntimeError(f"ambiguous effect did not converge to one observed PR: {ambiguous_terminal}")
    ambiguous_doc = json.loads(pathlib.Path(ambiguous_capture).read_text())
    capture_docs.append(ambiguous_doc)
    for doc in capture_docs:
        for observation in doc["observations"]:
            body = pathlib.Path(observation["raw_body_file"]).read_bytes()
            if hashlib.sha256(body).hexdigest() != observation["raw_body_sha256"]:
                raise RuntimeError("raw response digest mismatch in smoke captures")
    result2 = {
        "schema": "nir03-s1-infrastructure-smoke-v1",
        "label": label2,
        "scenario": "R4-infrastructure-only",
        "policy": "contract-aware-infrastructure-only",
        "run_id": label2,
        "status": "smoke-passed",
        "separate_from_registered_dataset": True,
        "repository": repo2,
        "base_sha": base2,
        "candidate_sha": candidate2,
        "verification_id": identity2["verification_id"],
        "object_format": identity2["object_format"],
        "fixture_branch_visibility": visibility2,
        "observer_captures": [ambiguous_capture],
        "terminal_recovery_observations": ambiguous_terminal,
        "barriers": [ambiguous_barrier],
        "proxy_transport_error": transport_error,
        "created_at": utc(),
    }
    runner.atomic(out / "results.json", {"assignments": [result, result2]})
    evaluation = subprocess.run(
        [
            sys.executable,
            str(pathlib.Path(__file__).with_name("evaluation.py")),
            str(out / "results.json"),
            "--expected-label",
            label,
            "--expected-label",
            label2,
            "--output",
            str(out / "evaluation.json"),
        ],
        text=True,
        capture_output=True,
        env=runner.clean_python_environment(),
        check=True,
    )
    eval_doc = json.loads((out / "evaluation.json").read_text())
    if not eval_doc["all_expected_present"] or any(c["terminal_classification_from_observation"] != "complete" for c in eval_doc["cells"]):
        raise RuntimeError("independent smoke evaluation did not derive complete from observer evidence")
    result["independent_evaluation"] = eval_doc
    runner.atomic(out / "smoke-summary.json", result)
    proxy.shutdown()


if __name__ == "__main__":
    main()
