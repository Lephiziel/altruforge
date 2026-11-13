# Authentication and account ownership

## Contributor accounts

The contributor authenticates with GitHub and their supported coding tool. PRs originate from the contributor's account/fork in the MVP. They are not created from a pooled subscriber identity.

Use supported login flows. Prefer provider-owned authentication handling and OS credential storage over custom token files. GitHub permissions must be limited to the documented operations and public-repository scope required by the MVP.

## Separation

Project workspaces, build workers, task bodies, logs, reports, and submitted artifacts never contain account credentials or authentication directories.

The provider's trusted client may need credentials to make model requests. That does not grant project-controlled commands access to those credentials. MVP-01 must prove the complete boundary, including child processes and environment inheritance, on each target OS.

Do not extract browser cookies, scrape private endpoints, copy OAuth sessions between participants, or silently switch from subscription use to paid API keys.

## Failure and logout

Classify authentication failures, quota exhaustion, unsupported integrations, and revoked credentials. Stop or pause with a clear result. Do not repeatedly retry an invalid account or report an incomplete run as successful.

Logout and project removal must not unexpectedly delete user-owned global provider sessions. Document whether a session is owned by Altruforge or reused from an existing client.

## Provider evidence

Codex is the first adapter. Its documented app-server protocol provides account and session integration. The exact supported version and execution mode belong to MVP-01 evidence.

Additional backends, including Claude, need their own supported-auth and platform evidence. The existence of an SDK does not imply permission to intermediate a subscriber's credentials.
