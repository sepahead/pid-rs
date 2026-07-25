# Claim SX-CERTIFIED-AVERAGED-PID2-001, revision 2

## Record status

Revision 2 re-adjudicates revision 1 after intentional changes to the producer report schema,
independent-verification schema, resource policy, permitted-claim text, source manifest, verifier,
and sign-decision semantics. Those changes were all revision-1 re-adjudication triggers. Revision
1 remains recorded in [claim-v1.md](claim-v1.md), [decision.md](decision.md), and
[bindings.md](bindings.md); this document does not silently rewrite it.

This revision is retrospective. It was not preregistered, was not run under independent human
custody, and has no external transparency-log or binary-attestation record. The disposition is
**conditionally supported for the two narrow implications below, with external and formal
assurance obligations open**. See [decision-v2.md](decision-v2.md).

## Claim class and provenance

The categorical shared-exclusions functional is paper-defined by Makkeh, Gutknecht, and Wibral.
The canonical count-table schema, exact-expression representation, directed producer, dyadic
certificate, bounded rational-product comparison, independent verifier, resource policies, and
assurance workflow are project-defined. This packet defines no new PID measure, imports no atoms
or axioms from another PID proposal, and makes no scientific-priority claim.

## Fixed mathematical objects

- Exactly two categorical sources, $S_1,S_2$, and one categorical target, $T$.
- One accepted canonical finite empirical count table with positive exact integer counts.
- Definition revision `makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1`.
- Natural-logarithm units (nats).
- Four cumulative nodes `(source_one, source_two, joint_sources, redundancy)`.
- Four atoms `(unique_one, unique_two, synergy, redundancy)`.
- Informative, misinformative, and signed-net components.
- Exactly 24 averaged coordinates under the fixed event map and two-source Möbius lattice.

The version-2 executable bindings are in [bindings-v2.md](bindings-v2.md). The event and lattice
definitions remain those in [conventions.md](conventions.md).

The producer report schema is `pid-rs/certified-sxpid-report/v2`, the independent-verification
schema is `pid-rs/certified-sxpid-independent-verification/v2`, and the resource policy is
`sxpid2-certification-default-v2`. These identifiers are claim premises, not descriptive labels.

## Exact coordinate representation

For accepted normalized count-table semantics $X$ with total count $n>0$, the independent
verifier reconstructs every coordinate as

$$
F_j(X)=\sum_{r=1}^{m_j}a_{jr}\log q_{jr},
\qquad
a_{jr}\in\mathbb Q\setminus\{0\},
\quad
q_{jr}\in\mathbb Q_{>0}\setminus\{1\}.
$$

For this empirical averaging and integer Möbius transform, every cleared exponent

$$
e_{jr}=n a_{jr}
$$

is an integer. When the bounded exact-product preflight admits coordinate $j$, define the exact
positive rational

$$
R_j(X)=\prod_{r=1}^{m_j}q_{jr}^{e_{jr}}.
$$

Then finite logarithm identities give

$$
F_j(X)=\frac{1}{n}\log R_j(X).
$$

Because $n>0$ and the natural logarithm is strictly increasing,

$$
F_j=0\iff R_j=1,
\qquad
F_j>0\iff R_j>1,
\qquad
F_j<0\iff R_j<1.
$$

This equality is an exact-real identity for the frozen empirical object. It is not a sampling,
population, or downstream theorem.

## Target implication A: interval containment

Let $B$ be input bytes accepted by the revision-2 independent verifier and let $C$ be a
revision-2 producer certificate accepted for $B$. For coordinate $j$, let the certificate's
normalized dyadic interval be $I_j(C)=[L_j,U_j]$.

> If `verify_certificate.py` returns status `verified` for $(B,C)$ and the locally bound source
> tree, then, conditional on the reviewed verifier implementation, Python exact-integer and
> `Fraction` semantics, JSON/SHA-256 primitives, filesystem/process behavior, and the reviewed
> rational-log enclosure proof, every interval contains the independently reconstructed exact
> coordinate:
>
$$
\forall j\in\{1,\ldots,24\},\qquad L_j\le F_j(X)\le U_j.
$$

Acceptance requires an independently constructed rational-log interval to be a subset of the
producer interval. Numerical overlap is insufficient. This is the revision-1 containment claim
replayed under revision-2 schemas and source, not an inference from an old certificate.

## Target implication B: bounded exact zero and strict sign

For each coordinate whose independently validated exact-product record has status `compared`:

> The verifier reconstructs the coordinate expression from the input, checks integer denominator
> clearing, independently recomputes the exact positive rational product under the revision-2
> resource limits, and validates the producer evidence. Conditional on the verifier and runtime
> premises above, the recorded decision is exact:
>
> - `certified_exact_zero` implies $F_j(X)=0$;
> - `certified_positive` implies $F_j(X)>0$; and
> - `certified_negative` implies $F_j(X)<0$.

The product record is a separate decision lane. It does not replace the dyadic interval, enclose a
nonzero magnitude, or rewrite `interval.decision`. In particular, a nonempty log expression can
have exact product one while its narrow interval still reports `unresolved_sign`.

If a coordinate records `not_compared_per_expression_preflight_limit` or
`not_compared_total_preflight_limit`, no exact-product zero/sign claim is available. That bounded
abstention is not a certificate failure because implication A remains independently checked.

## Additional accepted facts

Within the same conditional route, successful verification also establishes that:

1. input, report, expression, and verification objects use their exact versioned schemas;
2. semantic/input/payload/expression/lattice/precision/source/lockfile digests recompute as
   required;
3. independently reconstructed exact terms equal certificate terms coordinate by coordinate;
4. the fixed zeta matrix reconstructs every cumulative from the atoms;
5. the three nonredundancy net cumulatives equal independently reconstructed empirical mutual
   information expressions;
6. each producer interval has width at most $2^{-160}$; and
7. every exact-product status, decision, witness, and preflight field equals independent
   reconstruction under the aggregate resource policy.

## Explicit premises

1. The formulas in [conventions.md](conventions.md) faithfully instantiate the intended
   paper-defined two-source averaged categorical SxPID functional.
2. The independent verifier source faithfully implements those event formulas, exact term
   reconstruction, fixed lattice, product comparison, rational-log enclosure, and schema checks.
3. Python arbitrary-precision integers and `fractions.Fraction` have their documented exact
   semantics in the executed program.
4. The executed verifier and locally read source tree are the bytes whose digests the verification
   route reports and checks.
5. JSON parsing, UTF-8/ASCII handling, SHA-256, filesystem reads, process execution, and the
   operating environment behave as assumed.
6. A consumer requires a complete successful verification result and never treats producer
   output, product preflight abstention, interval overlap, or an unverified sign string as
   acceptance.

## Excluded claims

Revision 2 does not establish:

- refinement or numerical correctness of `pid-core` binary64 output;
- population validity, sampling assumptions, support recovery, consistency, bias, calibration,
  confidence coverage, uncertainty quantification, or causal interpretation;
- authenticity, provenance, ownership, or scientific meaning of input data;
- correctness of Python, Rust, Rug, MPFR, GMP, Cargo, compilers, linkers, native libraries,
  operating systems, JSON, SHA-256, or the verifier source itself;
- executable/native-archive identity, reproducible binaries, independent custody, or authorship;
- pointwise, quantized, $I_{\min}$, continuous, three-source, or four-source PID;
- a universal sign or nonnegativity theorem for SxPID atoms;
- resolution of known SxPID desiderata or uniqueness questions; or
- downstream scientific, monitoring, safety, authorization, or policy validity.

## Falsifiers

The revision-2 claim is false if an accepted pair $(B,C)$ exists for which any of the following
holds:

1. an independently defined $F_j(X)$ lies outside its accepted producer interval;
2. an exact-product record with status `compared` has a decision different from the sign of
   $R_j-1$;
3. a product preflight abstention is accepted with a nonempty decision or zero witness;
4. integer denominator clearing is incorrectly accepted when some $na_{jr}\notin\mathbb Z$;
5. the producer or verifier powers a factor before the bounded preflight admits it;
6. the aggregate projected-bit ceiling is bypassed or recomputed inconsistently;
7. interval/product consistency accepts a positive product with $U_j\le 0$, a negative product
   with $L_j\ge 0$, or product one with $0\notin I_j$;
8. the source disjunction, target restriction, lattice, or coordinate order differs from the
   frozen semantics;
9. a changed input, expression, resource record, source manifest, or claim boundary is accepted
   after self-consistent resealing; or
10. a different verifier is executed while the verification report asserts the bound source.

The retained nonempty product-one example and mutation suite are fault-finding evidence for these
boundaries, not a proof that no other falsifier exists.

## Evidence needed for stronger closure

A stronger “formally verified executable” claim still requires a kernel-checked bridge from bytes
to event counts, exact expressions, bounded product comparison, rational-log enclosures, and
acceptance; verified or independently checked runtime semantics; immutable public source and
artifact bindings; and independent human custody. Statistical and downstream claims require
separate models and claim packets.

## Novelty-safe description

Use:

> A project-defined, independently replayable exact-integer/rational-log containment checker with
> a separately bounded exact-rational zero/sign decision for the paper-defined averaged two-source
> categorical SxPID functional on one canonical empirical count table.

Do not use “new PID,” “formally verified pid-rs,” “certified statistical inference,” “confidence
interval,” or a scientific-priority claim.
