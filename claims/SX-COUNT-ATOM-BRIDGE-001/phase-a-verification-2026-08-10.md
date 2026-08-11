# Phase-A verification record, 2026-08-10

## Disposition

State: **complete within the supplied-count, fixed-two-source categorical formal scope**.

This receipt records the exact Lean, mutation, integration, and document evidence used for revision
2 of `SX-COUNT-ATOM-BRIDGE-001`. It binds evaluated file bytes and reported command outcomes. It
does not authenticate a release, establish a signed publication record, or extend the claim beyond
the residual boundary below.

The work was prepared on branch `review/sx-count-atom-bridge-r1` over base commit
`a28b2ef340095036c41ed1e8904ee84c88c28d9a`. The content digests below, rather than the mutable
branch name, identify the checked formal and PDF artifacts.

## Pinned formal environment

The finite-convergence project declares `leanprover/lean4:v4.32.0`. The checked runtime reported:

```text
Lean (version 4.32.0, arm64-apple-darwin24.6.0, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)
Lake version 5.0.0-src+8c9756b (Lean version 4.32.0)
```

The dependency manifest SHA-256 is
`e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd`; it pins Mathlib revision
`81a5d257c8e410db227a6665ed08f64fea08e997` and the complete dependency set enforced by
`scripts/check-lean-finite-convergence.py`.

| Bound artifact | SHA-256 | Bytes | Lines |
|---|---|---:|---:|
| `audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean` | `c0c92e4f9974b2770b3033a6ebca1d16939417707301aac4531a102649b7a16c` | 24,009 | 474 |
| `audit/formal/lean/PidFiniteConvergenceSemanticContract.lean` | `c1c8e21280c887667225d4837da341fefd42b031731d2fc334e0f3d178c80b0c` | 18,421 | 404 |
| `audit/formal/lean/PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean` | `ec8483d8719c0cdaa9c1300196b7f0e6fc3f370cbaf68dad99e998c6c27a59ba` | 47,370 | 974 |
| `audit/formal/lean/PidFiniteConvergenceSxPid2AtomSemanticContract.lean` | `dbe2e956f81b0e3ed3aa96b47577d1a5f1eda9d41ef8997cc594d4c1c6176076` | 23,716 | 475 |
| `scripts/check-lean-finite-convergence.py` | `f3226a0fc9c80938aeffe07ed1fd6ad8ca9ba4fe55f6e8d019672a5a6a00585b` | 51,821 | 1,185 |
| `scripts/check-lean-finite-convergence-self-test.py` | `7d08179db73628bb2ccb40d362440d77ba5bd0966df5fa77ad7120681c007c05` | 42,906 | 1,216 |

## Exact formal inventory

The aggregate project contains 11 checked Lean sources. Its root imports exactly eight formal
modules with the following bound declaration inventory:

| Imported module | Declarations | Named theorems |
|---|---:|---:|
| `Dependence.lean` | 20 | 19 |
| `Deterministic.lean` | 13 | 13 |
| `FractionalCover.lean` | 23 | 20 |
| `LocalContinuity.lean` | 88 | 66 |
| `SupportChangeContinuity.lean` | 44 | 37 |
| `SxEventBridge.lean` | 37 | 22 |
| `TwoSourceCountEventBridge.lean` | 38 | 24 |
| `TwoSourceMobiusAtomBridge.lean` | 76 | 45 |
| **Total** | **339** | **246** |

The established semantic contract contains 16 examples and five private definitions. The new
SxPID2 atom contract contains 11 examples, six private helper theorems, and seven private
definitions. Thus the two separately compiled contracts contain 27 examples in total. The checker
also audits the six named helper theorems against the permitted logical basis.

All 246 named source theorems were checked to use no assumptions outside the permitted subset of
`propext`, `Classical.choice`, and `Quot.sound`. In particular, all 24 count/event bridge theorems
and all 45 Möbius/atom bridge theorems passed that audit.

## Four formal replay gates

The following four commands were run with the pinned toolchain:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check-lean-finite-convergence.py
PYTHONDONTWRITEBYTECODE=1 python3 -O -B scripts/check-lean-finite-convergence.py
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/check-lean-finite-convergence-self-test.py
PYTHONDONTWRITEBYTECODE=1 python3 -O -B scripts/check-lean-finite-convergence-self-test.py
```

Both checker runs reported the same 11-source, eight-import, 339-declaration, 246-theorem
inventory; successful Lake build; Lean kernel replay; explicit unlimited-heartbeat compilation of
both semantic contracts; exact source bindings; and complete theorem-axiom audit.

Both self-test runs rejected all 71 registered changes:

```text
40 static source mutations
+ 5 baseline-first isolated count/event mutations
+ 17 baseline-first isolated Mobius/atom-module mutations
+ 9 baseline-first isolated atom-contract mutations
= 71
```

The new atom surface contributes 56 of those routes: 30 post-baseline static routes, 17 isolated
module routes, and nine isolated contract routes. Every isolated family first compiled an
unmodified copy, then required the changed copy to return nonzero Lean status with an error
diagnostic.

The required K2 minimum classes map to concrete registered routes as follows:

| Minimum | Registered route ID | Mutation function | Checked change |
|---|---|---|---|
| K2-06 | `K2-06-mobius-zeta-inverse-same-name-weakening` | `weaken_mobius_zeta_inverse_same_name` | Replace the inverse theorem with a same-name tautology; exact source binding rejects it. |
| K2-07 | `K2-07-coordinate-omission-duplication` | `omit_and_duplicate_coordinate` | Omit one coordinate and duplicate another. |
| K2-10 | `K2-10-net-subtraction-to-addition` | `change_net_subtraction_to_addition` | Replace signed-net subtraction with addition. |
| K2-12 | `K2-12-atom-product-quotient-to-multiplication` | `change_atom_product_quotient_to_multiplication` | Replace an atom-product quotient with multiplication. |
| K2-13 | `K2-13-product-comparison-reversal` | `reverse_product_comparison` | Reverse the product comparison used by a sign result. |
| K2-14 | `K2-14-log-product-positivity-premise-removal` | `remove_log_product_positivity_premise` | Replace the log-product nonzero premise with an invalid reflexive proof. |

The 71-route result is a finite sensitivity inventory. It is not an exhaustive proof that no
unregistered mistake can exist.

As a separate algebraic corroboration, the five existing Z3 PID2/PID3 lattice obligations returned
`unsat`. That solver route checks its own encoded identities; it is not a second derivation of the
Lean count/event or exact-product semantics.

## Checked mathematical result

For an arbitrary natural-valued count function on the complete finite key type of exactly two
possibly heterogeneous finite sources and one finite target, with positive total count, the checked
formal route covers:

- four cumulative nodes in order `[sourceOne, sourceTwo, jointSources, redundancy]`;
- four atoms in order `[uniqueOne, uniqueTwo, synergy, redundancy]`;
- three components in order `[informative, misinformative, net]`;
- the complete duplicate-free 24-coordinate surface;
- concrete Möbius and zeta coefficient tables and both inverse compositions over an additive
  commutative group;
- formula-only source-coordinate exchange and its involution/equivariance;
- informative, misinformative, and signed-net local count arguments;
- support positivity and `net = informative / misinformative` in the count-argument domain;
- finite weighted-sum/Möbius commutation;
- equality of every empirical cumulative and atom coordinate to its exact count expression;
- positive real products and exact rational products with proved cast agreement;
- uniform `(1/N) * log(product)` normalization; and
- positive, negative, and zero equivalences with product comparison to one.

A generic real-valued `law` in the algebraic layer denotes a support-restricted weighted sum. It
has an empirical-average interpretation only after specialization to the normalized nonnegative
empirical law induced by the supplied positive-total natural counts.

## Corrections and supersessions

Revision 1 remains preserved as a historical pre-integration hold and carries no current
authority. Revision 2 closes only the bounded scope recorded here.

An earlier atom-module candidate had SHA-256
`362ce9cdb168df6c07b0dff53493671d39a25b9f55a9a6bbc2943909f177dd57` and size 47,009 bytes. It was
superseded by the final `ec8483…` source through a docstring-only clarification: generic
real-valued laws are support-restricted weighted sums, and empirical-average language applies only
after the empirical-law specialization. No declaration, theorem statement, or proof body changed.
The checker was rebound to the final source bytes.

A prototype proof of `sx_pid2_mobius_row_sum` using `native_decide` was rejected after its generated
native-evaluator assumptions appeared in the axiom inspection. It supplies zero proof credit. The
final proof uses kernel `decide`, and a registered mutation confirms that reintroducing
`native_decide` is rejected.

The first atom semantic-contract draft did not compile and supplies zero replay credit. The
replacement uses an asymmetric eight-key binary fixture with three positive anchors of weights
one, two, and one. This makes the empirical exponent observable while exercising all local
arguments, cumulative products, 12 atom products, and scaled-log normalization.

The Rust source received only an order-clarifying comment: `NODES2` is cumulative
`[source1, source2, joint, redundancy]`, while `invert2` returns atoms
`[unique1, unique2, synergy, redundancy]`. No Rust logic, public API, or numerical result changed,
and no Lean-to-Rust refinement is inferred from that comment.

## PDF artifact bindings

Five formal papers affected by this integration were regenerated and checked:

| PDF | SHA-256 | Bytes | Pages |
|---|---|---:|---:|
| `finite-alphabet-plugin-convergence.pdf` | `9ffcf842e216b6e2cf9f226fa4bb4f059e2cec1cf8f5039c4290b49e6a53feb7` | 452,223 | 19 |
| `dependency-colored-sxpid-concentration.pdf` | `614259de0c3bfe9d8b37176d8e5fc13759840c1f01ece4a7ed9fcc1838a2216d` | 529,227 | 29 |
| `support-change-tolerant-averaged-sxpid-continuity.pdf` | `d2b3227444a0a610169b609ff5e7f3ecc930d5289ac7ff3a5504bf1a0f185d51` | 356,007 | 12 |
| `formal-tool-adoption-audit.pdf` | `73619ff2e7ac4a744e4c51f89a9fd23bb554ed4f6fd769937b516f4cb8e80656` | 381,351 | 22 |
| `two-source-sxpid-count-atom-bridge.pdf` | `7776f7d898738882b74724306afb4f76f3e6650d19044db27284cf705b0b824d` | 363,886 | 12 |

All five use A4 geometry (`595.276 × 841.89` points), for 94 reviewed pages in this integration.

The repository-wide command

```text
scripts/check-formal-pdf-set.sh --exact
```

checked the exact declared ten-source/ten-PDF inventory:

```text
certified-sxpid2-executable-assurance
dependency-colored-sxpid-concentration
ecosystem-compatibility-audit
exact-log-product-sxpid2-assurance
finite-alphabet-plugin-convergence
formal-tool-adoption-audit
foundational-shared-exclusions-pid-audit
mathematical-problem-solving-workflow
support-change-tolerant-averaged-sxpid-continuity
two-source-sxpid-count-atom-bridge
```

The aggregate gate enforces the shared visual system, source/inventory closure, strict LaTeX-log
policy, A4 geometry, embedded/subset/Unicode-mapped fonts, required bounded-scope text, and
same-toolchain byte reproduction. Its exact mode reported that every declared formal LaTeX source
has one warning-free same-toolchain-reproducible PDF. This is an artifact-construction result, not
a proof of mathematical truth. No cross-toolchain identity claim is credited here.

The final crosswalk review found and corrected one obsolete pre-rename theorem identifier in the
atom-paper source. The leaf gate now requires the exact current Lean declaration
`sx_pid2_mobius_coordinate_swap_equivariant` in the source and rendered text and rejects the old
`sx_pid2_mobius_source_swap_equivariant` spelling. A copied-source hostile mutation restoring the
obsolete spelling failed at that intended pre-render predicate with exit status 1.

### Page-level visual inspection

A second read-only same-workflow visual review inspected pages 1–19 of the exact finite-alphabet
PDF (`9ffcf8…`) and pages 1–29 of the exact dependency-color PDF (`614259…`) individually at
full 180-dpi render detail. Both files retained their expected byte identities, A4 geometry,
nonblank extracted text, and embedded, subset, Unicode-mapped fonts. No page had clipping,
overflow, overlap, collision, illegible prose or mathematics, broken table continuation,
header/footer defect, blank page, or actionable orphan. Finite-alphabet page 18 explicitly states
that the remaining complete-lattice task concerns the “three-and-higher-source SxPID lattice
beyond the fixed two-source supplied-count bridge,” so it does not reopen the accepted two-source
surface. The dependency-color paper kept its categorical and formal boundaries and did not transfer
its result to continuous families or a global binary64 theorem. This visual review is artifact QA
within the same workflow, not an independent proof.

A read-only same-workflow visual review inspected all 46 pages of the exact support-change
(`d2b322…`, 12 pages), formal-tool (`73619f…`, 22 pages), and corrected atom (`7776f7…`, 12 pages)
PDFs individually. Every page was A4; every font was embedded, subset, and Unicode-mapped; and
text extraction contained neither replacement glyphs nor CID placeholders. The review found no
clipping, overlap, truncated equation, illegible table or listing, header collision, corrupt font,
blank page, or actionable orphan. The formal-tool paper's path wrapping on page 5 and intentional
source-index whitespace on page 22 remained legible. The atom paper's coordinate listing on pages
7–8 and theorem crosswalk across pages 9–10 continued cleanly. Page 9 visibly and extractably
used `sx_pid2_mobius_coordinate_swap_equivariant`; the obsolete spelling was absent. The extracted
scope text retained the 339/246/71 inventories and the exclusions for component-atom
nonnegativity, heterogeneous source transport, rows-to-counts, Rust, binary64, other estimator
families, higher-source lattices, population conclusions, application validity, and scientific
priority. This visual review is artifact QA within the same workflow, not an independent proof.

## Catalog and assurance routing

The method catalog contains 73 rows and now includes the dedicated row
`validation.two-source-sxpid-count-atom-bridge`. Its enforced classification is:

- category `validation`;
- definition origin `project-defined`;
- implementation status `stable`;
- dependency only on `shared-exclusions.categorical`;
- release scope only `pid-core.stable.categorical`;
- no Rust or Python entry point; and
- no scientific-priority claim.

Catalog status `stable` is a release/API classification. It is not a claim of numerical stability,
binary64 accuracy, executable refinement, or a global floating-point error bound.

The paper-defined inputs are the Makkeh–Gutknecht–Wibral categorical shared-exclusions events,
informative and misinformative components, empirical averaging, and two-source Möbius atom
construction, together with the associated Gutknecht–Wibral–Makkeh part-whole organization. The
Lean types, coordinate orders, supplied-count interface, theorem factorization, contracts,
checkers, mutation registry, claim packet, and PDF gates are project-defined assurance.

No Williams–Beer `I_min` theorem or implementation is credited to this bridge. Other literature
used elsewhere in the repository does not transfer merely because it appears in the same catalog.
The integration checker requires the atom-bridge evidence set to occur in exactly
`pid-core.stable.categorical`; it rejects propagation into stable quantization, `I_min`, Shannon
invariants, continuous estimators, experimental PID3, or any other release family.

A catalog-wide attribution cross-check used the five paper records with Michael Wibral as an
author, excluding software records. Exactly nine paper-defined rows and two paper-derived rows
link those papers; 11 project-defined rows link them directly. Under the different, explicitly
transitive predicate “project-defined row with local code availability whose `depends_on` closure
reaches one of the nine paper-defined roots,” the count is 18. These counts describe direct
citation, scientific origin, and dependency closure respectively; they are not interchangeable,
do not transfer support from unrelated literature, and establish no scientific-priority or
all-literature novelty claim.

The method-catalog checker and its mutation suite, plus the assurance-registry checker and its
mutation suite, were run under normal and optimized Python after the active revision-2 paths were
installed. The registry tuple names the revision-2 claim, decision, obligations, routes, theorem
map, receipt, formal sources, report, PDF, and PDF checker. Revision-1 files remain historical and
are not the active tuple.

## Repository integration gates

The Rust change is comment-only, but the complete requested integration matrix was still replayed.
The following test configurations all passed:

```text
cargo test --locked --workspace --exclude pid-python
cargo test --locked -p pid-core --no-default-features
cargo test --locked -p pid-core --features parallel
cargo test --locked -p pid-core --all-features
cargo test --locked --release -p pid-core --all-features
```

`cargo fmt --all --check`, workspace/all-feature Clippy with warnings denied, both documented
`cargo doc` configurations, both docs.rs-style `cargo rustdoc` configurations, and explicit
`pid-core` and `pid-runlog` doctests also passed. The deterministic `ksg_and_pid` example reproduced
its documented values. The `exp0` smoke run completed with the expected descriptive high-dimensional
`NO-GO`/geometry `PIVOT` outcome, and the run-log validator accepted its 11 events with zero errors
or warnings; that diagnostic result is not part of the atom-bridge acceptance.

The software-identity checker and its 73-route mutation suite, the five PID algebra obligations and
five satisfiable algebra mutations, the release-scope checker and self-test, the KSG Lean/Z3 gates,
and both citation-edge countermodel routes also passed. These broader repository gates establish
integration consistency only; they do not enlarge the formal result or turn adjacent evidence into
support for this bridge.

## Review disposition

| Review role | Result |
|---|---|
| Formal source and theorem review | A separate read-only 40-lens review found no mathematical or Lean blocker; it checked the final module, dependency, contracts, permitted axiom bases, order/inverse/product/sign boundaries, and retained nonclaims. |
| Checker and mutation review | Exact bindings, declaration inventories, baseline-first isolation, mutation counts, and all six required K2 classes were cross-checked; no unresolved gate defect remained. |
| Provenance and integration review | The defining-paper/project-assurance split and categorical-only fanout were checked. Quantized, `I_min`, invariants, continuous, PID3, higher-source, and executable-refinement transfer remain excluded. |
| PDF review A | All 48 finite-alphabet and dependency-color pages passed exact-identity, A4/font/text, page-level layout, corrected open-work wording, and non-transfer review; no visual blocker remained. |
| PDF review B | All 46 support-change, formal-tool, and corrected atom pages passed exact-identity, A4/font/text, page-level layout, crosswalk, and non-transfer review; no visual blocker remained. |

These are separate read-only reviews within one repository workflow. They are not external peer
review, independent authorship, or mutually independent mathematical proofs. The count/event
module, atom module, and semantic contracts form one dependent Lean route. The Z3 algebra check,
mutation suite, catalog checks, and PDF checks inspect different properties but do not convert that
route into independent replications.

## Residual boundary

This acceptance does not establish:

- a theorem from publication text to the Lean definitions;
- universal nonnegativity of informative or misinformative component atoms, or any other universal
  atom-sign theorem;
- rows, bytes, files, tables, JSON, or serialization to the supplied count function;
- typed exchange of heterogeneous source data;
- Rust `NODES2`, `invert2`, accumulation, result-field, parser, or binary64 refinement;
- standalone-certifier, Python, compiler, runtime, hardware, or bounded-resource refinement;
- support-change transfer between two laws;
- sampling, concentration, uncertainty, consistency, calibration, population, or consumer validity;
- continuous shared-exclusions estimators, fitted quantization, `I_min`, or Shannon invariants;
- three-source or general higher-source lattices;
- scientific priority, uniqueness, application validity, release authority, or downstream
  readiness; or
- Lean kernel soundness or absence of every possible unregistered defect.

The sign equivalences classify a coordinate conditional on its exact positive product. They do not
prove which side of one any component-atom product must occupy.
