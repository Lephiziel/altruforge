# NIR-03 supplementary replication amendment S1-R2

**Status:** preregistered before S1-R2 outcome collection  
**Parent branch state:** `7b7dd1408a8fbddea3fb1d0ec9db7e699e420ede`  
**Infrastructure correction commit:** `c418e8fd9f8b44839fcf72e5925fa7dcbcd9fa19`  
**Final smoke harness commit:** `f98706510813790fff5dd3247b7bbd8a8fa3d22f`  
**Original S1 protocol:** [`PREREGISTRATION.md`](PREREGISTRATION.md), preserved unchanged  
**Replication ID:** `S1-R2`  
**S1-R2 assignment labels:** `nir03-s1-r2-R<n>-<policy>`

This amendment was drafted after the original S1 setup failure and the separate infrastructure smoke suite passed. It must be committed before the S1-R2 assignment matrix is run. Smoke records are infrastructure evidence and are excluded from the S1-R2 dataset. S1-R2 remains one descriptive 14-cell replication; it is not a replacement of S1 and is not a second collection of the same registered outcomes.

## Reason for a separate replication

The original S1 run attempted every assigned cell, but all 14 failed before fixture push because the frozen runner set `GIT_CONFIG_COUNT=2` while supplying only `GIT_CONFIG_KEY_0` and `GIT_CONFIG_VALUE_0`. Git requires a contiguous key/value pair for every index from zero through count minus one and stopped with `missing config key GIT_CONFIG_KEY_1`. The original `results.json` and evaluator remain unchanged. Those cells remain blocked and are not replaced or relabeled as S1-R2 outcomes.

## Infrastructure defect, audit, and correction

The frozen `runner.py` at `8a5d27c477421aeb1786e1f2b1abb4872738f066` built the fixture subprocess environment from the parent environment, then assigned `GIT_CONFIG_COUNT=2` with only one indexed entry. Copying the parent also allowed inherited `GIT_CONFIG_*`, `GIT_DIR`, and other Git controls to leak into fixture commands.

The correction in `git_env.py` creates an allowlisted environment and sets exactly one complete entry:

```text
GIT_CONFIG_COUNT=1
GIT_CONFIG_KEY_0=http.extraheader
GIT_CONFIG_VALUE_0=Authorization: token <temporary owner token>
```

The full reviewed correction diff is the durable Git change `c418e8f` (parent `7b7dd1408a8fbddea3fb1d0ec9db7e699e420ede`); reproduce it with `git show --format=fuller --find-renames c418e8fd9f8b44839fcf72e5925fa7dcbcd9fa19`. The central replacement is:

```diff
-env = os.environ.copy(); env.update({...})
+env = build_git_environment(token=token, token_file=tokenfile,
+                            askpass=ask, home=root)
...
-env['GIT_CONFIG_COUNT']='2'; env['GIT_CONFIG_KEY_0']='http.extraheader'; ...
+# exactly one complete indexed pair is constructed by git_env.py
```

`git_env.py` also explicitly sets `GIT_CONFIG_COUNT` from one complete key/value pair and excludes inherited Git controls. The commit adds regression tests and the separate smoke harness; the smoke harness itself is not part of the registered dataset.

It also fixes and audits two related fixture/observation defects found during the smoke sequence:

1. After the candidate commit, local `main` points at the candidate. The old push command therefore could publish that moving local ref as provider `main`. The corrected runner pushes the captured `base_sha` directly to `refs/heads/main`, and puts the candidate on `feature` (the base on `feature` for R1, and the competing SHA for R6).
2. Forgejo can return a transient branch API 404 immediately after a successful Git HTTP push while the ref is already present. The corrected setup polls that branch endpoint for at most 15 seconds, records each status/SHA/timestamp, and requires the returned SHA to equal the frozen fixture identity before proceeding.
3. Forgejo status list entries omit their target SHA and return state under `status`. The observer now records the requested SHA from the `/statuses/{sha}` endpoint and normalizes the returned state field. The scorer checks both the endpoint SHA and exact status context, description, and success value.
4. Intent and candidate ledger files are atomically persisted before the first Git push. Setup failures with no identity no longer trigger an invalid observer call. Git diagnostics redact the temporary token.
5. Worker and observer subprocesses use a clean Python environment. R5 barrier events carry the actual provider response status/body digest or recovery observations, while worker termination is still confirmed by the parent process.
6. Provider mutation responses and proxy-forwarded response digests, byte counts, endpoints, timestamps, injected errors, and lost-ack barriers are retained in the run record.

The regression suite is `tests/test_git_env.py`. It simulates hostile inherited Git configuration, asserts exactly one complete indexed setting and no inherited Git directory/config parameters, invokes Git with the constructed environment, and checks credential redaction.

## Scope and frozen scientific design

S1-R2 retains the original research question, two recovery policies, seven scenarios, one assignment per scenario-policy cell, recovery semantics, safety criteria, and observer-only evaluator rules from `PREREGISTRATION.md`. It makes no statistical comparison or general efficacy claim. Every one of the 14 cells is run once under this distinct replication ID. A setup or trial failure stays in its assigned cell; there are no replacement trials or selective repeats.

The only assignment identity change is the separate fixed prefix `nir03-s1-r2`, which prevents S1-R2 repository, run, PR, intent, and ledger identifiers from colliding with the retained S1 records. For each scenario `R<n>` and policy, the label and repository use the prefix plus the scenario and policy. Verification identity remains SHA-256 of `NIR03-S1-VERIFIED\n<label>\n<candidate-sha>\n`.

The smoke suite uses separate labels `nir03-s1r2-infra-smoke-*`, separate disposable repositories and Forgejo instances, a separately scoped observer credential, and a different output root. Its records are never included in the 14 S1-R2 assignments or evaluation denominator. The final v8 readiness run is summarized in [`smoke-v8/SMOKE-REPORT.md`](s1-r2/smoke-v8/SMOKE-REPORT.md). Earlier infrastructure-only attempts v1–v7 are retained outside the repository under `/tmp/nir03-s1r2-infrastructure-smoke*`; none contributes to the experiment. v1 had a failed branch verification whose precise cause was not isolated. v2–v3 observed transient branch-endpoint 404s after push before later reads returned the exact refs; this motivated bounded visibility polling. v4–v5 observed the created exact PR but scored zero exact statuses because the provider list shape exposes `status` and omits the target SHA; this motivated endpoint-identity normalization. v6–v7 passed the two-case smoke before the R1 no-effect path was added to the smoke harness. These attempts were infrastructure debugging only; no registered outcome was observed or used to alter the research question, policies, scenarios, or evaluation criteria.

## Smoke outcome and separation

The accepted final smoke is [`smoke-v8`](s1-r2/smoke-v8/SMOKE-REPORT.md). It used Forgejo 17.0.2 on loopback and three private smoke repositories. It checked repository creation, exact base/candidate refs, branch visibility polling, the separate observer's read access, status and PR identity, all three R5 synchronization barriers and confirmed SIGKILLs, recovery, an injected observer 503 followed by restored responses, a forwarded PR create with its HTTP 201 acknowledgement dropped, the R1 no-effect path resolving to `not_executed`, raw response digests, and independent evaluation. The R4 and R5 cases scored `complete` with one exact PR and status each; the R1 case scored `not_executed` with no PR or status. The raw bodies remain in a mode-0700 `/tmp` directory; a checked-in index records file digests and sizes.

Several earlier smoke iterations failed on infrastructure defects and are retained outside the research dataset under `/tmp/nir03-s1r2-infrastructure-smoke*`. These are not trial outcomes. The final passing smoke is the sole infrastructure readiness decision.

## S1-R2 execution procedure

Use a fresh empty Forgejo state path and unused loopback port. Prepare Forgejo using `research/nir-03/prepare_forgejo.sh`, then create the separate non-admin observer user and scoped token exactly as in the smoke setup. Keep all tokens, state, raw captures, and run output under a new mode-0700 `/tmp` directory. Confirm the Forgejo version through the authenticated API before running.

Run the fixed matrix exactly once:

```sh
RUN=/tmp/nir03-s1-r2-run-<unique-id>
mkdir -m 700 "$RUN"
python3 research/nir-03/supplementary/runner.py \
  --base-url http://127.0.0.1:<port> \
  --owner-token-file "$STATE/api-token" \
  --observer-token-file "$STATE/observer-token" \
  --capture-dir "$RUN/captures" \
  --output "$RUN/results.json" \
  --experiment-id S1-R2 \
  --protocol research/nir-03/supplementary/S1-R2-AMENDMENT.md \
  --label-prefix nir03-s1-r2 \
  --repo-prefix nir03-s1-r2
python3 research/nir-03/supplementary/evaluation.py \
  "$RUN/results.json" \
  --matrix-prefix nir03-s1-r2 \
  --output "$RUN/evaluation.json"
```

Do not invoke the registered runner until this amendment and the infrastructure correction have been committed. On completion, copy the non-secret results and evaluator JSON into `supplementary/s1-r2/`, keep raw observer bodies private under the recorded capture directory, and add a digest index. If a cell fails, preserve it in place and stop; do not restart that cell.

## Acceptance boundary

The smoke pass establishes that the implemented setup and evidence path functioned for three smoke paths (R5 repeated interruption, R4 ambiguous create, R1 no effect) on this Forgejo build. It does not establish S1-R2 scientific results, statistical performance, production readiness, or universal exactly-once behavior. Those conclusions remain unavailable until the independently scored 14-cell replication completes. No production Harness or Altruforge runtime state is involved; merge and auto-merge remain disabled.
