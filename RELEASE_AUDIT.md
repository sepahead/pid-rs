# pid-rs 1.0 release-candidate implementation and evidence record

This record maps the 1.0 candidate implementation to the P0 requirements in
`PID_RS_V1_0_FINAL_RELEASE_AUDIT.md`, whose audited input commit was
`70b45f7b75fac06777ea215a73df01209490311a`. The tagged tree, CI run, release workflow, artifacts,
and independent reproduction report are the authoritative completion evidence. Source changes
alone do not close a runtime or external-publication requirement. **No tag, publication, GitHub
Release, registry upload, or other release action is claimed by this document.** Independent review
and all tag-specific evidence remain pending until a maintainer explicitly starts that process.

Release author and maintainer: **Sepehr Mahmoudian**.

## Release boundary

- The approved stable/experimental/unsupported table is prominent in `README.md` and repeated in
  `KNOWN_LIMITATIONS.md`.
- `pid-core` has empty default features and explicit default-off research features. Full
  mixed-dimensional continuous PID3 is compile-time gated.
- The ordinary Python wheel exposes the stable module; experimental bindings require a separately
  requested build feature/namespace.
- Publication-facing continuous use is report-first and records support, configuration,
  provenance, diagnostics, warnings, revision identity, and resource estimates.

## Objective evidence map

| Audit item | Repository evidence | External/tag evidence required before approval |
|---|---|---|
| P0-01/03/04/05 stable scope and quarantine | `crates/pid-core/Cargo.toml`, `src/lib.rs`, default/no-default docs tests, Python import tests | Package/wheel symbol inspection |
| P0-02 shell ties | k=2 rejection, positive-shell ambiguity, independent unique-shell oracle, serial/parallel feature runs, 1/2/3/4/available-thread exact-identity fixtures, and `public_configs_shells` fuzz target | Cross-platform CI result |
| P0-06 quantization | fitted quantizer, serialized edges/occupancy, held-out tests | Rust/Python fixture parity |
| P0-07 reports | stable KSG report (including unclamped signed estimate) and typed Python result | Serialized golden fixture |
| P0-08/09 resources | `ResourceBudget`/preflight APIs, fallible estimator/pipeline/run-log allocations, Standardizer aggregate peak accounting, parallel stack/concurrent-resample accounting, solver quarantine, and boundary fuzzing | Fuzz/coverage CI result |
| P0-10 run log | bounded streaming and decoded-event APIs, typed schema/hash IDs, crash-safe atomic replacement, file sync on all desktop targets, and parent-directory sync on Unix | Cross-platform crash/golden migration tests; Windows power-loss limitation acknowledged |
| P0-11 Python | typed outputs/stubs, owned inputs before GIL release, cooperative core cancellation, signal polling, structured exceptions, and no-orphan worker test | Wheel matrix and cross-platform cancellation/mutation results |
| P0-12 advisory | nalgebra 0.35/simba 0.10, empty cargo-deny ignore list | cargo-deny run with exact lockfile |
| P0-13 CI | `.github/workflows/ci.yml` plus `scripts/verify-package-archives.sh`, which locally seeds the exact packaged `pid-runlog`, performs Cargo's normal `pid-core` package verification, and compiles every target/all features from the exact unpacked core archive while locked/offline | Successful tag CI URL; true crates.io dry run remains release-sequenced |
| P0-14 release | `.github/workflows/release.yml`, checksums/SBOM/attestation policy | Successful protected-environment workflow URL |
| P0-15 known failures | explicit known-failure tests, including deterministic invalid-null AR(1) type-I inflation, and `KNOWN_LIMITATIONS.md` | Exact test output/fixture hashes |
| P0-16 reproduction | `RELEASE_REPRODUCTION.md` | Independent signed report and environment hashes |

## Intentional signed-tag deviation

The audit specification proposed a signed `v1.0.0` tag. The repository’s controlling operational
policy forbids signing commits or tags and sets `tag.gpgsign=false`. The release therefore uses an
**unsigned annotated protected tag**, verifies its exact peeled commit, produces SHA-256/SHA-512
manifests, and requests GitHub OIDC build-provenance attestations for artifacts. This deviation is
visible in the README, security policy, release notes, reproduction guide, and workflow; it must
not be represented as a cryptographically signed Git tag.

## Approval rule

The protected `release` environment is used twice. On the first approval, the independent human
reviewer certifies that:

1. every job in the tag’s complete CI matrix passed at the exact peeled commit;
2. the workflow-created source archive was reproduced using the lockfile;
3. analytic, empirical, known-failure, Rust/Python parity, and artifact-install fixtures passed;
4. the externally hosted report, detached signature, public-key fingerprint, and hashes configured
   on the environment are theirs and name this exact tag/commit/lockfile; and
5. publishing the byte-reviewed `pid-runlog` archive as the dependency seed is approved.

After that seed makes `pid-core` package verification possible, the workflow builds and attests the
complete checksum-covered bundle. On the second approval, the reviewer supplies a detached-signed
final addendum naming the core-crate and checksum-manifest hashes and certifies that package/wheel
contents, SBOMs, provenance subjects, and registry ownership/trusted-publisher configuration were
reviewed, identify Sepehr Mahmoudian’s release, and waive no critical/high finding.

If any statement is false, do not approve the relevant environment gate and do not create the
GitHub Release.
