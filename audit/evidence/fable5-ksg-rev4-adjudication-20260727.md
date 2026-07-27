# Fable 5 Max KSG revision-4 adjudication

Status: **no new bounded-arithmetic-core blocker; repository/publication integration NO-GO**

Claim under review: `KSG-INTEGER-HARMONIC-001`, revision 4.

This is the human rendering paired with
[`fable5-ksg-rev4-adjudication-20260727.json`](fable5-ksg-rev4-adjudication-20260727.json).
The JSON is the machine-readable finding matrix. Neither file is a proof and neither may promote
the claim. Model output is attack input: a proposition is admitted only after independent source
inspection, an exact counterexample, or a replayable proof.

## Receipt and authority boundary

The recovered historical preclosure review is bound by:

```text
prompt   a1d6f955cc26419e76b93a36a0ec8efbe3ddebda6b6a5c897f69903faed9c515
context  21a08acd99bfc5c5881a6d267382bc808075fb69bca9ae6f76b103775c5f3ee3
receipt  cfdf84ba5ca1e51c215b7785d577c7378e4836d213de12230caf5449f33e010b
response b4cac94ca6b636d8f5433bc3e2112f5cee7c118aa60cff9a321ea1fdcaf7dd9a
```

The fresh formal-methods recovery review is bound by:

```text
prompt   ef8c4438d2d3123d2ed07412013d3017ced1ebbc0dde1d45490bcfe214fae5a8
receipt  8f3308ecc873628bd675df3e974593eb130e855e591def8ce25e001fde56327b
```

Three of five configured aliases completed. Their visible-response digests are
`742a684d4ff9517a0a09ce09a47cd9ea46680042c123deb6fe550ea9d90cf5db`,
`a286e80b360f64432f5350280cc2adf6ea1440c77660cce2bc8d67c8274053fc`, and
`0c889b39be45fed9b9ff8eaebcf4bcae7f4854186a4991fb5450c5b6a8f8f7ab`.
Two aliases returned the provider's insufficient-credit response. No key value is retained.
Agreement among model calls is not an independent verification route.

The status words below mean:

- **accepted**: correct, material, and actionable after independent inspection;
- **already closed**: a valid concern covered by current code, evidence, or an explicit limit;
- **conditional**: potentially sound only after the named premises and bridge are proved;
- **deferred**: worthwhile bounded work, but not an established revision-4 defect; and
- **rejected**: false, overbroad, about the wrong object, or unsupported by the proposed argument.

## Historical preclosure findings

| ID | Adjudication | Independent disposition |
|---|---|---|
| F1 | already closed | The naive-prefix route is executed in Python and compiled Rust and requires exactly 121 nonzero rows and no negative zero. |
| F2 | already closed | Revision-4 prose has independently named semantic markers and leaf-plus-manifest reseal mutations. |
| F3 | already closed | The four rejected-prime collision rows are explicitly one divisibility event plus its sign reversal, not four independent events. |
| F4 | already closed | Signed-zero counts are described as structural regression tripwires, not independent scientific evidence. |
| F5 | already closed | The directed-enclosure route covers all 8,198 rows and exact `Fraction` containment for the 6,920 exhaustive rows, with Decimal and host-binary64 cuts disclosed. |
| F6 | already closed | The catalog and active methods bind revision 4 and reject stale revision-1/2/3 evidence. |

These closures must still replay on the final settled staged tree. Historical or recovery-time
passes do not satisfy that requirement.

## Domain and production-dataflow adjudication

### Unique-shell contract

The allegation that tied shells can silently feed counts outside the proved domain is already
closed for the inspected production routes.
`nn.rs::validate_kth_neighbor_shell` requires a positive finite radius, exactly `k - 1` non-anchor
points strictly inside the joint shell, and exactly one point on its boundary. KSG and Ehrlich
shared-exclusions call this validation before invoking the harmonic helper. Duplicate/zero-radius
and boundary-tie cases fail closed.

Strict joint interior also implies each required strict marginal predicate for those interior
points. Together with the anchor-inclusive initialization, this establishes the lower harmonic
arguments used by the shipped routes. This is a dataflow argument over the inspected code; final
compiled tests and feature-profile parity remain separate obligations.

Tie rejection is only a one-sided sample diagnostic. It does not identify quantization,
discreteness, rounding, an atom in the population law, or any other unique population cause.

### All-unique W2 endpoint witness

The review alleged that the W2 source-disjunction count had minimum `k + 1` because it includes the
anchor and all `k` joint neighbors. That premise is false: a joint neighbor can be selected because
of the target coordinate while failing the strict source-disjunction predicate.

Take one-dimensional target and sources:

```text
n = 3, k = 1, anchor row i = 0
T  = [0, 0.4, 0.8]
S1 = [0, 1,   3]
S2 = [0, 10, 30]
```

For row 0, the two joint `L∞` distances used by the two-source shared-exclusions route are `1` and
`3`. Hence the raw first-neighbour radius is `1`; its strict interior contains zero non-anchor
rows and its boundary contains exactly one, so the unique-shell contract accepts it.

The target distances `0.4` and `0.8` are both strictly below `1`. The anchor-inclusive target
count is therefore `n_t = 3 = n`. For the source-disjunction predicate, row 1 has
`max(|S1_1-S1_0|, |S2_1-S2_0|) = 10`, and row 2 has value `30`; neither is strictly below `1`.
Only the anchor is counted, so `n_alpha = 1 = k`. All values within each coordinate are unique.
Thus the declared W2 endpoint pair `(n_alpha,n_t)=(k,n)` is attainable without duplicate rows.

This exact witness should become a compiled regression test. Until then it is an independently
checked construction, not a settled-tree test receipt.

### Structural zeros are not generic range gaps

The proposed claim that every non-structural row is separated from zero by at least `1/(n-1)` is
false. With `n=8`, `k=2`, `x=3`, and `y=5`,

```text
H_(k-1) + H_(n-1) - H_(x-1) - H_(y-1)
= H_1 + H_7 - H_2 - H_4
= 1/105
< 1/7.
```

No such gap may be used for sign or zero classification. The endpoint cases that are structurally
zero must be distinguished in wording from nonzero range extrema.

## Exact algebra, modular certificates, and logic

Every reciprocal summand index in the bounded corpus is at most `999999`, and every selected or
rejected modulus is independently checked prime and greater than `999999`. Therefore all summand
denominators are invertible in each field. Existing prose that says “maximum harmonic
denominator” is potentially ambiguous because a harmonic number's reduced rational denominator
is a different object; it should say **maximum reciprocal summand denominator/index**.

The modular route does not reconstruct a rational numerator with the Chinese remainder theorem.
It uses only the sound implication

```text
nonzero residue modulo any admissible prime  =>  exact rational is nonzero.
```

The converse is explicitly prohibited. Exact zeros are established by structural harmonic
cancellation. The rejected prime and its collision rows are a negative control for the converse,
not evidence that CRT is necessary.

Z3 vacuity is already guarded by a satisfiable positive preflight before every negated-goal
unsatisfiable query. Requiring every premise to appear in an unsatisfiable core would be unsound:
cores are nonunique and may omit redundant premises. The stronger proposed test is accepted:
delete or weaken one domain premise at a time, require a satisfiable mutant, freeze its complete
model, and independently evaluate that model outside the solver.

A proof-producing cvc5 replay with a separately pinned proof checker remains valuable solver
diversity. It becomes a credible additional route only if proof-corruption mutations fail closed
and SAT models are independently evaluated. Re-encoding the same statement in a second solver is
not a second derivation of the statement.

## Lean theorem hardening

Two supplements are accepted without rewriting the frozen revision-4 theorem:

1. formulate the bounded identity with successor-indexed positive arguments or otherwise without
   truncated natural subtraction, derive compatibility with the frozen statement, print its axiom
   inventory, and add premise-deletion mutants; and
2. prove separately that any function satisfying the positive-integer recurrence
   `f(m+1)=f(m)+1/m` yields the four-term harmonic cancellation, because its arbitrary additive
   base cancels.

The recurrence theorem alone does not identify the analytic digamma function. A separate,
pinned-Mathlib bridge must establish that the actual digamma object satisfies the recurrence on
the stated positive-integer domain. Compiler success and `#print axioms` output are required; an
uncompiled theorem sketch is not evidence.

## Binary64 and exact-real boundary

The following quantities are intentionally different:

- `8 epsilon`: worst error against the rounded Decimal reference in the frozen corpus;
- approximately `9.761311 epsilon`: worst directed enclosure against the exact rational on the
  unique non-rounding-maximizer row; and
- `32 epsilon`: the reviewed public ceiling.

They may not be substituted for one another.

An exact integer comparator is not automatically a cheap replacement for the directed Decimal
route: it must cover binary64 exponent/subnormal cases and the large exact `H_999999` rational.
It is worth prototyping as an additional failure-diverse route. Likewise, MPFR or Arb interval
replay would add heterogeneous finite-instance evidence; it would not replace the existing route
or prove a universal bound.

The proposed universal `28 epsilon` Gappa/Flocq theorem is conditional and presently unproved.
Admitting it requires all of:

1. a certified error bound for the actual Neumaier harmonic table;
2. the exact round-to-nearest-even operation DAG used by production;
3. the complete input range and special-value exclusions;
4. a compiler/source-to-formal bridge; and
5. mutants for reassociation, table construction, and the claimed bound.

Parallel execution is currently index ordered and uses a fixed reduction order. It must still
replay bit-identically across debug/release and serial/parallel profiles on the final bytes.

## Statistical and literature boundary

No published KSG theorem has yet been shown to apply verbatim to the shipped estimator. Candidate
papers may use `log N`, inclusive raw-radius marginal counts, or other conventions, whereas the
shipped route uses `psi(n)`, strict counts, and a unique-shell contract. A theorem transfer
requires an exact formula-and-hypothesis bridge, not similarity of names.

The accepted next artifact is a shipped-versus-paper registry that freezes, for each result:

- norm and joint metric;
- raw/halved radius convention;
- strict or inclusive marginal count;
- anchor inclusion;
- shell/tie policy;
- `psi(n)` or `log n`;
- support, density, smoothness, and boundary assumptions;
- fixed or varying `k`;
- dimension regime; and
- convergence mode and quantifier order.

The exact-real local range does imply a scoped saturation obstruction. If
`D = H_(n-1)-H_(k-1)` and an estimator is the arithmetic mean of exact-real local terms each in
`[-D,D]`, then `|I_hat| <= D`. For a nonnegative target value `I>D`, any such estimate has absolute
error at least `I-D`. Equivalently, achieving error at most `delta` requires
`D >= I-delta`. This is only a necessary condition. It is neither an accuracy upper bound nor a
sufficient sample-complexity theorem.

The proposed checkerboard/minimax result remains deferred until its distribution class, coupling,
Bayes-to-minimax step, smoothing, retained mutual information, constants, and quantifiers are
proved. Nondifferentiability of a minimum functional also does not by itself prove universal
ordinary-bootstrap inconsistency. A concrete counterexample family or an applicable
directional-differentiability theorem is required.

An exact finite-group permutation theorem is worthwhile but separate from KSG arithmetic. It must
state the transformation group, identity/tie/add-one convention, exchangeability premise,
failed-transform policy, and mutation suite.

## MGW shared-exclusions PID3 route

Finite empirical categorical Makkeh--Gutknecht--Wibral shared-exclusions quantities admit an exact
rational-log representation. Revision-2 PID2 exact-log-product work already establishes the
architecture; PID3 should extend it rather than claim an unrelated invention.

A canonical sparse prime-exponent vector provides custody and decides exact zero by exponent
cancellation. It does **not** determine sign lexicographically. Sign requires exact comparison of
the corresponding numerator and denominator integer products, or certified intervals with exact
fallback.

Before implementing the proposed 18-node/108-coordinate program:

1. freeze an unambiguous ordered coordinate and lattice manifest;
2. derive the antichain order and Möbius coefficients through two independent implementations;
3. emit exact zero/sign/product certificates;
4. bind the certificates to compiled production outputs; and
5. kill order, coefficient, count, sign, cancellation, and serialization mutants.

This is accepted frontier work, not evidence that the current PID3 implementation is complete.

## Prioritized actions

P0 before KSG revision-4 integration:

1. compile the successor-indexed and recurrence-based Lean supplements and premise mutants;
2. add the all-unique W2 endpoint witness as a production regression;
3. separate structural-zero and range-extremum terminology;
4. correct reciprocal-summand-denominator wording;
5. freeze the exact shipped-versus-paper KSG registry; and
6. independently evaluate all SMT mutant countermodels.

P1 additional failure-diverse routes:

1. proof-producing cvc5 plus an external proof checker;
2. a bounded Kani shipped-function refinement harness;
3. MPFR or Arb finite-instance interval replay;
4. a formal exact permutation theorem; and
5. the exact MGW SxPID3 prime-log certificate program.

P2 research routes, admitted only if their missing bridges are completed:

1. formal Neumaier-table analysis followed by Gappa or Flocq;
2. the complete checkerboard/minimax lower bound;
3. a fresh-statement Rocq or Isabelle port; and
4. an explicit nonregular-bootstrap counterexample or theorem.

## Final disposition

Across domain/dataflow, exact algebra, Lean/SMT, binary64, statistics/literature, PID extension,
and provenance lenses, the adjudication found no new blocker to the already scoped bounded
exact-arithmetic core. It did find concrete hardening work and several attractive but presently
conditional or deferred routes.

The bounded core therefore remains GO only on its declared positive-integer/corpus scope.
Repository/publication integration remains NO-GO until the independent gates, final-byte replays,
isolated staged-tree custody, and pushed receipts close. Hash equality and Git bundles establish
integrity relative to observed bytes and object graphs; they do not establish signer identity,
origin, authenticity, statistical validity, or scientific truth.
