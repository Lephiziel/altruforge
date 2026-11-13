# Product brief

## Purpose

Let people contribute available coding-agent capacity to open-source projects under rules set by the project's maintainers.

Altruforge provides an open specification and a reference CLI. A repository can adopt it without joining a mandatory central hub.

## People and responsibilities

| Role | Controls |
| --- | --- |
| Maintainer | Eligible tasks, change boundaries, verification policy, review capacity, and merges |
| Contributor | Their GitHub identity, supported AI tool, account usage, run limits, and stopping a run |
| Altruforge runtime | Enforced workflow, checkpoints, task ownership, checks, and publication |
| Coding agent | Reasoning and implementation inside the permitted task and execution boundary |

A solo developer can hold both human roles. The process remains the same.

## Problem

Potential contributors encounter unfamiliar setup and project conventions. Maintainers spend time reviewing unsuitable work and explaining expectations. More generated PRs can increase that burden.

The product must make a contribution useful enough to justify the maintainer's setup and review time.

## Intended experience

The contributor connects accounts, selects a configured repository, and starts a bounded run. The tool finds eligible work, reports its choice, implements it, checks it, and returns a Draft PR or a clear stopped/failed outcome.

Task selection is a notification, not a routine approval prompt. Decisions outside the configured scope produce a blocked result or a proposal rather than an unauthorized feature.

## Outcomes

Measure accepted changes, maintainer setup time, review time, required corrections, usage where measurable, and regressions after merge. Keep failed and interrupted attempts in the denominator.

Compare the harness with the same coding tool on similar tasks and budgets. Star count and generated lines are not evidence of reduced maintainer effort.

## Constraints

Subscription use must follow provider-supported integration and account controls. A subscriber's capacity is not pooled or resold. No silent fallback to billable APIs is permitted.

The product does not guarantee that passing tests makes a change correct. Human review and project-owned CI remain necessary.
