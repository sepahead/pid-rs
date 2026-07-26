# Active completion-run resume manifest

## Status and authority

Updated: **2026-07-26**. Active branch: `main`. Parent durable commit when this manifest was written:
`56fefea64b813c16f4d1debaabf74f866a03f5d8` (`audit: add durable completion run ledger`), pushed
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

## Active workstream: PID2 represented-sum hardening

Active claim: `PID2-REPRESENTED-SUM-001`, revision 3. This is a binary64 checked-constructor
contract for the four represented PID2 coordinates; it is not a defect, theorem, attainability
claim, or calibration result for the MGW functional.

Read now:

- `claims/PID2-REPRESENTED-SUM-001/{revision-index.md,claim-v3.md,correction-ledger-v3.md,
  obligations-v3.md,routes-v3.md,evidence-matrix-v3.md,decision-v3.md}`;
- all files under `claims/PID2-REPRESENTED-SUM-001/failures/` and the separately pinned
  `acceptance-monotonicity-v2.md`;
- `scripts/check-pid2-represented-sum.py` and
  `scripts/check-pid2-represented-sum-self-test.py` at the exact regions being edited;
- `crates/pid-core/src/pid2.rs`, `crates/pid-core/src/stats.rs`, and PID2/statistics tests at the
  exact constructor, guard, rustdoc, and baseline-test regions; and
- the six exact method-catalog entries and their generated `METHODS.md` rendering only when the
  catalog milestone starts.

Verify, but do not edit, the frozen revision-2 hashes:

```text
b11a5443fd3c7a44e4e7991213a4ec080a94216e4c669ad1f00e7547185c82a4  claim-v2.md
677027d15cc3bee9f9dafe5cb30903293ff11c91ef103a36f4554b818ef1f605  obligations-v2.md
8b0171ce7ffe9820746ed228a2e743cae34472f1b784b943208f821a0badf042  routes-v2.md
7852d1677191125715e68ef8b80ac7e7a340a1d7ed11f3ca5615a81599160d57  evidence-matrix-v2.md
5fe09195bcb67f909fbe0153bd0cd352128dd60da83bd241615b607f21713b6b  decision-v2.md
```

Settled facts to preserve:

- `Red=R`; `U1=RN(I1-R)`; `U2=RN(I2-R)`;
  `Syn=RN-even(exact[J,-I1,-I2,R])`.
- The checked constructor exactly accumulates and once rounds the three represented
  reconstructions, rejects a non-finite reconstruction, and accepts ordered-binary64 distance
  **at most 32**, inclusive.
- Field/path zero semantics are local: redundancy copies `R`; uniques follow subtraction; exact
  synergy and exact-accumulator cancellation canonicalize exact zero to positive zero.
- Exact-only acceptance is a strict subset of the historical hybrid constructor on the same
  inputs. Coordinate-scale acceptance monotonicity is separately refuted by the exact times-two
  overflow-midpoint witness. The false static `16*|J|` condition is separately retained.
- The target after truthful hardening is 129 registered mutations and 18 compiled baseline tests.
  Textual source mutations are not compiled kills. The omitted eighteenth baseline is
  `stats::tests::exact_binary64_sum_matches_independent_fraction_oracle_under_all_permutations`.
- `source` scope must not run arithmetic and each scope must print an exact, scope-specific claim.
  `all` remains the conjunction. Both normal Python and `-O` must test stdout and scope isolation.
- Six catalog methods still bind revision 2, so `catalog` and `all` correctly remain red until the
  catalog milestone. Do not report the present 125-mutation suite as replayed green because its
  unmodified aggregate preflight stops before executing mutations.
- `Pid2Result` is `#[non_exhaustive]`, so safe downstream Rust cannot create it de novo with a
  struct literal. Its public fields remain mutable, however, so the invariant is not type-enforced
  after construction. Guarantees apply at the checked `Pid2Result::from_estimate` return boundary
  and to production paths that do not subsequently mutate the fields, not to every extant value.

Exact stop point: governing/relevant state has been replayed after the thirty-second compaction;
no PID2 source, checker, catalog, release, or identity edit has occurred since commit `56fefea`.
The next edit is the isolated-scope/exact-stdout/18th-baseline checker milestone, followed by its
normal/optimized preflight tests. Parallel read-only audits are active for the four new mutations,
honest source-mutation classification, Rustdoc, and debug/release baseline contract.

## Long-horizon milestone queue

This table is the durable to-do authority after compaction. Advance a row only with the named exit
evidence; never infer completion from effort, elapsed time, model agreement, or an unrelated green
test. Update the exact stop point above whenever work is interrupted.

| ID | Milestone | State | Next advancing action | Exit evidence |
|---|---|---|---|---|
| M0 | relevance-bounded recovery and durable planning | active until this process commit is pushed | review these two process files, whitespace-check, commit, push | pushed unsigned commit; next resume authenticates manifest and bounded routing |
| M1 | PID2 checker/source hardening | next | isolate scopes; pin stdout; route baseline 18; add four model mutants; fix mutation labels; harden Rustdoc | 129 registered mutations truthfully classified; 18 named compiled baselines; normal and `-O` scope/preflight replay; focused Rust tests/rustdoc |
| M2 | PID2 catalog/evidence/release closure | pending on M1 | migrate exactly six catalog bindings from retained revision 2 to active revision 3; regenerate derived docs | catalog/all green; mutation suite executes; method catalog/review evidence/release scope agree; frozen hashes unchanged |
| M3 | KSG harmonic assurance integration | pending on M2 | activate only `KSG-INTEGER-HARMONIC-001`; bind 20 methods and six arithmetic-owning formal routes | Lean/Z3/checker/mutations/CI/catalog/release wording and receipts replay with qualified scope |
| M4 | categorical SxPID3 Programs A--E | pending on M3 | activate proposed SxPID3 packet; freeze producer and independent-verifier interfaces before code | all 108 coordinates bound through event/count/Mobius/certificate/compiled/archive routes; bounded corpus and mutations replay; open gates stated |
| M5 | publishable PID discovery/orchestration methods paper | pending; specification pinned above | literature/source map, frozen paper outline, process schema, and independent hostile-method review | canonical Markdown/LaTeX parity; citations checked; case evidence reproducible; schema mutations killed; no novelty/evidence overclaim |
| M6 | comprehensive scientific PDFs | pending on settled source artifacts | generate each PDF from canonical sources, extract text, render every page, inspect, and bind hashes | complete-detail semantic parity plus zero visual defects and reproducible render receipts |
| M7 | final release/identity/cross-repository closure | pending on M1--M6 | run full CI/release/identity/archive matrix; then inspect each sibling repo independently | all pid-rs gates green on settled bytes; scoped dispositions; small main commits pushed; only clean/authorized sibling changes pushed |

The active lifecycle goal tool remains paused and cannot change its objective text without replacing
the unfinished goal. This queue records the user's later Wibral, formal-assurance, publication,
PDF, compaction, and small-milestone requirements without falsely completing or replacing it.

## Deferred routing table — do not load until activated

| Workstream | Entry point when activated | Current boundary |
|---|---|---|
| KSG harmonic integration | `claims/KSG-INTEGER-HARMONIC-001/` | narrow exact arithmetic only; catalog/formal/release wiring open |
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
