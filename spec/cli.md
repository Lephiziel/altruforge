# Planned CLI contract

These commands are the interface to implement. They are not currently executable.

| Command | Result |
| --- | --- |
| `altruforge doctor [--json]` | Report installed dependencies and supported capabilities |
| `altruforge init [--path PATH]` | Generate a disabled project manifest and local instructions |
| `altruforge validate [--path PATH] [--json]` | Validate project configuration without running project code |
| `altruforge auth github` | Connect the contributor's GitHub account |
| `altruforge auth codex` | Use the provider-supported Codex account flow |
| `altruforge auth status [--json]` | Report connection status without credential values |
| `altruforge auth logout <backend>` | Remove only the connection/session owned by this tool |
| `altruforge projects add <owner/repo>` | Register a selected project locally |
| `altruforge projects list [--json]` | List locally selected projects |
| `altruforge projects remove <owner/repo>` | Remove a local selection without altering upstream |
| `altruforge run <owner/repo> [--max-duration 30m] [--max-attempts 2] [--json]` | Start one bounded contribution run |
| `altruforge status [run-id] [--json]` | Read persisted state and result |
| `altruforge resume <run-id> [--json]` | Explicitly revalidate and resume a recoverable run |
| `altruforge stop <run-id>` | Stop the full job and record cancellation |

## Interaction

Initial account and dependency setup may require user action. After a contributor starts a permitted run, task selection is announced without a routine confirmation prompt.

A materially ambiguous task is skipped or blocked according to policy. The tool does not keep asking the contributor to make the maintainer's product decisions.

## Output and exit codes

JSON mode sends versioned structured output/events to stdout and human diagnostics to stderr. It must be usable without a TTY.

| Code | Meaning |
| --- | --- |
| 0 | Requested operation completed, or a run handed off a Draft PR |
| 2 | Invalid arguments or configuration |
| 3 | No eligible work |
| 4 | Missing account, capability, authorization, or required dependency |
| 5 | Execution, verification, or publication failed |
| 6 | Paused by a recoverable condition such as quota exhaustion |
| 130 | Contributor cancellation after job termination |

A CLI parser error must not be confused with the outcome of an already-created run. Persist the detailed outcome even when the process exits.
