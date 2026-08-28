<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
    <img alt="pid-rs logo" src="assets/logo-light.svg" width="200">
  </picture>
</p>

<h1 align="center">pid-rs</h1>

<p align="center">
  <strong>Shared-exclusions partial information decomposition and mutual-information estimators in Rust.</strong>
</p>

> **Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE.** Version `0.9.0` is the first public
> source-review prerelease. It provides the exact source offered for review, proposed-1.0 scope
> records, release provenance, and checksums for reviewer feedback. `Source review` names the
> prerelease's purpose, not a completed review. The later 186-row tag-file inventory records every
> file as `UNASSIGNED` and `INVENTORIED_NOT_REVIEWED`. It is identity/coverage metadata only, not
> evidence of completed line, model, human, formal, or scientific review. Model review is advisory
> and is not independent human or institutional review. The immutable `v0.9.0` tag preserves its
> original wording; this correction does not rewrite tag history. The prerelease contains no
> registry packages, wheels, binaries, SBOMs, or docs.rs publication.

Distribution is GitHub-only: crates.io and PyPI are not published for this 0.9.0 review prerelease.
This 0.9.0 review prerelease makes no 1.x compatibility promise.

Author and maintainer: **Sepehr Mahmoudian**. The 0.9 review release has no software DOI or Zenodo
record; those identifiers are intentionally deferred until after review.

Earlier pre-review tag refs were retired during repository cleanup. Their peeled commits remain in
Git history and the changelog links to immutable commit IDs; no earlier GitHub Releases existed.

<p align="center">
  <a href="https://github.com/sepahead/pid-rs/actions/workflows/ci.yml"><img src="https://github.com/sepahead/pid-rs/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="#license"><img src="https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg" alt="License: MIT OR Apache-2.0"></a>
  <img src="https://img.shields.io/badge/rustc-1.89%2B-orange.svg" alt="MSRV 1.89">
  <img src="https://img.shields.io/badge/pid--core-unsafe%20forbidden-success.svg" alt="pid-core: unsafe forbidden">
</p>

`pid-rs` exposes two distinct shared-exclusions constructions that share notation but are not
identified by a general mapping theorem:

- stable direct empirical-PMF categorical SxPID, including the pointwise informative,
  misinformative, and signed-net construction of Makkeh, Gutknecht & Wibral (2021); and
- the default-off, gauge-dependent continuous functional of Ehrlich et al. (2024), estimated by a
  source-disjunction k-nearest-neighbour procedure adapted from KSG-style counting.

Continuous PID2 separately combines the Ehrlich redundancy estimate with three KSG mutual-
information coordinates. Neither shared notation nor shared kNN machinery identifies any of these
functionals or estimators.

It also supplies diagnostics and statistics needed to assess a result: geometry checks, Shannon
invariants, explicitly declared resampling distributions, typed permutation/surrogate nulls,
multiple-testing correction, preprocessing, and structured run-logs. Generic resampling summaries
are descriptive unless a statistic-specific calibration theorem is supplied. The estimator core is
safe Rust (`#![forbid(unsafe_code)]`) and reports all information quantities in nats.

## Method provenance and claim boundary

**“New in pid-rs” means an implementation, API, composition, diagnostic, or engineering contribution
new to this repository; it is not a claim of scientific novelty.** The exhaustive, versioned map
from methods to papers, external reference code, Rust/Python entry points, feature gates, repository
contributions, and unsupported requests is [`METHODS.md`](METHODS.md). Its machine-readable source
is [`method-catalog.json`](method-catalog.json).

The scoped, junior-facing [mathematical results guide](MATHEMATICAL_RESULTS_GUIDE.md) and its
[human PDF](output/pdf/mathematical-results-guide.pdf) map eight result families to their exact
objects, assumptions, formulas, evidence, costs, uses, nonclaims, and governing sources. The guide
keeps categorical MGW shared exclusions, continuous Ehrlich shared exclusions, Williams–Beer
$I_{\min}$, BROJA, and KSG in separate semantic lanes. It is a navigation layer, not a replacement
for the method catalog, claim packets, or detailed proofs.

The source-pinned [research blueprint](PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md) and
its [derived human PDF](PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf) document the
PrimeGaps proof-engineering review, semantic nontransfer firewall, exact categorical SxPID3
proposal, autoresearch protocol, formal-tool limits, and durable branch/worktree promotion process.
Its [machine-readable transfer ledger](audit/evidence/primegaps-to-pid-transfer-ledger-v1.json)
binds the 20-lens review and exact anchors. The SxPID3 Programs A--E remain open; these artifacts are
a research design and audit record, not an accepted higher-source certificate or evidence for KSG,
continuous PID, population inference, or scientific novelty.

The [ecosystem capability and gap matrix](ECOSYSTEM_CAPABILITIES.md) projects this catalog and the
assurance registry onto four exact historical consumer snapshots. Its
[machine-readable contract](ecosystem-capabilities.json) records retained boundaries and missing
evidence. Every consumer integration remains `not_claimed`. The matrix does not establish current
compatibility, integration, qualification, operational validation, or application validity.
It also classifies pid-rs as a standalone, protocol-neutral library and tooling project: pid-rs is
not an NCP peer, provider, or consumer and receives no NCP role receipt.

The catalog uses these distinctions consistently:

| Label | Meaning |
|---|---|
| Paper-defined | The mathematical quantity or estimator is defined in a cited publication. |
| Paper-derived | pid-rs composes published quantities or algorithms; the composition itself may have no dedicated paper or theorem. |
| Project-defined | The diagnostic, contract, report, or workflow is specified by this repository and is not presented as a published mathematical method. |
| External reference code | A cited authors' or independent implementation is used for bounded comparison; it is not vendored or silently treated as proof. |
| No implementation | The request is explicitly unsupported; no feature flag or status label implies hidden code. |

Selected boundaries that are easy to confuse:

| Surface | Provenance and code/paper status |
|---|---|
| Categorical SxPID | Paper-defined shared-exclusions functional; stable direct empirical-PMF implementation. Abzinger/SxPID is external reference code. |
| Typed SxPID interpretation | Project-defined API and serialization contract: pointwise and empirical-PMF-averaged atoms have distinct types and carry an explicit claim boundary. It changes no paper-defined atom or numerical estimator. |
| Fitted quantized categorical PID | Project-defined compositions of fitted equal-width transforms with categorical SxPID or $I_{\min}$; stable code for declared quantized estimands, with no dedicated estimator paper claimed. |
| Certified categorical SxPID2 reference | Project-defined, source-only audit tool for canonical exact count tables. It reconstructs all 24 averaged two-source informative, misinformative, and signed-net cumulative/atom expressions and returns directed MPFR dyadic enclosures under an explicit trust boundary. It does not certify `pid-core` binary64 output, population inference, higher-source or continuous PID, or downstream validity. See the [tool contract](audit/tools/certified-sxpid/README.md), [conditional-assurance paper](audit/formal/latex/certified-sxpid2-executable-assurance.tex), and [rendered PDF](output/pdf/certified-sxpid2-executable-assurance.pdf). |
| Two-source categorical SxPID count-to-atom formal bridge | Project-defined Lean assurance over paper-defined categorical quantities. From supplied exact positive-total counts it covers all 24 fixed informative, misinformative, and signed-net cumulative and concrete Möbius-atom coordinates, exact products, and sign/zero equivalences. It does not prove publication-to-Lean correspondence, component-atom nonnegativity, rows-to-counts, Rust/binary64/parser/certifier refinement, support-change transfer, a higher-source result, or population validity. See the [formal audit](audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md). |
| Finite-alphabet plug-in convergence | New project-defined theoretical-validation note for existing paper-defined PID functionals and selected Shannon quantities. It defines no new estimator and makes no scientific-novelty claim. See the [proof and evidence boundary](FINITE_ALPHABET_PLUGIN_CONVERGENCE.md). |
| Support-change-tolerant averaged categorical SxPID continuity | Project-defined exact-real validation of the paper-defined categorical functional. On one fixed complete finite Cartesian-product alphabet and fixed full redundancy lattice, joint-law-averaged informative, misinformative, and signed net cumulatives and atoms admit explicit total-variation moduli across support creation and deletion without a positive population cell-mass floor. Pointwise disappearing-key values, changing alphabets or quantizers, binary64 refinement, estimator calibration, scientific priority, and consumer validity remain outside the claim. |
| SxPID concentration under a dependency coloring | New project-defined validation for the paper-defined categorical SxPID functional. “Coloring” qualifies the sampling theorem, not PID: there is no measure called “colored PID,” and the label is not attributed to Makkeh, Gutknecht, or Wibral. It adds no estimator or public API. It includes one-$\Lambda$ cumulative bounds, general-source Möbius-row bounds, and complete two-source bounds. Exact diamond analysis sharpens only the synergy modulus to $\Lambda-\eta$. The [derivation](DEPENDENCY_COLORED_SXPID_CONCENTRATION.md), [LaTeX source](audit/formal/latex/dependency-colored-sxpid-concentration.tex), [PDF](output/pdf/dependency-colored-sxpid-concentration.pdf), [Lean local-continuity core](audit/formal/lean/PidFiniteConvergence/LocalContinuity.lean), [fraction-exact and high-precision generator](scripts/generate-dependency-colored-sxpid-oracle.py), and [bounded Rust implementation comparison](crates/pid-core/tests/dependency_colored_sxpid_oracle.rs) state separate evidence boundaries. |
| Continuous shared exclusions / PID2 | Ehrlich et al. define the redundancy estimator and two-source atom reconstruction. pid-rs implements that paper-defined core experimentally and adds project-defined report, split-sample, and cross-fit contracts. |
| Incomplete / full continuous PID3 | The incomplete result is a project-defined availability diagnostic, not a complete PID. The full lattice is research-only reference reproduction whose mixed-dimensional branches lack a general consistency result. |
| General mixed-variable shared exclusions | Schick-Poland et al.'s arXiv v2 proposes an auxiliary-indicator/RCP/Radon–Nikodým construction for a finite source family under stated Radon/Borel premises, intended to cover discrete, continuous, and mixed variables. pid-rs neither implements it nor adjudicates pointwise existence or version-independence at null conditioning events or for target-local Radon–Nikodým representatives. Barà et al.'s narrower discrete-target/continuous-source estimator is not implemented here. |
| Heuristics / Lorentz KSG | Heuristics are project-defined research baselines; Lorentz KSG is a paper-derived research adaptation. Neither has a pid-rs consistency result for the claimed target setting. |
| Shannon redundancy/vulnerability | Target-conditioned $\bar r$ and $\bar v$ follow the cited Shannon-invariants work. Target-free $\mathrm{Red}^{\circ}$ and $\mathrm{Vul}^{\circ}$ are project-defined entropy-ratio analogues, not those published target quantities. |
| Resampling and testing | Moving-block bootstrap, permutation schemes, and BH/BY use cited or standard procedures; pid-rs adds typed assumptions, failure retention, and provenance, not a generic calibration theorem. |
| Run logs and Python bindings | Project engineering around the estimator code; no statistical-method paper is claimed for the schema, replay tooling, wrappers, or result classes. |
| Software identity | Project-defined software infrastructure with stable local Rust and Python code; it has no defining method paper and makes no scientific-novelty claim. |

For two sources, the four averaged atoms reconstruct the joint mutual information:

$$
I(S_1,S_2;T)
=\mathrm{Red}+\mathrm{Unq}(S_1)+\mathrm{Unq}(S_2)
+\mathrm{Syn}.
$$

Pointwise and averaged SxPID atoms are deliberately different public types. A
`SxPointwiseAtom` belongs to one distinct positive-mass joint realization under the complete
supplied PMF; repeated input rows contribute to that realization's empirical probability rather
than creating different pointwise values. Its containing record retains `empirical_count` and
`empirical_probability`. An `SxAveragedAtom` is the empirical-PMF plug-in expectation

$$
\Pi^\pm(\alpha)
=\sum_r\widehat p(r)\pi^\pm(r,\alpha),
\qquad
\Pi(\alpha)=\Pi^+(\alpha)-\Pi^-(\alpha).
$$

It is not, in general, a mutual information, a population expectation, or an unbiased population
estimate; unobserved states are absent and no finite-sample bias correction is applied. Both types
retain the paper-defined informative and misinformative Möbius components, while `net_nats()` is
derived from them. Exact-real components are non-negative, but Möbius subtraction can leave a tiny
negative binary64 residual at zero, and the sign of a much smaller net can be unresolved when its
components nearly cancel. Use a scale-aware tolerance; values are never clamped.

Their serialized `SxAtomInterpretation` is a **project-defined** contract that names the
shared-exclusions SxPID measure and records aggregation scope, antichain-coordinate semantics,
statistical-information domain, and the need to retain the containing coordinate/realization
record. It also states that an atom alone establishes none of intentional deception, causal
effect, fault attribution, per-source responsibility, measure-independent decomposition, or an
unbiased population estimate. Those exclusions are software interpretation guards, not a new
theorem or a claim attributed to the defining paper. A bare atom omits its concrete coordinate and,
for pointwise output, its realization; extracting a bare `f64` discards the remaining contract.
Source/target names, complete matrix shapes, and input hashes must be supplied by the caller or a
run log rather than inferred from this categorical result.
Persisted consumers must require the exact supported interpretation-contract revision; treating a
higher unknown revision as compatible would defeat the fail-closed vocabulary.

Categorical three- and four-source decompositions use the full redundancy lattice: 18 and 166
atoms, respectively. The continuous 18-atom extension is retained only behind the explicit
mixed-dimensional research gate described below.
[Lyu, Clark & Raviv (2026)](https://doi.org/10.1103/8rzp-w5z1) show why this computability claim
must remain separate from satisfying every desired cross-subsystem consistency property of a
multivariate lattice PID. Their result is not, by itself, evidence of a code defect or a direct
refutation of categorical SxPID.

## Finite-alphabet plug-in convergence (new project analysis)

The [finite-alphabet plug-in convergence note](FINITE_ALPHABET_PLUGIN_CONVERGENCE.md) proves an
exact-real result for fixed finite alphabets and fixed lattices. It covers categorical SxPID for
2–4 sources, Williams--Beer $I_{\min}$ for 2–3 sources, and finite-alphabet Shannon entropy, mutual
information, co-information, and O-information. Under i.i.d. or strictly stationary and ergodic
sampling, the prefix plug-in quantities converge almost surely. Normalized ratios also need a
strictly positive population denominator. The paper-defined PID and Shannon quantities keep the
origins listed in [METHODS.md](METHODS.md); only this validation analysis is new in pid-rs. The
note retains the derivations, counterexamples, and rejected stronger claims for later audit.
The same result has a standalone [LaTeX paper](audit/formal/latex/finite-alphabet-plugin-convergence.tex)
and a checked [PDF rendering](output/pdf/finite-alphabet-plugin-convergence.pdf).

For i.i.d. data, the note also gives a conservative time-uniform envelope from Hoeffding's
inequality and union bounds. A usable support-stabilization time needs a known positive lower bound
on the smallest supported cell mass, $p_{\min}$. A training artifact must be independent of the raw
evaluation sequence. The frozen map must be measurable with respect to the training sigma-field
and raw input. It must return a valid finite output with conditional probability one. Evaluation
rows must be conditionally i.i.d. given the training sigma-field.

The pinned Lean project checks the deterministic exact-real continuity core, heterogeneous keyed
categorical events, a finite equivalence-union load theorem, and supplied-count bridges for
categorical SxPID. For every natural-valued count function with positive total on a complete finite
two-source key space, the first bridge derives the four signed-net averaged cumulatives from exact
event counts. A separate
[count-to-atom bridge](audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md) fixes all 24
informative, misinformative, and signed-net cumulative and concrete Möbius-atom coordinates, proves
the concrete two-source inversion and averaging algebra, constructs exact rational and real
products, and reduces every coordinate's sign and zero to comparison of its product with one.
Event and paper-facing semantics are a reviewed repository transcription, not an independently
derived publication-correspondence theorem. Component-atom nonnegativity, rows or bytes to counts,
Rust, binary64, support-change transfer between laws, more than two sources, and population
validity remain out of scope. The checker inventories all 339 source declarations across eight
imported modules, audits all 246 named source theorem axiom bases, SHA-256-binds both supplied-count
bridges, and separately compiles digest-pinned semantic contracts. Contract examples are not
counted as named-theorem axiom audits. A separate 100-digit Decimal generator and
companion Rust test
compare a bounded set of 2-, 3-, and 4-source SxPID tables, 2- and 3-source $I_{\min}$ tables, tie
crossings, realization-key changes, and pointwise omission of an absent realization on the listed
support face. The Rust test separately checks fitted-quantizer wrappers against direct categorical
calls. This evidence is not a general proof or a global floating-point error bound.

This base result does not establish binary64 asymptotic convergence, dependence or drift
guarantees, validity for sliding windows, same-row or changing-transform fitting, arbitrary fold
pooling, or statistical calibration. It is not a scientific-novelty claim.

### Support-change-tolerant averaged SxPID continuity (new project analysis)

The
[support-change-tolerant theorem](SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md)
keeps one complete finite Cartesian-product alphabet, source count, keyed event map, and full
redundancy lattice fixed while probability cells enter or leave support. It applies to
joint-law-averaged informative, misinformative, and signed net cumulatives and atoms. It does not
apply to pointwise values at disappearing realization keys, changing alphabets, or changing
quantizers. It removes the positive support-mass-floor premise only from this exact-real averaged
deterministic transfer.

Write $\eta=d_{\mathrm{TV}}(p,q)$. For each fixed finite system, the component envelopes have
leading order $\eta\log(1/\eta)$ and the signed-net envelopes have leading order
$2\eta\log(1/\eta)$; the fixed branch and Möbius terms are
$O_{\mathcal F}(\eta)$. Fixed-system, fixed-atom witnesses show that any family covering the
displayed systems with a common leading coefficient needs at least one for components and at
least two for signed net atoms. This is worst-case leading-order optimality only. It does not say
that every atom attains these coefficients, make lower-order or complete moduli sharp, or produce
an alphabet-independent bound. The coefficients change if distance is restated using
$\lVert p-q\rVert_1=2\eta$.

The [revision-3 claim](claims/SX-SUPPORT-FREE-CONTINUITY-001/claim-v3.md) and retained
[counterexamples](claims/SX-SUPPORT-FREE-CONTINUITY-001/failures/exact-counterexamples.md)
record why there is no global linear modulus, pointwise support-boundary theorem, active-face
entropy substitution, signed-residual maximum shortcut, arbitrary truncated-lattice transfer, or
alphabet-independent modulus. The historical packet identifier contains `SUPPORT-FREE`, but
user-facing claims use **support-change-tolerant** because the alphabet, event map, and lattice
remain fixed.

The result has a standalone
[LaTeX paper](audit/formal/latex/support-change-tolerant-averaged-sxpid-continuity.tex) and
[reproducible PDF](output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf).
Lean checks [finite-vector algebra](audit/formal/lean/PidFiniteConvergence/SupportChangeContinuity.lean),
the exact [heterogeneous keyed event map](audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean),
and the [finite equivalence-union load bound](audit/formal/lean/PidFiniteConvergence/FractionalCover.lean)
with source, target-restricted, and target-event corollaries. The separate
[two-source count/event bridge](audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean)
starts from supplied exact natural counts with positive total and checks the four fixed two-source
signed-net cumulative logarithms and positive-support averages. The further
[count-to-atom bridge](audit/formal/lean/PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean)
checks all 24 informative, misinformative, and signed-net cumulative and concrete Möbius-atom
coordinates, their exact rational and real products, and uniform scaled-log sign and zero
equivalences. Neither bridge proves the support-change logarithmic transfer between laws, the
published component-atom nonnegativity theorem, rows or bytes to counts, Rust or floating-point
refinement, certifier/parser execution, higher-source lattices, or statistical and population
validity.

An implementation-separated
[generator](scripts/generate-support-change-tolerant-sxpid-oracle.py) uses exact rational structure
and high-precision Decimal logarithms. Its digest-bound corpus contains 18 law pairs and replays 36
count tables through the stable two- through four-source categorical route. It retains equality
witnesses, support creation and deletion, endpoint records, falsifiers, and every returned
coordinate. The
[Rust replay](crates/pid-core/tests/support_change_tolerant_sxpid_oracle.rs) is bounded conformance
evidence, not the analytic proof, an executable refinement theorem, an interval-certified
binary64 result, or independent review.

The deterministic modulus can consume a separately justified law-distance radius. For the
result under a dependency coloring below, total variation is at most $D_n/2$ only on the declared
law-distance event. This composition does not validate the coloring, remove an explicit drift
bias, remove the exponential alphabet factor, or calibrate repeated alerts.

### Categorical SxPID under a dependency coloring (new project analysis)

The separate
[SxPID concentration analysis under a dependency coloring](DEPENDENCY_COLORED_SXPID_CONCENTRATION.md)
gives a separate result for a declared deterministic coloring. All complete source-target rows
must share one common finite law. The rows in each nonempty color class must be mutually
independent.
Dependence across colors can be arbitrary. For class sizes $n_j$, it uses the exact proof proxy

$$
V_n=\left(\sum_j\sqrt{n_j}\right)^2
$$

and gives a finite-sample empirical-law tail, a telescoping all-prefix envelope, an explicit
average-law drift term, and local common-support SxPID atom bounds. The local result gives one
$\Lambda$ bound for each cumulative informative, misinformative, or net term. It transfers this
bound through the exact Möbius row norm for a general source count. For two sources, redundancy
and unique information retain the $\Lambda$ bound. Exact ordinary- and conditioned-diamond
analysis gives the smaller synergy modulus $\Lambda_{\mathrm{syn}}=\Lambda-\eta$ and sharper
averaged synergy caps. This pointwise-key route still requires support containment and a positive
population support floor. The separate averaged support-change-tolerant theorem above removes
that floor only from its deterministic averaged transfer on a fixed complete alphabet. These are
new project-defined validation results for the published functional. They are not new PID
definitions, estimators, or scientific-priority claims. In particular, “dependency coloring”
describes the sampling assumption and concentration proof; it does not name a “colored PID”
measure and is not terminology attributed to the SxPID authors. A fixed-width finite-output map of i.i.d.
innovations is one valid corollary when residue classes use disjoint innovation blocks.
The displayed envelope proves almost-sure exact-real plug-in consistency under the sufficient
condition
$V_n\log(n)/n^2\to0$; a fixed color count is sufficient. The displayed drift envelope proves
convergence to a fixed reference law when that sufficient condition holds and the explicit bias
term tends to zero. These are not necessary conditions under a stronger sampling theorem.

The result does not cover pairwise-only independence, data-adaptive colors, circular windows,
an unspecified mixing premise, continuous SxPID, or a support floor estimated from the same rows.
Its Lean modules check deterministic exact-real subclaims only. They do not formalize probability,
path integration, SxPID identification, the published component-nonnegativity theorem, or the
analytic identification of the conditioned-diamond coordinates with net SxPID synergy. Lean proves
the exact ordinary-diamond diameter; the exact candidate-extrema form, sharp union-reciprocal
bound, and normalized corollaries for the eight conditioned-diamond coordinates; the exact
five-coordinate conditioned-nested diameter; and the refined logarithmic linearization chain.
The conditioned-nested zero-side-mass witness is algebraic only. It is not a supported
common-law perturbation or an SxPID-realizability claim. The
standard-library generator uses exact rational arithmetic for finite identities and 400-digit
Decimal arithmetic for logarithms. It audits all 64 ordered conditioned-diamond coordinate pairs
in each of seven rational cases, plus the ordinary-diamond and conditioned-nested exact identities
on the same inputs. The cases include zero-lift and unnormalized algebra-only boundaries. It
reconstructs three counterexamples where the endpoints are valid but one componentwise lift is
negative. Nine cases with six positive displayed masses that sum to one realize all exact
minimum/maximum regimes.
Two cases attain the refined gradient bound exactly; their ratio to the older reciprocal bound is
$999/1000$. It also enumerates other falsifying constructions, six full two-source pointwise and
averaged local-modulus challenges, including one bounded near-tightness case for the
$\Lambda-\eta$ synergy modulus, six two-cell cases that reject applying that modulus to other
atoms, and one fixed overlapping-window population law. The Rust test uses a scale-aware
$32\,\mathtt{f64::EPSILON}$ tolerance for reconstructed logarithmic constants and bounds. It uses
an absolute $32\,\mathtt{f64::EPSILON}$-nat ceiling for categorical estimator outputs. These
bounded checks are not a global binary64 certificate or external review. A separate bounded
numerical suite checks ten adaptive refined-modulus cases and six endpoint-ceiling cases against
400-digit references for the exact real values represented by the parsed binary64 inputs. Stored
hexadecimal payloads bind each parsed operand and subtraction result. The cases include adjacent
branch-seam inputs, the exact lower endpoint of the upper-branch floor ratio, and strict-support
boundaries with normal or subnormal positive floors. Its upper modulus branch uses the normal ratio
$q_{\mathrm{floor}}/p_{\min}$ and rejects selected unstable inverse-quotient and cancellation
routes.

## Proposed 1.0 scientific status (0.9 review surface)

A future 1.0 version would promise API and software compatibility for the approved default stable
surface. The 0.9 review release makes no such 1.x promise, and no version number turns an estimator
into a theorem or makes it valid outside its declared assumptions. Default builds exclude the
research families; opt-in features do not change their scientific status.

| Family | 1.0 status | Meaning |
|---|---|---|
| Empirical categorical SxPID (2–4 sources) | Stable | Direct binary64 evaluation on the empirical categorical PMF. |
| Fitted quantized categorical PID | Stable quantized estimands | SxPID or $I_{\min}$ of variables transformed by declared, reusable bin edges; neither path is continuous PID. |
| Williams–Beer $I_{\min}$ | Stable legacy comparator | A different redundancy definition; never pool these atoms with SxPID atoms. |
| Euclidean/Chebyshev KSG MI report | Conditional stable estimator | Software-stable under the explicit regular continuous-law and support contract. |
| Continuous two-source shared exclusions and PID2 | Experimental | Paper-defined Ehrlich-et-al. redundancy and PID2 atom construction; algebraic reconstruction does not remove finite-sample error in separately estimated terms. |
| Partial continuous PID3 | Experimental incomplete diagnostic | Dynamically available coordinates are not a complete PID. |
| Full continuous PID3 | Research-only | Mixed-dimensional branches lack a general consistency result. |
| Hyperbolic pairwise KSG | Research-only | Correct geodesic distance code does not establish estimator consistency. |
| Hyperbolic shared exclusions/PID | Unsupported | No product/disjunction estimator is provided. |
| Generic kNN bootstrap confidence intervals | Unsupported | Subsample percentiles are diagnostics, not calibrated confidence intervals. |
| Train-split supervised PLS→held-out PID | Exploratory | Fit/select on training data and estimate on held-out evaluation data. |
| Added Gaussian-noise provenance | Experimental project-defined software | Local Rust code exists. Python and run-log schema 2 do not expose it. It has no defining method paper. |

See [Known limitations](KNOWN_LIMITATIONS.md) before using a result in publication or a
consequential decision. The feature boundary and 0.4→1.0 source changes are listed in the
[migration guide](MIGRATION.md).

## Capabilities

| Area | Implemented surface |
|---|---|
| Continuous MI | KSG mutual information with exact Chebyshev neighbour queries and strict-radius marginal counts. |
| Continuous shared exclusions | Default-off experimental $I_\cap^{\mathrm{sx}}$ redundancy and PID2; partial/full continuous PID3 are separately labelled research surfaces. |
| Empirical categorical SxPID | `discrete_sxpid2`, `discrete_sxpid3`, and `discrete_sxpid_n` (2–4 sources), with direct empirical-PMF pointwise and averaged signed atoms. |
| Explicit quantization | Reusable fitted equal-width quantization followed by categorical SxPID or $I_{\min}$ for a declared quantized estimand. |
| Alternative discrete PID | Williams–Beer $I_{\min}$ via explicit empirical-PMF APIs. This is a different measure; do not pool its atoms with $I_\cap^{\mathrm{sx}}$. |
| Screening and diagnostics | Shannon invariants with typed defined/undefined normalized-ratio states, intrinsic dimension, distance concentration, sampled four-point delta summaries, and the `exp0` diagnostic program. |
| Preprocessing | Explicit constant-column policies, fitted-state/training hashes, standardization, PCA, CountSketch projection, seeded observation-noise sensitivity, and supervised PLS. |
| Observation-noise provenance | Experimental typed Rust declarations and application reports for added Gaussian noise. No Python or run-log schema 2 exposure exists. |
| Resampling/inference | Declared moving-block resampling distributions, random-origin kNN subsample diagnostics, typed permutation/surrogate nulls, complete failure outcomes, and BH/BY adjustment provenance. |
| Reproducibility | Seeded RNG, serial/parallel identity tests, structured estimator reports, typed package-safe software identity, and bounded `pid-runlog` replay/consistency checks. |
| Python | A maturin/PyO3 module with a stable default namespace and an explicit experimental build feature. |

## Categorical data is not numeric data

The categorical SxPID entry points take `DiscreteMatRef` labels. They evaluate the empirical PMF
directly in binary64; this is not a claim of population-exact atoms. Only equality of complete
rows matters;
`0`, `1`, and `100` are three categories, not points on a number line. Sparse, negative (after
Python-side dense encoding), and non-monotone labels therefore do not change the mathematical
result under a bijective relabeling.

```rust
use pid_core::stable::categorical::discrete_sxpid2;
use pid_core::DiscreteMatRef;

fn main() -> Result<(), pid_core::PidError> {
    let s1_data = [0, 0, 1, 1];
    let s2_data = [0, 1, 0, 1];
    let t_data  = [0, 1, 1, 0]; // XOR
    let s1 = DiscreteMatRef::new(&s1_data, 4, 1)?;
    let s2 = DiscreteMatRef::new(&s2_data, 4, 1)?;
    let t = DiscreteMatRef::new(&t_data, 4, 1)?;
    let pid = discrete_sxpid2(s1, s2, t)?;
    println!("Red={:.4} Syn={:.4}", pid.red.net_nats(), pid.syn.net_nats());
    Ok(())
}
```

The distinction from $I_{\min}$ is concrete on the two-bit COPY of independent fair sources,
$T=(S_1,S_2)$: categorical SxPID assigns redundancy $\ln(4/3)$ nats, while $I_{\min}$ assigns
$\ln 2$
nats. The identity axiom of
[Harder, Salge & Polani (2013)](https://doi.org/10.1103/PhysRevE.87.012130) instead requires
redundancy equal to $I(S_1;S_2)$, which is zero for these independent sources. This tests that named
axiom, not every PID axiom; properties established for a functional in its defining paper and
broader PID desiderata should be stated separately.

When starting from continuous measurements, opt into equal-width binning explicitly:

```rust,ignore
use pid_core::stable::quantized::{
    fitted_quantized_sxpid2, EqualWidthQuantizer, QuantizerConfig,
};

// Fit on training rows, then reuse exactly those edges on evaluation rows.
let s1_quantizer = EqualWidthQuantizer::fit(s1_train, 8, QuantizerConfig::default())?;
let s2_quantizer = EqualWidthQuantizer::fit(s2_train, 8, QuantizerConfig::default())?;
let target_quantizer = EqualWidthQuantizer::fit(target_train, 8, QuantizerConfig::default())?;
let s1 = s1_quantizer.transform_with_report(s1_eval)?;
let s2 = s2_quantizer.transform_with_report(s2_eval)?;
let target = target_quantizer.transform_with_report(target_eval)?;
let result = fitted_quantized_sxpid2(&s1, &s2, &target)?;
let pid = result.pid;
```

Quantized results depend on the bin count and numeric scaling. The composed result embeds all three
quantization reports—including exact edges, separate domain-tagged training-input,
transform-input, and categorical-output hashes, out-of-range policy, and occupancy—alongside the
PID and observed cardinalities.

Each report separates requested nominal labels, labels with at least one finite-binary64 preimage
under the fitted map, and labels actually observed in this transform call. Structural collapse and
reachable-but-unobserved cells are reported separately; map reachability is not population support,
positive probability, or evidence that the bin count is scientifically adequate. Interior edges
are overflow-safe, finite, in range, and nondecreasing, but adjacent representable endpoints can
still collapse nominal bins.

Categorical SxPID final empirical-PMF component averaging and selected two-source PID synergy
formulas now sum their already represented binary64 operands exactly and round once, ties-to-even;
pointwise SxPID Möbius inversion remains compensated. This removes incidental operand-order
effects only for those named final multisets, not estimator, logarithm, probability, or sampling
error. The scoped counterexamples, rejected pointwise/$I_{\min}$ PID3 transfers, cost model,
oracle boundary, and migration guidance are documented in
[the numerical-assurance note](NUMERICAL_ASSURANCE.md).

Those SHA-256 preimages are reproducible outside Rust. Their NUL-terminated domains are
`pid-rs/quantizer/training-input/f64-bits-le/v1\0`,
`pid-rs/quantizer/transform-input/f64-bits-le/v1\0`, and
`pid-rs/quantizer/categorical-output/u128-le/v1\0`. Append `nrows` then `ncols` as little-endian
`u128`; append input matrices as row-major `f64` bit patterns in little-endian `u64`, or categorical
labels as row-major little-endian `u128`. The final `\0` denotes one zero byte, and no other
separator or text encoding is present. The canonical contract and fixed vectors are in the
[`pid-core` README](crates/pid-core/README.md).

## Continuous quickstart

```rust
use pid_core::stable::continuous::{ksg_mi_report, KsgConfig, KsgProvenance};
use pid_core::MatRef;

fn main() -> Result<(), pid_core::PidError> {
    // This is a tiny API example, not enough data for a scientific estimate.
    let s1_data = [0.03, 0.97, 0.14, 0.86, 0.22, 0.78, 0.35, 0.65];
    // This example adds fixed values and records a caller-declared observation model.
    // It does not prove finite mutual information.
    let noise = [0.03, -0.02, 0.01, -0.04, 0.02, -0.01, 0.04, -0.03];
    let t_data: Vec<f64> = (0..8).map(|i| s1_data[i] + noise[i]).collect();
    let s1 = MatRef::new(&s1_data, 8, 1)?;
    let t = MatRef::new(&t_data, 8, 1)?;

    // This is a population-law assertion, not something a finite sample can prove.
    let config = KsgConfig::assume_regular_full_dimensional();
    let provenance = KsgProvenance::new(
        "raw scalar measurements; no fitted preprocessing",
        "additive continuous observation noise",
        None,
    )?;
    let report = ksg_mi_report(s1, t, &config, &provenance)?;
    println!("MI={:.3} nats", report.estimate_nats);
    Ok(())
}
```

Runnable examples provide better-sized synthetic systems:

```bash
cargo run --release -p pid-core --features experimental-continuous --example ksg_and_pid
cargo run --release --example discrete_sxpid
```

## Scientific cautions

These estimators are not interchangeable with ground truth.

- Continuous estimators fail closed when their support contract is `Unspecified`. The ordinary
  ambient-coordinate Chebyshev/L∞ path requires an explicit
  `AssumeRegularFullDimensional` assertion covering every
  marginal and joint law used by the call—not merely numeric input types. Exact per-coordinate
  ties are incompatible with ideal i.i.d., unrounded continuous-sample conditions and are rejected,
  but they do not identify their cause or population support. Their absence does not prove
  continuity, full-dimensional support, finite MI, or compatible reference measures. Use
  `continuous_input_diagnostics` to inspect exact multiplicities and marginal k-th-shell/radius
  summaries before choosing an estimator. Prefer `ksg_mi_report` (Python: `compute_mi_report`) when
  a result leaves local scope: it carries these diagnostics together with support, preprocessing,
  observation-model, and geometry provenance.
- Two-source shared-exclusions and the PID2 atom reconstruction implement the cited Ehrlich-et-al.
  construction in its restricted domain. pid-rs adds report, split-sample, and cross-fit wrappers;
  neither paper provenance nor those wrappers supply a crate-level general consistency theorem. The
  default-off `pid2_isx_report` (Python
  experimental migration namespace: `compute_pid2_report`) retains all three signed KSG reports,
  the complete ISX source-union/radius/count/scaling/overlap report, atom/term values, provenance,
  warnings, and aligned local-contribution covariance/conditioning diagnostics. The covariance is
  descriptive local-contribution covariance—not calibrated sampling covariance. Split-sample and
  cross-fit helpers require explicit split identities and never pool independently fitted fold
  coordinates.
- The supported population-estimation interpretation of standard KSG and the Ehrlich continuous
  estimator requires i.i.d. rows from one fixed joint law under the declared density and geometry
  premises. Subsampling and dependence-aware uncertainty methods may be reported as diagnostics or
  inference procedures; neither proves estimator consistency for dependent rows without a separate
  theorem naming the dependence conditions and rates.
- Continuous kNN formulas require an unambiguous k-th-neighbor shell. Zero radii and positive
  boundary ties are rejected with structured errors; quantized data needs a scientifically
  justified discrete model, not a silent tie convention. Jitter changes the estimated distribution:
  use it only under an explicit observation-noise model or in a seeded, reported noise-scale
  sensitivity analysis; otherwise select a scientifically suitable support-matched method outside
  pid-rs or a declared discrete/quantized estimand. pid-rs provides no general arbitrary
  mixed-support estimator.
- `GaussianNoiseTransform` is experimental project-defined software that is new in pid-rs. It is
  not a new estimator or a claim of scientific novelty. It has no defining method paper.
- The typed contract separates the ideal kernel, scientific declaration, stream, input binding,
  and generated report. It requires $\sigma>0$. A declared resampling context does not prove that
  the declared indices produced the input matrix.
- Under the ideal model, Gaussian convolution gives a smooth positive density with full support in
  the ambient Euclidean space. For a fixed seed, the generated binary64 matrix is deterministic.
  It is not a population law. The contract does not establish finite MI, i.i.d. rows, KSG
  validity, calibrated uncertainty, or PID-atom monotonicity. Separate matrix reports do not
  establish one joint noise model for all sources and the target. `Jitter` remains an unreported
  migration primitive.
- KSG returns signed finite-sample estimates by default. `NegativeHandling::ClampToZero` is an
  opt-in presentation transform; do not apply it to terms entering PID/Shannon identities or
  inferential procedures.
- High intrinsic dimension and distance concentration can invalidate nearest-neighbour geometry.
- Exact deterministic maps between continuous variables have singular joint laws and infinite
  mutual information, outside this finite-MI estimator's domain. An explicit observation-noise
  model defines a different noisy population law. Finite mutual information remains a separate
  population assumption. Otherwise, use a suitable discrete or mixed estimator. Near-deterministic
  dependence can still require prohibitive sample sizes even in low dimension.
- A practical general estimator for arbitrary combinations of discrete, continuous, singular, and
  mixed support remains absent. [Barà et al. (2025)](https://doi.org/10.1103/58bg-5n9s) provide a
  narrower nearest-neighbour PID method for a discrete target with continuous sources; pid-rs does
  not implement that method, and its restricted orientation does not close the general gap.
- For continuous $I_\cap^{\mathrm{sx}}$, the relative units and preprocessing of the separate source
  variables
  determine how source neighborhoods are compared and are therefore part of the estimand, not an
  innocuous implementation detail. Record the full scaling/projection scheme and do not compare or
  pool atoms obtained under different schemes.
- Two-source continuous $I_\cap^{\mathrm{sx}}$ requires equal ambient source column counts because
  its
  small-ball disjunction compares raw source-neighborhood radii. Equality is necessary but does not
  prove equal intrinsic dimensions, compatible reference measures, or comparable neighborhood
  geometry.
- The full continuous PID3 lattice necessarily contains singleton-vs-pair branches, so it compares
  source neighborhoods with different ambient dimensions. It is absent from default builds and
  requires the `research-mixed-dimension-pid3` Cargo feature (or an explicitly experimental Python
  build). That compile-time opt-in is for reference reproduction and labelled diagnostics; it does
  not validate the atoms as mixed-dimensional scientific estimates. Full results carry
  support/dimension/experimental status and deterministic warnings alongside the values.
  `pid3_isx_report` and the experimental Python migration surface
  additionally require and return caller-declared per-variable preprocessing and observation-model
  provenance, structurally checked only for nonemptiness.
  Prefer `incomplete_pid3_report` (experimental Python migration namespace:
  `compute_pid3_partial`), which requires the same provenance and reports every node/atom's
  dynamic availability instead of returning suspect numbers. For equal-dimensional sources
  specifically, 15 redundancy nodes and 8 atoms are available.
  A finite-union small-ball bound now makes the obstruction precise. If branch masses scale as
  $c_jr^{d_j}+o(r^{d_j})$ in one raw radius, the union has the smallest exponent. Branches with
  larger exponents have vanishing relative mass. This is a standard mathematical consequence and
  a new pid-rs limitation analysis, not a new estimator or scientific-novelty claim. It establishes
  branch-weight collapse, not estimator inconsistency. See [Known
  limitations](KNOWN_LIMITATIONS.md#finite-union-small-ball-bound) for the proof, counterexample,
  and missing estimator-specific obligations.
- Hyperbolic/Lorentz KSG remains standalone pairwise-MI-only and experimental, and is available
  only through the structured report that requires embedding-training provenance. Its
  smooth-manifold support assertion, fixed curvature `-1`, and use of Lorentz geodesic distance do
  not constitute a manifold-KSG consistency theorem; scalar/local APIs, concatenated invariants, and
  shared exclusions reject it. Lorentz KSG and geometry diagnostics use typed entry points under
  `experimental::hyperbolic`; enabling that feature does not add variants or fields to stable
  types.
- `sampled_four_point_delta_summary` reports a distribution over sampled quadruples. Its mean and
  quantiles are descriptive, and even its sampled maximum is only a lower bound on the
  sup-over-all-quadruples Gromov constant.
- `pid2_isx` combines KSG MI terms with an independently estimated $I_\cap^{\mathrm{sx}}$
  redundancy term. Their
  finite-sample biases differ, so a small near-zero atom may be estimator error.
- The default-off `pls_project_then_*` research wrappers fit supervised PLS and evaluate PID on the
  same rows, so they are exploratory and require an explicit acknowledgement. For inference, fit the
  variable-specific projectors and select every hyperparameter on training data, then keep each
  fitted transform fixed while evaluating held-out rows; do not mix independently rotated foldwise
  coordinates in one kNN sample. Fitted standardizers, PCA, and PLS projectors expose deterministic
  training/parameter hashes; choose an explicit constant-column policy when fitting a standardizer.
- For finite-PMF MGW categorical SxPID, the exact-real informative and misinformative Möbius-
  component atoms are separately non-negative, while their signed-net atoms may be negative and are
  never clamped (Makkeh et al. 2021, Theorem IV.3). Binary64 output needs its own error bound or
  tolerance; the exact-real theorem does not make represented values exact. The same semantic
  statement applies to fitted-quantized MGW output only conditional on its realized frozen finite
  transform. The theorem is not evidence about Ehrlich continuous estimates, KSG mutual
  information, Williams--Beer $I_{\min}$, heuristics, or PID2 wrappers. A negative MGW net atom
  states only that its misinformative component exceeds its informative component at that lattice
  coordinate; it is not an intent, causal, fault, or responsibility finding.
- `FullShuffle` permutation nulls require exchangeable rows. `BlockShuffle { block_size }` preserves
  order inside equal, non-overlapping blocks and yields a permutation p-value only when whole blocks
  are exchangeable; it requires `n % block_size == 0`. For a stationary autocorrelated series,
  `CircularShift { min_shift }` preserves serial structure better, but its restricted offsets yield
  an approximate stationary-surrogate score rather than an exact randomization-test p-value. Choose
  the block or shift scale from the dependence length. Any failed or non-finite transformation
  invalidates the complete result rather than merely reducing its reported count.
- Permutation alternatives are explicitly signed `Upper` or `Lower` tails and should be chosen
  before inspecting results. Shuffling one source defines an alignment/exchangeability null; it
  does not generally test “this signed PID atom equals zero,” and no implicit absolute-value
  two-sided test is applied.
- Generic resampling calls require a typed dependence and block-length-selection declaration,
  preserve every requested replicate/fold failure, and return raw empirical spread/percentiles only
  when the complete predeclared set succeeds. With-replacement block bootstrap can duplicate rows
  and collapse kNN radii. Adding jitter changes
  the resampled distribution and still distorts local-density statistics; use it only under the
  explicit noise-model/sensitivity-analysis contract above. Prefer `RowResampleScheme::Subsample`
  for KSG-based diagnostics and report the smaller subsample size; its raw m-sample quantiles are
  not calibrated confidence intervals for the full n-row estimate.
- Atom × source × window searches are multiple-testing problems. Use Benjamini–Hochberg only under
  its independence/positive-dependence assumptions; `benjamini_yekutieli` is the more conservative
  option when dependence within the predeclared family is unknown.

The exact Chebyshev kd-tree is an acceleration, not a complexity guarantee. Queries are typically
sublinear in low dimension but can degrade to a scan; the full estimator is worst-case quadratic.
Other metrics, small samples, and high-dimensional joints use the brute-force path directly.

## Validation

The suite triangulates analytic, external, and standalone reference paths with internal identities:

- KSG MI against the closed-form Gaussian-channel value
  $-\tfrac12\ln(1-\rho^2)$.
- The integer KSG local-count arithmetic against a standard-library-only 80-digit Decimal
  harmonic-number oracle: 6,920 exhaustive rectangular-arithmetic outer-box tuples through 16
  samples plus 1,278 fixed stress tuples through one million samples. The outer box is not
  asserted to equal the runtime unique-shell image. Two reference metrics are kept separate on this
  selected finite corpus: the maximum difference from `binary64(stored Decimal prefix text)` is
  `8 * f64::EPSILON` nats with 40 ties. Under the checker's stated 160-digit Python `Decimal`
  directed-rounding semantics, a separate enclosure of the exact harmonic rational certifies a
  unique maximum below `9.761311 * f64::EPSILON` nats, including the fixed stress rows. Both remain
  below the reviewed `32 * f64::EPSILON`-nat ceiling. Exact-rounded 80-digit references differ
  textually on 6,509 rows and numerically on 5,934 rows, but all 8,198 pairs convert to the same
  binary64 value. After canonical finite-Decimal validation, an exact `Fraction(Decimal)`
  comparator subtracts and orders all 8,198 stored/exact-rounded pairs without ambient Decimal
  precision. The selected association's compiled Rust test directly classifies the complete
  corpus as 354 positive zeros, no negative zeros, and 7,844 nonzeros, with finiteness and
  source-swap checks before classification.
  These are not ULP, universal, or portable results and do not validate neighbor search or counts,
  an estimator, population support, or PID. The active
  [revision-4 claim](claims/KSG-INTEGER-HARMONIC-001/claim-v4.md) and retained
  [Decimal](claims/KSG-INTEGER-HARMONIC-001/failures/decimal-reference-metric-conflation-v4.md),
  [modular](claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md), and
  [SMT-LIB](claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.md) failures
  separate scientific mutations from representation/checker controls and record the remaining
  human and implementation cuts. The bounded arithmetic core is scoped green; repository and
  publication integration remain a 13-gate **NO-GO**.
- Two-source continuous $I_\cap^{\mathrm{sx}}$, plus the explicitly research-gated three-source
  reproduction, against the authors' public
  [`csxpid`](https://gitlab.gwdg.de/wibral/continuouspidestimator) implementation at pinned commit
  `7bb984611a422cf7944ece68993fe3a27e2eadec`; all redundancy/atom values on the committed fixture
  agree within `1e-12` nats after the recorded bit-to-nat conversion. The
  [generator](scripts/generate-csxpid-reference.py) records the backend and environment, and the
  [SHA-256 sidecar](crates/pid-core/tests/fixtures/csxpid_reference.json.sha256) covers its output.
- Continuous $I_\cap^{\mathrm{sx}}$ against a fixed-sample semi-analytic comparison: pointwise
  Gaussian terms
  are closed form, while the expectation and its ordinary Monte Carlo standard error are evaluated
  on the same seeded finite sample. This is a bounded estimator check, not population ground truth.
- Discrete SxPID against separate hard-coded fixtures from pinned Abzinger/SxPID and IDTxl
  `pid_goettingen` paths, after converting bits to nats; all compared values agree within `1e-12`.
  Those fixtures have no checked-in generator or environment lock and are not complete external
  reproduction bundles.
- Two-source categorical SxPID against a standard-library-only, 80-digit Decimal oracle that
  directly evaluates the published event-probability definition. The committed corpus exhausts
  all 494 nonempty binary count tables with at most four samples; every Rust atom component and MI
  term agrees within four binary64 epsilons. This finite implementation-path cross-check is not an
  external review, a proof for larger alphabets/lattices, or a population-validity claim.
- The fixed finite-alphabet plug-in path against an implementation-separated,
  standard-library-only, 100-digit
  Decimal oracle. Its digest-bound corpus covers all coordinates in listed 2-, 3-, and 4-source
  SxPID tables, 2- and 3-source $I_{\min}$ tables, minimizer-tie crossings, realization-key changes,
  and pointwise omission of an absent realization on the listed support face. The Rust test
  separately checks fitted-quantizer wrappers against direct categorical calls. This is bounded
  implementation evidence, not the convergence proof,
  external review, population validation, or a global binary64 bound.
- The support-change-tolerant averaged categorical theorem against an implementation-separated
  standard-library generator using exact rational structure and high-precision Decimal logarithms.
  Its digest-bound corpus contains 18 law pairs and replays 36 count tables through the stable
  two- through four-source categorical route, including equality witnesses, support creation and
  deletion, endpoint records, retained falsifiers, and every returned coordinate. This is bounded
  conformance evidence, not the analytic proof, a refinement theorem, an interval-certified
  binary64 result, or independent review.
- The SxPID result under a dependency coloring against a fraction-exact and 400-digit Decimal
  standard-library challenge generator. The
  corpus enumerates pairwise-only, copied-color, singleton-color, adaptive-color,
  unspecified-mixing, net-weight half-factor, support-boundary, marginal-only, and new-support
  failures. It also checks the class-size proxy that is optimal within the declared
  Hölder–Hoeffding proof scheme,
  telescoping allocation, all displayed bounds on six committed two-source law pairs, and one
  fixed-width overlapping-window population law. The Rust test compares the fixed-window law and
  all six local perturbation pairs with the categorical implementation under an absolute
  $32\,\mathtt{f64::EPSILON}$-nat ceiling. It uses a scale-aware tolerance with the same multiplier
  when it reconstructs stored logarithmic constants and bounds. Ten adaptive-modulus cases and
  six endpoint-ceiling cases separately challenge branch seams, cancellation, ratio rounding,
  exact payload identity, and overflow with normal and subnormal positive floors. This is bounded internal evidence, not
  a proof of the stochastic theorem or a general binary64 certificate.
- MGW Theorems IV.2 and IV.3, categorical relabeling invariance, all source-subset
  self-redundancy identities, and reconstruction on the 4-, 18-, and 166-node lattices.
- Williams–Beer $I_{\min}$, co-information, O-information, bootstrap/permutation semantics, and
  serial/parallel equality against hand-derived or deterministic fixtures.

`exp0` is a diagnostic, not a conventional pass/fail benchmark. Its default sweep deliberately
enters high-dimensional regimes where kNN estimates fail and may report a `NO-GO` MI/coherence
verdict or a separate non-gating `PIVOT` geometry disposition while exiting successfully.
Atom-measure validation remains `not_adjudicated`, and atom-estimator validation remains `blocked`.
Unavailable optional estimates and diagnostics carry machine-readable produced/abstained/
not-requested states and reason codes without numeric placeholders. `--strict-gate` enforces `GO`
only on a separately scoped curated one-dimensional Gaussian band with analytic MI values.

```bash
cargo run -p pid-core --all-features --bin exp0 -- --seeds 4 --summary-json summary.json --runlog run.jsonl
cargo run -p pid-runlog --bin pid-runlog-replay -- --validate run.jsonl
```

## Software identity

`pid_core::software_identity()` and Python `pid_core_rs.software_identity()` expose the same typed,
format-1 envelope. This is **new project-defined software infrastructure**, implemented locally in
Rust and bound directly into Python; it is not an estimator, has no defining paper, and claims no
new mathematics or statistical result. Python also exposes the identical function under
`pid_core_rs.stable.software_identity`.

The envelope deliberately separates five interpretation domains:

| Domain | What it identifies | What it does not establish |
|---|---|---|
| Public Rust declaration signature | Epoch/revision/status for the exact proposed release-scope feature profiles, backed by pinned-tool declaration snapshots. | A cryptographic signature, Python API/ABI, numerical behavior, estimand definitions, package-version compatibility, authenticity, or a 1.x promise. |
| Source | A layout-matched workspace Git commit, Cargo package metadata, or a typed unavailable reason, with route-scoped clean/dirty/unknown state. | Authorship, authenticity, archive equality, or whole-repository cleanliness. |
| Build context | Compiler version when available, target, Cargo profile, optimization level, debug-information flag (not debug assertions), and exact enabled `pid-core` features. | Dependencies, linker inputs, arbitrary compiler flags, environment, or executable identity. |
| Reference artifacts | Manifest-declared SHA-256 of the exact raw canonical repository-file bytes; layout-matched workspace builds verify the current files. | A guarantee that packaged builds contain or re-verify those files, API compatibility, estimator validity, application suitability, data quality, or cross-platform numerical identity. |
| Attestation | Explicitly `none` in format 1. | Any executable, dependency-graph, source, or supply-chain attestation. |

The workspace observation is a build-time snapshot, not a live repository monitor. Its Git probes
discard ambient repository, worktree, object-overlay, replacement, graft, configuration,
pathspec, and global/system-attribute overrides. Cargo invalidation covers the package tree,
workspace markers and attribute locations, linked-worktree routing, index/shared-index files,
effective repository config, bounded `objects/info` metadata, and the active files/reftable
reference state without recursively watching the complete `.git` or object database. Unsupported
ref-storage payloads, config includes, incomplete probes, and recovery states retain a deliberately
absent watch path so the next Cargo invocation rechecks them. The final typed source result also
controls that recovery watch, so a transient failure cannot be cached behind a separately healthy
route probe. Git older than 2.45 cannot establish workspace cleanliness and therefore reports
`unknown` with the recovery watch retained. Re-running the build script does not rewrite unchanged
generated identity bytes. The clean/dirty observation assumes repository metadata and package
files are not concurrently mutated during the bounded probe; repeated status/input checks and a
final HEAD check catch ordinary mid-probe changes but do not make the observation atomic. Under
that assumption, any effective `filter` attribute on a tracked package path (including unset or
unconfigured values), `attr.tree`, a tracked symbolic link, or a tracked gitlink makes the package
working-tree state `unknown`, and no external clean-filter command is executed. These broader
invalidation watches do not broaden the serialized clean/dirty scope beyond `crates/pid-core`. The
build aborts if an end-of-run recheck finds that the typed source, layout route, or exact bound
reference bytes changed after their initial observation.

Declaration snapshots live at immutable revision-scoped paths and retain their generation tool,
toolchain, original host, explicit rustdoc target, and format. The evidence update is intentionally two-phase: a source commit first
contains the code whose declarations are captured, and the following evidence commit adds the
snapshots and registry entry. The source commit therefore need not contain those snapshot bytes at
their recorded paths. Append preservation is checked against every HEAD-reachable commit that
touched the registry, the direct tip parents, and monotone source ancestry. After a committed
binding, each snapshot path's exact bytes are also checked throughout its reachable full history.
Git evidence queries discard ambient routing/configuration, disable replacement/graft overlays,
and require the canonical worktree root to match the files being checked. This still cannot cover
an unreachable never-merged branch or history absent from the presented repository and is not a
cryptographic signature, transparency log, or timestamp.

`exp0` now places this same envelope under its existing `build_provenance` configuration key rather
than maintaining a second ad hoc representation. Digest equality is useful for exact forensic
comparison only; interpret the referenced catalog and scope instead of treating a hash match as a
validity certificate.

## Run-log guarantees

`pid-runlog` schema 2 records versioned JSONL events, typed scientific PID provenance, explicit
hash-algorithm/revision identities, order-sensitive trace hashes, and optional manifests/anchors.
Readers stream under `RunLogLimits` rather than loading unbounded files, and schema-2 canonical JSON
hashes preserve integer identity instead of silently converting arbitrary integers through
binary64. Schema 1 remains deliberately readable and has a golden migration into schema 2.
Validation checks schema, ordering, lifecycle, causality, finite/lossless values, paths, and internal
hash consistency. Replay makes recorded state inspectable and comparable; it does not recompute an
estimator without the original inputs and build.

The experimental `pid_runlog::experimental::schema3` module contains project-defined Rust types
for a possible future scientific-outcome contract. The types record analysis plans, request
ledgers, data lineage, split declarations, separate gates, named values, and content identities.
An experimental typed validator checks exact terminal-outcome coverage for request ledgers with at
most 1,024 entries. It keeps support, preflight, and computation counts separate. This coverage is
not statistical interval coverage. Public encoders implement the supported matrix and split hash
contracts. This module adds no PID measure or estimator. The active event and sidecar schema
remains version 2. No schema 3 event, reader, replay path, sidecar, CLI path, or migration exists.

These hashes are not authentication on their own. A log and colocated sidecar can be replaced
together. Tamper evidence requires storing the digest in a trusted external or signed anchor.

## Source use and registry status

The 0.9 review prerelease is distributed only through GitHub as source, scope records, provenance,
and checksum manifests. Version 0.9.0 is not published to crates.io or PyPI, and docs.rs does not
host 0.9.0 documentation. Do not treat registry installation commands for 0.9.0 as
available.

Use its checksum-verified source archive or pin the exact peeled commit corresponding to the source
offered for review. A Git dependency can be recorded as follows:

```toml
[dependencies]
pid-core = { git = "https://github.com/sepahead/pid-rs", rev = "<40-character commit SHA>" }
```

The `v0.9.0` review tag is annotated but deliberately unsigned under repository policy.
The attached source, scope, and provenance files are covered by SHA-256 and SHA-512 manifests; see
[release reproduction](RELEASE_REPRODUCTION.md). Checksums establish byte integrity, not signer
identity, and neither a tag nor a checksum substitutes for reviewing the estimator's scientific
assumptions. GitHub release immutability locks this prerelease's tag and six attached files and
automatically generates a cryptographically verifiable GitHub release attestation for the
tag, commit, and assets. The prerelease is not marked as the latest production release. Separate
build-provenance attestations, signed human review, SBOMs, and registry publication are reserved for
a later qualified release.

## Python

The Python extension supports CPython 3.11 or newer. Its distribution name is `pid-core-rs`; the
import name is `pid_core_rs`. No 0.9.0 wheel or source distribution is
published to PyPI. Build and test the exact tagged source tree locally instead:

```bash
python -m pip install maturin numpy pytest
maturin develop --release --locked -m crates/pid-python/Cargo.toml
pytest crates/pid-python/tests -q
```

`compute_mi_report` and continuous diagnostics accept finite two-dimensional `float64` arrays.
`compute_categorical_sxpid2/3` and `compute_categorical_sxpid` accept two-dimensional `int64`
arrays and dense-encode complete signed-label rows without treating their magnitude as meaningful.
`EqualWidthQuantizer.fit(...)` and `compute_fitted_quantized_sxpid2(...)` preserve fitted edges and
occupancy in typed result objects. Inputs are copied/validated before long-running work releases the
GIL. A default wheel built locally from this source contains no continuous-PID, hyperbolic,
heuristic, hierarchy, or same-sample PLS entry points; pre-1.0 compatibility functions exist only
in an explicitly experimental source build under `pid_core_rs.experimental.migration`.

That migration namespace also contains same-sample quantization adapters with a deliberately weaker
contract. `compute_discrete_pid2/3` apply Williams–Beer `I_min`, whereas
`compute_quantized_sxpid2/3/n` apply categorical Makkeh–Gutknecht–Wibral shared exclusions; these
are different functionals with no mapping theorem here. Both families compute per-column ranges on
the rows they evaluate and select bins with an exact binary64-significand rule, thereby changing the
variables and estimand. They materialize no fitted edge vector and are not binary64-equivalent to
the stable fitted-edge `EqualWidthQuantizer` at every rounded boundary. Their flat dictionaries
discard the Rust same-sample wrapper's bin-count provenance and, for SxPID, typed atom
interpretation. Three-source `I_min` and MGW dictionaries even share the same antichain-key shape;
output shape cannot identify the functional, so callers must retain the function/method identity.
Both Rust routes enforce the same aggregate estimator resource preflight as their categorical
counterparts before quantization. Deprecated Python additionally retains a conservative legacy
preflight proportional to `columns * (num_bins + 1)` before it enters Rust, so it can reject very
large bin counts accepted by the Rust transform; admitted calls share the Rust bin semantics, but
the accepted input domains are not identical. They are exploratory migration aids, not automatic
fallbacks when a continuous estimator fails.

## Ecosystem use

The published `v0.9.0` GitHub-only source-review prerelease and the proposed core `pid-rs` 1.0
boundary are standalone. pid-rs is a protocol-neutral library and tooling project, not an NCP
peer, provider, or consumer. It receives no NCP role receipt. Any NCP-facing integration belongs
to a downstream, consumer-owned optional adapter; no downstream service is a build or runtime
dependency of pid-rs, and no PID result or run log grants identity, capability, permission, or
authority.

Compatibility with Prisoma, Galadriel, Crebain, Haldir, external-authority adapters, and full-stack
deployment profiles is **not claimed** by this published `v0.9.0` review prerelease. An NCP
candidate or release has its own authorization and qualification boundary: it neither changes
pid-rs release status nor turns pid-rs into an NCP role subject.

## Workspace

| Crate | Purpose |
|---|---|
| [`pid-core`](crates/pid-core) | Estimators, PID lattices, invariants, diagnostics, preprocessing, and `exp0`. |
| [`pid-runlog`](crates/pid-runlog) | Versioned run-log schema plus replay/validate/compare CLI. |
| [`pid-python`](crates/pid-python) | PyO3/maturin bindings exposed as `pid_core_rs`. |

The workspace MSRV is Rust 1.89 and is checked in CI. The optional `parallel` feature must remain
bit-identical to the serial estimator path.

## References

This short list covers the principal PID/MI lineage. The exhaustive method-by-method bibliography,
including diagnostics, preprocessing, geometry, resampling, multiple testing, external code, and
entries with no dedicated paper, is in [`METHODS.md`](METHODS.md).

| Component | Reference |
|---|---|
| KSG mutual information | Kraskov, Stögbauer & Grassberger (2004), *Physical Review E* 69, 066138 |
| Discrete shared exclusions | Makkeh, Gutknecht & Wibral (2021), *Physical Review E* 103, 032149; [Abzinger/SxPID](https://github.com/Abzinger/SxPID) |
| PID parthood foundation | Gutknecht, Wibral & Makkeh (2021), [arXiv:2008.09535](https://arxiv.org/abs/2008.09535) |
| Continuous shared exclusions | Ehrlich et al. (2024), [Physical Review E 110, 014115](https://doi.org/10.1103/PhysRevE.110.014115); [external validation code](https://gitlab.gwdg.de/wibral/continuouspidestimator) |
| $I_{\min}$ PID | Williams & Beer (2010), [arXiv:1004.2515](https://arxiv.org/abs/1004.2515) |
| $\bar r$ and $\bar v$ | Gutknecht et al. (2025), [arXiv:2504.15779](https://arxiv.org/abs/2504.15779) |
| O-information | Rosas et al. (2019), [Physical Review E 100, 032305](https://doi.org/10.1103/PhysRevE.100.032305) |
| kNN sample complexity | Gao, Ver Steeg & Galstyan (2015), [arXiv:1411.2003](https://arxiv.org/abs/1411.2003) |

If you use this software in academic work, cite the specific method papers identified in
[`METHODS.md`](METHODS.md) and the software metadata in [`CITATION.cff`](CITATION.cff).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md), the new project-defined
[mathematical claim and blind-benchmark workflow](MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md), and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). The workflow is process guidance, not scientific
evidence. Report security issues through the process in [SECURITY.md](SECURITY.md), not a public
issue.

## License

Licensed under either [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE), at your option.
