# Reproducing and verifying pid-rs 1.0 releases

This procedure separates repository identity, artifact integrity, build provenance, software test
coverage, and scientific validation. None substitutes for the others.

## Trust and tag policy

Repository policy forbids signing commits and Git tags. Release tags are annotated and protected
against update/deletion, but `git tag -v` is therefore expected to report no signature. Do not
weaken or work around that policy during a release.

The release workflow instead:

1. checks out the exact protected `vMAJOR.MINOR.PATCH` ref with persisted credentials disabled;
2. verifies that it is an annotated tag whose Cargo/CFF/docs metadata matches the tag;
3. builds artifacts from that commit with pinned actions and locked dependencies;
4. emits SHA-256 and SHA-512 manifests plus CycloneDX SBOMs; and
5. requests GitHub artifact attestations using short-lived OIDC identity.

Verify a downloaded artifact against both checksum files and the GitHub attestation:

```text
sha256sum --check SHA256SUMS
sha512sum --check SHA512SUMS
gh attestation verify <artifact> --repo sepahead/pid-rs
```

On macOS, use `shasum -a 256 -c SHA256SUMS` and `shasum -a 512 -c SHA512SUMS`.

## Expected release artifacts

- GitHub-generated source archives plus a workflow-created source archive from the tagged tree;
- packaged `pid-runlog` and `pid-core` `.crate` archives;
- `pid-runlog-replay` and `exp0` CLI archives for supported Linux, macOS, and Windows targets;
- stable-ABI `pid-core-rs` wheels for the supported platform/architecture matrix and an sdist;
- SHA-256 and SHA-512 manifests;
- CycloneDX JSON SBOMs for the Rust workspace and Python wheels;
- GitHub/SLSA-compatible provenance attestations;
- per-target build-provenance records plus the independent signed reproduction report and final
  review addendum;
- `CHANGELOG.md`, `KNOWN_LIMITATIONS.md`, the release audit, and this reproduction protocol.

## Clean source-archive reproduction

Start in a disposable environment with Git, GitHub CLI, Rust 1.89, Python 3.11 or newer, and no
repository credentials in the build directory. First confirm the protected tag identity, then
download the `release-source` artifact from the tag workflow and build the workflow-created archive
rather than silently substituting a clone:

```text
git clone --filter=blob:none https://github.com/sepahead/pid-rs.git
cd pid-rs
git fetch --tags --force
git checkout --detach v1.0.0
test "$(git cat-file -t refs/tags/v1.0.0)" = tag
scripts/check-version-coherence.sh v1.0.0
tag_commit="$(git rev-parse refs/tags/v1.0.0^{})"
cd ..
RUN_ID=<tag-release-workflow-run-id>
mkdir pid-rs-source-artifact
gh run download "$RUN_ID" --repo sepahead/pid-rs \
  --name release-source --dir pid-rs-source-artifact
sha256sum pid-rs-source-artifact/pid-rs-1.0.0-source.tar.gz
tar -xzf pid-rs-source-artifact/pid-rs-1.0.0-source.tar.gz
cd pid-rs-1.0.0
scripts/check-version-coherence.sh
test ! -e .git
```

Record the tag’s peeled commit, source-archive hash, and archive environment:

```text
printf '%s\n' "$tag_commit"
sha256sum Cargo.lock
rustc +1.89 --version --verbose
cargo +1.89 --version --verbose
python --version
```

## Rust gates

```text
cargo +1.89 check --locked --workspace
cargo +1.89 check --locked --workspace --all-features
cargo test --locked --workspace --exclude pid-python
cargo test --locked -p pid-core --no-default-features
cargo test --locked -p pid-core --features parallel
cargo test --locked -p pid-core --all-features
cargo test --locked --release -p pid-core --all-features
cargo fmt --all --check
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS="-D warnings" cargo doc --locked -p pid-core --no-default-features --no-deps
RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps
cargo deny --all-features --locked check
```

Run each individual research feature as listed in `MIGRATION.md`; do not use only
`--all-features` as evidence that every boundary compiles independently. Run the deterministic
property suite and fixed fuzz corpus through the CI recipes. Miri/sanitizer jobs are supplemental
because not every numerical/FFI dependency supports them.

Package in dependency order. Before `pid-runlog` is visible on crates.io, a true crates.io
`pid-core` dry run is expected to fail because Cargo verifies versioned dependencies against the
index. The pinned local-registry check nevertheless creates both exact archives, performs Cargo's
normal package verification, and compiles every shipped core target/all features from the unpacked
archive while locked and offline:

```text
cargo install cargo-local-registry --locked --version 0.2.12
scripts/verify-package-archives.sh
cargo publish --locked -p pid-runlog --dry-run
# After pid-runlog 1.0.0 is visible in the target registry:
cargo publish --locked -p pid-core --dry-run
```

## Python gates

Build wheels in clean, platform-native environments; do not treat one local abi3 wheel as the full
platform matrix:

```text
python -m pip install --upgrade "maturin==1.14.1" "numpy==1.26.4" "pytest==9.1.1"
maturin build --release --locked --manifest-path crates/pid-python/Cargo.toml --out dist
python -m pip install --no-index --find-links dist "pid-core-rs==1.0.0"
pytest crates/pid-python/tests -q
python -m pip check
```

Repeat with the current supported CPython and NumPy lines. Inspect every wheel for licenses, SBOM,
`.pyi` stubs, `py.typed`, the intended architecture tag, and the absence of experimental symbols in
the default import. Compare the frozen Rust/Python numerical fixture bits or declared tolerance.

## Independent signed sign-off records

The dependency-order constraint creates two review stages. Before the `pid-runlog` seed exists, the
independent reviewer signs a reproduction report containing:

- tag and peeled commit SHA plus the source archive and lockfile hashes;
- preliminary `pid-runlog` crate, CLI, wheel, sdist, and SBOM hashes;
- compiler/tool versions, target triples, container/image digest, and feature flags;
- tag-CI and release-build workflow URLs;
- analytic and empirical fixtures reproduced, with seeds and generator revisions;
- preliminary package/wheel contents reviewed;
- every exception, unsupported platform, and known failure observed; and
- reviewer identity, date, and a detached OpenPGP signature.

Before approving the first protected-environment job, publish the report, detached signature, and
reviewer public key at immutable HTTPS locations and configure these `release` environment
variables:

```text
REPRODUCTION_REPORT_URL
REPRODUCTION_REPORT_SHA256
REPRODUCTION_SIGNATURE_URL
REPRODUCTION_SIGNATURE_SHA256
REPRODUCTION_SIGNER_KEY_URL
REPRODUCTION_SIGNER_KEY_SHA256
REPRODUCTION_SIGNER_FINGERPRINT
```

The workflow downloads and hashes all three objects, verifies the key fingerprint and detached
signature, and requires the report to name the exact tag, peeled commit, and `Cargo.lock` hash. Do
not upload the reviewer’s private key or put it in repository/environment secrets.

After the first approval publishes the byte-reviewed dependency seed, the workflow builds
`pid-core`, the complete checksum manifests, and the first provenance attestations, then uploads
`final-release-bundle`. The same independent reviewer downloads that artifact, verifies it, and
signs a final addendum containing at minimum:

- the exact tag and peeled commit;
- the `pid-core-1.0.0.crate` SHA-256;
- the SHA-256 of the reviewed pre-approval `SHA256SUMS` manifest;
- final crate/wheel/SBOM/provenance review results; and
- the `gh attestation verify` command/output (the report must include the word `attestation`).

Configure these additional environment variables before the second approval:

```text
FINAL_REVIEW_REPORT_URL
FINAL_REVIEW_REPORT_SHA256
FINAL_REVIEW_SIGNATURE_URL
FINAL_REVIEW_SIGNATURE_SHA256
```

The workflow verifies this addendum with the already-pinned reviewer key, checks the two required
hashes, preserves the reviewed manifests as `PRE_APPROVAL_SHA256SUMS` / `PRE_APPROVAL_SHA512SUMS`,
then regenerates both final checksum manifests to include those manifests and the addendum/signature
and attests the fully approved bundle. The signed report, final addendum, signatures, and public key
become release assets.

The protected `release` GitHub environment must require an independent human reviewer, prevent
self-review, and disallow administrator bypass. The workflow uses it twice: the first approval
verifies the signed reproduction report and permits only the unavoidable `pid-runlog` dependency
seed; the second occurs after `pid-core`, all checksums, provenance, and attestations exist and
permits final publication. Repository **release immutability** must be enabled before the workflow
starts. The workflow creates a draft, attaches the complete verified asset set, then publishes it
so GitHub locks the assets and tag.

PyPI uses its GitHub OIDC trusted publisher. The environment must provide a least-privilege
`CARGO_REGISTRY_TOKEN` secret and a separate fine-grained `RELEASE_SETTINGS_TOKEN` with only
repository Administration-read access, used solely to confirm release immutability before the
first registry write. Configure registry owners/publishers to identify Sepehr Mahmoudian, rotate
the Cargo token after the first-name claim, and never store either token in the source tree. A
retried workflow accepts an already-published crate or Python distribution only when the registry
exposes the exact local filenames and SHA-256 digests; publication existence alone is not treated
as successful verification.
