# Threats to validity

## Construct validity

“Exactly once” can refer to request delivery, handler invocation, logical object creation, or user-visible effect. The protocol therefore measures physical requests and logical provider effects separately. A provider's response schema may not expose every internal effect. The independent oracle tests visible postconditions, not hidden server internals.

## Internal validity

Fault injection can miss a request boundary or accidentally create multiple events. Synchronization barriers, unique event IDs and raw proxy/provider logs are required. The prior NIR-03 R4 duplicated aggregate barrier entries show why individual events must be reconciled with source logs. A fixture smoke failure must remain separate from treatment outcomes. The evaluator's prior 404 edge case motivates requiring successful exact-state evidence.

## Measurement validity

Driver labels are not ground truth. The observer must use actual provider state, independent read-only credentials and raw response preservation. Separate process/token does not fully isolate shared host, network, provider database, caches, or common API implementation. Record this dependency and, where practical, separate routing/observer host. Preserve HTTP bodies and hashes after redacting secrets; record redaction rules and original-response digest before secure filtering where policy permits.

## External validity

One provider/version and synthetic workloads cannot generalize to all forges. Endpoint guarantees change over time and must be pinned to versioned specifications and verified in the actual disposable fixture. Agent benchmark success does not generalize to publication safety. Formal finite-state abstractions omit production complexity.

## Statistical conclusion validity

Rare unsafe events need large samples; one observation per cell cannot establish comparative claims. Trials may be correlated within one provider instance or fault schedule. Predefine the estimand, effect size, confidence interval, multiplicity family, and cluster handling. A nonsignificant result is not evidence of equivalence. Unknown and missing evidence must not be silently pooled with success or discarded.

## Model validity

TLA+ state abstraction and fairness assumptions can hide implementation defects. A finite TLC pass is bounded model-checking evidence, not proof of provider behavior or code. Counterexamples show behaviors admitted by the abstraction, not necessarily behaviors of a particular provider unless assumptions are validated. The proposed model itself requires expert review before conclusions.

## Reproducibility and security

Network variability, external API changes, secrets, and hidden environment state affect replication. Pin tool/provider digests, capture environment and random seeds, keep raw private artifacts with checksums, and publish sanitized evidence only. Credentials must be least-scoped, temporary and excluded from logs/artifacts. Never test against production repositories or state.
