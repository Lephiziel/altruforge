"""One disposable publication attempt. The supervisor controls named barriers."""

import argparse
import http.client
import json
import os
from pathlib import Path
import sqlite3
import sys

from lab import BASE, HEAD, OWNER, api, digest, ref_tips, require


STRATEGIES = ("retry", "checkpoint", "readback", "fail-stop", "retry-reconcile")
RESPONSE_LOST = 75


def seal(path, intent):
    if path.exists():
        raise FileExistsError(path)
    with sqlite3.connect(path) as db:
        db.executescript("""
            PRAGMA journal_mode = DELETE;
            PRAGMA synchronous = FULL;
            CREATE TABLE publication (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                intent TEXT NOT NULL,
                submissions INTEGER NOT NULL DEFAULT 0,
                receipt TEXT,
                verdict TEXT
            );
            CREATE TRIGGER sealed_intent BEFORE UPDATE OF intent ON publication
            BEGIN
                SELECT RAISE(ABORT, 'publication intent is immutable');
            END;
        """)
        db.execute("INSERT INTO publication (singleton, intent) VALUES (1, ?)", (json.dumps(intent),))


def ledger(db):
    intent, count, receipt, verdict = db.execute(
        "SELECT intent, submissions, receipt, verdict FROM publication WHERE singleton = 1"
    ).fetchone()
    return {
        "intent": json.loads(intent), "submissions": count,
        "receipt": json.loads(receipt) if receipt else None,
        "verdict": json.loads(verdict) if verdict else None,
    }


def read_ledger(path):
    with sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True) as db:
        return ledger(db)


def barrier(name, **details):
    print(json.dumps({"barrier": name, **details}), flush=True)
    if sys.stdin.readline() != "continue\n":
        raise RuntimeError(f"controller disconnected at {name}")


def pull_path(intent):
    return f"/api/v1/repos/{OWNER}/{intent['repo']}/pulls"


def branch_pair(pr, intent):
    for side, ref in (("head", "candidate"), ("base", "main")):
        fields = pr.get(side) or {}
        if fields.get("ref") != ref or (fields.get("repo") or {}).get("id") != intent["repo_id"]:
            return False
    return True


def matching_pulls(intent):
    path = pull_path(intent)
    matches = []
    for page in range(1, 21):
        items = require(api(intent["origin"], f"{path}?state=all&limit=50&page={page}"), 200)
        if not items:
            return matches
        matches.extend(pr for pr in items if branch_pair(pr, intent))
    raise RuntimeError("could not exhaust PR list")


def current_tips(intent):
    refs = ref_tips(f"{intent['origin']}/{OWNER}/{intent['repo']}.git")
    return {"head": refs.get(HEAD), "base": refs.get(BASE)}


def finish(db, intent, status, reason, pr=None):
    verdict = {"status": status, "reason": reason, "intent_key": intent["key"]}
    if pr:
        verdict.update(pr_id=pr["id"], pr_number=pr["number"])
    barrier("before_verdict", verdict=verdict)
    with db:
        db.execute("UPDATE publication SET verdict = ? WHERE singleton = 1", (json.dumps(verdict),))
    return 0


def verify_and_finish(db, intent, identity, reason):
    path = f"{pull_path(intent)}/{identity['number']}"
    status, pr = api(intent["origin"], path)
    if status != 200:
        return finish(db, intent, "unknown", f"canonical PR lookup returned HTTP {status}")
    marker = f"NIR-03 intent {intent['key']}"
    exact_tips = {"head": intent["candidate_sha"], "base": intent["base_sha"]}
    if (
        pr["id"] != identity["id"]
        or not branch_pair(pr, intent)
        or {side: pr[side]["sha"] for side in ("head", "base")} != exact_tips
        or current_tips(intent) != exact_tips
        or marker not in (pr.get("body") or "").splitlines()
        or not pr["title"].startswith("WIP: ")
        or pr.get("draft") is not True
        or pr["state"] != "open"
        or pr["merged"]
    ):
        return finish(db, intent, "blocked", "remote PR or ref identity conflicts with the sealed intent")
    return finish(db, intent, "complete", reason, pr)


def resolve_lookup(db, intent, reason):
    matches = matching_pulls(intent)
    if len(matches) == 1:
        return verify_and_finish(db, intent, matches[0], reason)
    if matches:
        return finish(db, intent, "blocked", "multiple historical PRs match the branch tuple")
    return finish(db, intent, "unknown", "absence does not settle an earlier submission")


def publish(db, state, relay, strategy):
    intent = state["intent"]
    barrier("before_create", previous_submissions=state["submissions"])
    with db:
        db.execute("UPDATE publication SET submissions = submissions + 1 WHERE singleton = 1")
    body = (
        f"NIR-03 intent {intent['key']}\n"
        f"Verified candidate {intent['candidate_sha']}\n"
        f"Verified base {intent['base_sha']}\n"
        f"Evidence SHA-256 {intent['evidence_sha256']}"
    )
    try:
        status, pr = api(
            relay, pull_path(intent), "POST",
            {"head": "candidate", "base": "main", "title": "WIP: NIR-03 fixture", "body": body},
            os.environ["NIR03_PUBLISHER_AUTH"],
        )
    except (OSError, http.client.HTTPException) as error:
        barrier("transport_lost", error=type(error).__name__)
        return RESPONSE_LOST
    if status == 409 and strategy == "retry-reconcile":
        return resolve_lookup(db, intent, "duplicate conflict, tuple lookup and canonical read")
    if status != 201:
        return finish(db, intent, "unknown", f"create returned HTTP {status} without a receipt")

    receipt = {"number": pr["number"], "id": pr["id"]}
    barrier("after_create", receipt=receipt, status=status)
    with db:
        db.execute("UPDATE publication SET receipt = ? WHERE singleton = 1", (json.dumps(receipt),))
    barrier("after_receipt", receipt=receipt)
    return verify_and_finish(db, intent, receipt, "creation response and canonical read")


def attempt(db, strategy, relay):
    state = ledger(db)
    intent = state["intent"]
    sealed = dict(intent)
    key = sealed.pop("key")
    evidence = intent["evidence"]
    if (digest(sealed) != key or digest(evidence) != intent["evidence_sha256"]
            or evidence["candidate"] != intent["candidate_sha"]
            or evidence["base"] != intent["base_sha"] or evidence["result"] != "pass"):
        raise RuntimeError("invalid sealed fixture evidence")
    if state["verdict"] is not None:
        return 0
    tips = current_tips(intent)
    if tips != {"head": intent["candidate_sha"], "base": intent["base_sha"]}:
        return finish(db, intent, "blocked", "Git ref drift detected")
    if state["submissions"] and strategy == "readback":
        return resolve_lookup(db, intent, "tuple lookup and canonical read")
    if state["receipt"] and strategy in {"checkpoint", "fail-stop"}:
        return verify_and_finish(db, intent, state["receipt"], "durable receipt and canonical read")
    if state["submissions"] and strategy == "fail-stop":
        return finish(db, intent, "unknown", "ambiguous submission requires manual reconciliation")
    return publish(db, state, relay, strategy)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--strategy", choices=STRATEGIES, required=True)
    parser.add_argument("--relay", required=True)
    args = parser.parse_args()
    with sqlite3.connect(f"{args.ledger.resolve().as_uri()}?mode=rw", uri=True) as db:
        db.execute("PRAGMA synchronous = FULL")
        return attempt(db, args.strategy, args.relay)


if __name__ == "__main__":
    sys.exit(main())
