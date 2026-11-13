# Project-owned runtime configuration

This directory is the planned self-hosting configuration for Altruforge. `project.yaml` is disabled during bootstrap and validates against [the draft manifest](../spec/project-manifest.md).

The listed Go checks become runnable only after MVP-02 introduces a real Go module. A manifest is not proof that a runtime, coordinator, or executor exists.

Implementation agents must start with [AGENTS.md](../AGENTS.md) and [the backlog](../docs/tasks/README.md). Enable self-hosting only in MVP-16 after the release evidence is available.
