# S1-R2 raw observer archive

The archive stores byte-for-byte copies of all 30 observer capture JSON documents and 120 raw response bodies from `/tmp/nir03-s1-r2-run-20261126/captures/`. It was verified against the preexisting `../raw-capture-index.json` before archival. No files were redacted or normalized.

## Integrity and access

Archive: `nir03-s1-r2-raw-observer-captures.tar.gz`

SHA-256: `31954a6564acebcd3cb4161874e9404defd80bf1a73dc239c4bf984cafeafc10`

Manifest: [`ARCHIVE-MANIFEST.json`](ARCHIVE-MANIFEST.json)

Manifest SHA-256: `5724faf81ecb25dd0af995a72d3756963a5d6ff0b5ee7647de3614c5c6807257`

From a fresh checkout of PR #29, verify the archive before extraction:

```sh
cd research/nir-03/supplementary/s1-r2/archive
sha256sum nir03-s1-r2-raw-observer-captures.tar.gz
```

Compare the output with the SHA-256 above and the archive manifest. Extract as an unprivileged user into a private directory:

```sh
mkdir -m 700 /tmp/nir03-s1-r2-archive-read
tar -xzf nir03-s1-r2-raw-observer-captures.tar.gz \
  -C /tmp/nir03-s1-r2-archive-read
```

The archive places files under `raw-captures/`. The manifest maps every archive member to the original absolute path and gives its size and SHA-256. Capture JSON documents retain their original `/tmp` `raw_body_file` strings; use the manifest's `archive_member` mapping to find each body in the extracted archive. To verify all extracted members, compare each manifest entry's size and SHA-256.

## Content review

Before archival, all 150 files matched the existing capture index and every body digest referenced by each JSON document matched its indexed body entry. The automated scan found no authorization, proxy-authorization, cookie, set-cookie, password, access-token, refresh-token, secret fields; no bearer-token or JWT-shaped strings; and no sensitive personal data. The only email-like values are generated test identities: `nir03-s1@example.invalid`, `researcher@localhost`, and `researcher@noreply.127.0.0.1`. No redactions were needed. The archive contains synthetic repository names, generated commit IDs, timestamps, Forgejo API responses, and local loopback endpoint addresses.

The archive is retained as a research artifact in this Git repository. Access follows the repository's existing PR/repository access controls. Do not replace the original capture index or results with normalized copies.
