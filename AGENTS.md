# AGENTS.md

Operational instructions for **pid-rs**. `CLAUDE.md` imports this file. Start with the session
handoff, then read this guide in full before you change the designated integration checkout.

## Start or resume a session

1. Read [SESSION_HANDOFF.md](SESSION_HANDOFF.md) and the ignored `.local/SESSION_HANDOFF.md`, when
   present. Find the current integration checkout, recovery copies, and unfinished work. Verify
   those locations before use. Machine-specific paths locate evidence; they do not establish it.
2. Observe the actual root, branch, HEAD, index, staged and unstaged changes, untracked files,
   worktrees, remote refs, and active writers. Preserve existing bytes before writing. A branch
   name, dated ledger, old plan, or previous percentage does not establish current progress.
3. Read the integration checkout in this order: README; mathematical results guide; method catalog
   and current claim decisions; mathematical workflow; discovery and durability blueprint; formal
   baseline and scripts guide; then the exact unfinished-work queue. Use the entry points below.
   Read the definitions, assumptions, proofs, and failure records for the work you select.
4. Before each important decision, compare at least ten materially distinct routes. Include no
   action and the simplest applicable non-PID route. State each route's assumptions, failure
   conditions, and required evidence. Record why you select or reject it and what could change
   that decision. Cosmetic variants do not count as separate routes.
5. Obtain independent-first written council critiques before members see each other's conclusions.
   Apply the required scientific and publication lenses below. Inspect the exact evidence yourself;
   record shared dependencies and retain dissent. Agreement is not proof or independent review.
6. Define one coherent milestone with a bounded write scope and explicit completion evidence.
   Freeze any required claim and judge packet before candidate work. Use gate modes that match the
   current release and claim state. Historical commands do not create current work items.
7. Complete the milestone, run its applicable checks, and reconcile code, proofs, claims, and
   publications. Make a small professional unsigned commit and push under the established
   authorization. Verify the remote object and required hosted checks at that exact commit. Move
   accepted work to main only through the preservation and integration procedure below.
8. Update the handoff with completed obligations, exact evidence, remaining work, and storage
   locations before a context reset. Do not mark the whole program complete when one milestone ends.

### Where to read next

| Need | Entry point | What governs the work |
|---|---|---|
| Project overview and use | [README.md](README.md) | Reading map, API boundaries, examples, and scientific cautions |
| Mathematical results | [MATHEMATICAL_RESULTS_GUIDE.md](MATHEMATICAL_RESULTS_GUIDE.md) | Navigation to exact statements and proofs; claim decisions retain their authority |
| Method identity and availability | [method-catalog.json](method-catalog.json), [METHODS.md](METHODS.md), and the current claim decision | Defining source, estimand, implementation status, assumptions, and accepted evidence |
| Mathematical workflow | [MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md](MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md) | Claim packets, proof routes, falsification, councils, and publication procedure |
| Discovery and preservation | [PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md](PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md) | Source-transfer review and proposed assurance design; it does not close claims |
| Formal evidence and checks | [assurance registry](audit/evidence/assurance-registry.json), [formal baseline](audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md), [scripts guide](scripts/README.md) | Exact theorem, toolchain, execution, and custody contracts |
| Unfinished work and retirement | [SESSION_HANDOFF.md](SESSION_HANDOFF.md), then the current claim and evidence indexes it names | Current obligations; re-observe refs and bytes before integration or deletion |
| Applications and alternatives | [ecosystem matrix](ECOSYSTEM_CAPABILITIES.md), [sensor and Galadriel guide](PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md) | Consumer assumptions, simpler comparators, and qualification gaps |

### Handoff and preservation rules

Use repository-relative links in public documents. Keep machine-specific roots, process handles,
private locators, and recovery manifests in ignored local records or the appropriate restricted
store. Preserve permitted working bytes and Git objects outside temporary directories. A Git bundle
omits uncommitted files. Record each copy's coverage and verify retrieval. Local recovery and remote
publication are separate obligations.

Assess useful fragments within each branch and worktree. A stale tree can contain a current proof,
counterexample, correction, or publication asset. Give each relevant fragment a recorded disposition
and a retrievable successor. Integrate accepted fragments into current main. Preserve load-bearing
negative evidence with its assumptions, exact inputs, result, rejection reason, and conditions for
reconsideration. Correct active false claims and retain their original evidence with a clear label.

The handoff must identify unfinished code and proofs, Markdown/PDF consistency work, required
hosted checks, mainline integration, and unresolved fragment dispositions. A permanently failed
attempt keeps that result. Retire a branch or worktree only after no process owns it and every
relevant byte has a verified successor. The detailed rules below define the complete procedure.

## Contents

- [Start or resume a session](#start-or-resume-a-session)
- [Commit & attribution policy (READ FIRST)](#commit--attribution-policy-read-first)
- [What this project is](#what-this-project-is)
- [Method provenance and novelty claims](#method-provenance-and-novelty-claims)
- [Scientific-object and evidence firewall (MANDATORY)](#scientific-object-and-evidence-firewall-mandatory)
- [Branch/worktree durability and closure (MANDATORY)](#branchworktree-durability-and-closure-mandatory)
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

New or materially redesigned human-facing PDFs, and changed pages in the mathematical-workflow and
durability-blueprint PDFs, use the reviewed repository-local publication design language. Existing
publications keep their established design
unless their own scope explicitly requires migration. Reuse reviewed repository-local publication
packages, headers, and figure grammar instead of importing an external runtime dependency. Preserve
the source palette identities: lapis `#1F3F60`, turquoise `#1F6968`, ink `#2C3E50`, mineral blue
`#D2E0E2`, ivory `#F7F3E9`, bronze body accent `#916400`, saffron structure `#B28218`, and
pomegranate `#743E37`. Use turquoise for subordinate headings, not for the primary title. Keep
vector paper grain, girih/rosette or related restrained geometric patterns low contrast and
decorative only. A pattern must never encode mathematical status, table value, or graph magnitude
without a text/shape label. Keep real searchable text above decoration, preserve generous spacing
and grayscale legibility. Render-inspect every changed page at normal size and inspect a declared
high-risk subset at high resolution.
Do not publish absolute paths or links to the private design source; the reviewed repository-local
TeX/SVG assets are the portable authority.

For each changed publication surface, record one visual council pass through 20 named lenses:
hierarchy; typography; grid; spacing/rhythm; narrative order; motif provenance; motif coherence;
ornamental restraint; palette identity; pattern/data-semantic separation; color-redundant labels;
grayscale legibility; real-text searchability and logical extraction order; print fidelity; A4/PDF
profile and embedded fonts; link/action safety; deterministic reproduction; source/derived-asset
separation; portable repository-local dependencies; and normal-size plus high-resolution rendered
inspection. An applicability reason may replace a pass. A source-code palette check, page count,
render digest, or council judgment does not substitute for the other lenses.

The inert negative-archive and contextual rare-tail gates preserve exact rejected evidence and its
non-adoption boundary. Passing either gate grants no scientific, formal, implementation, or release
credit; do not route those payloads into executable or authority surfaces.
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

## Branch/worktree durability and closure (MANDATORY)

These rules apply to every repository lane, regardless of whether an agent, a human, a proof tool,
or an ordinary build task created it. Research durability is part of the method, not housekeeping:

The dated human case record is
[`audit/evidence/worktree-and-branch-preservation-2026-08-27.md`](audit/evidence/worktree-and-branch-preservation-2026-08-27.md).
Its dated 1 September 2026 primary-common-Git-directory facts are projected into the strict
[`audit/evidence/worktree-and-branch-retirement-ledger-2026-09-01.json`](audit/evidence/worktree-and-branch-retirement-ledger-2026-09-01.json).
Ten separately rooted sibling common Git directories and their 12 observed worktrees are projected
into the separate strict
[`audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json`](audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json).
Both ledgers are bounded snapshots, not live monitors or cleanup authority. The sibling checker is
snapshot-integrity-only: it does not revisit the registries, bundles, remote, or network. The two
records exclude different scopes and together are not a global filesystem or non-Git custody
inventory; re-observe every applicable fact before retirement.

The separate dated
[`post-publication-custody-2026-09-02.json`](audit/evidence/post-publication-custody-2026-09-02.json)
records the later accepted-mainline observation and named cleanup actions. Its checker binds the
exact 14-line remote-head preimage and closed JSON bytes; the companion six-page PDF and visual
receipt are human presentation layers. This is a past-tense, bounded receipt: it neither authorizes
another deletion nor proves authenticity, theorem truth, estimator validity, application value, or
future repository state. Re-query every mutable ref and custody route before any later cleanup.

Treat storage classes as typed, non-interchangeable objects:

| Storage class | Credit and required boundary |
|---|---|
| Model context, terminal output, `/tmp`, or scratch file | Exploration only. It provides no recovery or evidence credit. |
| Dirty worktree/index/stash | Mutable local working state. Inventory tracked, staged, untracked, relevant ignored, mode, and process ownership; Git history does not preserve these bytes automatically. |
| Local commit/ref | Local Git-object recovery only. It supplies neither off-host durability nor accepted-mainline status. |
| Verified Git bundle | Recovery for exactly the advertised reachable Git objects. Bind bytes and SHA-256, compare advertised refs with the intended frozen inventory, run `git bundle verify`, and perform an isolated recovery drill. Preserve non-Git state separately. |
| Remote side/archive ref | Recovery through the declared remote for its reachable history. Call it off-host only when the separate host or custodian and a retrieval drill establish that fact. It is not accepted `main`, a release, or permanent scholarly storage. |
| Remote `main` commit | Minimum operational anchor for accepted work under the stated remote-retention and no-history-rewrite assumptions. Re-query the ref and bind the exact OID; a side-branch run does not substitute for a mainline event. |
| Release or scholarly/content-addressed archive | Named longer-term publication/recovery object under that service's policy. Record exact bytes, digest, locator, access, license, retention, and retrieval drill; none of these proves mathematical truth. |
| Approved restricted durable store | Home for protected, private, blinded, or embargoed preimages. Publish only a safe commitment/manifest, keep the retrievable locator access-controlled, and record omissions and retention limits. |
| Hosted CI artifact or cache | Ephemeral execution aid with expected expiry. It is not archival storage and must not be the only home of load-bearing evidence. |

- Use a separate branch/worktree when a task needs an isolated write scope, a frozen claim
  revision, a clean reproduction checkout, or an inert home for rejected/restricted evidence.
  Record the base commit, current commit/tree, branch or detached `HEAD`, common Git directory,
  owner, purpose, allowed writers, expected outputs, and configured build root. A linked worktree
  supplies a separate checkout, index, and `HEAD`; a separate build directory and bounded write
  scope require project convention or configuration. Linked worktrees share the object database
  and most refs, while `HEAD`, pseudorefs, and some per-worktree refs remain separate. A worktree is
  not an independent repository, scientific reviewer, durable store, or acceptance state.
- Isolation creates a closure obligation. Before integration, stop writers and inventory every
  worktree, ref, stash, alternate index, branch-only commit, dirty tracked path, staged path,
  untracked path, relevant ignored path, symbolic link, gitlink/submodule, sparse/skip-worktree or
  assume-unchanged state, and live process that owns the lane. Compare paths, blobs, and semantic
  roles. A mostly stale branch can contain one current theorem witness, counterexample, SVG,
  receipt, or process finding; preserve that fragment without merging the stale tree wholesale.
- A Git bundle preserves selected refs and reachable Git objects only. It does not preserve the
  working tree, index, stash, hooks, configuration, or uncommitted/ignored bytes. Before relying on
  a bundle, commit the permitted payload to an explicit ref or preserve non-Git state separately.
  Record bundle size and SHA-256, run `git bundle verify`, list advertised heads, and perform a
  clean recovery drill. A digest without a retrievable preimage supplies no recovery.
- Integrate from a fresh remote-`main` descendant. Port explicit paths or one coherent claim
  packet. Reconcile formulas, assumptions, source markers, tests, schemas, hostile controls,
  Markdown, TeX, PDFs, and receipts together. Regenerate self-referential manifests and derived
  publication bytes last. Never bulk-overlay an old worktree on a corrected tree.
- A formal lane must bind the exact proposition, definitions, distributions/support assumptions,
  units, quantifiers, boundary cases, source-to-symbol map, theorem roster, imports, axioms,
  toolchain/dependency revisions, checker source, and artifacts. Run kernel/solver checks, normal
  and optimized checker modes where supplied, hostile semantic/revision/artifact mutations, and a
  fresh hosted replay. Keep paper correspondence, formal validity, exact arithmetic, executable
  refinement, binary64 behavior, estimator calibration, and consumer qualification as separate
  obligations. A green algebra theorem does not formalize probability unless the stated random
  objects and probability claims occur in the checked theorem.
- Before advancing `main`, query the remote old object ID, prove the candidate is its descendant,
  and use an explicit expected-old lease. Query the remote after push, align local `main` with that
  observed object, and require the relevant hosted workflows on the exact mainline SHA. A
  side-branch run is preflight evidence, not the mainline publication event.
- Retire only after no process owns the lane, every byte has a disposition, accepted work is
  reachable from remote `main`, archive-only material has a verified durable successor, relevant
  gates pass, and a post-removal reachability inventory succeeds. Use `git worktree remove` for a
  linked worktree. Retain ambiguous refs. Delete reproducible caches and temporary build trees
  last, after exact targets and ownership are checked.

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
  accepted artifact identified by the attempt ledger or manifest is reachable from remote `main`.
  Keep the exact preimage of every adjudicating or selection/load-bearing artifact—including a
  rejected route—reachable from remote `main` or a verified durable locator under its typed
  negative/archive disposition. Only an artifact separately established as non-load-bearing and
  outside the required retention scope may be discarded with a ledgered reason. A rejection label
  or digest without a retrievable preimage never satisfies a load-bearing retention obligation. A
  remote side branch is a backup, not completion; move accepted work to `main`.
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
  preserves the advisory finding-by-finding adjudication.
  [`audit/evidence/wibral-pid-program-active-plan-2026-08-12.md`](audit/evidence/wibral-pid-program-active-plan-2026-08-12.md)
  is an immutable historical planning snapshot, despite `active-plan` in its filename. It is not a
  current work queue and its commands are not current instructions. Resolve present scientific
  status from the catalog, current claim decision/evidence indexes, and `KNOWN_LIMITATIONS.md`; use
  the exact C12 terminal boundary below for the composite lifecycle.
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
python3 -I -S -B scripts/check-pid-mathematical-audit-protocol.py
python3 -O -I -S -B scripts/check-pid-mathematical-audit-protocol.py
python3 -I -S -B scripts/check-pid-mathematical-audit-protocol-self-test.py
python3 -O -I -S -B scripts/check-pid-mathematical-audit-protocol-self-test.py
# Only after every intended source and operational byte is frozen, follow the private two-output
# regeneration-and-install procedure in scripts/README.md. Never redirect an emitter directly over
# the tracked manifest: a failed command would truncate the only retained copy.
python3 -I -S -B scripts/check-current-source-state-v1.py
python3 -O -I -S -B scripts/check-current-source-state-v1.py
python3 -I -S -B scripts/check-current-source-state-v1-self-test.py
python3 -O -I -S -B scripts/check-current-source-state-v1-self-test.py
```

### Current exact-C12 terminal boundary

The current composite-lifecycle authority is
[`ksg-rev4-m1a-composite-v12-terminal-failure-2026-08-23.json`](audit/evidence/ksg-rev4-m1a-composite-v12-terminal-failure-2026-08-23.json),
SHA-256 `375bf287c73dea35c70d21c74be58e54fe17ae27b4c38ebd9cdf543c8beab47c`,
for exact C12 commit `01466e88b0550333c2718f1716289e9642e30dc6`. Its bounded operational
conclusion is `Q12 = false`; `R12 = permanently_unissued`; and
`L12 = not_adjudicated`. The last value is neither success nor failure. The failed attempt-1
repository-CI and dedicated-v12 terms make Q12 false for either Boolean value of L12. These are
operational lifecycle conclusions, not a judgment about the KSG theorem, estimator, or scientific
claim.

`just ksg-composite-v12` refuses replay. The only current repeatable route is
`just ksg-composite-v12-preservation`; it rechecks the immutable terminal record and hostile
controls in normal and optimized Python and grants zero new execution, qualification, hosted,
scientific, or publication credit. `just ksg-composite-v9` and `just ksg-composite-v11` also refuse
replay. A later repair cannot become an exact-C12 attempt-1 term, revive Q12, or issue R12. Any
future lifecycle must have a separately specified version, task boundary, and evidence contract.

### Historical composite lifecycle (not current operational guidance)

The detailed C3--C12 chronology, rejected candidates, exact failure observations, and zero-credit
boundaries live in dated evidence rather than in this operational guide. Start with the
[v3 impossibility record](audit/evidence/ksg-rev4-m1a-composite-v3-impossibility-2026-08-15.json),
[v4 process](audit/evidence/ksg-rev4-m1a-composite-v4-process-2026-08-15.md),
[v5](audit/evidence/ksg-rev4-m1a-composite-v5-boundary-2026-08-18.md),
[v6](audit/evidence/ksg-rev4-m1a-composite-v6-boundary-2026-08-18.md),
[v7](audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md),
[v8](audit/evidence/ksg-rev4-m1a-composite-v8-boundary-2026-08-19.md),
[v9](audit/evidence/ksg-rev4-m1a-composite-v9-boundary-2026-08-19.md),
[v11](audit/evidence/ksg-rev4-m1a-composite-v11-boundary-2026-08-23.md), and
[v12](audit/evidence/ksg-rev4-m1a-composite-v12-boundary-2026-08-23.md) records.
Imperative wording inside those historical contracts describes the rule that applied then; it is
not permission to execute, replay, merge, promote, or reuse their artifacts now. Use only the
exact-C12 refusal/preservation boundary above unless a separately reviewed lifecycle is added.

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

This is a command catalog. Select the applicable checks from the changed paths, causal
dependencies, current claim packet, and release state. Record that scope before execution. The
catalog includes historical NO-GO results, refusal commands, and ordered replay phases. Do not run
it as one all-green queue or reopen a closed attempt. A command's presence does not change its
current authority or expected result.

For Rust or API changes, the practical matrix remains mandatory: stable workspace tests;
no-default-feature, parallel, all-feature, and release tests; formatting; all-target Clippy; the
listed rustdoc and docs.rs checks; examples and run-log replay; software-identity and API/package
checks; and applicable binding tests. Keep the declared dependency-policy preflight and check.
For publication changes, run the affected complete exact PDF checks and their self-tests, all
required normal and optimized modes, the full formal-PDF-set check, and publication-link checks.
Also run the milestone's causal, source-consistency, and package gates. Applicable failures remain
failures; do not lower scientific thresholds or remove a check to complete the milestone.

Local `just deny` and `just certified-sxpid` require exactly cargo-deny 0.20.2 and run the shared
version preflight plus its hostile self-test before their policy command. A raw `cargo deny`
invocation bypasses that repository preflight. The exact version-output check detects the known
0.19/0.20 command-grammar split; it does not authenticate the binary or atomically bind the later
process.

```bash
cargo test --locked --workspace --exclude pid-python        # stable workspace tests
cargo test --locked -p pid-core --no-default-features       # approved stable default surface
cargo test --locked -p pid-core --features parallel         # exact data-parallel kNN path
cargo test --locked -p pid-core --all-features              # every default-off research surface
cargo test --locked --release -p pid-core --all-features    # release-mode numerical fixtures
cargo fmt --all --check                                     # formatting
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
scripts/check-cargo-deny-toolchain.sh                       # requires cargo-deny 0.20.2 exactly
scripts/check-cargo-deny-toolchain-self-test.sh             # 2 accepted + 10 rejected probes
cargo deny --all-features --locked check                    # top-level options precede `check`
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
python3 -I -S -B scripts/check-inert-negative-archives.py  # 4 inert packets; 28 payloads
python3 -O -I -S -B scripts/check-inert-negative-archives.py
python3 -I -S -B scripts/check-inert-negative-archives-self-test.py  # 45 hostile mutations
python3 -O -I -S -B scripts/check-inert-negative-archives-self-test.py
python3 -I -S -B scripts/check-contextual-rare-tail-counterexample.py  # bounded binary64 witness
python3 -O -I -S -B scripts/check-contextual-rare-tail-counterexample.py
python3 -I -S -B scripts/check-contextual-rare-tail-counterexample-self-test.py  # 25 mutations
python3 -O -I -S -B scripts/check-contextual-rare-tail-counterexample-self-test.py
python3 -I -S -B scripts/check-pid2-represented-coordinate-v4.py --scope full  # exact grid + debug/release
python3 -O -I -S -B scripts/check-pid2-represented-coordinate-v4.py --scope full
python3 -I -S -B scripts/check-pid2-represented-coordinate-v4-self-test.py  # copied-root + mutations
python3 -O -I -S -B scripts/check-pid2-represented-coordinate-v4-self-test.py
scripts/check-pid2-represented-coordinate-assurance-pdf.sh --exact
scripts/check-pid2-represented-coordinate-assurance-pdf.sh --cross-toolchain
python3 -I -S -B scripts/check-z3-pid2-algebra.py       # exact PID2/PID3 lattice obligations; Z3 4.16.0
python3 -O -I -S -B scripts/check-z3-pid2-algebra.py
python3 -I -S -B scripts/check-z3-pid2-algebra-self-test.py  # common + sign/coordinate/row SAT controls
python3 -O -I -S -B scripts/check-z3-pid2-algebra-self-test.py
python3 scripts/check-lean-finite-convergence.py         # 339 declarations / 246 named theorems
python3 -O scripts/check-lean-finite-convergence.py
python3 scripts/check-lean-finite-convergence-self-test.py
python3 -O scripts/check-lean-finite-convergence-self-test.py
python3 -I -S -B scripts/check-lean-toolchain-freeze.py       # frozen 4.33 replay/current-vs-historical custody
python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
python3 -I -S -B scripts/check-lean-exact-log-product.py  # frozen 7-theorem generic algebra gate
python3 -O -I -S -B scripts/check-lean-exact-log-product.py
python3 -I -S -B scripts/check-lean-exact-log-product-self-test.py  # hostile/scope controls
python3 -O -I -S -B scripts/check-lean-exact-log-product-self-test.py
python3 -I -S -B scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py  # bounded Program-A semantics; still partial/open
python3 -O -I -S -B scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py
python3 -I -S -B scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4-self-test.py  # historical false-green + reseal controls
python3 -O -I -S -B scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4-self-test.py
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
python3 -I -B scripts/check-publication-links.py          # staged Markdown/PDF target and action graph
python3 -O -I -B scripts/check-publication-links.py
python3 -I -B scripts/check-publication-links-self-test.py  # 4 controls + 111 hostile staged/link/PDF mutations
python3 -O -I -B scripts/check-publication-links-self-test.py
scripts/check-formal-pdf-set.sh                          # all declared formal papers and render contracts
python3 -I -S -B scripts/check-post-publication-custody.py  # dated mainline/cleanup record
python3 -O -I -S -B scripts/check-post-publication-custody.py
python3 -I -S -B scripts/check-post-publication-custody-self-test.py  # 56 hostile mutations + isolation controls
python3 -O -I -S -B scripts/check-post-publication-custody-self-test.py
scripts/check-post-publication-custody-pdf-self-test.sh  # 2 controls + 31 hostile cases
scripts/check-post-publication-custody-pdf.sh --exact    # exact-only two-build/PDF-byte gate
python3 -I -B scripts/check-mathematical-results-guide-prose.py  # selected editorial subset; no ASD-STE100 conformance claim
python3 -O -I -B scripts/check-mathematical-results-guide-prose.py
python3 -I -B scripts/check-mathematical-results-guide-prose-self-test.py  # 59 hostile/control cases
python3 -O -I -B scripts/check-mathematical-results-guide-prose-self-test.py
python3 -I -S -B scripts/normalize-mathematical-results-guide-pandoc-tex-self-test.py  # 4 positive + 214 rejected subprocesses
python3 -O -I -S -B scripts/normalize-mathematical-results-guide-pandoc-tex-self-test.py
# historical 16-page v1 hosted raw profile: 2 controls + 67 hostiles = 69
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
python3 -I -B scripts/check-mathematical-results-guide-pdf-structure-v2-self-test.py  # 70 object + 1 raw + 4 diagnostic + 4 path controls
python3 -O -I -B scripts/check-mathematical-results-guide-pdf-structure-v2-self-test.py
scripts/check-mathematical-results-guide-pdf.sh --exact  # raw repeated-build and rebuilt/committed guide bytes
# The current reviewed 23-page v2 profile accepts only its closed Ubuntu 24.04/x86 producer tuple
# and retained raw-fixture relation. Exact mode remains same-toolchain byte identity. The retained
# v2 fixture came from translated local x86 execution; native hosted replay remains pending and has
# no hosted-execution credit. Retained 16-page v1 packages are historical replay evidence only.
scripts/check-mathematical-results-guide-pdf.sh --cross-toolchain
scripts/check-numerical-assurance-pdf.sh --exact  # represented-binary64 assurance, 23 pages
scripts/check-numerical-assurance-pdf.sh --cross-toolchain
scripts/check-numerical-assurance-pdf-self-test.sh  # 1 contract + 3 accepted + 32 hostile controls
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
# replays four live-applicable routes, invokes the current catalog gate, and retains superseded
# claim-only/release-only plus the frozen catalog route only through exact-tree replay. Its
# self-test has 36 controls.
python3 -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation.py
python3 -O -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation.py
python3 -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation.py --historical-tree-replay
python3 -O -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation.py --historical-tree-replay
python3 -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation-self-test.py
python3 -O -I -S -B scripts/check-ksg-harmonic-revision-v4-preservation-self-test.py
# Binds the current public revision index to the exact terminal C12 boundary. This successor
# independently derives Q12=false for both possible Boolean L12 values while retaining
# L12=not_adjudicated, R12=permanently_unissued, and zero qualification credit. It does not read
# or reactivate the historical active packet or claim-only route. Its hostile suite has 54 controls.
python3 -I -S -B scripts/check-ksg-revision4-terminal-index.py
python3 -O -I -S -B scripts/check-ksg-revision4-terminal-index.py
python3 -I -S -B scripts/check-ksg-revision4-terminal-index-self-test.py
python3 -O -I -S -B scripts/check-ksg-revision4-terminal-index-self-test.py
# Replays the immutable C3 checkpoint as both a clean commit and its exact parent-plus-overlay
# candidate, then replays the settled hosted-follow-up gate at its own immutable direct-child
# commit. The historical lifecycle is required by the hostile suite that creates test commits;
# neither replay adjudicates the current descendant.
# The wrapper normalizes its child-checkout umask to 022 before cloning; its mktemp root stays 0700.
scripts/check-ksg-c3-checkpoint.sh
# The follow-up runner freezes source size+SHA-256 and the self-test binds the actual child mode.
# Diagnostic checker output is explicitly no-credit. The historical f6 contract accepted only its
# exact implementation child through the immutable wrapper above; it required any then-later
# descendant to have a separate acyclic receipt and hosted run. That successor instruction is now
# closed history. It does not open a route after the exact-C12 terminal boundary stated above.
# The reviewed overlay is exactly 13 paths (eight modified and five added), leaving 552 immutable
# anchor paths protected. Its SxPID2 claim-checker edit is exactly three mutable-container digest
# rebindings. The source inventory has 109 hostile cases in 18 bookkeeping families and declares
# 88 mutation-target verifier launches (86 checker and two self-test), plus 22 local receipt cases
# and 38 separately named, non-mutation harness controls. The verifier runtime is restricted to
# GIL-enabled CPython 3.11 through 3.14 with one enumerated Python thread; see scripts/README.md for
# the explicit signal, preexec, waiter, native-thread, and hard-deadline nonclaims. The immutable
# wrapper supplies the exact historical f6 lifecycle; descendants receive no credit from it.
# Historical M1a phase-checker replay, separate from the historical C3/f6 wrapper above. These
# commands test the archived policy parser and its hostile controls only. They do not open an M1a
# lifecycle, accept a descendant, or grant execution, qualification, hosted, scientific, or
# publication credit. The exact-C12 terminal refusal/preservation boundary above is current.
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
python3 -I -S -B scripts/check-worktree-and-branch-retirement-ledger.py
python3 -O -I -S -B scripts/check-worktree-and-branch-retirement-ledger.py
python3 -I -S -B scripts/check-worktree-and-branch-retirement-ledger-self-test.py
python3 -O -I -S -B scripts/check-worktree-and-branch-retirement-ledger-self-test.py
python3 -I -S -B scripts/check-sibling-registry-retirement-ledger.py
python3 -O -I -S -B scripts/check-sibling-registry-retirement-ledger.py
python3 -I -S -B scripts/check-sibling-registry-retirement-ledger-self-test.py
python3 -O -I -S -B scripts/check-sibling-registry-retirement-ledger-self-test.py
scripts/check-public-api-snapshots.sh                    # rebuild immutable declaration evidence
scripts/check-release-state.sh review-source v0.9.0       # current source-review metadata truth
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

The historical 13-gate repository/publication disposition remained **NO-GO** throughout M1a. Its
then-applicable commit/push/M1c sequence is closed history, not current operational guidance. Do
not create, replay, or promote an M1a/M1c descendant to bypass or reinterpret the exact-C12
terminal record. For the current authority and chronological evidence map, use
`claims/KSG-INTEGER-HARMONIC-001/revision-index.md` and
`audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md`; the only repeatable exact-C12 route is the
preservation command stated above. Preserve the negative paths and checker repairs in the
revision-4 correction ledger and failure memos. Advisory external-model material is process
evidence, never claim evidence.

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
covers the practical local subset. Use the broader `just release-audit` only for a release or a
current lifecycle that requires it, after checking its modes and prerequisites. Use the
release-state check's `candidate` mode only for a tree whose metadata declares that state.

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
- **PID2 represented coordinates are a separate numerical layer:** `Pid2Result::from_estimate`
  gives the four already represented inputs one exact-sum synergy meaning, then applies the
  project-defined inclusive 32-position reconstruction guard. Preserve its input/atom/identity
  error split, signed-zero rules, and exact reducer. Use
  [`PID2_REPRESENTED_COORDINATE_ASSURANCE.md`](PID2_REPRESENTED_COORDINATE_ASSURANCE.md) and the
  revision-4 checker before changing it. This is not an estimator-attainability, calibration,
  support, paper-defect, or Rust-refinement theorem.
- **Negative atoms are real:** `I^sx_∩` (and its atoms) can be negative; never silently clamp.
- **SxPID3 event syntax is semantic:** in the MGW construction, the event is an OR across source
  collections and an AND within each collection. Equation (4)'s OR is the singleton-collection
  special case; it does not replace the within-collection conjunction in Equation (6). Source-label
  permutations are also distinct from reordering the branches of one antichain. The Program-A v4
  checker reconstructs this finite three-source model and binds its local record; it does not
  independently interpret the paper, prove Rust refinement, or close any Program A--E.
- **Acceptance-bearing Python equality is typed:** Python value equality is not exact evidence
  equality because `False == 0` and `5.0 == 5`. Checks of decoded JSON records and parsed frozen
  Python registries must compare shape, exact type, and value recursively; JSON parsers must also
  reject duplicate keys. Add causal normal/optimized hostile tests for discovered coercions, and
  preserve the pre-correction bytes and minimal witnesses as named negative evidence. Such a repair
  strengthens the verification chain; it does not upgrade the mathematical result, Program status,
  source correspondence, or checker independence.
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

Complete one coherent milestone and run its applicable causal, source-consistency, package, and
scientific gates. Use the mandatory Rust/API and publication checks stated above when those
surfaces change. Record exact inputs, commands, results, and remaining obligations. Keep expected
diagnostic NO-GO results and lifecycle refusals separate from passing checks. Do not omit a failing
applicable gate or reinterpret a closed failure as permission to proceed.

Reconcile the changed code, proofs, claims, and publications. Update `CHANGELOG.md` under
`[Unreleased]` for the accepted change, keep the commit small and unsigned, and push under the
established authorization. Verify the pushed object and required hosted workflows at its exact
SHA before advancing main. Then follow the ancestry, lease, preservation, and exact-mainline
hosted-check procedure above. A side-branch preflight does not satisfy the mainline evidence gate.
Update the handoff with the result and remaining work.

For security issues, follow `SECURITY.md` and do not open a public issue. See `CONTRIBUTING.md`
for the full contributor guide.
