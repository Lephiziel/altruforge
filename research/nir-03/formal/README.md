# NIR-03 formal artifacts

- `SPECIFICATION.md`: state, identities, transition semantics, safety, conditional liveness, and limits.
- `CandidatePublication.tla`: finite initial TLA+ model.
- `Safety.cfg`: explores all modeled actions, including crashes, and checks invariants.
- `ConditionalLiveness.cfg`: checks conditional liveness with weak fairness and no further crashes.
- `runs/v1.8.0/`: successful TLC stdout/stderr captures. `runs/failed-terminal-deadlock/` and `runs/failed-unbounded-crash/` retain exact model/config snapshots, TLC trace binaries, decoded state traces in the replay logs, and counterexamples from the two initially failing checks. The traces show why terminal states were excluded from deadlock checks and why unbounded crashes defeat the liveness claim.

Reproduce with Java 11 or newer and the official TLA+ tools v1.8.0 JAR. The release JAR SHA-256 used here was `fdffef247f563ef6edbfd44958d2a82db79e7564e07cb673262d896353fa6713`.

```sh
curl -fL https://github.com/tlaplus/tlaplus/releases/download/v1.8.0/tla2tools.jar \
  -o /tmp/tla2tools-v1.8.0.jar
echo 'fdffef247f563ef6edbfd44958d2a82db79e7564e07cb673262d896353fa6713  /tmp/tla2tools-v1.8.0.jar' \
  | sha256sum -c -
java -jar /tmp/tla2tools-v1.8.0.jar \
  -config research/nir-03/formal/Safety.cfg -workers 1 \
  research/nir-03/formal/CandidatePublication.tla
java -jar /tmp/tla2tools-v1.8.0.jar \
  -config research/nir-03/formal/ConditionalLiveness.cfg -workers 1 \
  research/nir-03/formal/CandidatePublication.tla
```

The runs retained here were performed with OpenJDK `27.0.1.1`, TLC `2026.11.19.180144` from the v1.8.0 release JAR. Safety checked 26 distinct states; conditional liveness checked 16 distinct states. Both final runs completed without an error. See each raw log. The two earlier failed runs and generated temporal traces are preserved; they are not represented as successful checks.
