# Ecosystem compatibility audit

## pid-rs, Prisoma, Galadriel, Haldir, and Crebain

**Audit date:** 2026-07-25

**Status:** source-read compatibility review; not qualification, deployment approval, or an authority claim

**Companion source:** [`audit/formal/latex/ecosystem-compatibility-audit.tex`](audit/formal/latex/ecosystem-compatibility-audit.tex)

## Claim boundary

This report compares four consumer source bases with the pid-rs contracts at the revisions and
working-tree states recorded below. It separates implemented behavior, planned behavior, stale
documentation, and missing evidence. It does not certify a checkout, prove a deployment assumption,
or approve scientific or operational use.

The existing [`ecosystem-capabilities.json`](ecosystem-capabilities.json) remains the
machine-readable authority for its historical capability-and-gap projection. This report has a
different purpose. It records concrete integration findings from the observed local consumer
checkouts. It is review evidence, not a generated contract.

No repository was missing. Three source bases were not clean, including two consumer checkouts.
Therefore this review cannot bind all findings to immutable trees:

| Repository | Source base read | Working-tree state during review | Consequence |
|---|---:|---|---|
| pid-rs | `67e8b92d42d23a051b839bc81ba05c26c08377fe` | 30 pre-existing entries before this report | Current local contracts were read, but this is not an immutable release snapshot. |
| Prisoma | `879a1909a986bda381f86979b5c02e3cec89d68c` (`main`) | clean | Findings bind this local commit. |
| Galadriel | `80506dd2ce52b33c3334c7d1760a8155c7631241` (`main`) | 64 entries | Relevant `galadriel-pid` changes were documentation wording; the live files were read. The full checkout is not immutable evidence. |
| Haldir | `bb6c0a7b27bbc57fe9935f80e22d06ca3b60e8ba` (`wip/current-file-review-ledger`) | 12 entries | The two evidence files used below were unchanged. This is not a `main`-branch release claim. |
| Crebain | `f1f4c050a1aa6f703b1b25699c232f4305bfb001` (`main`) | clean | Findings bind this local commit and the current-head refresh below. |

A release qualification must repeat this audit against clean, pinned commits and retain the exact
input and output hashes.

**Current-head Crebain refresh.** Crebain was rechecked at the clean commit above against the
previously audited base `448c9c43c15b0081c879037aa62b6a9f1bc4a341`. The three-commit delta
touches 12 dependency, security, baseline, and CI files (171 insertions and 93 deletions);
`git diff --check` passed. A complete manual diff review found no change to PID/SxPID behavior,
the Galadriel scientific data contract, sensor-fusion algorithms, or the authority boundary. In a
detached clean worktree, a frozen-lockfile install followed by `bun run validate:all` exited zero,
including 551 frontend tests, 383 passed/1 ignored default Rust library tests plus 22 benchmark
tests, and 485 passed/1 ignored NCP-feature Rust library tests plus 22 benchmark tests. The
original checkout's ignored `.env` correctly caused the Phase 0 baseline gate to reject ambient
state; that file was neither read nor moved, and the detached worktree was used instead. These are
source and component-validation results. They are not a release qualification, live receiver or
deployment test, statistical calibration, or end-to-end PID evidence.

## Review method

The review used a claim-to-code trace, not a keyword count:

1. Read each available repository instruction file and rechecked source interpretations against it.
2. Recorded the active branch, commit, dirty state, dependency pins, and submodule pin.
3. Traced data from producer or adapter, through preprocessing and estimator selection, to reported
   status and any downstream authority boundary.
4. Preferred executable source and manifests over summaries. Marked a document stale when its claim
   contradicted current code.
5. Challenged the operational rule with exact negative constructions. Direct enumeration of the
   four equiprobable binary states verified the XOR and target-rotation identities. The
   coherent-majority case follows from the closed-form Gaussian MI formula.
6. Searched manifests and Rust sources before stating that no direct dependency was found.
7. Did not treat passing component tests, declared assumptions, or producer publication as
   end-to-end scientific evidence.

Apart from the current-head Crebain source/component validation recorded above, the review did not
run consumer release qualification, a live Neuro-Cybernetic Protocol (NCP)/Galadriel deployment,
or a statistical calibration study. Companion PDF build and render checks are a separate
presentation-integrity evidence layer; they do not fill those scientific or operational gaps.

## Executive determination

No qualification evidence against the pid-rs source base reviewed here was found in the reviewed
consumer source bases.

| Consumer | Implemented today | Current determination | Principal blocker |
|---|---|---|---|
| Prisoma | Direct path dependency through a pinned pid-rs submodule; continuous and discrete $I_{\min}$ screens | **Partly integrated; not scientifically qualified** | The SAFE adapter omits the harness support contract. Current same-row PLS and quantizer paths are descriptive. No confirmatory holdout is registered. |
| Galadriel | Direct immutable pid-core pin; pairwise-KSG clique verdict; report-only continuous shared-exclusions atoms | **Advisory research integration only** | The verdict is not a PID verdict. It cannot detect pure synergy, assumes agreement implies the trustworthy majority, changes the atom target across channel rows, and lacks fleet/sequential calibration. |
| Haldir | No direct pid-rs dependency found; design/review document only | **Not integrated; permanent no-authority boundary** | The design note contains stale pid-rs claims and no executable adapter. PID evidence must never grant or widen authority. |
| Crebain | Optional Galadriel-compatible evidence producer; no direct pid-rs dependency found | **Producer plumbing only** | No live receiver/window assembler/PID adapter exists. The observation envelope lacks the scientific and estimator contract required for a PID claim. |

The lifecycle state of each claim is explicit:

| Consumer | Current implementation | Planned or missing interface | Stale statement | Unsupported interpretation |
|---|---|---|---|---|
| Prisoma | Pinned harness with continuous and discrete $I_{\min}$ screens | H3 endpoint scorer, held-out frozen transform, updated schema | SAFE says it mirrors the Rust schema exactly | Same-row fitted PLS/bins or an asserted support model as confirmatory evidence |
| Galadriel | Pairwise-MI clique verdict plus report-only PID atoms | Fleet and repeated-window calibration; fixed-target atom report | Broad “PID engine/verdict” naming hides the decision statistic | Pure-synergy detection, trustworthy-majority inference, causal fault attribution |
| Haldir | No executable PID adapter found | Advisory Mirror receiver and evidence contract | No multiplicity correction; generic jitter repair; raw resampling “CI” | PID-created authority, alarm-grade latency, calibrated posterior |
| Crebain | Optional bounded evidence producer | Live receiver, window receipt, scientific/estimator adapter | Historical cross-repository revision records are not current integration proof | JSONL/NCP publication as end-to-end PID, calibration, receipt, or authority |

The executive rows are not single-lens conclusions. Each determination is justified by the
seven-lens assessment below. A route fails qualification if any required lens remains unsupported.

## Mandatory seven-lens assessment

### Prisoma

| Lens | Evidence-based conclusion |
|---|---|
| Provenance | Prisoma pins pid-rs at `796c11e70f009634b853dc4ada6f565563d82f51`, not the pid-rs source base reviewed here. The consumer checkout was clean, but compatibility with current pid-rs has not been established. |
| SxPID estimand compatibility | Current discrete harness routes are labelled $I_{\min}$, which is not shared-exclusions PID. The continuous ISX route is a different estimator and regime. No measure-specific $I_{\min}$ atom value, theorem, sign property, or benchmark transfers to SxPID without an explicit mapping theorem. |
| Mathematical assumptions | A usable route needs a fixed target, disjoint transform fitting, a justified finite alphabet or declared continuous support, a valid row-dependence model, and a predeclared selection family. The current support value is asserted by the caller, not proved by data. |
| Implementation/API | The SAFE schema omits the Rust harness's top-level `support` map. Same-row PLS and quantizer fitting remain descriptive. The holdout registry contains no confirmatory holdout. |
| Numerical/statistical validity | Missing support causes typed continuous abstention. KSG/ISX geometry gates do not establish consistency in the application law. Same-row fitting has no out-of-sample calibration, and raw resampling ranges are not generic PID confidence intervals. |
| Adversarial/operational misuse | Independent high-dimensional noise can be target-fitted to interpolate the evaluation labels, producing maximal training-row association with zero test-law MI. An asserted support label can also turn a model assumption into an apparently measured fact. |
| Authority | Prisoma results may support a preregistered offline scientific analysis only. They cannot by themselves authorize deployment, select a model on the confirmatory rows, or convert an abstention into evidence of no effect. |

### Galadriel

| Lens | Evidence-based conclusion |
|---|---|
| Provenance | Galadriel pins pid-core at `1cd2424f7967e1752dcc8e53859e8fdad3566f51`, not the pid-rs source base reviewed here. The checkout was dirty; relevant `galadriel-pid` differences were documentation wording, but the tree is not immutable qualification evidence. |
| SxPID estimand compatibility | The operational verdict is a pairwise-MI clique rule. Continuous SxPID atoms are report-only and do not drive it. Atom rows change the target, so they are not coordinates of one fixed PID. Pairwise MI, $I_{\min}$, categorical SxPID, and continuous ISX results are not interchangeable. |
| Mathematical assumptions | The route needs regular full-dimensional continuous laws, finite MI, valid row sampling, common scalar projections, a fixed scientific target for atom comparison, and justified threshold construction. Added pseudo-noise proves none of these assumptions. |
| Implementation/API | PID is optional and off by default. The engine computes all gated pairwise MI values, selects a unique strict-majority clique, and separately reports atoms. It uses legacy `Jitter`, which changes the analysed law and lacks a complete application receipt. |
| Numerical/statistical validity | Geometry and shell checks are one-sided diagnostics, not calibration. Delete-block stability is not a generic confidence interval. There is no fleet-level, repeated-window, post-selection, or false-alarm guarantee for the clique threshold or attribution. |
| Adversarial/operational misuse | XOR is invisible to the pairwise graph; a coherent faulty majority can isolate the honest channel; rotating targets invalidate cross-row atom comparison. Common-mode faults require no adversary and produce the same majority failure. |
| Authority | Galadriel's own rules correctly keep PID advisory: `Nominal` cannot create permission and insufficient evidence cannot become nominal. No MI edge, clique, atom, or score may grant or widen authority. |

### Haldir

| Lens | Evidence-based conclusion |
|---|---|
| Provenance | No direct pid-rs or pid-core dependency was found. The reviewed PID material is a design/adversarial note on a dirty non-main branch; the cited note and frozen authority file were unchanged. |
| SxPID estimand compatibility | No executable SxPID estimator or adapter exists. The note distinguishes $I_{\min}$ from $I^{\mathrm{sx}}$, and that distinction must remain. A result from either definition cannot validate the other without a mapping theorem for the declared distribution class and atom semantics. |
| Mathematical assumptions | Sequential monitoring, adaptive windows, drift, dependence, missingness, transform selection, and post-selection all need explicit theorems or validation. A fixed-window estimator theorem does not establish alarm or authorization performance. |
| Implementation/API | The proposed Mirror path is not implemented. The note has stale claims about multiplicity correction, recommends generic jitter repair, and labels uncalibrated resampling ranges as confidence intervals. |
| Numerical/statistical validity | Current pid-rs BH/BY functions require valid input p-values and their dependence conditions. Block sensitivity ranges are not generic KSG/PID intervals. The sample-size/latency conflict and slow-drift blind spot remain unresolved. |
| Adversarial/operational misuse | A coherent wrong majority, slow drift, missing evidence coerced to zero, or a score-to-command bridge can all defeat the intended interpretation. Verification of the statistic does not resolve reference truth or causal attribution. |
| Authority | The permanent invariant is non-expansion: any PID-aware authorization must imply the original authorization. PID may restrict an already allowed action under a predeclared rule; it may never create an `ALLOW`, override a failed conjunct, or route a command. |

### Crebain

| Lens | Evidence-based conclusion |
|---|---|
| Provenance | The clean checkout has no direct pid-rs dependency. Historical cross-repository revision records and a successful local producer `put` do not prove receiver receipt, accepted schema, estimator identity, or deployed compatibility. |
| SxPID estimand compatibility | `PidObservation` is an envelope name, not an SxPID definition. It does not bind a target, ordered source tuple, measure, lattice, units, or atom semantics. NIS and consistency projections cannot be transplanted into PID quantities. |
| Mathematical assumptions | A valid adapter needs a fixed frame/context/horizon, row unit, receiver-window construction, missingness and drift accounting, support declaration, transform split, and source/target semantics. These fields are absent from the current envelope. |
| Implementation/API | The optional producer is off by default and needs exact runtime opt-in. No live receiver, window assembler, registry transform executor, or pid-rs adapter was found. Projection is emitted only for an already matching frame and empty transform chain. |
| Numerical/statistical validity | Producer bounds and NIS fields do not calibrate PID. Publication does not establish delivery or acceptance. No estimator configuration, typed abstention, interval status, multiplicity family, or run-log replay receipt accompanies the observation. |
| Adversarial/operational misuse | Loss, reorder, duplicates, restart, saturation, target rotation, coherent-majority data, and registry disagreement can change a downstream window or estimand while the producer remains locally successful. |
| Authority | Crebain's present trust-domain table correctly gives Galadriel advisory observation and no command capability. Producer, receiver, observer, Haldir, command, and plant credentials must remain separate. |

The useful path is narrow but real. Categorical or independently frozen quantized SxPID can support
offline, low-cardinality, held-out analysis when the row law, target, transform, support, and
uncertainty contract are explicit. Continuous KSG/ISX remains a restricted research route. Neither
route supplies mission authority.

## Terminology

There is no PID measure called “colored PID.” Dependency coloring qualifies a finite-sample
concentration theorem for categorical SxPID. It is a statement about dependence among sample rows.
It is not a new PID functional, estimator, or term attributed to Makkeh, Gutknecht, or Wibral.
Consumer interfaces must use “dependency-colored concentration for categorical SxPID” or equivalent
language, not “colored PID.”

## Minimal mathematical primer

For discrete random variables, mutual information is

$$
I(X;T)=\sum_{x,t}p(x,t)\log\frac{p(x,t)}{p(x)p(t)}.
$$

It is zero exactly when the variables are independent. It measures statistical dependence, not
causality, truth, intent, or fault.

A two-source PID resolves the total information into four coordinates:

$$
I((S_1,S_2);T)=\mathrm{Red}+\mathrm{Unq}_1+
\mathrm{Unq}_2+\mathrm{Syn}.
$$

The target $T$ is part of the definition. Changing it changes the decomposition. Shared-exclusions
PID also separates informative and misinformative pointwise components; its signed net atoms may be
negative. Williams--Beer $I_{\min}$ uses a different redundancy definition. Its output must not be
presented as shared-exclusions PID.

### No-transplant rule

Let a claim $C_M$ be proved or validated for a measure or estimator $M$. It may be used for another
measure or estimator $N$ only if an explicit mapping theorem states the distribution class,
target/source semantics, lattice coordinates, normalization and units, numerical representation,
and the property preserved by the map. Shared atom names, a common reconstruction identity, similar
benchmark values, or use of the same mutual-information terms are not such a theorem.
This review found no mapping theorem in the checked source that licenses any transfer below.

Consequently:

- $I_{\min}$ results do not validate SxPID atoms;
- categorical SxPID theorems do not validate continuous ISX estimators or claims about an
  unquantized law;
- KSG MI checks do not validate continuous PID atom bias, variance, or coverage;
- two-source results do not validate three-source or mixed-dimensional lattices; and
- a pairwise-MI consensus rule does not become a PID decision rule because PID atoms appear in the
  same report.

When no mapping theorem exists, the adapter must report separate estimands and separate evidence.

The categorical routes operate on finite empirical count tables. KSG and continuous ISX use local
neighbourhood geometry and need stronger population-support, sampling, dimension, and tie
assumptions. A correct formula or clean software test does not establish those application
assumptions.

## Common compatibility contract

A consumer adapter must retain the following fields. A string label without the corresponding
evidence is not sufficient.

### Identity

- Consumer repository, commit, dirty state, build features, and executable identity.
- Exact pid-rs revision, crate version, public API revision, method-catalog entry, and catalog digest.
- Units. All pid-rs information quantities are in nats.
- Exact estimator family. `I_min`, categorical shared exclusions, quantized shared exclusions, and
  continuous shared exclusions are different routes. One is not a silent fallback for another.

### Scientific roles

- One declared target and an ordered, labelled source tuple.
- The physical meaning, units, common frame, and time horizon for every variable.
- The row unit: frame, episode, track window, trial, subject, or another declared unit.
- The population or finite-population estimand. A window estimate is not automatically a fleet or
  trajectory estimand.

### Sampling and support

- IID, stationary, exchangeable-block, dependency-color, or unsupported row status.
- For a dependency coloring, a deterministic color map and a justification of **mutual**
  independence of complete rows within each color. Pairwise uncorrelatedness is not enough.
- Drift and selection declarations. Concentration about an average row law does not identify a fixed
  target law without a separate drift bound.
- Categorical alphabet identity, or a continuous/mixed support declaration. Observed uniqueness
  cannot prove continuous full-dimensional population support.
- A population support floor only when a theorem requires it. An observed minimum cell mass cannot
  substitute for an unknown population floor.

### Preprocessing

- Training row identities, evaluation row identities, and proof of disjointness at the correct
  episode/subject level.
- Frozen transform bytes or parameters, source order, training digest, and application digest.
- Target-adaptive operations such as PLS selection and fitting must occur outside evaluation rows.
- Quantizer edges are part of the estimand. Same-row fitted bins define a descriptive, data-adaptive
  quantity.
- Added noise must have a declared observation model or be labelled a sensitivity analysis. It
  changes the estimated law. It is not a generic repair for ties.

### Estimation and outcomes

- Estimator parameters, metric, neighbour count, gauge, seeds, resource limits, and signed negative
  handling.
- `produced`, `warning`, `abstained`, and `failed` as distinct states. Missing or invalid output must
  never become numeric zero.
- Signed informative, misinformative, and net atoms where available. A negative net atom is not a
  fault, intent, causal, or responsibility finding.
- The exact status of every interval: certified numerical enclosure, calibrated confidence
  interval, raw resampling percentile, or sensitivity envelope.
- A predeclared multiplicity family and valid input p-values before BH/BY is applied.

### Replay and authority

- Input, transform, configuration, output, run-log, and software-identity digests.
- A replay result that verifies terminal statuses, not only successful scalar values.
- An explicit `advisory_only` or stronger no-authority marker.
- A rule that no atom, interval, score, or missingness state can create or widen an authorization.

## Prisoma

### What is implemented

Prisoma directly consumes the pid-rs submodule at
`796c11e70f009634b853dc4ada6f565563d82f51`. The local harness records this revision in
`crates/pid-sim/src/offline_harness.rs:3937-3938`. This pin is older than the pid-rs source reviewed
here. Compatibility with current pid-rs `main` has not been established.

The offline harness implements:

- continuous KSG/ISX screens under a caller assertion of regular full-dimensional support;
- discrete and discrete-PLS screens labelled `discrete_imin` and `pls_discrete_imin`;
- fitted equal-width quantization; and
- typed abstention for support, geometry, shell, and uncertainty failures.

The current continuous configuration is honest about its boundary. The
`assume_regular_full_dimensional` constructor is an assertion, not proof
(`crates/pid-sim/src/offline_harness.rs:4276-4286`).

### Confirmed adapter defect

The Python SAFE adapter says that it mirrors `OfflineVldaDataset` “exactly”
(`experiments/safe_adapter/contract.py:1-14`). It does not.

The Rust dataset now contains a top-level `support` map. A missing axis fails closed as
`support_contract_unspecified` (`crates/pid-sim/src/offline_harness.rs:369-378`,
`:3964`, and `:3998`). The Python `VldaDataset` has only `samples`, `run_id`, `source`, `model`, and
`task`. Its serializer emits no `support` field
(`experiments/safe_adapter/contract.py:147-211`). The converter and verifier also omit support
(`experiments/safe_adapter/convert.py:376-395` and
`experiments/safe_adapter/verify.py:50-135`).

Therefore a dataset can pass the SAFE adapter verifier and still force every continuous harness
tuple to abstain. This is a current, reproducible schema incompatibility. It is not a statistical
opinion.

Required correction:

1. Add a closed enum support declaration for `v`, `l`, `d`, and `a`.
2. Reject missing, unknown, or contradictory axis declarations in the Python verifier.
3. Preserve `capture_integrity` and `publication_receipt` when an NCP artifact requires them.
4. Add a negative fixture that passes the old verifier, reaches the Rust loader, and must return
   `support_contract_unspecified`.
5. Remove “exactly” from the adapter documentation until a cross-language schema test proves it.

### Same-row fitting is exploratory

`DiscretePls` fits source-to-target PLS on the rows supplied to the screen and transforms those same
rows (`crates/pid-sim/src/offline_harness.rs:1291-1328`). The quantizer likewise fits on `x` and
transforms `x`; the code correctly calls the route descriptive
(`crates/pid-sim/src/offline_harness.rs:4302-4314`). Leave-one-out selection of the number of PLS
components does not make the final same-row projection held out.

A simple negative construction explains the risk. Let an evaluation design matrix
$X\in\mathbb{R}^{n\times p}$ contain continuous noise independent of a binary target $T$, with
$p\ge n$. With probability one, $X$ has row rank $n$. A target-adaptive linear fit can choose $w$
such that $Xw=T$ on those rows. Let $\widehat P_n$ be the discrete empirical law assigning mass
$1/n$ to each fitted pair $(Z_i,T_i)$, where $Z=Xw$. Then
$I_{\widehat P_n}(Z;T)=H_{\widehat P_n}(T)$ even though the population relation is $I(X;T)=0$.
This finite-table identity is not a claim that KSG is valid on the resulting tied, singular sample.
It does not say that every PLS call interpolates. It proves that same-row target-adaptive fitting
cannot, by itself, support an inferential PID claim.

### Holdout and endpoint status

`protocols/holdout_registry_v1.json` records `holdout_count: 0`. The H3 power path also states that
the current H1 feature model lacks the train-reference local PID/CI scores, leakage tests, censoring
rules, and mandatory baselines required by the endpoint
(`crates/pid-sim/src/power.rs:1383`). These are blockers, not future-looking caveats.

### Realistic Prisoma regime

An offline Prisoma claim is workable when all of the following hold:

- source and target roles are fixed before analysis;
- a low-cardinality categorical model is scientifically justified, or a quantizer is fitted on
  disjoint training episodes and frozen;
- evaluation episodes are disjoint and the row-dependence contract is valid;
- the complete testing family and endpoints are preregistered;
- atom signs and abstentions are retained; and
- a registered confirmatory holdout is evaluated once under the frozen pipeline.

High-dimensional learned embeddings, same-row supervised projections, adaptive quantization,
overlapping episode rows without a valid dependence theorem, and unrestricted continuous PID are
not in that regime.

## Galadriel

### What is implemented

Galadriel pins pid-core revision
`1cd2424f7967e1752dcc8e53859e8fdad3566f51` with `experimental-pipelines`
(`Cargo.toml:63-70`). This is not the pid-rs revision reviewed here.

The PID path is optional and off by default. Signed-correlation analysis remains the default.
Galadriel's own architecture rules say that `Nominal` cannot create permission and
`InsufficientEvidence` cannot become `Nominal` (`AGENTS.md:117-146`). These are correct permanent
boundaries.

The operational rule in `crates/galadriel-pid/src/engine.rs:1283-1527` is:

1. estimate every pairwise channel MI that passes the geometry and numerical gates;
2. define an edge threshold from the MI floor and the strongest pair;
3. find the largest MI clique;
4. require one unique strict-majority clique; and
5. attribute an excluded channel only when all of its assessed clique edges are below threshold.

The shared-exclusions redundancy and synergy fields are computed separately. They do not drive the
verdict (`crates/galadriel-pid/src/lib.rs:40-44` and
`crates/galadriel-pid/src/engine.rs:1378-1389`). The correct name is therefore “pairwise-MI consensus
with report-only PID atoms,” not “a PID verdict.”

The code asserts continuous support
(`crates/galadriel-pid/src/engine.rs:1625-1640`) and adds deterministic Gaussian pseudo-noise through
the legacy `Jitter` primitive (`:1820-1848`). Current pid-rs states that `Jitter` changes the law,
drops application provenance, and is not a generic tie repair
(`crates/pid-core/src/preprocess.rs:1376-1386`). Galadriel records a configured scale and seed, but
that does not prove the population noise model, finite MI, IID rows, or calibration.

### Counterexample 1: pure synergy is invisible to the verdict

Let $X$ and $Y$ be independent fair bits and let $T=X\oplus Y$. Then

$$
I(X;Y)=I(X;T)=I(Y;T)=0,
\qquad
I((X,Y);T)=\log 2.
$$

The proof is direct. Conditional on either input, $T$ remains fair, while $T$ is deterministic when
both inputs are known. The pairwise MI graph has no positive edge, despite $\log 2$ nats of
joint-target information. With a positive MI floor the Galadriel verdict is insufficient. The
report-only PID fields cannot change it.

This is a discrete structural counterexample to the decision statistic. It is not a claim that the
continuous KSG implementation should run on binary XOR data. It proves that a pairwise consensus
graph is not a general synergy detector.

### Counterexample 2: coherent majority can invert attribution

Let $A,U,E_1,E_2,E_3$ be independent standard Gaussian variables. Define three coherent channels
and one honest independent channel by

$$
M_j=A+\sigma E_j\quad(j=1,2,3),
\qquad H=U,
\qquad \sigma>0.
$$

Every pair $(M_i,M_j)$ is regular and jointly Gaussian with correlation
$\rho=1/(1+\sigma^2)$, so

$$
I(M_i;M_j)=-\tfrac12\log(1-\rho^2)>0,
\qquad I(H;M_j)=0.
$$

For a threshold between zero and the within-majority MI, the unique strict-majority clique is
$\{M_1,M_2,M_3\}$. The rule attributes $H$ as decoupled. If the coherent channels share a common
fault or coordinated spoof while $H$ is correct, attribution is exactly reversed. The algorithm
finds agreement, not truth. Geometry gates and delete-block confirmation cannot supply a trusted
reference label.

This counterexample requires no adversary. A common-mode calibration error has the same structure.

### Counterexample 3: the reported atoms do not share one target

For channel index `i`, `isx_atoms` sorts the other modalities, uses the first as a peer, and defines
the target as the mean of the remaining channels
(`crates/galadriel-pid/src/engine.rs:1862-1905`). With three modality keys ordered $X<Y<Z$, the rows
are:

| Report row | Source 1 | Source 2 | Target |
|---|---|---|---|
| $X$ | $X$ | $Y$ | $Z$ |
| $Y$ | $Y$ | $X$ | $Z$ |
| $Z$ | $Z$ | $X$ | $Y$ |

Input vector permutation is tested and stable. Scientific target rotation is a different issue.
The rows decompose different total mutual informations.

For an exact example, let $X,Y$ be independent fair bits and encode $Z=(X,Y)$ as one four-state
variable. Then

$$
I((X,Y);Z)=2\log 2,
\qquad
I((Z,X);Y)=\log 2.
$$

No PID atom vector can be invariant to that target change because its atom sum changes. Cross-row
atom comparisons therefore require an explicit statement that the estimand changes with the row.
They must not be interpreted as per-channel coordinates of one fixed decomposition.

### Realistic Galadriel regime

The current engine can be used as an advisory dependence screen when:

- scalar common-frame projections and one window identity are fixed;
- the population support assertion is scientifically defensible;
- effective row dependence, drift, and missingness are declared;
- enough data exist for the geometry and estimator gates;
- thresholds are calibrated for the exact fleet, route, and repeated-window policy;
- common-mode and coherent-majority counterexamples are included in validation; and
- the output remains a non-causal, non-authorizing screen.

It is not a pure-synergy detector, a trusted-majority oracle, a calibrated attack posterior, or a
general which-channel fault locator.

## Haldir

### What exists and what does not

No direct `pid-rs` or `pid-core` dependency was found in Haldir manifests or Rust source. The main
PID-related artifact read here is `docs/galadriels-mirror.md`. It is a design and adversarial review,
not an executable integration.

Three statements in that document are stale or too strong against current pid-rs:

1. `docs/galadriels-mirror.md:356` and `:423` say that pid-core ships no multiple-comparison
   correction. Current pid-rs exports both Benjamini--Hochberg and Benjamini--Yekutieli under
   `experimental-pipelines` (`crates/pid-core/src/pipeline.rs:28-32`, `:3703`, and `:3732`). Their
   guarantees still require valid p-values and the stated dependence conditions.
2. `docs/galadriels-mirror.md:270` recommends seeded jitter as a tie/radius repair. Current pid-rs
   explicitly rejects generic jitter repair. Added noise changes the estimand.
3. The note repeatedly calls raw block-subsample ranges “CIs.” Current pid-rs calls these sensitivity
   diagnostics, not calibrated confidence intervals
   (`crates/pid-core/src/bootstrap.rs:5-25` and `KNOWN_LIMITATIONS.md:503-509`).

The note itself correctly recognizes several deep limits: slow-drift blind spots, common-majority
inversion, latency/sample-size tension, and that $I_{\min}$ is not a validation fallback for
$I^{\mathrm{sx}}$ (`docs/galadriels-mirror.md:420-434`). Those negative findings should be retained
after the stale API claims are corrected.

### Permanent no-authority invariant

Haldir's frozen authority model says that advisory evidence cannot grant or widen authority and that
a failed or missing conjunct has no fallback
(`release/0.9.0/authority-model.json:26-36` and `:62-78`). PID integration must preserve this rule
permanently.

Let $A_0(s,a)$ be Haldir's authority predicate for state $s$ and action $a$ before PID evidence.
Let $A_{\mathrm{PID}}(s,a,e)$ be any future predicate that also reads PID evidence $e$. The required
non-expansion property is

$$
\forall s,a,e:\quad A_{\mathrm{PID}}(s,a,e)\Longrightarrow A_0(s,a).
$$

Equivalently, the set of actions authorized after adding PID is a subset of the set authorized
without it. The allowed composition is a predeclared restriction such as
$A_{\mathrm{PID}}=A_0\wedge R(e)$. The forbidden composition is any rule of the form
$A_0\vee G(e)$, any override of a failed conjunct, or any conversion from a score or atom to a plant
command.

This remains true even if future PID estimators become formally verified and statistically
calibrated. Verification of a statistic does not confer authority.

### Realistic Haldir regime

PID may enter Haldir only as replayable advisory evidence or as a predeclared restriction that
cannot create an `ALLOW`. Unavailable, failed, or unresolved PID must remain an explicit state. It
must not become zero, nominal, or permission. Runtime command selection, effector routing, and safe
action selection remain outside pid-rs.

## Crebain

### What is implemented

The current-head refresh from `448c9c43c15b0081c879037aa62b6a9f1bc4a341` to
`f1f4c050a1aa6f703b1b25699c232f4305bfb001` changed dependency, security, baseline, and CI
metadata but no PID/SxPID, Galadriel scientific-contract, sensor-fusion, or authority-path source.
The full source/component validation passed in a detached clean worktree. This strengthens the
currency of the source reading; it does not change the integration determination.

Crebain has no direct pid-rs dependency in its Rust manifests. It implements an optional,
off-by-default Galadriel evidence producer. The producer requires both the `ncp` build feature and
the exact runtime opt-in `CREBAIN_GALADRIEL_ENABLE=1`
(`docs/GALADRIEL_PRODUCER.md:1-24`). It publishes bounded evidence on two named routes. A successful
local `put` does not prove receiver delivery, decoding, acceptance, or action
(`docs/GALADRIEL_PRODUCER.md:239-243`).

The strongest comparable field is `ConsistencyProjection`. It binds a common frame, context, and
frozen prior identifier (`src-tauri/src/pid_observation.rs:57-76`). The base `PidObservation`
contains track/time/sequence, modality, NIS, optional innovation/covariance, and the optional
projection (`:180-212`). This is good producer provenance. It is not a complete PID adapter.

The envelope does not bind:

- a fixed target and ordered source tuple;
- a window/horizon and row unit;
- IID, block, color, stationarity, drift, or selection assumptions;
- continuous, categorical, or mixed population support;
- a fitted transform/train-evaluation split receipt;
- a PID measure, method-catalog identity, estimator configuration, or units;
- signed atom meaning and abstention status; or
- a calibrated uncertainty and multiplicity policy.

The producer also does not execute registry transform chains. A projection is emitted only for an
already matching frame with an empty transform chain
(`docs/GALADRIEL_PRODUCER.md:138-144`). Registry transform/calibration/projection references are not
loaded or verified (`SECURITY.md:101`).

### Missing integration

Crebain's own documentation requires a live Galadriel receiver, tap/monitor/cross-route assembler,
registry agreement, gap and heartbeat handling, and receiver-side campaigns before a deployment
claim (`docs/GALADRIEL_PRODUCER.md:245-264`). None was found here. A JSONL parser or NIS smoke test is
not end-to-end PID evidence (`SECURITY.md:100`).

Required next interface:

1. Preserve the raw producer envelope unchanged.
2. Build a separate receiver/window receipt that lists included, excluded, late, duplicate, and
   missing sequence identities.
3. Bind one target, ordered sources, common frame/context, and fixed horizon.
4. Attach the complete common compatibility contract from this report.
5. Produce pid-rs run-log and software-identity receipts with explicit terminal statuses.
6. Test loss, reorder, restart, saturation, drift, target rotation, and coherent-majority cases.
7. Keep producer, observer, Haldir, command, and plant credentials in separate trust domains.

Crebain's current trust-domain table already assigns Galadriel advisory observation only and no
command/final-route capability (`docs/SYSTEM_CONTEXT.md:115-138`). Preserve that boundary.

### Realistic Crebain regime

The current realistic claim is producer qualification, not PID qualification. A controlled campaign
may show bounded publication, transport, receiver acceptance, sequence-gap accounting, and common
frame/context preservation. A PID claim begins only after a separate window receipt binds one target,
ordered sources, one row law, one support and transform contract, and one exact pid-rs route. An
offline categorical or independently frozen quantized analysis may then be feasible. Continuous
ISX still needs its own support, geometry, sampling, and calibration evidence. Until that adapter and
evidence exist, Crebain provides candidate inputs only.

## Cross-ecosystem negative test corpus

The following fixtures must be permanent. A qualification suite should test both the expected
numerical relation and the required terminal status.

| Fixture | Required observation | Required system behavior |
|---|---|---|
| Fair XOR/parity | Pairwise MI is zero; joint information is positive | Galadriel pairwise verdict must not be described as synergy-capable. A matching categorical PID route may report atoms separately. |
| Coherent Gaussian majority plus independent honest channel | Majority edges are positive; honest-to-majority edges are zero | Report agreement structure, not “honest fault” or “attack source.” No authority change. |
| Target rotation with $Z=(X,Y)$ | Total MI changes from $2\log 2$ to $\log 2$ | Reject cross-row atom comparison as one fixed PID decomposition. |
| Same-row target-adaptive projection of independent high-dimensional noise | Training-row association can be maximal while test-law MI is zero | Mark descriptive/exploratory; held-out qualification must fail. |
| SAFE JSON without `support` | Python structural verifier can accept; continuous Rust preflight abstains | Preserve `support_contract_unspecified`; never coerce it to zero. |
| Exact ties plus generic jitter | Numeric KSG route can become runnable after noise | Report a changed/noised estimand or abstain. Never call this repair of the original estimand. |
| Common-mode fault | Several wrong channels remain mutually coherent | Do not infer truth from the largest clique. |
| Slow drift below window resolution | Marginals and dependence may remain inside the screen band | Record non-detection. Do not infer absence of attack or fault. |
| Missing/failed PID record | No scalar exists | Retain unavailable/failed state; no nominal default and no authority expansion. |
| Invalid surrogate p-values | Restricted shifts lack exact randomization validity | Do not pass them to BH/BY as exact p-values. |

## Qualification sequence

Do not use one scalar “confidence” score to combine incompatible evidence layers. Complete and
report each layer separately.

1. **Schema conformance.** Cross-language golden messages and rejection fixtures.
2. **Semantic conformance.** Exact source/target/event/atom mapping against a small categorical
   oracle.
3. **Executable refinement.** Prove or exhaustively check histogram, event, lattice, and atom
   correspondence for bounded domains; retain failures and counterexamples.
4. **Numerical certification.** Use a directed-rounding or ball-arithmetic reference for categorical
   log terms and atom signs near zero.
5. **Sampling validation.** Evaluate the exact row process, support regime, transform split, drift,
   and uncertainty procedure.
6. **Selection and sequential validation.** Control the complete predeclared family and repeated
   window policy. A one-window interval is not an alert guarantee.
7. **Independent challenge.** Freeze commits and thresholds, run hidden exact/adversarial cases, and
   publish every case after scoring.
8. **Consumer replay.** Rebuild the exact adapter and replay run logs on pinned consumer commits.
9. **Authority non-expansion.** Machine-check that no PID status can create or widen an allowed
   action. Run mutation tests that try to bypass every failed authority conjunct.

The categorical offline route can advance through all nine layers. Continuous two-source PID first
needs estimator-specific consistency/calibration evidence in the declared consumer regime. A full
continuous three-source or mixed-dimensional authority claim remains outside the release path.

## Evidence ledger

All paths below are relative to the named repository root.

### pid-rs

- `AGENTS.md`
- `README.md:550-574`
- `KNOWN_LIMITATIONS.md:159-186`, `:470-515`
- `crates/pid-core/src/bootstrap.rs:1-35`, `:299-345`
- `crates/pid-core/src/pipeline.rs:1-68`, `:3703`, `:3732`
- `crates/pid-core/src/preprocess.rs:1376-1386`
- `ecosystem-capabilities.json`
- `ECOSYSTEM_CAPABILITIES.md`
- `method-catalog.json` entries `multiple-testing.bh-by`,
  `resampling.moving-block-bootstrap`, and `unsupported.generic-knn-bootstrap-ci`

### Prisoma

- `.gitmodules`
- `AGENTS.md:8-28`, `:107-112`
- `protocols/holdout_registry_v1.json:11`
- `crates/pid-sim/src/offline_harness.rs:129-182`, `:369-384`, `:1291-1328`,
  `:3937-3998`, `:4276-4314`
- `crates/pid-sim/src/power.rs:1383`
- `experiments/safe_adapter/contract.py:1-14`, `:147-211`
- `experiments/safe_adapter/convert.py:376-395`
- `experiments/safe_adapter/verify.py:50-135`

### Galadriel

- `AGENTS.md:117-173`
- `Cargo.toml:63-70`
- `crates/galadriel-pid/src/lib.rs:7-60`
- `crates/galadriel-pid/src/engine.rs:1272-1527`, `:1582-1640`, `:1820-1905`,
  `:3710-3745`

### Haldir

- `docs/galadriels-mirror.md:204-219`, `:255-274`, `:348-367`, `:420-434`
- `release/0.9.0/authority-model.json:26-36`, `:47-78`

### Crebain

- `AGENTS.md:84-100`, `:128-162`
- `src-tauri/src/pid_observation.rs:45-76`, `:180-212`
- `docs/GALADRIEL_PRODUCER.md:1-24`, `:120-169`, `:239-267`
- `docs/SYSTEM_CONTEXT.md:13-20`, `:115-138`
- `SECURITY.md:100-103`

## Final decision

pid-rs addresses part of the ecosystem need. It supplies a strong categorical implementation,
restricted continuous research estimators, typed failures, provenance, resource controls, and
several validation layers. It does not validate the consumer's target, rows, support, preprocessing,
selection, repeated alerts, or authority policy.

The immediate priorities are concrete:

1. repair the Prisoma SAFE schema and add a real held-out frozen-transform path;
2. rename Galadriel's operational rule accurately and retain the XOR, target-rotation, and coherent
   majority counterexamples;
3. correct stale Haldir API claims and encode permanent authority non-expansion;
4. implement the Crebain receiver/window/scientific-contract layer before any PID claim; and
5. qualify exact pinned consumer routes, not pid-rs in isolation.

Until those steps are complete, all four consumer uses remain advisory, descriptive, experimental,
or blocked as stated above. No PID result may authorize an action.
