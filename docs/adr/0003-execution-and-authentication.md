# ADR 0003 Authentication and execution boundary

Status: evidence-gated (MVP-01 partial observations recorded; candidate revised, decision not accepted).
Date: 2026-11-13.

## Context

A contributor uses their own supported AI account and GitHub identity. Project-controlled code must not gain access to credentials, unrelated personal files, or publication authority. The workflow must operate from Windows, macOS, and Linux.

## Candidate approach

Keep a trusted host supervisor and provider-owned authentication outside worker-readable storage. Integrate Codex through its documented app-server protocol. Use an explicit executor boundary, initially a Linux environment managed through Docker Engine API.

The final supported arrangement of agent file/tool access and command execution must be demonstrated by MVP-01. A raw credential-directory mount into a container is not an acceptable substitute.

Use OS-native process control where needed, and terminate the complete job on cancellation. A future Docker Sandboxes adapter can be added independently; its narrower current host requirements do not make it the sole portable executor.

## Required proof

Supported login; worker denial of credential/personal-file access; controlled network/environment inheritance; bounded execution; interruption; recovery; and one documented route for each target OS family.

The prototype must record provider and executor versions, exact configuration, observed failures, and limitations. No live credentials belong in the repository.

## If the candidate fails

Produce a concrete ADR amendment with a supported alternative and its tradeoffs. Do not silently disable isolation, copy subscriber sessions, introduce API billing, or narrow the required OS scope.

## Evidence outcome and candidate amendment (2026-11-28)

The Linux observations in [MVP-01 evidence](../evidence/MVP-01-boundary.md) used Codex CLI `0.171.0` on Arch Linux x86_64. A real ChatGPT login and non-interactive CLI turn succeeded. Codex's default `workspace-write` mode did not meet the credential boundary: temporary host files and a sentinel environment variable were readable by command and child processes.

The candidate is amended to prefer a Codex-documented `workspace-only` permission profile: extend `:workspace`, deny reads at `:root`, grant `:minimal` runtime reads, and allow writes only in the workspace. Set `shell_environment_policy.inherit = "core"` and `ignore_default_excludes = false`. This profile denied host canary reads and filtered a sentinel environment value from commands and children on the tested Linux host. A temporary JSON-RPC v2 client also completed an app-server turn and invoked the canary probe under this profile. Codex permission profiles are documented as beta. The temporary prototype exercised app-server cancellation, but the Altruforge adapter and production cancellation integration remain unimplemented. The original Docker candidate passed an independent Linux container check but was not connected to Codex tools. These are candidate mechanisms, not acceptance of the product boundary.

Windows 11 Pro build 26200/AMD64 was exercised with Codex CLI `0.171.0`; ChatGPT login succeeded. The strict `:root = deny` profile failed closed before project tools ran: the unelevated sandbox could not enforce split read restrictions, and the elevated sandbox helper required effective `:root` read access at `thread/start`. The profile was not weakened. Thus Windows canary, cancellation, and recovery remain untested; macOS was not exercised. A temporary Linux app-server supervisor probe successfully interrupted the full provider/tool turn, preserved a test checkpoint outside the worker, stopped the child, and resumed the stored thread from a fresh app-server process. This is not the Altruforge production run state machine. Keep this ADR evidence-gated until the full scenarios pass on every required host. The documented native Codex permission profile is the proposed supported alternative to unrestricted host execution; if app-server cannot preserve that boundary, do not ship the adapter and return with a supported provider/executor design rather than weakening the profile.

This gate prevents unsupported architecture from being treated as implemented. It does not require maintainer approval for routine implementation choices.
