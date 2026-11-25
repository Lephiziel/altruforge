# Replicate NIR-03

Run from the repository root as a regular user on Linux amd64, with Git, Python 3.11 or later, Java 11 or later, and standard shell utilities. The pinned Forgejo release includes SQLite. It listens on an ephemeral loopback port and creates accounts, branches, and PRs inside a fresh temporary directory. The workflow uses freshly generated credentials and accepts no remote forge URL. Each output directory must be new.

## Tool downloads

`bash
nir03_tools=$(mktemp -d)
forgejo_asset=forgejo-15.0.12-linux-amd64
curl -fL "https://code.forgejo.org/forgejo/forgejo/releases/download/v15.0.12/$forgejo_asset" \
  -o "$nir03_tools/$forgejo_asset"
curl -fL https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar \
  -o "$nir03_tools/tla2tools-1.7.4.jar"
printf 'd10b861514736e29f43e9d8e70bcf8e57a0b26e9e212412952ee4fa987662ca5  %s\n' \
  "$nir03_tools/$forgejo_asset" | sha256sum -c -
printf '936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88  %s\n' \
  "$nir03_tools/tla2tools-1.7.4.jar" | sha256sum -c -
chmod u+x "$nir03_tools/$forgejo_asset"
`

The recorded Forgejo binary matched the release checksum. See the [official Forgejo release index](https://forgejo.org/releases/15.x/) and the [TLA+ tools release](https://github.com/tlaplus/tlaplus/releases/tag/v1.7.4).

## Forgejo run

`bash
PYTHONDONTWRITEBYTECODE=1 python3 research/nir-03/run.py \
  --forgejo "$nir03_tools/$forgejo_asset" --out "$nir03_tools/forgejo-run"
`

Add `--contract-only` and choose a new output directory to run the endpoint probes alone. The process stops the forge and removes its disposable working directory on exit. The specified output directory retains `trace.jsonl` and `outcomes.json`. Expect 35 assigned trials and zero infrastructure errors for a complete run. A nonzero exit indicates an infrastructure error with a retained trace. The concurrent probes are timing dependent.

Use `seq` and `ms` to follow observed event order and elapsed monotonic time. The `contract` events capture individual probes. Inspect `kill_barrier_confirmed`, `sigkill_confirmed`, `response_drop_barrier`, `response_dropped`, and `oracle_final` to check the corresponding boundaries and outcomes. `forge_forward` and `forge_response` pair one relay request with its upstream reply, while `install_ref` and `contributor_push` record native Git commands. Responses include the fields used for grading and HTTP errors.

`bash
gzip -dc research/nir-03/records/forgejo-final-trace.jsonl.gz | less
python3 -m json.tool research/nir-03/records/forgejo-final-outcomes.json | less
`

## TLC run

`bash
(
  cd research/nir-03/model
  for profile in guarded stable mutable-refs blind-replay; do
    status=0
    java -XX:+UseParallelGC -jar "$nir03_tools/tla2tools-1.7.4.jar" -workers 1 \
      -metadir "$nir03_tools/tlc-$profile" -config "$profile.cfg" Publication.tla \
      > "$nir03_tools/tlc-$profile.txt" 2>&1 || status=$?
    printf '%s %s\n' "$profile" "$status"
  done
)
`

Expected exit codes are 0 for `guarded` and `stable`, and 12 for `mutable-refs` and `blind-replay`. Check the named invariants in each trace because syntax errors and invariant counterexamples represent different outcomes. TLC records its selected fingerprint and seed in the output.
