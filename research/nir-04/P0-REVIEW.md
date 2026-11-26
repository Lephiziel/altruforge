# NIR-03 closeout review for NIR-04 / P0

**Requested source:** PR #29 at commit `d706e37db4d4d15f1f50529a671cfd70df00f7d8`.

## Independent read-only findings

- Local worktree and `origin/research/nir-03-p01` tracking ref were both at the requested commit; the NIR-03 worktree was clean.
- The S1-R2 raw archive was locally accessible. Its archive SHA-256 matched the documented value `31954a6564acebcd3cb4161874e9404defd80bf1a73dc239c4bf984cafeafc10`. The manifest SHA-256 matched `5724faf81ecb25dd0af995a72d3756963a5d6ff0b5ee7647de3614c5c6807257`. All 150 members matched manifest sizes and SHA-256 values.
- Protected P0.1 result files, NIR-03 formal artifacts, original S1 preregistration/results/evaluation and S1-R2 artifact set were unchanged relative to `7b7dd1408a8fbddea3fb1d0ec9db7e699e420ede`.
- Final scientific/technical review is substantive and addresses model abstraction, protocol adherence, fault fidelity, observer independence, unknown/ledger evidence, evaluator, failed runs, conclusions and reproducibility.
- R4 aggregate barrier duplication is reconciled in the existing audit: source proxy records show one POST/201/drop event per cell and observer evidence shows one PR. Original aggregate rows are retained.
- Limitations disclosed in the final review remain: no separately persisted file-level snapshots of intermediate unknown ledger state; evaluator allows branch 404 plus empty object lists to classify not-executed (observed R1 records later had a successful exact-base 200 response); observer/driver/proxy share host and Forgejo instance; one Forgejo build and one trial per scenario-policy cell; formal abstraction omits concurrent publishers, stale reads, permanent observation failure and post-terminal mutations.

## Live PR, CI, and archive verification

The initial local DNS failure prevented verification, but a later authenticated GitHub query succeeded. PR #29 is **open** against `main` at head `d706e37db4d4d15f1f50529a671cfd70df00f7d8`. The Documentation check and Go application checks on Ubuntu, macOS, and Windows all report success.

The raw archive was fetched from the exact PR head via GitHub's raw-content endpoint. Remote and local sizes both equal 29,629 bytes; both SHA-256 digests equal `31954a6564acebcd3cb4161874e9404defd80bf1a73dc239c4bf984cafeafc10`. The local archive's 150 members were independently verified against the capture index and archive manifest as recorded above.

## Disposition

**NIR-03 content and evidence:** ready for owner acceptance. The live PR state, head, green CI, and archive accessibility/integrity have now been independently confirmed. No merge was made; PR #29 remains open for owner acceptance. No NIR-03 trials were rerun and no NIR-03 historical files were changed during this audit.
