# Literature search protocol

## Scope and dates

The scoped search was conducted 2026-11-26. It is a documented targeted review, not a claim of exhaustive systematic-review coverage. The goal is to establish known mechanisms and assumptions relevant to crash/retry publication, consistency, concurrency, provenance, reconciliation, and autonomous software agents.

## Sources searched

- ACM Digital Library / DOI metadata and author-hosted copies.
- USENIX proceedings and paper pages (OSDI, FAST, ATC).
- IETF RFC index and standards-track specifications.
- Official Git, GitHub, Apache Kafka, SLSA and in-toto documentation.
- ICLR proceedings and primary benchmark papers for software engineering agents.
- Cross-checking via web search indexes for discovery only; bibliographic claims are checked against publisher/proceedings or author sources.

The environment had outbound access to indexed literature sources. That access did not establish live GitHub PR or CI status; the latter remains unverified.

## Queries

Searches used these query families (quotes indicate phrases, not required exact syntax):

1. `distributed exactly-once semantics idempotent retries remote procedure calls paper`; `transactional outbox idempotency exactly once distributed systems`.
2. `sagas distributed transactions crash recovery original paper`; `consensus on transaction commit Gray Lamport`.
3. `linearizability concurrent objects observation consistency stale reads`; `reconciliation controller liveness failures formal verification`.
4. `concurrent idempotence consistency retries stateful serverless OSDI`; `locks with intent exactly-once cloud storage OSDI`; `Beldi transactional stateful serverless exactly-once OSDI` (added during review).
5. `software artifact provenance SLSA provenance in-toto statement subject digest`; `software supply chain provenance specification`.
6. `Git reference update compare-and-swap atomic push receive-pack`; `GitHub REST update reference fast-forward conflict documentation`.
7. `autonomous software engineering agent benchmark SWE-bench primary paper`; `SWE-agent issue resolution benchmark paper`.
8. Official-documentation queries: `site:docs.github.com REST Git refs update`; `site:git-scm.com/docs git push atomic`; `site:kafka.apache.org idempotent producer transactions`; `site:slsa.dev provenance specification`; `site:rfc-editor.org RFC 9110 idempotent`; `etcd transaction compare-and-swap API`; `Kubernetes resourceVersion consistency API concepts`.

## Inclusion and exclusion

Include primary research papers, peer-reviewed proceedings/journals, foundational papers, standards, and authoritative provider specifications that directly address at least one of: delivery/retry semantics; deduplication or idempotence; distributed commit/compensation; concurrency consistency; reconciliation/liveness; publication/ref update semantics; provenance/integrity; or evaluation of autonomous software engineering systems.

Exclude unsourced opinion, marketing claims without a normative contract, secondary summaries where a primary source exists, unrelated artifact-signing tools without identity/provenance relevance, and papers whose only connection is generic distributed systems context. A directly relevant engineering specification is included even when it is not peer reviewed, and is labeled as such.

## Screening and limitations

Titles/abstracts were screened for direct relevance; included papers were inspected at least at abstract and guarantee/assumption level. Specifications were checked for normative or endpoint-specific semantics. Search engine ranking, indexing, language (English), and access constrain coverage. This review does not assert that every relevant publication has been found. Candidate gaps below are provisional and require independent reviewer challenge, not novelty claims.
