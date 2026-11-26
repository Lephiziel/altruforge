# S1-R2 infrastructure smoke v7

**Classification:** infrastructure-only; excluded from S1 and S1-R2 datasets  
**Source correction:** `c418e8fd9f8b44839fcf72e5925fa7dcbcd9fa19`  
**Provider:** Forgejo `17.0.2+gitea-1.22.0`, SQLite, loopback `127.0.0.1:30308`  
**Private smoke output:** `/tmp/nir03-s1r2-infrastructure-smoke-v7/output/`  
**Private raw observer bodies:** `/tmp/nir03-s1r2-infrastructure-smoke-v7/output/captures/`

The output directory used mode 0700; token files used mode 0600. The driver and observer used separate credentials. `s1-observer` was a non-admin collaborator with repository read permission and a `read:repository,read:user` token.

## Verified smoke paths

- Created private synthetic repositories and pushed a deterministic base commit to `main` and candidate commit to `feature`. Provider responses confirmed both exact SHAs; the setup recorded branch API visibility checks before proceeding.
- Started three separate recovery workers and synchronized on `after_first_remote_read`, `after_first_missing_effect_dispatch`, and `before_final_durable_classification`. The parent confirmed each worker exited with SIGKILL (`-9`), then resumed recovery.
- Recovery independently observed the candidate ref, one exact PR, and the exact status receipt.
- The observer received HTTP 503 for the injected PR-list GET, retained the raw response and digest, then observed restored successful responses in the terminal pass.
- In a separate smoke repository, the proxy forwarded PR creation to Forgejo and dropped the acknowledgement. The upstream response was HTTP 201, the client saw `RemoteDisconnected`, and later independent observation found exactly one PR and the exact status.
- The independent evaluator used observer captures, not runner labels. Both smoke fixtures were classified `complete`, each with exact PR count 1 and exact status count 1. `all_expected_present=true` for the two explicitly enumerated smoke labels.

Regression tests:

```sh
python3 -m unittest discover -s research/nir-03/supplementary/tests -v
```

Observed: 3 tests passed. Python syntax compilation also passed for `runner.py`, `observer.py`, `evaluation.py`, `git_env.py`, and `infrastructure_smoke.py`.

## Evidence files and hashes

- `results.json` SHA-256: `f48976f0204468000283b00853b63be28a94a8d04abc2bfc71d9f620e1a370fc`
- `evaluation.json` SHA-256: `c78590e408a8c557991b5e4d2cfe2521f7b858109ff080096e942792ef8e7a16`
- `smoke-summary.json` SHA-256: `711be3f5332fd8a06264c11d6a3edb5375c5f9a45ff6822277e47766a097c1a3`
- `raw-capture-index.json` SHA-256: `3becf48fa210fd4d5776ccc34f8e17dbd0b2d12e3c2fccb208f0195549ec3be2`
- Forgejo process log SHA-256: `25331031d1360137755495e1a18f6e7d1e9c8e20b93b973f90fcdfeaec862811`

The index lists each private raw body filename, byte length, and SHA-256. The captures include observation endpoint identities, timestamps, HTTP statuses, and body digests. No credentials are included.

## Earlier failed smoke iterations

Earlier smoke-only attempts are preserved under `/tmp` and were excluded from the registered dataset:

| Attempt | Observed failure | Correction covered by final smoke |
| --- | --- | --- |
| v1–v3 | Immediate Forgejo branch API read returned 404 after Git push although the bare repository held the expected refs; a later read returned the refs | Bounded, recorded branch visibility polling with exact SHA assertion |
| v1 source audit | Local `main` had advanced to candidate before the remote main push | Push the frozen base SHA directly to provider `main` |
| v4–v5 | Status matching failed because the API returns the success field as `status` and status-list rows omit the SHA | Match returned status/context/description and bind the SHA to the recorded `/statuses/{sha}` request path |
| v6 | End-to-end smoke passed before the final structured worker-event and response-digest record changes | v7 reran the complete smoke after those changes |

The failed smoke attempts indicate infrastructure defects only; they are neither registered observations nor excluded S1-R2 trials.
