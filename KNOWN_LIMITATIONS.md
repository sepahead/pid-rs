# Proposed pid-rs 1.0 known limitations (0.9 review surface)

The published 0.9 GitHub-only source-review prerelease presents these proposed 1.0 limitations for reviewer feedback.
They are not an assertion that 1.0 has shipped or that 1.x compatibility has begun. A green test
suite establishes implemented software behavior on its covered cases; it does not prove that a
statistical estimator is valid for an arbitrary dataset. All information quantities are in nats
and signed estimates/atoms are preserved.

**“New in pid-rs” means implementation, API, composition, diagnostic, or engineering work new to
this repository; it is not a claim of scientific novelty.** [`METHODS.md`](METHODS.md), generated
from [`method-catalog.json`](method-catalog.json), is the authoritative map of paper-defined,
paper-derived, project-defined, externally compared, and unsupported surfaces. A feature gate,
test fixture, Python binding, or stable API label does not change that origin or prove a population
theorem.

The published 0.9 prerelease is a GitHub-only source prerelease containing source, scope records,
review provenance, and checksums. It does not publish crates, wheels, binaries, docs.rs
documentation, SBOMs, or separate build-provenance attestations, and it has no software DOI or
Zenodo record. GitHub release immutability automatically supplies a signed release attestation;
that integrity record is not independent scientific review. Earlier release commits remain
reachable through immutable changelog links after obsolete tag refs were retired. The later
registry and signed-review qualification process is outside the 0.9 release boundary.

## Stable empirical estimators

Categorical SxPID directly evaluates the empirical PMF in binary64. It is deterministic and
invariant to bijective relabeling of complete categorical states, but it is not exact population
PID and inherits finite-sample plug-in bias. Sparse or unobserved states remain unobserved.

Its pointwise atoms are functions of a distinct observed joint realization **and the complete
empirical PMF**; they are not intrinsic annotations of raw rows. Its averaged atoms are empirical
probability-weighted expectations of those pointwise atoms, not generic population quantities or
mutual informations. Rust uses separate `SxPointwiseAtom` and `SxAveragedAtom` types, and stable
Python exposes `SxAveragedAtom`. Their project-defined interpretation contract makes aggregation
and claim boundaries explicit, names the shared-exclusions measure, and warns that a bare atom
lacks its concrete coordinate/pointwise realization. A caller can still discard the contract by
extracting a scalar. The categorical result itself does not embed source/target names, complete
matrix shapes, or input hashes; caller provenance or a run log must retain them.

The paper-defined term *misinformative* names one component of a signed information decomposition.
It does not establish intentional deception. Likewise, an antichain Möbius atom alone establishes
no causal effect, fault attribution, or per-source responsibility. A negative net value says only
that the misinformative component is larger than the informative component for that coordinate.
Nor is an atom a measure-independent PID coordinate or an unbiased population estimate: averaged
atoms are uncorrected empirical plug-in functionals over observed states. Although the two
components are non-negative in exact arithmetic, a mathematical zero can retain a tiny negative
binary64 residual, and near-cancellation can leave the sign of a much smaller net numerically
unresolved. Use scale-aware tolerances and do not clamp.
The operational prediction interpretation in Makkeh et al. applies to the cumulative local shared
information under its constructed receiver setting; it is not automatically an interpretation of
every isolated Möbius atom.

Williams–Beer $I_{\min}$ is a different redundancy definition. Its atoms cannot be pooled with or
interpreted as shared-exclusions atoms.

On the two-bit COPY of independent fair sources, $T=(S_1,S_2)$, categorical SxPID assigns
$\ln(4/3)$ nats of redundancy and $I_{\min}$ assigns $\ln 2$ nats. The identity axiom of
[Harder, Salge & Polani (2013)](https://doi.org/10.1103/PhysRevE.87.012130) instead requires
redundancy equal to $I(S_1;S_2)$, which is zero for these independent sources. This comparison is
against that named axiom, not every PID axiom: properties proved for a functional in its defining
paper and broader PID desiderata must be reported separately.

Fitted quantized SxPID and fitted quantized $I_{\min}$ estimate their respective PIDs of the declared
quantized variables. Results depend on fitted edges, scaling, bin count, training sample, and
empty/sparse occupancy. Quantization does not solve the curse of dimensionality and cannot silently
turn a mixed or singular law into a continuous estimand.

### Exact-real finite-alphabet convergence boundary

The [finite-alphabet plug-in convergence note](FINITE_ALPHABET_PLUGIN_CONVERGENCE.md) is new
project analysis in pid-rs. It is not a new PID functional, estimator, or scientific-novelty claim.
The existing SxPID, $I_{\min}$, and Shannon quantities keep the origins listed in
[METHODS.md](METHODS.md). The note retains the derivations, counterexamples, and rejected stronger
claims for later audit.

The note proves exact-real plug-in convergence for fixed finite alphabets and fixed lattices. It
covers categorical SxPID for 2–4 sources, Williams--Beer $I_{\min}$ for 2–3 sources, and
finite-alphabet Shannon entropy, mutual information, co-information, and O-information. The result
holds almost surely for cumulative prefixes from an i.i.d. process or a strictly stationary and
ergodic process. Strict stationarity without ergodicity is not sufficient. Normalized ratios need
a strictly positive population denominator; a report threshold can add a stricter status boundary.

For i.i.d. data, a conservative time-uniform envelope from Hoeffding's inequality and union bounds
controls all prefix empirical cell probabilities. A usable support-stabilization time needs a
known positive lower bound on $p_{\min}$, the smallest supported population cell mass. The observed
empirical minimum cannot replace it because an unobserved rare state can have positive population
mass. The envelope does not apply to dependent or sliding windows, drift, feedback that changes
the law, or rejection-selected samples.

A training artifact must be independent of the raw evaluation sequence. The frozen map must be
measurable with respect to the training sigma-field and raw input. It must return a valid finite
output with conditional probability one. Evaluation rows must be conditionally i.i.d. given the
training sigma-field. The limit is the PID or
Shannon quantity of the conditional push-forward law. It is not generally the same as the quantity
of the unconditional mixture. Same-row fitting, changing transforms, arbitrary pooling across
fitted folds, and target-adaptive fitting on evaluation rows are outside the result.

The pinned Lean proof checks only deterministic exact-real continuity lemmas. It does not encode
an empirical PMF, a stochastic limit theorem, the SxPID or $I_{\min}$ definitions, or Rust
refinement.
The independent 100-digit Decimal generator covers only its committed 2-, 3-, and 4-source tables.
The companion Rust test separately covers listed transform cases. They do not supply a general
proof, an external review, population validation, or a global binary64 error bound. In particular,
the theorem does not establish asymptotic convergence for binary64 Rust outputs or statistical
calibration.

### Dependency-colored SxPID boundary

The separate
[dependency-colored SxPID concentration analysis](DEPENDENCY_COLORED_SXPID_CONCENTRATION.md) is
new project-defined validation of the existing paper-defined categorical SxPID functional. It
adds no estimator or public API and makes no scientific-novelty claim.

The common-law concentration result requires a fixed finite alphabet and a deterministic row
coloring. Every row must have the declared common law. The complete source-target rows in each
nonempty color class must be mutually independent. Pairwise independence, zero covariance, and an
unspecified mixing statement do not imply this premise. Dependence across color classes can be
arbitrary. The exact class-size proxy can vary by prefix. A fixed upper bound on the number of
occupied colors is needed only for the coarse rate.
The displayed envelope proves almost-sure exact-real plug-in consistency under the sufficient
condition
$V_n\log(n)/n^2\to0$; a fixed color count is sufficient. The displayed drift envelope proves
convergence to a fixed reference-law SxPID when that sufficient condition holds and its explicit
bias term also tends to zero. These are not necessary conditions under a stronger sampling
theorem.

The drift extension concentrates about the average row law. A reference-law statement also needs
an explicit deterministic drift bound. It does not infer a stationary estimand. The local SxPID
transfer also needs empirical support contained in population support and a positive population
support floor. The observed support and observed minimum frequency do not establish these
population facts. Under that floor and a strict common-support margin, the analysis gives a
one-$\Lambda$ cumulative modulus, exact general-source Möbius-row transfer, and complete
two-source atom-specific bounds. Exact diamond analysis sharpens the synergy pointwise modulus to
$\Lambda-\eta$ only. Redundancy and unique information still need $\Lambda$, and retained
two-cell counterexamples attain it. These are exact-real validation results for the published
functional. They do not define a new estimator or establish binary64 error.

The analysis retains explicit counterexamples for pairwise-only independence, removal of the color
factor, one singleton color per row, data-adaptive coloring, use of an unspecified mixing label,
an invalid net-weight half-factor from range information alone, support deletion at the strict
boundary, a false all-atom $\Lambda-\eta$ refinement, univariate-marginal-only control, and a
new-support linear bound.
The generic net-weight example is superseded for the complete two-source SxPID-specific range
conclusions. It remains evidence that a smaller coefficient does not follow from an abstract range
alone.
Its fixed-width window corollary applies only to a fixed finite-output map of i.i.d. innovations
with disjoint innovation blocks in each residue class. It does not cover circular windows,
selected widths, generic time-series dependence, continuous SxPID, or repeated post-selection
claims.

Lean checks deterministic exact-real lemmas for centered total variation and event-log and
intersection-PMI gradient bounds. It checks the exact ordinary-diamond diameter and its
attainment. It also checks the exact candidate extrema, closed-form diameter, and zero-side-mass
algebraic witness for the five conditioned-nested coordinates. For the eight conditioned-diamond
coordinates, it checks the exact candidate extrema, the sharp union-reciprocal bound, and the
normalized corollaries. It also checks the refined logarithmic linearization chain, diamond range,
positive segment floors, linear-row and finite-average transfer, normalized effective-color
bounds, unit-scale telescoping allocation, and exponent cancellation.

Lean does not formalize the probability space, independence premise, differentiation, or path
integration. It does not formalize the SxPID definition, published pointwise component
nonnegativity, identification of the algebraic lemmas with SxPID atoms, the drift theorem,
deductive Rust refinement, or binary64 arithmetic. The fraction-exact and 400-digit Decimal
generator and the Rust fixture cover seven conditioned-diamond algebra cases, nine exact extremal
regimes, and six committed law pairs. The same rational inputs check the ordinary-diamond and
conditioned-nested exact identities. They reconstruct three counterexamples that show separate
base and full validity does not replace the nonnegative componentwise lift premise. These are
bounded internal evidence, not a proof of the general theorem, external review, or a global
numerical certificate. Ten refined-modulus and six endpoint-ceiling stress cases check only the
documented adaptive binary64 routes on committed branch-seam, endpoint, normal, and subnormal
inputs. Stored hexadecimal payloads bind their parsed operands and subtraction results. These
cases are not a global error bound or interval implementation. The law fixture uses a scale-aware
$32\,\mathtt{f64::EPSILON}$ tolerance for reconstructed logarithmic constants and bounds. It uses
an absolute $32\,\mathtt{f64::EPSILON}$-nat ceiling for categorical estimator outputs. The
separate stability cases use the documented $256\,\mathtt{f64::EPSILON}$ bounded-operation
tolerance, exact positive zero, and naive-route separation rule.

## Conditional KSG MI

The stable Euclidean/Chebyshev KSG reporting API requires an explicit assertion of regular,
full-dimensional, absolutely continuous marginal and joint population laws with finite mutual
information. A finite sample cannot prove that assertion.

- Exact ties, duplicate rows, zero radii, and ambiguous positive k-th shells are incompatible with
  the implemented continuous rank formulas and fail closed.
- All-unique observations do not prove continuity, a common reference measure, or finite MI.
- A deterministic continuous map has singular joint support and can have infinite MI.
- Bias and variance grow in high dimension, under strong dependence, and when neighbourhood radii
  are nonlocal. Passing a one-dimensional Gaussian oracle is not universal validation.
- Finite-sample KSG values can be negative. Clamping changes downstream algebra and is presentation
  only.
- The kd-tree backend has exact output parity with brute force but retains worst-case quadratic
  query behavior.

Use k/sample-size trajectories, shell/radius/count reports, geometry diagnostics, representation
sensitivity, and a matched synthetic oracle. These diagnostics can falsify some assumptions but do
not certify them.

Normalized average redundancy/vulnerability quantities are unitless screening ratios, not PID
atoms or universal validation scores. Their denominator is an estimated joint MI: a non-positive
or policy-small denominator makes the ratio explicitly undefined. `NormalizedInvariantReport`
records that status and the caller-selectable threshold in nats; choosing a smaller threshold does
not make a noise-dominated ratio scientifically stable.

The target-conditioned `average_degree_of_redundancy` ($\bar r$) and
`average_degree_of_vulnerability` ($\bar v$) follow the cited Shannon-invariants formulation.
`red_degree_discrete` ($\mathrm{Red}^{\circ}$) and
`vul_degree_discrete` ($\mathrm{Vul}^{\circ}$) are project-defined, target-free entropy-ratio
analogues. Their notation and bounds do not make them the published target quantities, PID atoms,
or substitutes for a target-conditioned analysis.

## Continuous shared exclusions and PID

Continuous two-source shared exclusions and PID2 are default-off experimental estimators. The
implementation follows the cited finite-sample construction in its restricted domain, but no claim
of unbiasedness or universal consistency is made. The disjunctive common-radius gauge depends on
relative source units and preprocessing. Equal ambient source dimensions are necessary for the
implemented comparison; they do not establish equal intrinsic dimensions or compatible measures.

PID2 atoms are algebraically reconstructed from separately estimated MI/redundancy terms. Exact
reconstruction of those represented terms does not eliminate their different finite-sample biases.
The atom reconstruction is defined in Ehrlich et al.; pid-rs's structured report, split-sample, and
cross-fit workflows are project-defined additions.
The complete PID2 report's covariance matrices describe aligned local estimator contributions; they
are not calibrated sampling covariance, standard errors, or confidence intervals. Cross-fit reports
keep fold-specific gauges and neighborhood coordinates separate and deliberately do not pool them.

Partial continuous PID3 is an incomplete diagnostic. An available node or atom means its exact
implemented dependencies were dimension-compatible, not that a complete PID exists. Full
continuous PID3 contains mixed-dimensional singleton-versus-pair branches whose required measure
theory is unresolved here; it is research-only reference reproduction.

### Finite-union small-ball bound

This subsection is new project analysis in pid-rs. It records a standard consequence of finite
union bounds. It is not a new PID functional, estimator, or scientific-novelty claim.

A branch is one event in an antichain. The raw-radius gauge uses the same numeric radius for all
branches. Branch-weight collapse means that a higher-exponent branch has vanishing probability
relative to the union in this gauge.

Let $E_1(r),\ldots,E_m(r)$ be branch-neighborhood events in one probability space. Assume that

$$
\Pr(E_j(r))=c_j r^{d_j}+o(r^{d_j}), \qquad c_j>0,\ d_j>0,
$$

as $r\downarrow 0$. Let $d_*=\min_j d_j$, let $M=\{j:d_j=d_*\}$, and let
$U(r)=\bigcup_j E_j(r)$. Because the family is finite, the elementary bounds

$$
\max_j \Pr(E_j(r))\leq \Pr(U(r))\leq \sum_j \Pr(E_j(r))
$$

give

$$
\max_{j\in M} c_j
\leq \liminf_{r\downarrow0}\frac{\Pr(U(r))}{r^{d_*}}
\leq \limsup_{r\downarrow0}\frac{\Pr(U(r))}{r^{d_*}}
\leq \sum_{j\in M}c_j.
$$

Thus, the union has order $r^{d_*}$. More precisely, for every
$0<C_{\mathrm{low}}<\max_{j\in M}c_j$ and every
$C_{\mathrm{high}}>\sum_{j\in M}c_j$, there is an $r_0>0$ such that

$$
C_{\mathrm{low}}r^{d_*}\leq\Pr(U(r))\leq C_{\mathrm{high}}r^{d_*},
\qquad 0<r\leq r_0.
$$

The union therefore has positive mass for all sufficiently small $r$. For each branch with
$d_j>d_*$, $\Pr(E_j(r))/\Pr(U(r))\to0$. If $M$ contains one branch, the two outer bounds are equal
and the exact coefficient is that branch's $c_j$. If $M$ contains more than one branch, the
assumptions do not require an exact leading coefficient for the union.

Nestedness in $r$ does not force a coefficient. For a counterexample on $[0,1]$ with uniform
probability, set $a=1/4$, $x=\log(1/r)$, and

$$
q(r)=r\left(\frac12+a\sin x\right),\qquad
e(r)=r-q(r).
$$

For $0<r\leq1/4$, set

$$
A(r)=[0,q(r)],\quad
B(r)=[1/3,1/3+e(r)],\quad
C(r)=[2/3,2/3+e(r)].
$$

Both $q(r)$ and $e(r)$ are positive and at most $3r/4\leq3/16$. Thus, the intervals are pairwise
disjoint and contained in $[0,1]$. Define $E_1(r)=A(r)\cup B(r)$ and
$E_2(r)=A(r)\cup C(r)$. The derivatives satisfy

$$
q'(r)=\frac12+a(\sin x-\cos x)>0,\qquad
e'(r)=\frac12+a(\cos x-\sin x)>0.
$$

Each derivative is at least $1/2-\sqrt{2}/4>0$. Thus, $q$ and $e$ are strictly increasing. For
$0<r_1<r_2\leq1/4$, each of $A$, $B$, $C$, $E_1$, and $E_2$ at $r_1$ is a subset of its counterpart
at $r_2$. Each event has mass exactly $r$, but

$$
\frac{\Pr(E_1(r)\cup E_2(r))}{r}
=\frac{2r-q(r)}{r}
=\frac32-a\sin(\log(1/r)),
$$

which has no limit as $r\downarrow0$. For integer $n\to\infty$, radii
$\exp[-(\pi/2+2\pi n)]$ and $\exp[-(3\pi/2+2\pi n)]$ give the extreme normalized values $5/4$ and
$7/4$. The nested family $E_1(r)=E_2(r)=[0,r]$ attains the lower bound. The nested families
$E_1(r)=[0,r]$ and $E_2(r)=[1/2,1/2+r]$, for $r\leq1/2$, attain the upper bound. Thus, both bounds
are sharp.

An exact coefficient follows under an additional intersection condition. One sufficient condition
is that, for each nonempty $A\subseteq M$,

$$
\frac{\Pr\!\left(\bigcap_{j\in A}E_j(r)\right)}{r^{d_*}}\longrightarrow c_A.
$$

The union of the branches outside $M$ is $o(r^{d_*})$. Finite inclusion-exclusion on the branches
in $M$ then gives

$$
\frac{\Pr(U(r))}{r^{d_*}}\longrightarrow
\sum_{\varnothing\ne A\subseteq M}(-1)^{|A|+1}c_A.
$$

A simpler sufficient condition is
$\Pr(E_i(r)\cap E_j(r))=o(r^{d_*})$ for every two distinct branches in $M$. Bonferroni bounds then
give the coefficient $\sum_{j\in M}c_j$. All higher intersections are subsets of pairwise
intersections and are also negligible.

Any intersection that includes a branch with exponent larger than $d_*$ is negligible at this
scale because the intersection is a subset of that branch. Overlap among minimum-exponent events
can change the leading behavior but cannot change the minimum exponent. More precisely, if
$r_n\downarrow0$ and
$\Pr(E_i(r_n)\mathbin{\triangle}E_j(r_n))=0$ for every $n$, then the positive power-law expansions
force $d_i=d_j$ and $c_i=c_j$.

For an exact interior example, take three independent uniform coordinates and center all balls at
$(1/2,1/2,1/2)$. Let one branch be a one-coordinate ball and let the other branch be a
two-coordinate product ball. For $r\leq1/2$,

$$
\Pr(E_1)=2r,\qquad \Pr(E_{23})=4r^2,\qquad
\Pr(E_1\cap E_{23})=8r^3,
$$

and therefore

$$
\Pr(E_1\cup E_{23})=2r+4r^2-8r^3.
$$

The two-coordinate branch has a vanishing share in the common raw-radius union as $r\downarrow0$.
The known-failure tests evaluate this exact expression and the oscillating-overlap counterexample.

This bound proves raw-radius branch-weight collapse under the stated power-law expansions. It
proves neither consistency nor inconsistency of a kNN estimator. Such a proof must also control the
random kNN radius, sample dependence, local-uniform remainder terms, zero densities, boundaries,
ties, reference measures, neighbor counts, and estimator bias. Substitution of a data-dependent
radius also needs joint measurability and a conditional-law or dependence argument. The
deterministic ratio limit does not transfer to a random radius without the required uniform
control. Equal ambient dimensions remove the immediate exponent mismatch only under the declared
full-dimensional model. They do not prove equal intrinsic exponents or the required intersection
limits.

Dimension-normalized radii, probability-content or rank gauges, and fitted density-power
corrections can prevent the raw exponent imbalance. pid-rs does not implement these proposals.
They change the relative neighborhood gauge and can define a different estimand. They must not be
called the paper-defined estimator without a separate derivation and validation result.

Schick-Poland et al. define a measure-theoretic shared-exclusions PID functional for arbitrary
discrete, continuous, and mixed variable types. pid-rs does not implement a practical general
estimator for that functional; the paper-defined quantity does not make the full-dimensional KSG
or research PID3 code applicable to mixed support.
[Barà et al. (2025)](https://doi.org/10.1103/58bg-5n9s) provide a narrower nearest-neighbour PID
method for a discrete target with continuous sources. That orientation is not implemented here and
does not close the broader arbitrary-support, arbitrary-orientation estimator gap.

For three and four sources, enumerating and inverting a chosen categorical redundancy lattice is a
computability statement. [Lyu, Clark & Raviv (2026)](https://doi.org/10.1103/8rzp-w5z1) establish
incompatibilities among universal cross-subsystem consistency requirements for multivariate
lattice PID. Their result motivates reporting lattice computability, properties proved for a
chosen redundancy functional, and broader consistency desiderata separately; it is not by itself
evidence of a pid-rs code defect or a direct refutation of categorical SxPID.

Heuristic shared-exclusions methods are research-only. Their presence behind a feature is not a
consistency or calibration claim.

## Software-added Gaussian noise

The typed Gaussian-noise contract is project-defined software work. It is not a PID estimator and
has no defining method paper. The `experimental-pipelines` feature exposes the local Rust code.
The current Python API and run-log schema 2 do not expose it. Gao et al. (2018) supplies
KSG-assumption background only.

The ideal model is $Y=X+Z$, where $Z\sim\mathcal{N}(0,\sigma^2 I)$ is independent of the input and
$\sigma>0$. If this declaration is true for all joint coordinates, the noisy population law has a
smooth positive density with full support in the ambient Euclidean space. For a fixed seed, the
generated binary64 matrix is deterministic. It is not a population law.

Gaussian smoothing does not establish finite mutual information. It also does not establish i.i.d.
rows, KSG consistency, calibrated uncertainty, or monotonic PID atoms. A caller must keep these
assumptions separate. The report records this boundary but cannot prove the declaration.

The current transform supports one scalar standard deviation for all cells. Raw columns must have a
declared common unit and calibration. A fixed preprocessing declaration must bind the exact input
matrix identity. This binding does not prove that the preprocessing fit split was valid.

The generator is non-cryptographic. Recorded seeds and unsalted matrix hashes provide no
confidentiality, authenticity, or attestation. pid-rs does not promise exact replay across
different floating-point elementary-function implementations.

One declaration covers one matrix. Separate declarations do not establish mutual independence
across sources and a target. The joint full-support result needs one joint population-noise model
for all coordinates. pid-rs does not yet implement that higher-level report.

One `SeededScaleSensitivityProbe` is not a sensitivity result. A complete study must also bind the
unmodified comparison, scale grid, coupling policy, and all outputs. pid-rs does not yet implement
that trajectory type. The legacy `Jitter` type returns only a matrix and drops generated
application provenance.

## Geometry and hyperbolic paths

Intrinsic-dimension and distance-concentration outputs are sample diagnostics, not population
certificates. Local dimension can vary across a dataset, and nonlocal radii invalidate small-ball
interpretations.

Lorentz-hyperbolic distance conversion is numerically guarded, but pairwise hyperbolic KSG remains
research-only because correct distance computation does not prove an entropy/MI estimator on that
manifold. Hyperbolic shared exclusions and PID are unsupported.

## Preprocessing, uncertainty, and testing

Target-adaptive preprocessing fitted on evaluation rows leaks target information. Fit and select
standardization/PCA/PLS/quantization on training data, freeze it, and estimate on held-out rows.
Same-sample supervised PLS→PID is exploratory only. Constant columns require an explicit fitted
policy; fitted parameter/training hashes establish identity but do not prove train/evaluation
separation or scientific suitability.

Moving-block bootstrap and permutation procedures are valid only under their stated dependence or
exchangeability assumptions. Restricted circular shifts are approximate surrogate scores, not
exact randomization p-values. Random-origin circular-grid kNN subsample percentile ranges are sensitivity
diagnostics, not calibrated confidence intervals for the full-sample estimate. BH requires its
dependence conditions; BY is more conservative but still assumes valid input p-values.
Typed declarations and complete failure retention prevent silent reinterpretation, but they do not
establish the caller's sampling assumptions or calibrate a generic statistic. Cooperative
cancellation returns no partial estimate and does not make an intrinsically expensive procedure
cheap.

The cited moving-block, permutation, add-one p-value, and BH/BY procedures remain distinct from
pid-rs's project-defined typed assumption records, scheduling, failure-retention, and report
schemas. Those engineering additions do not create a generic confidence-interval or
randomization-test theorem for an arbitrary callback statistic.

Known-failure fixtures intentionally cover mixed-dimensional collapse, atom/continuous mixtures,
singular maps, tied shells, local dimension heterogeneity, high-dimensional concentration,
hyperbolic nonlocal radii, same-sample PLS optimism, and invalid permutation nulls. A deliberate
failure is evidence that an unsupported regime is rejected or exposed, not that it became valid.

## Software identity

`software_identity()` is project-defined infrastructure with local Rust/Python code and no defining
method paper. It is an inspectable record, not authentication, an estimator-validity certificate,
or a binary fingerprint. Its public Rust API revision covers only the exact proposed release-scope
feature profiles; it does not version Python API/ABI, numerical behavior, method definitions,
scientific evidence, package-version compatibility, or executable bytes.

Workspace source state is limited to `crates/pid-core`: repository-root files, `Cargo.lock`, and
sibling crates are outside its clean/dirty flag. In a layout-matched workspace, the Git route is
authoritative: a Git failure produces a typed unavailable state and does not fall back to a stray
`.cargo_vcs_info.json`. Here, layout-matched includes the expected canonical directory structure,
repository markers, and a `.git` entry at the root. A source archive without `.git` is an
unrecognized layout, not a layout-matched Git failure. Other layouts use Cargo package metadata
when valid. Its `dirty` field is a version-dependent, best-effort archive-creation observation, not
the current extracted tree; an omitted flag is reported as `unknown`, not inferred clean. Either
route may be unavailable, and a named commit does not prove authorship, authenticity, or equality
between that commit, a source archive, and an executable. Format 1 accepts only full lowercase
40-hex SHA-1 commit identifiers; Git SHA-256 object identifiers are rejected as unsupported rather
than truncated or reinterpreted.

The workspace result is a build-script-time snapshot, not a live Git monitor. Ambient Git routing,
replacement/graft, config, pathspec, ref-backend, and global/system attribute overrides are
neutralized. Bounded Cargo watches cover ordinary package, marker, attribute, linked-worktree,
index, config, and files/reftable-ref transitions; unavailable states retain an absent recovery
watch. The bounded `objects/info` metadata directory is watched, including repository-local
alternate-store routing, but the referenced external object stores are not live-monitored. Any
effective `filter` attribute on a tracked package path (including unset or unconfigured values),
`attr.tree`, tracked symbolic links, and tracked gitlinks yield `unknown`. Deliberate manual
repository-layout rewrites that create a previously absent `commondir`, in-place replacement of the
Git executable, and later loss/corruption of an otherwise unchanged object database are outside
that invalidation contract. The cached observation remains the state captured by the earlier build;
it does not claim current tool or object-store availability. Config includes and unsupported
ref-storage payloads intentionally make Cargo re-run the probe conservatively.

Workspace clean/dirty probing requires Git 2.45 or newer. Older versions yield `unknown` because
the isolation contract depends on versioned Git behavior for global configuration, fsmonitor, and
lazy fetching. A clean/dirty result also assumes repository metadata and package files do not change
concurrently during the bounded probe. Repeated status/input checks and a final HEAD read catch
ordinary mid-probe changes, but no finite reread is an atomic filesystem snapshot; ABA mutation and
hostile concurrent rewriting remain outside the claim.

The build script repeats the typed source, workspace-layout, and exact reference-byte checks at the
end and aborts when those claimed inputs changed during execution. This closes the ordinary Cargo
mtime window but does not turn the filesystem into a transaction: a change after the final check or
an ABA rewrite remains governed by the stable-input assumption.

Build context records only the compiler version when discoverable, target, Cargo profile,
optimization level, debug-information flag (not debug assertions), and enabled `pid-core`
features. It omits dependency artifacts, linker inputs, arbitrary compiler flags, environment, and
output bytes. Two different executables can therefore share the recorded fields, and legitimate
builds can differ without implying a scientific change.

Reference SHA-256 values identify the exact raw bytes of canonical repository files, not necessarily
the Git blob at the source commit. Verification depends on the layout in which `pid-core` is
compiled, not on the final artifact type: an exact layout-matched workspace verifies the current
root files against the manifest, while other layouts carry the manifest-declared values without
re-verifying those files. Consequently, a source archive without `.git` does not re-verify root
reference files even if the archive contains them. Published crate archives and wheels need not
contain the repository-root paths; `repository_path` is routing metadata, not a package-local
availability promise. Matching hashes does not establish API compatibility, data quality,
scientific or application validity, source/archive/binary equality, or cross-platform numerical
identity. Format 1 explicitly reports `attestation = none`; no source, dependency-graph,
supply-chain, or executable attestation should be inferred.

Public Rust declaration snapshots are retained under immutable revision-scoped paths with their
generation context. A registry entry names the preceding source commit whose declarations were
captured; the following evidence commit contains the snapshot bytes. Append preservation checks
every HEAD-reachable commit that touched the registry, each direct tip parent, and monotone source
ancestry. Once a committed registry binding is an ancestor, the exact snapshot bytes are also
checked at binding states, direct tip boundaries, and every reachable commit in that snapshot
path's full history. Pre-binding states remain outside that interval. An unreachable never-merged
branch, force-push, complete repository rollback, or coordinated replacement of code and internal
hashes cannot be detected without an external monotonic trust anchor; the registry is not a
transparency log, timestamp, or attestation. The local checker removes ambient Git routing and
configuration, disables replacement/graft overlays, and requires the canonical Git worktree root
to match the files being checked, but those controls cannot recover objects or references absent
from the presented repository.

## Resources, Python, and run logs

Some exact pairwise and lattice operations remain quadratic or combinatorial. Use the resource
preflight/budget APIs; a successful estimate at one size is not a runtime guarantee at a larger
size. Allocation and parser budgets reject oversized work rather than overcommit memory.
Generic resampling/permutation estimates cannot see allocations or complexity inside a caller's
opaque statistic callback. Experimental PLS/logistic QR and dense-factorization paths conservatively
preflight and hard-cap solver dimensions, but nalgebra still owns internal infallible allocations;
those quarantined research backends therefore cannot promise recovery from operating-system
allocator exhaustion below the declared ceiling.
Run-log byte/event/container limits are enforced before or during decoding and aggregate replay,
and destination vectors reserve fallibly. Serde-owned nested strings/JSON values and deterministic
`BTreeMap` nodes still use Rust's infallible allocator within those finite ceilings; like nalgebra,
they cannot convert process-wide allocator exhaustion below the chosen ceiling into a recoverable
error. Choose limits comfortably below the process memory boundary.

The Python extension uses native code through PyO3. Stable calls validate/copy or otherwise own
inputs before GIL release; callers must still avoid assuming that concurrently mutated arrays have
snapshot semantics unless the specific API documents it.

Run-log hashes and colocated sidecars detect internal inconsistency; they do not authenticate a log
that an attacker can replace together with its digest. Store the release/run digest in a trusted
external signed anchor when tamper evidence is required. Atomic sidecar replacement flushes the
new file on every supported desktop target and additionally flushes the parent directory on Unix.
Rust exposes no portable Windows directory-flush operation, so an immediate power loss can lose a
just-renamed Windows directory entry even though readers never observe a truncated sidecar.

For reproducible release verification, see [RELEASE_REPRODUCTION.md](RELEASE_REPRODUCTION.md).
