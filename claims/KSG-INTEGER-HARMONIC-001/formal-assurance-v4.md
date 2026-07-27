# Formal assurance for `KSG-INTEGER-HARMONIC-001` revision 4

## Disposition

Evidence label: **theorem proved under stated assumptions** for 19 exact Lean theorems, with four
separately encoded conditional QF_UFLIRA obligations checked by Z3. This is not end-to-end
formal verification. The analytic positive-integer digamma identity is still a typed premise, and
the implementation/refinement, neighbor-geometry, binary64, estimator, support, PID, and
application layers remain outside both formal systems.

## Revision-preserving source custody

The first revision-2 Lean result is retained byte-for-byte at
`../../audit/formal/lean-ksg-harmonic/v2/PidKsgIntegerHarmonic.lean`:

```text
812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943
```

Revision 4 does not rewrite that source. Its canonical extended source is
`../../audit/formal/lean-ksg-harmonic/v4/PidKsgIntegerHarmonic.lean`, with SHA-256:

```text
32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4
```

The pre-existing unversioned path
`../../audit/formal/lean-ksg-harmonic/PidKsgIntegerHarmonic.lean` retains the exact revision-2
bytes. The checker requires both historical revision-2 paths to have the displayed hash and
identical bytes; the active revision-4 extension exists only at its revision-scoped path.

## Lean route

Pinned environment:

| Artifact | Identity |
|---|---|
| Lean toolchain | `leanprover/lean4:v4.32.0` |
| Lean source commit | `8c9756b28d64dab099da31a4c09229a9e6a2ef35` |
| `audit/formal/lean/lean-toolchain` | `2773c517aa90b66ea8a2c52bddddf84393157797f8341be0df45294fff7fd32e` |
| `audit/formal/lean/lakefile.toml` | `1c3f1818c4a62ab48f4ae05de573f6d884aaf7f7397a21646df162151cfccdf1` |
| `audit/formal/lean/lake-manifest.json` | `e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd` |
| Mathlib source revision | `81a5d257c8e410db227a6665ed08f64fea08e997` |
| revision-4 proof source | digest pinned by the revision-4 checker |

The checker validates every manifest package checkout's root, exact revision, recorded origin, and
clean status under isolated Git configuration. It checks the exact Lean version and source commit,
the source/import inventory, proof-escape exclusions, scope sentinels, theorem declarations, and
the complete `#print axioms` result. Only `propext`, `Classical.choice`, and `Quot.sound` are
permitted.

The 14 retained revision-2 conclusions cover the rational finite-sum definition and recurrence,
four-sign cancellation conditional on `PositiveIntegerDigammaPremise`, direct/range equality,
source symmetry, exclusive successor, inclusive identity, argument bounds, and both count-index
maps. Revision 4 adds five kernel-checked conclusions:

1. universal monotonicity of the exact rational harmonic finite sum;
2. preservation of the range expression under the rational-to-real order embedding;
3. nonnegativity and full-tail upper bounds for both selected harmonic ranges;
4. the two-sided rational bound
   `-(H_(n-1)-H_(k-1)) <= T <= H_(n-1)-H_(k-1)`; and
5. one combined real theorem that explicitly composes the typed digamma premise, four-sign
   cancellation, direct-to-range identity, rational-to-real coercion, and both real inequalities.

The combined theorem assumes natural indices satisfying

```text
1 <= k <= n
k <= x <= n
k <= y <= n.
```

The inventoried rectangular arithmetic outer box uses the stricter common domain `1 <= k < n`.
It is not asserted to equal the runtime unique-shell image. Proving a theorem on the slightly
larger `k=n` arithmetic domain does not assert that a runtime estimator accepts that endpoint or
that every outer-box tuple is runtime-realizable.

The baseline-first Lean self-test compiles the unmodified source and kills 14 semantic mutations.
The five new kills reverse harmonic monotonicity, corrupt the rational-to-real bridge, strengthen a
zero tail to one, reverse the rational lower bound, and offset the combined real conclusion. The
nine retained kills cover the denominator, min/max, coefficient signs, source swap, exclusive and
inclusive maps, bounds, and the direct exclusive index.

## Z3 route

The checker requires exact `Z3 version 4.16.0 - 64 bit`. CI obtains the official
`z3-4.16.0-x64-glibc-2.39.zip` archive and verifies SHA-256
`7288c49a5bd6dbafd7b0b0d1f65956b91672da24b08f09242919af159be3418e`
before placing its executable on `PATH`.

| Script | Conditional obligation | SHA-256 |
|---|---|---|
| `ksg-digamma-cancellation.smt2` | four-sign cancellation under four explicit digamma instances | `8ae66c11fb66541bc47766b2682cf1e53d9b656aa0fa12e6945ac22057816ed4` |
| `ksg-index-maps.smt2` | exclusive successor, inclusive identity, bounds, and harmonic indices | `71ea8db97df43f51da89496a5e799bedc6216f9ede40368207d2ffed8df40fe1` |
| `ksg-symmetric-range.smt2` | direct/range equality and source exchange for arbitrary harmonic values | `add0fc3a371c65433fdfd8b1e51d3182c6ef78db0cfd1d372f461f1d030e19a9` |
| `ksg-local-bound-v4.smt2` | direct/range equality and the full-tail bound under explicit local harmonic-order premises | `33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31` |

The repaired checker and self-test source digests are:

```text
2e0579820c02423e6d15bf81f6ee7470563a121908b4d06e5168b6508f991680  checker
927a21d119686d8e5a03755e8cf48581a2879bb67c835c295fdefcede26ec101  self-test
```

The correlated token-stream pins and exact top-level-form counts are:

| Obligation | Top forms | Token-stream SHA-256 |
|---|---:|---|
| digamma cancellation | 27 | `46d504aea109ae875598404a7d680e8dceb93635a4f91ab3d11bd51b08de5292` |
| index maps | 34 | `7e655ca85f042c4275042fc8e9368a72aef10b1e0cbde3dce7b87c67769a7f2c` |
| local bound | 32 | `9f20298f0fb6a630167995b96638f6446a07e4005b9bc1a265a136302a73f284` |
| symmetric range | 28 | `e7d9605f13384e1f7d04b0f1b6b4a61848adc70a6ae1925a06eeeddca2475aa1` |

The token digest has domain prefix `pid-rs/smtlib-token-stream/v1` followed by a zero byte.
Comments and whitespace are omitted; each raw lexeme is framed by token kind and unsigned
32-bit length. This is a tripwire against rebasing only the raw-hash field, not an independent
source encoding.

For each script, the checker requires the positive formulation to be exactly `sat` before requiring
the negated obligation to be exactly `unsat`. This excludes vacuity from an inconsistent premise
set. Before invoking Z3, the checker lexes bounded ASCII, parses every byte as S-expressions, and
requires an exact ordered per-file profile of top-level commands, declared symbols and sorts,
operator arities, and the terminal negated obligation. Unsupported commands, trailing forms after
`exit`, malformed/oversized inputs, and profile/type drift are rejected.

The fail-closed parser limits are:

| Quantity | Maximum |
|---|---:|
| source bytes | 16,384 |
| tokens | 2,048 |
| nesting depth | 16 |
| top-level forms | 64 |
| direct items in one list | 64 |
| atom bytes | 64 |
| string-lexeme bytes | 128 |

The accepted type subset is `Bool`, `Int`, and `Real`, with exact same-sort operands. Addition is
binary; subtraction has arity one through three; comparisons and equality are binary; `not` is
unary; `ite` is ternary; `and` has at least two operands; and `harmonic`/`psi` are typed unary
applications.

Each accepted source is bound both by its raw SHA-256 and by a
whitespace/comment-insensitive token-stream fingerprint. These are correlated custody views of
the same source, not two proofs. All four raw snapshots are loaded and validated before the first
solver process starts. The positive preflight is derived only from the validated in-memory
negative snapshot, both exact forms are sent over standard input, and no proof path is reopened
between validation and solving. The resolved executable path, binary digest, and exact version are
reported as observed runtime identity, not authenticity. The repeated manifest observations are a
bounded consistency check, not an atomic filesystem snapshot.

The revision-4 bound script explicitly assumes only the three local instances

```text
H_(k-1) <= H_(min(x,y)-1) <= H_(max(x,y)-1) <= H_(n-1).
```

Z3 does not prove those harmonic-order premises. Lean separately proves universal monotonicity for
the exact rational harmonic definition. This division is deliberate and must not be described as
two failure-independent proofs of harmonic monotonicity.

The Z3 self-test retains eight cancellation/range/index mutants and adds four bound mutants: a
strictly tightened lower conclusion and reversals of the lower, middle, and upper harmonic-order
premises. All 12 must expose a satisfiable countermodel. Grammar limits, forbidden commands,
symbol/sort/operator/arity/profile changes, raw/token pin drift, snapshot replacement,
standard-input transport, timeout, and malformed solver results are tested in a separately
labelled 52-control firewall: 16 lexer/parser, 25 profile/type, and 11
custody/transport/result controls. They do not increase the 12 semantic-mutant count.

The retained adequacy boundary is a well-typed wrong digamma theorem with raw SHA-256
`88e67f4289caf81770c9457d3ac77de4f470fe56d8bf3eb0a8139ac42c23ec52` and token-stream SHA-256
`f8c8334b0cd73a55072e833463ae6ec43bd0f6042c0f7e888eff01b8f75caa8e`. After a deliberate dual
pin rebase, its positive form is `sat`, its negation is `unsat`, and all 12 old semantic mutants
still return `sat`. Thus the exact profile blocks command smuggling but cannot determine the
intended theorem; deliberate dual rebase and statement approval remain a shared human/Git/receipt
cut. Z3 emits solver results, not proof certificates checked by a separate smaller kernel.

## Shared cuts and prohibited promotions

Lean and Z3 share the chosen theorem statements, the human `(+1,+1,-1,-1)` sign transcription, the
exclusive successor/inclusive identity map, and the analytic positive-integer digamma premise.
Their engine diversity cannot close an error in one of those shared inputs. In particular:

- neither route constructs the analytic digamma function or proves
  `psi(m)=H_(m-1)-gamma`;
- neither proves that neighbor code produced counts in the formal domains;
- neither represents the selected Rust prefix/reassociation or any binary64 error;
- neither proves KSG/Ehrlich consistency, calibration, or support validity; and
- neither proves a Makkeh--Gutknecht--Wibral shared-exclusions functional or any PID atom.

The exact bound permits negative local terms. It is an arithmetic bound in nats after the typed
digamma bridge, not a bound on mutual information, redundancy, a PID atom, estimator bias, or
application error.

## Required replay

```text
python3 scripts/check-lean-ksg-integer-harmonic.py
python3 -O scripts/check-lean-ksg-integer-harmonic.py
python3 scripts/check-lean-ksg-integer-harmonic-self-test.py
python3 -O scripts/check-lean-ksg-integer-harmonic-self-test.py
python3 scripts/check-z3-ksg-integer-harmonic.py
python3 -O scripts/check-z3-ksg-integer-harmonic.py
python3 scripts/check-z3-ksg-integer-harmonic-self-test.py
python3 -O scripts/check-z3-ksg-integer-harmonic-self-test.py
```

Closure requires 19 Lean theorem inventories, 14/14 killed Lean semantic mutations, four exact Z3
positive `sat` preflights, four exact negated `unsat` results, and 12/12 Z3 mutants returning exact
`sat` under both normal and optimized Python execution. It also requires the separately labelled
52 SMT grammar/profile/pin/snapshot/transport/result controls to pass; those controls are not
additional formal theorems or semantic countermodels. Current normal and optimized runs are
byte-identical green for the repaired checker and self-test; repository integration still requires
final settled-tree replay.
