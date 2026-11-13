# MVP implementation backlog

Every task is currently unimplemented. Start with the first unblocked package requested by the maintainer; documentation does not satisfy runtime acceptance.

MVP-01 proves the critical boundary. MVP-02 can establish the module while that evidence is collected; it cannot certify the boundary.

| Task | Outcome | Dependencies | GitHub issue |
| --- | --- | --- | --- |
| [MVP-01](MVP-01.md) | Prove supported authentication and execution boundaries | None | To be linked after issue creation |
| [MVP-02](MVP-02.md) | Bootstrap the Go module and core development workflow | None | To be linked after issue creation |
| [MVP-03](MVP-03.md) | Implement strict project manifest loading and policy validation | MVP-02 | To be linked after issue creation |
| [MVP-04](MVP-04.md) | Implement durable run state and crash recovery | MVP-02 | To be linked after issue creation |
| [MVP-05](MVP-05.md) | Implement GitHub identity and isolated Git workspaces | MVP-02 | To be linked after issue creation |
| [MVP-06](MVP-06.md) | Implement the Codex agent adapter | MVP-01, MVP-02, MVP-04 | To be linked after issue creation |
| [MVP-07](MVP-07.md) | Implement the controlled Linux executor | MVP-01, MVP-02, MVP-03 | To be linked after issue creation |
| [MVP-08](MVP-08.md) | Implement authoritative GitHub task leases | MVP-02, MVP-03, MVP-05 | To be linked after issue creation |
| [MVP-09](MVP-09.md) | Implement eligible issue discovery and task selection | MVP-03, MVP-05, MVP-08 | To be linked after issue creation |
| [MVP-10](MVP-10.md) | Implement bounded run orchestration | MVP-04, MVP-06, MVP-07, MVP-09 | To be linked after issue creation |
| [MVP-11](MVP-11.md) | Implement independent verification and report generation | MVP-03, MVP-07, MVP-10 | To be linked after issue creation |
| [MVP-12](MVP-12.md) | Implement idempotent Draft PR publication | MVP-05, MVP-08, MVP-10, MVP-11 | To be linked after issue creation |
| [MVP-13](MVP-13.md) | Implement onboarding and the public CLI contract | MVP-03, MVP-04, MVP-05, MVP-06, MVP-10, MVP-12 | To be linked after issue creation |
| [MVP-14](MVP-14.md) | Implement cross-platform packaging and release checks | MVP-02, MVP-13 | To be linked after issue creation |
| [MVP-15](MVP-15.md) | Record real end-to-end and contribution-quality evidence | MVP-11, MVP-12, MVP-13, MVP-14 | To be linked after issue creation |
| [MVP-16](MVP-16.md) | Finalize maintainer onboarding and enable proven self-hosting | MVP-14, MVP-15 | To be linked after issue creation |

## Working rules

Use one scoped PR per package. Do not mark a task complete until its acceptance evidence exists. Independent work can use isolated branches/worktrees when dependencies are satisfied. All issue and PR content must be in English.

The GitHub issues mirror these task documents. If they diverge, resolve the discrepancy before implementation.
