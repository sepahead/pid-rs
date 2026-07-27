# Durable execution plan — Wibral PID completion

## Status and authority

This is mutable coordination state for lifecycle goal
`019f9ec9-2763-7ae3-9532-2169a23307f0`. It is not scientific evidence and cannot promote a
claim. The normative objective is the text between the separators in
`codex-goal-prompt-2026-07-26.md`; the exact technical handoff is
`completion-handoff-2026-07-26-ksg-rev4.md`. Claim packets, formal sources, certificates,
compiled tests, primary literature, and settled release receipts remain authoritative for their
own evidence classes.

Updated: 2026-07-27. Active workstream: `KSG-INTEGER-HARMONIC-001`, revision 4 recovery,
assurance hardening, and integration.

## Immutable recovery anchors

- Scientific/protected-content baseline:
  `e96122b56c15e895c081379210103d1a26eac25f`, tree
  `fee2346732da20af0cde32844fcab527ec2d6c4a`.
- Delivery/fast-forward parent:
  `9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56`, tree
  `13b15a7564fdd52df16e2e4380f6293db4ea4367`.
- The delivery parent differs from the scientific baseline only by the four durable handoff,
  prompt, resume, and ledger paths committed in `9bbcf5`.
- Durable revision-4 candidate worktree for the current run:
  `/Users/torusprime/Development/sepahead-github/pid-rs-ksg-rev4-candidate` on branch
  `codex/ksg-rev4-candidate-20260726`, reconstructed from pushed commit
  `118e1de6a2d6d2ae33fe7bdc224736257e42a83f`.
- The ambient `main` checkout is a mixed multi-wave tree and must never be staged or committed.
- `/tmp/pid-rs-ksg-only.o80cJV` is an unchanged export of the scientific baseline, not a delivery
  candidate.
- `/private/tmp/pid-rs-oracle-worktree.21EOFe` contains later support-change SxPID oracle work and
  is excluded from KSG revision 4.
- Byte-recovery-complete checkpoint:
  `refs/codex/checkpoints/ksg-rev4-recovery-complete-2`, commit
  `7eb959e3e3fd4bc2893cef83e6728b1594f8691b`, tree
  `423dd61a5284717db41a7dbda5702f7d81bd48f7`; its verified bundle SHA-256 is
  `23a1db4ae281c03723094093c4fa9e726867d07fd6406847f29542ec418f8078`.

Before trusting a resumed run, reauthenticate these commits/trees, the frozen hashes in the
handoff, and the newest checkpoint/bundle receipt in
`ksg-rev4-recovery-ledger-20260727.{md,json}`. The missing temporary candidate is historical. Never
substitute the ambient tree.

## Scientific operating rule

For every consequential statement, record at least five applicable lenses and normally more:

1. object, estimand, domain, range, quantifier, support, units, and non-implication;
2. exact algebra/analysis/combinatorics, boundary cases, and smallest counterexamples;
3. formal proof or finite certificate, explicit premises, critical shared cuts, and mutations;
4. binary64 association, signed zero, overflow/underflow, and exact-versus-represented values;
5. compiled production dataflow across debug/release, serial/parallel, kernels, and platforms;
6. statistical identifiability, finite-sample calibration, dependence, UQ, and holdout design;
7. provenance, custody, catalogs, release identity, Git isolation, and archive reproduction;
8. citation, source-arrow correspondence, literature priority, and novelty boundaries; and
9. downstream consumer contracts plus publication semantic/visual parity.

Different agents or model names are not independent routes when they share the same premise,
source text, fixture, generator, formal statement, compiler lineage, or human transcription.
Evolutionary/genetic search, randomized search, simulation, and model review are discovery and
falsification methods. They become proof only after conversion to an exact derivation, exhaustive
finite certificate, rigorous enclosure, or accepted formal argument on the stated domain.

Preserve every negative result, first failure, smallest witness, failed search, inconclusive
discriminator, shared cut, mutation count, and correction. Never rewrite a frozen revision after
observing evidence.

## Object firewall

Keep KSG local arithmetic, KSG MI estimation, continuous Ehrlich shared exclusions, continuous
PID2 reconstruction, categorical Makkeh--Gutknecht--Wibral shared exclusions, Williams--Beer
`I_min`, fitted quantized compositions, heuristics, incomplete/full PID3, project diagnostics, and
software wrappers distinct. No result crosses this firewall without an explicit mapping theorem.
Information quantities use nats. Continuous support is declared rather than inferred. Added noise
changes the estimand. Negative shared-exclusions atoms are valid. PID MI inputs remain signed.

## Required iteration

Use:

```text
review -> freeze scoped claim -> plan -> edit -> implement -> test -> hostile review
       -> improve -> settled-byte replay -> isolated staged-tree verification
       -> small unsigned commit -> fast-forward push main -> durable receipt
```

Tests run while any bound source, fixture, claim, formal file, generator, catalog, release view, or
identity input is moving are diagnostics only. Final evidence is rerun after the last byte change.
Commits and PRs contain no AI attribution, co-author trailers, or signatures.

## Milestone 1 — KSG integer-harmonic revision 4

Current disposition: exact positive-integer arithmetic core GO on its declared domain;
repository/publication integration NO-GO.

### M1a — formal bounded-arithmetic route

- [x] Authenticate all frozen revision-2/revision-3 hashes, including the 1,985-byte/40-line
  `formal-assurance-v3.md`.
- [x] Independently direct-compile the live 19-theorem Lean v4 source and direct-check the v4 SMT
  bound as `unsat`; these are pre-wrapper diagnostics.
- [x] Rewire the Lean checker from absent v3 to v4 while preserving unversioned/v2 identity.
- [x] Rewire Z3 and its bound mutations from absent v3 to v4.
- [x] Correct the stale v4 Lean digest in formal assurance.
- [x] Make both self-tests fail through controlled diagnostics on checker preflight errors.
- [x] Replay 19 theorem/axiom inventories, 14/14 Lean mutations, four `sat` preflights/four
  `unsat` negated obligations, and 12/12 Z3 mutants in normal and optimized Python.
- [x] Hostile proof-blind review of the theorem/premise correspondence. Its one minor finding,
  missing mutation of the middle harmonic-order premise, was corrected and independently replayed.
- [x] Commit and push a truthful conditional-formal submilestone if its exact staged tree is
  coherent and does not imply repository closure.

Receipt: unsigned commit `afc45ff27e5af7fe04e44f2bb9f4147fb472c81e`
(`formal: add conditional KSG harmonic proofs`) was fast-forward pushed to `main`. An anonymous
staged-tree worktree independently passed all eight normal/optimized Lean and Z3 checker/self-test
commands before the commit. The proof scope remains conditional and does not change the
repository/publication NO-GO disposition.

### M1b — bounded corpus certificate and claim custody

- [x] Generate a canonical modular certificate for all 8,198 frozen rows.
- [x] For each selected prime `1,000,033`, `1,000,037`, and `1,000,081`, independently replay 354
  structural zeros and 7,844 nonzero residues with the frozen ordered residue digest.
- [x] Retain prime `1,000,003` and its four nonendpoint collisions as a negative control proving
  that residue zero does not imply rational zero in general.
- [x] Use independent modular inverse/replay implementations where practical; record the shared
  formula/corpus cut and that the triple is fault diversity, not three proofs or CRT recovery.
- [x] Mutate prime admissibility, primality, row order, endianness, residues, predicate, counts,
  implication direction, custody, schema, and canonicality.
- [x] Author revision-4 preclosure claim, obligations, routes, witnesses, implementation map,
  correction ledger, failures, disposition, and revision index without changing frozen bytes.
  The immutable final evidence matrix and decision remain reserved for M1c closure.
- [x] Add canonical `active-packet-v4.json`, exactly one active revision, regular-file/path checks,
  `--claim-only`, hash-first mutations, and one-hash-rebased semantic mutations.
- [x] Explicitly bind the KSG/Ehrlich/PID2/MGW non-transfer firewall and revision 4's post-result
  status.
- [x] Reconstruct every pre-loss bounded-certificate/custody byte with exact provenance and
  digests; recover the historical external review offline without reading `.env` or using the
  network.
- [ ] Commit and push a coherent bounded-certificate/custody submilestone while the broader release
  decision remains NO-GO.

### M1c — isolated production and release integration

- [x] Reconstruct parent-plus-KSG-only `stats.rs`, KSG/ISX/PID3 callers, tests, fixture, and
  generator; exclude exact-binary64-sum, PID2 represented-sum, and Imin changes.
- [x] Bind W1 production radius `79`, ordered counts `(4,1)`, exact target `107/210`, and selected
  bits in brute and kd-tree paths.
- [x] Bind W2 inclusive mapping and public propagation, using “eight ordered-binary64 positions.”
- [x] Derive the 240/114 endpoint split in Python and Rust; bind 354 selected `+0`, zero selected
  `-0`, and 150/354 nonzeros for ordinary-left association over the selected Neumaier prefix.
- [x] Recapture all 13 serial constants using parent PID2 code plus KSG-only changes; replay exact
  equality with `parallel` and thread-budget variations.
- [x] Move catalog evidence to revision 4 and derive the exact 21-node reverse closure minus the
  sole shared-config exclusion: 20 affected and 49 protected method objects, 45 references, and
  protected metadata.
- [x] Bind 15 affected and 20 protected full release-family objects; retain KSG-only bridge strings
  for the four PID2-emitting families.
- [ ] Add a candidate-tree phase checker: exact parent, exact path allowlist, four-path delivery
  envelope, protected projections, full shared-risk blobs, forbidden later-wave paths/tokens, and
  hash-rebased semantic mutations. The replacement must be anchor-relative, reject every deletion,
  require an independent `A`/`M` policy, call critical gates in exact order, isolate Git/config/
  attribute state, and produce a separately tested tree receipt.
- [x] Regenerate `METHODS.md` and `RELEASE_SCOPE_1_0.md`; rebuild review evidence, dispositions,
  assurance registry, ecosystem bindings, and software identity only after all sources settle.
- [x] Preserve ecosystem consumer/inventory objects; record the historical projection rather than
  falsely requiring an unchanged full projection after authority hashes change.
- [ ] Run generator, exact, Decimal, binary64, certificate, claim, formal, source, compiled
  debug/release, brute/kd-tree, serial/parallel, format, clippy, rustdoc, stable/all-feature,
  Python, catalog, release, review, ecosystem, identity, CI, and release-audit gates on settled
  candidate bytes.
- [x] Recover and independently adjudicate the pre-loss Fable review; retain its exact receipt and
  distinguish closed, conditional, deferred, and rejected propositions.
- [x] Attempt every configured Anthropic alias once for proof/SMT, floating-point/refinement, and
  statistical attacks; retain three completed responses and two insufficient-credit outcomes
  without treating model agreement as proof.
- [ ] Obtain final source-blind and proof-blind native/model attacks after all bytes settle;
  independently adjudicate every point and rerun affected gates.
- [ ] Commit unsigned, fast-forward push `main`, then push a narrow receipt commit if the decision
  must name the implementation commit.

## Deferred queue — activate in order only

1. PID2 represented-sum revision 4 on the pushed KSG parent.
2. Categorical MGW SxPID3 Programs A–E, binding all 108 coordinates.
3. Explicitly scoped frontier mathematics: replacement theorems, finite-alphabet bridges,
   finite-sample bounds, lattice/event results, and retained refutations.
4. Literature-reviewed PID discovery/assurance methods paper with machine-readable process schema,
   negative mutations, worked successes/failures, and resource accounting.
5. Complete-detail scientific PDFs with definitions, derivations, counterexamples, open routes,
   receipts, extracted-text parity, and visual inspection of every page.
6. Final CI/release/security/archive/package/SBOM/coverage/fuzz/platform/Python closure.
7. Only then inspect Prisoma, Crebain, Haldir, Galadriel, and other sibling repositories
   independently; implement only necessary authorized consumer contracts and qualify realistic
   ranges with local evidence. Push each repository's `main` in small coherent milestones.

## Current pre-closure diagnostics — not final evidence

- Frozen v2/v3 custody matches the comprehensive handoff.
- The revision-4 conditional formal lane is pushed at `afc45ff27e5af7fe04e44f2bb9f4147fb472c81e`:
  19 Lean theorems, 14/14 Lean mutations, four Z3 `sat` premise preflights, four `unsat` negated
  obligations, and 12/12 Z3 countermodel mutations pass in normal and optimized Python.
- The canonical modular route classifies 354 endpoints and 7,844 nonendpoints in three retained
  fields; the rejected fourth field has four retained collisions. Its checker/self-test passes
  normal and optimized Python with 26 registered faults.
- The exact-enclosure route distinguishes the 8-epsilon rounded-reference result from the unique
  exact-rational maximum below 9.761311 epsilon under the stated Decimal premise. It checks 6,920
  exact `Fraction` containments and rejects 29/29 mutations in normal and optimized Python.
- The revision-4 active packet is canonical and explicitly `integration_no_go`: 68 mapped files,
  35 historical hashes, 49 claim mutations, and 161 integration mutations plus two scope
  preflights pass in normal and optimized Python.
- Source- and prose-hostile reviews found no remaining arithmetic, routing, claim, catalog, or
  release defect after correcting Decimal-premise wording, review-registry negative-result
  custody, the missing revision-3 artifact implication, and one stale digamma comment.
- Debug/release W1 and W2, the full stable/no-default/parallel/all-feature Rust matrix, and explicit
  12-test serial/parallel profiles were green. Clippy then found a test-only
  `needless_range_loop`; after correction, the affected oracle/source routes, Clippy, and rustdoc
  reran green. The final full matrix still awaits settled-byte replay.
- Method, release, review, ecosystem, and software-identity authorities are rebound. Ecosystem
  consumer/inventory projection `ccc5ba...` and historical/base projection `63a843...` remain
  independently pinned; 76 ecosystem mutations pass.
- Git phase isolation, final external advisory rerun, settled-byte replay, immutable final
  evidence/decision, alternate-index commit construction, and push remain open. Repository and
  publication integration therefore remain NO-GO.
- The missing temporary candidate was recovered byte-for-byte into the durable sibling worktree.
  Checkpoint 1 preserves the exact source/test/fixture slice, and the offline 31-artifact replay
  recovered the historical Fable context (`21a08a...`), receipt (`cfdf84...`), and response
  (`b4cac9...`). Recovery-time gate runs are diagnostics only.
- Fresh Fable attacks produced three completed reviews and two insufficient-credit outcomes. The
  paired adjudication at `fable5-ksg-rev4-adjudication-20260727.{md,json}` found no new bounded-core
  blocker, rejected a false `1/(n-1)` gap and an unproved universal floating-point bound, and
  admitted only explicitly scoped hardening work.
- A pinned Lean/Mathlib rebuild, successor-indexed recurrence supplement, anchor-relative phase
  hardening, and complete final-byte matrix remain open.
- Recovery and hostile-review custody was committed unsigned and fast-forward pushed in
  `ca24ab8ebade81a94ffc001531abaf5a5579d5e9`
  (`audit: preserve KSG recovery evidence`), with 21 audit-only paths. This did not promote
  scientific source or change the integration NO-GO disposition.

## Stop and compaction rule

Before any stop, update this file and the active resume manifest, append only the new delta to the
historical ledger, and preserve exact candidate paths/commits/tree IDs/results. On compaction,
reload this file, the comprehensive handoff, only the newest ledger delta, and the active revision
artifacts. Do not reload deferred packets or old model transcripts unless resolving a named
obligation.
