# ADR 0003 Authentication and execution boundary

Status: evidence-gated.
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

This gate prevents unsupported architecture from being treated as implemented. It does not require maintainer approval for routine implementation choices.
