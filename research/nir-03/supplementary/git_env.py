"""Minimal, deterministic environment for synthetic fixture Git subprocesses."""
from __future__ import annotations

import os
from pathlib import Path


def build_git_environment(
    *,
    token: str,
    token_file: str | Path,
    askpass: str | Path,
    home: str | Path,
) -> dict[str, str]:
    """Return an allowlisted environment with exactly one Git config entry.

    Do not copy the parent environment: inherited GIT_CONFIG_COUNT and indexed
    GIT_CONFIG_KEY_n/VALUE_n variables can silently alter commands or make Git
    reject a sparse configuration. The access token stays in the child process
    environment and is never included in command-line arguments or logs.
    """
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "LC_ALL": "C",
        "TZ": "UTC",
        "GIT_ALLOW_PROTOCOL": "http",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": str(askpass),
        "NIR03_TOKEN_FILE": str(token_file),
        "GIT_AUTHOR_NAME": "NIR-03 S1",
        "GIT_AUTHOR_EMAIL": "nir03-s1@example.invalid",
        "GIT_COMMITTER_NAME": "NIR-03 S1",
        "GIT_COMMITTER_EMAIL": "nir03-s1@example.invalid",
        "GIT_AUTHOR_DATE": "2020-01-01T00:00:00 +0000",
        "GIT_COMMITTER_DATE": "2020-01-01T00:00:00 +0000",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "http.extraheader",
        "GIT_CONFIG_VALUE_0": f"Authorization: token {token}",
    }
    return env


def redact_git_error(stderr: str, token: str) -> str:
    """Remove the credential if a provider/Git diagnostic echoes it."""
    return stderr.replace(token, "[REDACTED]")[-250:]
