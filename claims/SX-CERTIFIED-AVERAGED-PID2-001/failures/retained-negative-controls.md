# Retained negative controls for SX-CERTIFIED-AVERAGED-PID2-001

## Evidence rule

Negative controls record how the claim can fail and why each guard exists. A passing mutation
suite proves that the current gate detects the registered mutations. It does not prove that all
possible faults have been enumerated.

## NC1: Source disjunction is not joint-source intersection

For the four equally weighted XOR states

$$
(0,0,0),\ (0,1,1),\ (1,0,1),\ (1,1,0),
$$

and key $(0,0,0)$:

$$
|E_1\cup E_2|=3,
\qquad
|E_1\cap E_2|=1.
$$

The informative local arguments are therefore $4/3$ and $4$. Replacing redundancy masks `[1,2]`
with joint mask `[3]` changes the functional. The independent verifier qualification mutates this
field, reseals all relevant digests, and rejects the certificate.

A subtler retained source mutant replaces the target-restricted inclusion--exclusion mass

```text
source_one_target + source_two_target - keyed_count
```

with `max(source_one_target, source_two_target)`. Nesting checks, exact net-ratio identities, all
three direct-MI identities, and the symmetric XOR example still pass. A direct row scan of all
twelve cumulative event expressions over the 494-table corpus rejects it. This counterexample is
why zeta self-consistency and direct MI alone are not described as complete event-semantic
evidence.

## NC2: Python boolean/integer coercion is unsound for schema equality

In Python, `True == 1`. A generic equality test can therefore accept a boolean where a JSON integer
value of one is required.

Two retained mutations replace:

1. the numeric target-state width by `true`; and
2. one lattice coefficient equal to one by `true`, followed by lattice and payload resealing.

The verifier uses type-strict recursive equality and explicit integer parsing that rejects
booleans. Both mutations fail closed.

## NC3: Transient cumulative growth can exceed the final term budget

A 410-row canonical table with rows

```text
(source_one="s0000".."s0409", source_two="constant", target="constant",
 count=1..410)
```

creates 1640 transient cumulative terms. The pinned incremental ceiling is 1638.

Checking only final atom expressions after cancellation would allow resource amplification before
the final bound. Both producer and independent verifier enforce the cumulative limit while
extracting rows. The retained fixture is rejected with:

```text
cumulative extraction reached 1640 terms; maximum is 1638
```

## NC4: A low Python integer-text limit must not change acceptance silently

Producer-valid counts may contain up to 1024 decimal digits. Some Python runtimes impose a lower
integer-to-text conversion limit. The qualification temporarily sets that limit to 640 and
supplies a canonical 1000-digit count.

The verifier rejects before parsing unless the runtime limit is unlimited or at least 4096. It
does not silently narrow the producer's accepted count domain.

## NC5: A lone Unicode surrogate is not a canonical token

A JSON string can spell a lone surrogate through an escape such as `\ud800`. It is not valid
canonical ASCII state content and can also cause later UTF-8 encoding failures.

The retained structural adversary uses such a token. The verifier rejects it at the token
contract, before semantic reconstruction or canonical hashing.

## NC6: Interval overlap is not containment

Suppose the exact value is $3$, a producer claims $[0,2]$, and a reference interval is
$[1.9,3.1]$. The intervals overlap, yet the producer interval excludes the truth.

The independent verifier therefore requires

$$
J_{\mathrm{independent}}\subseteq I_{\mathrm{certificate}}.
$$

The bounded Rust Decimal fixture remains agreement evidence only; it is not used as a proof
interval.

## NC7: Negative coefficients reverse interval endpoints

If $x\in[1,2]$ and $a=-1$, then $ax\in[-2,-1]$. Reusing the positive-coefficient order yields the
invalid pair $[-1,-2]$.

Möbius inversion creates negative coefficients. The Rust static-policy suite retains mutations
that remove endpoint swapping, while the independent verifier constructs signed sum bounds with
exact-integer outward operations.

## NC8: A self-consistently resealed forged expression is still false

Changing an exact coefficient and recomputing:

- the coordinate expression digest;
- the aggregate coordinates digest; and
- the certificate payload digest

produces an internally self-consistent forgery. Digest checks alone cannot detect it.

The independent verifier reconstructs the expression from the original count table and rejects
the forged terms.

## NC9: A certificate cannot be reused for another table

The retained changed-input mutation increments one count while preserving the original complete
certificate. The original report remains self-consistent, but its raw and semantic input digests
and reconstructed exact terms no longer match.

The verifier rejects the pair.

## NC10: Exact zero and strict sign need separate evidence

An interval $[0,\varepsilon]$ does not prove strict positivity, and
$[-\varepsilon,0]$ does not prove strict negativity. A false-zero mutation replaces a nonzero
coordinate interval with $[0,0]$ and reseals the payload. A separate mutation forges the sign label.

The verifier derives the expected label from exact expression and dyadic bounds and rejects both.
An empty exact-term map is a sound but incomplete zero witness.

A narrower mutation takes a certified-positive coordinate and sets its upper endpoint equal to its
own reported downward-rounded lower endpoint. Its schema, width, normalization, and positive sign
remain plausible. Only the independent subset-containment proof rejects it. This isolates the
guard that the route claims.

## NC11: Canonical dyadics and bounded exponents are part of the proof object

The suite retains:

- zero with a nonzero exponent; and
- a nonzero endpoint with exponent $-65537$.

The first is a noncanonical representation. The second exceeds the verifier's proof-resource
bound. Both are rejected before containment.

## NC12: Reported resource evidence must be recomputed

Changing `total_exact_terms` or
`estimated_exact_term_json_bytes_upper_bound` by one and resealing the payload produces plausible
but false evidence. The verifier independently counts terms and recomputes the estimate. Both
mutations are rejected.

## NC13: Claim and build evidence cannot be broadened by certificate text

The suite mutates and reseals:

- the permitted claim;
- arithmetic/native-version status;
- build-context scope; and
- distribution route.

The verifier compares these fields with exact bounded constants. A certificate cannot promote
source-only, non-exhaustive evidence into a binary attestation.

## NC14: Other registered certificate mutations

The remaining current semantic mutations are:

- noncanonical dyadic endpoint;
- forged sign decision;
- duplicate coordinate identity;
- forged source-manifest digest;
- false target-width flag;
- inconsistent precision trace; and
- build-host text inconsistent with the embedded `rustc -vV` record; and
- changed-input reuse.

Together with the cases above, the 2026-07-24 independent suite reports 21 killed semantic
mutations: 20 resealed certificate mutations and one input/certificate mismatch.

## NC15: Fixed-point source mutation

A retained source mutant subtracts 70 fixed-point units from the upper endpoint of the reduced
$\ln 2$ enclosure. The separate exact-`Fraction` partial-sum and rational-tail qualification
rejects this small loss of outwardness. This negative control shows sensitivity to that named
source fault; it does not establish which other evidence routes would accept the mutant. The
975-case logarithm grid remains a distinct evidence layer rather than another
producer-certificate comparison.

## NC16: Cross-artifact binding adversaries

The qualification requires intended-path rejection after:

- changing the verifier source after module import; and
- changing and rehashing the standalone Cargo manifest so that the Rug dependency contract is no
  longer exact;
- adding and rehashing a Cargo `[patch]` source substitution; and
- replacing and rehashing the locked Rug checksum.

These four controls test source/runtime and manifest/report binding. They are not counted as
certificate semantic mutations.

## NC17: Structural adversaries outside the 21 count

The verifier also rejects:

- duplicate JSON object keys;
- the lone-surrogate token;
- the 1640-term transient-growth table; and
- the low Python integer-text-capacity environment; and
- an invalid POSIX filename byte through one bounded canonical CLI rejection; and
- the complete CLI started with an insufficient integer-text limit.

These are retained structural/environment adversaries. They are not included in the reported
21 semantic-mutation total. Separate invocation controls require a symlinked verifier path to bind
the real source and a closed stdout to return transport status 1 without a traceback.

## NC18: Static-policy mutations are a distinct layer

The Rust source-policy self-test kills 34 representative mutations spanning:

- arithmetic and rounding;
- sign boundaries;
- source closure and compile-time inclusion;
- an explicit unsafe-function surface;
- build routing and native feature boundaries;
- vector and count-event semantics;
- lattice algebra; and
- resource/report acceptance.

This evidence protects a different layer from the Python semantic mutation suite. Neither suite
is a formal proof.

## Replay boundary

All controls are deterministic and local. They do not establish:

- absence of unnamed faults;
- correctness of the Python interpreter or Rust toolchain;
- independent authorship or custody;
- population/statistical validity; or
- `pid-core`, continuous, pointwise, quantized, or higher-source correctness.
