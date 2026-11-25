# Publication specification

## State and authority

Consider one eligible task, one authorizing lease generation, one verifier policy, and one publisher. The inputs are a Git object database, verification evidence, and publication authorization. The local orchestration ledger, remote Git refs, and forge PR store have separate commit points. Git objects are content addressed. A branch name and the PR that follows it can outlive several different Git objects.

| Domain | State | Trust boundary |
| --- | --- | --- |
| Local Git | Base commit, verified candidate commit and tree, commit ancestry | The verifier reads immutable objects and a pinned policy independently of the author |
| Verifier | Verifier and policy identity, base and candidate OIDs, execution context, check outcomes and evidence digest | A digest binds stored bytes. An authorized verifier or trusted attestation establishes the provenance of those bytes |
| Coordinator | Task, run, publisher, lease generation and validity | An authoritative lease can grant or fence an attempted handoff. A local copy is evidence of an observation |
| Local ledger | Sealed intent, dispatch count, optional receipt, optional durable verdict | Commits survive worker termination in the experiment. Volatile variables and responses can disappear |
| Remote Git | Repository identity and writable refs | Native ref operations can condition a specific ref update on an expected OID. Authorized contributors can move refs |
| Forge | PR records, open/closed status, head and base repository/ref associations, reported OIDs and draft status | The observer trusts scoped reads from this forge for the specified observation window |

In the fixture, verification checks a single allowed path, its exact contents, and the direct parent. The runner records tree and commit OIDs and hashes the verifier policy and the check record. It assumes fixture authorization for the duration of the trial. A live coordinator, cryptographic attestations, and upstream CI are outside the fixture.

## Identities

The verified artifact identity binds the repository, verified base OID, candidate commit and tree OIDs, verifier and policy, and evidence digest. A valid publication intent additionally binds the target deployment, head/base repository IDs and ref names, task, run and publisher authority. The general intent binds the lease generation. The experiment instantiates a static fixture task and authority, and hashes its sealed record using canonical JSON.

The local intent key stays fixed across restart. A marker carrying that key and the evidence references travels in the PR body. It is a lookup aid on an editable resource. The remote effect identity is the forge deployment, target repository ID, and provider-assigned PR ID and number. Adoption requires independently matching the branch tuple, marker, open draft state, reported PR head/base OIDs, and current Git tips to the intent. The verification checks are bound to those OIDs. A different head or base requires separate evidence and authority.

## Allowed transitions

| From | Step | Durable and remote effects |
| --- | --- | --- |
| Unsealed | Validate evidence and authority, seal intent | Commit intent before any publication mutation |
| Pending | Establish candidate ref | Install the exact candidate using an expected absence or an authorized expected OID. Preserve an unexpected ref |
| Pending | Validate current refs and dispatch create | Commit the dispatch marker before sending. The forge can settle independently of the worker |
| Pending | Receive a creation receipt | Optionally commit the provider's effect identity. Completion still requires an observation |
| Pending or unknown | Read remote state during recovery | Read identified PRs and refs. Compare them against the sealed intent |
| Pending or unknown | Observe exactly one matching draft and commit the verdict | Record the effect identity and the assertion supported by the observation |
| Pending or unknown | Observe incompatible refs, PR identity or multiplicity | Record a blocked outcome. Preserve remote state |
| Pending | Lose the ability to settle the effect | Record an explicit unknown outcome. Further observation can resolve it |

A crash clears in-memory preflight checks, observations and unpersisted responses. A request that reached the forge can complete after the worker exits. A new process reads the last committed intent and any receipt and must re-establish its evidence before completing. A dispatch marker establishes that a submission was possible. Even with that marker, a restart can encounter a request that never left the process.

## Safety predicates

| Predicate | Scope |
| --- | --- |
| Intent precedes effect | A scoped candidate ref installation or PR submission requires a sealed intent |
| Artifact binding at creation | The head and base at the PR creation point equal the verified SHAs. In the model, a sticky flag records any violation |
| Valid completion | A durable completion names the one identified open draft and the verified head/base values established by a coherent observation |
| Effect multiplicity | At most one PR creation for an intent over the admitted history. Count creation effects even if a later action closes a PR |
| Ref ownership | The publisher never replaces an unexpected tip or writes unrelated refs. External changes authorized for a trial appear in the independent trace |
| Honest uncertainty | An absent receipt, timeout, or unqualified empty lookup does not establish which remote effects occurred |

Completion describes an observation, with a bounded interval of validity tied to its inputs. The model treats observation as atomic. The driver reads the forge and Git separately on a quiescent interval in the matrix. A deployment subject to continuous writes needs stronger observation semantics or a means to fence writes for that interval. Fresh authorization and artifact checks are needed for any later gate that acts on a live PR.

## Endpoint assumptions and progress

The guarded model assumes an atomic comparison of both ref OIDs at PR creation and serialized uniqueness for the sole open PR in its admitted history. In an implementation, enforceable ref immutability during the write can supply the creation guard. Comparing tips before POST and applying compare-and-swap to a previous Git push leave a gap before the forge resolves the branch names.

Liveness is conditional. With matching refs that stay stable, eventual delivery and settlement of the allowed request, eventual visible reads, at most two modeled crashes, and weak fairness for individual recovery steps, the stable profile eventually reaches durable completion. Conflicting evidence can lead to blocked resolution. Unavailable or inconclusive observations can leave a durable unknown. State changes outside the admitted history include concurrent publishers, PR closure, reversible ref changes, and loss of the forge or its storage.

For an endpoint without a trustworthy settlement test or enforceable deduplication, consider two histories with the same read results after restart. In one, the dispatch never reached the forge. In the other, the forge accepted it and may finish after the read. Progress in the first history can require resubmission. The same resubmission in the second can duplicate a non-idempotent effect. The protocol needs a stronger endpoint contract, an enforceable exclusion mechanism, or a way to surface unresolved outcomes. A mutable metadata marker alone provides no exclusion.

## Model scope

[Publication.tla](model/Publication.tla) represents one intent, a missing/verified/foreign candidate ref, a verified/foreign base ref, at most one outstanding create, up to two submissions and up to two crashes. Intent validity is abstracted into the seal transition. A late settlement can occur during worker downtime or after an unknown or blocked verdict. The model represents lost acknowledgment by making settlement independent of the worker's observation. Its effect count assumes that PRs stay open. The replay profile models an endpoint that can accept a second submission.

The four TLC profiles exercise different assumptions. [Results](RESULTS.md#tla-model-checking) includes the checked state counts and counterexamples. There is no refinement mapping from the Python driver or Forgejo internals to this finite model.
