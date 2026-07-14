# pid-rs 0.9.0

Release status: **DRAFT — not yet published**.

Author and maintainer: **Sepehr Mahmoudian**.

pid-rs 0.9.0 will be the first public **review release**. It exposes the deliberately narrow
default surface proposed for 1.0 so reviewers can comment before any 1.x
compatibility promise is made. It is not a claim that every estimator is universally valid.

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

## Forthcoming installation after publication

These commands become valid only after all corresponding public artifacts have been published and
verified:

```text
cargo add pid-core@0.9.0
cargo install pid-runlog --version 0.9.0 --locked --bin pid-runlog-replay
python -m pip install "pid-core-rs==0.9.0"
```

The MSRV is Rust 1.89. The dependency update to nalgebra 0.35/simba 0.10 removes the unmaintained
`paste` dependency and the former cargo-deny exception.

## Before upgrading or publishing a result

- Read [`MIGRATION.md`](MIGRATION.md) for source, feature, support-contract, and Python changes.
- Read [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) for estimator assumptions and unsupported
  regimes.
- Review [`CHANGELOG.md`](CHANGELOG.md) for all numerical and behavior changes.
- Follow [`RELEASE_REPRODUCTION.md`](RELEASE_REPRODUCTION.md) to verify checksums and GitHub
  provenance attestations.

Release tags are protected annotated tags but are intentionally unsigned under repository policy.
Published GitHub Releases use release immutability to lock their tag and assets. Every attached
artifact is covered by SHA-256/SHA-512 manifests and a GitHub build-provenance attestation. An
independent reviewer must reproduce the release candidate before approving the protected `release`
environment.
