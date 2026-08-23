# Development tasks for pid-rs — executable mirror of the canonical commands in AGENTS.md.
# Install `just`: https://github.com/casey/just   (then run `just` to list recipes)

# List available recipes
default:
    @just --list

# Full workspace test suite (pid-python is tested via maturin; see `py-test`)
test:
    cargo test --locked --workspace --exclude pid-python

# Approved stable/default surface (default features are intentionally empty)
test-stable:
    cargo test --locked -p pid-core --no-default-features

# The exact data-parallel kNN path (must stay bit-identical to serial)
test-parallel:
    cargo test --locked -p pid-core --features parallel

# Every default-off experimental/research surface
test-all-features:
    cargo test --locked -p pid-core --all-features

# Release-mode numerical fixtures
test-release:
    cargo test --locked --release -p pid-core --all-features

# Format check + clippy (mirrors CI's lint gate — the whole workspace, pid-python included;
# clippy is check-based and never links libpython)
lint:
    cargo fmt --all --check
    cargo clippy --locked --workspace --all-targets --all-features -- -D warnings

# Auto-format the tree
fmt:
    cargo fmt --all

# Build docs with warnings denied, then the docs.rs `--cfg docsrs` gate
# (`--lib` is required: cargo refuses to forward rustdoc args to more than one target)
doc:
    RUSTDOCFLAGS="-D warnings" cargo doc --locked -p pid-core --no-default-features --no-deps
    RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps
    RUSTDOCFLAGS="-D warnings" cargo rustdoc --locked -p pid-core --all-features --lib -- --cfg docsrs
    RUSTDOCFLAGS="-D warnings" cargo rustdoc --locked -p pid-runlog --all-features --lib -- --cfg docsrs

# Estimator benchmarks
bench:
    cargo bench -p pid-core

# Supply-chain audit (advisories + licenses + bans + sources).
# --all-features so the `parallel` (rayon) dependency subtree is scanned, matching CI;
# top-level cargo-deny flags go BEFORE the `check` subcommand.
deny:
    cargo deny --all-features --locked check

# The worked examples
examples:
    cargo run --locked --release -p pid-core --features experimental-continuous --example ksg_and_pid
    cargo run --locked --release --example discrete_sxpid

# exp0 diagnostic + run-log round-trip smoke
smoke:
    cargo run --locked -p pid-core --all-features --bin exp0 -- --seeds 1 --summary-json /tmp/summary.json --runlog /tmp/run.jsonl
    cargo run --locked -p pid-runlog --bin pid-runlog-replay -- --validate /tmp/run.jsonl

# Build + test the Python bindings via maturin (needs: pip install maturin numpy pytest)
py-test:
    maturin develop --release --locked -m crates/pid-python/Cargo.toml
    pytest crates/pid-python/tests -q

# Version coherence (Cargo workspace version == CITATION.cff; CI also runs a tag mode on tag pushes)
version-check:
    scripts/check-current-release-state.sh
    scripts/check-release-state-self-test.sh
    python3 scripts/check-software-identity.py
    python3 scripts/check-software-identity-self-test.py
    python3 scripts/check-method-catalog.py
    python3 scripts/check-method-catalog-self-test.py
    python3 scripts/check-ecosystem-capabilities.py
    python3 scripts/check-ecosystem-capabilities-self-test.py
    scripts/check-handoff-intake.py
    scripts/check-handoff-intake-self-test.py
    python3 scripts/generate-finite-alphabet-plugin-oracle.py
    python3 scripts/generate-dependency-colored-sxpid-oracle.py
    python3 scripts/generate-support-change-tolerant-sxpid-oracle.py
    python3 scripts/generate-ksg-local-arithmetic-oracle.py
    python3 scripts/generate-sxpid2-exhaustive-oracle.py
    python3 scripts/check-markdown-math.py
    python3 scripts/check-markdown-math-self-test.py
    python3 scripts/check-review-evidence.py
    python3 scripts/check-review-evidence-self-test.py
    python3 -I -S -B scripts/check-source-errata.py
    python3 -O -I -S -B scripts/check-source-errata.py
    python3 -I -S -B scripts/check-source-errata-self-test.py
    python3 -O -I -S -B scripts/check-source-errata-self-test.py
    python3 -I -S -B scripts/check-assurance-registry-typed-view-v1.py
    python3 -O -I -S -B scripts/check-assurance-registry-typed-view-v1.py
    python3 -I -S -B scripts/check-assurance-registry-typed-view-v1-self-test.py
    python3 -O -I -S -B scripts/check-assurance-registry-typed-view-v1-self-test.py
    python3 -I -S -B scripts/check-methods-summary.py
    python3 -O -I -S -B scripts/check-methods-summary.py
    python3 -I -S -B scripts/check-methods-summary-self-test.py
    python3 -O -I -S -B scripts/check-methods-summary-self-test.py
    python3 -I -S -B scripts/check-pid-mathematical-audit-protocol.py
    python3 -O -I -S -B scripts/check-pid-mathematical-audit-protocol.py
    python3 -I -S -B scripts/check-pid-mathematical-audit-protocol-self-test.py
    python3 -O -I -S -B scripts/check-pid-mathematical-audit-protocol-self-test.py
    python3 -I -S -B scripts/check-current-source-state-v1.py
    python3 -O -I -S -B scripts/check-current-source-state-v1.py
    python3 -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -O -I -S -B scripts/check-current-source-state-v1-self-test.py
    scripts/collect-repository-snapshot.py --validate audit/evidence/repository-snapshot.json
    scripts/check-repository-snapshot-self-test.sh
    scripts/repin-pidrs-self-test.sh
    scripts/check-release-scope.py
    scripts/check-release-scope-self-test.sh

# From a clean committed checkout, emit and replay deterministic identity bytes through standard
# streams. The shell owns temporary storage; the v2 artifact makes no storage-custody claim.
post-commit-source-state:
    #!/usr/bin/env bash
    set -euo pipefail
    set -o noclobber
    umask 077
    artifact_dir="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-post-commit-source-state.XXXXXX")"
    artifact="$artifact_dir/post-commit-source-state-v2.json"
    python3 -I -S -B scripts/check-post-commit-source-state-v2.py --emit > "$artifact"
    python3 -O -I -S -B scripts/check-post-commit-source-state-v2.py --emit > "$artifact.optimized"
    cmp "$artifact" "$artifact.optimized"
    python3 -I -S -B scripts/check-post-commit-source-state-v2.py --validate-stdin < "$artifact"
    python3 -O -I -S -B scripts/check-post-commit-source-state-v2.py --validate-stdin < "$artifact"
    python3 -I -S -B scripts/check-post-commit-source-state-v2-self-test.py
    python3 -O -I -S -B scripts/check-post-commit-source-state-v2-self-test.py
    printf 'post-commit source-state artifact: %s\n' "$artifact"

# Rebuild all frozen pid-core public API profiles (requires cargo-public-api 0.52.0 and the
# pinned nightly recorded in release-scope-1.0.json).
api-snapshots:
    scripts/check-public-api-snapshots.sh
    scripts/check-public-api-snapshots-self-test.sh

# Bounded exact-real PID2 and PID3 algebra obligations (requires Z3 4.16.0, 64-bit CLI).
# The target keeps its original name as a compatibility route.
formal-pid2:
    python3 scripts/check-z3-pid2-algebra.py
    python3 scripts/check-z3-pid2-algebra-self-test.py

# Bounded positive-integer KSG/Ehrlich arithmetic and fail-closed candidate custody.
# The unscoped main checker is intentionally omitted while the active packet is integration_no_go.
ksg-revision:
    python3 scripts/generate-ksg-local-arithmetic-oracle.py
    python3 -O scripts/generate-ksg-local-arithmetic-oracle.py
    python3 scripts/check-ksg-harmonic-exact-enclosure.py
    python3 -O scripts/check-ksg-harmonic-exact-enclosure.py
    python3 scripts/check-ksg-harmonic-exact-enclosure-self-test.py
    python3 -O scripts/check-ksg-harmonic-exact-enclosure-self-test.py
    python3 scripts/generate-ksg-harmonic-modular-certificate.py
    python3 -O scripts/generate-ksg-harmonic-modular-certificate.py
    python3 scripts/check-ksg-harmonic-modular-certificate.py
    python3 -O scripts/check-ksg-harmonic-modular-certificate.py
    python3 scripts/check-ksg-harmonic-modular-certificate-self-test.py
    python3 -O scripts/check-ksg-harmonic-modular-certificate-self-test.py
    python3 scripts/check-ksg-harmonic-revision.py --claim-only
    python3 -O scripts/check-ksg-harmonic-revision.py --claim-only
    python3 scripts/check-ksg-harmonic-revision-self-test.py --claim-only
    python3 -O scripts/check-ksg-harmonic-revision-self-test.py --claim-only
    python3 scripts/check-ksg-harmonic-revision-self-test.py
    python3 -O scripts/check-ksg-harmonic-revision-self-test.py
    python3 -I -S -B scripts/check-ksg-m1a-phase.py --validate-policy-only
    python3 -O -I -S -B scripts/check-ksg-m1a-phase.py --validate-policy-only
    python3 -I -S -B scripts/check-ksg-m1a-phase-self-test.py
    python3 -O -I -S -B scripts/check-ksg-m1a-phase-self-test.py
    # BEGIN KSG_M1A_HOSTED_RECOVERY_JUST_V1
    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery.py --validate-policy-only --allow-provisional-diagnostic
    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery.py --validate-policy-only --allow-provisional-diagnostic
    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    # END KSG_M1A_HOSTED_RECOVERY_JUST_V1
    scripts/check-ksg-c3-checkpoint.sh

# This gate is intentionally red until every integration gate is closed and the packet is promoted.
ksg-integration-decision:
    python3 scripts/check-ksg-harmonic-revision.py
    python3 -O scripts/check-ksg-harmonic-revision.py

# Conditional exact-arithmetic routes (requires the pinned Lean/Mathlib and Z3 4.16.0).
formal-ksg-harmonic:
    python3 scripts/check-lean-ksg-integer-harmonic.py
    python3 -O scripts/check-lean-ksg-integer-harmonic.py
    python3 scripts/check-lean-ksg-integer-harmonic-self-test.py
    python3 -O scripts/check-lean-ksg-integer-harmonic-self-test.py
    python3 scripts/check-z3-ksg-integer-harmonic.py
    python3 -O scripts/check-z3-ksg-integer-harmonic.py
    python3 scripts/check-z3-ksg-integer-harmonic-self-test.py
    python3 -O scripts/check-z3-ksg-integer-harmonic-self-test.py

# Standalone fixed-kernel regression/custody packet. These are local source plus positive/negative
# policy/custody controls only: Darwin has reviewed pins requiring a later strict replay, Linux is
# hosted_pending, and no live archive or real nested regression runs. This standalone packet keeps
# its historical Lean 4.32.0 baseline; the active scientific project is separately frozen at 4.33.0.
lean-kernel-14576-packet:
    python3 -I -S -B scripts/check-lean-kernel-14576-self-test.py
    python3 -O -I -S -B scripts/check-lean-kernel-14576-self-test.py
    python3 -I -S -B scripts/check-lean-toolchain-custody-self-test.py
    python3 -O -I -S -B scripts/check-lean-toolchain-custody-self-test.py

# Require exactly one compiled W1/W1b/W2/W2b witness and one exact successful harness summary.
ksg-witnesses:
    #!/usr/bin/env bash
    set -euo pipefail
    require_summary() {
      local expected="$1"
      local label="$2"
      local output="$3"
      local summary_count
      summary_count="$(printf '%s\n' "$output" | \
        grep -Ec "^test result: ok\\. ${expected} passed; 0 failed; 0 ignored; 0 measured; [0-9]+ filtered out; finished in [^;]+s$" || true)"
      if [[ "$summary_count" -ne 1 ]]; then
        printf '%s\n' "$output" >&2
        printf 'expected one exact successful %s-test harness summary for %s, observed %s\n' \
          "$expected" "$label" "$summary_count" >&2
        exit 1
      fi
    }
    run_witness() {
      local label="$1"
      local test_name="$2"
      shift 2
      local listing count output
      listing="$(cargo test "$@" "$test_name" -- --list 2>&1)"
      count="$(printf '%s\n' "$listing" | grep -c ': test$' || true)"
      if [[ "$count" -ne 1 ]]; then
        printf '%s\n' "$listing" >&2
        printf 'expected one %s witness, observed %s\n' "$label" "$count" >&2
        exit 1
      fi
      output="$(cargo test "$@" "$test_name" -- --exact 2>&1)"
      printf '%s\n' "$output"
      require_summary 1 "$label" "$output"
    }
    for profile in debug release; do
      profile_args=(--locked)
      if [[ "$profile" == release ]]; then
        profile_args+=(--release)
      fi
      run_witness "W1 $profile" \
        ksg::tests::ksg_ordered_count_witness_reaches_production_diagnostics \
        "${profile_args[@]}" -p pid-core --all-features --lib
      run_witness "W1b predecessor $profile" \
        ksg::tests::ksg_strict_radius_predecessor_reaches_both_backends \
        "${profile_args[@]}" -p pid-core --all-features --lib
      run_witness "W1b predecessor swapped $profile" \
        ksg::tests::ksg_strict_radius_predecessor_preserves_swapped_ordered_counts \
        "${profile_args[@]}" -p pid-core --all-features --lib
      run_witness "W1b xblocks $profile" \
        ksg::tests::xblocks_strict_radius_predecessor_reaches_both_backends \
        "${profile_args[@]}" -p pid-core --all-features --lib
      run_witness "W1b xblocks swapped $profile" \
        ksg::tests::xblocks_strict_radius_predecessor_preserves_selected_bits_when_marginals_swap \
        "${profile_args[@]}" -p pid-core --all-features --lib
      run_witness "W1b overflow parity $profile" \
        ksg::kdtree_parity_tests::overflowing_coordinate_span_returns_numerical_instability_on_both_backends \
        "${profile_args[@]}" -p pid-core --all-features --lib
      run_witness "W2 $profile" \
        isx::tests::ehrlich_inclusive_counts_reach_the_exact_integer_harmonic_local_term \
        "${profile_args[@]}" -p pid-core --all-features --lib
      run_witness "W2b $profile" \
        isx::tests::ehrlich_all_unique_rows_attain_the_structural_zero_count_endpoint \
        "${profile_args[@]}" -p pid-core --all-features --lib
    done

# Assert the serial test binary is nonempty before crediting debug/release parallel equality.
ksg-parity:
    #!/usr/bin/env bash
    set -euo pipefail
    run_profile() {
      local label="$1"
      shift
      local listing count output summary_count
      listing="$(cargo test "$@" -- --list 2>&1)"
      count="$(printf '%s\n' "$listing" | grep -c ': test$' || true)"
      if [[ "$count" -ne 12 ]]; then
        printf '%s\n' "$listing" >&2
        printf 'expected 12 parallel_bit_identity tests for %s, observed %s\n' \
          "$label" "$count" >&2
        exit 1
      fi
      output="$(cargo test "$@" 2>&1)"
      printf '%s\n' "$output"
      summary_count="$(printf '%s\n' "$output" | \
        grep -Ec "^test result: ok\\. 12 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in [^;]+s$" || true)"
      if [[ "$summary_count" -ne 1 ]]; then
        printf 'expected one exact 12-test successful harness summary for %s, observed %s\n' \
          "$label" "$summary_count" >&2
        exit 1
      fi
    }
    run_profile serial-debug \
      --locked -p pid-core --no-default-features \
      --features experimental-pipelines --test parallel_bit_identity
    run_profile serial-release \
      --locked --release -p pid-core --no-default-features \
      --features experimental-pipelines --test parallel_bit_identity
    run_profile parallel-debug \
      --locked -p pid-core --no-default-features \
      --features experimental-pipelines,parallel --test parallel_bit_identity
    run_profile parallel-release \
      --locked --release -p pid-core --no-default-features \
      --features experimental-pipelines,parallel --test parallel_bit_identity

# Deterministic finite-alphabet convergence core (frozen Lean 4.33.0 and pinned mathlib closure).
formal-finite-convergence:
    python3 scripts/check-lean-finite-convergence.py
    python3 -O scripts/check-lean-finite-convergence.py
    python3 scripts/check-lean-finite-convergence-self-test.py
    python3 -O scripts/check-lean-finite-convergence-self-test.py

# Fail-closed active Lean freeze/replay and historical-evidence custody.
lean-toolchain-freeze:
    python3 -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py

# Append-only KSG M1a composite-v4 contract, offline transport controls, and process PDF.
# Historical C4 validation only: its hosted qualification failed and R4 is permanently unissued.
# The checker requires a clean committed tree, so all result files live outside the repository.
ksg-composite-v4:
    #!/usr/bin/env bash
    set -euo pipefail
    umask 077
    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v4.XXXXXX")"
    trap 'rm -rf -- "$result_root"' EXIT
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v4.py --self-test > "$result_root/capture.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v4.py --self-test > "$result_root/capture.optimized.json"
    cmp "$result_root/capture.json" "$result_root/capture.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v4.py --validate-static > "$result_root/static.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v4.py --validate-static > "$result_root/static.optimized.json"
    cmp "$result_root/static.json" "$result_root/static.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v4-self-test.py > "$result_root/self-test.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v4-self-test.py > "$result_root/self-test.optimized.json"
    cmp "$result_root/self-test.json" "$result_root/self-test.optimized.json"
    scripts/check-ksg-m1a-composite-v4-process-pdf.sh --exact

# Append-only composite-v5 successor: five C4 failure-surface controls, fresh r10 custody,
# no-credit predecessor capture semantics, and the conditional C5-to-R5 contract.
ksg-composite-v5:
    #!/usr/bin/env bash
    set -euo pipefail
    umask 077
    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v5.XXXXXX")"
    trap 'rm -rf -- "$result_root"' EXIT
    python3 -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    python3 -O -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    scripts/check-release-state-self-test.sh
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.json"
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.optimized.json"
    cmp "$result_root/zeta.json" "$result_root/zeta.optimized.json"
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    scripts/check-ksg-m1a-composite-v5-boundary-pdf.sh --exact
    scripts/check-ksg-m1a-composite-v5-boundary-pdf-self-test.sh
    python3 -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -I -S -B scripts/check-current-source-state-v1.py
    python3 -O -I -S -B scripts/check-current-source-state-v1.py
    python3 -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -O -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v5.py --self-test > "$result_root/capture.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v5.py --self-test > "$result_root/capture.optimized.json"
    cmp "$result_root/capture.json" "$result_root/capture.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v5.py --validate-static > "$result_root/static.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v5.py --validate-static > "$result_root/static.optimized.json"
    cmp "$result_root/static.json" "$result_root/static.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v5-self-test.py > "$result_root/self-test.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v5-self-test.py > "$result_root/self-test.optimized.json"
    cmp "$result_root/self-test.json" "$result_root/self-test.optimized.json"

# Append-only composite-v6 successor: immutable-v4/v5 keyed PDF portability,
# one bounded C5 association-rule repair, fresh r11 custody, and conditional R6.
ksg-composite-v6:
    #!/usr/bin/env bash
    set -euo pipefail
    umask 077
    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v6.XXXXXX")"
    trap 'rm -rf -- "$result_root"' EXIT
    python3 -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    python3 -O -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    scripts/check-release-state-self-test.sh
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.json"
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.optimized.json"
    cmp "$result_root/zeta.json" "$result_root/zeta.optimized.json"
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v6-local-closure.py --self-test > "$result_root/local-closure-self-test.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v6-local-closure.py --self-test > "$result_root/local-closure-self-test.optimized.json"
    cmp "$result_root/local-closure-self-test.json" "$result_root/local-closure-self-test.optimized.json"
    scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --exact
    scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --exact
    python3 -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -I -S -B scripts/check-current-source-state-v1.py
    python3 -O -I -S -B scripts/check-current-source-state-v1.py
    python3 -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -O -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v6.py --self-test > "$result_root/capture.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v6.py --self-test > "$result_root/capture.optimized.json"
    cmp "$result_root/capture.json" "$result_root/capture.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v6.py --validate-static > "$result_root/static.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v6.py --validate-static > "$result_root/static.optimized.json"
    cmp "$result_root/static.json" "$result_root/static.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v6-self-test.py > "$result_root/self-test.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v6-self-test.py > "$result_root/self-test.optimized.json"
    cmp "$result_root/self-test.json" "$result_root/self-test.optimized.json"

# Retained historical composite-v7 self-check authority. C7 later failed two hosted routes;
# this callable recipe grants zero qualification credit and cannot issue permanently-unissued R7.
ksg-composite-v7:
    #!/usr/bin/env bash
    set -euo pipefail
    umask 077
    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v7.XXXXXX")"
    trap 'rm -rf -- "$result_root"' EXIT
    command -v rg >/dev/null
    rg --version >/dev/null
    python3 -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    python3 -O -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    scripts/check-release-state-self-test.sh
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.json"
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.optimized.json"
    cmp "$result_root/zeta.json" "$result_root/zeta.optimized.json"
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v7-local-closure.py --self-test > "$result_root/local.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v7-local-closure.py --self-test > "$result_root/local.optimized.json"
    cmp "$result_root/local.json" "$result_root/local.optimized.json"
    scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --exact
    scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --exact
    scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh --exact
    scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh --exact
    python3 -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -I -S -B scripts/check-current-source-state-v1.py
    python3 -O -I -S -B scripts/check-current-source-state-v1.py
    python3 -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -O -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v7.py --self-test > "$result_root/capture.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v7.py --self-test > "$result_root/capture.optimized.json"
    cmp "$result_root/capture.json" "$result_root/capture.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v7.py --validate-static > "$result_root/static.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v7.py --validate-static > "$result_root/static.optimized.json"
    cmp "$result_root/static.json" "$result_root/static.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v7-self-test.py > "$result_root/self-test.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v7-self-test.py > "$result_root/self-test.optimized.json"
    cmp "$result_root/self-test.json" "$result_root/self-test.optimized.json"

# Retained historical composite-v8 self-check authority. C8 failed the retained
# certified-SxPID2 surface; this recipe grants zero qualification credit and cannot issue R8.
ksg-composite-v8:
    #!/usr/bin/env bash
    set -euo pipefail
    umask 077
    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v8.XXXXXX")"
    trap 'rm -rf -- "$result_root"' EXIT
    command -v rg >/dev/null
    rg --version >/dev/null
    python3 -I -S -B scripts/check-github-action-pins.py > "$result_root/action-pins.json"
    python3 -O -I -S -B scripts/check-github-action-pins.py > "$result_root/action-pins.optimized.json"
    cmp "$result_root/action-pins.json" "$result_root/action-pins.optimized.json"
    python3 -I -S -B scripts/check-github-action-pins-self-test.py > "$result_root/action-pins-self.json"
    python3 -O -I -S -B scripts/check-github-action-pins-self-test.py > "$result_root/action-pins-self.optimized.json"
    cmp "$result_root/action-pins-self.json" "$result_root/action-pins-self.optimized.json"
    python3 -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    python3 -O -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    scripts/check-release-state-self-test.sh
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.json"
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.optimized.json"
    cmp "$result_root/zeta.json" "$result_root/zeta.optimized.json"
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v8-local-closure.py --self-test > "$result_root/local.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v8-local-closure.py --self-test > "$result_root/local.optimized.json"
    cmp "$result_root/local.json" "$result_root/local.optimized.json"
    scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --exact
    scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --exact
    scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh --exact
    scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh --exact
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc scripts/check-mathematical-workflow-pdf-self-test.sh
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc scripts/check-mathematical-workflow-pdf.sh --exact
    python3 -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -I -S -B scripts/check-current-source-state-v1.py
    python3 -O -I -S -B scripts/check-current-source-state-v1.py
    python3 -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -O -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v8.py --self-test > "$result_root/capture.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v8.py --self-test > "$result_root/capture.optimized.json"
    cmp "$result_root/capture.json" "$result_root/capture.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v8.py --validate-static > "$result_root/static.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v8.py --validate-static > "$result_root/static.optimized.json"
    cmp "$result_root/static.json" "$result_root/static.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v8-self-test.py > "$result_root/self-test.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v8-self-test.py > "$result_root/self-test.optimized.json"
    cmp "$result_root/self-test.json" "$result_root/self-test.optimized.json"

# Composite-v9 repairs the five stale certified-SxPID2 operational bindings exposed in C8,
# leaves theorem sources/statements, estimator code, numerical fixtures, and PDF artifacts unchanged,
# separately corrects six synthetic fixture modes, and requires fresh L9 and hosted evidence.
ksg-composite-v9:
    #!/usr/bin/env bash
    set -euo pipefail
    umask 077
    python3 -I -S -B -c 'import sys; raise SystemExit(0 if sys.implementation.name == "cpython" and sys.version_info == (3, 14, 6, "final", 0) and sys._is_gil_enabled() else 1)'
    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v9.XXXXXX")"
    trap 'rm -rf -- "$result_root"' EXIT
    command -v rg >/dev/null
    rg --version >/dev/null
    python3 -I -S -B scripts/check-github-action-pins.py > "$result_root/action-pins.json"
    python3 -O -I -S -B scripts/check-github-action-pins.py > "$result_root/action-pins.optimized.json"
    cmp "$result_root/action-pins.json" "$result_root/action-pins.optimized.json"
    python3 -I -S -B scripts/check-github-action-pins-self-test.py > "$result_root/action-pins-self.json"
    python3 -O -I -S -B scripts/check-github-action-pins-self-test.py > "$result_root/action-pins-self.optimized.json"
    cmp "$result_root/action-pins-self.json" "$result_root/action-pins-self.optimized.json"
    python3 -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    python3 -O -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    scripts/check-release-state-self-test.sh
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.json"
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.optimized.json"
    cmp "$result_root/zeta.json" "$result_root/zeta.optimized.json"
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v9-local-closure.py --self-test > "$result_root/local.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v9-local-closure.py --self-test > "$result_root/local.optimized.json"
    test -s "$result_root/local.json"
    test -s "$result_root/local.optimized.json"
    cmp "$result_root/local.json" "$result_root/local.optimized.json"
    scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --exact
    scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --exact
    scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh --exact
    scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh --exact
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC python3 -I -S -B -c 'import sys; raise SystemExit(0 if sys.implementation.name == "cpython" and sys.version_info == (3, 14, 6, "final", 0) and sys._is_gil_enabled() else 1)'
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc scripts/check-mathematical-workflow-pdf-self-test.sh
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc scripts/check-mathematical-workflow-pdf.sh --exact
    python3 -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -I -S -B scripts/check-current-source-state-v1.py
    python3 -O -I -S -B scripts/check-current-source-state-v1.py
    python3 -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -O -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v9.py --self-test > "$result_root/capture.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v9.py --self-test > "$result_root/capture.optimized.json"
    test -s "$result_root/capture.json"
    test -s "$result_root/capture.optimized.json"
    cmp "$result_root/capture.json" "$result_root/capture.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v9.py --validate-static > "$result_root/static.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v9.py --validate-static > "$result_root/static.optimized.json"
    test -s "$result_root/static.json"
    test -s "$result_root/static.optimized.json"
    cmp "$result_root/static.json" "$result_root/static.optimized.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v9-self-test.py > "$result_root/self-test.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v9-self-test.py > "$result_root/self-test.optimized.json"
    test -s "$result_root/self-test.json"
    test -s "$result_root/self-test.optimized.json"
    cmp "$result_root/self-test.json" "$result_root/self-test.optimized.json"

# Fresh direct-C9 composite-v11 closure. This preserves the substantive v9 gate
# families while replacing the rejected C10 lifecycle with independently checked
# v11 capture, authority, topology, and hostile controls.
ksg-composite-v11:
    #!/usr/bin/env bash
    set -euo pipefail
    umask 077
    python3 -I -S -B -c 'import sys; raise SystemExit(0 if sys.implementation.name == "cpython" and sys.version_info == (3, 14, 6, "final", 0) and sys._is_gil_enabled() else 1)'
    result_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v11.XXXXXX")"
    trap 'rm -rf -- "$result_root"' EXIT
    command -v rg >/dev/null
    rg --version >/dev/null
    python3 -I -S -B scripts/check-github-action-pins.py > "$result_root/action-pins.json"
    python3 -O -I -S -B scripts/check-github-action-pins.py > "$result_root/action-pins.opt.json"
    cmp "$result_root/action-pins.json" "$result_root/action-pins.opt.json"
    python3 -I -S -B scripts/check-github-action-pins-self-test.py > "$result_root/action-pins-self.json"
    python3 -O -I -S -B scripts/check-github-action-pins-self-test.py > "$result_root/action-pins-self.opt.json"
    cmp "$result_root/action-pins-self.json" "$result_root/action-pins-self.opt.json"
    python3 -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    python3 -O -I -S -B scripts/normalize-actions-checkout-worktree-config-self-test.py
    python3 -I -S -B scripts/normalize-actions-checkout-git-info-exclude-self-test.py
    python3 -O -I -S -B scripts/normalize-actions-checkout-git-info-exclude-self-test.py
    scripts/check-release-state-self-test.sh
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.json"
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall.py > "$result_root/zeta.opt.json"
    cmp "$result_root/zeta.json" "$result_root/zeta.opt.json"
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
    scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --exact
    scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh --exact
    scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --exact
    scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh --exact
    scripts/check-ksg-m1a-composite-v7-boundary-pdf-self-test.sh --exact
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc scripts/check-mathematical-workflow-pdf-self-test.sh
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc scripts/check-mathematical-workflow-pdf.sh --exact
    python3 -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
    python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
    python3 -I -S -B scripts/check-current-source-state-v1.py
    python3 -O -I -S -B scripts/check-current-source-state-v1.py
    python3 -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -O -I -S -B scripts/check-current-source-state-v1-self-test.py
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v11.py --self-test > "$result_root/hosted.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v11.py --self-test > "$result_root/hosted.opt.json"
    cmp "$result_root/hosted.json" "$result_root/hosted.opt.json"
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v11-local-closure.py --self-test > "$result_root/local.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v11-local-closure.py --self-test > "$result_root/local.opt.json"
    cmp "$result_root/local.json" "$result_root/local.opt.json"
    python3 -I -S -B scripts/capture-ksg-m1a-composite-v11-local-closure.py --preflight-live > "$result_root/preflight.json"
    python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v11-local-closure.py --preflight-live > "$result_root/preflight.opt.json"
    cmp "$result_root/preflight.json" "$result_root/preflight.opt.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v11-self-test.py > "$result_root/self-test.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v11-self-test.py > "$result_root/self-test.opt.json"
    cmp "$result_root/self-test.json" "$result_root/self-test.opt.json"
    python3 -I -S -B scripts/check-ksg-m1a-composite-v11.py --candidate > "$result_root/static.json"
    python3 -O -I -S -B scripts/check-ksg-m1a-composite-v11.py --candidate > "$result_root/static.opt.json"
    cmp "$result_root/static.json" "$result_root/static.opt.json"

# Standalone exact-count, directed-rounding SxPID2 certifier (Rug/MPFR; source-only).
certified-sxpid:
    cargo fetch --locked --manifest-path audit/tools/certified-sxpid/Cargo.toml
    # Fail dependency-policy/tool-CLI incompatibilities before any evidence-producing command.
    cargo deny --manifest-path audit/tools/certified-sxpid/Cargo.toml --config audit/tools/certified-sxpid/deny.toml check
    CARGO_TARGET_DIR=target/certified-sxpid cargo test --locked --manifest-path audit/tools/certified-sxpid/Cargo.toml
    CARGO_TARGET_DIR=target/certified-sxpid-msrv cargo +1.89 test --locked --manifest-path audit/tools/certified-sxpid/Cargo.toml
    CARGO_TARGET_DIR=target/certified-sxpid cargo clippy --locked --manifest-path audit/tools/certified-sxpid/Cargo.toml --all-targets -- -D warnings
    RUSTDOCFLAGS="-D warnings" CARGO_TARGET_DIR=target/certified-sxpid cargo doc --locked --no-deps --manifest-path audit/tools/certified-sxpid/Cargo.toml
    cargo fmt --manifest-path audit/tools/certified-sxpid/Cargo.toml --all --check
    python3 audit/tools/certified-sxpid/scripts/check-static-policy.py
    python3 audit/tools/certified-sxpid/scripts/check-static-policy-self-test.py
    python3 audit/tools/certified-sxpid/scripts/check-independent-verifier.py
    python3 -O audit/tools/certified-sxpid/scripts/check-independent-verifier.py
    python3 audit/tools/certified-sxpid/scripts/check-exact-products.py
    python3 audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py
    python3 audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py
    python3 audit/tools/certified-sxpid/scripts/challenge-exact-products.py
    python3 scripts/check-lean-exact-log-product.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py
    python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
    python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py

# Rebuild the standalone finite-alphabet mathematical paper and compare its exact PDF bytes.
formal-finite-convergence-pdf:
    scripts/check-finite-alphabet-convergence-pdf.sh

# Rebuild the SxPID-under-dependency-coloring paper and compare its exact PDF bytes.
formal-dependency-sxpid-pdf:
    scripts/check-dependency-colored-sxpid-pdf.sh

# Rebuild the support-change-tolerant averaged SxPID paper and compare its exact PDF bytes.
formal-support-change-sxpid-pdf:
    scripts/check-support-change-tolerant-sxpid-pdf.sh

# Rebuild the formal-tool adoption decision record and compare its exact PDF bytes.
formal-tool-adoption-pdf:
    scripts/check-formal-tool-adoption-pdf.sh

# Rebuild the exact-count SxPID2 executable-assurance paper and compare its exact PDF bytes.
formal-certified-sxpid2-assurance-pdf:
    scripts/check-certified-sxpid2-assurance-pdf.sh

# Rebuild the exact rational-product SxPID2 zero/sign paper and compare its PDF.
formal-exact-log-product-sxpid2-pdf:
    scripts/check-exact-log-product-sxpid2-pdf.sh

# Rebuild the downstream ecosystem compatibility audit and compare its PDF.
formal-ecosystem-compatibility-audit-pdf:
    scripts/check-ecosystem-compatibility-audit-pdf.sh

# Rebuild the foundational shared-exclusions PID audit and compare its PDF.
formal-foundational-sxpid-audit-pdf:
    scripts/check-foundational-sxpid-audit-pdf.sh

# Check the finite adjacent-arrow countermodel and its fail-closed mutations.
citation-edge-countermodel:
    python3 scripts/check-citation-edge-countermodel.py
    python3 scripts/check-citation-edge-countermodel-self-test.py
    python3 scripts/check-lean-citation-edge-countermodel.py
    python3 scripts/check-lean-citation-edge-countermodel-self-test.py

# Check exact shortcut countermodels and the zeta-to-PID no-direct-transfer firewall.
zeta-pid-transfer-firewall:
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall.py
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall.py
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py

# Check the canonical Markdown enclosure and the synchronizer, log, and render-comparator
# mutations, then rebuild the complete mathematical problem-solving workflow and compare its
# exact PDF bytes. Normal and optimized Python replay the same mutation cases.
formal-mathematical-workflow-pdf:
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall.py
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall.py
    python3 -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc -c 'python3 -I -S scripts/sync-mathematical-workflow-tex.py --check'
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc -c 'python3 -I -S scripts/sync-mathematical-workflow-tex-self-test.py && python3 -O -I -S scripts/sync-mathematical-workflow-tex-self-test.py'
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc scripts/check-formal-pdf-log-self-test.sh
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc -c 'python3 -I -S scripts/compare-formal-pdf-renders-self-test.py && python3 -O -I -S scripts/compare-formal-pdf-renders-self-test.py'
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc scripts/check-mathematical-workflow-pdf-self-test.sh
    /usr/bin/env -i PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC bash --noprofile --norc scripts/check-mathematical-workflow-pdf.sh --exact

# Require a one-to-one inventory of formal LaTeX sources and rendered PDFs, then replay
# every warning-free deterministic PDF build.
formal-pdfs:
    scripts/check-formal-pdf-set.sh

# Minimum supported Rust version
msrv:
    cargo +1.89 check --locked --workspace
    cargo +1.89 check --locked --workspace --all-features

# Fixed corpus smoke; requires a rustup nightly and
# `cargo install cargo-fuzz --locked --version 0.13.2`.
fuzz-smoke:
    #!/usr/bin/env bash
    set -euo pipefail
    cd fuzz
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum --check corpus/SHA256SUMS
    else
      shasum -a 256 -c corpus/SHA256SUMS
    fi
    for target in matrix_shape public_configs_shells quantizer_sxpid experimental_antichain runlog_json_manifest experimental_hyperbolic resource_budgets; do
      cargo +nightly fuzz run "$target" -- -runs=128 -max_len=16384 -seed=424242
    done

# Release-candidate checks that are useful locally (CI also runs cross-platform/Python/coverage).
release-audit: lint test test-stable test-parallel test-all-features test-release doc msrv deny smoke version-check formal-pid2 ksg-revision formal-ksg-harmonic ksg-witnesses ksg-parity ksg-integration-decision formal-finite-convergence lean-toolchain-freeze ksg-composite-v11 certified-sxpid citation-edge-countermodel formal-pdfs
    cargo publish --locked -p pid-runlog --dry-run
    scripts/verify-package-archives.sh

# Core local gates. CI additionally runs OS/Python matrices, coverage, fuzz, SBOM, semver/package,
# a full-history secret scan, and the pinned MSRV matrix.
ci: lint test test-stable test-parallel test-all-features doc deny smoke version-check lean-toolchain-freeze
