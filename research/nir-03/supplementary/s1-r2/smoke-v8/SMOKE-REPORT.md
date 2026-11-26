# S1-R2 infrastructure smoke v8

**Classification:** infrastructure-only, excluded from registered trial data  
**Correction commit:** `c418e8fd9f8b44839fcf72e5925fa7dcbcd9fa19`  
**Smoke harness commit:** `f98706510813790fff5dd3247b7bbd8a8fa3d22f`  
**Provider:** Forgejo `17.0.2+gitea-1.22.0`, SQLite, loopback `127.0.0.1:30309`  
**Private instance:** `/tmp/nir03-s1r2-smoke-forgejo-v8/`  
**Private run output:** `/tmp/nir03-s1r2-infrastructure-smoke-v8/output/`  
**Private raw captures:** `/tmp/nir03-s1r2-infrastructure-smoke-v8/output/captures/`

The instance was created from the verified Forgejo 17.0.2 binary with `research/nir-03/prepare_forgejo.sh`. Credentials were mode 0600 outside Git. The independent observer was a separate non-admin account with `read:repository,read:user` token scope and repository read permission (collaborator grant HTTP 204).

## Exact smoke invocation

```sh
python3 research/nir-03/supplementary/infrastructure_smoke.py \
  --base-url http://127.0.0.1:30309 \
  --owner-token-file /tmp/nir03-s1r2-smoke-forgejo-v8/api-token \
  --observer-token-file /tmp/nir03-s1r2-smoke-forgejo-v8/observer-token \
  --output-dir /tmp/nir03-s1r2-infrastructure-smoke-v8/output
```

The smoke creates three private, uniquely labeled fixtures in a fresh disposable instance. It does not use the S1 or S1-R2 assignment labels, result directory, or repositories.

## Results

The independent evaluator reported all three expected smoke labels and derived:

| Smoke path | Independent terminal classification | Exact PRs | Exact statuses |
| --- | --- | ---: | ---: |
| R5 repeated recovery interruption | `complete` | 1 | 1 |
| R4 forwarded create with dropped acknowledgement | `complete` | 1 | 1 |
| R1 no publication effect, branch read failure then restore | `not_executed` | 0 | 0 |

R5 synchronized each worker after the first remote read, after the missing-effect dispatch, and before final durable classification. Each event included provider response metadata; the parent confirmed each child terminated with SIGKILL (`-9`). Recovery then observed the candidate ref and exactly one PR.

R4's reverse proxy recorded upstream HTTP 201 and the SHA-256/length of the upstream response before dropping the acknowledgement. The client saw `RemoteDisconnected`. The independent observer later read one exact PR and the exact status.

R1's independent observer captured HTTP 503 for the branch GET, followed by successful restored reads: branch at the base SHA, empty PR list, and empty candidate-status list. The final independent classification was `not_executed`.

The observer raw bodies were saved with mode 0600, and their containing directory with mode 0700. They include timestamps, endpoint identities, HTTP statuses, raw-body digests, and returned identity fields. The checked-in [`raw-capture-index.json`](raw-capture-index.json) records each filename, size, and SHA-256; the raw bodies stay in the private `/tmp` path above.

## Regression verification

```sh
python3 -m unittest discover -s research/nir-03/supplementary/tests -v
python3 -m py_compile \
  research/nir-03/supplementary/runner.py \
  research/nir-03/supplementary/observer.py \
  research/nir-03/supplementary/evaluation.py \
  research/nir-03/supplementary/git_env.py \
  research/nir-03/supplementary/infrastructure_smoke.py
```

Observed before the smoke: all 3 Git environment regression tests passed; Python syntax compilation and `git diff --check` passed.

## Artifact digests

- `results.json`: `d4c9e47bfde69a062bfc69e3e65ab403b7d9a30b8e9cfda3bd24584af7491256`
- `evaluation.json`: `699520ce5f7ddb37562feefc2965e22be5d8d700d459b0bad9efd46bbfdc2c5b`
- `smoke-summary.json`: `2abbdd1276de94c38efd496205f140c0a2621321bc30fac0a56dbfcf6cc12937`
- `raw-capture-index.json`: `d4e48e4ff443247a83199bad73e70509aa7a47b84a889f2d1132da2f6a62f4b5`
- Forgejo process log: `d49f9949ad81c1f4d24d4e7d6c68900c13612a1c6e68a56e80bb0379630a3be8`

The smoke establishes readiness only for the checked paths on this Forgejo build. It is not an S1-R2 trial and contributes no scientific outcome.
