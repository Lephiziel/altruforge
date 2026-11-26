# Infrastructure smoke iteration archive

This separate archive retains the available outputs and Forgejo process logs from infrastructure-only smoke iterations v1–v8. It is not experimental data and is excluded from the S1-R2 14-cell denominator. Iterations v1–v5 were failed setup/smoke attempts; v6 and v7 passed the then-current two-path smoke; v8 passed the final three-path readiness smoke.

The archive contains 104 files (logs, smoke output, capture JSON, and raw bodies), each with a size and SHA-256 in `ARCHIVE-MANIFEST.json`. No credentials or database state are included. A credential-pattern scan returned zero matches; no redactions were needed.

Archive: `infrastructure-smoke-v1-v8.tar.gz`

SHA-256: `4a599c1b8e7a900d7d62ac8ebd0dbb8c34eba181484478049fcaf305e57749c3`

Manifest SHA-256: `ae6e09c21f0a04618713516cfa4ca5d2619caf48097261c3e56d31ad5e5f85fd`

Verify the archive checksum from a checkout of this research branch before reading it:

```sh
sha256sum research/nir-03/supplementary/s1-r2/smoke-attempts/infrastructure-smoke-v1-v8.tar.gz
```

The manifest documents each member's original `/tmp` path. Extract as an unprivileged user into a private directory with `tar -xzf infrastructure-smoke-v1-v8.tar.gz -C <private-directory>` and verify each file against the manifest. These artifacts preserve infrastructure development history only; v8 is the readiness smoke cited by the preregistration amendment.
