# Related work

This is a targeted selection, not an exhaustive bibliography. A guarantee means only the guarantee under the cited system's stated assumptions; none should be transferred automatically to a forge API.

## Distributed effects, retries and transactions

### [1] End-to-end argument

J. H. Saltzer, D. P. Reed, and D. D. Clark. “End-to-End Arguments in System Design.” *ACM Transactions on Computer Systems* 2(4), 277–288 (1984). DOI: [10.1145/357401.357402](https://doi.org/10.1145/357401.357402); [author copy](https://web.mit.edu/saltzer/www/publications/endtoend/endtoendA4.pdf).

**Problem/method:** where system functions and checks must reside for end-to-end correctness. **Assumptions/guarantees:** lower layers can aid reliability but cannot establish application-level correctness alone; endpoints must check what the application needs. **Evaluation/limits:** architectural argument, not an experiment or publication protocol. **Relevance:** a remote acknowledgement is not proof of the desired artifact-level postcondition; independent end-to-end observation matters.

### [2] RPC semantics

A. D. Birrell and B. J. Nelson. “Implementing Remote Procedure Calls.” *ACM Transactions on Computer Systems* 2(1), 39–59 (1984). DOI: [10.1145/2080.357392](https://doi.org/10.1145/2080.357392).

**Problem/method:** practical remote procedure invocation under failures. **Assumptions/guarantees:** the caller cannot generally infer from a failed response whether the remote operation ran; stronger invocation semantics require protocol support beyond a bare timeout. **Evaluation/limits:** system design and implementation, not a modern forge API study. **Relevance:** ambiguous acknowledgement is a fundamental boundary for publication retries.

### [3] Sagas

H. Garcia-Molina and K. Salem. “Sagas.” *Proceedings of the 1987 ACM SIGMOD International Conference on Management of Data*, 249–259. DOI: [10.1145/38713.38742](https://doi.org/10.1145/38713.38742); [author report](https://www.cs.princeton.edu/techreports/1987/070.pdf).

**Problem/method:** long-lived transactions split into local transactions with compensating actions. **Assumptions/guarantees:** compensation is application-defined and may not restore the exact prior world; the model supports partial progress and recovery. **Evaluation/limits:** database transaction framework, not a generic exactly-once primitive. **Relevance:** forge publication may be a multi-step saga, but compensation is not atomic rollback.

### [4] Consensus on transaction commit

J. Gray and L. Lamport. “Consensus on Transaction Commit.” *ACM Transactions on Database Systems* 31(1), 133–160 (2006). DOI: [10.1145/1132863.1132867](https://doi.org/10.1145/1132863.1132867); [Microsoft Research](https://www.microsoft.com/en-us/research/publication/consensus-on-transaction-commit/).

**Problem/method:** compare two-phase commit and consensus-based transaction commit. **Assumptions/guarantees:** progress depends on coordinator/participant and quorum assumptions; 2PC can block under failures, while Paxos Commit tolerates coordinator failures within its fault model. **Evaluation/limits:** protocol analysis, not an external forge integration. **Relevance:** no atomic transaction spans local intent and independent forge endpoints unless the provider exposes a corresponding primitive.

### [5] FLP impossibility

M. J. Fischer, N. A. Lynch, and M. S. Paterson. “Impossibility of Distributed Consensus with One Faulty Process.” *Journal of the ACM* 32(2), 374–382 (1985). DOI: [10.1145/3149.214121](https://doi.org/10.1145/3149.214121).

**Problem/method:** deterministic consensus in a fully asynchronous message-passing system. **Guarantee/limit:** deterministic consensus cannot guarantee termination in all admissible executions with one crash failure. **Evaluation:** impossibility proof. **Relevance:** contextualizes liveness under unbounded delay, but is not itself an impossibility theorem for artifact publication or exactly-once effects.

### [6] Olive locks with intent

S. Setty, C. Su, J. R. Lorch, L. Zhou, H. Chen, P. Patel, and J. Ren. “Realizing the Fault-Tolerance Promise of Cloud Storage Using Locks with Intent.” *12th USENIX OSDI* (2016), 501–516. [USENIX paper](https://www.usenix.org/conference/osdi16/technical-sessions/presentation/setty).

**Problem/method:** Olive provides locks-with-intent atop cloud storage for deterministic bounded snippets. **Assumptions/guarantees:** storage primitives, logging, deterministic bounded computation, and protocol support provide eventual exactly-once execution plus mutual exclusion despite failures/duplicate execution. **Evaluation:** implementation on storage services and derived workloads. **Limits:** guarantee belongs to Olive's abstraction and assumptions; it does not imply exactly-once effects across arbitrary third-party APIs. **Relevance:** durable intent has substantial prior art; NIR-04 must compare provider contracts rather than claim intent itself as novel.

### [7] Flux idempotence consistency

H. Ding, Z. Wang, Z. Shen, R. Chen, and H. Chen. “Automated Verification of Idempotence for Stateful Serverless Applications.” *17th USENIX OSDI* (2023), 887–910. [Paper and proceedings](https://www.usenix.org/conference/osdi23/presentation/ding).

**Problem/method:** verify retry transparency for concurrent stateful serverless applications using idempotence consistency and simulation. **Assumptions/guarantees:** application/model scope and database-operation reasoning; it does not require every operation to execute physically once. **Evaluation:** 27 applications, issues found in 12, confirmed by developers for 8. **Limits:** not forge publication or arbitrary remote settlement. **Relevance:** concurrent retry reasoning and observable equivalence versus physical exactly-once are established.

### [8] Beldi

H. Zhang, A. Cardoza, P. B. Chen, S. Angel, and V. Liu. “Fault-tolerant and Transactional Stateful Serverless Workflows.” *14th USENIX OSDI* (2020), 1187–1204. [USENIX paper](https://www.usenix.org/conference/osdi20/presentation/zhang-haoran); [extended version](https://arxiv.org/abs/2010.06706).

**Problem/method:** library/runtime using intent and operation logs, replay, and transaction protocols for stateful serverless workflows. **Assumptions/guarantees:** operations use Beldi APIs and underlying storage atomicity/transaction scopes; it provides exactly-once workflow semantics within this abstraction and its assumptions. **Evaluation:** three applications and evaluation on AWS Lambda. **Limits:** application-controlled operations are routed through Beldi; this does not make arbitrary external APIs transactional. **Relevance:** mature intent/log/replay baseline; underscores that durable intent without control over operation effects is not equivalent to Beldi's guarantee.

## Consistency, controllers and concurrency control

### [9] Linearizability

M. P. Herlihy and J. M. Wing. “Linearizability: A Correctness Condition for Concurrent Objects.” *ACM Transactions on Programming Languages and Systems* 12(3), 463–492 (1990). DOI: [10.1145/78969.78972](https://doi.org/10.1145/78969.78972); [author PDF](https://www.cs.columbia.edu/~wing/publications/HerlihyWing90.pdf).

**Problem/method:** each concurrent operation appears atomic between invocation and response while respecting real-time precedence. **Guarantee/limits:** a correctness condition, not a mechanism that makes an API linearizable. **Evaluation:** formal definition and examples. **Relevance:** provides a precise endpoint contract for modeling observations and concurrent ref writes.

### [10] Chubby lock service

M. Burrows. “The Chubby Lock Service for Loosely-Coupled Distributed Systems.” *7th USENIX OSDI* (2006), 335–350. [USENIX paper](https://www.usenix.org/legacy/event/osdi06/tech/full_papers/burrows/burrows_html/).

**Problem/method:** coarse-grained distributed locking and coordination. **Assumptions/guarantees:** sequencers/fencing tokens let resource servers reject operations by stale holders when the resource validates tokens. **Evaluation:** deployed-service design and operational experience. **Limits:** a client lease without resource-side fencing does not stop a delayed actor. **Relevance:** supports explicit fencing variables and guards against assuming a lock alone is sufficient.

### [11] Anvil

X. Sun, W. Ma, J. T. Gu, Z. Ma, T. Chajed, J. Howell, A. Lattuada, O. Padon, L. Suresh, A. Szekeres, and T. Xu. “Anvil: Verifying Liveness of Cluster Management Controllers.” *18th USENIX OSDI* (2024), 649–666. [USENIX paper](https://www.usenix.org/conference/osdi24/presentation/sun-xudong).

**Problem/method:** formal liveness specification (eventually stable reconciliation) and verified controller development. **Assumptions/guarantees:** liveness is conditional on explicit environment/fairness premises. **Evaluation:** verification and deployment of three controllers for ZooKeeper, RabbitMQ, FluentBit. **Limits:** controller setting, not forge publication. **Relevance:** RQ5 should specify stable-state liveness and fairness; reconciliation is established practice.

## Provenance and artifact integrity

### [12] in-toto Statement

in-toto Attestation Framework, “Statement v1” specification. [Specification](https://github.com/in-toto/attestation/blob/main/spec/v1/statement.md).

**Problem/method:** bind a typed predicate to subjects identified by digest. **Assumptions/guarantees:** digest identifies bytes under selected hash; signer trust and predicate semantics remain separate. **Evaluation:** specification, not comparative experiment. **Relevance:** publication identity should use a content digest and verification receipt bound to that digest, not a mutable branch name alone.

### [13] SLSA provenance

SLSA. “Provenance” specification, version 1.1. [Specification](https://slsa.dev/spec/v1.1/provenance).

**Problem/method:** standard predicate describing where/how an artifact was produced. **Assumptions/guarantees:** level-dependent builder and provenance requirements; provenance records claims but does not itself make a source/artifact trustworthy. **Evaluation:** conformance specification. **Relevance:** vocabulary for binding source, build, artifact; publication recovery additionally must preserve that binding through remote effects.

## Git and forge endpoint contracts

### [13] HTTP method idempotency

R. Fielding, M. Nottingham, and J. Reschke, eds. “HTTP Semantics.” RFC 9110, §9.2.2 (2022). [IETF RFC](https://www.rfc-editor.org/rfc/rfc9110.html).

**Problem/method:** normative semantics for HTTP methods and intermediaries. **Guarantee/limits:** idempotence concerns the intended effect of repeated identical requests; the server may still log each request or have other side effects. Clients should not automatically retry non-idempotent methods without knowing they are safe or detecting that the original was not applied. **Evaluation:** standards specification. **Relevance:** a method's generic idempotence label does not establish idempotence of a forge operation's full workflow or external effects.

### [14] Git atomic push

Git project. `git push` manual, `--atomic` option. [Git documentation](https://git-scm.com/docs/git-push).

**Problem/method:** request atomic update of multiple refs when supported. **Guarantee/limits:** applies to requested ref updates; it does not wrap PR creation, checks, attestations, or unrelated stores. **Evaluation:** normative tool documentation. **Relevance:** distinguish multi-ref atomicity from whole-workflow transactions.

### [15] GitHub REST reference update

GitHub. “REST API endpoints for Git references.” [Official API documentation](https://docs.github.com/en/rest/git/refs).

**Problem/method:** create/read/update Git refs over REST. **Assumptions/guarantees:** update accepts a target SHA and force setting; non-force updates are constrained to fast-forward behavior, with conflict/validation responses documented. **Limits:** no general cross-endpoint transaction or universal read freshness guarantee. **Relevance:** endpoint contracts are provider-specific and must not be assumed from Git semantics alone.

### [16] etcd transactions

etcd project. “API” and “API Guarantees,” v3.7/v3.6 documentation. [Transactions](https://etcd.io/docs/v3.7/learning/api/); [guarantees](https://etcd.io/docs/v3.6/learning/api_guarantees/).

**Problem/method:** atomic compare-and-swap transactions over etcd's key-value store. **Assumptions/guarantees:** comparisons and transaction writes are atomic within the etcd store; does not span a separate forge API. **Evaluation:** authoritative implementation documentation. **Relevance:** concrete CAS/transaction capability baseline; highlights the difference between a real provider primitive and client-side read-then-write.

### [17] Kubernetes resource versions

Kubernetes. “API Concepts,” resource versions and consistency. [Official documentation](https://kubernetes.io/docs/reference/using-api/api-concepts/).

**Problem/method:** resource versions identify server-side object versions and support client consistency requirements for get/list/watch. **Assumptions/guarantees:** semantics are scoped to Kubernetes API resources and versioned API behavior. **Evaluation:** technical specification/documentation. **Relevance:** offers a relevant example of version-aware observations and optimistic concurrency in a reconciliation system; not a forge guarantee.

### [18] Kafka delivery semantics (contrast)

Apache Kafka. “Message Delivery Semantics.” [Official documentation](https://kafka.apache.org/documentation/#semantics).

**Problem/method:** transactional producer/consumer coordination and idempotent writes within Kafka. **Guarantees/limits:** exactly-once applies to supported Kafka read-process-write flows; external destinations need cooperation. **Evaluation:** implementation documentation. **Relevance:** demonstrates scoped exactly-once claims, not universal external API execution.

### [21] Transactional outbox pattern (engineering practice)

C. Richardson. “Pattern: Transactional outbox.” Microservices.io. [Pattern description](https://microservices.io/patterns/data/transactional-outbox.html).

**Problem/method:** atomically store an event in a service-local database transaction, then relay it to a broker. **Assumptions/guarantees:** outbox and domain state share a transaction; relay may publish more than once, so consumers need idempotency. **Evaluation:** practitioner pattern description, not peer-reviewed experimental research. **Limits:** the external relay effect is at-least-once and requires an idempotent consumer; does not atomically publish to arbitrary forge APIs. **Relevance:** useful engineering baseline for local intent plus relay, but not a solution to remote effect observation.

## Autonomous software engineering evaluation

### [19] SWE-bench

J. Jimenez et al. “SWE-bench: Can Language Models Resolve Real-World GitHub Issues?” *International Conference on Learning Representations* (2024). [Proceedings and paper](https://proceedings.iclr.cc/paper_files/paper/2024/hash/edac78c3e300629acfe6cbe9ca88fb84-Abstract-Conference.html).

**Problem/method:** benchmark generated patches against tests for real GitHub issues. **Assumptions/guarantees:** repository tasks, tests and environment define resolution. **Evaluation:** issue instances across Python repositories with execution-based evaluation. **Limits:** passing tests do not establish safe remote publication, provenance, or correct recovery after ambiguous effects. **Relevance:** agent capability and workflow safety are distinct axes.

### [20] SWE-agent

J. Yang et al. “SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering.” arXiv:2405.15793 (2024). [arXiv](https://arxiv.org/abs/2405.15793).

**Problem/method:** agent-computer interface for repository issue resolution. **Assumptions/guarantees:** effectiveness depends on interface, benchmark and model setup. **Evaluation:** benchmark performance on SWE-bench variants. **Limits:** does not settle third-party publication semantics or prove artifact identity at deployment. **Relevance:** separates autonomous code work from durable, independently observable publication lifecycle.

## Search-index cross-checks

Discovery queries also covered transaction-outbox patterns, etcd compare-and-swap, Git receive-pack and artifact attestations. They are not used for claims here without a primary source or authoritative specification. Reviewer-identified adjacent work should be added before preregistration; the selection above does not justify novelty.
