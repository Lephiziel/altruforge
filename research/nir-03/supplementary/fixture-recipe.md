# S1 deterministic fixture recipe

This file is part of the preregistration. Do not change it after any S1 outcome has been observed; changes require a new protocol revision and separate result directory.

For each cell label `L = nir03-s1-R<n>-<policy>`:

1. Create a private disposable repository named by the preregistration and initialize `main` with one UTF-8/LF file `base.txt` containing exactly `NIR-03 S1 synthetic base fixture v1\n`.
2. Create the base commit with message `NIR-03 S1 base fixture`; author and committer name `NIR-03 S1`, email `nir03-s1@example.invalid`, author and committer date `2020-01-01T00:00:00 +0000`. Set `LC_ALL=C`, `TZ=UTC`, `core.autocrlf=false`, and `core.filemode=false` for fixture creation.
3. Create the candidate commit as a child of that base by adding `candidate.txt` with exactly `NIR-03 S1 candidate fixture: <L>\n`; commit message `NIR-03 S1 candidate <L>` with the same author/committer identity and fixed date. The candidate SHA is the immutable artifact identity.
4. Generate the synthetic verification identity as lowercase hex SHA-256 of the UTF-8 bytes `NIR03-S1-VERIFIED\n<L>\n<candidate-sha>\n`. It is metadata for the experiment, not a real code-quality or security attestation.
5. Store these run/base/candidate/verification identities in a pre-dispatch manifest written atomically before fault injection. The driver may read this manifest; the observer independently reads forge state and must not derive observed values from it.

The fixed timestamps, content, branch names, and environment make Git objects reproducible for a given cell label and Git object format. Record `git --version` and the resulting object format. Do not reuse a repository across cells or executions.
