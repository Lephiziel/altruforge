# P0.1 remote-oracle audit

## Finding

P0.1's `observer` values are read from Forgejo API responses, not copied from strategy return values or completion labels:

- `branch_sha()` calls `GET /repos/{owner}/{repo}/branches/{branch}` and extracts the returned commit SHA.
- `find_pulls()` calls `GET /repos/{owner}/{repo}/pulls?state=all&head=...&base=...`; exactness then checks returned head/base fields. `exact_pull()` additionally checks candidate SHA and stable marker.
- After all trial actions, the runner calls those read functions again. It separately calls `GET /repos/{owner}/{repo}/statuses/{candidate_sha}` and the base SHA endpoint; status attribution is derived from the returned status objects.
- `observer` includes HTTP status and the observed branch SHA, exact candidate PR count, and status attribution. The evaluator independently recomputes outcome categories from those recorded observer fields rather than trusting `outcome` or `eligible_resolution`.

Relevant implementation is in `pilot_forgejo.py`: `find_pulls` around line 122, `branch_sha` around line 140, final status reads around lines 529–545, and final observer construction around lines 574–586. The exact line numbers may move in later commits; inspect the named functions.

## Independence limits

The P0.1 observer is a direct provider read, but it runs in the same runner process, with the same instance and credential as orchestration. The evaluation script is separate and does not import the runner, but it evaluates serialized observer fields; it cannot detect a malicious or defective runner that fabricated those fields. The oracle is therefore **provider-backed but not independently captured**. The experiment also assumes Forgejo's API reads accurately represent current state. The one-version pilot did not test stale-read behavior.

S1-R2 addressed this capture-isolation limitation for its supplementary assignments: the observer ran as a separate process with a separate non-admin, read-only credential; it saved raw response bodies, digests, endpoints, timestamps, and errors, and its evaluator ignored driver completion labels. The observer and orchestrator still shared the same disposable Forgejo instance and loopback fault proxy, so this is process/credential separation rather than an independent provider or infrastructure trust domain. The original S1 assignment records remain blocked and unchanged.

The v1 and v2 P0.1 result files are retained unchanged; this audit does not rewrite their observations or upgrade them to an independent-observer claim.
