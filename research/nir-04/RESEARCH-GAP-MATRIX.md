# Research gap matrix

“Candidate gap” denotes a question this scoped review did not resolve for the specific forge-publication setting. It is not evidence of novelty. Each item must survive broader literature review and reviewer challenge.

| Dimension | Established knowledge | AltruForge-specific adaptation | Candidate open question | Possible contribution, contingent on prior-art review |
| --- | --- | --- | --- | --- |
| Retry ambiguity | RPC failures can leave invocation outcome unknown; idempotence can make retries observationally transparent. | A forge create/update can settle after timeout and become visible later. | How long can a recovery decision safely classify absence, and what provider contract changes that boundary? | Endpoint-contract model plus schedule-based comparison of classification soundness. |
| Durable intent | Olive and transactional systems use durable intent/logging under explicit storage and code assumptions. | Intent spans local verifier receipt and several independent forge endpoints. | Which subset of intent fields/protocol steps is sufficient when remote effect and local commit are not atomic? | A bounded model and operational contract mapping, not a claim that intents are new. |
| Concurrent publishers | Linearizability, CAS, transactions, locks and fencing are established tools. | Forge branch/ref mutation, PR creation and status APIs may have different atomicity and visibility contracts. | What combination of provider-side CAS/fencing and resource validation preserves publication safety? | Endpoint-specific assumption matrix and counterexample set. |
| Mutable references | Content digests and provenance subjects bind claims to bytes; refs are names that can move. | Verification can target a commit while publication API accepts mutable ref names. | What evidence must survive from verifier input through observed published head to classify completion? | An explicit refinement mapping between verified digest, Git object and remote observation. |
| Observation consistency | Linearizability gives a standard concurrent-object condition; stale reads can violate current-state reasoning. | API reads can fail, be stale, or return inconsistent snapshots across endpoints. | Is linearizable read required, or is versioned/monotonic observation enough for each terminal classification? | A conditional classification rule tied to named provider guarantees. |
| Repeated recovery | Controller literature treats eventual reconciliation as a conditional liveness property with fairness premises. | Recovery may itself crash repeatedly and observations may remain unavailable. | Which fairness and eventual-stability assumptions are sufficient without turning unknown into false completion? | Explicit temporal properties and counterexamples under weakened fairness. |
| Autonomous agents | SWE-bench/SWE-agent evaluate issue resolution and code interaction. | Safe publication is a separate lifecycle that may outlive one agent process/session. | Which workflow properties should be evaluated independently of patch correctness? | A clearly separated lifecycle evaluation framework if literature review supports it. |

## Classification of claims

- **Established knowledge:** idempotence, logs/intents, sagas, consensus commit, CAS, linearizability, fencing, reconciliation, and digest-based provenance each have substantial prior art.
- **Engineering adaptation:** map these concepts onto concrete forge APIs and bind an immutable verified artifact identity to remote state.
- **Open questions:** cross-endpoint contracts, delayed settlement, stale observations, and repeated crashes in a particular publication workflow; these require endpoint-specific formalization.
- **Potential original contributions:** only conditional candidates in the final column. No novelty conclusion is made from search failure.
