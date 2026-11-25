"""Forgejo endpoint probes on a repository reserved for characterization."""

from concurrent.futures import ThreadPoolExecutor
import threading
import time

from lab import ACTOR, BASE, HEAD, OWNER, git_result, ref_tips, request, require
from oracle import pr_view, snapshot


def characterize(lab, fixture, journal):
    repo = "contract"
    repo_id = lab.create_repo(repo)
    path = f"{lab.repo_path(repo)}/pulls"
    url = lab.git_url(repo)
    started = time.monotonic_ns()

    def record(probe, **fields):
        journal.record("contract", probe=probe, repo_id=repo_id, **fields)

    def push(probe, sha, ref, *options, actor=False):
        source = fixture.actor_source if actor else fixture.source
        user = ACTOR if actor else OWNER
        result = lab.push(repo, source, sha, ref, *options, user=user)
        record(probe, actor=user, target=ref, git=git_result(result))
        return result

    for ref in (
        BASE, HEAD, "refs/heads/field", "refs/heads/race",
        "refs/heads/post-race", "refs/heads/post-same", "refs/heads/move",
    ):
        sha = fixture.base if ref == BASE else fixture.candidate
        push("seed", sha, ref, f"--force-with-lease={ref}:").check_returncode()

    def post(probe, branch, title, note, **extra):
        data = {"head": branch, "base": "main", "title": title, "body": note, **extra}
        status, body = lab.call(path, "POST", data)
        record(probe, request=data, status=status, response=pr_view(body) if status == 201 else body)
        return status, body

    def get(pr):
        return pr_view(require(lab.call(f"{path}/{pr['number']}", user=None), 200))

    def ui(pr):
        status, html = request(lab.origin, f"/{OWNER}/{repo}/pulls/{pr['number']}")
        return {"status": status, "wip_notice": b"marked as a work in progress" in html,
                "draft_icon": b"octicon-git-pull-request-draft" in html}

    spec = require(lab.call("/swagger.v1.json", user=None), 200)
    properties = spec["definitions"]["CreatePullRequestOption"]["properties"]
    record("create_schema", fields=sorted(properties))
    first = require(post("wip_post", "candidate", "WIP: Verified artifact", "probe intent A"), 201)
    acknowledged = time.monotonic_ns()
    immediately = snapshot(lab, repo)
    record("read_after_write", elapsed_ms=round((time.monotonic_ns() - acknowledged) / 1e6, 3),
           view=immediately)
    record("wip_ui", pr=get(first), ui=ui(first))
    post("same_post", "candidate", first["title"], first["body"])
    post("same_tuple_different_marker", "candidate", "WIP: Another operation", "probe intent B")
    field = post("draft_field_post", "field", "Plain title", "field alone", draft=True)
    if field[0] == 201:
        record("draft_field_ui", pr=get(field[1]), ui=ui(field[1]))

    closed = lab.call(f"{path}/{first['number']}", "PATCH", {"state": "closed"})
    record("close_first", status=closed[0], response=pr_view(closed[1]) if closed[0] in (200, 201) else closed[1])
    post("same_tuple_after_close", "candidate", first["title"], first["body"])
    record("history_after_close", view=snapshot(lab, repo))
    push("advance_candidate", fixture.drift_a, HEAD, actor=True).check_returncode()
    record("history_after_candidate_advance", view=snapshot(lab, repo))

    race_ref = "refs/heads/race"
    start = threading.Barrier(2, timeout=12)

    def race_push(label, sha, actor):
        tips = ref_tips(url)
        record("race_preflight", caller=label, observed_sha=tips.get(race_ref))
        start.wait()
        return push(label, sha, race_ref, actor=actor)

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(race_push, "race_push_a", fixture.drift_a, False)
        b = pool.submit(race_push, "race_push_b", fixture.drift_b, True)
        results = [a.result().returncode, b.result().returncode]
    winner = ref_tips(url).get(race_ref)
    record("race_result", exit_codes=results, winning_sha=winner)
    other = fixture.drift_b if winner == fixture.drift_a else fixture.drift_a
    push("ordinary_non_ff", other, race_ref)
    push("stale_explicit_lease", other, race_ref, f"--force-with-lease={race_ref}:{fixture.candidate}")
    record("after_rejected_updates", observed_sha=ref_tips(url).get(race_ref))
    ref = "refs/heads/field"
    push("matching_explicit_lease", fixture.drift_b, ref, f"--force-with-lease={ref}:{fixture.candidate}")
    record("after_matching_lease", observed_sha=ref_tips(url).get(ref))

    def race_posts(branch, same_intent):
        create_barrier = threading.Barrier(2, timeout=12)

        def concurrent_create(caller):
            note = "same publication intent" if same_intent else caller
            create_barrier.wait()
            return post("concurrent_post", branch, "WIP: Concurrent create", note)[0]

        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = list(pool.map(concurrent_create, ("caller A", "caller B")))
        record("post_race_result", branch=branch, same_intent=same_intent, statuses=statuses,
               view=snapshot(lab, repo))

    race_posts("post-race", same_intent=False)
    race_posts("post-same", same_intent=True)

    move_ref = "refs/heads/move"
    record("check_before_post", head=ref_tips(url).get(move_ref), expected_candidate=fixture.candidate)
    push("contributor_between_check_and_post", fixture.drift_a, move_ref, actor=True).check_returncode()
    moved = post("post_after_check_and_move", "move", "WIP: Check-to-create gap",
                 f"Verified candidate {fixture.candidate}")
    if moved[0] == 201:
        record("check_to_create_result", expected_candidate=fixture.candidate, pr=get(moved[1]),
               actual_tip=ref_tips(url).get(move_ref))
    record("contract_finished", elapsed_ms=round((time.monotonic_ns() - started) / 1e6, 3),
           view=snapshot(lab, repo))
