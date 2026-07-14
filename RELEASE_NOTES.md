# pid-rs 0.9.0

**Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE.**

Author and maintainer: **Sepehr Mahmoudian**.

pid-rs 0.9.0 is the first public **review release**. It exposes the deliberately narrow
default surface proposed for 1.0 so reviewers can comment. It is not a claim
that every estimator is universally valid.

Distribution is GitHub-only: crates.io and PyPI are not published for this 0.9.0 review prerelease.
This 0.9.0 review prerelease makes no 1.x compatibility promise.

This release is authored and maintained solely by Sepehr Mahmoudian. No software DOI or Zenodo
record has been assigned to 0.9.0; the top-level software DOI field intentionally remains absent.

Stable by default:

- direct empirical categorical shared-exclusions PID for two to four sources;
- reusable fitted quantization, explicitly interpreted as PID of the quantized variables;
- Williams–Beer `I_min` as a separately named legacy comparator;
- report-first Euclidean/Chebyshev KSG MI under an explicit regular continuous-law contract; and
- diagnostics, resource preflight, reproducible run logs, and stable Python result types.

Here “stable” names the proposed default module/API disposition; because this is version 0.9, the
surface may still change in response to review before 1.0.

Continuous shared exclusions/PID2, partial/full continuous PID3, hyperbolic KSG, heuristic
methods, hierarchy, and target-adaptive pipelines remain default-off experimental or research-only
features. Hyperbolic shared exclusions/PID and generic calibrated kNN bootstrap intervals remain
unsupported.

## Review distribution boundary

The 0.9.0 release is a GitHub **prerelease for source review**. Its downloadable payload is
limited to the reviewed source archive, the human- and machine-readable proposed-1.0 scope records,
`REVIEW_RELEASE_PROVENANCE.txt`, and SHA-256/SHA-512 checksum manifests. GitHub's automatically
generated source archives remain available as usual.

This prerelease does **not** publish `pid-core` or `pid-runlog` to crates.io, `pid-core-rs` to PyPI,
or 0.9.0 API documentation to docs.rs. It contains no crate archives, wheels, source distribution,
binary bundles, SBOMs, or separately generated build-provenance attestations. Use the
checksum-verified source archive or its exact peeled commit for review; do not use 0.9.0
registry-installation commands.

The MSRV is Rust 1.89. The dependency update to nalgebra 0.35/simba 0.10 removes the unmaintained
`paste` dependency and the former cargo-deny exception.

## Before upgrading or publishing a result

- Read [`MIGRATION.md`](MIGRATION.md) for source, feature, support-contract, and Python changes.
- Read [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) for estimator assumptions and unsupported
  regimes.
- Review [`CHANGELOG.md`](CHANGELOG.md) for all numerical and behavior changes.
- Follow [`RELEASE_REPRODUCTION.md`](RELEASE_REPRODUCTION.md) to verify the tag, source archive,
  scope records, provenance record, and checksums.

The release tag is annotated but intentionally unsigned under repository policy. Earlier
release commits remain reachable through immutable changelog links after obsolete tag refs were
retired; no earlier GitHub Releases existed. GitHub release immutability locks the review tag and
six attached files; the prerelease is not marked as the latest
production release. Immutability automatically generates a cryptographically verifiable GitHub
release attestation for the tag, commit, and assets. The heavyweight registry workflow—with package
and wheel builds, SBOMs, separate build-provenance attestations, detached human sign-off records,
protected-environment approval, and public-registry verification—is reserved for a later qualified
release and is not part of 0.9.0.
