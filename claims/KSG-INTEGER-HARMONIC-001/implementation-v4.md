# Implementation and correspondence map for `KSG-INTEGER-HARMONIC-001`, revision 4

## Production arithmetic candidate

`crates/pid-core/src/stats.rs` constructs `table[m]=H_(m-1)` using a deterministic
Neumaier-compensated positive prefix and evaluates:

```text
(table[n] - table[max(x,y)]) - (table[min(x,y)] - table[k]).
```

Eligible exclusive KSG callers pass `nx+1,ny+1`. Eligible anchor-inclusive Ehrlich ISX/PID3
callers pass their counts directly. The non-cancelling heuristic retains general digamma
arithmetic. No public signature, shell rule, support contract, estimator definition, or
information unit changes.

The Ehrlich per-index map mutates only index-local scratch and has no cross-index mutable state.
That is implementation purity for deterministic ordered collection; it is not a claim that rows or
local contributions are statistically independent.

Under a successful finite-positive unique-shell call, the exclusive and anchor-inclusive
strict-radius membership-set maps conditionally imply `x+y<=n+k` by inclusion--exclusion. The
corresponding balanced harmonic lower bound is recorded as an unpromoted candidate. Neither is
installed here as a new runtime precondition, debug assertion, public contract, or revision-4
formal theorem; source refinement and the other promotion lanes remain open.

This map is a candidate correspondence until final source, compiled, serial/parallel, and staged
tree gates pass. Text markers are bounded guards, not compiler def-use proofs.

## Exact/formal files

| Layer | Active artifact | Scoped result |
|---|---|---|
| historical Lean | `audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean` | exact retained revision-2 bytes |
| active Lean | `audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean` | 19 theorem declarations |
| Lean checker | `scripts/check-lean-ksg-integer-harmonic.py` | pinned environment/source/axiom inventory |
| Lean mutations | `scripts/check-lean-ksg-integer-harmonic-self-test.py` | 14/14 semantic kills |
| Z3 obligations | `audit/formal/z3-ksg-harmonic/*.smt2` | four conditional exact obligations |
| Z3 checker | `scripts/check-z3-ksg-integer-harmonic.py` | bounded grammar/profile/snapshot validation; stdin sat-preflight then unsat-negation |
| Z3 mutations | `scripts/check-z3-ksg-integer-harmonic-self-test.py` | 12/12 satisfiable semantic countermodels plus separately classified firewall controls |

The repaired Z3 checker has SHA-256
`2e0579820c02423e6d15bf81f6ee7470563a121908b4d06e5168b6508f991680`; its self-test has SHA-256
`927a21d119686d8e5a03755e8cf48581a2879bb67c835c295fdefcede26ec101`.

The formal layer does not represent Rust, binary64, neighbor geometry, estimator statistics, or
PID objects.

The Z3 checker lexes bounded ASCII and parses all input as S-expressions, then requires the exact
ordered top-level command, symbol, sort, operator, arity, and terminal obligation profile for each
file. Raw SHA-256 and a whitespace/comment-insensitive token-stream pin both bind each accepted
snapshot. All four snapshots are loaded and validated before any solver call; the positive
formulation is derived only from the validated in-memory negative bytes, and both are transported
to the resolved solver over standard input. Thus validation and solving cannot observe different
path contents. Parser/profile/pin/snapshot/transport controls remain separate from the 12
solver-semantic countermodels. The repaired self-test rejects 52/52 separate controls: 16
lexer/parser, 25 profile/type, and 11 custody/transport/result. Limits are 16,384 source bytes,
2,048 tokens, depth 16, 64 top-level forms, 64 direct list items, 64-byte atoms, and 128-byte string
lexemes. The two source pins are correlated, and profile checking is not semantic proof of theorem
intent. A retained well-typed wrong-theorem dual-pin rebase preserves the expected solver outcomes,
so statement approval remains a human/Git/receipt cut.

## Bounded oracle and modular files

| Artifact | SHA-256 |
|---|---|
| `scripts/generate-ksg-local-arithmetic-oracle.py` | `a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b` |
| schema-2 fixture | `560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c` |
| fixture sidecar file | `fb91172bdb767b3e11e15ef4e89bb0482b932c5c2450f87d566245eda87a8ec7` |
| modular generator | `969c4a5a5a8f6a9054de0154a331824bf2034223c30cb3a76f5e975f6f68a1c3` |
| modular certificate | `5c1923413edecb27bde19d388ab3365844e07bc0ba5f0fa9b28672053ef8901f` |
| modular sidecar file | `5b24f136aecb26ce77d96c7786965c03c31e5e32dbac50f81db0bb667d2611cc` |
| modular checker | `201b046957cee263ad4864acd84ab18095db4bbfc5a23bf90c2bb836b986afec` |
| modular self-test | `1eebc0d575b730753d98659baee5e1f76f17c783e112a9610b731d5f07618c65` |
| exact-enclosure checker | `b7c4df526703adc3dd8f5f04471b027decb256bfaaaa2d32ff9f918253546468` |
| exact-enclosure self-test | `afc2ca44795f86b3dd9c74d2c07234ae9e0372737cdae7d718ec2db2e5204782` |

The modular checker separately recomputes prime admissibility, inverse residues, segment
counts, residue digests, collision witnesses, canonical bytes, and implication direction. Its
28-mutant suite additionally rejects the stale harmonic-denominator object name and removal of
the reciprocal-summand invertibility premise, alongside prime/domain, residue/encoding,
endpoint/split, prime inventory, custody, schema/canonicality, and claim-boundary/collision faults.
Static certificate sections and replayed selected/rejected records are compared recursively by
exact JSON shape, scalar type, and value, closing Boolean/integer coercions without adding those
type-firewall controls to the 28 scientific/custody mutations. Normal and optimized replay kills
`28/28` registered modular mutations and separately rejects `2/2` type-firewall controls.
The composite-modulus mutation is `1000001=101*9901`: it bypasses the 2-through-37 small-prime
prefilter and exercises the deterministic u32 Miller--Rabin witness loop without changing the
registered mutation count.

`scripts/check-ksg-harmonic-exact-enclosure.py` is a separate standard-library route. It
reconstructs row order and lower/upper harmonic prefixes without importing the generator, main
checker, or pid-rs. It distinguishes the 8-epsilon binary64-rounded-reference comparator from the
unique exact-rational maximum enclosed below 9.761311 epsilon. It also preserves the negative
result that 6,509 strings differ textually and 5,934 values differ numerically from exact-rounded
rational references even though all binary64 conversions agree. Its exact `Fraction` route checks
all 6,920 exhaustive rectangular-arithmetic outer-box containments, not a runtime-shell image. It
also converts each finite stored and exact-rounded Decimal operand exactly to `Fraction` before
ordering all 8,198 absolute differences; the unique maximum is
`818/10^79 = 409/(5*10^78)` and is rendered as `8.18e-77`. The 1,278 stress rows retain Decimal
directed-rounding as a premise. Its self-test keeps the exact-comparator controls separate from
the 29 registered mutations covering rounding direction, precision,
row order, endpoint handling, vector digest, mismatch counts, maximum identity and selected value,
full-corpus zero partition, metric labels, strict-threshold direction, ceiling, scope, and
optimized-child execution. Normal and optimized replay kills `29/29` registered mutations and
separately rejects `2/2` exact-comparator controls.

The compiled Rust corpus test classifies every selected helper output directly after asserting
that the rounded reference, selected output, and source-swapped output are finite. It asserts the
fixed 8,198-row partition `+0/-0/nonzero=354/0/7844` in addition to endpoint and association
diagnostics. This is compiled correspondence over the frozen fixture, not an independent exact
proof.

## Claim custody

The current preclosure `active-packet-v4.json` is canonical UTF-8 JSON with a sorted
path-to-SHA-256 map, exact JSON scalar types, exactly one active revision, scalar facts, historical
hashes, open gates, and the object firewall. The checker recursively requires equality with the
complete mapped claim-tree file and directory inventory; rejects every symlink, external hardlink,
and normalized-path collision; and separately pins the complete bytes of every reviewed active
scientific document. Typed facts are the machine authority; prose hashes are reviewed-byte
custody, not semantic theorem proving. Supplemental statement/forbidden markers are only bounded
tripwires. The packet excludes itself and the claim checker/self-test to avoid a digest cycle. The
eventual Git commit anchors both sides.

The phase checker has the same unavoidable self-reference boundary for its own checker and
self-test bytes. Its hostile suite retains a coordinated policy/checker rebase that passes the
modified checker and a tree generated after that mutation, while an independently pre-pinned
pristine tree rejects it. Therefore precommit output with `candidate-tree=not-requested` is only a
working-tree diagnostic. M1a custody requires the exact alternate-index candidate tree and a
detached checkpoint supplied through the external tree/commit hooks; the eventual commit and
remote observation then preserve those bytes. This is custody, not authenticity or science.

This is not the immutable final M1c packet. The older `afc45ff...` checkpoint is provisional
history rather than the canonical M1a anchor for these repaired bytes. A future canonical M1a must
commit, push, remotely verify, and receipt the settled implementation while integration remains
NO-GO. Only afterward may a separate descendant/re-anchored M1c create final
`evidence-matrix-v4.md` and `decision-v4.md`; the manifest and checker pin must then be regenerated
on settled bytes to include them.

Claim-only mutations first demonstrate failure against the unchanged envelope, then update the
changed leaf hash and the unavoidable manifest digest in the checker. The separately reviewed
prose-byte map must still reject a marker bag or rephrased contradiction. Type confusion,
extra-root/nested/case/symlink/hardlink packet nodes, and marker-preserving scientific
contradictions are attacked explicitly. This is layered custody and bounded fault sensitivity,
not a general natural-language proof.

The binary64 loader separately reconstructs the exact exhaustive/stress row sequence, requires
canonical duplicate-free JSON with exact types and finite Decimal/binary64 values, and invokes the
pinned generator's no-write exact-output replay. Aggregate extrema are evaluated only after every
row passes finiteness. This closes the specific schema/order/NaN false greens while retaining the
same-repository authenticity boundary.

The lifecycle checker admits only the reviewed preclosure and immutable-final status/stage tuples.
At final closure, canonical authorities in the evidence matrix and decision must bind all 13 gate
receipts, the evidence-matrix digest, and a full implementation commit. Success output is derived
from the accepted manifest rather than hardcoded.

## Integration phase boundary

The KSG-only release must be synthesized from the declared pushed parent. Shared files are rebuilt
from that parent plus reviewed KSG hunks. Later PID2 represented-sum, I_min, categorical frontier,
unrelated formal/PDF, and combined identity bytes are excluded.

Exactly 15 release families may advance to KSG-only revisions; 20 remain protected. Catalog
closure is the 21-node reverse dependency closure from two KSG roots minus the single
non-numerical shared-config object, yielding 20 affected and 49 protected methods. These rows are
requirements, not completed evidence in this preclosure document.

## Required replay before final decision

Run normal and optimized claim, formal, modular, generator, exact, binary64, source, catalog, and
release checkers plus the exact-enclosure checker; debug/release focused Rust tests; brute/kd-tree
W1; serial/parallel/thread
identity; format, clippy, rustdoc, stable/no-default/all-feature debug/release; Python bindings;
review/ecosystem/identity/release audits; and phase-isolation mutations. Rerun after the last byte
change. The generic default checker must remain explicitly lifecycle-red while status is
`integration_no_go` or any gate is open. Runs made while any input moved are not evidence.
