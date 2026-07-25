# Claim SX-CERTIFIED-AVERAGED-PID2-001, revision 1

## Record status

This packet was created on 2026-07-24 after the standalone Rust certifier and its independent
Python verifier had been implemented. It is retrospective. It was not preregistered, was not
executed under independent human custody, and is not a blind evaluation or evidence of scientific
priority.

The disposition is **conditionally supported, with external-assurance obligations open**. The
exact mathematical implication is supported by a prose proof and replayable checks. The verifier
implementation is not itself formally verified. The independent verifier and qualification
harness are committed unchanged at
`b8b9a48b88cb28d812d8cbd70b8f999a3bac5a8e`; exact source digests are recorded in
[bindings.md](bindings.md). Independent human custody and an external transparency record remain
open. See [decision.md](decision.md).

## Claim class

The categorical shared-exclusions functional is paper-defined by Makkeh, Gutknecht, and Wibral.
The canonical count-table schema, exact-expression representation, directed Rust producer,
certificate schema, independent integer/rational-log verifier, and assurance workflow are
project-defined.

This packet does not define a new PID measure and makes no priority claim for SxPID.

## Fixed objects

- Exactly two categorical sources, $S_1$ and $S_2$, and one categorical target, $T$.
- One accepted canonical finite empirical count table with positive exact integer counts.
- Definition revision
  `makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1`.
- Natural-logarithm units (nats).
- Four cumulative nodes in the order
  `(source_one, source_two, joint_sources, redundancy)`.
- Four atoms in the order `(unique_one, unique_two, synergy, redundancy)`.
- Informative, misinformative, and net components.
- The fixed event map, Möbius matrix, zeta matrix, schemas, and resource policy in
  [conventions.md](conventions.md) and [bindings.md](bindings.md).

These objects do not change during one accepted verification.

## Exact target statement

Let $B$ be input bytes accepted by the independent verifier, let
$X=\mathrm{normalize}(B)$ be their canonical count-table semantics, and let $C$ be
certificate bytes accepted for $B$. The verifier independently reconstructs 24 exact-real values

$$
F_j(X)=\sum_{r=1}^{m_j} a_{jr}\log q_{jr},
\qquad
a_{jr}\in\mathbb Q\setminus\{0\},
\quad
q_{jr}\in\mathbb Q_{>0}\setminus\{1\}.
$$

The values comprise 12 averaged cumulatives and 12 averaged atoms: four lattice coordinates for
each of the informative, misinformative, and net components.

Let the certificate's normalized dyadic interval for coordinate $j$ be

$$
I_j(C)=[L_j,U_j].
$$

The target implication is:

> If `verify_certificate.py` returns status `verified` for the pair $(B,C)$ and the locally bound
> certifier source tree, then, under the stated trust assumptions for the verifier implementation,
> Python's exact-integer and `Fraction` semantics, JSON/SHA-256 primitives, and the reviewed
> logarithm-tail argument, every reported interval contains the independently reconstructed
> exact-real averaged categorical SxPID2 coordinate:
>
$$
\forall j\in\{1,\ldots,24\},\qquad L_j\leq F_j(X)\leq U_j.
$$

Acceptance additionally proves, within the same conditional route, that:

1. the input and certificate satisfy their exact versioned schemas;
2. the input digest, payload digest, exact-term digests, lattice digest, precision-policy digest,
   source-manifest digest, and lockfile digest recompute as required;
3. the independently reconstructed exact terms equal the certificate terms coordinate by
   coordinate;
4. the fixed zeta matrix reconstructs every cumulative from the atoms;
5. the three nonredundancy net cumulatives equal independently reconstructed empirical mutual
   information expressions;
6. the independently derived rational-log enclosure is a **subset** of $I_j$, not merely
   overlapping it; and
7. every $I_j$ has width at most $2^{-160}$ under the pinned policy.

This implication does not require the Rust producer's Rug/MPFR/GMP arithmetic or compiled
toolchain to be correct for value containment. Producer arithmetic, expressions, lattice fields,
sign labels, and endpoint-generation correctness are not trusted for value containment. The
parsed endpoints remain inputs defining $I_j(C)$; their correctness is not assumed because
acceptance requires an independently derived $J_j\subseteq I_j(C)$. Those components remain
relevant to the producer-only route and to reproducibility, not to the final
independent-containment inference.

## Premises

1. The intended SxPID event semantics and the formulas in [conventions.md](conventions.md) are the
   correct paper-defined two-source averaged categorical functional.
2. The independent verifier source faithfully implements those formulas, exact rational
   arithmetic, the fixed lattice, and the stated rational-log tail bound.
3. Python arbitrary-precision integers and `fractions.Fraction` have their documented exact
   semantics for the executed program.
4. The executed Python source is the source whose digest is recorded in the verification report.
5. JSON parsing, UTF-8/ASCII handling, SHA-256, filesystem reads, and the operating environment
   behave as assumed by the verifier.
6. The consumer requires a complete successful verifier result and does not infer acceptance from
   a partial output, a producer exit code alone, or certificate overlap alone.

These premises are explicit. They are not converted into attestations by the certificate.

## Excluded claims

This packet does not establish:

- refinement or numerical correctness of `pid-core` binary64 output;
- statistical or population validity, support recovery, sampling assumptions, consistency,
  calibration, confidence coverage, or causal interpretation;
- downstream scientific, monitoring, safety, authorization, or policy validity;
- three-source or four-source SxPID;
- continuous KSG, continuous shared exclusions, or continuous PID;
- pointwise SxPID;
- fitted quantization or equivalence to an unquantized estimand;
- $I_{\min}$ PID;
- authenticity, provenance, ownership, or scientific meaning of the input data;
- correctness of Python, the operating system, JSON or SHA-256 libraries, or the verifier source;
- correctness of Rug, MPFR, GMP, rustc, Cargo, compiler wrappers, the linker, the native compiler,
  the target ABI, or the producer executable;
- executable, native-archive, or independently archived source identity;
- independent-human review, custody, or execution; or
- formal verification of this verifier, the certifier, or all of `pid-rs`.

## Falsifiers

The target implication is false if an accepted pair $(X,C)$ can be produced for which:

1. one independently defined $F_j(X)$ lies outside $I_j(C)$;
2. the verifier's event union or target restriction differs from the fixed SxPID semantics;
3. the verifier accepts an altered count table with a certificate for another table;
4. the fixed matrices do not implement the stated two-source lattice;
5. the rational-log series or tail bound fails to enclose a positive rational logarithm;
6. fixed-point outward rounding is inward for any accepted operation;
7. Python boolean/integer coercion bypasses a typed certificate equality;
8. malformed Unicode or noncanonical JSON changes the semantic object without rejection; or
9. a mutable or different verifier source is executed while the report asserts the recorded
   source digest.

Named negative controls are retained in
[failures/retained-negative-controls.md](failures/retained-negative-controls.md). Passing them is
evidence of fault sensitivity, not a proof that no other falsifier exists.

## Evidence needed for stronger closure

A stronger statement such as “formally verified executable SxPID2” would require, at minimum:

1. a kernel-checked specification of the exact count-table event semantics and fixed lattice;
2. a refinement proof from accepted bytes through exact-expression reconstruction;
3. a checked proof of the rational-log series and fixed-point enclosure implementation;
4. a verified or independently checked runtime for the acceptance path;
5. an immutable committed source snapshot and reproducible artifact manifest;
6. execution under independent human custody; and
7. separate claims for `pid-core`, statistics, continuous estimators, or downstream use.

Those are not silently imported into revision 1.

## Novelty-safe description

Use:

> A project-defined, independently replayable exact-integer/rational-log containment checker for
> the paper-defined averaged two-source categorical SxPID functional on one canonical empirical
> count table.

Do not use “new PID,” “formally verified pid-rs,” “certified statistical inference,” or a
scientific-priority claim.
