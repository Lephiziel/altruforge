# NIR-03 fresh-checkout reproducibility

This procedure records how to reproduce the P0.1 setup and how the completed S1-R2 environment was prepared from a fresh checkout, without prior chat state or credentials from another run. Every reproduction uses only disposable synthetic repositories. NIR-03's experimental program is frozen: **do not rerun any P0.1, S1, or S1-R2 assignment**. Reproduction here means auditing artifacts or setting up a separately approved future study with a new identity and protocol; it does not authorize additional NIR-03 trials.

## Obtain the PR source from a fresh checkout

```sh
git clone https://github.com/Lephiziel/altruforge.git altruforge-nir03
cd altruforge-nir03
git fetch origin pull/29/head:refs/heads/nir-03-completion-audit
git checkout nir-03-completion-audit
git rev-parse HEAD
```

Record the printed source commit in the reproduction notes. The PR ref advances when the PR is updated; pin that commit for any reported rerun. Continue with the environment setup below from the repository root.

## Requirements and tested environment

Required: Linux x86_64, Git, Python 3, GnuPG, curl, and Java 11+ for the optional TLC model. The retained P0.1 run was on Linux x86_64 with Forgejo `17.0.2+gitea-1.22.0`; its exact Git/Python versions are in `pilot-results.json`. Formal checks used OpenJDK `27.0.1.1` and official TLA+ tools v1.8.0.

The P0.1 runner requires Forgejo 17.0.2 and loopback HTTP. It creates private repositories through the API, uses Git HTTP only, and refuses an existing result path or experiment root.

## Obtain and verify Forgejo

Use the fixed version rather than `latest`. Forgejo's official download page documents the binary and signature verification procedure at <https://forgejo.org/download/>. Its documented release signing master-key fingerprint is `EB114F5E6C0DC2BCDD183550A4B61A2DC5923710`.

```sh
set -eu
export NIR03_SETUP=/tmp/nir03-repro-setup
mkdir -m 700 -p "$NIR03_SETUP/gnupg"
export GNUPGHOME="$NIR03_SETUP/gnupg"
chmod 700 "$GNUPGHOME"
gpg --keyserver hkps://keys.openpgp.org --recv-keys EB114F5E6C0DC2BCDD183550A4B61A2DC5923710
gpg --fingerprint EB114F5E6C0DC2BCDD183550A4B61A2DC5923710
# Confirm the full fingerprint printed above matches the official fingerprint.
curl -fL https://code.forgejo.org/forgejo/forgejo/releases/download/v17.0.2/forgejo-17.0.2-linux-amd64 -o "$NIR03_SETUP/forgejo-17.0.2-linux-amd64"
curl -fL https://code.forgejo.org/forgejo/forgejo/releases/download/v17.0.2/forgejo-17.0.2-linux-amd64.asc -o "$NIR03_SETUP/forgejo-17.0.2-linux-amd64.asc"
gpg --verify "$NIR03_SETUP/forgejo-17.0.2-linux-amd64.asc" "$NIR03_SETUP/forgejo-17.0.2-linux-amd64"
chmod 700 "$NIR03_SETUP/forgejo-17.0.2-linux-amd64"
"$NIR03_SETUP/forgejo-17.0.2-linux-amd64" --version
```

The signature check must report a good signature from Forgejo Releases and the displayed primary fingerprint must match. Stop on any mismatch. The NIR-03 runner verifies the API version again before creating repositories.

## Prepare the isolated instance

From the repository root:

```sh
research/nir-03/prepare_forgejo.sh \
  "$NIR03_SETUP/forgejo-17.0.2-linux-amd64" \
  /tmp/nir03-forgejo-fresh \
  30300
```

The script refuses an existing state path, binds its generated config to `127.0.0.1`, uses SQLite, disables registration, SSH, SMTP, Actions, OpenID sign-in, and package registry, creates a synthetic admin account, and writes a scoped API token to a mode-0600 file. It does not print the token. Do not commit or display that file.

In a dedicated terminal, start the disposable server:

```sh
"$NIR03_SETUP/forgejo-17.0.2-linux-amd64" \
  --work-path /tmp/nir03-forgejo-fresh \
  --config /tmp/nir03-forgejo-fresh/custom/conf/app.ini \
  web
```

Wait until `curl --fail http://127.0.0.1:30300/api/v1/version` succeeds. If port 30300 is occupied, select an unused port in the prepare step and substitute it consistently below.

## Run the retained P0.1 protocol and evaluator

Use unique, absent output and disposable-root paths. Never target the retained matrix artifact in the repository:

```sh
mkdir -m 700 -p /tmp/nir03-p01-fresh-output
python3 research/nir-03/pilot_forgejo.py \
  --base-url http://127.0.0.1:30300 \
  --token-file /tmp/nir03-forgejo-fresh/api-token \
  --output /tmp/nir03-p01-fresh-output/pilot-results.json \
  --disposable-root /tmp/nir03-p01-fresh-trials
python3 research/nir-03/evaluate_pilot.py \
  /tmp/nir03-p01-fresh-output/pilot-results.json
```

Keep the full JSON result and evaluator JSON as the output of that reproduction. The evaluator is read-only with respect to Forgejo and computes outcome counts from the `observer` response fields. Compare results descriptively with `pilot-results.json`; do not pool the runs or claim statistical results.

## S1-R2 environment and artifact reproduction

S1-R2 used the same signed Forgejo 17.0.2 binary, `prepare_forgejo.sh`, and loopback-only disposable instance. Its separate observer account and read-only token were created with these commands after `prepare_forgejo.sh` prepared the owner account. Replace paths and port only when creating a separately identified reproduction environment; the historical run used port 30310.

```sh
STATE=/tmp/nir03-s1-r2-fresh-forgejo
PORT=30310
FORGEJO="$NIR03_SETUP/forgejo-17.0.2-linux-amd64"
research/nir-03/prepare_forgejo.sh "$FORGEJO" "$STATE" "$PORT"
"$FORGEJO" --work-path "$STATE" --config "$STATE/custom/conf/app.ini" \
  admin user create --username s1-observer --random-password \
  --email observer@localhost --must-change-password=false
"$FORGEJO" --work-path "$STATE" --config "$STATE/custom/conf/app.ini" \
  admin user generate-access-token --username s1-observer \
  --token-name s1-r2-read-only --scopes read:repository,read:user --raw \
  > "$STATE/observer-token"
chmod 600 "$STATE/observer-token"
```

Start Forgejo in a dedicated terminal and confirm authenticated `/api/v1/version` reports 17.0.2. Create a fresh mode-0700 run directory and use the owner token from `prepare_forgejo.sh`. For historical exact command lines, source commit, protocol path, and evaluator invocation, see [`supplementary/s1-r2/EXECUTION-AND-AUDIT.md`](supplementary/s1-r2/EXECUTION-AND-AUDIT.md). That completed run must not be repeated. For audit-only reproduction, verify the archived tar checksum against [`supplementary/s1-r2/archive/ARCHIVE-README.md`](supplementary/s1-r2/archive/ARCHIVE-README.md), extract into a private directory, then match each capture document and raw body to `raw-capture-index.json` and `archive/ARCHIVE-MANIFEST.json`. The independent reviewer verified all indexed sizes and SHA-256 digests.

The observer runs as a separate process, reads only the observer token, and captures provider GET responses, errors, endpoint identities, timestamps, body digests, and raw body files. The runner grants that account read access to each synthetic private repository. Preserve the original results and frozen evaluator output; do not change scoring after seeing outcomes.

## Model-checking reproduction

Use the exact two commands and pinned v1.8.0 JAR SHA-256 in [`formal/README.md`](formal/README.md). The raw retained logs and initial counterexamples are under `formal/runs/v1.8.0/`.

## Shutdown and disposable-state cleanup

Stop Forgejo with Ctrl-C. After preserving any output JSON you need, remove only the exact temporary directories created for this run, including their credential files:

```sh
rm -rf -- /tmp/nir03-forgejo-fresh /tmp/nir03-p01-fresh-trials \
  /tmp/nir03-p01-fresh-output /tmp/nir03-repro-setup
```

Do not run cleanup with a production path or a path not created by this procedure. No production Harness or Altruforge runtime state is part of this workflow.

## Verification performed while authoring this procedure

The setup helper was run from new `/tmp` paths against the signed Forgejo 17.0.2 binary. In the later S1-R2 run, the owner and observer tokens and config were mode 0600. A fresh server started on loopback; `/api/v1/version` returned 17.0.2 and the scoped tokens were exercised against synthetic private repositories. The S1-R2 server was stopped after the 14 assignments. Its private instance and credentials remain outside Git under `/tmp`; raw observer evidence is separately archived as a checked-in research artifact. This procedure did not rerun or modify P0.1 or the original blocked S1 assignments.
