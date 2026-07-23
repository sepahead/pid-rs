# Mathematical problem-solving workflow for pid-rs

## Status and scope

This note has two parts. The first part records observations from external sources. The second part
defines a protocol for pid-rs. A source observation is not a pid-rs result.

This note does not validate the mathematical claims in the external sources. It also does not claim
that the source workflow guarantees a correct proof. The workflow is useful because it makes the
claim, search, failure, and audit steps explicit.

This note is project-defined process guidance. It has no software implementation or defining
method paper. It adds no PID method, estimator, theorem, benchmark result, or validation.

## Source observations

### X thread

The thread author reports six solutions to open Erdős problems in five days. The thread does not, by
itself, verify those solutions. It describes this repeated loop:

```text
attempt -> failure -> diagnosis -> new approach -> proof draft -> adversarial audit -> revision
```

The author reports runs of about 6 to 32 hours for individual problems. The author also gives these
search rules:

- Restate the exact problem.
- State what a complete proof or disproof must show.
- List weaker results that do not solve the problem.
- List traps and edge cases.
- Start several independent approaches.
- Keep incompatible approaches active.
- Search for counterexamples to proposed lemmas.
- Block a route that stops at an unproved statement of comparable strength.
- Challenge each candidate argument before acceptance.

These observations come from the five linked posts:

- [Thread introduction](https://x.com/Qiaoqiao2001/status/2080003441821163958)
- [Exact problem and audit requirements](https://x.com/Qiaoqiao2001/status/2080003451270885851)
- [Independent routes and blocker rules](https://x.com/Qiaoqiao2001/status/2080003454165295403)
- [Long-run work pattern](https://x.com/Qiaoqiao2001/status/2080003459248755141)
- [Research loop](https://x.com/Qiaoqiao2001/status/2080003461517549887)

### Cycle Double Cover prompt

The [Cycle Double Cover prompt](https://cdn.openai.com/pdf/04d1d1e4-bc75-476a-97cf-49055cd98d31/cdc_prompt.pdf)
starts with exact definitions. It fixes the graph class, the meaning of a cycle, edge multiplicity,
disconnected graphs, and the empty graph. It then states the one result that counts as complete.

The prompt also lists results that do not count. Examples include proofs for special graph classes,
finite computation, a cover with the wrong edge multiplicity, and a reduction to another unproved
claim. It asks for independent approach families. It delays the sharing of ideas between routes
until each route has clear strengths and gaps. It requires concrete lemmas, constructions,
equations, or counterexamples. It also gives a problem-specific audit list.

Project interpretation: this structure separates three questions:

1. What is the exact claim?
2. What work can help the search but cannot complete the claim?
3. What checks can falsify a candidate proof?

### Erdős repository

The source tree was inspected at immutable commit
[`f2ae0edb45cbdb257e135d51ef855f64caeb348b`](https://github.com/ShouqiaoW/erdos/commit/f2ae0edb45cbdb257e135d51ef855f64caeb348b).
At that commit, each of the six problem directories contains a problem-specific prompt and a paper.
The tree also contains Lean projects for problems 486, 788, and 1038. It contains Python numerical
verifiers for problems 390, 536, and 1038.

The immutable prompt files are available for
[1002](https://github.com/ShouqiaoW/erdos/blob/f2ae0edb45cbdb257e135d51ef855f64caeb348b/1002/prompt.md),
[1038](https://github.com/ShouqiaoW/erdos/blob/f2ae0edb45cbdb257e135d51ef855f64caeb348b/1038/prompt.md),
[390](https://github.com/ShouqiaoW/erdos/blob/f2ae0edb45cbdb257e135d51ef855f64caeb348b/390/prompt.md),
[486](https://github.com/ShouqiaoW/erdos/blob/f2ae0edb45cbdb257e135d51ef855f64caeb348b/486/prompt.md),
[536](https://github.com/ShouqiaoW/erdos/blob/f2ae0edb45cbdb257e135d51ef855f64caeb348b/536/prompt.md), and
[788](https://github.com/ShouqiaoW/erdos/blob/f2ae0edb45cbdb257e135d51ef855f64caeb348b/788/prompt.md).
The prompts state the quantifier order and required target strength explicitly. They list
non-solutions and problem-specific failure modes. Examples include:

- an exact asymptotic limit instead of an order bound;
- one fixed infinite witness instead of a different finite witness at each scale;
- a full-sequence limit instead of a selected subsequence;
- exact extrema and sharpness instead of numerical candidates;
- strict control of limit interchange, tightness, and mass escape;
- preservation of integer, graph, or measure structure during a reduction.

Project interpretation: problem 1038 shows one certificate pattern. Its
[numerical verifier](https://github.com/ShouqiaoW/erdos/blob/f2ae0edb45cbdb257e135d51ef855f64caeb348b/1038/numerical_verifier.py)
is designed to use a double-precision scan for initial brackets. Its higher-precision and Arb
interval checks are designed to certify signs. The
[Lean project](https://github.com/ShouqiaoW/erdos/tree/f2ae0edb45cbdb257e135d51ef855f64caeb348b/1038/lean)
contains rational and interval data for finite kernel checks. This review did not run the verifier
or build the project. The repository also has immutable
[486](https://github.com/ShouqiaoW/erdos/tree/f2ae0edb45cbdb257e135d51ef855f64caeb348b/486/lean)
and
[788](https://github.com/ShouqiaoW/erdos/tree/f2ae0edb45cbdb257e135d51ef855f64caeb348b/788/lean)
Lean trees. It has numerical verifiers for
[390](https://github.com/ShouqiaoW/erdos/blob/f2ae0edb45cbdb257e135d51ef855f64caeb348b/390/numerical_verifier.py)
and
[536](https://github.com/ShouqiaoW/erdos/blob/f2ae0edb45cbdb257e135d51ef855f64caeb348b/536/numerical_verifier.py).

Project interpretation: no complete chronological failure log was found in the inspected commit.
The prompts request a route registry and blocker policy, but this inspection did not find a full
transcript. This difference matters when pid-rs records its own process.

### Unavailable source

The linked
[ChatGPT share](https://chatgpt.com/share/6a5fdc7a-d6f8-83e8-bbea-8deb42cfed56)
could not be retrieved on 2026-07-23. It showed only an access shell. It is not evidence for any
statement in this note.

## pid-rs protocol

The rest of this note defines a repository protocol. It is an adaptation, not a source claim.

### 1. Write an exact-claim packet

Create one packet before work starts. Give the packet a stable claim ID. Include these fields:

| Field | Required content |
|---|---|
| Claim | One mathematical or statistical statement |
| Objects | Exact domains, alphabets, measures, lattices, and sample spaces |
| Quantifiers | Their full order, including every uniformity requirement |
| Assumptions | Support, dependence, moments, stationarity, sample size, and numerical model |
| Units | Natural logarithms and nats, unless the claim states another unit |
| Conclusion | Exact equality, inequality, limit, coverage, error rate, or abstention rule |
| Non-solutions | Weaker statements that do not complete the claim |
| Falsifiers | Boundary cases and counterexamples that can refute the claim |
| Evidence class | Mathematical proof, machine-checked proof, certified computation, test, or holdout result |
| Completion check | A mechanical or human check that can close the claim |

Do not overwrite a claim packet after you inspect a result. To correct or change it, create a new
revision and retain the old revision.

### 2. Build an obligation graph

Split the claim into named obligations. Each edge must state why one obligation implies its
destination obligation. Use separate nodes for these classes:

- definition and semantics;
- mathematical reduction;
- finite algebra;
- analytic inequality or limit;
- numerical certificate;
- estimator behavior;
- software conformance;
- statistical validation;
- downstream acceptance.

If an edge depends on an unproved lemma, create a separate obligation node. Mark it as open until
evidence closes it.

### 3. Keep an independent approach registry

Use one row for each mathematical idea. Do not use one row for each worker or prompt.

| Field | Meaning |
|---|---|
| Approach ID | Stable identifier |
| Family | Main mathematical mechanism |
| Independent inputs | Ideas not copied from another route |
| Current obligation | The exact node under study |
| Best result | Strongest proved statement |
| Counterexample search | Cases that were tested |
| Missing lemma | Exact open step |
| State | Proposed, active, blocked, falsified, merged, or complete |
| Reopen condition | New fact that can justify more work |
| Artifact links | Notes, code, proof files, fixtures, and logs |

For PID work, start with different families when they apply. Useful families include Möbius and
lattice algebra, measure-theoretic analysis, concentration inequalities, information geometry,
optimization, exact finite enumeration, and certified interval analysis.

Do not give every route the current preferred answer. First, let each route state its own
assumptions and failure modes. Combine routes only after this step.

### 4. Retain blockers and failed routes

Record every failed route. Keep its exact statement and its failure reason. Use one of these failure
classes:

- a concrete counterexample;
- a false intermediate lemma;
- a missing assumption;
- a quantifier error;
- a reduction to a claim of comparable strength;
- a numerical certificate that does not cover the full domain;
- a machine-checked proof that checks only a weaker statement;
- a statistical design that reuses development data.

Do not delete an invalidated derivation. Mark it clearly as invalid. Add a small counterexample when
one is available. State why it falsifies the route. A route can reopen only when it has a new
mechanism or a stronger premise that the claim packet permits.

### 5. Convert computation into certificates

Use numerical work to find structure. Do not treat a plot or a floating-point match as a proof.
Use this conversion path when it applies:

```text
exploratory computation
    -> exact reduction
    -> rational or outward-rounded interval data
    -> finite certificate statement
    -> machine check
    -> independent implementation replay
```

Keep the generator, its inputs, the generated certificate, the checker, and their digests. Add
documented negative mutations. The checker must reject each mutation.

Rational probabilities do not imply rational logarithmic information values. Use a symbolic
identity or a certified interval for a proof claim. Label an uncertified high-precision value as a
reference. Do not call a decimal reference an exact entropy oracle.

### 6. Run an adversarial audit

Audit each candidate result through five review categories:

1. **Semantic review:** Does the statement preserve the estimand, object class, and quantifier order?
2. **Mathematical review:** Can a small, boundary, singular, or dependent example falsify a lemma?
3. **Formal review:** What does the proof assistant check? What remains an assumption or prose proof?
4. **Numerical review:** Can rounding, cancellation, overflow, ties, or an unstable transform change
   the result?
5. **Statistical review:** Does the design control sampling error, dependence, selection, and repeated
   testing?

An audit must try to find a counterexample, a violated premise, or a numerical failure. It must not
only restate the proof. Record the challenge, result, and revision. If the revision changes an
assumption, create a new claim-packet revision.

### 7. Use a blind holdout protocol

A proof and a holdout test answer different questions. A proof can establish a theorem under stated
assumptions. A holdout test can estimate the behavior of an estimator or implementation on a
defined benchmark distribution. Do not use one as a substitute for the other.

Call a benchmark blind only when the development and implementation roles cannot access the
holdout rows, holdout seeds, target values, or unredacted adjudication output before the frozen
analysis produces the complete first result table. Preregister every reported output. Record an
access matrix for all roles and assets. Record who holds each sealed artifact and its immutable
digest. If these conditions do not hold, call the design a controlled holdout, not a blind holdout.

Use this protocol for estimator and pipeline claims:

1. Freeze the estimand, data-generating families, parameter grid, sample sizes, metrics, tolerances,
   failure rules, and analysis code.
2. Seal the generator, seed list, and targets. Publish an independently timestamped digest before
   holdout access.
3. Define the development, implementation, execution, and adjudication roles. Record all role
   overlaps and the access matrix.
4. Separate development, calibration, and holdout data. Do not tune on the holdout data.
5. Keep the holdout rows, seeds, target values, and unredacted result output unavailable to the
   development and implementation roles until the adjudicator records the complete first result
   table.
6. Include positive controls, negative controls, boundary cases, and known failure regimes.
7. Use repeated holdout draws for sampling claims. State confidence limits and preregistered
   acceptance criteria.
8. Report every planned cell. Do not remove a cell after a poor result.
9. Report effect errors, interval coverage, abstentions, failures, and resource limits.
10. Apply the stated multiplicity control when the decision uses many cells or hypotheses.
11. Record the first holdout result before a revision. A revision needs a new holdout version.
12. Publish the generator, manifest digest, adjudicator, and full result table after the blind phase.

The benchmark must define its scope. Synthetic Gaussian performance does not prove performance for
mixed, singular, quantized, or dependent laws. A fixed benchmark does not prove a general theorem.

#### Minimum blind-benchmark commitment

The pre-access commitment must contain enough information to detect a change after result access.
Record these fields:

| Field | Required content |
|---|---|
| Benchmark ID | Stable versioned identifier |
| Claim IDs | Exact claims that the benchmark can accept or reject |
| Analysis-plan digest | Digest of the metrics, tolerances, confidence limits, multiplicity rule, and acceptance rule |
| Code identity | Immutable source identity and environment or package-lock identity |
| Generator identity | Generator digest, parameter-grid digest, and sampling-law version |
| Sealed inputs | Digest of the seed list, target bundle, or encrypted holdout package |
| Role separation | People or systems that develop, implement, execute, and adjudicate, including all role overlaps |
| Access matrix | Permitted access for each role to code, rows, seeds, targets, keys, and result output |
| Digest custody | Party that holds each sealed artifact and its immutable digest |
| Access rule | Event that permits target access and the party that records that event |
| Independent time evidence | Third-party timestamp or an independent adjudicator record |
| Failure rule | Treatment of crashes, non-finite values, abstentions, missing cells, and resource exhaustion |
| Result identity | Digest of the complete first result table before any revision |
| Deviations | Every difference from the frozen plan |

A local Git commit time alone is not independent time evidence. Do not store a secret seed, target,
decryption key, or credential in the repository. The adjudicator must retain failed cells and must
run the frozen analysis without manual result-dependent changes. If a security constraint prevents
public release of a sealed input, publish its digest and state who controls access.

This protocol reduces result-dependent tuning and selective reporting. It does not make a
benchmark distribution representative, prove that an analytic target is correct, or replace a
theorem.

### 8. Maintain a claim-to-evidence matrix

Use the matrix to prevent evidence substitution.

| Claim class | Evidence that can support it | Evidence that does not complete it |
|---|---|---|
| PID definition and provenance | Defining paper, exact repository definition, and provenance marker | Similar name or similar output |
| Möbius reconstruction identity | Symbolic derivation and machine-checked finite algebra | Random numerical examples |
| Population functional theorem | Proof with explicit assumptions and counterexample audit | Passing implementation tests |
| Finite-alphabet consistency | Probability proof, stated mode of convergence, and formalized subclaims | One Monte Carlo curve |
| Numerical reference value | Symbolic value, rigorous interval, or high-precision value with error limit | Default floating-point agreement |
| Rust implementation conformance | Independent oracle, mutation test, feature-path parity, and boundary tests | A paper citation |
| Scoped estimator calibration | Declared data-generating family, repeated preregistered holdout draws, confidence limits, and acceptance criteria | Reused development fixtures or one unqualified draw |
| Dependence-aware inference | Valid dependence assumptions plus block or permutation design checks | An independent-row test |
| Downstream suitability | Consumer-specific input contract and acceptance fixture | A generic PID example |
| Limitation or impossibility | Explicit counterexample or proved obstruction | Failure to find a proof |

Each new or revised scientific claim must identify its applicable claim class or classes, evidence,
and scope. A result can use more than one claim class. For example, a correct functional identity
does not establish estimator calibration.

## Application to shared-exclusions PID

The primary theoretical target in this project is the shared-exclusions PID line. Keep
paper-defined quantities separate from project-defined diagnostics, wrappers, and workflows.
[`method-catalog.json`](method-catalog.json) and its generated [`METHODS.md`](METHODS.md) rendering
are the authorities for method origin, code availability, and validation status.

### Exact claim packet for a new PID theorem

The packet must define:

- the source collection and target;
- the source antichains and lattice order;
- the pointwise informative, misinformative, and net terms;
- the averaging law;
- the logarithm base and units;
- the population support and any minimum-mass condition;
- the row dependence model;
- the estimator and all fitted preprocessing;
- the requested conclusion and its convergence mode;
- the status of negative atoms;
- all cases where the method must abstain.

If the theorem concerns a plug-in estimator, distinguish the population functional from the
empirical law and the implementation. If it concerns continuous data, state the support model. Do
not infer full-dimensional absolute continuity from unique observed rows.

### Independent PID approach families

For each new theorem, use at least three applicable audit families. If fewer apply, record why.

- **Combinatorial:** antichain order, Möbius inversion, atom reconstruction, and source symmetry.
- **Analytic:** continuity, support boundaries, limiting arguments, and perturbation bounds.
- **Probabilistic:** concentration, dependence colorings, mixing assumptions, and resampling.
- **Computational:** exhaustive small alphabets, exact count tables, and counterexample search.
- **Formal:** Lean or SMT statements for finite algebra and deterministic inequalities.
- **Statistical:** coverage, power, null calibration, selection effects, and blind holdout behavior.

These families can support each other. They are not interchangeable. A formal lattice identity does
not prove a concentration theorem. A concentration theorem does not prove that a continuous kNN
estimator targets the intended functional.

### Required counterexample search

For each new PID claim, test the relevant cases:

- independent sources and target;
- copied sources;
- XOR and other synergy gates;
- duplicate or deterministic sources;
- zero-probability and near-zero-probability cells;
- support deletion and support creation;
- singular and mixed-dimensional continuous laws;
- exact ties and quantized observations;
- row dependence and a false dependence partition;
- cancellation in reconstructed atoms;
- source permutation and target relabeling;
- serial and parallel implementation paths.

Keep a counterexample when it breaks a proposed unconditional claim. State the corrected assumption
next to the retained example.

### Formal and software evidence

Formalize the exact theorem statement before large certificate generation. Record the proof kernel,
toolchain, imported axioms, and unformalized steps. For finite domains, use exact enumeration or
certified intervals when possible. Then replay the same cases through the Rust API.

Use mutation tests for proof and evidence scripts. Add documented negative mutations. The check
must reject each mutation. Run every API, feature, and build mode named by the claim.

### Statistical and ecosystem evidence

Define separate benchmark strata for categorical SxPID, fitted quantized SxPID, continuous KSG
terms, composed PID atoms, and uncertainty procedures. Each stratum needs its own analytic target or
certified numerical reference. If a stratum has neither, label it diagnostic. Each stratum also
needs its own tolerance and abstention policy.

For Prisoma, Haldir, Galadriel, and Crebain, record a consumer contract. The contract must identify
the required estimand, data support, dependence model, scale, uncertainty output, resource limit,
and failure behavior. Do not claim consumer readiness until a versioned acceptance suite checks
every contract field. One fixture supports only its declared case. Do not infer consumer readiness
from general unit tests.

## Acceptance rule

Record an evidence label and a separate claim disposition. Use one of these evidence labels:

- theorem proved under stated assumptions;
- machine-checked finite obligation;
- certified numerical bound;
- preregistered empirical result;
- counterexample;
- diagnostic observation; or
- no accepted evidence.

Use one of these dispositions: proposed, active, blocked, falsified, or complete. A result is
complete only when all applicable obligations are closed. A closed finite or machine-checked
sub-obligation does not close its parent claim. A counterexample can complete a disproof but cannot
complete the original proof claim.

Do not change an evidence label or disposition without new evidence. Link all artifacts with the
claim ID. This record helps reviewers find gaps. It does not prove the claim.
