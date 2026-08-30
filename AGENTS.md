# AGENTS.md

Guidance for AI coding agents (and humans) working in **pid-rs**. Tool-agnostic; Claude Code also
reads `CLAUDE.md`, which imports this file.

This file is the operational guide (policy, commands, conventions, code map). For the *scientific*
picture — what PID is, which estimator does what, the references, and the caveats — read
[`README.md`](README.md) first; per-crate docs live in each `crates/*/README.md`.

## Contents

- [Commit & attribution policy (READ FIRST)](#commit--attribution-policy-read-first)
- [What this project is](#what-this-project-is)
- [Method provenance and novelty claims](#method-provenance-and-novelty-claims)
- [Scientific-object and evidence firewall (MANDATORY)](#scientific-object-and-evidence-firewall-mandatory)
- [Workspace layout](#workspace-layout)
- [Where things live in `pid-core`](#where-things-live-in-pid-core)
- [Build / test / lint (mirror CI)](#build--test--lint-mirror-ci)
- [Conventions to preserve](#conventions-to-preserve)
- [Before you push](#before-you-push)

## Commit & attribution policy (READ FIRST)

- **Do not add AI/agent attribution to commits or pull requests.** Never append a
  `Co-Authored-By:` trailer that names Claude, an AI, or an agent, and never add
  "Generated with Claude Code" / "Co-authored with …" / any agent advertising to commit messages
  or PR descriptions. Commits are authored **solely by the human contributor**.
- **Do not sign commits or tags.** This repository sets `commit.gpgsign=false` and
  `tag.gpgsign=false` locally; leave them unsigned.
- This is enforced by `.claude/settings.json` (`attribution.commit` and `attribution.pr` are empty
  strings). Do not re-introduce attribution there or in any commit you author.

## What this project is

A safe-Rust workspace for **partial information decomposition** (the shared-exclusions `I^sx_∩`
measure) and the continuous **k-nearest-neighbour** estimators it builds on (KSG mutual
information), plus discrete `I_min` PID, Shannon invariants, geometry diagnostics, preprocessing/PLS,
dependence-aware uncertainty quantification (block bootstrap, permutation nulls, and
Benjamini–Hochberg/Yekutieli FDR adjustment), reproducible run-logs, typed package-safe software
identity, and Python bindings.

## Method provenance and novelty claims

**“New in pid-rs” means implementation, API, composition, diagnostic, or engineering work new to
this repository; it is not a claim of scientific novelty.** [`method-catalog.json`](method-catalog.json)
is the machine-readable authority and [`METHODS.md`](METHODS.md) is its exhaustive human rendering.
Use the catalog's distinctions consistently:

- **paper-defined** for a quantity or estimator defined by a cited publication;
- **paper-derived** for a repository composition of published quantities or algorithms;
- **project-defined** for a repository diagnostic, contract, report, or workflow;
- **external reference code** for a separately maintained comparison implementation; and
- **no implementation** for an explicitly unsupported request.

Do not infer paper support from the existence of code, infer implementation from a paper citation,
or call a bounded fixture comparison a general validation result. Fitted quantized SxPID is a
project composition for a quantized estimand; PID2 composes separately estimated published terms;
its atom construction is defined in Ehrlich et al., while pid-rs report/cross-fit wrappers are
project-defined. Incomplete PID3 is an availability diagnostic; the full paper-defined
mixed-dimensional PID3 remains research-only here. Heuristics are project-defined baselines;
Lorentz KSG is a paper-derived research adaptation. Target-free `Red°`/`Vul°` are project-defined
analogues rather than the published target-conditioned `r̄`/`v̄`; resampling contracts and run
logs add engineering without a generic calibration theorem; Python exposure is a binding status,
not a method-origin status. The software-identity envelope is project-defined infrastructure with
local Rust/Python code, no defining method paper, and no scientific-novelty or attestation claim.

When a method, estimator, diagnostic, or binding changes, update the catalog entry, its source
marker/documentation, and any audience-specific summary that becomes inaccurate, then run:

```text
python3 scripts/check-method-catalog.py
```

## Scientific-object and evidence firewall (MANDATORY)

pid-rs implements and composes objects from several distinct PID research lines, including
multiple papers co-authored by Michael Wibral. Similar notation, shared authors, shared code,
citations, passing tests, or a common repository do not identify two scientific objects. Before
changing or making a claim about a method, estimator, diagnostic, proof, wrapper, or consumer,
record a compact object card containing all of the following:

- **Source:** exact defining source. For paper-defined/derived work, give the paper title and
  immutable revision (`arXiv:<id>vN` or the DOI version of record); for project-defined work, give
  the exact local specification revision and state that no defining paper is claimed. Include the
  source locator and byte hash when a claim depends on retrieved bytes.
- **Scientific object:** construction and estimand; variable domain; population-support premises;
  information units; and whether each row set defines an empirical PMF, fits/selects/preprocesses,
  evaluates/holds out, resamples, or supplies a synthetic fixture.
- **Implementation:** exact repository source/code route, public API, feature gate, method/schema
  revision, preprocessing/metric/gauge/quantizer identity, and affected downstream consumers.
- **Evidence and reviewer:** evidence class, exact artifact/blob/scope, inputs, toolchain and
  assumptions; reviewer class; and separately stated semantic, implementation, custody,
  institutional, and data independence.
- **Correspondence:** separately status each edge
  source→repository specification→formal object→executable algorithm→Rust/Python and
  finite-precision execution→scientific estimand/application. Record every open edge; evidence
  inside one object does not close an adjacent edge or the transitive chain.
- **Boundary:** explicit nonclaims, unsupported regimes, retained negative evidence, and the exact
  scope of any comparison. Unknown or unrecorded fields stay open and fail closed.

A result transfers between rows below only through a premise-explicit typed mapping theorem or an
explicitly scoped empirical comparison that names both objects. A comparison is evidence about its
declared fixture, not an equivalence theorem.

For every important scientific claim, method transfer, application recommendation, or publication
decision, add a council review with at least 50 explicitly named hostile lenses beyond the ordinary
author pass. Ask, at minimum: why PID; why this named PID functional; why this source grouping,
target, alphabet, law, and estimator; and why not MI/CMI, direct task loss, fixed-model and retrained
ablation, explicit failure utility, coverage, Bayesian or Fisher design, another PID functional, or
no PID. Deduplicate correlated arguments, preserve dissent and shared failure cuts, and treat the
lens count as a coverage checklist rather than correctness evidence.

Before an important method, design, proof, estimator, integration, or repair decision, compare at
least ten materially distinct routes. Include a no-action route and the simplest applicable non-PID
route. Evaluate the routes through the hostile council, then select the best single route or a
premise-compatible combination of the best parts. Record the selected rationale, rejected routes,
failure conditions, and evidence needed to reconsider them. Do not count cosmetic variants as
distinct routes, and do not treat enumeration or council agreement as mathematical evidence.

Scientific documents must be self-contained for a mathematically trained reader who is new to this
repository. State each equation's domain and assumptions near the equation; define symbols before
use; show the physical-to-mathematical input and output; include at least one worked example where
useful; distinguish pointwise, averaged, empirical, and population quantities; report estimator,
sampling, numerical, resource, and application bounds; and explain both legitimate uses and reasons
to prefer a simpler method. Cite primary sources for paper-defined and classical results, and mark
project-defined derivations and novelty status explicitly. Use ASD-STE100-inspired plain technical
prose for technical sections, but do not claim ASD-STE100 conformance without a separate audit.
Preserve counterexamples, false positives, unsuccessful routes, and negative results with their
scope and rejection reason; do not leave stale claims in an apparently current lane.
Keep repository prose and commit messages claim-centered and professional: describe the evidence,
correction, and remaining boundary without naming private review settings or personal evaluations.

| Object | Exact source and construction | pid-rs route and hard boundary |
|---|---|---|
| MGW categorical shared exclusions | Makkeh–Gutknecht–Wibral, `arXiv:2002.03356v5`, *Phys. Rev. E* 103, 032149: finite-categorical pointwise informative/misinformative shared exclusions and signed joint-law averages. | Stable direct categorical plug-in routes, reported in nats. Empirical rows define the plug-in PMF; this is not Ehrlich continuous shared exclusions, Schick-Poland general measure theory, or Williams–Beer `I_min`. |
| Gutknecht parthood/formal logic | Gutknecht–Wibral–Makkeh, `arXiv:2008.09535v2`, DOI version of record `10.1098/rspa.2021.0110`: parthood and formal-logic foundations for information decomposition. | A conceptual/formal source, not by itself a numerical estimator, implementation, or mapping among the other rows. Use only where the method catalog names the exact relationship. |
| Schick-Poland general construction | Schick-Poland et al., `arXiv:2106.12393v2`: proposed auxiliary-indicator/RCP/Radon–Nikodým construction for a finite source family under stated Radon/Borel premises, intended for discrete, continuous, and mixed variables. | No implementation. Pointwise existence and version-independence at null conditioning events and for target-local Radon–Nikodým representatives remain unadjudicated here; open source obligations do not prove the construction false. |
| Ehrlich continuous shared exclusions | Ehrlich et al., `arXiv:2311.06373v3`, DOI version of record `10.1103/PhysRevE.110.014115`: purely continuous, gauge-dependent analytic shared-exclusions functional and source-disjunction kNN estimator. | Default-off experimental `isx` routes, in nats, with an explicit population-support declaration and sample diagnostics. Source corrections in `audit/source-errata.json` are reviewer-derived, not author-confirmed, and bounded regression is not paper→Rust refinement. |
| KSG mutual information | Kraskov–Stögbauer–Grassberger (2004), DOI version of record `10.1103/PhysRevE.69.066138`: KSG1 mutual-information estimator. | Stable report-first Chebyshev/max-product route and experimental raw scalars, in nats. Strict marginal counts, tie rejection, and `SupportContract` are explicit implementation/policy identity. KSG evidence does not validate an SxPID functional or PID atoms. |
| PID2 / PID3 | Ehrlich `arXiv:2311.06373v3` atom construction plus separately estimated Ehrlich-redundancy and KSG-MI terms. | PID2 is experimental; its report/cross-fit/split-sample layers are project-defined. Incomplete PID3 is a project availability diagnostic; full mixed-dimensional PID3 is research-only. Algebraic reconstruction does not establish calibration, consistency, or a complete PID3. |
| Williams–Beer `I_min` | Williams–Beer, `arXiv:1004.2515v1`: finite-categorical `I_min` redundancy/PID. | Stable empirical categorical comparator, in nats. It is a different redundancy measure; never pool or relabel its atoms as MGW SxPID. |
| Project wrappers and adaptations | Repository-defined contracts at their exact method/schema revisions govern fitted quantized and same-sample routes, reports, cross-fit, hyperbolic/hierarchy/pipeline/UQ surfaces, run logs, and software identity; cited component algorithms retain their own sources. | Treat as project-defined or paper-derived exactly as the method catalog says. Preserve fit/evaluation roles and estimand-changing transforms. A wrapper, binding, hash, or run log adds no scientific theorem or application validity. |

Evidence classes are non-interchangeable labels and dimensions, not an assurance ladder:

| Evidence class | What it establishes—and does not establish |
|---|---|
| Inventory | Exact objects were enumerated; it is not line, mathematical, or human review. |
| Model review | Advisory output from an agent/model/system, not human or institutional review. Model agreement alone is correlated; infer no independence dimension without exact recorded scope. |
| Line review | A disposition bound to exact lines/blobs and stated scope; it says nothing about unreviewed objects or scientific validity unless explicitly included. |
| Human review | A named human disposition bound to exact objects and scope. State every independence dimension; a name or count alone is not independence or proof. |
| Formal proof | A named theorem/model checked by the pinned formal toolchain. It does not automatically prove source correspondence, executable refinement, binary64 behavior, or application validity. |
| Execution evidence | A test, checker, fixture, mutation suite, or receipt bounded to exact inputs, environment, and assumptions; it is not a universal theorem or generic validation result. |
| Tag/release fact | Git or release identity/history only; it is not review completion, authenticity, scientific validity, or a fact about later `main`. |

A reviewer-derived source observation or candidate correction remains reviewer-derived until an
exact author- or publisher-confirmation artifact is recorded; neither a named reviewer nor repeated
agreement upgrades it. Treat every claim from another agent, model, or system as a hypothesis.
Independently read the exact primary-source/repository bytes, rerun the applicable checker and
hostile self-test in normal and optimized Python where provided, and inspect the outputs. Apply the
same rerun-and-inspect standard to your own claims; never inherit a reported green result.

### AI-assisted candidate/judge isolation and research-integrity controls (MANDATORY)

These controls apply prospectively to every research/scientific proof, numerical certificate,
estimator or algorithm implementation, benchmark, or model attempt opened after this policy
revision when it can change a scientific or public claim. They do not retroactively upgrade an
existing claim, proof, certificate, or review. Deterministic execution of an already-fixed
operational custody contract follows that contract's own pre-bound checker and receives no
scientific credit; do not relabel routine receipt generation as a scientific candidate attempt.

An output produced before its attempt is registered and its packet is sealed permanently loses
preregistered, selection-unbiased, and strict-confirmatory credit. Preserve it as retrospective
`exploratory` evidence; do not erase it. Naming it after selection does not repair the boundary, and
rerunning against the same exposed data or judge does not cure adaptive selection. A deterministic
formal or exact artifact may later receive only its separately checked predicate; empirical
promotion needs candidate-inaccessible confirmation or a declared selection-aware design.

- Before candidate access, seal a versioned task packet containing the exact claim or theorem,
  definitions, imports, permitted axioms and trust routes, source/toolchain identities, candidate
  write scope, acceptance predicate, resource budget, stopping rule, and selection rule. Publish
  only a permitted projection or commitment when the packet contains protected material. Any
  semantic or acceptance change starts a new revision; it does not repair the scored attempt.
- Restrict candidate writes to the declared payload. A fresh-checkout, pre-bound judge outside the
  candidate's authority must reject changes to the statement, definitions, imports, axiom policy,
  verifier, tests, fixtures, reference values, or trust surface, including undeclared `sorryAx`, new
  axioms/imports, unsafe/partial execution, code generation or external execution outside the
  packet, network/secret access outside the frozen allowlist, and toolchain drift. An unavailable,
  crashed, timed-out, or incomplete judge is not a pass.
- Give every attempt a durable minimum ledger entry: task revision, purpose/route, candidate and
  judge identity, terminal status, selection decision, reopen condition, and output identity or
  explicit omission. Retain full permitted inputs, decisive output/diff, verifier receipt, resource
  use, and known model/system/tool/context metadata for every promoted, adjudicating, or
  load-bearing failed/withdrawn attempt. Any valid unselected attempt that enters a best-of-$N$ or
  other selection decision is load-bearing: retain its decisive permitted output and verifier
  receipt. If that record is unavailable, mark the selection route incomplete and grant it no
  strict-selection credit. Record bounded omissions/redactions rather than claiming complete
  transcripts or deterministic hosted-model replay. Append corrections; never erase or relabel
  failures and unselected valid candidates.
- Model proposer/judge output remains advisory. A different prompt, session, role, model, vendor,
  file, or implementation is not by itself semantic, data, implementation, epistemic,
  institutional, or custody independence. Record the existing independence vector and require a
  separately scoped human disposition whenever human scientific review is claimed.
- A kernel proof establishes only the exact formal statement under its inventoried imports, axioms,
  kernel, and trust surface. A numerical certificate establishes only its declared finite
  arithmetic predicate and covered domain. Neither closes paper-to-definition correspondence,
  executable/binary64 refinement, estimator calibration or consistency, PID-functional identity,
  or an application edge. Apply these boundaries separately to every PID, estimator, evaluator,
  objective, law/support class, and downstream consumer.
- Candidate/judge write isolation is tamper resistance, not holdout isolation or scientific
  independence. Repeated judge feedback makes that route development evidence. Empirical packets
  must separate development, selection, and candidate-inaccessible confirmation routes unless a
  declared sequentially valid design permits reuse. A frozen campaign packet may govern multiple
  child attempts while its semantics, judge, budget, stopping rule, and selection rule remain
  unchanged; every child still gets a durable attempt ID, and any frozen-field change starts a new
  packet revision.

Research durability is part of the method, not housekeeping:

- No unique accepted or load-bearing research object may exist only in `/tmp`, a disposable
  worktree, an unpushed branch, a terminal transcript, or an agent conversation. Scratch state has
  zero durable-evidence credit until its permitted bytes or a content-addressed manifest are in a
  commit reachable from the remote `main` branch, or protected bytes are in an approved restricted
  durable store with a safe public commitment and stated access/retention boundary.
- Commit and push coherent milestones early: frozen task packet; candidate or counterexample;
  judge/verifier result; disposition; and publication artifact. Keep those commits small enough to
  review, but never split a self-consistency set such as Markdown/TeX/PDF/rendering receipt or a
  schema/checker/hostile-vector change. Verify the pushed `main` OID with a read-only remote query.
- A pushed Git commit is the project's operational recovery anchor, not permanent scholarly
  preservation. Publication-grade objects must additionally record exact paths, byte sizes and
  digests, provenance and nonclaims, and a release or archival deposit when the claim packet
  requires one. If raw data, prompts, or provider artifacts cannot be committed, retain them in an
  approved durable store and commit a bounded manifest/locator; record any omission, access
  restriction, or retention limit explicitly.
- This policy does not itself authorize a commit, push, tag, release, archive deposit, or public
  disclosure. Obtain explicit maintainer authorization and honor branch protection and review.
  Do not publish a packet, holdout, judge feedback, failure, or candidate while publication would
  contaminate a blinded or pending attempt; use restricted durable storage and expose only a safe
  commitment/manifest until the boundary closes. A commitment without a retrievable permitted
  preimage provides binding, not recovery or reproducibility.
- Before deleting or abandoning any worktree, branch, cache, or local artifact, prove that every
  accepted, adjudicating, or selection/load-bearing artifact identified by the attempt ledger or
  manifest is either reachable from remote `main`, intentionally rejected with a ledger record, or
  bound by a verified durable external locator. A remote side branch is a backup, not completion;
  move accepted work to `main`.
- Verify publication with a read-only remote query. Record the remote URL, ref, observed OID, and
  observation time. If `main` advanced after the milestone, prove the milestone is an ancestor of
  the observed tip; never force-push merely to restore a previously expected tip.
- Use a council for every named scientific claim, method transfer/adoption, disposition, and
  publication milestone. Require independent-first written critiques before cross-member
  discussion; cover the applicable semantic, mathematical, numerical/statistical, implementation,
  transfer, adversarial, publication, and custody lenses; preserve dissent; and record shared
  dependencies. Council votes and same-system agreement are advisory, not independent evidence.
  The primary agent must read the exact sources, adjudicate every finding, and remain responsible
  for the final decision. Any council-driven change to the frozen task or judge opens a new revision.

Durable routing and validation:

- [`audit/evidence/external-model-pid-rs-deep-audit-adjudication-2026-08-12.md`](audit/evidence/external-model-pid-rs-deep-audit-adjudication-2026-08-12.md)
  preserves the advisory finding-by-finding adjudication; the mutable, unchecked work queue is
  [`audit/evidence/wibral-pid-program-active-plan-2026-08-12.md`](audit/evidence/wibral-pid-program-active-plan-2026-08-12.md).
- [`audit/source-errata.json`](audit/source-errata.json) is the versioned source-observation and
  construction-transfer firewall. Its reviewer-derived records are not author-confirmed errata.
- [`audit/evidence/assurance-registry.json`](audit/evidence/assurance-registry.json) remains the
  assurance authority. [`audit/evidence/assurance-registry-typed-view-v1.json`](audit/evidence/assurance-registry-typed-view-v1.json)
  is only a deterministic derived query view; never edit it as a competing authority or infer a
  closed five-edge chain.
- The represented-input exact PID2-synergy revision is bound to exactly six release-scope families
  whose outputs directly emit or transitively contain the revised two-source synergy: stable and
  same-sample Williams--Beer `I_min`, continuous PID2, configured heuristic PID2, hierarchy, and
  pair screening. This is an evidence partition, not a global runtime-call inventory; `exp0` also
  calls the constructor as a diagnostic. The revision does not cover PID3 or the quantization-only
  same-sample custody family, and the bounded `I_min` census cannot validate Ehrlich shared
  exclusions or another PID.
- [`METHODS_SUMMARY.md`](METHODS_SUMMARY.md) is a generated stable-first navigation view; it does
  not replace the catalog or exhaustive `METHODS.md`. [`PID_MATHEMATICAL_AUDIT_PROTOCOL.md`](PID_MATHEMATICAL_AUDIT_PROTOCOL.md)
  is a generated object-card review aid that keeps PID2, incomplete PID3, and the full research
  PID3 lattice separate. Neither derived view is an assurance authority or review disposition.
- [`audit/evidence/current-source-state-v1.json`](audit/evidence/current-source-state-v1.json) is a
  deterministic self-excluding worktree-source projection. It does not contain or claim its own
  digest or final containing commit; resolve the containing commit from Git after committing. Its
  11-entry `generated_pdfs` field is a selected byte-identity roster. It is not the exhaustive
  `output/pdf/` inventory. The separate `generated_pdf_set` subprojection covers every repository-
  visible entry under `output/pdf/`, including PDFs and adjacent TSV rendering receipts.
- `check-post-commit-source-state-v2.py` resolves that commit only after the manifest is committed.
  From a clean checkout it emits canonical deterministic identity bytes on standard output and
  validates the same bytes in a separate invocation from standard input, binding `HEAD`, its tree,
  and the tracked manifest blob. Storage and upload remain caller-owned and are not claims of the v2
  artifact. It is post-commit identity
  evidence only—not authenticity, attestation, review, CI-pass, release, formal, scientific,
  numerical, or application evidence—and must never be committed back into the source projection.

```text
python3 scripts/check-source-errata.py
python3 -O scripts/check-source-errata.py
python3 scripts/check-source-errata-self-test.py
python3 -O scripts/check-source-errata-self-test.py
python3 scripts/check-review-evidence.py
python3 -O scripts/check-review-evidence.py
python3 scripts/check-review-evidence-self-test.py
python3 -O scripts/check-review-evidence-self-test.py
python3 scripts/check-assurance-registry-typed-view-v1.py
python3 -O scripts/check-assurance-registry-typed-view-v1.py
python3 scripts/check-assurance-registry-typed-view-v1-self-test.py
python3 -O scripts/check-assurance-registry-typed-view-v1-self-test.py
python3 -S -B scripts/check-method-catalog.py
python3 -O -S -B scripts/check-method-catalog.py
python3 -S -B scripts/check-method-catalog-self-test.py
python3 -O -S -B scripts/check-method-catalog-self-test.py
python3 -S -B scripts/check-finite-convergence-document-semantics.py
python3 -O -S -B scripts/check-finite-convergence-document-semantics.py
python3 -S -B scripts/check-finite-convergence-document-semantics-self-test.py
python3 -O -S -B scripts/check-finite-convergence-document-semantics-self-test.py
python3 scripts/check-methods-summary.py
python3 -O scripts/check-methods-summary.py
python3 scripts/check-methods-summary-self-test.py
python3 -O scripts/check-methods-summary-self-test.py
python3 scripts/check-pid-mathematical-audit-protocol.py
python3 -O scripts/check-pid-mathematical-audit-protocol.py
python3 scripts/check-pid-mathematical-audit-protocol-self-test.py
python3 -O scripts/check-pid-mathematical-audit-protocol-self-test.py
# Only after every intended source and operational byte is frozen:
python3 -I -S -B scripts/check-current-source-state-v1.py --emit > audit/evidence/current-source-state-v1.json
python3 -I -S -B scripts/check-current-source-state-v1.py
python3 -O -I -S -B scripts/check-current-source-state-v1.py
python3 -I -S -B scripts/check-current-source-state-v1-self-test.py
python3 -O -I -S -B scripts/check-current-source-state-v1-self-test.py
```

The composite-v3 hosted receipt is permanently unissued: its fixed semantic language order and
increasing opaque-ID predicate conflict on the exact recovery run, and its exact-three-additions
topology cannot also refresh the self-excluding source manifest. Preserve those historical bytes
and the append-only composite-v4 process documented in
[`ksg-rev4-m1a-composite-v4-process-2026-08-15.md`](audit/evidence/ksg-rev4-m1a-composite-v4-process-2026-08-15.md).
Published C4 commit `da253576a5f76e99633fff4de5cf1118f967b90d` failed its first hosted
qualification, so R4 is permanently unissued and the v4 capture/receipt paths remain absent.
Preserve that failure; do not rewrite C4, rerun it for attempt-1 credit, or revive R4.

Published C5 commit `be862b155d710573ec95356fc1cbe9a96a2b83b9` retained the C4 failure,
applied its five bounded operational repairs, and published fresh Lean `r10`. Its attempt-1 hosted
qualification failed in the PDF portability lane, so R5 is permanently unissued. Preserve C5,
that failed attempt, the exact r10 receipt, and the immutable v5 gate bytes; do not rerun them for
attempt-1 credit, rewrite their cross-toolchain predicate in place, or revive R5.

Published C6 commit `0c3afa0ab5b264370072a18d24655df35b90574c` retained the C5 failure,
applied its bounded report/figure association repair, and published fresh Lean `r11`. Its
attempt-1 CodeQL run passed, while repository CI and the dedicated-v6 route failed because `rg`
was absent from the hosted dependency closure. R6 is permanently unissued. Preserve C6, the exact
failed observations, and finalized `r11`; do not rerun them for attempt-1 credit or revive R6.

Published C7 commit `23b69abafb4bfdaab4b2321eb6cee7be7e1cd32e` retained C6 and fresh Lean
`r12`. Its attempt-1 CodeQL run passed, while the dedicated-v7 route failed during job setup on a
39-hex upload-action ref and repository CI separately failed at the final mathematical-workflow
cross-toolchain layout comparator. R7 is permanently unissued. Preserve C7, the two distinct
hosted failure records, and finalized `r12`; do not rerun them for attempt-1 credit or revive R7.

Published C8 commit `7c80d48db415279fc4d744eadb1515797606912b` retained C7 and fresh Lean
`r13`. Its attempt-1 CodeQL run passed. Repository CI and the dedicated-v8 route both reached the
retained certified-SxPID2 checker and failed on the exact marker `certified SxPID2 claim check
failed: release-audit just dependency line exact digest changed`. The first reached marker identifies one stale binding. Read-only
sequential digest-repin analysis identified the exact five changed operational bindings, and
source reconstruction guards that difference set without establishing unique counterfactual
necessity or order. No L8 record is installed; no operator-invocation history is claimed. R8 is
permanently unissued. Preserve C8, finalized `r13`, and the exact failed hosted observations; do
not rerun them for attempt-1 credit or revive R8.

The operative append-only successor is composite-v9, documented in
[`ksg-rev4-m1a-composite-v9-boundary-2026-08-19.md`](audit/evidence/ksg-rev4-m1a-composite-v9-boundary-2026-08-19.md).
From a clean committed checkout run:

```text
just ksg-composite-v9
```

C9 and R9 are separate unsigned, human-attributed milestones. C9 must be the exact direct child of
C8. It retains the exact C8 publication family and failed hosted observations, and repins exactly
the five stale operational bindings without changing certified theorem statements,
mathematical-claim semantics, estimator results, or PDF bytes. The claim packet changes only its replay-custody
pointer prose. C9 retires the v8 workflow, publishes no new PDF, and publishes a fresh Lean `r14`
replay. R9 is permitted only after one fresh exact-C9 local closure and fresh attempt-1 CI, CodeQL,
and dedicated-v9 success for that same commit. The local observation has no attempt-number
authority: a separately typed recorder must run the fixed `just ksg-composite-v9` command from an
exact clean C9 checkout, retain bounded
output and clean endpoint observations in a
mode-0600 staging file outside the repository, and install those exact bytes only after validation.
Those endpoints use ordinary Git status plus selected metadata checks. Rejecting
`core.excludesFile` removes one ignore-routing overlay, but repository-ignored products and
uninspected Git metadata remain outside the observation and may remain side inputs; this is not a
hermetic closure.

Candidate `0a6ece9c525ad7aad061f55b3edea83554891b42`, tree
`1d5446f19d34b742feeb51429bf58a0706750757`, was not observed accepted or published on `main` as C9 in the bounded provider/history checks and
receives zero credit. The required composite run under inherited `umask 077` had
`ok 273 - refresh writer reports an injected second-replacement failure` as its last confirmed
output line; the next observed
stable diagnostic had prefix `refresh destination mode drifted: ` and path suffix
`/root/output/pdf/workflow.pdf`. No complete raw transcript or whole-run digest of that required run
was retained. A separate direct workflow-PDF self-test under `umask 022` passed 366/366 controls but
is documentary only, was not checker-replayed as a C9 qualification run, and receives zero
qualification credit. Its
145,611-byte `r14` (SHA-256
`2a882358e158ebeae06dbdf8d1cd35637d698f59ce217c1e2fbecf1d8787dfb7`) is archive-only and outside
every accepted `prior_replay_*` lineage. The mutable provider ref
`refs/heads/archive/composite-v9-rejected-workflow-pdf-umask-20260821` was observed at the candidate
commit; it is a recovery locator, not authentication, durability, or accepted-on-main C9
publication status or credit. The deterministic checker binds the recorded identifiers but does not
query provider archive, main, or workflow-run endpoints or require the sibling commit object. The
candidate had no L9, and GitHub exposed no workflow run for it on 21 August while `main` remained
exact C8. Do not
merge or cherry-pick the rejected commit or reuse/copy its `r14` or evidence. Reapplying reviewed
non-evidentiary source/contract bytes onto a fresh C8 child is permitted; byte reuse transfers no
execution, replay, qualification, or acceptance credit.
A second precommit candidate is likewise rejected with zero credit. Unsigned archive commit
`113cbad2e58a9cfa40cf43b1c0ffc260b566aa92`, tree
`ae3204d72c012dddaa5b634d9f5c4c745d5823d2`, was observed on 22 August through mutable provider
recovery ref `refs/heads/archive/composite-v9-rejected-r14-fixed-point-20260822`; the ref then pointed
to the commit, `main` remained exact C8, and GitHub exposed zero workflow runs for it. Its final
145,356-byte same-slot `r14` has SHA-256
`9ae3b4915f3cf4fd062723c8b80d80e0319ddc9db250662c50584b3f764d373c` (provisional SHA-256
`41fafe5dfdfbaf23c206ae366913082ff255e6e5f92217f02cfc95b83a5fc048`); all 39 receipt records
carry `exit_code: 0`, but the artifact and candidate receive zero credit. The mandatory precommit
certified-SxPID2 baseline failed in normal and optimized modes with exact stderr SHA-256
`5994ccdfb8dcfe35fac7646050c15ef4f19eee8524233b1cd57f651d19d78611` over 255 bytes: expected
justfile digest `74fb7bfd4500d8b121666a738a412fbdb409e7acf673b156645d215453ab310f`, observed
`93399171cfbb743dba93c7be1ec85e446a33193e41ada3977d198b0e4ecc6437`. Its 124-mutation self-test was
operator-observed passing in both modes with identical 58-byte stdout SHA-256
`2f163d400569a0897533ef5f5bdae357bd97962d0888ac2bbf68cfa5fe753351`, but therefore did not
establish the baseline. Independent review also found that three documents conflated named
self-test output with `r14` command custody. The archived `r14` exact argv roster contains zero
records for the certified baseline, certified self-test, Lean-freeze self-test, or C9 self-test;
ten other named self-test command records are present. Canonical receipt bytes contain zero literal
`live-pre-replay-ready` occurrences, but stream payloads retain only byte-count/SHA-256 descriptors,
so that is not a raw-stdout absence claim. Separate normal/optimized Lean-freeze self-test outputs
were operator-observed identical at 268 bytes with SHA-256
`a77c6d4634ad134975d9a42520a4dc16cd696d51879614a1a4f711eab8ce9f93` and report 132 mutations,
including `live-pre-replay-ready`; this is outer observation, not `r14` invocation/stdout custody.
At a separate generator call site, the same validator implementation evaluates the equivalent
live-cut predicate once before the replay command sequence. Full static checks and custody snapshots
precede the sequence; full static checks and custody/executable comparisons follow it before
publication. These correlated, common-mode endpoint checks are not per-command or atomic custody,
and source custody is not invocation/stdout custody. The observed mutable ref was a recovery
locator, not authentication or durability. No L9 was issued for the candidate, and the bounded
provider/history check observed no accepted-on-main C9 publication; there is no permission to reuse
its `r14`. A fresh current `r14` must exclude all three rejected same-slot final `r14` artifacts from current and
`prior_replay_*` lineage. During fresh recovery review, the first `justfile` repin exposed a second
fail-fast baseline edge at `scripts/README.md`: expected
`daedd86d0307984df8885849528ddfdd2d096a7b9d2799e308358ad4af59b33a`, observed
`c7fd28e0180bc19ebb09644840266e47f5a93c9b5af7e9062c7f0bbd2012e857`; its exact 273-byte stderr
has SHA-256 `e94271b9e1c1b7e885fb78d1839b2d8dacebf79aa6a72e6233db5773ded93ade`. This was an
operator-observed recovery-worktree diagnostic, not archived-candidate qualification or `r14`
custody. The repair now binds all five mutable certified surfaces plus the exact CI job and just
recipe sub-blocks.
A third unsigned direct-child C9 candidate is also rejected with zero credit. Archive commit
`769547a6d6ed70a074707d90bc2f55393fd34fa4`, tree
`fb89c31922454dfc6d3da3d8ffa26dbe491b353e`, was observed on 22 August through mutable provider
recovery ref `refs/heads/archive/composite-v9-rejected-local-authority-oversize-20260822`; the ref
then pointed to that commit, `main` remained exact C8, and GitHub exposed zero workflow runs for it.
Its 145,356-byte same-slot `r14` has SHA-256
`66fdc640aad886c6de25a3a544a24ba016f4f2e73989abe5319f562da1c08919`; all 39 receipt records
carry `exit_code: 0`, but the artifact and candidate receive zero credit. Deterministically
substituting final Lean custody
`281b7504b96cabe88e4faa4db46c04d32832b4d42a3540f462951ffd68aea07c` with replay custody
`15d5fa25c532380db6d7f0a938dac84300ecfacf6c559332eda99bf7bc09fd96` in the canonical final `r14`
bytes reconstructs the provisional `r14` byte identity as SHA-256
`eece30e6d8477cb7aa3464df31d3fae590393a8b0dc47e21ea759ae5f3d6ab17`. This is a deterministic
reconstruction only, not an observed or retained provisional artifact, and receives no replay,
custody, or credit. Its 202,419-byte
self-excluding current-source manifest has SHA-256
`23d37f444b52d2bb8854e6cc7df53d0207074eceee6a080c89ace6729a850243`; that is archived byte
identity only, not acceptance, attestation, or semantic-correctness evidence. The production local
recorder failed closed and issued no L9. Its generic 51-byte stderr has SHA-256
`11da5230cf3da2dc9a8e4a1378e4707e90ba5b612f8cab4830e392d268cc5b40` and contains only
`ERROR: bounded local closure capture failed closed`; alone, that fixed public error discloses
neither the failure stage nor the production command streams. In the exact rejected source route,
`run_bounded` returns before `validate_record_value`, whose post-command record validation calls
`validate_authority_roster`. That source ordering does not retain or authenticate the production
stdout or stderr. Separate direct and sanitized operator invocations of `just ksg-composite-v9`
both exited zero and produced identical 32,248-byte stdout with SHA-256
`acf47c3a89810bd9cd47a5f3454d4cd5b519766dc3544cafd8565f94816bd41c` and identical 434-byte
stderr with SHA-256 `c73f68757307c6c5d44f354043b10b0a4e62b579d3500b7cf152449a5e863009`.
Those correlated command diagnostics are not local-recorder invocation or stream custody and do
not issue or replace L9. A separate substituted postcondition diagnostic produced the exact
104-byte, SHA-256 `4c9309bb307c001cd7231caff0dc92a9e6d6d2900116fece68ebe13a5b61dd81`
two-line log `FAIL CaptureError: local closure named-oversize authority inventory changed` and
`substituted_command_calls=1`. It isolates a stale named size-class roster: exact C9 self-test
`scripts/check-ksg-m1a-composite-v9-self-test.py`, SHA-256
`a704698097be3ffb0702a66f5fd0f9c794ca0a4ffbe137e6c3b94bd1825544db`, is 129,911 bytes and
therefore exceeded the 65,536-byte classification threshold but was absent from the expected
named-oversize set. It remained below the separate 2 MiB authority-stream maximum; this was a
named-roster classification defect, not authority-size exhaustion. The substituted diagnostic made
one substituted call and then failed at that postcondition, diagnosing the defect within the
substituted route. It is not production execution or custody, does not prove or retain the
production command streams, and its call must not be relabelled as the recorder-owned production
`just` invocation.
The mutable ref is a recovery locator, not authentication or durability. No L9, hosted, C9/R9,
scientific, accepted-current-replay, or independence credit transfers. Do not merge or cherry-pick
the candidate or reuse its evidence. A fresh current `r14` must exclude all three rejected
same-slot artifacts from current and `prior_replay_*` lineage.
The corrected same-version C9 is a fresh direct child of C8. Its changed-path set contains 32
paths; the rejected candidate's changed-path set contained 31. The sole path-set membership
difference is the fresh C9 addition of `scripts/check-mathematical-workflow-pdf-self-test.sh`;
this is a set-membership statement, not a claim that shared paths have identical bytes. The added
path carries one four-line test-fixture correction: set mode `0644` on six synthetic pre-existing workflow-PDF destinations
under the inherited restrictive umask. The PDF, LaTeX source, production portability gate, and
writer remain exact C8 bytes. This is not a sixth stale C8 binding or a theorem, estimator, PDF,
scientific, or production-writer change. A third, disjoint latent compatibility correction selects
exact GIL-enabled CPython 3.14.6 for local-recipe and hosted-post-setup C9 qualification because
immutable V7 contains a minor-sensitive
`ast.dump` projection that does not match C8's inherited 3.11 route; C8 failed before reaching that
route. New v9 complete-function guards use raw source-slice hashes whose selected slices were equal
in a documentary review on exact CPython 3.11.13, 3.12.11, 3.13.7, and 3.14.6, but immutable V7
remains runtime-bound; that comparison receives no qualification or portability credit. One hosted
pre-setup checkout-normalizer call plus four normal/optimized action-pin checker/self-test calls
remain runner-Python surfaces outside the exact-3.14.6 lane. Runtime preflights observe a bounded
command point; they do not
authenticate the interpreter, bind its executable bytes, prove atomicity or absence of later path
mutation, or enumerate every transitive process. The AST/source-route checks and hostile mutations
are finite regression evidence for a fixed lexical roster, not proofs of semantic soundness, causal
execution, or non-bypass. Dynamic namespace mutation and arbitrary execution custody remain
outside those analyses. Exact whole-file, tree, replay, and human-review custody remain authoritative
within their stated bounds. This is not a sixth stale binding, cross-minor portability
result, interpreter authentication, or scientific evidence. A completely fresh one-shot `r14` is
mandatory.

R9 has exactly four paths: it adds that durable local-closure record, the successor hosted capture,
and the deterministically derived receipt, then regenerates current-source last. The receipt binds
and validates the predecessor capture, local record, and successor capture. Neither milestone may
change scientific code, issue a v3/v4/v5 receipt, recreate a missing historical index, promote KSG
M1a beyond `integration_no_go`, or transfer evidence among the scientific-object rows above.

Only after committing the final self-excluding manifest, run the post-commit route from an exact
clean checkout. The shell owns these temporary files; v2 makes no path, durability, or upload
custody claim:

```text
artifact_dir="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-post-commit-source-state.XXXXXX")"
artifact="$artifact_dir/post-commit-source-state-v2.json"
(umask 077; set -o noclobber
 python3 -I -S -B scripts/check-post-commit-source-state-v2.py --emit > "$artifact"
 python3 -O -I -S -B scripts/check-post-commit-source-state-v2.py --emit > "$artifact.optimized")
cmp "$artifact" "$artifact.optimized"
python3 -I -S -B scripts/check-post-commit-source-state-v2.py --validate-stdin < "$artifact"
python3 -O -I -S -B scripts/check-post-commit-source-state-v2.py --validate-stdin < "$artifact"
python3 -I -S -B scripts/check-post-commit-source-state-v2-self-test.py
python3 -O -I -S -B scripts/check-post-commit-source-state-v2-self-test.py
```

`AGENTS.md` is part of the exact current operational-wiring projection checked by the Lean freeze
gate. Since C12, that mutable projection is separate from the immutable historical `r14` receipt.
After operational text changes, freeze all bytes, rebind only the current operational-wiring
hashes, and pass the freeze checker and self-test under normal and optimized Python. Generate the
source-state manifest last. This rebind gives no Lean execution or replay credit. Never edit or
repin the preserved `r14` maps or receipt. A new replay requires a separate reviewed, versioned
route and a new receipt; do not reuse the one-shot `r14` generator.

Preserve Lean 4.32 receipts as immutable historical evidence: never rewrite an old observed run as
4.33, and never transfer a historical receipt to the current descendant. The most recent accepted
4.33 replay receipt is
`audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json`;
the 11 August, unsuffixed 12 August, finalized `r2`, finalized `r3`, finalized `r4`, finalized `r5`,
finalized `r6`, finalized `r7`, finalized `r8`, finalized `r9`, finalized `r10`, finalized `r11`,
finalized `r12`, and finalized `r13` receipts are exact-hash-bound prior replays. Here `r14` is the
fourteenth accepted slot in the sequence beginning 12 August. Counting the separate 11 August
historical receipt, it is the fifteenth receipt in the accepted/historical lineage. Rejected
same-slot artifacts are additional zero-credit documents; no total count of every generated
receipt is claimed. The suffix does not denote a calendar date, schema, theorem, review, assurance
tier, or independence revision. The `r14` route receives execution credit only for its exact bound
command and source state when that receipt exists and validates. Current operational-wiring checks
do not extend that credit to changed operational bytes.

## Workspace layout

| Crate | Path | Role |
|---|---|---|
| `pid-core` | `crates/pid-core` | The estimators, PID atoms, invariants, geometry, preprocessing, and the `exp0` diagnostic binary. `#![forbid(unsafe_code)]`. |
| `pid-runlog` | `crates/pid-runlog` | Versioned, content-addressed run-log schema + the `pid-runlog-replay` CLI. |
| `pid-python` | `crates/pid-python` | PyO3 + maturin bindings (the `pid_core_rs` module). Built as an `abi3` wheel, not via plain `cargo`. |

## Where things live in `pid-core`

The public API is re-exported from `crates/pid-core/src/lib.rs` under an explicit namespace split:
`stable::{categorical, quantized, imin, continuous, preprocessing}` and `diagnostics` are the
default surface (`stable::continuous` is report-first — `ksg_mi_report` + `SupportContract`; the
raw scalars are deliberately demoted to `experimental::continuous::raw_scalars`), while every
research family lives under a default-off, feature-gated `experimental::*` module (`continuous`,
`isx_heuristics`, `mixed_dimension_pid3`, `hyperbolic`, `hierarchy`, `pipelines`). `lib.rs` is the
authoritative map of what is public where; the implementation is split by topic in the modules
below. Tests live in two places. Same-stem integration files under `crates/pid-core/tests/`
cover `ksg` (+ `ksg_report`), `isx`, `pid2`, `pid3` (+ `pid3_partial`), `geometry`, `invariants`,
`preprocess`, `observation_noise`, `distance_matrix`, `hierarchy`, the `sxpid_*` family for
`sxpid.rs` (`_axioms`, `_properties`, `_nsource`, `_bootstrap`, `_interpretation`, `_reference`,
`_gaussian_oracle`,
`_exhaustive_oracle`), `imin.rs` +
`discrete_pid_properties.rs` for `discrete_pid.rs`, `fitted_quantized_sxpid.rs` for the
quantizer→sxpid path, `permutation_and_fdr.rs` for `pipeline.rs`, and the cross-cutting suites
(`cross_validation.rs`, `gaussian_pid_atoms.rs`, `hyperbolic_mi.rs`, `parallel_bit_identity.rs`,
`known_failures.rs`, `continuous_reports.rs`, `continuous_resource_contracts.rs`,
`discrete_resource_contracts.rs`, `software_identity.rs`, `software_identity_build.rs`), with shared
fixture/digest helpers in `tests/common/mod.rs`.
`bootstrap.rs`, `pls.rs`, `logistic.rs`, `discrete_pid.rs`, and the kernel modules additionally
carry in-module `#[cfg(test)]` blocks.

The gate column is the cargo feature that compiles the module in (from the `#[cfg(feature = …)]`
mod declarations in `lib.rs`); "—" means it is part of the default build. Where a module compiles
by default but re-exports some items only under a feature, the row says so.

| Module (`src/…`) | Gate | Key public items | What it covers |
|---|---|---|---|
| `ksg.rs` | — | stable `ksg_mi_report`, `KsgConfig`, `NegativeHandling`; raw `ksg_mi` / `ksg_local_mi_terms` only under `experimental::continuous::raw_scalars` | KSG continuous MI estimator; the stable surface is report-first. |
| `isx.rs` | `experimental-continuous` | `isx_redundancy_report`, `IsxConfig`, `IsxMethod`; raw `isx_redundancy` under `raw_scalars` | Continuous `I^sx_∩` redundancy (Ehrlich et al. 2024). `experimental-heuristics` additionally exposes `experimental::isx_heuristics` — formula-labelled baselines that do **not** estimate the paper functional. |
| `pid2.rs` | `experimental-continuous` | `pid2_isx`, `Pid2Config`, `Pid2Result`, cross-fit/split-sample reports | Continuous 2-source PID atoms (Red/Unq1/Unq2/Syn). |
| `pid3.rs` | `experimental-continuous`; full lattice `research-mixed-dimension-pid3` | `incomplete_pid3_*`; research `pid3_isx` | Incomplete diagnostics and research-only full 3-source continuous lattice. |
| `discrete_pid.rs` | — | `imin_pid2`, `imin_pid3` (+ `_quantized` / `_with_budget` variants), exported as `stable::imin` | Discrete `I_min` PID (Williams & Beer 2010). |
| `sxpid.rs` | — | `discrete_sxpid2/3/n`, `fitted_quantized_sxpid2/3/n`, `SxPointwiseAtom`, `SxAveragedAtom`, `SxAtomInterpretation`, `SxAtomDecompositionMeasure` | Empirical categorical shared-exclusions PID `i^sx_∩` (2–4 sources); typed pointwise/averaged atoms plus a project-defined measure/scope/claim boundary. |
| `quantizer.rs` | — | `EqualWidthQuantizer`, `QuantizerConfig` | Training-fitted reusable equal-width quantization with edge/occupancy provenance. |
| `invariants.rs` | — | `o_information_discrete`, `co_information_pairwise_discrete`, `red_degree_discrete` / `vul_degree_discrete` | Discrete co-/O-information, `r̄`, `v̄` screening stats. |
| `ci.rs` | `experimental-continuous` | `co_information_pairwise/triplet` (+ report forms) | Continuous (KSG-based) co-information. |
| `geometry.rs` | — | intrinsic-dimension, distance-concentration, four-point-delta summaries | Geometry diagnostics for kNN-validity. |
| `support.rs` | — | `SupportContract`, `continuous_input_diagnostics`, shell diagnostics | Fail-closed population-support declarations and one-sided sample diagnostics. |
| `report.rs` / `resource.rs` | — | `EstimandIdentity`, `EstimateReport`, `ResourceBudget`, `CancellationToken` | Report-first scientific status/assumptions and bounded memory/operation preflight. |
| `identity.rs` (+ crate `build.rs` / `build_support.rs`) | — | `software_identity`, `SoftwareIdentity`, typed API/source/build/reference/attestation components | Project-defined, package-safe software identity; no estimator or defining paper. |
| `preprocess.rs` | — | `Standardizer`, `PcaProjector`, `HashProjector`; legacy `Jitter` re-exported only under `experimental-pipelines` | Fitted standardization, PCA, hash projection, and the unreported jitter migration primitive. |
| `observation.rs` | `experimental-pipelines` | `GaussianNoiseSpecification`, `GaussianNoiseDeclaration`, `GaussianNoiseStream`, `GaussianNoiseTransform`, `GaussianNoiseApplicationReport` | Project-defined typed provenance for an ideal added-Gaussian kernel and its deterministic binary64 application. This is not a PID estimator or a scientific-novelty claim. |
| `pls.rs` | `experimental-pipelines` | `PlsProjector` | Partial least squares supervised projection. |
| `bootstrap.rs` | `experimental-pipelines` | `block_bootstrap`, `block_bootstrap_paired`, `BootstrapConfig` | Dependence-aware block-bootstrap uncertainty quantification. |
| `pipeline.rs` | `experimental-pipelines` | `permutation_rows_pvalue*`, `permutation_pid3*`, `benjamini_hochberg` / `benjamini_yekutieli`, `pls_cv_select_components`, `pls_project_then_pid3`, `screen_pid2_pairs`, `bootstrap_rows_stats` | Composed PLS → PID → UQ pipelines: permutation nulls, FDR adjustment, PLS component selection, pair screening — the bulk of `experimental::pipelines`. |
| `same_sample.rs` | `experimental-pipelines` | `ExploratorySameSampleQuantizedResult`, `SameSampleEqualWidthProvenance` | Feature-only provenance wrapper for same-row equal-width adapters without mutating stable categorical encoding enums. |
| `logistic.rs` | `experimental-pipelines` | `LogisticRegression`, `LogisticRegressionConfig` | L2-regularised logistic regression (Newton–IRLS); internal failure-detector primitive. |
| `hierarchy.rs` | `experimental-hierarchy` | `hierarchical_pairwise`, `hierarchical_triplet`, `HierarchicalConfig` | Fast→slow screening for many-source settings. |
| `hyperbolic.rs` | `experimental-hyperbolic` | `HyperbolicMetric`, `hyperbolic_distance_lorentz`, Poincaré ↔ Lorentz maps, typed KSG and geometry diagnostics | Hyperbolic (Lorentz-model) pairwise MI and diagnostics isolated from stable metric/config/report types. |
| `kdtree.rs` / `nn.rs` | — (internal) | — | Exact Chebyshev kd-tree and brute-force kNN backends behind KSG/`i^sx` (bit-identical to each other; parity-tested). |
| `metric.rs` / `matrix.rs` / `error.rs` | — | `Metric`, `MatRef` / `MatOwned` / `DiscreteMatRef`, `PidError` / `PidResult` | Metrics, borrowed/owned matrix views, and the error taxonomy — the types every estimator signature uses. |
| `distance_matrix.rs` | — | `symmetric_distances`, `SymmetricDistanceMatrix` | Budgeted pairwise distance matrices (under `diagnostics`). |
| `par.rs` / `stats.rs` | — (internal) | — | Index-ordered parallel map (keeps the `parallel` feature bit-identical to serial) and digamma/statistics helpers. |
| `bin/exp0.rs` | `experimental-all` | — | The `exp0` validation/diagnostic binary (see below). |

Runnable end-to-end examples live in `crates/pid-core/examples/`: `ksg_and_pid.rs` (continuous MI +
2-source `I^sx_∩` PID on a synthetic system) and `discrete_sxpid.rs` (discrete shared-exclusions PID
on canonical logic gates, with deterministic reference-matching output).

## Build / test / lint (mirror CI)

```bash
cargo test --locked --workspace --exclude pid-python        # stable workspace tests
cargo test --locked -p pid-core --no-default-features       # approved stable default surface
cargo test --locked -p pid-core --features parallel         # exact data-parallel kNN path
cargo test --locked -p pid-core --all-features              # every default-off research surface
cargo test --locked --release -p pid-core --all-features    # release-mode numerical fixtures
cargo fmt --all --check                                     # formatting
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
RUSTDOCFLAGS="-D warnings" cargo doc --locked -p pid-core --no-default-features --no-deps
RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps
# the docs.rs gate is cargo *rustdoc*, not cargo doc — --lib is required because --all-features
# also exposes bin/example/bench targets, and cargo forwards trailing args to only one target
RUSTDOCFLAGS="-D warnings" cargo rustdoc --locked -p pid-core --all-features --lib -- --cfg docsrs
RUSTDOCFLAGS="-D warnings" cargo rustdoc --locked -p pid-runlog --all-features --lib -- --cfg docsrs
# worked example: MI + 2-source PID on a synthetic system (fast sanity check)
cargo run --release -p pid-core --features experimental-continuous --example ksg_and_pid
# smoke: the exp0 diagnostic + a run-log round-trip
cargo run -p pid-core --all-features --bin exp0 -- --seeds 1 --summary-json /tmp/summary.json --runlog /tmp/run.jsonl
cargo run -p pid-runlog --bin pid-runlog-replay -- --validate /tmp/run.jsonl
python3 scripts/check-software-identity.py               # identity/schema/feature/digest/package coherence
python3 scripts/check-software-identity-self-test.py     # fail-closed mutation suite
python3 -I -S -B scripts/check-advisory-councils-archive.py  # bounded inert archive accounting
python3 -O -I -S -B scripts/check-advisory-councils-archive.py
python3 -I -S -B scripts/check-advisory-councils-archive-self-test.py  # 64 named mutations
python3 -O -I -S -B scripts/check-advisory-councils-archive-self-test.py
python3 scripts/check-z3-pid2-algebra.py                 # exact PID2/PID3 lattice obligations; Z3 4.16.0
python3 scripts/check-z3-pid2-algebra-self-test.py       # satisfiable proof mutations must fail closed
python3 scripts/check-lean-finite-convergence.py         # 339 declarations / 246 named theorems
python3 -O scripts/check-lean-finite-convergence.py
python3 scripts/check-lean-finite-convergence-self-test.py
python3 -O scripts/check-lean-finite-convergence-self-test.py
python3 -I -S -B scripts/check-lean-toolchain-freeze.py       # frozen 4.33 replay/current-vs-historical custody
python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
just --justfile justfile.sxpid3-informative-invariance verify  # P1 Lean/exact/Rust layers
python3 scripts/check-lean-ksg-integer-harmonic.py       # 19 conditional exact harmonic theorems
python3 -O scripts/check-lean-ksg-integer-harmonic.py
python3 scripts/check-lean-ksg-integer-harmonic-self-test.py  # 14 semantic proof mutations
python3 -O scripts/check-lean-ksg-integer-harmonic-self-test.py
python3 -I -S -B scripts/check-lean-kernel-14576-self-test.py  # local packet: 199 negative + 8 positive controls
python3 -O -I -S -B scripts/check-lean-kernel-14576-self-test.py
python3 -I -S -B scripts/check-lean-toolchain-custody-self-test.py  # local custody: 740 negative + 21 positive; Q1 retained at zero credit
python3 -O -I -S -B scripts/check-lean-toolchain-custody-self-test.py
python3 scripts/check-z3-ksg-integer-harmonic.py         # 4 premise-explicit QF_UFLIRA obligations
python3 -O scripts/check-z3-ksg-integer-harmonic.py
python3 scripts/check-z3-ksg-integer-harmonic-self-test.py   # 12 semantic + 52 separate firewall controls
python3 -O scripts/check-z3-ksg-integer-harmonic-self-test.py
scripts/check-formal-pdf-set.sh                          # all declared formal papers and render contracts
python3 -I -B scripts/check-mathematical-results-guide-prose.py  # selected editorial subset; no ASD-STE100 conformance claim
python3 -O -I -B scripts/check-mathematical-results-guide-prose.py
python3 -I -B scripts/check-mathematical-results-guide-prose-self-test.py  # 33 hostile/control cases
python3 -O -I -B scripts/check-mathematical-results-guide-prose-self-test.py
python3 -I -S -B scripts/normalize-mathematical-results-guide-pandoc-tex-self-test.py  # 4 positive + 214 rejected subprocesses
python3 -O -I -S -B scripts/normalize-mathematical-results-guide-pandoc-tex-self-test.py
# hosted raw profile: 2 controls + 67 hostiles = 69
HOSTED_GUIDE_FIXTURE="$PWD/audit/evidence/mathematical-results-guide-pandoc-3.10.2-ubuntu-24.04-texlive-2023-hosted-raw.pdf"
python3 -I -B scripts/check-mathematical-results-guide-pdf-hosted-raw-profile-self-test.py "$HOSTED_GUIDE_FIXTURE"
python3 -O -I -B scripts/check-mathematical-results-guide-pdf-hosted-raw-profile-self-test.py "$HOSTED_GUIDE_FIXTURE"
python3 -I -B scripts/check-mathematical-results-guide-pandoc-portability-receipt.py  # closed translated 3.1.3 receipt
python3 -O -I -B scripts/check-mathematical-results-guide-pandoc-portability-receipt.py
# per mode: 2 controls + 100 semantic + 11 custody; plus 6 separation + 4 source-custody
python3 -I -B scripts/check-mathematical-results-guide-pandoc-portability-receipt-self-test.py
python3 -O -I -B scripts/check-mathematical-results-guide-pandoc-portability-receipt-self-test.py
# producer-profile dispatch; runtime reports the current inventory
python3 -I -B scripts/check-mathematical-results-guide-pdf-mode-wiring-self-test.py
python3 -O -I -B scripts/check-mathematical-results-guide-pdf-mode-wiring-self-test.py
scripts/check-mathematical-results-guide-builder-self-test.sh  # 69 source/staging/mode/comparison/output cases
scripts/check-mathematical-results-guide-tagpdf-compat-self-test.sh
scripts/check-mathematical-results-guide-uri-contents-compat-self-test.sh  # 6 controls + 14 hostiles
scripts/check-mathematical-results-guide-filespec-compat-self-test.sh  # 3 controls + 14 hostiles
python3 -I -B scripts/check-mathematical-results-guide-figure-assets.py
python3 -O -I -B scripts/check-mathematical-results-guide-figure-assets.py
python3 -I -B scripts/check-mathematical-results-guide-figure-assets-self-test.py  # 45 hostile mutations
python3 -O -I -B scripts/check-mathematical-results-guide-figure-assets-self-test.py
python3 -I -B scripts/regenerate-mathematical-results-guide-open-font-figures-self-test.py  # 2 controls + 14 hostiles
python3 -O -I -B scripts/regenerate-mathematical-results-guide-open-font-figures-self-test.py
python3 -I -S -B scripts/check-mathematical-results-guide-font-roster-self-test.py  # 2 controls + 26 hostiles
python3 -O -I -S -B scripts/check-mathematical-results-guide-font-roster-self-test.py
python3 -I -B scripts/check-mathematical-results-guide-pdf-id-variance-self-test.py  # 4 controls + 28 hostiles
python3 -O -I -B scripts/check-mathematical-results-guide-pdf-id-variance-self-test.py
python3 -I -B scripts/check-mathematical-results-guide-trailer-id-observation.py  # receipt only; zero portability/execution credit
python3 -O -I -B scripts/check-mathematical-results-guide-trailer-id-observation.py
python3 -I -B scripts/check-mathematical-results-guide-trailer-id-observation-self-test.py  # 3 controls + 56 hostiles
python3 -O -I -B scripts/check-mathematical-results-guide-trailer-id-observation-self-test.py
python3 -I -B scripts/check-mathematical-results-guide-pdf-structure-self-test.py  # 74 object + 1 raw + 4 diagnostic + 4 path controls
python3 -O -I -B scripts/check-mathematical-results-guide-pdf-structure-self-test.py
scripts/check-mathematical-results-guide-pdf.sh --exact  # raw repeated-build and rebuilt/committed guide bytes
# selected hosted/legacy profile; unsupported producers fail closed
scripts/check-mathematical-results-guide-pdf.sh --cross-toolchain
scripts/check-pid-sensor-placement-and-galadriel-guide-pdf.sh --exact  # current/proposed Galadriel placement guide
scripts/check-sxpid3-source-marginal-audit-pdf.sh --exact  # canonical MD/PDF SxPID3 audit coherence
python3 scripts/generate-ksg-local-arithmetic-oracle.py  # no-write replay of all 8,198 rows
python3 -O scripts/generate-ksg-local-arithmetic-oracle.py
python3 scripts/check-ksg-harmonic-exact-enclosure.py    # 6,920 Fraction + directed-Decimal route
python3 -O scripts/check-ksg-harmonic-exact-enclosure.py
python3 scripts/check-ksg-harmonic-exact-enclosure-self-test.py  # 29 scientific/custody + 2 comparator controls
python3 -O scripts/check-ksg-harmonic-exact-enclosure-self-test.py
python3 scripts/generate-ksg-harmonic-modular-certificate.py
python3 -O scripts/generate-ksg-harmonic-modular-certificate.py
python3 scripts/check-ksg-harmonic-modular-certificate.py
python3 -O scripts/check-ksg-harmonic-modular-certificate.py
python3 scripts/check-ksg-harmonic-modular-certificate-self-test.py  # 28 scientific/custody + 2 JSON controls
python3 -O scripts/check-ksg-harmonic-modular-certificate-self-test.py
# The unscoped historical checker remains nonzero with 13 open gates. The descendant wrapper
# replays five live-applicable routes, invokes the current catalog gate, and retains release-only
# plus the frozen catalog route only through exact-tree replay. Its self-test has 35 controls.
python3 -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation.py
python3 -O -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation.py
python3 -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation.py --historical-tree-replay
python3 -O -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation.py --historical-tree-replay
python3 -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation-self-test.py
python3 -O -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation-self-test.py
# Replays the immutable C3 checkpoint as both a clean commit and its exact parent-plus-overlay
# candidate, then replays the settled hosted-follow-up gate at its own immutable direct-child
# commit. The historical lifecycle is required by the hostile suite that creates test commits;
# neither replay adjudicates the current descendant.
# The wrapper normalizes its child-checkout umask to 022 before cloning; its mktemp root stays 0700.
scripts/check-ksg-c3-checkpoint.sh
# The follow-up runner freezes source size+SHA-256 and the self-test binds the actual child mode.
# Diagnostic checker output is explicitly no-credit. The direct-child route remains valid only at
# the exact implementation child and is invoked there by the immutable wrapper above; do not relax
# it to accept later descendants. A later descendant needs its own acyclic receipt and hosted run.
# The reviewed overlay is exactly 13 paths (eight modified and five added), leaving 552 immutable
# anchor paths protected. Its SxPID2 claim-checker edit is exactly three mutable-container digest
# rebindings. The source inventory has 109 hostile cases in 18 bookkeeping families and declares
# 88 mutation-target verifier launches (86 checker and two self-test), plus 22 local receipt cases
# and 38 separately named, non-mutation harness controls. The verifier runtime is restricted to
# GIL-enabled CPython 3.11 through 3.14 with one enumerated Python thread; see scripts/README.md for
# the explicit signal, preexec, waiter, native-thread, and hard-deadline nonclaims. Do not invoke
# that direct-child gate from a descendant; the immutable wrapper supplies its exact f6 lifecycle.
# Current direct-child M1a lifecycle, separate from the historical C3/f6 wrapper above. Before the
# commit, provide the independently constructed alternate-index tree, redirect its sealed mode-0400
# regular file to standard input, and provide the detached checkpoint in `--mode precommit`; after
# committing, use `--mode postcommit` with the same exact identities. No path is passed to Python.
# Policy-only/self-test modes are local diagnostics and grant no M1a credit.
python3 -I -S -B scripts/check-ksg-m1a-phase.py --validate-policy-only
python3 -O -I -S -B scripts/check-ksg-m1a-phase.py --validate-policy-only
python3 -I -S -B scripts/check-ksg-m1a-phase-self-test.py
python3 -O -I -S -B scripts/check-ksg-m1a-phase-self-test.py
just ksg-witnesses                                      # exact W1/W1b/W2/W2b summaries in debug/release
# Each command below must execute exactly 12 tests, never a feature-gated zero-test false green.
cargo test --locked -p pid-core --no-default-features --features experimental-pipelines --test parallel_bit_identity
cargo test --locked --release -p pid-core --no-default-features --features experimental-pipelines --test parallel_bit_identity
cargo test --locked -p pid-core --no-default-features --features experimental-pipelines,parallel --test parallel_bit_identity
cargo test --locked --release -p pid-core --no-default-features --features experimental-pipelines,parallel --test parallel_bit_identity
python3 scripts/check-citation-edge-countermodel.py      # exact C2 adjacent-arrow negative control
python3 scripts/check-citation-edge-countermodel-self-test.py
python3 scripts/check-lean-citation-edge-countermodel.py # same witness via pinned Lean/Mathlib
python3 scripts/check-lean-citation-edge-countermodel-self-test.py
python3 -I -S -B scripts/check-zeta-pid-transfer-firewall.py # exact no-transfer controls
python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall.py
python3 -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
python3 scripts/check-release-scope.py                   # scope/signature-registry coherence
scripts/check-release-scope-self-test.sh                 # fail-closed scope/history mutations
scripts/check-public-api-snapshots.sh                    # rebuild immutable declaration evidence
scripts/check-release-state.sh candidate                  # pre-tag public-metadata truth
```

For KSG revision 4, keep evidence inventories failure-diverse and numerically separate. The
compiled Rust corpus test directly classifies all 8,198 selected helper outputs as
`+0/-0/nonzero = 354/0/7844`. The exact-enclosure inventory is 29 scientific/custody mutations
plus two exact-`Fraction(Decimal)` comparator controls; the modular inventory is 28
scientific/custody mutations plus two strict JSON shape/type/value controls; and the Z3 inventory is
12 semantic countermodels plus 52 bounded parser/profile/type/snapshot/transport/result controls
(`16/25/11`). Do not sum controls into theorem or semantic-mutation counts.

The Z3 raw and token-stream pins are correlated custody views of the same proof bytes. A retained
well-typed wrong-theorem dual rebase remains a human/Git/receipt cut. The odd-prime modular lanes
share `H_(p-1-t) = H_t (mod p)`; the rejected-prime collisions are one reflected event, and the
selected fields are not independent proofs. The `1000001=101*9901` control reaches the
deterministic u32 Miller--Rabin loop after bypassing the `2..37` small-prime prefilter, but that is
path coverage only.

Treat `x+y <= n+k` only as a conditional eligible-row set lemma under the finite-positive-radius,
unique-shell, exact-count, common-row-set, and inventoried-map premises. Neither it nor the stronger
balanced lower bound is a promoted revision-4 theorem. Implementation-local purity of a row helper
does not imply statistically independent observations.

The 13-gate repository/publication disposition remains **NO-GO** throughout M1a. Commit, push, and
remotely verify the canonical unsigned M1a implementation first. Only a separate descendant M1c
may bind immutable `evidence-matrix-v4.md` and `decision-v4.md`; never use preclosure evidence to
grant final authority early. Preserve the negative paths and checker repairs in the revision-4
correction ledger and failure memos. Advisory external-model material is process evidence, never
claim evidence.

W1b is a finite Rust binary64/call-site witness only. It binds the immediate predecessor of the
raw radius, pair ordered counts, and pair/xblocks selected bits on one `n=4,k=1` fixture in both
source orders. Its production selected bits are one ordered position below the correctly rounded
exact-real `5/6` target. Never report W1b as an ULP theorem, a general nextafter/backend/neighbor
result, population-support evidence, estimator consistency/calibration, or PID validation; the
broader P2 backend corpus remains open.

The active formal baseline is the exact Lean 4.33.0/Mathlib v4.33.0 closure recorded in
`audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md`. Do not chase later releases: a new stable release,
release candidate, nightly, announcement, elapsed cadence, optional feature, speculative speedup,
or dependency-bot proposal is not a migration trigger. Keep 4.33 current until a documented
security/kernel issue, a required maintained route with no acceptable pinned workaround, sustained
reproducible baseline unavailability, or an exceptional human decision opens a new migration. A
candidate must close the source, kernel, checker, mutation, custody, documentation, and replay
gates and carry a rollback plan before it replaces the current pin. Preserve every 4.32 receipt as
historical evidence; never rewrite an observed old run to look like a 4.33 execution.

These commands track CI's core gates but are not byte-identical to `.github/workflows/ci.yml`.
CI also sets `RUSTFLAGS=-D warnings`, checks every individual feature on Ubuntu and default/all
features on macOS and Windows, verifies MSRV 1.89, runs deterministic property and fuzz corpora,
enforces coverage, reviews package/semver/unused-dependency state, generates an SBOM, scans history
for secrets, and builds/installs the Python wheel across its minimum/current matrix. `just ci`
covers the practical local subset; `just release-audit` lists the heavier release-candidate gates.

The example is the quickest "is the core working" check. Expected output (deterministic — the example
seeds its own RNG):

```text
Mutual information (nats):
  I(S1; T)     = 0.4209
  I(S2; T)     = 0.3798

2-source PID atoms (I^sx_∩), nats:
  Redundancy   = 0.1662
  Unique(S1)   = 0.2547
  Unique(S2)   = 0.2137
  Synergy      = 1.2350
  (sum of atoms = 1.8695 = I(S1,S2; T))
```

`pid-python` is a PyO3 extension module, so exclude it from the plain workspace `cargo test`: that
path can depend on a host `libpython` and has no binding coverage. The upgraded PyO3/NumPy wrapper
does participate in the workspace rustdoc gate. Exercise its actual Python API via maturin:

```bash
pip install maturin numpy pytest
maturin develop --release --locked -m crates/pid-python/Cargo.toml
pytest crates/pid-python/tests -q
```

## Conventions to preserve

- **Units:** all information quantities are in **nats** (natural log).
- **PID identities:** MI terms that feed PID atoms must be computed with `NegativeHandling::Allow` —
  clamping a term before a subtraction breaks `Red + Unq1 + Unq2 + Syn = I(S1,S2;T)`.
- **Negative atoms are real:** `I^sx_∩` (and its atoms) can be negative; never silently clamp.
- **Continuous support is declared, never inferred:** bare default continuous configs are
  intentionally non-runnable. Use the explicit absolute-continuity constructor only when every
  marginal and joint law required by that call has the stated full-dimensional population model.
  Exact ties are incompatible with ideal i.i.d., unrounded continuous-sample conditions but do not
  identify their cause or population support; all-unique samples cannot prove the model. Atomic,
  quantized, mixed, singular, or unknown support must be routed to a matching estimand.
- **Added noise changes the estimand:** never recommend it as a generic tie repair. Use the typed
  `GaussianNoiseTransform` only for an explicit observation-noise model or a seeded, reported
  noise-scale sensitivity analysis. The ideal Gaussian model gives smooth full support when its
  declaration is true. It does not prove finite MI, i.i.d. rows, estimator validity, or PID-atom
  monotonicity. Separate matrix reports do not establish a joint source-and-target noise model.
  `Jitter` is an unreported migration primitive.
- **Determinism:** accumulate over count maps with `BTreeMap`/sorted keys (not `HashMap`); the
  `parallel` feature must stay bit-identical to the serial path; seed all RNGs explicitly.
- **Software identity separates domains:** public Rust declaration-signature revision, source
  route, selected build context, forensic reference hashes, and attestation status are not
  interchangeable.
  Hash exact raw artifact bytes and retain declaration snapshots under immutable revision-scoped
  paths. Append preservation covers every HEAD-reachable registry-touch commit and direct tip
  parent; after a committed binding, exact snapshot bytes are checked through each path's reachable
  full history. The checker strips ambient Git routing/configuration, disables replacement/graft
  overlays, and binds Git's canonical worktree root. It cannot cover absent history and is not a
  transparency log.
  Never present identity equality as compatibility, authenticity, scientific/application validity,
  source/archive/binary equality, or cross-platform numerical identity. Format 1 attestation
  remains explicitly `none`.
  Preserve the build-time Git isolation and invalidation contract: do not re-enable ambient
  routing, replacement/graft, ref-backend, config, pathspec, or global/system attribute inputs; do
  not recursively watch the complete `.git` or object database (the bounded `objects/info`
  metadata watch is intentional); and keep unsupported or incomplete final source probes on an
  absent recovery watch. Preserve unchanged generated identity bytes across build-script reruns.
  Git older than 2.45 must not claim workspace cleanliness. Clean/dirty assumes repository metadata
  and package files remain stable during the bounded probe; retain the repeated input/status and
  final-HEAD checks, but do not describe them as an atomic snapshot.
  Any effective `filter` attribute on a tracked package path (including unset or unconfigured
  values), `attr.tree`, tracked symbolic links, and tracked gitlinks must remain `unknown`, without
  executing a clean-filter command under that stability assumption. This is a captured build
  snapshot, not a live Git-tool or object-store monitor.
- **`exp0` is a diagnostic gate, not a pass/fail test.** Its default sweep reports a scoped
  `GO`/`NO-GO` high-dimensional MI/coherence verdict and a separate, non-gating `GO`/`PIVOT`
  geometry disposition, and **exits 0 by default**. The sweep goes to dimension 256 at n=500,
  deliberately entering regimes where kNN MI is known to break down, so `NO-GO` MI/coherence or
  `PIVOT` geometry findings are expected, informative outcomes. Optional diagnostics use explicit
  produced/abstained/not-requested states rather than numeric sentinels. Shared-exclusions
  atom-measure validation is separately `not_adjudicated`, and atom-estimator validation is
  `blocked`; neither is inferred from the MI/coherence verdict.
  - `--strict-gate` does **not** enforce a verdict on the default high-d sweep (that would
    contradict the contract above). It enforces `GO` (exit code 3 otherwise) only on a **curated
    band** where `GO` is legitimately expected and is checked against an **analytic closed form**:
    a small grid of jointly-Gaussian systems at `d=1`, `n=4000` (an analytically checked,
    low-dimensional KSG regime), where the
    three measure-independent MI terms `I(S1;T)`, `I(S2;T)`, `I(S1,S2;T)` must match their
    Cover–Thomas Gaussian values within the scale-aware tolerance. `--strict-gate` implies
    `--strict-band` (which runs the band and reports it without enforcing). The four synthetic
    scenarios are still run at `d ∈ {2,4,8}` as a **non-gating** diagnostic alongside the band; they
    are a known non-`GO` regime because KSG underestimates the joint MI under strong dependence.
    `independent_additive` has positive shared-exclusions redundancy in the declared fixed-sample,
    fixed-gauge comparison in `tests/sxpid_gaussian_oracle.rs`; `exp0` reports it but never
    compares it with a zero target or folds it into a verdict. These are reported findings, not
    regressions, and must **not** be "fixed" by loosening the gate's tolerances.
- **Scientific changes:** a change that alters a numerical result must justify *why* the new value is
  correct (analytic ground truth or a cited paper), not merely that tests still pass.

## README-iff invariant (where READMEs may live, and how they wire in)

A directory gets a `README.md` **if and only if** it is one of:

- a **published artifact** (a crate published to crates.io, or a package published to PyPI), or
- a **directly-consumed unit** (something a human runs/imports on its own — a CLI, an example, a
  vendored tool), or
- a **browsed-asset directory** (a folder a reader lands in and expects orientation — currently
  only the repo root; `crates/` deliberately has none, since each crate README is one click away
  and the root README carries the workspace map).

No other directory should grow a stray `README.md`. If a folder is neither published, nor directly
consumed, nor browsed, it does not get one.

Wiring rules for the READMEs that do exist:

- **Rust library crates** (`pid-core`, `pid-runlog`): the crate README is the canonical crate-level
  doc and is wired into rustdoc via `#![doc = include_str!("../README.md")]` at the top of
  `src/lib.rs`. Because `include_str!` makes every ` ```rust ` and every **bare** ` ``` ` fence in
  the README a compiled-and-run doctest, audit the fences before wiring and re-fence:
  - prose / shell / commands / TOML / program output → ` ```text ` (never executed),
  - complete Rust that compiles but must not run → ` ```no_run `,
  - illustrative / incomplete / pseudocode Rust that won't compile (e.g. undefined vars like
    `s1_data` / `n`) → ` ```rust,ignore `.
  The bar is: `cargo test --doc -p <crate>` and
  `RUSTDOCFLAGS="-D warnings" cargo doc --no-deps -p <crate>` both pass clean. Each such crate's
  `Cargo.toml` also carries `readme = "README.md"`, `documentation = "https://docs.rs/<crate>"`, and
  a `[package.metadata.docs.rs]` block (`all-features = true`, `rustdoc-args = ["--cfg", "docsrs"]`).
- **maturin / PyO3 extension crates** (`pid-python`): wire the README with the `readme = "README.md"`
  manifest key **only** — do **not** add `#![doc = include_str!(...)]`. Their rustdoc is not the
  primary documentation surface, and a standalone README plus `readme=` avoids any risk to the
  maturin/`abi3` build.

## Before you push

Run the build/test/lint block above (all must be clean), update `CHANGELOG.md` under
`[Unreleased]`, and keep PRs focused. For security issues, follow `SECURITY.md` (do not open a
public issue). See `CONTRIBUTING.md` for the full contributor guide.
