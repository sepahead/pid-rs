# Claim SX-CERTIFIED-AVERAGED-PID2-001, revision 3

## Record status

Revision 3 re-adjudicates revision 2 after a change to the independent verifier's
loaded-execution digest, its runtime-integrity qualification, and the independent-verification
schema. These are revision-2 re-adjudication triggers. Revisions 1 and 2 remain historical and
are not silently rewritten.

This revision is retrospective. It was not preregistered, has not been executed under independent
human custody, and does not yet have a fresh public green CI rerun or an external transparency,
authorship, binary-attestation, or archive record. The disposition is **conditionally supported
for the same two narrow per-input implications as revision 2, with integration, external, and
formal assurance obligations open**. See [decision-v3.md](decision-v3.md).

## Exact revision delta

The independent-verification schema is
`pid-rs/certified-sxpid-independent-verification/v3`. Before serializing live module-owned code,
the verifier now primes the nonsemantic string-intern state of the code-object strings and nested
constants that enter its loaded-execution digest. The digest domain is
`pid-certified-sxpid-independent-loaded-execution-v3\0`. Its typed constant-state encoding binds
all 51 declared uppercase semantic/configuration globals by name rather than relying on a
positional, manually selected subset.

This change addresses a fail-closed false rejection observed on CPython 3.11.15. The observation,
failing source bytes, candidate source bytes, and open rerun status are retained in
[`audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md`](../../audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md).

The following objects are unchanged from revision 2:

- input schema `pid-rs/categorical-sxpid2-count-table/v1`;
- definition revision `makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1`;
- producer report schema `pid-rs/certified-sxpid-report/v2`;
- exact-expression schema `pid-rs/exact-log-linear/v1`;
- resource policy `sxpid2-certification-default-v2`;
- natural-logarithm units;
- the fixed two-source event map, coordinate order, Möbius and zeta matrices;
- rational-log range reduction, series, tail, and containment rule;
- denominator clearing, product preflight, comparison, statuses, decisions, and witness; and
- every mathematical, exhaustive, mutation, search, and Lean evidence count from revision 2,
  except that the independent-verifier harness now reports two additional loaded-execution
  cache/code controls, 51 post-import semantic-constant mutations, and, on the affected CPython
  3.11 route, one cache-normalization source mutation.

Revision 3 defines no new PID measure and makes no scientific-priority claim.

## Fixed mathematical object

For one accepted canonical finite empirical count table with exactly two categorical sources and
one categorical target, the verifier reconstructs exactly 24 averaged coordinates: informative,
misinformative, and signed-net components of four cumulative nodes and four atoms. Each coordinate
has the exact form

$$
F_j(X)=\sum_r a_{jr}\log q_{jr},
\qquad
a_{jr}\in\mathbb Q\setminus\{0\},
\quad
q_{jr}\in\mathbb Q_{>0}\setminus\{1\}.
$$

After the common empirical denominator $n>0$ is cleared, every admitted product comparison uses

$$
R_j(X)=\prod_r q_{jr}^{n a_{jr}},
\qquad
F_j(X)=\frac{1}{n}\log R_j(X).
$$

The mathematical object and both implications below are inherited without enlargement from
[claim-v2.md](claim-v2.md).

## Target implication A: interval containment

Let $B$ be input bytes accepted by the revision-3 independent verifier and $C$ be a
revision-2 producer certificate accepted for $B$. For coordinate $j$, let the producer's
normalized dyadic interval be $I_j(C)=[L_j,U_j]$.

> If `verify_certificate.py` emits one complete revision-3 report with status `verified` for
> $(B,C)$ and the locally bound source tree, then, conditional on the reviewed verifier source,
> Python loader/compiler, code-object, `marshal`, `sys.intern`, exact-integer and `Fraction`
> semantics, JSON/SHA-256, filesystem/process behavior, and the reviewed rational-log enclosure
> proof, every interval contains the independently reconstructed exact coordinate; equivalently,

$$
\forall j\in\{1,\ldots,24\},\qquad L_j\le F_j(X)\le U_j.
$$

Acceptance requires the independent enclosure to be a subset of the producer interval. Numerical
overlap is insufficient.

## Target implication B: bounded exact zero and strict sign

For each coordinate whose independently reconstructed exact-product record has status `compared`:

> Conditional on the same verifier/runtime premises, the separately reported product decision is
> exact: `certified_exact_zero` implies $F_j=0$, `certified_positive` implies $F_j>0$, and
> `certified_negative` implies $F_j<0$.

The product decision does not replace the dyadic interval, enclose a nonzero magnitude, or rewrite
`interval.decision`. A record with status
`not_compared_per_expression_preflight_limit` or
`not_compared_total_preflight_limit` supplies no exact-product zero/sign claim.

## Loaded-execution integrity boundary

The pre-interning step removes only the observed dependence on lazy string-intern cache state from
the project-defined digest route. The typed constant-state encoding covers every one of the 51
declared uppercase semantic/configuration globals in the reviewed source. The qualification
harness separately requires:

1. digest equality between isolated cold and explicitly interned copies of the same dynamically
   constructed code constant;
2. rejection after a live function's `__code__` is replaced, followed by successful integrity
   recovery after restoration;
3. rejection and recovery for one post-import mutation of each of the 51 declared semantic
   constants; and
4. on CPython 3.11, intended-path failure of an isolated source mutant that removes the
   normalization call.

The two cache/code controls, 51 constant mutations, and affected-runtime source mutant show
sensitivity to the named cases. They do not prove:

- semantic equivalence of arbitrary Python programs;
- equality of digests across Python implementations, versions, marshal formats, builds, or
  platforms;
- correctness of CPython, `sys.intern`, `marshal`, code-object metadata, or the verifier;
- process immutability outside the inspected module-owned functions and semantic constants; or
- source-to-bytecode refinement, provenance, authorship, or executable identity.

The report records the Python implementation and version. A loaded-execution digest is local
drift evidence under that reported runtime, not a portable semantic hash.

## Excluded claims

Revision 3 does not establish:

- deductive refinement or numerical correctness of `pid-core` binary64 output;
- population validity, support recovery, sampling assumptions, consistency, bias, calibration,
  confidence coverage, uncertainty quantification, or causal interpretation;
- pointwise, quantized, $I_{\min}$, continuous, three-source, or four-source PID;
- a universal atom-sign or nonnegativity theorem;
- authenticity, provenance, ownership, or scientific meaning of input data;
- correctness of Python, Rust, Rug, MPFR, GMP, compilers, operating systems, JSON, SHA-256,
  `marshal`, `sys.intern`, or either verifier source file;
- cross-runtime digest identity, reproducible binaries, independent custody, external review,
  authorship, or transparency; or
- downstream scientific, monitoring, safety, authorization, or policy validity.

## Falsifiers

The revision-3 claim is false if an accepted revision-3 report exists for which a revision-2
mathematical falsifier holds, or if:

1. the loaded-execution digest changes solely because the qualified lazy string-intern cache state
   changes;
2. a post-import replacement of inspected live function code is accepted as unchanged execution;
3. any one of the 51 declared semantic/configuration globals can change after import without
   changing the loaded-execution digest;
4. the integrity check with the cache-normalization call removed treats the qualified cache
   transition as unchanged on the affected CPython 3.11 route;
5. a version-2 verification report is accepted as revision 3;
6. the report's source or loaded-execution digest does not describe the bytes/code checked by the
   accepted route; or
7. the cache normalization erases executable code, code-object metadata, or semantic constants
   that the declared digest is meant to retain.

Passing the named controls is fault-sensitivity evidence, not proof that no other falsifier exists.

## Novelty-safe description

Use:

> A project-defined, independently replayable exact-integer/rational-log containment checker with
> a separately bounded exact-rational zero/sign decision for the paper-defined averaged two-source
> categorical SxPID functional. Revision 3 normalizes one CPython loaded-execution cache-state
> artifact while retaining an explicit runtime trusted base.

Do not use “new PID,” “formally verified pid-rs,” “verified Python,” “portable semantic hash,”
“certified statistical inference,” “confidence interval,” or a scientific-priority claim.
