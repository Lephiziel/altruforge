# P0.1 experimental method

## Unit and controls

The experimental unit is one sealed intent in one newly created Forgejo repository. The controller independently generates and verifies the same deterministic candidate and base commits for every trial. The authorized contributor has a separate account and clone. The controller installs the base and candidate refs with explicit empty Git leases, waits for the initial PR list to become readable, and verifies that both refs are exact and the list is empty before assigning a worker. The worker can preflight with read-only Git operations. Only the laboratory controller performs fixture ref writes.

A separate disposable repository hosts the endpoint probes. All Git mutations use native Git over Forgejo's HTTP endpoint. PR requests use the v15.0.12 REST API with its default draft title prefixes. The relay forwards one fixed create route to the same Forgejo instance. The oracle reads that instance directly using unauthenticated, read-only requests.

## Policies

| Policy | Recovery decision |
| --- | --- |
| Retry | Retry the same intended POST after a fresh ref preflight. A response without a usable creation receipt yields unknown |
| Checkpoint | Reuse a durable receipt via canonical GET when present. Otherwise retry once for this attempt, with the same rules as Retry |
| Read-back | After any recorded submission, look for an existing PR by repository and branch tuple, then validate it by number, ID, marker, and artifact identity. A missing match leaves the earlier submission unknown |
| Fail-stop | If submission was possible and no receipt exists, report unknown for manual reconciliation. If a receipt exists, validate it via canonical GET |
| Retry with reconciliation | Retry once for this attempt and use the same independent lookup policy as Read-back when the forge responds with a duplicate conflict. This compares recovery that relies on the native conflict response with recovery that reads first |

All policies start with the same ref preflight. A mismatch is blocked. All completion paths require the same canonical identity checks. Retry policies retain the forge's duplicate handling and Git's protection of non-fast-forward changes. The matrix assumes a single worker at a time and no PR closures during trials. Separate probes intentionally exercise concurrent creates and closure.

## Fault schedule

| Scenario | Synchronization and fault | Observed boundary |
| --- | --- | --- |
| Control | One worker proceeds through every barrier | A durable verdict after the usual POST and read |
| Kill before create | Stop the worker on its flushed `before_create` barrier before allowing it to advance | Fresh ledger has zero submissions and no receipt. The relay and oracle observe zero creates. Process exit is `-SIGKILL` |
| Kill after create | Stop at `after_create`, after the worker has parsed HTTP 201 | Direct numbered lookup shows the same PR. Dispatch is durable and the receipt and verdict are empty. Process exit is `-SIGKILL` |
| Drop response | Relay obtains HTTP 201, checks the PR via an independent read and closes the client socket before writing a response | Controller confirms zero forwarded response bytes and the worker observes `RemoteDisconnected`. The interrupted worker exits with 75 |
| Drift before recovery | Kill after create, then let the distinct contributor push a fast-forward child before launching recovery | The oracle sees the new tip from Git and reads the live PR. The new tip belongs to the scheduled contributor change |
| Kill while recovering | Kill after create, then kill the recovery process at its `before_verdict` barrier | The second process has made its decision. The direct PR effect remains and the verdict is empty. A third process restarts from the ledger |
| Kill after receipt | Kill at `after_receipt`, after the PR identity is committed | The receipt survives and the verdict is empty. This extra scenario distinguishes receipt reuse from a whole-request retry |

Each barrier uses a flushed message and waits for the controller on stdin. For a kill, the controller reads the ledger and remote state before sending SIGKILL and reopens the ledger after process exit. Fresh processes use the same SQLite file in rollback journal mode with full synchronization. The supervisor stays alive. The relay and supervisor journal sequence numbers order observed events.

## Oracle and measures

The oracle enumerates historical PRs using the direct API and dereferences each number. It queries remote refs with `git ls-remote --refs`. It compares those observations with the published effect IDs from the relay and with the expected fixture identity. The ledger is read only to compare a durable claim to those observations.

| Measure | Grading rule |
| --- | --- |
| Verified completion | The verdict names the single open draft by ID and number and the marker, PR head/base OIDs, and Git tips match the sealed intent. History agrees and the oracle observes no unauthorized effects |
| Publication effects | Distinct PR IDs from accepted create responses and direct history. The oracle records whether the two sources agree |
| Unauthorized changes | Unexpected writable ref tips, extra PR effects, unexpected PR state changes, or a creation response naming the wrong artifact or PR. Scheduled contributor drift is within the fault model |
| False completion | The durable verdict claims completion without an exact matching remote artifact and PR identity at the trial cutoff |
| Explicit unknown | The worker records unresolved effect knowledge in its verdict |
| Safe blocked | The worker stops at a detected conflict, remote history agrees, and no unauthorized effect is observed |
| Recovery time | From launching the first resumed attempt to last worker exit, including a second kill where assigned. Successful recovery latency is recorded only for a verified completion. Final oracle sampling follows the time window |

The drift scenario has a known conflict and is ineligible for automatic completion with its original evidence. No-fault trials measure ordinary completion. In all other scenarios recovery with the original evidence is eligible. Infrastructure failures are retained as ungraded assigned trials, with their errors and trace events. Eligibility and grading definitions apply to the retained run with seed visibility stabilization.

This is one exploratory observation per policy/scenario pairing. The added policy and receipt boundary address questions raised during setup. The endpoint probes and matrix do not provide frequency estimates for distributed races.
