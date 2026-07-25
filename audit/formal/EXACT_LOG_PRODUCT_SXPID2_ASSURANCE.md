# Exact multiplicative certificates for empirical categorical SxPID2

## Status and claim boundary

This note adds an exact arithmetic assurance route for the two-source empirical categorical
shared-exclusions PID of Makkeh, Gutknecht, and Wibral. It does not define a new PID and does not
import axioms, atoms, or desired properties from another PID proposal.

The route is representation-agnostic only in a narrow algebraic sense: after the
Makkeh--Gutknecht--Wibral source-event unions, target-restricted events, empirical averaging rule,
and integer Möbius transform are fixed, the same finite log expression can be normalized into one
positive rational product. The route is not representation-agnostic across PID definitions. If
the event logic, lattice, or cumulative is changed, it certifies a different object.

The result removes transcendental approximation from exact **zero and sign** decisions for the
fixed empirical count table. It does not by itself enclose the nonzero logarithmic magnitude. The
existing directed-rounding certifier supplies that separate value enclosure.

Artifact set: [this Markdown note](EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md),
[self-contained LaTeX](latex/exact-log-product-sxpid2-assurance.tex), and
[rendered PDF](../../output/pdf/exact-log-product-sxpid2-assurance.pdf). The deterministic PDF
checker rejects build warnings, layout diagnostics, stale bytes, changed extracted text or page
geometry, and non-embedded fonts.

## Definitions and hypotheses

Let $Z_+$ be the finite set of distinct observed complete states
$z=(s_1,s_2,t)$. Each state has an integer count $c_z>0$, and

$$
 n=\sum_{z\in Z_+}c_z>0.
$$

For a fixed SxPID lattice node $\alpha$ and keyed state $z$, define integer counts

$$
 a_{z,\alpha}=\#A_{z,\alpha},\qquad
 b_{z,\alpha}=\#(A_{z,\alpha}\cap\{T=t_z\}),\qquad
 t_z=\#\{T=t_z\}.
$$

Here $A_{z,\alpha}$ is exactly the disjunction of source-collection events in the published
shared-exclusions construction. Every defining event contains its keyed observed state. Hence

$$
 0<c_z\le b_{z,\alpha}\le a_{z,\alpha}\le n,
 \qquad b_{z,\alpha}\le t_z\le n.
$$

The three pointwise cumulative components, in nats, are

$$
 i^+_{z,\alpha}=\log\frac{n}{a_{z,\alpha}},
 \qquad
 i^-_{z,\alpha}=\log\frac{t_z}{b_{z,\alpha}},
$$

and

$$
 i^{\mathrm{sx}}_{z,\alpha}
 =i^+_{z,\alpha}-i^-_{z,\alpha}
 =\log\frac{n b_{z,\alpha}}{a_{z,\alpha}t_z}.
$$

The empirical cumulative is the exact count-weighted average

$$
 C^u_\alpha=\sum_{z\in Z_+}\frac{c_z}{n}i^u_{z,\alpha},
 \qquad u\in\{+, -, \mathrm{sx}\}.
$$

The hypotheses are therefore:

1. The complete categorical states are finite and coalesced into unique rows with positive
   integer counts.
2. The event definition is the published keyed SxPID source disjunction, with its keyed target
   intersection.
3. The empirical probabilities are exact count ratios and the average uses $c_z/n$. No
   smoothing, fractional pseudo-count, or alternative weighting rule is silently inserted.
4. The lattice is finite and its atom-from-cumulative Möbius coefficients are integers.
5. The logarithm is applied only to positive rational arguments. The implementation reports nats.

The product reduction extends to rational weights after clearing a declared common denominator,
but that extension is not used by the current checker.

## Exact product theorem

Define

$$
 R^+_\alpha
 =\prod_{z\in Z_+}\left(\frac{n}{a_{z,\alpha}}\right)^{c_z},
$$

$$
 R^-_\alpha
 =\prod_{z\in Z_+}\left(\frac{t_z}{b_{z,\alpha}}\right)^{c_z},
$$

and

$$
 R^{\mathrm{sx}}_\alpha
 =\prod_{z\in Z_+}
 \left(\frac{n b_{z,\alpha}}{a_{z,\alpha}t_z}\right)^{c_z}.
$$

All three are positive exact rationals. The logarithm product rule and integer power rule give

$$
 C^u_\alpha=\frac{1}{n}\log R^u_\alpha.
$$

The local identity also gives the exact multiplicative component identity

$$
 R^{\mathrm{sx}}_\alpha=\frac{R^+_\alpha}{R^-_\alpha}.
$$

Let $M_{\gamma\alpha}\in\mathbb Z$ be the fixed Möbius row that constructs atom
$\gamma$. Define

$$
 R^u_\gamma=\prod_\alpha (R^u_\alpha)^{M_{\gamma\alpha}}.
$$

Negative Möbius coefficients mean exact rational reciprocals. Linearity of logarithms gives

$$
 \Pi^u_\gamma
 =\sum_\alpha M_{\gamma\alpha}C^u_\alpha
 =\frac{1}{n}\log R^u_\gamma.
$$

Because $n>0$ and $R>0$, every cumulative and atom obeys

$$
 \frac{1}{n}\log R=0\iff R=1,
$$

$$
 \frac{1}{n}\log R>0\iff R>1,
 \qquad
 \frac{1}{n}\log R<0\iff R<1.
$$

Thus integer numerator-versus-denominator comparison is a complete exact zero/sign decision for
the fixed empirical coordinate. It does not call `log`.

The same conclusion can be read directly from the certifier's canonical log-linear expression.
Every emitted coefficient $q$ satisfies $nq\in\mathbb Z$, so

$$
 R=\prod_j x_j^{nq_j}.
$$

The independent checker reconstructs $R$ from event counts and separately reconstructs it from
the emitted terms. Equality binds the two representations.

## Retained counterexample to empty-term-only zero certification

The first implementation treated an empty canonical term map as the only exact-zero witness. That
condition is sufficient but not complete: logarithms with different rational arguments can cancel
multiplicatively even after equal arguments and zero coefficients have been combined.

The smallest binary-table counterexample found by exhaustive total-count search uses canonical
state order

$$
(0,0,0),(0,0,1),(0,1,0),(0,1,1),(1,0,0),(1,0,1),(1,1,0),(1,1,1)
$$

and counts

$$
(0,0,1,1,1,4,1,0),\qquad n=8.
$$

For the net `unique_one` atom, the canonical expression is nonempty:

$$
E=-\frac18\log\frac8{15}
  +\frac18\log\frac45
  +\frac18\log\frac89
  +\frac18\log\frac43
  -\frac18\log\frac{16}{9}.
$$

Nevertheless its denominator-cleared product is exactly

$$
R=\left(\frac8{15}\right)^{-1}
  \left(\frac45\right)
  \left(\frac89\right)
  \left(\frac43\right)
  \left(\frac{16}{9}\right)^{-1}
 =\frac{15}{8}\frac45\frac89\frac43\frac9{16}=1,
$$

so $E=\frac18\log R=0$. At 256 working bits, the directed interval is

$$
[-3\,2^{-258},\;5\,2^{-259}],
$$

which correctly contains zero but does not resolve its sign. The repaired report therefore keeps
the interval-local decision `unresolved_sign` and its interval zero witness empty, while a separate
exact-product record reports `certified_exact_zero` with witness
`exact_multiplicative_product_equals_one`. Claiming that the interval itself resolved zero would
be false; refusing the exact product-one proof would be incomplete.

Exhausting all 12,869 nonzero binary tables with total count at most eight, comprising 308,856
coordinates, finds no such cancellation below total eight and exactly 16 at total eight. All 16
have support size five and are net unique atoms. Thus total eight and support five are minimal only
within this explicitly exhausted binary domain, not universally over other alphabets or PID
definitions.

## Bounded executable exact-product route

The Rust certifier now performs a two-stage operation. It first verifies $nq_j\in\mathbb Z$ and
computes, without exponentiation, the conservative projection

$$
B=\sum_j |nq_j|\left(
  \mathrm{bits}(\mathrm{num}x_j)
 +\mathrm{bits}(\mathrm{den}x_j)
\right).
$$

It admits exact powering only when one expression has at most 256 terms, every absolute cleared
exponent is at most 16,384, $B\le262{,}144$, and the admitted-coordinate aggregate projection is
at most $1{,}048{,}576$. These ceilings are far smaller than permission to exponentiate the
parser's 8,192-bit total count. A failed preflight records an unavailable exact-product decision
and falls back to the still-valid directed interval; it does not allocate a huge power and does not
turn absence of exact comparison into a sign claim. No prime-factorization claim is made.

The independent report-term checker follows the same plan/evaluate split: it parses bounded
rationals and computes every local projection plus the aggregate admission decision before calling
its rational-power primitive. Two sentinel controls replace that primitive with a function that
fails on any call, then exercise a locally rejected plan and an aggregate-rejected plan. Both
guards reject with zero power calls. This is executable ordering evidence, not a formal time or
space bound for Python or Rust.

## Five-lens audit

### Lens 1: SxPID definitional compatibility

The checker scans the complete-state count table for each of the four two-source nodes:

- $\{S_1\}$,
- $\{S_2\}$,
- $\{S_1,S_2\}$, and
- the redundancy disjunction $\{S_1\}\lor\{S_2\}$.

It repeats each scan with the keyed target restriction. It does not substitute intersection for
the redundancy disjunction. The atom order and integer two-source Möbius matrix are fixed to the
shared-exclusions lattice. The first three net cumulatives are also reconstructed independently as
ordinary empirical mutual-information products to challenge the self-redundancy identity.

This lens establishes compatibility with the encoded Makkeh--Gutknecht--Wibral definition. It does
not prove that shared exclusions is the unique or universally preferred PID measure. In
particular, exact arithmetic does not resolve known differences between SxPID and desiderata such
as the identity axiom on the independent two-bit copy, nor does it settle general multivariate
lattice-consistency questions.

### Lens 2: proof assumptions and formal algebra

The proof needs finiteness, positive exact arguments, positive integer $n$, empirical integer
multiplicities, and integer Möbius coefficients. Support outside the observed empirical table is
irrelevant to this arithmetic identity but remains essential for population inference.

`audit/formal/lean-exact-log-product/PidExactLogProduct.lean` kernel-checks the generic reduction,
sign equivalences, cross-argument cancellation, and the retained witness product:

1. `log` of a finite signed-power product is the corresponding integer log sum;
2. scaling gives the $\log R/n$ representation;
3. exact positivity is equivalent to $R>1$;
4. exact negativity is equivalent to $R<1$; and
5. exact zero is equivalent to $R=1$; and
6. $\log x+\log(x^{-1})=0$ for positive $x$, exhibiting a nonempty cancellation; and
7. the five rational factors in the retained total-count-eight witness multiply exactly to one.

The permitted Lean axiom basis is only `propext`, `Classical.choice`, and `Quot.sound`. The Lean
file intentionally does not formalize concrete SxPID events or the concrete Möbius matrix. The
five-factor theorem checks exact witness arithmetic, while the independent exact-rational and Rust
routes bind those factors to the SxPID2 unique-one net atom. That concrete binding is not a
consequence of the generic theorem.

### Lens 3: executable refinement

`audit/tools/certified-sxpid/scripts/check-exact-products.py` uses only the Python standard
library for its independent derivation. For every bounded table it:

1. scans all events directly;
2. checks event nesting and the local net ratio;
3. constructs all 24 exact rational products;
4. checks three direct-MI products;
5. checks atom net/component identities;
6. checks all multiplicative zeta reconstructions;
7. runs the live Rust certifier;
8. reconstructs a product from every emitted exact-term list;
9. checks the separate exact-product decision, witness, and bounded preflight evidence; and
10. treats the interval decision as interval-local, requiring exact-product consistency without
    forging an interval sign when the endpoints straddle zero.

The fixture, generator, checker sources, and live executable are SHA-256 bound in the emitted
qualification receipt. This is bounded cross-implementation refinement evidence, not a universal
Rust refinement theorem. Python's interpreter, arbitrary-precision integers, `Fraction`, the
checker sources, the live binary, and their host execution remain in the trusted computing base.

### Lens 4: numerical and statistical meaning

The product route is stronger than a floating-point sign heuristic because it decides sign and
zero without evaluating a transcendental function. It complements rather than replaces directed
rounding: a nonzero magnitude or interval still requires a certified logarithm.

The result is conditional on the supplied empirical table. It does not establish:

- that the table represents the intended variables;
- population support coverage;
- unbiasedness, consistency, or calibrated uncertainty;
- independence, stationarity, dependency-color, or drift premises;
- equality between quantized and original continuous estimands; or
- downstream scientific or operational validity.

A tiny exact empirical sign can still be statistically unstable. Exact arithmetic eliminates one
numerical ambiguity; it does not eliminate sampling uncertainty.

### Lens 5: adversarial falsification

The fail-closed self-test kills six source-semantic/arithmetic mutations:

1. source disjunction changed to intersection;
2. keyed target restriction inverted;
3. empirical row multiplicity discarded;
4. the synergy Möbius sign changed; and
5. net multiplication substituted for division; and
6. the exact rational sign comparator reversed.

It also kills thirteen certificate mutations, including the exact-product decision, zero witness,
projected-bit preflight record, and both strict interval/product endpoint boundaries, and rejects
four malformed structural cases, for 23 adversaries total. The strict consistency conditions are

$$
R>1\Longrightarrow U>0,\qquad
R<1\Longrightarrow L<0,\qquad
R=1\Longrightarrow L\le 0\le U.
$$

Thus an interval ending exactly at zero cannot be consistent with a strict positive product, and
an interval beginning exactly at zero cannot be consistent with a strict negative product.
Two additional sentinel controls prove that the auxiliary checker reaches its per-expression and
aggregate admission guards before its powering primitive; they are controls, not added to the 23
rejected-adversary count.

The exhaustive bounded corpus contains every nonempty binary count table with total count at most
four: 494 tables and 11,856 coordinates. The checker verifies 5,280 event constraints, 5,280 local
net identities, 1,482 direct-MI identities, 3,952 component-net identities, and 5,928 zeta
reconstructions. Exact products classify 5,886 zeros, 5,762 positive coordinates, and 208 negative
coordinates. Every live exact-product decision agrees; interval decisions remain a separate
endpoint-derived field.

The boundary exhaustion through total count eight adds 12,869 tables and 308,856 coordinates. It
retains 16 nonempty product-one cases at the first possible total, validates the live minimized
witness, and kills a self-consistently resealed false exact-product sign.

The deterministic evolutionary falsifier uses seed `0x5358504944322026`, total count 64,
population 96, and 96 generations. It evaluates 5,921 distinct larger tables with exact rational
fitness and post-certifies the final boundary candidate. It searches specifically for a negative
informative or misinformative **SxPID partial atom**. It found none. This is negative bounded
evidence, not a proof of universal partial-atom nonnegativity. If it finds a violation in a future
run, it performs deterministic deletion-one minimization and then exact live post-certification.

## Positive and negative findings

Positive findings:

- The exact product theorem applies separately to informative, misinformative, and net
  cumulatives and to every integer-Möbius atom.
- All 11,856 bounded coordinate products equal the independent products reconstructed from the live
  certificate's exact term lists.
- All bounded exact-product signs and zeros agree with independently reconstructed products, and
  none contradicts its directed interval. The two decision domains are intentionally distinct.
- The generic product/sign algebra and retained five-factor product identity are kernel-checked in
  Lean.
- The larger seeded search found no negative informative or misinformative SxPID partial atom.

Negative findings and counterexamples:

- Exact arithmetic does **not** make all SxPID values nonnegative. The exhaustive corpus contains
  208 negative net coordinates. Any blanket nonnegativity claim is false.
- A large number of coordinates are exactly zero (5,886), so tolerance-only zero classification
  would discard available exact information.
- Empty canonical terms are sufficient but not necessary for exact zero. The retained $n=8$
  five-term counterexample disproves the former empty-term-only completeness assumption.
- The route does not certify the scientific choice of SxPID, its population interpretation, or
  its fitness for a downstream authority path.
- The current Lean proof checks generic algebra only. Concrete event extraction, lattice binding,
  and code refinement remain separately challenged rather than formally derived end to end.
- Exact rational products can grow very large. The Rust route therefore has explicit term,
  exponent, per-expression projected-bit, and aggregate projected-bit preflights and records an
  unavailable exact-product decision when they fail.
- Evolutionary search is incomplete. Its failure to find a violation cannot replace a theorem.

## Reproduction

```text
python3 audit/tools/certified-sxpid/scripts/check-exact-products.py
python3 audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py
python3 audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py
python3 audit/tools/certified-sxpid/scripts/challenge-exact-products.py \
  --output audit/evidence/sxpid2-exact-product-evolutionary-challenge.json
python3 scripts/check-lean-exact-log-product.py
scripts/check-exact-log-product-sxpid2-pdf.sh --exact
scripts/check-exact-log-product-sxpid2-pdf.sh --cross-toolchain
```

All commands fail closed. The first command builds the locked audit certifier unless
`--no-build` or an explicit `--certifier` path is supplied.
