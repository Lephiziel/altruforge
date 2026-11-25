# P0.1 results and limitations

The retained exploratory run completed all 35 assigned trials. The two policies that reconciled observed PR identity recovered all five eligible fault scenarios each. In separate contract probes the forge admitted duplicate concurrent requests and accepted a PR after its head advanced past the verified commit.

## Environment and recorded commands

The run took place on 25 November 2026 in a non-root Debian 13 Linux amd64 environment, kernel 6.18.57, Git 2.56.1, Python 3.12.14 and Python SQLite 3.53.1. Forgejo reported `15.0.12+gitea-1.22.0`, release 15.0.12 with bundled SQLite. TLC 2.19 from TLA+ tools v1.7.4 ran with OpenJDK 21.0.13.1. The binary checksums and portable commands are in the [replication guide](REPLICATION.md).

The two Forgejo commands ran from the repository root.

`bash
PYTHONDONTWRITEBYTECODE=1 python3 research/nir-03/run.py \
  --forgejo ../nir03-tools/forgejo-15.0.12-linux-amd64 --out ../nir03-tools/matrix-initial
PYTHONDONTWRITEBYTECODE=1 python3 research/nir-03/run.py \
  --forgejo ../nir03-tools/forgejo-15.0.12-linux-amd64 --out ../nir03-tools/matrix-final
`

The final model checks ran from `research/nir-03/model`.

`bash
for profile in guarded stable mutable-refs blind-replay; do
  status=0
  java -XX:+UseParallelGC -jar ../../../../nir03-tools/tla2tools-1.7.4.jar -workers 1 \
    -metadir "../../../../nir03-tools/tlc-final-$profile" -config "$profile.cfg" Publication.tla \
    > "../records/tlc-$profile.txt" 2>&1 || status=$?
  printf '%s %s\n' "$profile" "$status"
done
`

## TLA+ model checking

| Profile | TLC exit | Generated / distinct / queued | Outcome |
| --- | ---: | ---: | --- |
| Guarded with drift | 0 | 762 / 321 / 0 | All configured safety invariants passed with atomic ref guards and serialized open-PR uniqueness. [TLC log](records/tlc-guarded.txt) |
| Stable with fairness | 0 | 94 / 56 / 0 | Safety and `EventuallyComplete` passed under stable refs and weak fairness. [TLC log](records/tlc-stable.txt) |
| Mutable refs | 12 | 85 / 56 / 21 | `VerifiedAtCreation` failed. A contributor advanced the head after dispatch, and the unguarded forge settled the create at the new head. [Counterexample](records/tlc-mutable-refs.txt) |
| Blind replay | 12 | 33 / 26 / 5 | `AtMostOneEffect` failed. With no uniqueness check, two sequential submissions settled into two effects before completion was observed. [Counterexample](records/tlc-blind-replay.txt) |

The counterexamples stop at a violation, so their state counts describe partial searches. The checks cover the [bounded model](SPECIFICATION.md#model-scope) under each profile's assumptions. The model's guard and uniqueness assumptions need their own evidence when applied to a forge.

## Forgejo contract observations

| Probe | Observed on this configuration |
| --- | --- |
| Sequential duplicate | An identical repeat and a repeat with a different body marker each returned HTTP 409 while PR #1 was open. The conflict identified the existing branch tuple in its message |
| Concurrent create | Both requests returned HTTP 201 in each final probe. Separate GETs showed open PRs #4 and #5 for the same tuple with different body markers, and #6 and #7 for the same tuple with identical request bodies. The setup run also produced two 201 responses for a concurrent pair with different markers |
| Lifetime identity | Closing #1 by PATCH returned 201. Repeating its original create produced #3 with a distinct ID. An all-state list and per-number lookup returned both #1 and #3 |
| Git ref writes | Each of two contenders read the same candidate tip before the barrier. One ordinary push succeeded and the competing update was rejected. Ordinary non-fast-forward and stale explicit-lease attempts both left the winner in place. An explicit matching lease permitted a separate fast-forward |
| Visibility | The first independent list and per-number GET after a create response saw the PR. The combined Git and API snapshot completed 74 ms after acknowledgment in the final probe. During repository seeding, PR listing sometimes returned 404 after successful Git pushes. The final run logged 264 such pretrial reads before all 35 repositories became readable |
| Draft | A default `WIP:` prefix yielded `draft: true`, `mergeable: false` and an independent HTML draft indicator. A plain title with a `draft: true` create field yielded `draft: false` and the UI showed a normal PR. The instance's create schema omitted that input field |
| Moving candidate identity | After an authorized fast-forward, canonical reads for both the closed and open PR on that branch reported the new head while their IDs stayed fixed. In a separate check-to-create probe, Forgejo accepted 201 with the new head even though the body named the old verified SHA |

In the check-to-create probe the verified candidate was `b4bf10066a447dfd14561ba190432bde1c01349f` and the PR head was `784214211019e05e05f0519d37e612fcc4afd6fe`. The observed base remained `8c704ef3698885d94d3bc8f21c44ac67eb0e0f4c`. These probes used ordinary authorized writes and the forge's native protections. The duplicate probe bounds the assumption of serialized open-PR uniqueness. The drift probe shows the gap between a successful check of a Git tip and subsequent PR creation.

## Recovery matrix

| Scenario | Retry | Checkpoint | Read-back | Fail-stop | Retry with reconciliation |
| --- | --- | --- | --- | --- | --- |
| Control | Complete | Complete | Complete | Complete | Complete |
| Kill before create | Complete | Complete | Complete | Complete | Complete |
| Kill after create | Unknown | Unknown | Complete | Unknown | Complete |
| Drop response | Unknown | Unknown | Complete | Unknown | Complete |
| Drift before recovery | Blocked | Blocked | Blocked | Blocked | Blocked |
| Kill while recovering | Unknown | Unknown | Complete | Unknown | Complete |
| Kill after receipt | Unknown | Complete | Complete | Complete | Complete |

The 35 final trials produced 20 verified completions, 10 explicit unknowns, and five safe blocks. The control completed in all five policies. Among the 25 eligible recovery cases, 15 completed. The five drift cases were ineligible and blocked after the authorized change. Every final trial had one PR creation effect and agreement between the relay history and the direct oracle. At the recorded cutoffs there were zero false completions and zero unauthorized changes in this single-worker matrix. The concurrent duplicates and wrong-artifact creation in the contract probes belong to separate histories.

The controller verified 30 worker SIGKILL exits, five response drops with zero downstream response bytes, and five independently confirmed contributor pushes. The initial matrix had 14 setup failures after successful Git pushes and before a fault could be assigned. Those 14 trials were ungraded and the other 21 outcomes remain in the [initial outcomes](records/forgejo-initial-outcomes.json). The final runner waits up to five seconds at repository setup for the PR list to become readable. This changed the pretrial gate and did not add a visibility retry to the recovery policies.

| Policy | Verified recovery / eligible | Create requests across seven trials | Median successful recovery, ms |
| --- | ---: | ---: | ---: |
| Retry | 1 / 5 | 12 | 449 |
| Checkpoint | 2 / 5 | 11 | 366 |
| Read-back | 5 / 5 | 7 | 223 |
| Fail-stop | 2 / 5 | 7 | 381 |
| Retry with reconciliation | 5 / 5 | 12 | 451 |

Latency is descriptive with one observation per pairing. Recovery latency excludes initial fixture setup and the final oracle sample. The recovery request counts include native duplicate rejections. Policy decisions used the same forge contract.

## Limitations and next steps

The matrix isolates PR creation after candidate ref installation. It covers deterministic worker termination and one dropped acknowledgment on a loopback transport. It omits worker races, requests still in flight during recovery, transient absent reads after PR creation, power loss, database and forge restarts, fork permissions, and base drift. The two read-back policies exercised here resolve effects that are already visible. A missing or inaccessible effect is still ambiguous. Reads across Git and the forge require a stability window to establish one coherent observation.

One pinned Forgejo release on one host gives no basis for a GitHub guarantee, an estimate of how often a race occurs, or a claim of general superiority. The initial and final Forgejo processes overlapped during the first part of the final contract probes. Each used separate ports and storage. Host scheduling may influence which concurrent request wins.

For the next experiment, retain the two reconciliation baselines and freeze the scenario schedule and grading. First test late settlement, absent reads, ref-policy enforcement, and competing publishers with more repetitions. Compare an enforceable per-intent exclusion or immutable-ref policy under identical conditions. Characterize the GitHub fork/Draft PR contract separately before attaching these results to product acceptance.

## Execution records

- [Retained trace](records/forgejo-final-trace.jsonl.gz) and [per-trial outcomes](records/forgejo-final-outcomes.json).
- [Initial trace](records/forgejo-initial-trace.jsonl.gz) and [per-trial outcomes](records/forgejo-initial-outcomes.json). The runner exited 1 after preserving the setup failures. The revised run exited 0.
- [Forgejo startup failure](records/forgejo-initial-startup.jsonl). Forgejo needed a writable, isolated Git config. The initial `GIT_CONFIG_GLOBAL=/dev/null` was incompatible with its startup.
- [Initial TLC invocation error](records/tlc-initial-invocation.txt) and [initial model error](records/tlc-initial-settle-error.txt). The pinned TLC release rejected an extra command-line option. A later run found an incompletely specified successor until the disjunction assigned to `wrongArtifact` was parenthesized.
