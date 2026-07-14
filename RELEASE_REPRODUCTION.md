# Reproducing and verifying the pid-rs 0.9 GitHub review prerelease

Release status: **CANDIDATE.** No `v0.9.0` tag or GitHub prerelease is claimed by this source tree.
The metadata remains deliberately undated and the changelog entry remains unreleased until the
source-review prerelease is intentionally created.

This protocol separates repository identity, byte integrity, software test coverage, and
scientific review. None substitutes for the others.

## 0.9 distribution boundary

The intended 0.9.0 publication is a GitHub-only source prerelease for external review. In addition
to GitHub's automatically generated source archives, its attached files are limited to:

- `pid-rs-0.9.0-source.tar.gz`, produced from the exact tagged tree;
- `release-scope-1.0.json`, the machine-readable proposed 1.0 boundary;
- `RELEASE_SCOPE_1_0.md`, the rendered scope for human review;
- `REVIEW_RELEASE_PROVENANCE.txt`, recording the tag, peeled commit, workflow run,
  `SOURCE_DATE_EPOCH`, `Cargo.lock` and scope hashes, and tool versions;
- `SHA256SUMS`; and
- `SHA512SUMS`.

The checksum manifests cover the four attached payload files above them. They do not authenticate
GitHub's separately generated convenience archives.

Version 0.9.0 is **not** published to crates.io or PyPI, and docs.rs therefore does not publish
0.9.0 API documentation. The prerelease has no `.crate` files, wheels, Python source distribution,
binary archives, SBOMs, or separately generated build-provenance attestations. It also has no
software DOI or Zenodo record. Those omissions are intentional and must not be described as missing
assets.

Earlier pre-review tag refs were retired during repository cleanup. Their peeled commits remain in
Git history and the changelog uses immutable commit-ID links; no earlier GitHub Releases existed.
Creating `v0.9.0` establishes the current source-review reference.

## Trust and tag policy

Repository policy forbids signing commits and Git tags. The intended `v0.9.0` tag is annotated and
deliberately unsigned, so `git tag -v v0.9.0` is expected to report no signature. Do not weaken or
work around that policy.

The GitHub tag/ref and HTTPS release page establish the repository context. The checksum manifests
then detect corruption or substitution among downloaded attached files, but checksums alone do not
prove who created them. The provenance record makes the release inputs inspectable; it is not a
signature or build-provenance attestation. Reviewers should record the release URL, peeled commit,
and checksum-manifest hashes in their own trusted notes when a durable external anchor is required.

Before dispatch, an administrator must verify
[GitHub release immutability](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
through the repository-settings API and pass the workflow's exact `ENABLED` acknowledgement. This
preflight is intentionally performed outside Actions because the settings endpoint requires
Administration read permission, which `GITHUB_TOKEN` cannot request. The secret-free workflow then
verifies that the published prerelease, its tag, and its six attached files are immutable. GitHub
automatically creates a cryptographically verifiable release attestation containing the release
tag, commit SHA, and assets; the documented
[`gh release` verification commands](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/verify-release-integrity)
validate that record. This is not a build-provenance attestation or a human scientific sign-off. The
workflow also leaves the prerelease out of GitHub's “latest release” slot.

The authorized operator preflight and dispatch are:

```text
test "$(gh api \
  --header 'X-GitHub-Api-Version: 2026-03-10' \
  repos/sepahead/pid-rs/immutable-releases --jq '.enabled')" = true
gh workflow run review-release.yml --repo sepahead/pid-rs --ref main \
  -f tag=v0.9.0 -f immutability_preflight=ENABLED
```

The workflow accepts only `v0.9.0`, requires its tag to directly annotate the exact dispatch-time
`main` commit, and requires the successful tag-push CI run for that same commit before it drafts any
release.

## Verify the published prerelease and attached files

Run these commands only after the GitHub prerelease exists:

```text
mkdir pid-rs-0.9.0-review
cd pid-rs-0.9.0-review
gh release view v0.9.0 --repo sepahead/pid-rs \
  --json tagName,isDraft,isPrerelease,name
gh release download v0.9.0 --repo sepahead/pid-rs
test "$(gh api repos/sepahead/pid-rs/releases/tags/v0.9.0 --jq '.immutable')" = true
gh release verify v0.9.0 --repo sepahead/pid-rs

test -f pid-rs-0.9.0-source.tar.gz
test -f release-scope-1.0.json
test -f RELEASE_SCOPE_1_0.md
test -f REVIEW_RELEASE_PROVENANCE.txt
test -f SHA256SUMS
test -f SHA512SUMS
sha256sum --check SHA256SUMS
sha512sum --check SHA512SUMS
for asset in pid-rs-0.9.0-source.tar.gz release-scope-1.0.json \
  RELEASE_SCOPE_1_0.md REVIEW_RELEASE_PROVENANCE.txt SHA256SUMS SHA512SUMS; do
  gh release verify-asset v0.9.0 "$asset" --repo sepahead/pid-rs
done
```

On macOS, use `shasum -a 256 -c SHA256SUMS` and
`shasum -a 512 -c SHA512SUMS`. Confirm that `isDraft` is `false`, `isPrerelease` is `true`, the
release is not GitHub's latest production release, and the asset list contains exactly the six files
above—with no package, wheel, binary, SBOM, or separately uploaded build-provenance payload.

## Verify tag and source identity

Clone independently rather than trusting an existing working tree:

```text
git clone --filter=blob:none https://github.com/sepahead/pid-rs.git repository
git -C repository fetch --tags --force
test "$(git -C repository cat-file -t refs/tags/v0.9.0)" = tag
tag_commit="$(git -C repository rev-parse refs/tags/v0.9.0^{commit})"
printf '%s\n' "$tag_commit"
git -C repository show --no-patch --format=fuller refs/tags/v0.9.0
git -C repository tag --list 'v*' --sort=version:refname
```

The peeled commit must exactly match `REVIEW_RELEASE_PROVENANCE.txt`. The only version tag should be
`v0.9.0`; earlier release commits remain reachable through `CHANGELOG.md`'s immutable commit-ID
links. Inspect the provenance record and independently recompute the recorded lock and scope hashes:

```text
sha256sum repository/Cargo.lock
sha256sum repository/release-scope-1.0.json
sha256sum repository/RELEASE_SCOPE_1_0.md
cmp release-scope-1.0.json repository/release-scope-1.0.json
cmp RELEASE_SCOPE_1_0.md repository/RELEASE_SCOPE_1_0.md
```

Use `shasum -a 256` instead of `sha256sum` on macOS.

Verify that the attached archive contains exactly the tagged source tree, not merely files that
look similar:

```text
mkdir attached-source tagged-source
tar -xzf pid-rs-0.9.0-source.tar.gz -C attached-source
git -C repository archive --format=tar --prefix=pid-rs-0.9.0/ "$tag_commit" \
  | tar -xf - -C tagged-source
diff -qr tagged-source/pid-rs-0.9.0 attached-source/pid-rs-0.9.0
test ! -e attached-source/pid-rs-0.9.0/.git
```

Before extraction in a security-sensitive environment, inspect `tar -tzf` output and reject
absolute paths, `..` components, or unexpected links.

## Re-run source checks

The scope records are proposals for review, not evidence that all listed 1.0 blockers are closed.
From the independent tagged checkout, verify their coherence and pinned public-API projections:

```text
cd repository
git checkout --detach "$tag_commit"
python3 scripts/check-release-scope.py
scripts/check-release-scope-self-test.sh
scripts/check-public-api-snapshots.sh
scripts/check-public-api-snapshots-self-test.sh
```

Run the software gates from either the detached checkout or the verified attached source tree:

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
RUSTDOCFLAGS="-D warnings" cargo rustdoc --locked -p pid-core --all-features --lib -- --cfg docsrs
RUSTDOCFLAGS="-D warnings" cargo rustdoc --locked -p pid-runlog --all-features --lib -- --cfg docsrs
cargo deny --all-features --locked check
```

The last two rustdoc commands exercise the docs.rs configuration locally; they do not imply that
docs.rs has published this version. Run each individual research feature listed in `MIGRATION.md`,
the deterministic property/fuzz corpus, and the platform matrix when reproducing the complete CI
claim.

The Python extension can also be built and tested from source without publishing a distribution:

```text
python -m pip install maturin numpy pytest
maturin develop --release --locked -m crates/pid-python/Cargo.toml
pytest crates/pid-python/tests -q
```

## Interpreting the review

Passing these commands proves only the covered implementation and packaging properties at the
recorded source commit. It does not approve the proposed 1.0 boundary, establish universal
estimator validity, close blockers listed in `release-scope-1.0.json`, or begin a 1.x compatibility
promise. Reviewers should read `KNOWN_LIMITATIONS.md`, `MIGRATION.md`, `RELEASE_AUDIT.md`, and the
scope records before commenting.

## Reserved later registry qualification

The heavyweight publication path is deliberately outside the 0.9 source prerelease. A later,
separately approved registry release must qualify its own exact version, tag, commit, lockfile, and
artifacts before any upload. That process includes, at minimum:

1. the complete cross-platform Rust, Python, package-content, scientific-fixture, supply-chain,
   and known-failure matrices on the exact candidate commit;
2. reproducible `.crate`, wheel, source-distribution, and binary builds plus CycloneDX SBOMs;
3. an independent reproduction report and final addendum with detached human signatures (while
   repository commits and tags remain unsigned);
4. checksum manifests and GitHub OIDC provenance attestations covering the reviewed artifacts;
5. protected-environment approvals that prevent self-review and administrator bypass;
6. byte-for-byte verification of any already-published dependency seed before continuation;
7. least-privilege crates.io and PyPI publishing, followed by public digest and ownership checks;
8. docs.rs build verification for the published Rust crates; and
9. publication of the GitHub Release only after all registry and artifact checks succeed.

The registry workflow and its signed-review requirements are retained for that later qualification;
they must not be invoked or cited as completed evidence for `v0.9.0`.
