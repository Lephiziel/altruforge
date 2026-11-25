# NIR-03 execution notes

- Source revision: upstream `642f69132848e0671ed9e4547d9a278a7f04f718`; study branch `research/nir-03-p01`.
- Provider: Forgejo 17.0.2, official binary signature verified before use; local loopback listener, SQLite, isolated disposable data and private synthetic repositories.
- Protocol: v1 probes were retained separately. Forgejo's create-PR schema and actual request behavior showed no supported `draft` field, so protocol v2 was committed before the retained matrix and used regular open, unmerged PRs.
- Retained execution: five scenarios × five policies, 25 assignments. No automatic merge API was called. Forgejo Actions and external integrations were disabled.
- Independent evaluation: `evaluate_pilot.py` recomputed outcomes using observer fields. See `evaluation.md` and machine-readable `evaluation.json`.
- Temporary credentials and data were kept outside Git under `/tmp`; no production Harness state or Altruforge runtime state was accessed.
- Early development failures and corrections are preserved in protocol-v1 evidence and Git history. They are disclosed in `evaluation.md`, not silently folded into the final protocol-v2 denominator.
