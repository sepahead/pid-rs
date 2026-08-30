# Ecosystem capability and evidence-gap contract

## Project classification

This contract classifies pid-rs as a standalone, protocol-neutral library and tooling project. It is not an NCP peer, provider, or consumer and receives no NCP role receipt. It records pid-rs capabilities, retained boundaries, and missing evidence against four historical consumer snapshots. It does not claim compatibility, integration, qualification, operational validation, or application validity.

This is a selected, non-exhaustive risk projection from the bound historical sources. It is not a complete inventory of current or historical consumer requirements.

The machine-readable authority is [`ecosystem-capabilities.json`](ecosystem-capabilities.json). The checker generates this file from that authority.

The checker preserves the historical/base semantic projection at SHA-256 `63a843b4fbd36c43534ab8fa6dd9da2174c673862b13368c3dd6eed4fc2c5280`. That custody projection covers the inventory boundary, all consumer semantics and evidence records, and the reviewed base authority records. For its digest only, the three moving current authority digests are replaced by their historical/base values.

The checker separately binds the inventory boundary plus all consumer records to SHA-256 `ccc5ba5ad414a9c923f56619a3acb09ebc1f5e18ee014ce8f02e152ae24d3d40`. It independently hashes the exact canonical bytes of every current authority in the table below and requires each reviewed KSG-revision digest, live byte digest, path, role, and schema identity to match. Refreshing an authority digest does not claim current consumer compatibility or integration.

## Bound authorities

| Authority | Path | SHA-256 | Role |
|---|---|---|---|
| `assurance-registry` | `audit/evidence/assurance-registry.json` | `355fb84902fb344657e04f36767ac3a0865f24539496b28e174f03eaf3789e51` | Release-family assurance layers and explicit gaps. |
| `method-catalog` | `method-catalog.json` | `5c826dfe4e6a8ff14128f9dba41d67ea032c776d1f44e347d9ac6e6dfc3d8ab7` | Method origin, implementation status, constraints, and evidence. |
| `release-scope` | `release-scope-1.0.json` | `98473c97b3f49877e6231350c6a798c1a8745fa2c78eff9abf624b9a88f60ecf` | Proposed 1.0 family boundary and integration claim status. |
| `repository-snapshot` | `audit/evidence/repository-snapshot.json` | `b57e506bbf30183c29bea4ff062a3711a3e471400dd91ebbdd8f787152af4b56` | Historical repository identity evidence only. |

The repository snapshot records historical identity evidence. It does not prove API compatibility or current repository state.

## Local method maturity labels

| Label | Meaning |
|---|---|
| `experimental` | At least one named primary pid-rs method is an experimental local implementation. |
| `retained-boundary` | The requirement is deliberately outside the local pid-rs implementation boundary. |
| `stable` | Every named primary pid-rs method is a stable local implementation. |
| `unavailable` | No primary pid-rs implementation is named for the requirement. |

## Evidence classes

| Class | Meaning |
|---|---|
| `assumption-certificate` | A machine-readable contract records the scientific assumptions needed by the route. |
| `authorization-safety-case` | An independently reviewed safety case governs any authority-relevant use. |
| `bounded-software-test` | Executable tests cover a stated finite domain, property set, or fixture corpus. |
| `certified-numerical-bound` | A rigorous enclosure bounds finite-precision error for the reported quantity. |
| `consumer-commit-integration` | A named consumer commit pins and exercises the exact pid-rs API and configuration. |
| `deductive-rust-refinement` | A deductive proof connects the executable Rust kernel to the formal specification. |
| `definition-provenance` | The method catalog identifies the definition origin, implementation origin, and constraints. |
| `formal-or-analytic` | A machine-checked or exact analytic argument covers a stated mathematical obligation. |
| `holdout-benchmark` | A preregistered held-out challenge evaluates the exact consumer route. |
| `implementation-contract` | Typed code and tests enforce the declared software and interpretation boundary. |
| `independent-review` | A reviewer independent of the implementation records a scoped assessment. |
| `negative-mutation` | A fail-closed test rejects a scientifically invalid or metadata-invalid route. |
| `numerical-stress` | High-precision or adversarial fixtures challenge finite-precision behavior. |
| `runlog-replay` | A bounded reader validates and replays the relevant run-log schema. |
| `sequential-inference` | A theorem or calibrated procedure controls repeated, adaptive, or post-selection use. |
| `statistical-validation` | Calibration evidence covers the stated sampling process, estimator, and uncertainty claim. |
| `trusted-catalog-binding` | Runtime evidence binds a canonical method entry and verifies its exact digest. |

## Crebain

The selected historical Crebain sources define observation, producer, and model contracts but contain no direct pid-rs dependency evidence.

- Integration claim status: `not_claimed`.
- Historical commit: `4c311900ade5668200a48d56fb191be1916b884a`.
- Historical tree: `55eb96da6d98e65f89b6b84fbb81ee8f53f6cde0`.
- Snapshot scope: `historical_repository_identity_only`.

### Historical requirement sources

| Path | SHA-256 |
|---|---|
| `docs/GALADRIEL_PRODUCER.md` | `285aa1fb33b609793e3ddf7f2897ece2cbd512a9a6e278857ad439554481123d` |
| `docs/MODEL_CONTRACTS.md` | `1790c459504863022dad3e883fab5ce6c37d80bc93a9dc27680db0e27631862a` |
| `docs/PLANT_APPLY_OBSERVATION_V1.md` | `dd0fccec019a9c54a8d999c31e875c00b6edb182541708a41e7a687e7fd65927` |
| `scripts/fixtures/phase0-evidence-artifact-valid.json` | `4072dedaa841ef317163e311b0764878e8f370a24dc3bb3c4433c9e0734dce4e` |
| `src-tauri/src/pid_observation.rs` | `ab46a3f1941f271b98e8cd46e50d4cacd3e25fa0a0191501e7b80614d635dbee` |

### Requirements

| ID | Priority | Local method maturity | Missing evidence | Gaps |
|---|---|---|---|---|
| `crebain.adapter` | `P0` | `unavailable` | `consumer-commit-integration`, `implementation-contract`, `negative-mutation` | `crebain.adapter` |
| `crebain.frozen-map` | `P1` | `stable` | `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `holdout-benchmark` | `crebain.frozen-map`, `crebain.local-assurance` |
| `crebain.runlog-binding` | `P0` | `experimental` | `consumer-commit-integration`, `runlog-replay`, `trusted-catalog-binding` | `crebain.runlog-binding` |
| `crebain.signed-atoms` | `P0` | `stable` | `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `runlog-replay` | `crebain.local-assurance`, `crebain.signed-atoms` |

#### crebain.adapter: Direct adapter and dependency

Crebain needs a typed adapter before it can consume a PID result without losing role and failure semantics.

- Primary methods: None.
- Validation methods: None.
- Boundary methods: None.
- Release families: None.
- Historical sources: `docs/GALADRIEL_PRODUCER.md`, `src-tauri/src/pid_observation.rs`.
- Assumptions: The consumer must define source roles, target role, units, preprocessing identity, and failure handling.
- Limitations: Historical repository identity does not show a direct pid-rs dependency or adapter.

#### crebain.frozen-map: Frozen observation mapping

Crebain needs an explicit observation-to-category map with frozen training provenance.

- Primary methods: `shared-exclusions.fitted-quantized`.
- Validation methods: `validation.finite-alphabet-plugin-convergence`.
- Boundary methods: None.
- Release families: `pid-core.stable.quantized`.
- Historical sources: `docs/MODEL_CONTRACTS.md`, `src-tauri/src/pid_observation.rs`.
- Assumptions: A transform is fitted on independent training rows, frozen, and identified before evaluation.
- Limitations: The stable fitted route estimates a quantized law, not the original continuous representation.
- Present `bounded-software-test` evidence: `crates/pid-core/tests/fitted_quantized_sxpid.rs`.
  - `pid-core.stable.quantized/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F003-RUST`.
- Present `definition-provenance` evidence: `method-catalog.json`.
  - `pid-core.stable.quantized/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F003-DEF`.
- Present `implementation-contract` evidence: `crates/pid-core/src/quantizer.rs`, `crates/pid-core/src/sxpid.rs`, `crates/pid-core/tests/fitted_quantized_sxpid.rs`.
  - `pid-core.stable.quantized/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F003-RUST`.

Bound assurance layers:

| Family | Layer | Status | Tier | Gap IDs |
|---|---|---|---|---|
| `pid-core.stable.quantized` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F003-DEF` |
| `pid-core.stable.quantized` | `exact_algebra` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F003-ALG` |
| `pid-core.stable.quantized` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F003-NUM` |
| `pid-core.stable.quantized` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F003-RUST` |
| `pid-core.stable.quantized` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F003-STAT` |

#### crebain.runlog-binding: Trusted method and outcome binding

Crebain needs a runtime method-catalog binding and a bounded replay route for scientific outcomes.

- Primary methods: `software.runlog-schema-replay`, `software.scientific-outcome-contract-foundation`.
- Validation methods: None.
- Boundary methods: None.
- Release families: None.
- Historical sources: `docs/GALADRIEL_PRODUCER.md`, `scripts/fixtures/phase0-evidence-artifact-valid.json`.
- Assumptions: The runtime must use the exact method identity, schema, split identity, and terminal outcome state.
- Limitations: Stable schema 2 replay does not implement the experimental schema 3 event, reader, replay, CLI, or catalog-digest route.
- Present `bounded-software-test` evidence: `crates/pid-runlog/tests/scientific_contract.rs`.
- Present `implementation-contract` evidence: `crates/pid-runlog/src/scientific.rs`, `crates/pid-runlog/tests/scientific_contract.rs`.
- Present `negative-mutation` evidence: `crates/pid-runlog/tests/scientific_contract.rs`, `scripts/check-method-catalog-self-test.py`.

#### crebain.signed-atoms: Signed atom transport

Crebain needs to preserve signed atom interpretation and explicit abstention through transport.

- Primary methods: `shared-exclusions.categorical`, `software.sxpid-interpretation-contract`.
- Validation methods: None.
- Boundary methods: None.
- Release families: `pid-core.stable.categorical`.
- Historical sources: `docs/GALADRIEL_PRODUCER.md`, `docs/PLANT_APPLY_OBSERVATION_V1.md`, `src-tauri/src/pid_observation.rs`.
- Assumptions: Transport preserves nats, source order, target role, atom component, pointwise or averaged scope, and signed values.
- Limitations: Typed pid-rs values cannot stop a consumer from extracting and relabeling a scalar.
- Present `bounded-software-test` evidence: `crates/pid-core/tests/sxpid_interpretation.rs`, `crates/pid-core/tests/sxpid_properties.rs`.
  - `pid-core.stable.categorical/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F002-RUST`.
- Present `definition-provenance` evidence: `method-catalog.json`.
  - `pid-core.stable.categorical/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F002-DEF`.
- Present `implementation-contract` evidence: `crates/pid-core/src/sxpid.rs`, `crates/pid-core/tests/sxpid_interpretation.rs`, `crates/pid-core/tests/sxpid_properties.rs`.
  - `pid-core.stable.categorical/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F002-RUST`.

Bound assurance layers:

| Family | Layer | Status | Tier | Gap IDs |
|---|---|---|---|---|
| `pid-core.stable.categorical` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F002-DEF` |
| `pid-core.stable.categorical` | `exact_algebra` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-ALG` |
| `pid-core.stable.categorical` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-NUM` |
| `pid-core.stable.categorical` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F002-RUST` |
| `pid-core.stable.categorical` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F002-STAT` |

### Open gaps and retained boundaries

| ID | Priority | Disposition | Owner | Missing evidence | Statement |
|---|---|---|---|---|---|
| `crebain.adapter` | `P0` | `OPEN_CONSUMER` | `consumer` | `consumer-commit-integration`, `implementation-contract`, `negative-mutation` | The historical Crebain snapshot has no direct pid-rs adapter or pinned integration test. |
| `crebain.frozen-map` | `P1` | `OPEN_JOINT` | `joint` | `consumer-commit-integration`, `holdout-benchmark` | No Crebain observation mapping binds a separately fitted transform to held-out rows. |
| `crebain.local-assurance` | `P0` | `OPEN_LOCAL` | `pid-rs` | `certified-numerical-bound`, `deductive-rust-refinement` | The local categorical and quantized routes lack certified numerical bounds and deductive end-to-end Rust refinement. |
| `crebain.runlog-binding` | `P0` | `OPEN_JOINT` | `joint` | `consumer-commit-integration`, `runlog-replay`, `trusted-catalog-binding` | Schema 3 has a typed foundation, but it has no runtime trusted-catalog lookup or Crebain replay route. |
| `crebain.signed-atoms` | `P0` | `OPEN_JOINT` | `joint` | `consumer-commit-integration`, `runlog-replay` | pid-rs has typed signed atoms, but no Crebain transport and replay contract exercises them. |

#### crebain.adapter

- Evidence paths: `audit/evidence/repository-snapshot.json`, `release-scope-1.0.json`.
- Required negative challenges:

  - Reject an observation when its source order, target role, units, or preprocessing identity is absent.
  - Do not convert an unavailable PID route into a numeric zero.

#### crebain.frozen-map

- Evidence paths: `KNOWN_LIMITATIONS.md`, `crates/pid-core/tests/fitted_quantized_sxpid.rs`.
- Required negative challenges:

  - Reject same-row fitting as evidence for a frozen held-out estimand.
  - Reject a stale quantizer digest or a changed source order.

#### crebain.local-assurance

- Evidence paths: `KNOWN_LIMITATIONS.md`, `audit/evidence/assurance-registry.json`.
- Required negative challenges:

  - Reject an f64 sign as certified when a rigorous enclosure contains zero.
  - Reject bounded tests as a deductive Rust refinement proof.

#### crebain.runlog-binding

- Evidence paths: `crates/pid-runlog/tests/scientific_contract.rs`, `method-catalog.json`.
- Required negative challenges:

  - Reject an unknown or stale method-catalog identity.
  - Reject missing, duplicate, or contradictory terminal outcomes.
  - Reject a schema 3 record presented as a schema 2 replay.

#### crebain.signed-atoms

- Evidence paths: `crates/pid-core/tests/sxpid_interpretation.rs`, `crates/pid-runlog/tests/replay_cli.rs`.
- Required negative challenges:

  - Reject a bare scalar that omits atom measure, scope, sign, and units.
  - Reject conversion of abstention to zero.

## Galadriel

The selected historical Galadriel sources define a PID evidence envelope and record one bounded synthetic pid-rs migration. They do not establish current release or deployment qualification.

- Integration claim status: `not_claimed`.
- Historical commit: `017c615e3976eae69c3115aeeb74e9fdb50ec15d`.
- Historical tree: `bc47c9b1053ade871095e5529136145432683c82`.
- Snapshot scope: `historical_repository_identity_only`.

### Historical requirement sources

| Path | SHA-256 |
|---|---|
| `crates/galadriel-eval/src/evidence_main.rs` | `0539fc2daf65114b0faca66f039e7df321560f172c2487f5134c12b67e0a686a` |
| `crates/galadriel-ncp/schemas/galadriel-pid-envelope-v1.schema.json` | `1a95627882e8dd84277e21501b77f94a63c71cae0eb81e8d01bcebe86b64ab43` |
| `docs/PRODUCER-CONTRACT.md` | `f2acce55986baf63c333d47c4ddd2c8bb1df6ee6e4b4eea88f48f12cef177de1` |
| `evidence/pid-rs-1.0-migration.json` | `53fc6c9443ca4ad7c855fbe0d60bc46d5b26929dc2995640b4674d110837ff72` |
| `evidence/post-audit-v1.json` | `98f54cc1aa30c0f6deb0c5607fe33c8ff7a8b625bded970535081a147a1dc662` |

### Bounded historical integration evidence

These records describe exact historical fixtures only. They do not change the current integration claim status.

| ID | pid-rs revision | Sources | Scope | Limitation |
|---|---|---|---|---|
| `galadriel.synthetic-migration` | `1cd2424f7967e1752dcc8e53859e8fdad3566f51` | `evidence/pid-rs-1.0-migration.json` | Exact historical Galadriel and pid-rs revisions, commands, seeds, hashes, and paired synthetic outputs. | The artifact classifies itself as synthetic compatibility only and does not provide deployment calibration. |

### Requirements

| ID | Priority | Local method maturity | Missing evidence | Gaps |
|---|---|---|---|---|
| `galadriel.continuous-pid2` | `P0` | `experimental` | `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `holdout-benchmark`, `independent-review`, `statistical-validation` | `galadriel.continuous-pid2`, `galadriel.local-assurance` |
| `galadriel.dependent-windows` | `P0` | `stable` | `assumption-certificate`, `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `statistical-validation` | `galadriel.dependent-windows`, `galadriel.local-assurance` |
| `galadriel.preprocessing` | `P0` | `experimental` | `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `holdout-benchmark`, `statistical-validation` | `galadriel.local-assurance`, `galadriel.preprocessing` |
| `galadriel.sequential-alerts` | `P0` | `unavailable` | `consumer-commit-integration`, `implementation-contract`, `negative-mutation`, `sequential-inference`, `statistical-validation` | `galadriel.sequential-alerts` |

#### galadriel.continuous-pid2: Continuous PID2 support and gauge

Galadriel needs a fail-closed continuous PID2 route only when its support and gauge assumptions are true.

- Primary methods: `diagnostics.support-contracts`, `pid.continuous-pid2`, `shared-exclusions.continuous-report`.
- Validation methods: None.
- Boundary methods: None.
- Release families: `pid-core.diagnostics.support`, `pid-core.experimental.continuous.isx`, `pid-core.experimental.continuous.pid2`, `pid-core.stable.continuous`.
- Historical sources: `crates/galadriel-eval/src/evidence_main.rs`, `evidence/pid-rs-1.0-migration.json`, `evidence/post-audit-v1.json`.
- Assumptions: Every required marginal and joint law is full-dimensional and absolutely continuous; Mutual information is finite, source ambient dimensions are equal, and the relative source gauge is fixed and reported.
- Limitations: The route combines estimators with distinct finite-sample bias and has no generic consistency or calibrated uncertainty theorem.
- Present `assumption-certificate` evidence: `crates/pid-core/src/isx.rs`, `crates/pid-core/src/ksg.rs`, `crates/pid-core/src/pid2.rs`, `crates/pid-core/src/support.rs`, `crates/pid-core/tests/continuous_reports.rs`, `crates/pid-core/tests/isx.rs`, `crates/pid-core/tests/ksg_report.rs`, `crates/pid-core/tests/pid2.rs`.
  - `pid-core.diagnostics.support/statistical_application_validity`: `ASSUMPTION_GATED` / `ASSUMPTION_DECLARATION`; open or retained gap IDs: `GAP-F010-STAT`.
  - `pid-core.experimental.continuous.isx/statistical_application_validity`: `NOT_CLAIMED` / `ASSUMPTION_DECLARATION`; open or retained gap IDs: `GAP-F012-STAT`.
  - `pid-core.experimental.continuous.pid2/statistical_application_validity`: `NOT_CLAIMED` / `ASSUMPTION_DECLARATION`; open or retained gap IDs: `GAP-F014-STAT`.
  - `pid-core.stable.continuous/statistical_application_validity`: `ASSUMPTION_GATED` / `ASSUMPTION_DECLARATION`; open or retained gap IDs: `GAP-F005-STAT`.
- Present `bounded-software-test` evidence: `crates/pid-core/tests/continuous_reports.rs`, `crates/pid-core/tests/isx.rs`, `crates/pid-core/tests/ksg_report.rs`, `crates/pid-core/tests/pid2.rs`.
  - `pid-core.diagnostics.support/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F010-RUST`.
  - `pid-core.experimental.continuous.isx/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F012-RUST`.
  - `pid-core.experimental.continuous.pid2/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F014-RUST`.
  - `pid-core.stable.continuous/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F005-RUST`.
- Present `definition-provenance` evidence: `method-catalog.json`.
  - `pid-core.diagnostics.support/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F010-DEF`.
  - `pid-core.experimental.continuous.isx/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F012-DEF`.
  - `pid-core.experimental.continuous.pid2/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F014-DEF`.
  - `pid-core.stable.continuous/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F005-DEF`.
- Present `implementation-contract` evidence: `crates/pid-core/src/isx.rs`, `crates/pid-core/src/ksg.rs`, `crates/pid-core/src/pid2.rs`, `crates/pid-core/src/support.rs`, `crates/pid-core/tests/continuous_reports.rs`, `crates/pid-core/tests/isx.rs`, `crates/pid-core/tests/ksg_report.rs`, `crates/pid-core/tests/pid2.rs`.
  - `pid-core.diagnostics.support/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F010-RUST`.
  - `pid-core.experimental.continuous.isx/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F012-RUST`.
  - `pid-core.experimental.continuous.pid2/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F014-RUST`.
  - `pid-core.stable.continuous/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F005-RUST`.
- Present `numerical-stress` evidence: `crates/pid-core/tests/continuous_reports.rs`, `crates/pid-core/tests/gaussian_pid_atoms.rs`, `crates/pid-core/tests/isx.rs`, `crates/pid-core/tests/ksg.rs`, `crates/pid-core/tests/pid2.rs`.
  - `pid-core.diagnostics.support/floating_point_numerical_behavior`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F010-NUM`.
  - `pid-core.experimental.continuous.isx/floating_point_numerical_behavior`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F012-NUM`.
  - `pid-core.experimental.continuous.pid2/floating_point_numerical_behavior`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F014-NUM`.
  - `pid-core.stable.continuous/floating_point_numerical_behavior`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F005-NUM`.

Bound assurance layers:

| Family | Layer | Status | Tier | Gap IDs |
|---|---|---|---|---|
| `pid-core.diagnostics.support` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F010-DEF` |
| `pid-core.diagnostics.support` | `exact_algebra` | `NOT_APPLICABLE` | `NONE` | `GAP-F010-ALG` |
| `pid-core.diagnostics.support` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F010-NUM` |
| `pid-core.diagnostics.support` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F010-RUST` |
| `pid-core.diagnostics.support` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F010-STAT` |
| `pid-core.experimental.continuous.isx` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F012-DEF` |
| `pid-core.experimental.continuous.isx` | `exact_algebra` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F012-ALG` |
| `pid-core.experimental.continuous.isx` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F012-NUM` |
| `pid-core.experimental.continuous.isx` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F012-RUST` |
| `pid-core.experimental.continuous.isx` | `statistical_application_validity` | `NOT_CLAIMED` | `ASSUMPTION_DECLARATION` | `GAP-F012-STAT` |
| `pid-core.experimental.continuous.pid2` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F014-DEF` |
| `pid-core.experimental.continuous.pid2` | `exact_algebra` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F014-ALG` |
| `pid-core.experimental.continuous.pid2` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F014-NUM` |
| `pid-core.experimental.continuous.pid2` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F014-RUST` |
| `pid-core.experimental.continuous.pid2` | `statistical_application_validity` | `NOT_CLAIMED` | `ASSUMPTION_DECLARATION` | `GAP-F014-STAT` |
| `pid-core.stable.continuous` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F005-DEF` |
| `pid-core.stable.continuous` | `exact_algebra` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F005-ALG` |
| `pid-core.stable.continuous` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F005-NUM` |
| `pid-core.stable.continuous` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F005-RUST` |
| `pid-core.stable.continuous` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F005-STAT` |

#### galadriel.dependent-windows: Dependent-window row law

Galadriel needs a row-law and dependence contract for overlapping monitoring windows.

- Primary methods: `shared-exclusions.categorical`.
- Validation methods: `validation.dependency-color-sxpid-concentration`.
- Boundary methods: None.
- Release families: `pid-core.stable.categorical`.
- Historical sources: `crates/galadriel-eval/src/evidence_main.rs`, `docs/PRODUCER-CONTRACT.md`, `evidence/post-audit-v1.json`.
- Assumptions: Every row has the common declared law, and complete rows are mutually independent within each nonempty color; The fixed-width overlapping-window construction uses independent innovations and disjoint same-color innovation blocks.
- Limitations: The theorem does not cover arbitrary trajectory dependence, fitted global transforms, adaptive windows, or closed-loop selection.
- Present `bounded-software-test` evidence: `crates/pid-core/tests/dependency_colored_sxpid_oracle.rs`.
  - `pid-core.stable.categorical/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F002-RUST`.
- Present `definition-provenance` evidence: `method-catalog.json`.
  - `pid-core.stable.categorical/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F002-DEF`.
- Present `formal-or-analytic` evidence: `DEPENDENCY_COLORED_SXPID_CONCENTRATION.md`, `audit/formal/lean/PidFiniteConvergence/Dependence.lean`.
  - `pid-core.stable.categorical/exact_algebra`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F002-ALG`.
- Present `numerical-stress` evidence: `crates/pid-core/tests/dependency_colored_sxpid_oracle.rs`, `crates/pid-core/tests/fixtures/dependency_colored_sxpid_oracle.json`.
  - `pid-core.stable.categorical/floating_point_numerical_behavior`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F002-NUM`.

Bound assurance layers:

| Family | Layer | Status | Tier | Gap IDs |
|---|---|---|---|---|
| `pid-core.stable.categorical` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F002-DEF` |
| `pid-core.stable.categorical` | `exact_algebra` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-ALG` |
| `pid-core.stable.categorical` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-NUM` |
| `pid-core.stable.categorical` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F002-RUST` |
| `pid-core.stable.categorical` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F002-STAT` |

#### galadriel.preprocessing: Preprocessing and noise estimand

Galadriel needs explicit fit/evaluate separation and an estimand identity for any added observation noise.

- Primary methods: `preprocessing.gaussian-noise-provenance`, `shared-exclusions.fitted-quantized`.
- Validation methods: `validation.finite-alphabet-plugin-convergence`.
- Boundary methods: None.
- Release families: `pid-core.experimental.pipelines.gaussian-noise-provenance`, `pid-core.stable.quantized`.
- Historical sources: `crates/galadriel-eval/src/evidence_main.rs`, `evidence/pid-rs-1.0-migration.json`, `evidence/post-audit-v1.json`.
- Assumptions: Training and evaluation row identities are disjoint, and every transform is frozen before evaluation; Added Gaussian noise represents an explicit observation model or a named sensitivity study.
- Limitations: A noise declaration does not prove finite mutual information, row independence, estimator validity, or PID monotonicity.
- Present `bounded-software-test` evidence: `crates/pid-core/tests/fitted_quantized_sxpid.rs`, `crates/pid-core/tests/observation_noise.rs`.
  - `pid-core.experimental.pipelines.gaussian-noise-provenance/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F034-RUST`.
  - `pid-core.stable.quantized/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F003-RUST`.
- Present `definition-provenance` evidence: `method-catalog.json`.
  - `pid-core.experimental.pipelines.gaussian-noise-provenance/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F034-DEF`.
  - `pid-core.stable.quantized/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F003-DEF`.
- Present `implementation-contract` evidence: `crates/pid-core/src/observation.rs`, `crates/pid-core/src/quantizer.rs`, `crates/pid-core/tests/fitted_quantized_sxpid.rs`, `crates/pid-core/tests/observation_noise.rs`.
  - `pid-core.experimental.pipelines.gaussian-noise-provenance/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F034-RUST`.
  - `pid-core.stable.quantized/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F003-RUST`.

Bound assurance layers:

| Family | Layer | Status | Tier | Gap IDs |
|---|---|---|---|---|
| `pid-core.experimental.pipelines.gaussian-noise-provenance` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F034-DEF` |
| `pid-core.experimental.pipelines.gaussian-noise-provenance` | `exact_algebra` | `NOT_APPLICABLE` | `NONE` | `GAP-F034-ALG` |
| `pid-core.experimental.pipelines.gaussian-noise-provenance` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F034-NUM` |
| `pid-core.experimental.pipelines.gaussian-noise-provenance` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F034-RUST` |
| `pid-core.experimental.pipelines.gaussian-noise-provenance` | `statistical_application_validity` | `NOT_CLAIMED` | `ASSUMPTION_DECLARATION` | `GAP-F034-STAT` |
| `pid-core.stable.quantized` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F003-DEF` |
| `pid-core.stable.quantized` | `exact_algebra` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F003-ALG` |
| `pid-core.stable.quantized` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F003-NUM` |
| `pid-core.stable.quantized` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F003-RUST` |
| `pid-core.stable.quantized` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F003-STAT` |

#### galadriel.sequential-alerts: Sequential alert calibration

Galadriel needs repeated-alert and post-selection control for its exact monitoring policy.

- Primary methods: None.
- Validation methods: `validation.dependency-color-sxpid-concentration`.
- Boundary methods: None.
- Release families: None.
- Historical sources: `crates/galadriel-eval/src/evidence_main.rs`, `crates/galadriel-ncp/schemas/galadriel-pid-envelope-v1.schema.json`, `docs/PRODUCER-CONTRACT.md`.
- Assumptions: Repeated decisions require error control for the complete adaptive selection and alert process.
- Limitations: The all-prefix concentration envelope does not cover adaptive transforms, model selection, or alert policies.

### Open gaps and retained boundaries

| ID | Priority | Disposition | Owner | Missing evidence | Statement |
|---|---|---|---|---|---|
| `galadriel.continuous-pid2` | `P0` | `OPEN_JOINT` | `joint` | `consumer-commit-integration`, `holdout-benchmark`, `independent-review`, `statistical-validation` | The experimental continuous PID2 route lacks Galadriel-specific calibration, held-out challenge evidence, and independent review. |
| `galadriel.dependent-windows` | `P0` | `OPEN_JOINT` | `joint` | `assumption-certificate`, `consumer-commit-integration`, `statistical-validation` | No machine-readable Galadriel row-law certificate establishes the narrow dependency-color theorem premises. |
| `galadriel.local-assurance` | `P0` | `OPEN_LOCAL` | `pid-rs` | `certified-numerical-bound`, `deductive-rust-refinement` | The local PID routes lack certified numerical bounds and deductive end-to-end Rust refinement. |
| `galadriel.preprocessing` | `P0` | `OPEN_JOINT` | `joint` | `consumer-commit-integration`, `holdout-benchmark`, `statistical-validation` | No Galadriel route binds frozen preprocessing and an explicit joint noise estimand to held-out evaluation. |
| `galadriel.sequential-alerts` | `P0` | `OPEN_JOINT` | `joint` | `consumer-commit-integration`, `implementation-contract`, `negative-mutation`, `sequential-inference`, `statistical-validation` | pid-rs has no calibrated sequential false-alarm or post-selection procedure for Galadriel alerts. |

#### galadriel.continuous-pid2

- Evidence paths: `KNOWN_LIMITATIONS.md`, `crates/pid-core/tests/pid2.rs`.
- Required negative challenges:

  - Reject atomic, quantized, mixed, singular, tied, or unknown support.
  - Reject unequal source dimensions and undeclared relative source units.
  - Do not clamp signed mutual-information estimates before atom reconstruction.

#### galadriel.dependent-windows

- Evidence paths: `DEPENDENCY_COLORED_SXPID_CONCENTRATION.md`, `crates/pid-core/tests/dependency_colored_sxpid_oracle.rs`.
- Required negative challenges:

  - Reject pairwise-only independence, zero covariance, adaptive colors, and unspecified mixing.
  - Reject a window color when same-color rows do not use disjoint independent innovation blocks.

#### galadriel.local-assurance

- Evidence paths: `KNOWN_LIMITATIONS.md`, `audit/evidence/assurance-registry.json`.
- Required negative challenges:

  - Reject an f64 sign as certified when a rigorous enclosure contains zero.
  - Reject bounded Rust tests as a deductive refinement proof.

#### galadriel.preprocessing

- Evidence paths: `KNOWN_LIMITATIONS.md`, `crates/pid-core/tests/observation_noise.rs`.
- Required negative challenges:

  - Reject same-window fitting as a held-out transform.
  - Reject added noise as a generic tie repair or proof of estimator validity.
  - Reject separate matrix reports as proof of a joint source-target noise law.

#### galadriel.sequential-alerts

- Evidence paths: `DEPENDENCY_COLORED_SXPID_CONCENTRATION.md`, `KNOWN_LIMITATIONS.md`.
- Required negative challenges:

  - Reject reuse of a fixed-sample interval as a repeated alert threshold.
  - Reject adaptively selected windows, transforms, or alarms outside the declared theorem.

## Haldir

The selected historical Haldir sources define authority and evidence boundaries and contain no direct PID integration evidence. The PID requirements below are conservative implications of those boundaries.

- Integration claim status: `not_claimed`.
- Historical commit: `1c8862ec93999506c285c0777c82394ebe8ab409`.
- Historical tree: `357406073f1f117c71eaaa5c910699aa220724e7`.
- Snapshot scope: `historical_repository_identity_only`.

### Historical requirement sources

| Path | SHA-256 |
|---|---|
| `contracts/vectors/README.md` | `719acd90f06a5c443b466fcf0e4ed9196c4b145026f310a15effaa982dcadd0f` |
| `crates/haldir-deployment/src/contract.rs` | `db1850b804fbcaa7ef91e6834d3c0fe549ac97fe404bdf566600bbc15f1476ea` |
| `crates/haldir-evidence/src/gate_journal.rs` | `17ebb152ecb70e75cec8b50d7236c828b124d89216cffe71122c138a489f0f57` |
| `docs/EVIDENCE-SEMANTICS.md` | `211cb5a77bcef250aa8b3f9716ec79249ae747f744c465b0b9d521f620f1988b` |
| `docs/RESEARCH-PROTOCOL.md` | `d990edc06c1953857a1a1dc620311f0666bd749d5ecd9eff4b0f7830e67b63e1` |

### Requirements

| ID | Priority | Local method maturity | Missing evidence | Gaps |
|---|---|---|---|---|
| `haldir.authorization` | `P0` | `retained-boundary` | `authorization-safety-case`, `consumer-commit-integration`, `independent-review`, `negative-mutation` | `haldir.authorization-external`, `haldir.authorization-integration`, `haldir.authorization-local` |
| `haldir.dependency-certificate` | `P0` | `stable` | `assumption-certificate`, `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `statistical-validation` | `haldir.dependency-certificate`, `haldir.local-assurance` |
| `haldir.sequential-policy` | `P0` | `unavailable` | `consumer-commit-integration`, `implementation-contract`, `negative-mutation`, `sequential-inference`, `statistical-validation` | `haldir.sequential-policy` |
| `haldir.signed-interpretation` | `P0` | `stable` | `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `independent-review` | `haldir.local-assurance`, `haldir.signed-interpretation` |

#### haldir.authorization: Authorization boundary

Haldir needs an independently reviewed fail-closed policy before any PID evidence can enter an authority-relevant path.

- Primary methods: None.
- Validation methods: None.
- Boundary methods: None.
- Release families: None.
- Historical sources: `crates/haldir-deployment/src/contract.rs`, `docs/EVIDENCE-SEMANTICS.md`, `docs/RESEARCH-PROTOCOL.md`.
- Assumptions: Any future PID evidence must remain outside authority unless an independently reviewed fail-closed policy governs its use; it cannot widen existing authority.
- Limitations: No estimator result, proof, or run-log identity is a mission-safety certificate.

#### haldir.dependency-certificate: Dependency-color finite-sample certificate

Haldir needs machine-checkable dependence, support, and drift evidence for each finite-sample claim.

- Primary methods: `shared-exclusions.categorical`.
- Validation methods: `validation.dependency-color-sxpid-concentration`.
- Boundary methods: None.
- Release families: `pid-core.stable.categorical`.
- Historical sources: `crates/haldir-evidence/src/gate_journal.rs`, `docs/EVIDENCE-SEMANTICS.md`, `docs/RESEARCH-PROTOCOL.md`.
- Assumptions: Complete rows are mutually independent within each declared color, share the stated law, and have a justified population support floor.
- Limitations: A finite dataset cannot establish mutual within-color independence or an unknown population support floor.
- Present `bounded-software-test` evidence: `crates/pid-core/tests/dependency_colored_sxpid_oracle.rs`.
  - `pid-core.stable.categorical/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F002-RUST`.
- Present `definition-provenance` evidence: `method-catalog.json`.
  - `pid-core.stable.categorical/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F002-DEF`.
- Present `formal-or-analytic` evidence: `DEPENDENCY_COLORED_SXPID_CONCENTRATION.md`, `audit/formal/lean/PidFiniteConvergence/Dependence.lean`.
  - `pid-core.stable.categorical/exact_algebra`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F002-ALG`.
- Present `numerical-stress` evidence: `crates/pid-core/tests/dependency_colored_sxpid_oracle.rs`, `crates/pid-core/tests/fixtures/dependency_colored_sxpid_oracle.json`.
  - `pid-core.stable.categorical/floating_point_numerical_behavior`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F002-NUM`.

Bound assurance layers:

| Family | Layer | Status | Tier | Gap IDs |
|---|---|---|---|---|
| `pid-core.stable.categorical` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F002-DEF` |
| `pid-core.stable.categorical` | `exact_algebra` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-ALG` |
| `pid-core.stable.categorical` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-NUM` |
| `pid-core.stable.categorical` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F002-RUST` |
| `pid-core.stable.categorical` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F002-STAT` |

#### haldir.sequential-policy: Sequential and post-selection policy

Haldir needs sequential and post-selection control for the exact evidence policy.

- Primary methods: None.
- Validation methods: None.
- Boundary methods: None.
- Release families: None.
- Historical sources: `crates/haldir-evidence/src/gate_journal.rs`, `docs/EVIDENCE-SEMANTICS.md`, `docs/RESEARCH-PROTOCOL.md`.
- Assumptions: The complete selection, repetition, and decision process must be part of the error-control model.
- Limitations: Fixed-sample convergence and concentration results do not calibrate an adaptive policy.

#### haldir.signed-interpretation: Signed categorical interpretation

Haldir needs an in-band signed-atom interpretation contract for advisory evidence.

- Primary methods: `shared-exclusions.categorical`, `software.sxpid-interpretation-contract`.
- Validation methods: None.
- Boundary methods: None.
- Release families: `pid-core.stable.categorical`.
- Historical sources: `contracts/vectors/README.md`, `crates/haldir-deployment/src/contract.rs`, `docs/EVIDENCE-SEMANTICS.md`.
- Assumptions: The consumer preserves nats, signed values, atom component, source order, target role, and pointwise or averaged scope.
- Limitations: Typed metadata cannot prevent a downstream caller from discarding it.
- Present `bounded-software-test` evidence: `crates/pid-core/tests/sxpid_interpretation.rs`, `crates/pid-core/tests/sxpid_properties.rs`.
  - `pid-core.stable.categorical/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F002-RUST`.
- Present `definition-provenance` evidence: `method-catalog.json`.
  - `pid-core.stable.categorical/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F002-DEF`.
- Present `implementation-contract` evidence: `crates/pid-core/src/sxpid.rs`, `crates/pid-core/tests/sxpid_interpretation.rs`, `crates/pid-core/tests/sxpid_properties.rs`.
  - `pid-core.stable.categorical/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F002-RUST`.

Bound assurance layers:

| Family | Layer | Status | Tier | Gap IDs |
|---|---|---|---|---|
| `pid-core.stable.categorical` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F002-DEF` |
| `pid-core.stable.categorical` | `exact_algebra` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-ALG` |
| `pid-core.stable.categorical` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-NUM` |
| `pid-core.stable.categorical` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F002-RUST` |
| `pid-core.stable.categorical` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F002-STAT` |

### Open gaps and retained boundaries

| ID | Priority | Disposition | Owner | Missing evidence | Statement |
|---|---|---|---|---|---|
| `haldir.authorization-external` | `P0` | `BLOCKED_EXTERNAL` | `external` | `authorization-safety-case`, `independent-review` | The selected sources contain no independent authority safety case or review for PID evidence. |
| `haldir.authorization-integration` | `P0` | `OPEN_JOINT` | `joint` | `consumer-commit-integration` | The selected sources contain no direct PID integration evidence. |
| `haldir.authorization-local` | `P0` | `RETAINED_BOUNDARY` | `pid-rs` | `negative-mutation` | pid-rs retains authority use outside its claim boundary, but no executable Haldir-specific rejection test is recorded. |
| `haldir.dependency-certificate` | `P0` | `OPEN_JOINT` | `joint` | `assumption-certificate`, `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `statistical-validation` | No Haldir evidence path supplies the full row-law, color, support-floor, and drift certificate. |
| `haldir.local-assurance` | `P0` | `OPEN_LOCAL` | `pid-rs` | `certified-numerical-bound`, `deductive-rust-refinement` | The local categorical route lacks certified numerical bounds and deductive end-to-end Rust refinement. |
| `haldir.sequential-policy` | `P0` | `OPEN_JOINT` | `joint` | `consumer-commit-integration`, `implementation-contract`, `negative-mutation`, `sequential-inference`, `statistical-validation` | pid-rs has no Haldir-specific sequential or post-selection inference route. |
| `haldir.signed-interpretation` | `P0` | `OPEN_JOINT` | `joint` | `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `independent-review` | No Haldir commit exercises the typed signed-atom interpretation route. |

#### haldir.authorization-external

- Evidence paths: `audit/evidence/repository-snapshot.json`.
- Required negative challenges:

  - Reject a local software test as an independent authority safety case.

#### haldir.authorization-integration

- Evidence paths: `audit/evidence/repository-snapshot.json`.
- Required negative challenges:

  - Reject a claimed Haldir PID integration without an exact consumer commit and exercising test.

#### haldir.authorization-local

- Evidence paths: `KNOWN_LIMITATIONS.md`, `release-scope-1.0.json`.
- Required negative challenges:

  - Reject PID as an independent authorization condition.
  - Reject a PID observation that widens authority or bypasses fail-closed policy.

#### haldir.dependency-certificate

- Evidence paths: `DEPENDENCY_COLORED_SXPID_CONCENTRATION.md`, `crates/pid-core/tests/dependency_colored_sxpid_oracle.rs`.
- Required negative challenges:

  - Reject invalid or adaptive colors.
  - Reject drift under a fixed-law claim.
  - Reject an empirical minimum frequency as the population support floor.

#### haldir.local-assurance

- Evidence paths: `KNOWN_LIMITATIONS.md`, `audit/evidence/assurance-registry.json`.
- Required negative challenges:

  - Reject an f64 sign as certified when a rigorous enclosure contains zero.
  - Reject bounded tests as a deductive Rust refinement proof.

#### haldir.sequential-policy

- Evidence paths: `KNOWN_LIMITATIONS.md`, `release-scope-1.0.json`.
- Required negative challenges:

  - Reject repeated thresholding without a sequential error budget.
  - Reject post-selection reuse of fixed-sample uncertainty.

#### haldir.signed-interpretation

- Evidence paths: `crates/pid-core/tests/sxpid_interpretation.rs`, `release-scope-1.0.json`.
- Required negative challenges:

  - Reject negative-atom clamping.
  - Reject confusion between pointwise and averaged atoms.
  - Reject a bare scalar without its interpretation contract.

## Prisoma

The selected historical Prisoma sources record bounded producer-consumer fixtures and research-claim gates. They do not establish current pid-rs release qualification or application validity.

- Integration claim status: `not_claimed`.
- Historical commit: `0968128062f30da5c04f3f31c23f6ce8e0d95d36`.
- Historical tree: `d7ee5763cbdc5906c91ff4c82c5fc9a124c6aa84`.
- Snapshot scope: `historical_repository_identity_only`.

### Historical requirement sources

| Path | SHA-256 |
|---|---|
| `crates/pid-bridge/src/bin/contract.rs` | `216bedc991040c10f8340e72c11dac4574524db62eb821d7b4cb46a26524d242` |
| `protocols/capability_matrix_current_v1.json` | `ebb602b8630dffd1f4d5026e11cc653371d638c91c5997f2497ac66fcc129ee5` |
| `protocols/ecosystem_evidence_current_v1.json` | `e46c851c32f3b08cb7814a4e38e91e4d6b506cbd245686addad54ecc1662f408` |
| `protocols/holdout_registry_v1.json` | `0e9a7c756809fe3aec6157eca3811587bca7cfc9d407dd5c7a624995dcdb3b5f` |
| `protocols/research_claim_registry_v1.json` | `400364178eb2bf467488f6da5b05c2a2b011084c9047b68f8a4aece51f865b8a` |

### Bounded historical integration evidence

These records describe exact historical fixtures only. They do not change the current integration claim status.

| ID | pid-rs revision | Sources | Scope | Limitation |
|---|---|---|---|---|
| `prisoma.report-abstention` | `ac4a7803c5a77408f5e9176c60cda71c65c38260` | `protocols/capability_matrix_current_v1.json` | A pinned pid-rs producer and Prisoma consumer were tested together on positive and abstaining fixtures. | Positive and abstaining synthetic fixtures do not validate real embedding support, estimates, or application claims. |
| `prisoma.schema2-replay` | `ac4a7803c5a77408f5e9176c60cda71c65c38260` | `protocols/capability_matrix_current_v1.json` | A pinned pid-runlog producer and Prisoma consumer were tested together on schema 2 validation and replay fixtures. | Schema 2 fixture replay does not establish schema 3 scientific replay, policy replay, or current release qualification. |

### Requirements

| ID | Priority | Local method maturity | Missing evidence | Gaps |
|---|---|---|---|---|
| `prisoma.heldout-quantized` | `P0` | `stable` | `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `holdout-benchmark`, `independent-review`, `statistical-validation` | `prisoma.heldout-quantized`, `prisoma.local-assurance` |
| `prisoma.mixed-support` | `P0` | `retained-boundary` | `implementation-contract` | `prisoma.mixed-support` |
| `prisoma.row-law` | `P0` | `stable` | `assumption-certificate`, `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `statistical-validation` | `prisoma.local-assurance`, `prisoma.row-law` |
| `prisoma.uncertainty` | `P1` | `experimental` | `assumption-certificate`, `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `statistical-validation` | `prisoma.local-assurance`, `prisoma.uncertainty` |

#### prisoma.heldout-quantized: Held-out categorical or quantized SxPID

Prisoma needs a separately fitted, frozen, low-cardinality categorical route for representation diagnostics.

- Primary methods: `shared-exclusions.categorical`, `shared-exclusions.fitted-quantized`.
- Validation methods: `validation.finite-alphabet-plugin-convergence`.
- Boundary methods: None.
- Release families: `pid-core.stable.categorical`, `pid-core.stable.quantized`.
- Historical sources: `crates/pid-bridge/src/bin/contract.rs`, `protocols/capability_matrix_current_v1.json`, `protocols/ecosystem_evidence_current_v1.json`, `protocols/holdout_registry_v1.json`.
- Assumptions: A finite-output transform is fitted on an independent training sequence, frozen, and identified before evaluation; Evaluation rows satisfy the declared iid, ergodic, or valid dependency-color contract.
- Limitations: The result concerns the frozen quantized estimand, not the original continuous embedding.
- Present `bounded-software-test` evidence: `crates/pid-core/tests/finite_alphabet_plugin_oracle.rs`, `crates/pid-core/tests/fitted_quantized_sxpid.rs`, `crates/pid-core/tests/sxpid_exhaustive_oracle.rs`.
  - `pid-core.stable.categorical/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F002-RUST`.
  - `pid-core.stable.quantized/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F003-RUST`.
- Present `definition-provenance` evidence: `method-catalog.json`.
  - `pid-core.stable.categorical/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F002-DEF`.
  - `pid-core.stable.quantized/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F003-DEF`.
- Present `formal-or-analytic` evidence: `FINITE_ALPHABET_PLUGIN_CONVERGENCE.md`, `audit/formal/lean/PidFiniteConvergence/Deterministic.lean`.
  - `pid-core.stable.categorical/exact_algebra`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F002-ALG`.
  - `pid-core.stable.quantized/exact_algebra`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F003-ALG`.
- Present `implementation-contract` evidence: `crates/pid-core/src/quantizer.rs`, `crates/pid-core/src/sxpid.rs`, `crates/pid-core/tests/fitted_quantized_sxpid.rs`, `crates/pid-core/tests/sxpid_exhaustive_oracle.rs`.
  - `pid-core.stable.categorical/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F002-RUST`.
  - `pid-core.stable.quantized/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F003-RUST`.
- Present `numerical-stress` evidence: `crates/pid-core/tests/finite_alphabet_plugin_oracle.rs`, `crates/pid-core/tests/fitted_quantized_sxpid.rs`, `crates/pid-core/tests/fixtures/finite_alphabet_plugin_oracle.json`, `crates/pid-core/tests/sxpid_exhaustive_oracle.rs`.
  - `pid-core.stable.categorical/floating_point_numerical_behavior`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F002-NUM`.
  - `pid-core.stable.quantized/floating_point_numerical_behavior`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F003-NUM`.

Bound assurance layers:

| Family | Layer | Status | Tier | Gap IDs |
|---|---|---|---|---|
| `pid-core.stable.categorical` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F002-DEF` |
| `pid-core.stable.categorical` | `exact_algebra` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-ALG` |
| `pid-core.stable.categorical` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-NUM` |
| `pid-core.stable.categorical` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F002-RUST` |
| `pid-core.stable.categorical` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F002-STAT` |
| `pid-core.stable.quantized` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F003-DEF` |
| `pid-core.stable.quantized` | `exact_algebra` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F003-ALG` |
| `pid-core.stable.quantized` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F003-NUM` |
| `pid-core.stable.quantized` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F003-RUST` |
| `pid-core.stable.quantized` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F003-STAT` |

#### prisoma.mixed-support: Mixed-support estimator

Prisoma needs an explicit unavailable outcome for mixed categorical and continuous support.

- Primary methods: None.
- Validation methods: None.
- Boundary methods: `unsupported.mixed-support-continuous-pid`.
- Release families: None.
- Historical sources: `crates/pid-bridge/src/bin/contract.rs`, `protocols/capability_matrix_current_v1.json`, `protocols/research_claim_registry_v1.json`.
- Assumptions: Categorical targets and continuous sources require a method defined for that mixed support.
- Limitations: No current pid-rs estimator matches this mixed-support request.
- Present `definition-provenance` evidence: `method-catalog.json`.
- Present `negative-mutation` evidence: `crates/pid-runlog/tests/scientific_contract.rs`.

#### prisoma.row-law: Row-law and support certificate

Prisoma needs a machine-readable row-law, dependence, support-floor, and drift certificate.

- Primary methods: `shared-exclusions.categorical`.
- Validation methods: `validation.dependency-color-sxpid-concentration`.
- Boundary methods: None.
- Release families: `pid-core.stable.categorical`.
- Historical sources: `crates/pid-bridge/src/bin/contract.rs`, `protocols/ecosystem_evidence_current_v1.json`, `protocols/research_claim_registry_v1.json`.
- Assumptions: Complete rows are mutually independent within each deterministic nonempty color and share the declared law; The population support floor and any drift bound come from external scientific knowledge, not observed minima.
- Limitations: The theorem does not infer population support, mutual independence, or a drift target from a finite dataset.
- Present `bounded-software-test` evidence: `crates/pid-core/tests/dependency_colored_sxpid_oracle.rs`.
  - `pid-core.stable.categorical/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F002-RUST`.
- Present `definition-provenance` evidence: `method-catalog.json`.
  - `pid-core.stable.categorical/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F002-DEF`.
- Present `formal-or-analytic` evidence: `DEPENDENCY_COLORED_SXPID_CONCENTRATION.md`, `audit/formal/lean/PidFiniteConvergence/Dependence.lean`.
  - `pid-core.stable.categorical/exact_algebra`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F002-ALG`.
- Present `numerical-stress` evidence: `crates/pid-core/tests/dependency_colored_sxpid_oracle.rs`, `crates/pid-core/tests/fixtures/dependency_colored_sxpid_oracle.json`.
  - `pid-core.stable.categorical/floating_point_numerical_behavior`: `BOUNDED` / `BOUNDED_TEST`; open or retained gap IDs: `GAP-F002-NUM`.

Bound assurance layers:

| Family | Layer | Status | Tier | Gap IDs |
|---|---|---|---|---|
| `pid-core.stable.categorical` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F002-DEF` |
| `pid-core.stable.categorical` | `exact_algebra` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-ALG` |
| `pid-core.stable.categorical` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-NUM` |
| `pid-core.stable.categorical` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F002-RUST` |
| `pid-core.stable.categorical` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F002-STAT` |

#### prisoma.uncertainty: Rare-cell and uncertainty reporting

Prisoma needs rare-cell diagnostics and uncertainty calibrated for its exact evaluation design.

- Primary methods: `pipelines.quantized-sxpid-bootstrap`, `shared-exclusions.categorical`.
- Validation methods: `validation.dependency-color-sxpid-concentration`.
- Boundary methods: None.
- Release families: `pid-core.experimental.pipelines.quantized-sxpid-bootstrap`, `pid-core.stable.categorical`.
- Historical sources: `crates/pid-bridge/src/bin/contract.rs`, `protocols/ecosystem_evidence_current_v1.json`, `protocols/holdout_registry_v1.json`, `protocols/research_claim_registry_v1.json`.
- Assumptions: Any interval claim must match the sampling process, dependence structure, preprocessing, selected statistic, and target use.
- Limitations: The block-bootstrap percentiles are exploratory and the concentration radius can be vacuous for large alphabets.
- Present `bounded-software-test` evidence: `crates/pid-core/tests/dependency_colored_sxpid_oracle.rs`, `crates/pid-core/tests/sxpid_bootstrap.rs`.
  - `pid-core.experimental.pipelines.quantized-sxpid-bootstrap/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F027-RUST`.
  - `pid-core.stable.categorical/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F002-RUST`.
- Present `definition-provenance` evidence: `method-catalog.json`.
  - `pid-core.experimental.pipelines.quantized-sxpid-bootstrap/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F027-DEF`.
  - `pid-core.stable.categorical/definition`: `DOCUMENTED` / `DOCUMENTATION`; open or retained gap IDs: `GAP-F002-DEF`.
- Present `implementation-contract` evidence: `crates/pid-core/src/pipeline.rs`, `crates/pid-core/src/sxpid.rs`, `crates/pid-core/tests/sxpid_bootstrap.rs`, `crates/pid-core/tests/sxpid_properties.rs`.
  - `pid-core.experimental.pipelines.quantized-sxpid-bootstrap/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F027-RUST`.
  - `pid-core.stable.categorical/rust_refinement`: `TESTED` / `IMPLEMENTATION_TEST`; open or retained gap IDs: `GAP-F002-RUST`.

Bound assurance layers:

| Family | Layer | Status | Tier | Gap IDs |
|---|---|---|---|---|
| `pid-core.experimental.pipelines.quantized-sxpid-bootstrap` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F027-DEF` |
| `pid-core.experimental.pipelines.quantized-sxpid-bootstrap` | `exact_algebra` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F027-ALG` |
| `pid-core.experimental.pipelines.quantized-sxpid-bootstrap` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F027-NUM` |
| `pid-core.experimental.pipelines.quantized-sxpid-bootstrap` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F027-RUST` |
| `pid-core.experimental.pipelines.quantized-sxpid-bootstrap` | `statistical_application_validity` | `NOT_CLAIMED` | `ASSUMPTION_DECLARATION` | `GAP-F027-STAT` |
| `pid-core.stable.categorical` | `definition` | `DOCUMENTED` | `DOCUMENTATION` | `GAP-F002-DEF` |
| `pid-core.stable.categorical` | `exact_algebra` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-ALG` |
| `pid-core.stable.categorical` | `floating_point_numerical_behavior` | `BOUNDED` | `BOUNDED_TEST` | `GAP-F002-NUM` |
| `pid-core.stable.categorical` | `rust_refinement` | `TESTED` | `IMPLEMENTATION_TEST` | `GAP-F002-RUST` |
| `pid-core.stable.categorical` | `statistical_application_validity` | `ASSUMPTION_GATED` | `ASSUMPTION_DECLARATION` | `GAP-F002-STAT` |

### Open gaps and retained boundaries

| ID | Priority | Disposition | Owner | Missing evidence | Statement |
|---|---|---|---|---|---|
| `prisoma.heldout-quantized` | `P0` | `OPEN_JOINT` | `joint` | `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `holdout-benchmark`, `independent-review`, `statistical-validation` | No Prisoma commit and preregistered holdout challenge exercise the frozen quantized SxPID route. |
| `prisoma.local-assurance` | `P0` | `OPEN_LOCAL` | `pid-rs` | `certified-numerical-bound`, `deductive-rust-refinement` | The local categorical, quantized, and resampling routes lack certified numerical bounds and deductive end-to-end Rust refinement. |
| `prisoma.mixed-support` | `P0` | `RETAINED_BOUNDARY` | `pid-rs` | `implementation-contract` | Mixed-support continuous PID is explicitly unsupported and remains a retained boundary. |
| `prisoma.row-law` | `P0` | `OPEN_JOINT` | `joint` | `assumption-certificate`, `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `statistical-validation` | No Prisoma route records and checks the row-law, color, support-floor, transform, and drift assumptions. |
| `prisoma.uncertainty` | `P1` | `OPEN_JOINT` | `joint` | `assumption-certificate`, `certified-numerical-bound`, `consumer-commit-integration`, `deductive-rust-refinement`, `statistical-validation` | Available concentration and resampling evidence does not calibrate generic Prisoma embedding data. |

#### prisoma.heldout-quantized

- Evidence paths: `FINITE_ALPHABET_PLUGIN_CONVERGENCE.md`, `crates/pid-core/tests/fitted_quantized_sxpid.rs`.
- Required negative challenges:

  - Reject same-row fitting as a held-out estimator.
  - Reject a claim about the original continuous representation after quantization.
  - Reject adaptive quantizer selection outside the frozen-map theorem.

#### prisoma.local-assurance

- Evidence paths: `KNOWN_LIMITATIONS.md`, `audit/evidence/assurance-registry.json`.
- Required negative challenges:

  - Reject an f64 sign as certified when a rigorous enclosure contains zero.
  - Reject bounded tests as a deductive Rust refinement proof.

#### prisoma.mixed-support

- Evidence paths: `KNOWN_LIMITATIONS.md`, `crates/pid-runlog/tests/scientific_contract.rs`.
- Required negative challenges:

  - Reject a mixed categorical-target and continuous-source request with an explicit unavailable outcome.
  - Do not substitute continuous PID2, quantized PID, or a numeric sentinel.

#### prisoma.row-law

- Evidence paths: `DEPENDENCY_COLORED_SXPID_CONCENTRATION.md`, `KNOWN_LIMITATIONS.md`.
- Required negative challenges:

  - Reject pairwise-only independence, adaptive colors, unspecified mixing, and stale row identities.
  - Reject an observed support floor as a population support guarantee.

#### prisoma.uncertainty

- Evidence paths: `KNOWN_LIMITATIONS.md`, `crates/pid-core/tests/sxpid_bootstrap.rs`.
- Required negative challenges:

  - Reject exploratory bootstrap percentiles as generic calibrated confidence intervals.
  - Reject a vacuous concentration radius as informative uncertainty.
  - Reject an empirical minimum frequency as the unknown population support floor.

## Claims not made

- Compatibility with current or historical consumer code.
- Consumer integration or deployable adapters.
- Scientific validation of consumer data, preprocessing, or estimands.
- Sequential, alerting, mission, or authorization suitability.
- Authenticity or freshness of consumer repositories beyond the bound historical snapshot.
- Independent review or holdout qualification.
- NCP compatibility or any NCP peer, provider, consumer, transport, authority, or role-receipt status.

The release scope also contains `external-authority`. This contract excludes it because it is not one of the four audited consumers. Its release-scope status remains `not_claimed`.
