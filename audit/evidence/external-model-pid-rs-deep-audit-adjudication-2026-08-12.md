# External-model deep-audit intake and adjudication — 2026-08-12

Status: current review record; advisory evidence only
Repository baseline reviewed: `7e536f65822eecfb3f477cd675b857dc3fa3c373`
Intake/adjudication baseline: `bc071859472e4325aea7e5af185e1aaf974ceff1`

This record preserves and adjudicates an external model's review. It is not human, institutional,
formal, mathematical, scientific, security, or line-review credit. Findings were treated as
hypotheses and checked against repository bytes, executable gates, and primary papers. Agreement
between models is correlated evidence, not independence.

## Preserved inputs

| Artifact | Bytes | SHA-256 | Inspection |
|---|---:|---|---|
| `external-model-pid-rs-deep-audit-2026-08-12.md` | 97,481 | `c289373b23aeb521952101e9143d924b60316ccece6ab9be84c2ff2b9b0ebe71` | Parsed in full, 1,404 lines |
| `external-model-pid-rs-deep-audit-2026-08-12.pdf` | 185,287 | `3cf7457232eb4ba71ac93a1007fea003d61033a2f0caddab2963fa2175bf3fd2` | 29 A4 pages rendered and inspected; unencrypted; no forms or JavaScript |

The PDF's metadata names “OpenAI GPT-5.6 Pro” as author. That is provenance, not authority. The
review itself says it could not clone the exact tree, retrieve every blob, render the committed
PDFs, or inspect the authors' GitLab code. Repository-local rechecks therefore supersede its
unverified or stale observations.

Disposition vocabulary:

- **accept** — reproduced defect or worthwhile bounded improvement;
- **partial** — useful direction, but the proposed mechanism or scope is overbroad;
- **stale** — already closed or materially stronger in the intake baseline;
- **reject** — false, category-confused, unsafe, or contrary to repository policy;
- **defer** — valid work that requires an independently scoped future project.

## Finding-by-finding decision

| ID | Disposition | Reproduced result and bounded action |
|---|---|---|
| RB-01 | **accept; release blocker** | Reproduced: all 186 protected ledger rows are `UNASSIGNED` / `INVENTORIED_NOT_REVIEWED` while current prose said “reviewed source.” Correct current prose and fail-closed gates; preserve the immutable tag's historical wording without transferring review credit. |
| RB-02 | **accept; implemented locally, hosted closure pending** | Fragmentation was real. The tracked `current-source-state-v1` manifest excludes only itself and contains no commit identifier; the separate post-commit v2 checker binds its containing commit/tree/blob only after commit. Repository bytes are never passed to `compile`, `exec`, or `eval`. Hosted scan `31646328786` closed original alerts 181–183 without dismissal but exposed path authority in v1 as alerts 184–191. V2 removes every path-valued argument, emits only canonical standard output, validates only bounded canonical standard input, invokes a fixed-root child, and explicitly leaves storage/upload custody to its caller. Fixed schema-byte contracts and normal/optimized CLI-only hostile tests fail closed without suppression. Fresh hosted closure of 184–191 remains required. The Lean-bound operational reseal is append-only `r4`; finalized `r3` remains exact prior evidence, and `r4` receives no execution credit before its exact receipt exists and validates. Neither record implies generic schema validation, storage durability, authenticity, review, CI success, formal closure, or scientific validity. |
| RB-03 | **partial** | Correspondence edges remain open, but revision 1 already contains a 37-family, five-layer assurance registry. Version and extend that authority with typed edges; do not create a competing graph or call narrative length closure. |
| H-01 | **accept** | The four Ehrlich and four Schick-Poland source observations deserve a versioned registry, exact locators, statuses, tests, and explicit non-transfer boundaries. Reviewer-derived corrections are not author-confirmed errata. |
| H-02 | **partial** | Stable Python results are already structured; provenance-losing flat adapters are default-off migration surfaces. Keep them experimental/deprecated and remove before 1.0. Reject a generic `allow_provenance_loss` escape hatch. |
| H-03 | **partial** | Add a compact PID-only review protocol and index. Preserve the process compendium as a separately labelled case-study record; unrelated zeta/process evidence earns no PID credit. Do not destructively rewrite its historical evidence. |
| H-04 | **partial/stale in detail** | Current PDF gates already do exact builds, structure, fonts, navigation, dual renders, mutation controls, and visual receipts. Add one generated PDF-set manifest and consistent front-matter capsules prospectively; do not overwrite old PDFs or weaken exact gates. |
| H-05 | **accept as external dependency** | Implementation separation is not institutional independence. Before 1.0 assurance language, seek named human scientific and code dispositions with exact blob/scope bindings. This model review earns none of that credit. |
| H-06 | **partial** | The pinned authors' code is validation context, not a defining dependency. Preserve a license-compatible minimal snapshot or archival identifier if available. Do not make inaccessible third-party code load-bearing or claim author confirmation. |
| M-01 | **accept** | Generate a compact stable-first methods summary and a separate detailed evidence view from the existing catalog. Keep exhaustive `METHODS.md` machine-derived. |
| M-02 | **partial** | “Semantic authority” is an exact semantic freeze/change detector, not authenticity, review, or truth. Introduce clearer versioned audience labels without rewriting historical authority records. |
| M-03 | **partial** | `InformationUnit::Nats` already exists; no `Bits` variant currently exists. Use unit-bearing values in new standalone schemas and add/emit `Bits` only for a real bit-valued route; do not churn every internal `f64` or conflate unit safety with estimator validity. |
| M-04 | **partial** | PID2 already returns four aligned coordinates, a 4×4 local-contribution covariance, propagated atom covariance, and cancellation diagnostics, explicitly not sampling covariance. A generic duplicate-producing bootstrap is unsafe for fail-closed KSG. Research a no-replacement/aligned resampling route without calling it calibrated uncertainty. |
| M-05 | **accept, targeted** | Add residual/orthogonality/reconstruction/conditioning diagnostics and independent solver strata for PCA, PLS, and logistic regression. Existing SVD/PCA and adversarial tests remain evidence, not a universal oracle. |
| M-06 | **accept** | Add scheduled read-only aggregate dependency-compatibility reporting. Never auto-merge dependency changes or treat freshness as scientific correctness. |
| M-07 | **partial** | Workflow size alone is not a defect. Extract repeated shell logic into checked scripts with stable gate IDs; retain explicit job-to-claim mappings and pinned actions. |
| M-08 | **accept** | Every “independent” claim must state author, codebase, algorithm, runtime, input derivation, and shared assumptions. Rename same-repository Decimal/MPFR checks when they are only implementation-separated. |
| M-09 | **stale; reject broad form** | Current workflow already narrows the Cantor objection: Borel isomorphism alone does not supply the claimed ambient density; stronger mod-null constructions may salvage part. Do not claim universal impossibility. |
| M-10 | **stale** | Current source routing already separates published LCR results from later preprints and structural-impossibility context. Preserve that temporal/source boundary. |
| M-11 | **partial** | Give fitted equal-width quantizer edge semantics an explicit role/revision in serialized provenance. Do not invent equivalence between empirical categorical, exact-significand, and continuous estimands. |
| M-12 | **partial** | Same objective as RB-03. Version the existing assurance registry; avoid a second narrative/graph authority. |

## Primary-source adjudication

### Ehrlich et al. continuous shared exclusions

Against arXiv `2311.06373v3`, four printed-source observations are reproduced:

1. Equation (8) repeats the `S2` bin factor where the source-bin product requires `S1 × S2`.
2. The post-Definition-2 integral repeats `ds1`; the surrounding integrand/Appendix-D route requires
   the second source differential.
3. Equation (14)'s displayed digamma/log expression is in natural-log units; bit reporting needs a
   `1 / ln 2` conversion.
4. Algorithm 6 omits the antichain argument and applies a source-count routine to the target route.

These are **reviewer-derived printed-source corrections**, not author- or publisher-confirmed
errata. They do not prove estimator consistency, finite-sample bias, support validity, binary64
error, or paper-to-Rust refinement. The authors' code may corroborate intended wiring but cannot
retroactively repair or authenticate the paper.

### Schick-Poland et al. measure-theoretic construction

Against arXiv `2106.12393v2`, the finite-discrete conditional normalization, bimeasurable-to-
bicontinuous step, null-event RCP representative, and Borel-isomorphism-to-ambient-density steps
remain open. A stronger mod-null measure-space construction may address part of the last issue.
Therefore the truthful public description is: the arXiv v2 paper **proposes an
auxiliary-indicator/RCP/Radon–Nikodým construction for a finite source family under stated
Radon/Borel premises, intended to cover discrete, continuous, and mixed variables; pointwise
existence and version-independence at null conditioning events and for target-local
Radon–Nikodým representatives remain unadjudicated here**. This is not Ehrlich's kNN estimator,
MGW's empirical categorical functional, KSG, `I_min`, or a proof that a version-independent
arbitrary-support PID exists.

### MGW categorical SxPID correction to this external audit

The audit's line-636 XOR value is false. For fair XOR, exact MGW net atoms in bits are

| Atom | Exact value | Approximation |
|---|---:|---:|
| Red | `log2(2/3)` | `-0.5849625` |
| Unq1 | `log2(3/2)` | `+0.5849625` |
| Unq2 | `log2(3/2)` | `+0.5849625` |
| Syn | `log2(4/3)` | `+0.4150375` |

They sum to one bit. The primary MGW discussion says the synergy is reduced below one bit and the
two positive unique terms compensate negative redundancy. Repository exact-fraction fixtures and
the exhaustive-oracle generator reproduce these values. The audit's `1.58496` synergy is rejected.

### Other source boundaries

- Williams–Beer `I_min` remains a separate discrete redundancy measure and is not MGW SxPID.
- KSG's max-norm/joint-radius/strict-marginal-count arithmetic is paper-derived; tie rejection and
  support declarations are explicit project policies.
- Gutknecht parthood, Schick-Poland measure theory, Ehrlich analytic/kNN, MGW categorical SxPID,
  PID2/PID3 compositions, and project diagnostics do not transfer results without a typed mapping
  theorem closing the relevant correspondence edges.

## Module matrix adjudication

| Surface | Decision |
|---|---|
| `bootstrap.rs` | **partial:** preserve resource/cancellation contracts; require estimand and retained-failure policy for future calibrated routes. |
| `ci.rs` | **reject category error:** this is co-information, not confidence intervals or PID2 uncertainty. It already retains constituent reports and cancellation diagnostics. |
| `discrete_pid.rs` | **partial:** preserve `I_min`/SxPID separation; add unit/method identity to new serialization and expand exact lattice fixtures without conflating measures. |
| `distance_matrix.rs` | **partial:** make quadratic cost prominent; it remains a diagnostic, not a default large-sample neighbour backend. |
| `error.rs` | **accept:** stable machine codes and causal chains can improve Python/run-log fidelity without changing scientific claims. |
| `geometry.rs` | **stale:** current contracts already forbid geometry diagnostics from proving population support or estimator validity. |
| `hierarchy.rs` | **stale:** current surface is default-off exploratory and carries non-inferential warnings. |
| `hyperbolic.rs` | **partial/reject:** retain consistency nonclaims; a second exact hyperbolic backend does not exist, so generic “backend parity” is not a valid requirement. |
| `identity.rs` | **reject proposed signed-manifest centralization:** repository policy is unsigned and identity domains are deliberately separated. OIDC/detached attestations may be additive. |
| `invariants.rs` | **partial:** current names/prose separate published target-conditioned quantities from project analogues; strengthen future schema identities. |
| `isx.rs` | **accept:** bind implementation decisions to the source-errata registry and retain explicit Algorithm-6 count/unit evidence. |
| `kdtree.rs` / `nn.rs` | **mostly stale:** exact brute-force/tree radius and count parity already exists; extend only with missing `nextafter`/repeated-coordinate adversarial cases. |
| `ksg.rs` | **stale:** report-first routes already retain support disposition, shell/tie diagnostics, and project-policy warnings. |
| `lib.rs` | **partial:** continue stable/experimental namespace review; no evidence supports indiscriminate API deletion. |
| `logistic.rs` | **accept:** add iteration, gradient, conditioning, regularization, and external-solver strata. |
| `matrix.rs` | **reject:** checked constructors and Result-returning public/FFI boundaries already prevent the alleged user-dimension panic route. |
| `metric.rs` | **partial:** serialize/version metric and norm conventions where they define estimator identity. |
| `observation.rs` | **reject category error:** Gaussian-noise application is not a fitted transform and has no training role to record. |
| `par.rs` | **stale:** index ordering and serial/parallel bit identity are already specified and tested. |
| `pid2.rs` | **partial:** local covariance/cancellation already exists and is explicitly non-calibrated; sampling uncertainty remains open. |
| `pid3.rs` | **stale:** incomplete and research/full outputs already use distinct types/routes with no silent completion conversion. Public arbitrary-support wording still needs correction. |
| `pipeline.rs` | **partial:** strengthen explicit fit-role types where call-order inference remains; preserve current leakage guards. |
| `pls.rs` | **accept:** add independent numerical oracles and exact training/fold identity where a fitted artifact crosses a boundary. |
| `preprocess.rs` | **accept:** expose residual, orthogonality, reconstruction, and conditioning diagnostics across adversarial strata. |
| `quantizer.rs` | **partial:** version edge-generation semantics and fit role; preserve existing input/output hashes. |
| `report.rs` | **partial:** new versioned schemas should separate numeric value, evidence, and interpretation; avoid a breaking churn of already explicit reports. |
| `resource.rs` | **partial:** clarify preflight is not an allocator guarantee; record requested/approved estimates where observable, not fictional high-water measurements. |
| `same_sample.rs` | **stale/reject escape hatch:** current unmistakable experimental type is correct; do not add an “unsafe inference acknowledgement” conversion. |
| `stats.rs` | **reject category error:** internal numerical helpers are not the multiplicity/null API; those contracts live in `pipeline.rs`. |
| `support.rs` | **stale:** declarations and one-sided diagnostics are already separated and explicitly do not prove population support. |
| `sxpid.rs` | **partial:** exact/high-precision canonical fixtures are already extensive; add source-claim IDs and universal cancellation diagnostics prospectively. |
| Python bindings | **partial:** keep structured stable returns; retire default-off lossy legacy adapters before 1.0. |
| Run logs | **stale in part:** signature/attestation references and external anchors exist; continue to deny authenticity from same-repository hashes. |
| CI/workflows | **partial:** preserve pinned/narrow workflows; extract repeated mechanics and generate a claim-to-gate view without weakening gates. |

## Cross-cutting and test recommendations

| Proposal | Decision |
|---|---|
| Separate numeric value, evidence, interpretation | **partial:** already present in report-first APIs; make it the rule for new schemas and explicitly lossy adapters. |
| Stable negative capability taxonomy | **accept:** preserve fail-closed unsupported/research-only routes with source-backed reasons. |
| Same-sample descriptive isolation | **stale:** already a separate experimental type/route; retain it. |
| Universal signed-atom cancellation diagnostics | **accept, staged:** PID2/co-information already have them; extend where numerically meaningful without zero clamping. |
| Source-erratum mutations | **accept.** |
| Paper-symbol correspondence maps | **accept via assurance-registry v2**, not a second authority. |
| Quantizer boundary corpus | **accept:** include `nextafter`, signed zero, subnormals, huge ranges, repeated extrema, and round trips. |
| Exact backend parity | **accept where two exact backends exist**, not for unrelated metric implementations. |
| PCA/PLS/logistic oracle strata | **accept.** |
| Joint PID2 resampling | **research/defer:** retain covariance and failure pattern; do not label generic duplicate-sensitive bootstrap calibrated. |
| Documentation truth mutations | **accept; RB-01 implements the first set.** |
| PDF visual regression | **mostly stale:** current release PDFs already have exact and visual controls; unify manifests prospectively. |
| Consumer-loss tests | **accept for remaining lossy experimental adapters.** |
| Wrong-but-type-correct formal statements | **accept:** existing hostile suites are strong; add per new claim edge. |

## Release/supply-chain adjudication

- **Reject signed tags:** repository policy and release gates require unsigned commits/tags. Do not
  reverse that silently. Detached named-reviewer dispositions and GitHub OIDC artifact attestations
  are compatible additions.
- **Accept named external review as an open dependency:** require exact blob, claim, role, and
  independence-vector scope; “two reviewers” alone is not a proof.
- **Accept actual-release SBOM/provenance and clean-archive evidence bundles** when registry/binary
  artifacts exist. Do not pretend the source-review prerelease shipped them.
- **Accept PDF MIME/downloadability checks** for release assets; local exact reproduction remains a
  separate predicate.
- **Accept scheduled dependency visibility**; reject automatic scientific approval from dependency
  freshness.

## Twenty-lens review

| Lens | Conclusion |
|---|---|
| 1. Identity/temporal | Bind exact revision and artifact; never transfer tag facts to later `main`. |
| 2. Scientific object | Name exact measure/estimator/diagnostic; MGW, Schick-Poland, Ehrlich, KSG, PID2/PID3, and `I_min` are distinct. |
| 3. Primary-source fidelity | Four Ehrlich and four Schick-Poland observations reproduced; all remain reviewer-derived. |
| 4. Correspondence | Paper→spec→formal→implementation→binary/application edges are non-transitive and often open. |
| 5. Mathematical correctness | Reject the audit's XOR synergy; preserve signed MGW atom values and reconstruction. |
| 6. Estimator/support | Support declarations and sample diagnostics do not prove population regularity or consistency. |
| 7. Units/types | Nats are core; structural unit identity should grow prospectively, not through blind renaming. |
| 8. Numerical stability | Signed cancellation and solver residual/conditioning evidence deserve expansion. |
| 9. Uncertainty/calibration | PID2 local covariance is descriptive, not sampling covariance; calibration remains open. |
| 10. API/provenance | Structured reports are strong; retire remaining provenance-losing adapters. |
| 11. Negative capability | Unsupported/research-only routes are an asset and must remain fail closed. |
| 12. Formal boundary | Lean/Z3/exact-real results prove named objects only, not source correspondence or Rust refinement automatically. |
| 13. Tests/mutations | Keep negative controls; add erratum, correspondence, consumer-loss, and solver-strata mutations. |
| 14. Backend/language | Require exact parity only for genuinely equivalent implementations and disclose shared inputs/code. |
| 15. Documentation | Add compact PID-only and methods views; retain exhaustive evidence outside the primary reading path. |
| 16. PDF/artifact | Existing controls are strong; unify manifests/capsules and keep human visual review distinct. |
| 17. Reviewer independence | Model review is advisory/correlated; named human/institutional independence remains absent. |
| 18. Security/supply chain | Preserve pinned actions, least privilege, secret scans, unsigned policy, and domain-separated identity. |
| 19. Release truth | Current source-offer correction is mandatory; immutable historical wording stays historical. |
| 20. Ecosystem/downstream | No downstream compatibility, validity, or application transfer without explicit consumer evidence and a mapping theorem. |

## Immediate accepted work and nonclaims

Immediate work is tracked in `wibral-pid-program-active-plan-2026-08-12.md`. Acceptance into that
plan does not mean implementation, validation, review, or release completion. Rejected and stale
items remain recorded here so they are not repeatedly reintroduced under new wording.
