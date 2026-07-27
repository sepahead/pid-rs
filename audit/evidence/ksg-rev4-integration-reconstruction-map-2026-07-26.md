# KSG revision-4 integration reconstruction map

## Status and use

This is a read-only reconstruction audit and durable coordination artifact for
`KSG-INTEGER-HARMONIC-001` revision 4. It records how to build the KSG-only release candidate
without importing later work from the ambient multi-wave tree. It is not a theorem, validation
result, final evidence matrix, release decision, or substitute for settled-tree replay.

The reconstruction was checked through six lenses:

1. arithmetic source and compiled behavior;
2. formal theorem and mutation custody;
3. method-catalog dependency closure;
4. release/public-surface propagation;
5. generated evidence, ecosystem, and software-identity coherence; and
6. negative contamination and Git-phase isolation.

Scientific/protected baseline:
`e96122b56c15e895c081379210103d1a26eac25f`.

Current isolated candidate:
`/private/tmp/pid-rs-ksg-rev4.E11L9g/tree`.

The ambient checkout is evidence recovery input only. No ambient shared file may be copied
wholesale.

## Exact KSG production/oracle slice

Reconstruct these eleven paths from the isolated candidate after their writers stop:

```text
crates/pid-core/src/stats.rs
crates/pid-core/src/ksg.rs
crates/pid-core/src/isx.rs
crates/pid-core/src/pid3.rs
crates/pid-core/tests/ksg.rs
crates/pid-core/tests/ksg_report.rs
crates/pid-core/tests/isx.rs
crates/pid-core/tests/parallel_bit_identity.rs
crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json
crates/pid-core/tests/fixtures/ksg_local_arithmetic_oracle.json.sha256
scripts/generate-ksg-local-arithmetic-oracle.py
```

The settled eleven-path binary patch from the scientific baseline has diagnostic SHA-256
`4f8ec9612604763c795acd2d4d58dad785853c37f7c456693a3eb992b94a2c7c`.
This value must be recomputed if any allowed byte changes. It is not a final Git-phase receipt.

Explicitly preserve the scientific-baseline versions of:

```text
crates/pid-core/src/pid2.rs
crates/pid-core/src/discrete_pid.rs
crates/pid-core/src/bin/exp0.rs
crates/pid-core/tests/pid2.rs
```

Also exclude every Imin boundary file, exact-binary64-sum fixture/generator, Python binding/test,
frontier/SxPID theorem, and unrelated PDF change.

Current settled source/oracle identities are:

```text
f03b1ecca4e9259cc39bc17815e8161e8e538464f669a5de761078b95eb90f78  stats.rs
0f5109dda054a0222ed796209b10d22196348eddac76d8d53dd78b4e03a95250  ksg.rs
ad2bf59da32433f866313d339889084050bff21e0b672589019260df8ff690d5  isx.rs
f1f9d18b73312fb2e25e725382e65edf42bdaecd73d611d7dffc943221b2bfcd  pid3.rs
544192cac6c00957e1e05a4cc320c069453060eb1fe676131f83b155c1ee6daa  tests/ksg.rs
10b40cfc2b37243a28ae38d32917e803094d37e90549a993961a53eeeefd537d  tests/isx.rs
724c1fad3ce11ce14b789efda0edccfe96a6f3334d077cad075dd667683b0f44  tests/ksg_report.rs
611a31e1b76536b1b1b712cdbd7713dc5caad24f354b0c507e2779bbf8f3cb28  parallel_bit_identity.rs
560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c  oracle JSON
fb91172bdb767b3e11e15ef4e89bb0482b932c5c2450f87d566245eda87a8ec7  oracle sidecar file
a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b  oracle generator
```

## Serial/parallel negative control and constants

The former file gate

```text
#![cfg(all(feature = "experimental-pipelines", feature = "parallel"))]
```

made the purported serial invocation run zero tests. The KSG-only candidate instead requires:

```text
#![cfg(feature = "experimental-pipelines")]
```

The serial command must report 12 executed tests before parallel equality is credited.

The clean-parent KSG-only constants are:

```text
KSG_LOCAL_TERMS_CHECKSUM = 13714940533915299
KSG_LOCAL_TERM_0         = 4611372573292626839
KSG_LOCAL_TERM_MID       = 4608683422432580648
KSG_LOCAL_TERM_LAST      = 4609053335123176929
ISX_REDUNDANCY_BITS      = 4608069949341512143
PID2_RED_BITS            = 4608069949341512143
PID2_UNQ1_BITS           = 4590324628665003600
PID2_UNQ2_BITS           = 13821388618758275492
PID2_SYN_BITS            = 4591732782175321776
PID3_ATOM_CHECKSUM       = 9260367673031411424
PID3_RED_CHECKSUM        = 12358916445650220
PID3_ATOM_001_BITS       = 13803885910316517056
PID3_ATOM_111_BITS       = 4587721666143603408
```

The ambient `PID2_SYN_BITS = 4591732782175321784` is later PID2 represented-sum contamination and
is a phase-checker negative control. Twelve of the thirteen KSG-dependent values change relative
to the scientific baseline; the midpoint remains unchanged.

Required profiles include debug and release serial
`experimental-pipelines`, parallel `experimental-pipelines,parallel`, and thread budgets
1, 2, 3, 4, and available maximum. Configuration diversity is not a scientific-validation route.

## Method-catalog closure

Reverse traversal from `mutual-information.ksg1-raw` and
`mutual-information.ksg1-report` produces exactly 21 method nodes:

```text
co-information.continuous-raw
co-information.continuous-report
mutual-information.hyperbolic-ksg
mutual-information.ksg1-raw
mutual-information.ksg1-report
mutual-information.ksg1-sensitivity-trajectories
mutual-information.ksg1-shared-config
pid.continuous-pid2
pid.incomplete-continuous-pid3
pid.mixed-dimension-pid3
pipelines.hierarchy-screening
pipelines.pid2-screening
pipelines.pid3-permutation
pipelines.pls-pid-composition
shannon-invariants.continuous-ksg-composition
shared-exclusions.continuous-heuristics
shared-exclusions.continuous-raw
shared-exclusions.continuous-report
software.python-experimental-migration-bindings
software.python-v1-bindings
validation.exp0
```

`mutual-information.ksg1-shared-config` is the sole non-numerical exclusion. Therefore exactly
20 objects are affected, 49 method objects are protected, and all 45 reference objects are
protected.

For each affected object, only these validation fields may change:

```text
/validation/evidence_paths
/validation/limitations
/validation/scope
```

Preserve `validation.level` and every origin, definition, API, dependency, and citation field.

Six objects bind the formal route:

```text
mutual-information.ksg1-raw
mutual-information.ksg1-report
pid.incomplete-continuous-pid3
pid.mixed-dimension-pid3
shared-exclusions.continuous-raw
shared-exclusions.continuous-report
```

Their final evidence must name the revision-scoped v4 Lean source, all four SMT obligations,
`formal-assurance-v4.md`, the modular certificate, and the matching checkers.

Protected projection identities are:

```text
7dcad03d4b018243c020765a61d7ac2d5a7117d0b3b098ce650fd4c6251fb48d  49 methods
dfa02422f456880a5c03830ed730db835d45211cd07558738f02afce7f81f654  45 references
14cc8ececb23de3367f0629e85cb105c3a674f7499fdc09946bdcae9932ad6fb  catalog metadata
```

The ambient catalog is only a revision-3 semantic clue. Reconstruct revision 4, pin the complete
20-object affected projection, and regenerate `METHODS.md`; never copy ambient `METHODS.md`.

## Release-family closure

Exactly 15 complete family objects change, only at `estimator_revision`:

```text
stable.continuous
  strict-unique-shell-integer-harmonic-report-v4
experimental.continuous.co-information
  ksg-derived-co-information-integer-harmonic-v2
experimental.continuous.isx
  strict-unique-shell-integer-harmonic-isx-v4
experimental.continuous.pid2
  separate-biased-term-pid2-integer-harmonic-v2
experimental.continuous.incomplete-pid3
  equal-ambient-branch-screen-integer-harmonic-v2
research.raw-ksg
  ksg-chebyshev-integer-harmonic-raw-v2
research.raw-isx
  ehrlich-local-knn-integer-harmonic-raw-v2
research.raw-co-information
  ksg-co-information-integer-harmonic-raw-v2
research.isx-heuristics
  heuristic-baselines-with-integer-harmonic-ksg-v2
research.mixed-dimension-pid3
  mixed-dimensional-pid3-integer-harmonic-reference-v2
research.hyperbolic
  lorentz-geometry-and-integer-harmonic-ksg-safe-rust-v2
experimental.hierarchy
  hierarchy-screening-with-integer-harmonic-ksg-v2
experimental.pipelines.pid3-permutation
  explicit-seed-pid3-permutation-with-integer-harmonic-ksg-v2
experimental.pipelines.pls-selection-and-composition
  deterministic-pls-cv-and-integer-harmonic-pid-composition-v2
experimental.pipelines.pid2-screening
  deterministic-pair-enumeration-with-integer-harmonic-pid2-v2
```

The four KSG-only PID2-emitting bridge families are:

```text
experimental.continuous.pid2
research.isx-heuristics
experimental.hierarchy
experimental.pipelines.pid2-screening
```

Do not use later combined `represented-input-exact` revision strings.

Expected projection identities are:

```text
a0c7f7f625e787a86d08435d8eb1fbcea0c045813efd774215b58c59a73271f2  15 affected
3596fc9899e8f632f5165fe0138958919f41204d671b70484a5142bb1e72decb  20 protected
24e2f99f8e11d2e2270c77e92f9aa8b4bddecea24574fa39d8980e8616141d19  top metadata
```

The ambient release JSON is a useful KSG-only semantic blueprint, but its generated
`RELEASE_SCOPE_1_0.md` is contaminated. Rebuild the Markdown from final JSON.

## Review evidence, ecosystem, and identity

Reconstruct from the scientific baseline plus KSG-only changes:

```text
scripts/check-review-evidence.py
scripts/check-review-evidence-self-test.py
audit/evidence/assurance-registry.json
audit/evidence/task-dispositions.json
```

Do not modify `audit/evidence/FILE_REVIEW_LEDGER.csv`, which is historical tagged-tree evidence.
Update the same 15 release families; give the shared configuration evidence without an estimator
revision. T138 receives only the KSG paragraph/evidence change and retains its baseline SxPID2
content.

Preserve ecosystem consumer and inventory objects byte-for-byte. Their invariant projection is:

```text
ccc5ba5ad414a9c923f56619a3acb09ebc1f5e18ee014ce8f02e152ae24d3d40
```

Retain the historical/base full semantic projection:

```text
63a843b4fbd36c43534ab8fa6dd9da2174c673862b13368c3dd6eed4fc2c5280
```

Do not overwrite that value with the ambient `1ab358...` projection. Validate the historical
projection and current KSG authority bindings separately. Rebind only the final assurance-registry,
method-catalog, and release-scope hashes, then regenerate `ECOSYSTEM_CAPABILITIES.md`.

In `crates/pid-core/identity/software-identity-reference-v1.json`, update only the canonical raw
JSON hashes for final `method-catalog.json` and `release-scope-1.0.json`. Identity establishes
forensic correspondence, not API compatibility, authenticity, estimator validity, or application
suitability.

## Documentation and automation

Reconstruct narrowly:

```text
README.md
crates/pid-core/README.md
KNOWN_LIMITATIONS.md
CHANGELOG.md
MIGRATION.md
.github/workflows/ci.yml
justfile
scripts/README.md
AGENTS.md
```

The root README's KSG validation line is stale at 96/256 epsilons. Two corrected metrics must
remain distinct: the selected finite corpus differs from
`binary64(stored Decimal prefix text)` by at most `8 * f64::EPSILON` nats with 40 ties, while a
160-digit directed enclosure certifies a unique maximum below
`9.761311 * f64::EPSILON` nats under the checker's stated Python `Decimal` directed-rounding
semantics, including the fixed stress rows. Both remain under the reviewed
`32 * f64::EPSILON`-nat ceiling. Exact-rounded references differ textually on 6,509 rows and
numerically on 5,934 rows, but every binary64 conversion agrees. The selected route has 354
positive zeros, no negative zeros, and 7,844 nonzeros. None of these is an ULP, universal,
portable, estimator, support, or PID theorem.

CI/Just must run Lean, Z3, modular generator/checker/self-test, local oracle generator, exact
enclosure checker/self-test, main checker/self-test, phase checker/self-test, and explicit
nonzero-test serial/parallel profiles in normal/optimized and debug/release modes as applicable.
Exclude PID2 represented-sum, Imin, exact-binary64-sum, finite-convergence, count-bridge, frontier,
and unrelated PDF gates from the KSG-only reconstruction.

## Phase-isolation checker requirements

The dedicated checker must:

- authenticate the scientific baseline and delivery/current ancestry;
- bind an exact changed-path allowlist rather than a directory-prefix allowlist;
- compare every protected path by mode, type, and blob;
- pin complete blobs for shared/high-risk files;
- reject symlinks, gitlinks, replacement/graft/config overlays, wrong parents, changed delivery
  blobs, and protected-path edits;
- reject PID2/Imin/exact-sum/frontier/Python/PDF paths and tokens;
- reject ambient synergy bits `4591732782175321784` and combined PID2 release strings;
- include hash-first and hash-rebased typed-fact/reviewed-byte attacks; and
- keep cyclic checker/self-test identities outside self-hashed manifests, using Git ancestry to
  anchor them.

This proves phase provenance only, not arithmetic or scientific validity.

## Required construction order

1. Settle source, oracle, claim, formal, and modular-certificate bytes.
2. Capture KSG-only serial constants with baseline PID2 and prove the serial test executes.
3. Settle the main checker and its preclosure/final mutation modes.
4. Reconstruct release JSON, then catalog JSON.
5. Generate release and methods Markdown from those settled JSON files.
6. Rebuild review evidence, assurance registry, and task dispositions.
7. Rebind ecosystem authorities while preserving historical projections.
8. Rebind software identity.
9. Reconstruct audience docs, CI, Just, scripts documentation, and AGENTS.
10. Finalize phase-checker pins and mutations.
11. Replay all normal/optimized, debug/release, serial/parallel, generated-view, identity,
    contamination, and release gates after every writer stops.
12. Commit the implementation milestone, then issue the immutable final evidence/decision receipt
    commit if self-reference prevents binding the implementation commit in the first commit.
