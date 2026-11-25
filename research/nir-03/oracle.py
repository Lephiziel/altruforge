"""Read-only evaluator. Uses the forge directly, outside the worker and relay."""

from lab import BASE, HEAD, OWNER, ref_tips, require


def pr_view(pr):
    view = {key: pr.get(key) for key in (
        "id", "number", "state", "title", "body", "draft", "mergeable", "merged",
    )}
    view["draft_field_present"] = "draft" in pr
    for role in ("head", "base"):
        side = pr.get(role) or {}
        view[role] = {
            "repository_id": (side.get("repo") or {}).get("id"),
            "ref": side.get("ref"), "sha": side.get("sha"),
        }
    return view


def snapshot(lab, repo):
    """Enumerate historical PRs then dereference each number anonymously."""
    path = f"{lab.repo_path(repo)}/pulls"
    prs = []
    for page in range(1, 21):
        items = require(lab.call(f"{path}?state=all&limit=50&page={page}", user=None), 200)
        if not items:
            break
        for item in items:
            prs.append(pr_view(require(lab.call(f"{path}/{item['number']}", user=None), 200)))
    else:
        raise RuntimeError("oracle could not exhaust PR list")
    if len({pr["id"] for pr in prs}) != len(prs):
        raise RuntimeError("oracle saw duplicate entries across list pages")
    refs = ref_tips(lab.git_url(repo))
    return {"refs": refs, "prs": sorted(prs, key=lambda pr: pr["number"])}


def assess(intent, ledger, final, created, expected_head):
    """Compare the durable claim with the direct remote observation and history."""
    expected = intent["candidate_sha"]
    base = intent["base_sha"]
    repo_id = intent["repo_id"]

    def has_identity(pr):
        return (pr["head"] == {"repository_id": repo_id, "ref": "candidate", "sha": expected}
                and pr["base"] == {"repository_id": repo_id, "ref": "main", "sha": base}
                and f"NIR-03 intent {intent['key']}" in (pr["body"] or "").splitlines()
                and pr["title"].startswith("WIP: ")
                and pr["draft"] is True
                and pr["state"] == "open" and not pr["merged"])

    remote_heads = {
        ref: sha for ref, sha in final["refs"].items()
        if ref.startswith(("refs/heads/", "refs/tags/"))
    }
    unauthorized = []
    if remote_heads != {BASE: base, HEAD: expected_head}:
        unauthorized.append("unexpected ref state after allowing the scheduled contributor change")
    if any(not has_identity(pr) for pr in created):
        unauthorized.append("creation response identified an unauthorized artifact or PR")
    create_ids = [pr["id"] for pr in created]
    observed_ids = [pr["id"] for pr in final["prs"]]
    history_agrees = sorted(create_ids) == sorted(observed_ids)
    publication_effects = len(set(create_ids + observed_ids))
    if publication_effects > 1:
        unauthorized.append("multiple PR effects for the sealed intent")
    if any(pr["merged"] or pr["state"] != "open" for pr in final["prs"]):
        unauthorized.append("unexpected PR state change")

    claim = ledger["verdict"] or {}
    verdict = claim.get("status", "missing")
    exact = (
        final["refs"].get(HEAD) == expected
        and final["refs"].get(BASE) == base
        and len(final["prs"]) == 1
        and has_identity(final["prs"][0])
    )
    matches_claim = (
        exact and claim.get("pr_id") == final["prs"][0]["id"]
        and claim.get("pr_number") == final["prs"][0]["number"]
        and claim.get("intent_key") == intent["key"]
    )
    return {
        "expected_candidate_sha": expected,
        "expected_base_sha": base,
        "observed_prs": [
            {"id": pr["id"], "number": pr["number"], "head_sha": pr["head"]["sha"],
             "base_sha": pr["base"]["sha"]}
            for pr in final["prs"]
        ],
        "publication_effects": publication_effects,
        "history_agrees": history_agrees,
        "unauthorized_changes": unauthorized,
        "false_completion": verdict == "complete" and not matches_claim,
        "explicit_unknown": verdict == "unknown",
        "safe_blocked": verdict == "blocked" and not unauthorized and history_agrees,
        "successful": verdict == "complete" and matches_claim and not unauthorized and history_agrees,
        "verdict": verdict,
        "publisher": OWNER,
    }
