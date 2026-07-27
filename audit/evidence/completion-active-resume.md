# Active completion-run resume manifest

## Live checkpoint — durable KSG recovery and assurance hardening — 2026-07-27

This section supersedes every temporary-worktree path below. Lifecycle goal
`019f9ec9-2763-7ae3-9532-2169a23307f0` remains active. Read, in order:

1. `codex-goal-prompt-2026-07-26.md`, SHA-256
   `dc984b2586970c71a6eafe262604dd9e8d6b988723a8aa6b46df8ae7d58adab2`;
2. `completion-handoff-2026-07-26-ksg-rev4.md`, SHA-256
   `61ba9897f7323a88bccc9f683d752cbb0a1408e1ec71268615c5619d9aeacf29`;
3. `ksg-rev4-recovery-ledger-20260727.md` and its JSON companion; and
4. this live section. Load older narrative only to resolve a named provenance conflict.

The durable candidate is:

```text
/Users/torusprime/Development/sepahead-github/pid-rs-ksg-rev4-candidate
branch: codex/ksg-rev4-candidate-20260726
HEAD:   118e1de6a2d6d2ae33fe7bdc224736257e42a83f
origin/main at recovery: 118e1de6a2d6d2ae33fe7bdc224736257e42a83f
```

The ambient checkout remains the preserved mixed multi-wave tree and must never be staged
wholesale. The absent `/private/tmp/pid-rs-ksg-rev4.E11L9g/tree` path is historical only.

### Durable state and evidence credit

Recovery checkpoint 1 is:

```text
ref:    refs/codex/checkpoints/ksg-rev4-recovery-source-1
commit: 94813b96990ae9ec2b9f2db368fe06e2de797dd6
tree:   04669a046910c7fa7f4e33cedca31aecd402a03d
bundle: /Users/torusprime/Development/sepahead-github/pid-rs-recovery-checkpoints/
        ksg-rev4-recovery-source-1.bundle
bundle SHA-256: 7b0bf3c63d82e28b58fd9a0150d2c6878adade08db4ba33a03ef92529ead295a
```

Recovery checkpoint 2 seals the byte-recovery-complete tree:

```text
ref:    refs/codex/checkpoints/ksg-rev4-recovery-complete-2
commit: 7eb959e3e3fd4bc2893cef83e6728b1594f8691b
tree:   423dd61a5284717db41a7dbda5702f7d81bd48f7
parent: 118e1de6a2d6d2ae33fe7bdc224736257e42a83f
paths:  109
bundle SHA-256: 23a1db4ae281c03723094093c4fa9e726867d07fd6406847f29542ec418f8078
external receipt SHA-256:
858c429e91418a3883cfd62a755c4da32dbb5be4c1fe7b801cef86930f83f6e2
```

The bundle was restored into a new durable bare repository; commit, tree, parent, strict `fsck`,
and source/restored archive digest all matched. This is recovery integrity, not authenticity,
scientific verification, or release closure.

Every lost preclosure byte has now been reconstructed and hash-verified. In particular:

```text
21a08acd99bfc5c5881a6d267382bc808075fb69bca9ae6f76b103775c5f3ee3  old Fable context
cfdf84ba5ca1e51c215b7785d577c7378e4836d213de12230caf5449f33e010b  old Fable receipt
b4cac94ca6b636d8f5433bc3e2112f5cee7c118aa60cff9a321ea1fdcaf7dd9a  old Fable response
```

The offline recovery program and 31-artifact manifest are stored beside those records. The
recovery used no network or `.env` access and passed secret-pattern, byte-count, UTF-8, and digest
gates. It recovers historical bytes; it does not rerun the model or establish integration.

The fresh max-effort Fable sweep attempted all five configured aliases. Three advisory reviews
completed (137339 output tokens, 100885 thinking tokens); two aliases returned insufficient-credit
HTTP 400. Receipt SHA-256:
`8f3308ecc873628bd675df3e974593eb130e855e591def8ce25e001fde56327b`.
Do not retry exhausted aliases merely to seek agreement. Continue with native agents and local
proof/numerical tools. No model output is proof.

Normal/optimized Z3, modular-certificate, directed-enclosure, and claim-only runs matched recorded
outputs after recovery. They are diagnostics, not final passes. Lean failed closed because the
former temporary Mathlib dependency checkout was absent; a pinned rebuild is in progress. Only a
complete replay after all writers stop on the exact isolated staged tree can support GO.

The old and fresh model allegations have been independently adjudicated in
`fable5-ksg-rev4-adjudication-20260727.{md,json}`. The human rendering SHA-256 is
`19d284f357eaaecdd63580663c184838f6d31b09fac01d4f08c90e177bb4afec`; the machine rendering
SHA-256 is `0fa2904476cd400720a752e497c8e463a4c54855d1f3091eeae89cb61b4c2919`.
The adjudication found no new bounded-core blocker. It accepted targeted hardening, rejected the
false universal `1/(n-1)` nonzero gap and the unproved universal `28 epsilon` claim, and preserved
all deferred routes as non-evidence.

### Current scientific disposition

The bounded positive-integer KSG arithmetic core remains GO on its declared exact and finite-corpus
domains. Repository/publication integration remains NO-GO. Do not transfer this result to KSG
consistency, continuous Ehrlich shared exclusions, continuous PID2, categorical MGW SxPID, I_min,
fitted quantization, PID3, wrappers, consumers, or applications without a separate mapping theorem.

The highest-priority open obligations are:

1. add a kernel-checked analytic/recurrence bridge for the digamma premise if the pinned Mathlib
   theorem really supports it; publish `#print axioms`, a subtraction-free statement, mutations,
   and shared cuts;
2. turn the independently checked all-unique W2 endpoint counterexample into a compiled regression,
   distinguish structural-zero endpoints from range extrema, and replace ambiguous “maximum
   harmonic denominator” prose with “maximum reciprocal summand denominator/index”;
3. harden phase isolation to use the current pushed anchor, an independently reviewed `A`/`M`
   policy, no deletions, exact ordered critical calls, strict Git/config/attribute custody,
   metadata replay, and an external tested-tree receipt;
4. regenerate moving claim/catalog/release/review/ecosystem/identity facts only after the preceding
   bytes settle; and
5. run every formal, mutation, exact, binary64, Rust debug/release/serial/parallel, docs, Python,
   release, security, and isolated-tree gate before a small unsigned fast-forward push.

Fable's proposed cvc5 proof objects, Kani/CBMC, Gappa/Flocq, MPFR/Arb, TLA+/Alloy, statistical
bounds, and exact categorical prime-log vectors are research tasks, not accepted results. A method
enters the evidence matrix only after its exact obligation, bridge, trust base, mutations, and
boundedness are demonstrated. The proposed exact prime-log representation is especially promising
for later categorical MGW SxPID3 but is not a KSG theorem.

### Compaction rule

After context compaction, reload only the four authorities at the start of this section, query the
active goal, inspect `git status --short --branch`, list agents, and authenticate the latest
checkpoint/bundle receipt. Do not reload whole model transcripts or deferred PID packets. Expand
only for a named disputed obligation. Before any stop or commit, update this live section and the
recovery ledger with exact paths, hashes, negative results, and the next executable action.

## Live checkpoint — KSG revision-4 preclosure integration — 2026-07-26

Read `completion-execution-plan-2026-07-26.md` and
`completion-handoff-2026-07-26-ksg-rev4.md` before the older narrative below. Lifecycle goal
`019f9ec9-2763-7ae3-9532-2169a23307f0` is active. The clean candidate is
`/private/tmp/pid-rs-ksg-rev4.E11L9g/tree`; the ambient checkout remains a preserved, contaminated
multi-wave worktree and must not be staged.

Candidate `HEAD` and `origin/main` are
`118e1de6a2d6d2ae33fe7bdc224736257e42a83f`
(`audit: record KSG formal milestone receipt`). The local `main` ref in the ambient worktree
remains at the delivery parent `9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56`; do not update it by
checking out or merging the mixed ambient tree. The M1a implementation commit is the unsigned
`afc45ff27e5af7fe04e44f2bb9f4147fb472c81e`.

The exact arithmetic core remains GO on its declared domain; repository/publication integration
remains NO-GO. The isolated candidate now contains the KSG-only production reassociation, W1/W2
bridges, recaptured 12-test serial/parallel constants, canonical modular and exact-enclosure
routes, revision-4 preclosure claim custody, 20-method catalog / 15-family release propagation,
review and ecosystem bindings, software identity, audience documentation, and KSG-only
automation. The active packet SHA-256 is
`aa88850c46644f899538bfeef0445f62b048e39a4c71e07f62a6cca04a740108`
and explicitly says `integration_no_go`.

Current bounded counts are: 19 Lean theorems / 14 mutations; four Z3 obligations / 12
countermodels; 8,198 corpus rows; 354 structural endpoints / 7,844 nonendpoints; 26 modular
mutations; 6,920 exact `Fraction` containments / 29 enclosure mutations; 49 claim mutations; and
161 integration mutations plus two scope-isolation preflights. The rounded-reference maximum is
exactly `8 * f64::EPSILON` nats on 40 rows. Under the stated Python `Decimal`
directed-rounding premise, the exact-rational maximum is uniquely below
`9.761311 * f64::EPSILON` nats. These are local arithmetic facts, not Rust-refinement, neighbor,
estimator, support, Ehrlich/MGW PID, calibration, or consumer theorems.

Hostile source and claim/document reviews found no remaining arithmetic or semantic defect after
their corrections. The full Rust profile matrix was green; Clippy subsequently found one
test-only range-loop warning, which was corrected and followed by green affected source/oracle,
Clippy, and rustdoc replays. The final full settled-byte replay is still required.

The immediate order is:

1. finish and hostile-review the exact Git phase checker and its mutations;
2. stop all writers, recustody moving hashes, and run the complete settled-byte gate matrix;
3. rerun the final generous Fable 5 review on the settled facts and independently adjudicate it;
4. construct and verify the alternate-index commit from the declared parent;
5. commit unsigned, fast-forward push `main`, then add immutable evidence/decision receipts without
   overstating the bounded arithmetic result.

## Status and authority

### Manual-resume handoff override — 2026-07-26

The user requested a comprehensive `/goal` handoff and a clean stop. Before using the older active
workstream narrative below, read these two newer authorities completely:

1. `audit/evidence/codex-goal-prompt-2026-07-26.md` — the detailed objective to pass to `/goal`;
2. `audit/evidence/completion-handoff-2026-07-26-ksg-rev4.md` — exact scientific state, hashes,
   failures, contamination boundaries, agent stop reports, and milestone exit criteria.

They supersede the older revision-2/91-mutation stop description below. The active KSG arithmetic
core is mathematically GO on its declared bounded domain, but repository/publication promotion is
NO-GO. Frozen revision 3 failed pre-closure audit; revision 4 is required. The multi-wave ambient
worktree must not be committed wholesale. The dedicated formal checkers are temporarily
incoherent with newly revision-scoped v4 Lean/Z3 paths, generated catalog/release views and software
identity are stale, no settled full mutation replay is creditable, and no isolated KSG candidate
has been synthesized. Resume from the handoff, not from an earlier green line.

Updated: **2026-07-26**. Active branch: `main`. Parent durable commit when this manifest was written:
`626ded7b24c62e24ee6cdda21b04bec63675272b` (`audit: bound durable compaction recovery`), pushed
to `origin/main`.

This mutable file is the first document to read after context compaction. It is process state, not
scientific evidence. The append-only historical record remains
`completion-run-ledger-2026-07-25.md`; claim packets, formal artifacts, certificates, compiled
tests, and release gates remain the authorities for their own evidence classes. Never use this
manifest to promote a theorem, estimator, implementation, or consumer disposition.

Authority order for the active work is:

1. current system/user instructions and `AGENTS.md`;
2. `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md` and the active frozen claim revision;
3. replayable source, exact counterexamples, formal/certificate artifacts, tests, and checkers;
4. this coordination manifest and the historical ledger; and
5. audit reports and Fable/Opus outputs as recommendation or attack input only.

## Bounded bootstrap after compaction

Do not reload the whole project history by default.

1. Read this file completely. Query `get_goal`; run `git status --short --branch`; list native
   agents. Confirm the last commit and exact stop point below.
2. Authenticate the governing files. Current expected SHA-256 values are:

   ```text
   d7b161e749d21e6df64d54e2ce969f4115586c8f78b04d09bc174ac19e8c9830  AGENTS.md
   717015b862995b1003d66badceccfc4535f5bb231681212a9b2ceff3b8204f94  MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md
   7c4aec062863c88f496176188eaace3baaae06201e2c85aa2c1ed200ac1d1330  final Wibral audit Markdown
   ```

   If `AGENTS.md` or the workflow digest differs, read the changed file completely and update this
   manifest before acting. If unchanged and their contents are already present in the resumed
   prompt, apply them directly; otherwise read `AGENTS.md` and the workflow's protocol portion
   beginning at `## AI model operating protocol`. The source-observation history is not a routine
   compaction dependency.
3. Read the complete **active revision**, obligation graph, routes, evidence matrix, decision, and
   every retained failure named in the active-workstream section below. Verify frozen historical
   hashes without rereading historical prose unless custody fails or a semantic diff is disputed.
4. Read only source/checker/catalog/release regions named below. A truncated read is rejected; use
   bounded calls. Do not run broad repository searches when an exact path or symbol is known.
5. Reconstruct the current decision through at least five applicable lenses. For PID work the
   default set is semantic/estimand, exact mathematical, formal/certificate, binary64/numerical,
   compiled executable, statistical, provenance/release, and downstream-authority. Record shared
   proof cuts; model-name agreement is not independence.
6. Continue `review -> plan -> edit -> implement -> test -> verify`. Preserve counterexamples,
   failed routes, open obligations, negative atoms, frozen revisions, and first-result records.
7. Before a coherent milestone commit, update this file's stop/test/queue fields and append a
   short delta checkpoint to the historical ledger. Commit unsigned, without agent attribution,
   and push `main`. Record the resulting commit in the next advancing milestone; a file cannot
   truthfully contain the hash of the commit whose bytes include that file. Do not append
   repetitive full-replay narratives.

Expansion rules prevent stale context:

- load another claim packet only when its workstream becomes active or a shared dependency must be
  audited;
- load an old audit/report only to resolve a named provenance or recommendation question;
- load an external model transcript only to adjudicate a specific retained attack;
- if bytes, counts, or results conflict, stop promotion, retain both records, and reopen the
  smallest disputed obligation; and
- when switching workstreams, replace the active-workstream section and move the old state into
  one ledger delta rather than accumulating multiple active narratives here.

## Scientific invariants carried across every compaction

- The primary scientific object is Makkeh--Gutknecht--Wibral shared-exclusions PID. `I_min`, KSG,
  categorical SxPID, continuous shared exclusions, fitted quantization, and incomplete/full PID3
  are distinct objects until an explicit mapping theorem closes the transfer.
- Freeze domains, ranges, quantifier order, assumptions, units, non-solutions, falsifiers, evidence
  classes, and completion checks before changing a scientific result.
- Separate exact-real mathematics, formal semantics, certified numerics, Rust conformance,
  statistical calibration, consumer qualification, release identity, and external custody.
- Major claims require dependency-aware independent routes, a counterexample route, mutation
  assurance, and an adversarial audit. A formal proof of a surrogate or a test of bounded cases
  cannot close a stronger statement.
- Continuous support is declared, not inferred. Added noise changes the estimand. Negative SxPID
  atoms are valid. Information units are nats. PID atom construction must not clamp MI terms.
- Preserve negative/open results. Exact-versus-Neumaier PID2 guard equivalence remains open; a
  failed search is not evidence.
- Scientific PDFs are release artifacts and must contain definitions, assumptions, domains,
  ranges, full derivations, obligations, counterexamples, negative/open results, implementation
  correspondence, independent-method cuts, hashes/receipts, limitations, and replay commands.
  Render and visually inspect every page and check semantic parity before release.

## Publication-grade PID discovery and assurance protocol

The scientific process itself is a required publication artifact, not merely internal agent
instructions. It will be authored as a canonical Markdown methods paper with a semantically paired
LaTeX/PDF rendering. The paper must be reproducible, falsifiable, and useful to an expert team
without access to this conversation. It must include:

1. a precise problem class for mathematical/statistical PID claims and an explicit firewall among
   MGW shared exclusions, other PID functionals, estimators, implementations, and consumers;
2. frozen-claim construction, quantifier/domain/range/assumption tables, non-solutions,
   falsifiers, and version-preserving correction rules;
3. AND/OR obligation hypergraphs, minimal critical-cut-set accounting, dependency-aware evidence
   independence, and a formal rule for when multiple agents count as one route;
4. agent roles, task decomposition, dispatch/decision gates, information-flow controls,
   source-blind and proof-blind attacks, conflict escalation, liveness/termination criteria, and
   durable handoff/recovery semantics;
5. the complete discovery loop from conjecture generation through exact reduction, certificate
   construction, formalization, compiled refinement, statistical calibration, and release;
6. adversarial review across semantic, combinatorial, analytic, probabilistic, formal, numerical,
   compiled-executable, statistical, provenance, resource, portability, and downstream-authority
   lenses;
7. negative-result and failed-route retention, smallest-witness minimization, mutation design,
   correction-ledger dependency reach, and reopen conditions;
8. evidence aggregation without pseudo-independence, including shared oracles, shared imported
   theorems, shared generators, shared source text, and correlated model families;
9. worked pid-rs case studies covering a successful bounded bridge, a false transfer between PID
   definitions, a binary64 threshold counterexample, a mixed-rank estimand obstruction, an open
   failed discriminator search, and a proposed frontier claim that remains NO-GO;
10. measurable process outcomes and limitations: defect discovery, mutation sensitivity, replay
    coverage, wall/compute cost, unresolved obligations, specialist-review boundary, and threats
    to validity; and
11. executable schemas/checklists, artifact and digest conventions, exact replay commands, and a
    page-by-page PDF semantic/visual verification record.

This paper may describe a project-defined research protocol and report scoped case-study evidence.
It must not claim that orchestration guarantees truth, that model agreement is mathematical
evidence, that the process is scientifically novel without a literature review, or that a bounded
pid-rs result validates an unbounded theorem. Before release it requires independent hostile
methodological review, citation/source checks, exact correspondence to the live workflow and claim
packets, negative mutations of its machine-readable schema, extracted-text parity, and rendered
page inspection under the PDF workflow.

## Active workstream: KSG integer-harmonic integration

Active claim: `KSG-INTEGER-HARMONIC-001`, revision 2 retained as the frozen pre-implementation
claim/evidence decision. The active decision is whether the completed implementation and expanded
mutation evidence require a new revision 3 and how to land a KSG-only release milestone before
PID2. This is a narrow integer-argument arithmetic and bounded binary64 result used by KSG and the
continuous shared-exclusions estimators. It is not a theorem about estimator consistency,
population support, MGW PID atoms, or downstream statistical validity.

Read now:

- `claims/KSG-INTEGER-HARMONIC-001/{revision-index.md,claim-v2.md,correction-ledger-v2.md,
  obligations-v2.md,routes-v2.md,evidence-matrix-v2.md,decision-v2.md,behavioral-witnesses-v2.md,
  formal-assurance-v2.md,implementation-v1.md,call-site-map.md}`;
- every file under `claims/KSG-INTEGER-HARMONIC-001/failures/` plus the route memo and its v2
  erratum;
- `scripts/check-ksg-harmonic-revision.py` and
  `scripts/check-ksg-harmonic-revision-self-test.py` completely before changing their contract;
- the Lean/Z3 KSG checker and mutation scripts, their exact source artifacts, and only the
  `stats.rs`, `ksg.rs`, `isx.rs`, `pid3.rs`, fixture, generator, and test regions they bind; and
- the 20 catalog entries, 15 release families, review-evidence records, CI/just wiring, and
  software-identity reference only when constructing the isolated KSG milestone.

Verify, but do not edit, these current revision-2 hashes:

```text
2a114fca75c52d65410bc2b80bd561c7a1858035d5643a2d660044a53823f7f3  claim-v2.md
2c108aef29e833a6bf9f41968f917ad05b645606b377fc55ff3b0f9bccc1d389  obligations-v2.md
5cfe75c9572ee7742a2428dcd119018a6ae1bd92c7cfb1ed0bce5257f7691ab5  routes-v2.md
6b750c010a00debde29ec2b3959e1bd55751f7ebe9c136beac202503b1b6196c  evidence-matrix-v2.md
540d7f468bbcbc8771adeae8ce3ee103dad5d98d7bc5298a8c1e91a67a19fd26  decision-v2.md
0c65acef2b96bcac208be78a1d781bccb6c079b249076544d2227b3634e5b61b  correction-ledger-v2.md
e8e3d936d94bc25ed1eaa49e22d3cbdee0e65a649192f613e76dce8c22a99151  behavioral-witnesses-v2.md
1068d90dcfe7a20b5237305c0468a6a74eedeb5b91196ff6bfe9969dec300c10  formal-assurance-v2.md
```

Settled facts and live discrepancies to preserve:

- For positive integer `m`, `psi(m)=H_(m-1)-gamma`; hence for `n>=2`, `1<=k<n`, and valid
  integer arguments `x,y`, the four-term score is
  `H_(k-1)+H_(n-1)-H_(x-1)-H_(y-1)` with coefficients `(+1,+1,-1,-1)` in nats.
- Exclusive KSG counts require `k-1<=nx,ny<n` and use `x=nx+1`, `y=ny+1`. Inclusive Ehrlich
  shared-exclusions counts require `k<=x,y<=n` and pass the arguments without a successor. These
  domains and mappings are not interchangeable.
- The selected Neumaier-prefix plus symmetric-range binary64 implementation has, on the frozen
  8,198-cell Decimal corpus, maximum absolute error `8*EPSILON` nats, 40 maximum-error ties, and
  zero source-swap asymmetries. The allowed `32*EPSILON` absolute gate is bounded evidence, not an
  ULP bound, a correct-rounding theorem, or a universal error theorem.
- The exact `Fraction` route covers 6,920 feasible tuples through `n=16`. Lean proves 14 narrow
  exact algebra theorems conditional on the typed integer-digamma premise. Z3 checks three
  premise-explicit QF_UFLIRA obligations with uninterpreted harmonic values. Lean and Z3 share the
  analytic premise and the human sign/index mapping; neither proves binary64 or estimator validity.
- The v1 route memo incorrectly labelled 16/764 maximum-error cells as compensated. The retained
  erratum records the actual comparison: plain 8/0/39, Neumaier 8/0/39, selected symmetric range
  8/0/40. The extra selected tie is first `(4096,1,2048,2048)`.
- Live source/checker work now closes six gates that revision 2 records open: maximum-tie custody,
  generator drift and reseal custody, and three source dataflow shadows. The self-test therefore
  rejects 91 mutations (`4+2+19+66`), while revision-2 public text still says 85. Do not rewrite
  revision 2 after observing this result; issue a new revision or explicitly retain the six gates
  open.
- Four release families eventually combine KSG and PID2 revision strings. A PID2-first commit is
  false because parent `626ded7` lacks the KSG implementation. The KSG milestone must use the
  intermediate KSG-only revision for those four families; the later PID2 milestone advances them
  to the combined revision.

Exact stop point: PID2 source/checker hardening passes on the combined dirty tree with 129
registered mutations, two bidirectional scope-isolation preflights, 18 distinct compiled tests in
debug and release (36 invocations), focused Rust tests, Rustdoc, catalog, release, review-evidence,
and identity gates. It is deliberately held uncommitted until a coherent KSG parent exists. Two
external hostile reviews independently confirmed the PID2 arithmetic but found that two inventory
mutations read live artifacts while public prose says copied artifacts; that wording defect must
be corrected before PID2 release. One review additionally requested revision-1 custody, per-scope
copied-root baselines, and two pin mutations; another requested a compiled-test name mutation and
toolchain receipt. These are open hardening decisions, not silently accepted conclusions.

The active next action is to finish hostile KSG mathematical and release-slice audits, decide and
author a non-destructive revision 3 if required, harden the 91-mutation suite against false-green
diagnostics, construct KSG-only intermediate release identities, and validate the exact staged
snapshot before a small unsigned push. The full-tree clippy run is currently red only in an
unrelated uncommitted Imin boundary test (`needless_range_loop`); no KSG/PID2 scientific conclusion
is inferred from that failure.

## Long-horizon milestone queue

This table is the durable to-do authority after compaction. Advance a row only with the named exit
evidence; never infer completion from effort, elapsed time, model agreement, or an unrelated green
test. Update the exact stop point above whenever work is interrupted.

| ID | Milestone | State | Next advancing action | Exit evidence |
|---|---|---|---|---|
| M0 | relevance-bounded recovery and durable planning | complete at pushed `626ded7` | keep this manifest and append-only ledger current before every milestone | subsequent resumes authenticate the manifest and bounded routing |
| M1 | KSG harmonic assurance integration | active | reconcile frozen v2 with live 91-mutation evidence; create a retained v3 if required; land KSG-only intermediate release identities | exact/Decimal/Lean/Z3/source/compiled/mutations/CI/catalog/release/identity gates replay on an isolated staged snapshot; qualified wording; small unsigned push |
| M2 | PID2 checker/source/catalog/release closure | verified on combined tree; pending KSG parent and final hardening adjudication | replay against pushed KSG parent; correct live-vs-copied evidence prose; adjudicate domain/endpoint/custody/toolchain findings; create a new revision rather than edit frozen bytes if the claim changes | truthful mutation inventory; exact scopes normal/`-O`; compiled debug/release; catalog/release/review/identity and focused Rust/rustdoc; small unsigned push |
| M3 | categorical SxPID3 Programs A--E | pending on M2 | activate proposed SxPID3 packet; freeze producer and independent-verifier interfaces before code | all 108 coordinates bound through event/count/Mobius/certificate/compiled/archive routes; bounded corpus and mutations replay; open gates stated |
| M4 | publishable PID discovery/orchestration methods paper | pending; specification pinned above | literature/source map, frozen paper outline, process schema, and independent hostile-method review | canonical Markdown/LaTeX parity; citations checked; case evidence reproducible; schema mutations killed; no novelty/evidence overclaim |
| M5 | comprehensive scientific PDFs | pending on settled source artifacts | generate each PDF from canonical sources, extract text, render every page, inspect, and bind hashes | complete-detail semantic parity plus zero visual defects and reproducible render receipts |
| M6 | final release/identity/cross-repository closure | pending on M1--M5 | run full CI/release/identity/archive matrix; then inspect each sibling repo independently | all pid-rs gates green on settled bytes; scoped dispositions; small main commits pushed; only clean/authorized sibling changes pushed |

The active lifecycle goal tool remains paused and cannot change its objective text without replacing
the unfinished goal. This queue records the user's later Wibral, formal-assurance, publication,
PDF, compaction, and small-milestone requirements without falsely completing or replacing it.

## Deferred routing table — do not load until activated

| Workstream | Entry point when activated | Current boundary |
|---|---|---|
| PID2 represented-sum hardening | `claims/PID2-REPRESENTED-SUM-001/` | binary64 checked-constructor contract; combined-tree replay green; KSG parent, evidence wording, domain/endpoint revision, and release isolation open |
| Imin tie/swap | `claims/IMIN-TIE-SWAP-001/` | Williams--Beer object; never MGW evidence |
| two-source count/event bridge | `claims/SX-COUNT-EVENT-BRIDGE-001/` | bounded supplied-count categorical MGW bridge |
| certified SxPID2 | `claims/SX-CERTIFIED-AVERAGED-PID2-001/` | conditional bounded containment/product-sign assurance |
| categorical SxPID3 | `claims/SX-CERTIFIED-AVERAGED-PID3-001/` | proposed 108-coordinate target; Programs A--E open |
| continuous mixed-rank repair | final Wibral audit lines 242--339 and 375--382 | common-radius bridge refuted on smooth torus; replacement theorem open |
| publishable discovery protocol | `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md` plus this manifest's publication obligation | canonical methods paper, schema, adversarial review, and verified PDF open |
| comprehensive PDFs/release | LaTeX sources, output PDFs, release/identity gates | full-detail semantic and visual audit open |
| sibling repositories | `ECOSYSTEM_CAPABILITIES.md` plus each clean repo status | no cross-repo push until pid-rs authority and repo cleanliness permit it |

The older `first_pid_rs_audit_gpt5-6pro`, superseded Wibral report bodies, old compaction
checkpoints, inactive claim packets, and complete Fable/Opus transcripts are intentionally absent
from the default recovery set. Their paths remain in the historical ledger and claim packets.
