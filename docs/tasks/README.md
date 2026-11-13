# MVP implementation backlog

[First MVP tracker](https://github.com/Lephiziel/altruforge/issues/19)

Every task is currently unimplemented. Start with the first unblocked package requested by the maintainer; documentation does not satisfy runtime acceptance.

MVP-01 proves the critical boundary. MVP-02 can establish the module while that evidence is collected; it cannot certify the boundary.

| Task | Outcome | Dependencies | GitHub issue |
| --- | --- | --- | --- |
| [MVP-01](MVP-01.md) | Prove supported authentication and execution boundaries | None | [#3](https://github.com/Lephiziel/altruforge/issues/3) |
| [MVP-02](MVP-02.md) | Bootstrap the Go module and core development workflow | None | [#4](https://github.com/Lephiziel/altruforge/issues/4) |
| [MVP-03](MVP-03.md) | Implement strict project manifest loading and policy validation | MVP-02 | [#5](https://github.com/Lephiziel/altruforge/issues/5) |
| [MVP-04](MVP-04.md) | Implement durable run state and crash recovery | MVP-02 | [#6](https://github.com/Lephiziel/altruforge/issues/6) |
| [MVP-05](MVP-05.md) | Implement GitHub identity and isolated Git workspaces | MVP-02 | [#7](https://github.com/Lephiziel/altruforge/issues/7) |
| [MVP-06](MVP-06.md) | Implement the Codex agent adapter | MVP-01, MVP-02, MVP-04 | [#8](https://github.com/Lephiziel/altruforge/issues/8) |
| [MVP-07](MVP-07.md) | Implement the controlled Linux executor | MVP-01, MVP-02, MVP-03 | [#9](https://github.com/Lephiziel/altruforge/issues/9) |
| [MVP-08](MVP-08.md) | Implement authoritative GitHub task leases | MVP-02, MVP-03, MVP-05 | [#10](https://github.com/Lephiziel/altruforge/issues/10) |
| [MVP-09](MVP-09.md) | Implement eligible issue discovery and task selection | MVP-03, MVP-05, MVP-08 | [#11](https://github.com/Lephiziel/altruforge/issues/11) |
| [MVP-10](MVP-10.md) | Implement bounded run orchestration | MVP-04, MVP-06, MVP-07, MVP-09 | [#12](https://github.com/Lephiziel/altruforge/issues/12) |
| [MVP-11](MVP-11.md) | Implement independent verification and report generation | MVP-03, MVP-07, MVP-10 | [#13](https://github.com/Lephiziel/altruforge/issues/13) |
| [MVP-12](MVP-12.md) | Implement idempotent Draft PR publication | MVP-05, MVP-08, MVP-10, MVP-11 | [#14](https://github.com/Lephiziel/altruforge/issues/14) |
| [MVP-13](MVP-13.md) | Implement onboarding and the public CLI contract | MVP-03, MVP-04, MVP-05, MVP-06, MVP-10, MVP-12 | [#15](https://github.com/Lephiziel/altruforge/issues/15) |
| [MVP-14](MVP-14.md) | Implement cross-platform packaging and release checks | MVP-02, MVP-13 | [#16](https://github.com/Lephiziel/altruforge/issues/16) |
| [MVP-15](MVP-15.md) | Record real end-to-end and contribution-quality evidence | MVP-11, MVP-12, MVP-13, MVP-14 | [#17](https://github.com/Lephiziel/altruforge/issues/17) |
| [MVP-16](MVP-16.md) | Finalize maintainer onboarding and enable proven self-hosting | MVP-14, MVP-15 | [#18](https://github.com/Lephiziel/altruforge/issues/18) |

## Working rules

Use one scoped PR per package. Do not mark a task complete until its acceptance evidence exists. Independent work can use isolated branches/worktrees when dependencies are satisfied. All issue and PR content must be in English.

The GitHub issues mirror these task documents. If they diverge, resolve the discrepancy before implementation.
