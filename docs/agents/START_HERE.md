# Start here

This guide is the cold-start handoff for implementing Altruforge. The repository is intentionally ready for coding without containing an application implementation.

## Reading order

1. Read [AGENTS.md](../../AGENTS.md) and the current user request.
2. Read [MVP scope](../product/mvp.md) and [architecture](../architecture.md).
3. Select the requested task from [the backlog](../tasks/README.md).
4. Read that task's dependencies, acceptance criteria, contracts, and ADRs.
5. Inspect the checkout and accepted evidence; do not infer implementation from documentation.

## First task

Start with **MVP-01**, the authentication/execution feasibility boundary. MVP-02 is the module/bootstrap task; it may prepare the application skeleton but cannot certify the security boundary.

If the provider integration cannot satisfy the required host matrix and credential boundary, record the concrete incompatibility and propose an ADR. Do not solve it by copying credentials into a worker, disabling isolation, or narrowing the public OS requirement without a decision.

## Working protocol

Implement one task in a scoped branch. Keep its ID in the PR. Meet dependencies before claiming it complete. Use actual failure cases and exact validation results. Routine local decisions do not require a new approval conversation.

If another agent is working in the checkout, inspect current changes and coordinate through the task/branch. Do not overwrite concurrent work. Parallel work needs isolated branches/worktrees and satisfied dependencies; it is not a reason to bypass review.

Do not implement future marketplace, GUI, extra-provider, or automatic-merge features while closing an MVP task.

## Completion

Use [HANDOFF.md](HANDOFF.md). Update evidence and relevant docs. Report the next unblocked task, and leave unmet gates explicitly blocked.

The repository's own `.altruforge/project.yaml` is disabled during bootstrap. It is a manifest fixture and future self-hosting configuration; it does not replace these implementation instructions.
