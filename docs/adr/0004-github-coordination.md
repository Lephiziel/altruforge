# ADR 0004 GitHub-controlled task leases

Status: proposed, evidence-gated.
Date: 2026-11-13.

## Context

Contributors do not have upstream write access. Files and local SQLite cannot guarantee exclusive task ownership across independent machines. The maintainer prefers repository-owned configuration without operating a separate server.

## Candidate approach

A minimal trusted GitHub workflow handles authenticated issue-comment requests as structured input. It runs only trusted coordinator code from the maintained integration. It never executes submitted issue/PR content with its write token.

Keep lease state in a dedicated upstream state branch. For each mutation, read its head, build a child commit, and update the ref without force. Concurrent sibling updates must conflict; the losing writer re-reads and retries. Every grant increments a fenced generation.

The workflow needs only the GitHub permissions required to read requests, update its state, and reply. The contributor never receives the upstream token.

## Required proof

MVP-08 must prove the actual GitHub concurrency behavior, retry/idempotency rules, actor binding, expiry, stale-generation rejection, and failure reconciliation. A read-then-comment convention is insufficient.

The exact integration is a candidate until that evidence exists. The bootstrap repository does not install a live coordinator.

## Consequences

A target repository adds a small workflow as well as `.altruforge/`. GitHub supplies the state authority and compute, avoiding a mandatory Altruforge-hosted service.

A lease cannot physically stop an offline computer. It fences authorization for subsequent publication; a resumed worker must refresh authority.
