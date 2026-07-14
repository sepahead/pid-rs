# Security Policy

## Supported versions

Before 1.0, security fixes are shipped on the latest `0.x` review line. Only the latest 0.x minor
receives fixes; older 0.x versions are unsupported. A report that demonstrates a materially wrong
scientific result, a panic/resource-exhaustion path on untrusted input, or an FFI/file-handling flaw
is in scope even when it does not fit a conventional memory-safety category.

| Version | Supported |
|---------|-----------|
| Latest 0.x review release | ✅ |
| Older 0.x releases | ❌ |
| 1.x | Not published yet |

## Reporting a vulnerability

Please **do not** open a public issue for security-sensitive reports.

Instead, use GitHub's [private vulnerability reporting](https://github.com/sepahead/pid-rs/security/advisories/new)
("Report a vulnerability" under the repository's **Security** tab). If that form is unavailable,
email [sepmhn@gmail.com](mailto:sepmhn@gmail.com). Include a description, a minimal reproduction,
and the affected version/commit. Do not include sensitive details in a public issue.

You can expect acknowledgement within three business days and an initial severity/impact assessment
within seven business days. Target remediation is 14 days for critical findings and 30 days for
high-severity findings, subject to coordinated-disclosure constraints and the need to validate
scientific corrections independently. If a target cannot be met, the maintainer will provide a
revised private timeline rather than silently closing the report.

After triage we will work with you on a fix and coordinated disclosure. The core estimator library
`pid-core` is `#![forbid(unsafe_code)]` and has no network or filesystem surface in its library
path, so the most likely classes of issue there are denial-of-service via panics on crafted input
or incorrect numerical results; both are treated seriously. The `pid-python` bindings use PyO3
(FFI) and the `pid-runlog` crate and the `exp0` binary read and write files on disk, so reports
touching those paths are equally in scope.

Published GitHub Releases are immutable and their artifacts carry checksums, SBOMs, and GitHub
build-provenance attestations. Repository policy intentionally uses protected but unsigned Git tags; verify artifacts using
[`RELEASE_REPRODUCTION.md`](RELEASE_REPRODUCTION.md), not `git tag -v`.
