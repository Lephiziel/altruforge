# S1 execution notes and acceptance audit

**Protocol:** `PREREGISTRATION.md` (unchanged; frozen before outcomes)  
**Frozen runner/observer/evaluator:** commit `8a5d27c477421aeb1786e1f2b1abb4872738f066`  
**Assigned run ID:** `nir03-s1-run-8a5d27c`  
**Result:** all 14 assignments are retained as setup-blocked; no S1 fault treatment ran.

The artifacts were pushed to the existing `research/nir-03-p01` PR branch at commit `9ce2fec79381507e8476c08fc15450425cc56c7d`. The push succeeded. A separate GitHub PR metadata query was unavailable due a network connection error; no merge operation was issued.

## Environment and exact execution

The experiment used a fresh SQLite Forgejo `17.0.2+gitea-1.22.0` instance, created with `research/nir-03/prepare_forgejo.sh`, bound to `127.0.0.1:30301`. The active older disposable P0.1 instance already occupied port 30300 and was left untouched. The instance has a separate non-admin `s1-observer` account with a `read:repository,read:user` token. The driver token is separate. Both tokens and instance state remain outside the checkout under `/tmp/nir03-s1-forgejo-30301`; their values are not part of these artifacts.

The frozen execution command was:

```sh
python3 research/nir-03/supplementary/runner.py \
  --base-url http://127.0.0.1:30301 \
  --owner-token-file /tmp/nir03-s1-forgejo-30301/api-token \
  --observer-token-file /tmp/nir03-s1-forgejo-30301/observer-token \
  --capture-dir /tmp/nir03-s1-run-8a5d27c/captures \
  --output /tmp/nir03-s1-run-8a5d27c/results.json
```

The disposable server was started from the signed Forgejo binary using the generated configuration at `/tmp/nir03-s1-forgejo-30301/custom/conf/app.ini`. Forgejo was authenticated and version-checked before the runner started.

## Observed result

The frozen runner enumerated all 14 preregistered cells. In each cell it created the private repository, then failed while configuring the Git subprocess for fixture push. The runner itself sets `GIT_CONFIG_COUNT=2` but supplies only `GIT_CONFIG_KEY_0`/`GIT_CONFIG_VALUE_0`; Git exits with `missing config key GIT_CONFIG_KEY_1`. The generated fixture and candidate were not pushed, no pre-dispatch manifest was written, and no fault rule, publication mutation, recovery attempt, observer request, or R5 worker interruption occurred. The 14 empty setup repositories are retained in the disposable instance. Every cell is recorded as `blocked` in `results.json`.

No observer body captures exist (zero files in the private capture directory); therefore no remote outcome is inferred. The independent evaluator reports all 14 cells as `unobserved`. It does not convert missing evidence to conflict, absence, or completion. The evaluator also ignores all driver classification labels.

This is a failed setup run, not evidence for or against the preregistered question. The preregistration explicitly requires retaining setup failures and forbids replacing a failed cell with a fresh successful run. Accordingly, no cell was retried after this failure. A corrected runner would require an explicitly amended and separately identified run under the protocol's amendment rule; it cannot be described as completion of this S1 run.

## Preserved artifacts and reproducibility

- `results.json` contains the complete 14-cell assignment record and setup error for every cell. Its original run copy is `/tmp/nir03-s1-run-8a5d27c/results.json`.
- SHA-256 `results.json`: `6eb6d523f04536840c5bde693f032744c3bd0965d50f1e53974456c4c671bc2e`.
- `evaluation.json` is the independent evaluation of that result artifact. Reproduce it with:

  ```sh
  python3 research/nir-03/supplementary/evaluation.py \
    research/nir-03/supplementary/results.json \
    --output research/nir-03/supplementary/evaluation.json
  ```

- SHA-256 `evaluation.json`: `0ad1f2ca3079474e184082c0dc7d6ae1be0eabce57dc78d18255dc61937644c8`.

- Raw observer captures: none were produced. The private capture directory is `/tmp/nir03-s1-run-8a5d27c/captures`.
- The Forgejo process log and isolated SQLite state remain under `/tmp/nir03-s1-run-8a5d27c/forgejo.log` and `/tmp/nir03-s1-forgejo-30301/` respectively; these are setup evidence, not trial observation evidence.
- The original P0.1 25-trial matrix, formal model, TLC outputs, and preregistration were not edited by this run.

## Deviations and limitations

The only observed protocol deviation is that the frozen implementation failed before fixture publication. As a result, the requested conditions—independent remote observations, injected 503s, lost acknowledgement, repeated recovery interruption, unknown ledger transitions, endpoint-specific read failures, and independent trial scoring—were not exercised. No claims about those behaviors are warranted. The planned runner records tool versions, identities, and response evidence for successful setup, but this run could not record candidate identities because fixture push failed. The observer was not invoked, so its independence and read authorization were not experimentally validated in this run.

The run made no merge, enabled no auto-merge, and touched no production Harness or Altruforge runtime state. It did create only the 14 disposable private S1 setup repositories described above.

## NIR-03 S1 acceptance audit

| Requirement | Result |
| --- | --- |
| Frozen 14-cell assignment list represented | Pass: all 14 labels are present |
| Assignment execution retained without replacement | Pass: all 14 setup failures remain in the denominator |
| Exact deterministic fixture and manifest | Fail: fixture push failed before the manifest could be written |
| Independent observer with separate read-only credential | Not established: observer process was not reached |
| Raw provider responses, digests, endpoint IDs, timestamps, failures | Fail: no observer requests/captures occurred |
| Repeated recovery interruptions with synchronized barriers | Fail: no worker started |
| Ambiguous remote effect and unavailable observations | Fail: no fault treatments occurred |
| Explicit candidate-ledger unknown classification | Fail: no manifest/ledger was written |
| Independent evaluation without driver labels | Pass for setup outcome only: evaluator uses captures only and returns `unobserved` |
| Preserve failures, blocked and unknown outcomes | Pass: all 14 cells preserved as blocked; no unknown trial classification is fabricated |
| Protocol deviations, commands, reproducibility, limitations documented | Pass |
| P0.1 matrix and formal artifacts unchanged | Pass: no edits made to retained artifacts |
| Update PR #29, do not merge | Pass: artifacts pushed to its existing branch; no merge operation issued |

**Overall:** NIR-03 S1 acceptance does not pass. The experiment stopped at the preregistered setup-failure boundary; a fresh successful rerun would be a separately identified amended run, not a replacement for these 14 blocked assignments.
