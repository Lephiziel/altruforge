# Evidence index

The repository has no complete runtime or cross-platform end-to-end evidence. Individual records may contain partial observations; consult each record's limitations before relying on it.

Add evidence records when a task actually runs. A document describing a scenario is not a record that it passed.

| Field | Required content |
| --- | --- |
| Task and revision | MVP ID and immutable tested commit |
| Environment | Host OS/architecture, agent, executor, and relevant tool versions |
| Scenario | Exact commands or reproducible steps |
| Observation | Passed, failed, blocked, or not run |
| Artifacts | Redacted logs, reports, test output, or CI URL |
| Limitations | Untested behavior, manual steps, and unsupported combinations |
| Review | Reviewer and date |

## Records

| Record | Status |
| --- | --- |
| [MVP-01 boundary](MVP-01-boundary.md) | Partial Linux observations; acceptance gate remains blocked |

Store public evidence as `docs/evidence/MVP-XX-<topic>.md`. Keep private account artifacts outside the repository.
