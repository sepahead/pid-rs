# Security Policy

## Supported versions

pid-rs is pre-1.0. Security fixes are applied to the latest `0.x` release.

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |

## Reporting a vulnerability

Please **do not** open a public issue for security-sensitive reports.

Instead, use GitHub's [private vulnerability reporting](https://github.com/sepehrmn/pid-rs/security/advisories/new)
("Report a vulnerability" under the repository's **Security** tab). Include a description, a
minimal reproduction, and the affected version/commit.

You can expect an initial acknowledgement within a few days. Since `pid-core` is
`#![forbid(unsafe_code)]` and has no network or filesystem surface in the library path, the most
likely classes of issue are denial-of-service via panics on crafted input or incorrect numerical
results; both are treated seriously.
