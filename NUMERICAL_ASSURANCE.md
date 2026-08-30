# Represented-Binary64 Assurance for PID Reconstruction and Quantization

## Status and claim boundary

This note documents a numerical-assurance change in pid-rs. It changes implementation arithmetic,
resource estimates, diagnostics, serialized reports, and some final binary64 bits. It does **not**
change a PID estimand, a redundancy definition, a lattice, a paper-defined formula, or the units
(all information quantities remain nats). It is not a claim that the published work of Williams
and Beer, Makkeh, Gutknecht and Wibral, or Ehrlich et al. is wrong.

The central distinction is:

> Exact reduction of already represented binary64 operands is not exact estimation.

The inputs to a reduction may already contain empirical-PMF error, finite-sample estimator bias,
logarithm rounding, probability rounding, product rounding, nearest-neighbour error, or model
misspecification. The implementation removes one narrower error source: dependence of a selected
sum on an incidental order of the same represented operands.

The work has four outcomes:

1. a private, order-independent binary64 reduction primitive;
2. witnessed repairs to categorical SxPID final empirical-PMF averaging, categorical $I_{\min}$
   PID2 synergy, and continuous shared-exclusions PID2 synergy;
3. overflow-safe fitted equal-width edges and diagnostics that distinguish nominal, reachable, and
   observed labels; and
4. explicit negative dispositions that prevent the same arithmetic policy from being transferred
   to pointwise SxPID Möbius inversion or $I_{\min}$ PID3 without retained evidence of a defect.

## 1. Why the change was needed

PID reconstruction and averaging formulas contain cancelling sums. In exact real arithmetic, the
order of addition does not matter. In binary64 arithmetic it can matter because each intermediate
operation rounds. Reordering sources can reorder the weighted pointwise terms in an SxPID final
empirical-PMF average, or the represented terms in a two-source synergy residual, and alter one or
more last bits. That is undesirable when source exchange is part of the formula-level symmetry.

The defect is numerical, not statistical and not a flaw in a defining paper. For a fixed empirical
table, the old final reductions could evaluate the same represented multiset through two different
floating-point association trees. Compensated summation greatly reduces ordinary error but does
not define an order-independent result for every cancelling input. This observation alone does not
justify changing every compensated sum: the repository requires retained evidence at the actual
call site. The retained bounded pointwise SxPID suites establish only tolerance agreement, and the
larger raw-bit SxPID and $I_{\min}$ PID3 probes were not retained; neither route justifies a broader
scalar change.

Fitted equal-width quantization had a different boundary. The mathematical interpolation

$$
e_j = m + \frac{j}{B}(M-m), \qquad 0 \leq j \leq B,
$$

can encounter binary64 subtraction overflow when finite endpoints have opposite extreme signs.
At the other end of the scale, a requested partition can be finer than the representable values
between adjacent endpoints. The resulting repeated edges are not necessarily an implementation
failure, but treating all $B$ nominal labels as usable obscures the fitted map actually applied.

## 2. Exact reduction of represented operands

### 2.1 Integer model of every finite binary64 value

Every finite binary64 number is an integer multiple of $2^{-1074}$. The reducer decodes a finite
operand into its sign, 52 stored fraction bits, and exponent. A normal value contributes the hidden
leading bit; a subnormal does not. The resulting nonnegative integer significand is shifted into a
fixed unsigned limb array at the common $2^{-1074}$ scale.

The largest finite binary64 magnitude occupies 2,098 bits at that scale. Each accumulator instance
tracks accepted operands and rejects a call beyond `usize::MAX`; production reductions are also
bounded by Rust collection lengths. Adding `usize::BITS` carry capacity is therefore sufficient.
The compiled array length is

$$
L = \left\lceil\frac{2098 + \mathtt{usize::BITS}}{64}\right\rceil = 34
$$

on supported 32- and 64-bit targets. Positive and negative magnitudes are stored separately. This
avoids a signed-integer corner case and makes exact cancellation explicit.

### 2.2 One correctly rounded result

Finalization compares the positive and negative integers, subtracts the smaller magnitude from the
larger, and rounds the exact signed difference once to binary64. It keeps the leading 53-bit
significand and evaluates the guard and sticky bits. A halfway case increments only when the
retained significand is odd, implementing round-to-nearest, ties-to-even.

For finite operands $x_1,\ldots,x_n$, the intended arithmetic contract is therefore

$$
\mathrm{reduce}(x_1,\ldots,x_n)
= \mathrm{RN}_{\mathrm{even}}\!\left(\sum_{i=1}^{n} x_i\right),
$$

where the sum inside the parentheses is the exact real sum of the **represented binary64
operands**. Permuting those operands cannot change the result. Exact cancellation is canonicalized
to positive zero. A non-finite input is rejected. If the exact sum rounds beyond the finite
binary64 range, estimator-facing callers reject the infinity as numerical instability.

This contract does not claim that an input $x_i$ equals the exact mathematical quantity it was
intended to approximate.

### 2.3 Bounded conformance oracle

The committed same-project generator uses only the Python standard library. It converts binary64
payloads to exact integers and `Fraction` values, forms the exact rational sum, and implements
ties-to-even binary64 rounding along a separate code route. The fixture includes the four-term PID
residual cases as well as variable-arity streaming challenges at lengths 0, 1, 2, 3, 5, 63, 64,
and 65. It covers signed
zero, subnormals, normal-boundary transitions, long carry chains, cancellation, halfway rounding,
overflow, and deterministic stress cases. Every four-term case is tested under all 24
permutations; the 63--65-term cases are replayed in their original order, reverse order, and
one-position left and right rotations.

The generator does not import pid-rs. Normal and optimized-Python no-write runs verify the fixture
and its SHA-256 sidecar. A separate Rust custody test binds the live generator bytes to the pinned
snapshot, and Rust replays every case through both the array helper and streaming accumulator.

This is finite-corpus implementation-conformance evidence. It is not a universal proof, a formal
Rust refinement theorem, an independent external review, or a numerical bound for a PID estimator.

## 3. Measure-specific applications without semantic transfer

### 3.1 Categorical shared-exclusions PID

For a fixed pointwise realization and redundancy-lattice node $\alpha$, categorical SxPID has
informative and misinformative cumulative components. Möbius inversion has the exact-real form

$$
\pi^{\pm}(\alpha)
= I_{\cap}^{\pm}(\alpha)
- \sum_{\beta \prec \alpha}\pi^{\pm}(\beta).
$$

The pointwise Möbius inversion retains its established compensated reduction. pid-rs now averages
each already represented pointwise component through

$$
\bar\pi^{\pm}(\alpha)
= \sum_x \widehat p(x)\,\pi^{\pm}_x(\alpha)
$$

using the exact represented-binary64 reducer. Each product
$\widehat p(x)\pi^{\pm}_x(\alpha)$ is already rounded before it enters the accumulator. Thus this
change makes the final sum of a fixed product multiset order independent; it does not change the
pointwise atom bits. The signed net remains informative minus misinformative and may be negative;
it is never clamped.

This is a project-defined arithmetic policy in pid-rs's evaluator of the paper-defined categorical
shared-exclusions functional. It does not change the paper's functional, and it does not transfer a
theorem, interpretation, or atom value to Williams--Beer $I_{\min}$, BROJA, MMI, continuous shared
exclusions, or another PID.

#### Negative result: no promoted pointwise Möbius change

An earlier candidate also applied the exact reducer inside pointwise Möbius inversion. The three
pinned SxPID witnesses did not support that broader change: committed tests now require every
mapped pointwise informative, misinformative, and net payload in those exact two-, three-, and
four-source tables to be raw-bit identical under the named source exchange, while exactly reducing
only their old weighted pointwise terms reproduces each repaired average payload. This is a
three-table statement, not a general raw-bit theorem; the bounded general suites deliberately use a
floating tolerance and contain a signed-zero bit counterexample.

A temporary, uncommitted release-mode red-team probe then exercised the parent through public APIs.
Its executable and raw log were not preserved, so the counts below are an append-only historical
observation with **zero current release-evidence credit**. For every
table it compared every source transposition after mapping lattice keys, and compared informative,
misinformative, and derived-net pointwise payloads. The two- and three-source probes exercised both
specialized and general-$n$ paths; four sources has only the general path. It found no witness in:

- SxPID2: all 43,757 nonempty binary count tables through total mass 10, 200,000 random binary
  tables and 50,000 random ternary tables through mass 128, using `xorshift64` seed
  `0x2c125a22900d0001` and ternary seed `0xb225239bef477c14`;
- SxPID3: all 20,348 nonempty binary count tables through total mass 5, 75,000 random binary tables
  and 10,000 random ternary tables through mass 96, using seed `0x3c125a33900d0002` and ternary
  seed `0xa225238aef477c17`; and
- SxPID4: all 6,544 nonempty binary count tables through total mass 3. No random SxPID4 result is
  claimed because the unlogged phase was interrupted rather than retained as evidence.

In total, the unqualified run reported 405,649 tables, 194,865,076 mapped pointwise atom pairs, and
584,595,228 component payload comparisons. Those totals are not independently replayable and must
not appear in a qualification numerator. The durable evidence is narrower: tolerance-based bounded
suites, exact raw-bit assertions for the three named final-average witnesses, the retained seeds and
recipe above, and the decision not to promote an unwitnessed change. Pointwise Möbius inversion
therefore remains on the prior compensated path. This prevents unnecessary scalar churn and
prevents a general arithmetic capability from being mistaken for evidence that every
eligible-looking call site needed modification.

### 3.2 Williams--Beer $I_{\min}$ PID2

$I_{\min}$ is a different redundancy measure. Its two-source algebra uses

$$
U_1=I_1-R,\qquad U_2=I_2-R,
$$

and

$$
S=J-I_1-I_2+R,
$$

where $I_1=I(S_1;T)$, $I_2=I(S_2;T)$, $J=I(S_1,S_2;T)$, and $R$ is Williams--Beer redundancy.
Only the four-operand represented synergy sum receives the new reduction contract. No
shared-exclusions axiom or interpretation is imported.

For every valid public call, each observed target produces one target-specific value in every
source table. The implementation now treats violation of that private totality invariant, a
target/value length mismatch, or a non-finite stored value as `NumericalInstability` instead of
silently substituting zero. This changes no admitted result: the two-source accumulation and the
three-source Neumaier order remain identical. It is an implementation fail-closed repair, not an
observed estimator defect and not a correction to the Williams--Beer definition.

The three-source $I_{\min}$ Möbius path deliberately retains its earlier compensated reduction.
An uncommitted exhaustive search reported no $S_0\leftrightarrow S_1$ atom-bit witness among
245,156 nonempty binary count tables through total mass seven. An internal release-mode red-team
probe against exact
source commit `01466e88b0550333c2718f1716289e9642e30dc6` then evaluated 200,000 additional
valid binary tables with totals uniformly selected from 8 through 512 and compared every table
under all three source transpositions. It used four
50,000-case `xorshift64` streams seeded by `0x4f035cfaa1c89380`, `0x3c5f333ec24fa33f`,
`0xedab1672e4c2b2aa`, and `0xdae7ecb60541c241`; two of every three iterations used uniform
`raw & 15` cell selection and one used an intentionally uneven restricted-cell mapping. It found
no mismatch for $S_0\leftrightarrow S_1$, $S_0\leftrightarrow S_2$, or
$S_1\leftrightarrow S_2$. Neither executable nor raw log was retained, so both totals have zero
current release-evidence credit. They are preserved only as unqualified historical observations and
do not prove global bit equivariance or rule out a larger witness. The durable conclusion is the
conservative one: current retained evidence does not justify changing stable $I_{\min}$ PID3 scalar
bits merely because a measure-neutral arithmetic primitive exists.

### 3.3 Continuous shared-exclusions PID2

Continuous PID2 uses the Ehrlich-et-al. shared-exclusions redundancy estimate and three separately
estimated KSG mutual-information coordinates. Its represented synergy is now defined as

$$
S_{64}=\mathrm{RN}_{\mathrm{even}}
\bigl(\mathrm{exact}(J_{64}-I_{1,64}-I_{2,64}+R_{64})\bigr).
$$

The subscript emphasizes that the four inputs are already represented binary64 estimates. The
change does not remove their distinct finite-sample biases, validate a support declaration, or
turn the estimator into an exact-real PID.

`Pid2Result::from_estimate` also reconstructs the supplied $I_1$, $I_2$, and $J$ coordinates from
the separately rounded atoms. The three reconstructed sums use the same exact represented-input
reducer over respectively two, two, and four atom operands; together with the four-operand synergy
sum, construction performs four reductions over 12 represented addends. Exact reduction can change
whether the public constructor admits or rejects a tuple. It fails closed if any reconstruction
lies outside an inclusive 32-position ordered-binary64 guard. This inherited project policy is not
a derived identity, representability, forward-error, conditioning, relative-accuracy, or
statistical bound. Against a reconstructed positive zero, its near-zero boundary accepts an
expected positive-subnormal payload 32 and rejects payload 33.
Because the ordered mapping distinguishes signed zeros, it instead accepts negative payload 31 and
rejects negative payload 32. Accepted boundary cases have complete relative loss. The guard must
therefore not be presented as verified identity or representability. Synergy is not perturbed to
conceal rounding in the two unique atoms.

This threshold's 32 ordered-binary64 **positions** is unrelated to the KSG integer-harmonic
fixture's separate `32 * f64::EPSILON`-**nat** finite-corpus ceiling. They measure different
objects, use different units, and provide no evidence for one another.

Revision-4 assurance closes the declared exponent family rather than retaining a single scaling
example. There are 1,023 distinct finite seed tuples, indexed by `k = 1,...,1023`. Every seed is
accepted, and exact multiplication of all four represented coordinates by its corresponding
power of two maps it to the same finite-input endpoint whose atom reconstruction overflows and is
rejected. The `k = 4` member is the named multiplication-by-16 example. This proves that the
project compatibility policy is not homogeneous under that synthetic represented-coordinate
scaling family. It does **not** prove a scale defect in a PID measure, a valid probability-law or
source-coordinate transformation, an estimator-level gauge result, or a defect in Ehrlich et al.

The complete assumptions, exact bit patterns, symbolic family derivation, representative cases,
signed-zero census, conditioning branches, Neumaier and left-association negative controls, cost,
host/API expectations, verification layers, and nonclaims are in
[`PID2_REPRESENTED_COORDINATE_ASSURANCE.md`](PID2_REPRESENTED_COORDINATE_ASSURANCE.md). The earlier
bounded search that found no Neumaier discriminator remains useful negative historical evidence;
the exact counterexamples now supersede only its absence-of-witness conclusion. They do not turn
that bounded search into a general statement about Neumaier summation.

## 4. Reproducible counterexamples

Sections 4.1--4.4 use valid empirical count tables rather than synthetic non-PID operand lists; cell
order is lexicographic in the listed binary state bits, with the target bit last. Section 4.5 is
deliberately different: it is a represented-coordinate public-constructor tuple, not retained
estimator output.

### 4.1 Two-source categorical SxPID

For cells $(S_1,S_2,T)$, use

```text
[0, 1, 1, 1, 2, 1, 5, 1]    n = 12
```

Before the repair, source exchange changed the **averaged** synergy net from hexadecimal payload
`0x3fb41d4d04f468e3` to `0x3fb41d4d04f468e4`. The repaired specialized and general paths, with and
without pointwise retention, all select `0x3fb41d4d04f468e3` for the exact sum of the represented
weighted pointwise terms. The mapped pointwise atoms were already bit-identical for this table.

### 4.2 Three-source categorical SxPID

For cells $(S_0,S_1,S_2,T)$, use

```text
[4, 0, 3, 2, 1, 1, 0, 4, 0, 0, 1, 1, 3, 4, 0, 0]    n = 24
```

Under $S_0\leftrightarrow S_1$, averaged atom key $\{1,6\}$ maps to $\{2,5\}$. The repaired
informative, misinformative, and net payloads on both sides are

```text
0x3fa3b0124a6b77db  0x3f8a61d97c813f4d  0x3f9a2f37d6965010
```

### 4.3 Four-source categorical SxPID

For cells $(S_0,S_1,S_2,S_3,T)$, use

```text
[4,4,3,1,1,4,5,0,5,3,2,0,0,1,1,2,3,1,3,0,3,2,3,4,0,2,5,4,3,2,3,1]
n = 75
```

The averaged atom $\{1,4,10\}$ maps to $\{2,4,9\}$ under $S_0\leftrightarrow S_1$. Before repair,
source exchange changed the mapped misinformative payload from `0x3f721964bc3d4223` to
`0x3f721964bc3d4222` and the net from `0x3f316092e5b5f2a0` to `0x3f316092e5b5f2b0`. The repaired
values on both sides are

```text
informative     0x3f732f6dea98a14d
misinformative  0x3f721964bc3d4223
net             0x3f316092e5b5f2a0
```

### 4.4 Two-source categorical $I_{\min}$

Use the twelve rows

```text
S1 = [2,1,0,2,0,0,2,1,0,2,1,0]
S2 = [2,2,3,2,1,1,0,3,3,2,2,0]
T  = [2,0,1,0,2,0,0,1,2,2,1,0]
```

The pinned payloads in result-field order
$(R,U_1,U_2,S,I_1,I_2,J)$ are

```text
3fcb65a8c841cbb6 3fa14cc29dd51034 3fc31cb2a6c6c002 3fc65cf895b1f81f
3fcfb8d96fb70fc3 3fd7412db78445dc 3fe24ca12b0bf1f9
```

Before repair, source exchange changed the mapped synergy from `0x3fc65cf895b1f81e` to
`0x3fc65cf895b1f81f`. The repaired result selects the latter payload on both sides, preserves every
symmetric coordinate bit-for-bit, and swaps only the two unique coordinates.

The retained boundary suite additionally enumerates all 12,869 nonempty binary
$(S_1,S_2,T)$ count tables of total mass one through eight. Exact rational-product comparison finds
5,070 target-specific minimum-tie events—that is, supported `(table, target-value)` pairs, not
5,070 distinct tables—split by total mass as

```text
8, 36, 104, 230, 464, 800, 1,344, 2,084
```

and symmetrically as 2,535 tie events for each target value. All seven public scalar fields are bitwise
source-exchange equivariant on that bounded census. The suite also retains CE-003 as an exact tie
while confirming that no internal argmin or tie field is public, an exact-zero no-clamp witness,
and a positive-synergy witness whose exact exponentiated eight-sample ratio is
$823543/800000>1$. Direct, budgeted, cancellable, fitted-quantized, and same-sample wrapper routes
agree on the selected source-exchange witness. These are finite implementation results; the census
does not expose or certify an internal argmin choice, exhaust larger alphabets or counts, bound
elementary-function error globally, or establish population behavior.

These witnesses establish that the repaired cases were real. They do not establish a universal
floating-point theorem for every atom, estimator, build, platform, or source permutation.

### 4.5 Continuous PID2 represented-coordinate/API witness

The continuous PID2 arithmetic repair also has a public-constructor witness, but not a retained
dataset whose Ehrlich/KSG estimator calls emitted these coordinates. Let

```text
small = f64::from_bits(0x3fb5bf406b543dad)
large = f64::from_bits(0x3fe1fea645f0ef4e)
```

and call `Pid2Result::from_estimate` first with

$$
(I_1,I_2,J,R)=(\mathtt{small},\mathtt{large},\mathtt{large},\mathtt{small}),
$$

then with the first two coordinates exchanged. The historical left-associated synergy produced
`0x3c70000000000000` for the first order and positive zero for the second. Exact reduction of the
same four represented operands produces positive zero for both. This establishes a reachable
constructor-level source-order defect and its algebraic repair. It does not establish how often an
Ehrlich/KSG estimator pipeline emits such a tuple, nor validate that estimator.

## 5. Binary64-aware equal-width quantization

### 5.1 Edge construction

Let finite training endpoints satisfy $m\leq M$ and let $t=j/B$. Endpoints are assigned exactly:
$e_0=m$ and $e_B=M$. For an interior edge, the implementation first tries the difference-first
form

$$
c=m+t(M-m)
$$

when $M-m$ is finite. If the subtraction overflows, which requires a sufficiently wide
opposite-sign interval, it uses the convex form

$$
c=m(1-t)+Mt.
$$

A finite candidate is clamped to $[m,M]$ to absorb harmless last-bit overshoot. Every stored edge
must be finite, in range, and nondecreasing. Failure returns a typed numerical error. This is a
stable binary64 construction, not a claim that every interior edge equals the exactly rounded real
fraction $m+t(M-m)$.

### 5.2 Exact map-reachability test

The transform gives $m$ label 0 and $M$ label $B-1$. For $m<v<M$, it uses the half-open partition
$[e_j,e_{j+1})$. Therefore the endpoint labels are reachable whenever $m<M$. An interior label
$j\in\{1,\ldots,B-2\}$ is reachable exactly when

$$
\bigl(e_j>m\ \mathrm{and}\ e_j<e_{j+1}\bigr)
\quad\mathrm{or}\quad
\bigl(e_j=m\ \mathrm{and}\ \mathrm{nextUp}(m)<e_{j+1}\bigr).
$$

The second branch matters because $v=m$ is intercepted by the endpoint rule. If the next
representable value is already $e_{j+1}$, the half-open interval contains no admissible binary64
value. Subtraction-based width tests would lose precisely this adjacent-value case.

For a constant numeric range, including the numerically equal signed-zero pair, only label 0 is
reachable. Signed `-0.0` and `+0.0` are counted as distinct stored edge payloads but compare as one
numeric value for partitioning.

### 5.3 Nominal, reachable, and observed cardinality

For $D$ dimensions and requested $B$ bins per dimension, define

$$
N=B^D,\qquad R=\prod_{d=1}^{D}r_d,\qquad O=\text{observed joint label tuples},
$$

where $r_d$ is the exact finite-binary64 reachable-label count of dimension $d$. When representable
in `u128`, the report gives

$$
\text{structurally unreachable}=N-R,
$$

$$
\text{unobserved reachable}=R-O,
$$

and preserves the legacy field

$$
\text{empty joint cells}=N-O=(N-R)+(R-O).
$$

`None` means only that the relevant product overflowed `u128`; an impossible subtraction is an
error. Reachability is a property of the fitted finite-binary64 map. It is not population support,
positive probability, joint-law support, or evidence that a sample or bin count is adequate.

### 5.4 Boundary examples

- A constant range with $B=4$ has four nominal labels, one reachable label, and three structurally
  unreachable labels.
- Training on `[-0.0, +0.0]` has two distinct endpoint payloads but one numeric range and one
  reachable label.
- With $B=4$ and two adjacent binary64 endpoints, only labels 0 and 3 are reachable.
- With $B=4$ and endpoints two representable steps apart, fitted edges can be
  $[m,m,\mathrm{nextUp}(m),M,M]$. The reachable set is noncontiguous: $\{0,2,3\}$.
- For `m=0x7feffffffffffffd`, `M=0x7feffffffffffffe`, $B=7$, and $j=3$, the historical convex
  association rounded to `0x7feffffffffffffc`, one representable value below the training minimum.
  The difference-first path returns $m$ and the range/monotonicity validation pins that repair.
- Training on `[-f64::MAX, f64::MAX]` with 100 bins now produces finite monotone edges through the
  convex fallback, including an exact positive-zero centre edge.

No automatic compaction is performed. Compacting labels would change the serialized transform and
could hide that the requested quantizer exceeded the available binary64 resolution.

## 6. Cost and latency

The reducer has fixed $L=34$ limbs. One accumulator holds a positive and negative array with a
544-byte limb payload plus one `usize` accepted-term counter. SxPID retains these accumulators and
its public preflight charges their compiled `size_of` value; the scalar $I_{\min}$ PID2 and
continuous PID2 reducers are short-lived stack values and their public `estimated_bytes` fields do
not separately charge that stack storage. A worst-case add is charged as at most $2L=68$ limb
visits; finalization is charged as at most $4L=136$ limb visits for comparison, subtraction,
leading-bit search, and sticky-bit scan. These are conservative resource-accounting envelopes, not
CPU-instruction counts. Continuous PID2 construction charges the synergy and three reconstruction
reductions as 12 adds and four finalizations, or $12\cdot68+4\cdot136=1{,}360$ limb visits under
this envelope.

The repository also carries full-call Criterion benchmarks for categorical $I_{\min}$ PID2 and
averaged categorical SxPID at two, three, and four sources. A local `--quick` observation on
2026-08-24 used an Apple M4 Max, macOS 26.5.1, release mode, and Rust 1.97.1:

| Call and fixture | Criterion interval |
|---|---:|
| $I_{\min}$ PID2, $n=128$, $q=4$ | 66.165--66.964 $\mu$s |
| SxPID2 averaged, $n=128$, $q=4$ | 92.461--94.463 $\mu$s |
| SxPID3 averaged, $n=64$, $q=2$ | 186.10--189.04 $\mu$s |
| SxPID4 averaged, $n=32$, $q=2$ | 5.3102--5.3168 ms |
| Quantizer labels only, $n=100{,}000$, $d=4$, $B=256$ | 2.8014 ms median |
| Quantizer with report, same fixture | 26.250 ms median |

These are machine-specific smoke observations of the whole calls, not portable latency promises,
not isolated exact-reducer overhead, and not a statistically adequate performance study. Their raw
Criterion output and exact dirty-worktree source identity were not retained, so they receive zero
release-qualification credit. Reproduce or supersede them with
`cargo bench --locked -p pid-core --all-features --bench estimators -- categorical_pid_latency`
on deployment hardware. The order-of-magnitude jump at four sources is consistent with the
166-node lattice and event scans; it must not be attributed solely to the exact accumulator.

For $n$ operands, time is $O(nL)$ with fixed $L$, hence linear in operand count with a larger
constant than ordinary or Neumaier addition. SxPID retains two averaged accumulators per lattice
node. Their accumulator payload alone is approximately:

| Sources | Lattice nodes | Two-component accumulator payload |
|---:|---:|---:|
| 2 | 4 | 4,416 bytes |
| 3 | 18 | 19,872 bytes |
| 4 | 166 | 183,264 bytes |

This does not include atoms, pointwise output, histograms, keys, or vector headers, all of which are
covered separately by public resource preflight. The 4-source lattice and empirical event scans
already dominate many workloads; the change is not a free optimization. Callers with strict
ceilings may need to raise memory or operation budgets.

For any retained quantization report, let $E$ be the total number of stored edges, $C$ the number
of edge vectors, $D_r$ the total length of its four diagnostic vectors, and $S$ the UTF-8 byte
length of the scaling description. Report-copy preflight charges

$$
H=C\,\mathrm{sizeof}(\mathrm{Vec}\langle f64\rangle)
  +E\,\mathrm{sizeof}(f64)+D_r\,\mathrm{sizeof}(usize)+S
$$

heap bytes and $O_r=E+D_r+S$ copy-work units. It uses actual vector lengths, not the report's
nominal `dimensions` field. Fitted-quantized $I_{\min}$ and SxPID preflights sum $H$ and $O_r$ for
every retained source and target report; their different inline/`Vec` report containers are
charged separately.

For an ordinary $d$-dimensional transform with $B$ requested bins, the quantizer additionally
holds $O(dB)$ transient observed-label flags. Its conservative operation hint charges a
$2E$ structural-diagnostic envelope, a further $E$ for the retained edge copy, $6d$ units for the
four diagnostic-vector writes and two cardinality passes, and $S$ for the scaling-string copy, in
addition to the pre-existing $O(nd)$ labeling, hashing, sorting, and occupancy terms. These are
declared accounting units, not CPU instructions or latency predictions.

No new statistical estimator is required. The work changes arithmetic and diagnostics around
existing estimators. Fast ecosystem paths can choose among:

- categorical two-source calls, whose four-term exact residual has small fixed cost;
- pre-fitted quantizers reused across batches, avoiding repeated fitting; and
- bounded resource configurations that reject a workload before allocation.

The stable Rust `transform` call is now a genuine labels-only execution path. It preserves the
same validation, conservative report-sized budget admission, bin-assignment helper, out-of-range
errors, cancellation contract, and categorical output as `transform_with_report`, but skips
occupancy sorting, diagnostic vectors, edge/scaling copies, and provenance hashes after admission.
On the local fixture above that was about 9.37 times faster, or 89.3% lower latency. This is not a
portable speedup guarantee. Stable Python intentionally continues through the report path so its
provenance fields are not silently lost.

An optional fast-but-order-dependent mode was rejected because it would make scientific output
depend on an undocumented arithmetic policy. If future profiling shows a material bottleneck, a
new optimized reducer must preserve the same represented-input result and pass the same oracle and
source-exchange witnesses.

## 7. Testing and evidence layers

The assurance stack deliberately separates different questions:

1. **Arithmetic corpus:** 561 oracle cases: all positional permutations for arities through five,
   plus original, reverse, and two rotations for the 63--65-term streaming cases.
2. **Reachable empirical witnesses:** pinned SxPID2, SxPID3, and SxPID4 final-average defects and
   one $I_{\min}$ PID2 synergy defect; a separate continuous PID2 witness is constructed at the
   represented-coordinate API boundary rather than emitted by a retained estimator dataset.
3. **Negative promotion disposition:** retained bounded pointwise suites establish tolerance
   agreement, not a general raw-bit nonfinding. The three named categorical witnesses now carry
   exact mapped pointwise-bit assertions. Larger reported raw-bit probe totals remain unqualified
   history with zero release-evidence credit because their executable and raw log were lost.
4. **Bounded exhaustive agreement:** every binary SxPID2 count table through four samples and every
   binary SxPID3 table through three samples, including source exchange.
5. **Quantizer boundary tests:** constants, signed zero, adjacent values, noncontiguous reachable
   labels, opposite extremes, and `u128` cardinality overflow.
6. **API parity:** Rust serialization, Python classes/stubs, immutable NumPy labels, and ordinary
   and boundary-case Python tests.
7. **Resource/cancellation tests:** preflight includes accumulator/report storage and long loops
   remain cooperatively cancellable.
8. **Build diversity required at final source:** stable, no-default-feature, parallel, all-feature,
   and release-mode gates. Earlier local passes do not qualify a later integrated source; terminal
   final-source evidence remains a release-closure obligation.

Passing one layer does not imply another. In particular, a rational arithmetic oracle does not
validate a paper correspondence, population support, neighbour geometry, estimator consistency,
or an application decision.

## 8. Twenty-lens internal review

The change was reviewed through twenty non-interchangeable lenses. This is an internal project
review, not external peer review.

| Lens | Question | Disposition |
|---:|---|---|
| 1 | Estimand identity | Unchanged; implementation revision only. |
| 2 | PID-family semantics | SxPID, $I_{\min}$, and continuous PID2 remain distinct. |
| 3 | Exact-real algebra | Formulas unchanged. |
| 4 | Represented arithmetic | Exact only for supplied finite binary64 operands. |
| 5 | Source symmetry | Pinned reachable final-average defects repaired at 2, 3, and 4 Sx sources. |
| 6 | Negative evidence | Pointwise SxPID and $I_{\min}$ PID3 transfers rejected without witnesses. |
| 7 | Lattice dependency | Pointwise Möbius paths remain compensated; final-average order removed. |
| 8 | Overflow | Exact-sum infinity and invalid edges fail closed. |
| 9 | Underflow/subnormals | Oracle includes subnormal and boundary cases. |
| 10 | Signed zero | Exact cancellation canonicalized; quantizer payload/numeric roles separated. |
| 11 | Conditioning | No global conditioning theorem claimed. |
| 12 | Statistical validity | No bias, consistency, support, or calibration inference. |
| 13 | Determinism | Fixed operands have one result; serial/parallel identity remains gated. |
| 14 | Resources | Memory and conservative limb visits enter preflight. |
| 15 | Cancellation | Long report and lattice paths retain cooperative checks. |
| 16 | Rust API | New report fields and checked PID2 failure are documented migration changes. |
| 17 | Python parity | Binding, stub, serialization, and tests expose the same diagnostics. |
| 18 | Oracle independence | Generator avoids pid-rs imports; scope remains finite and correlated by specification. |
| 19 | Formal-method boundary | No Lean/Rust refinement or universal floating-point proof is asserted. |
| 20 | Ecosystem latency | No new estimator; costs are explicit and preflighted. |

The internal council used the same repository materials and is therefore correlated project review,
not independent replication or peer review. Its outcome was to keep only witnessed scalar changes:
exact SxPID final averaging and the two-source synergy repairs. It kept the quantizer diagnostics,
rejected unwitnessed exact SxPID pointwise-Möbius and $I_{\min}$ PID3 transfers, and required
publication of both positive and negative results.

## 9. Real-world use

The change helps where result identity and auditability matter more than an unreported last-bit
speed gain:

- **Neuroscience and electrophysiology:** exchanging two equally scoped source channels no longer
  changes a witnessed averaged categorical SxPID atom merely through final accumulator order.
- **Distributed sensor fusion:** a fitted quantizer can report that nominal resolution exceeds the
  representable range instead of presenting collapsed bins as ordinary sampling emptiness.
- **Small-sample categorical biology:** fixed empirical tables can be replayed with stable averaged-
  atom bits while finite-sample bias remains explicitly outside the arithmetic claim.
- **Real-time monitoring:** resource estimates expose the extra work before execution; a caller can
  choose a supported lower-source surface or reject an oversized 4-source lattice.
- **Cross-language pipelines:** Python receives the same reachability/occupancy fields and exact
  edge payloads as Rust, reducing silent schema or interpretation drift.

These examples do not establish application validity. A domain analysis must still justify the
chosen PID, target/source semantics, preprocessing, support model, estimator, sample size, and
uncertainty procedure.

## 10. What this work does and does not establish

It establishes, within the documented software and evidence scopes:

- one permutation-independent rounding of a fixed multiset of finite binary64 operands;
- concrete reachable source-exchange repairs for selected final-average or synergy reductions;
- finite monotone fitted quantizer edges across extreme ranges;
- exact finite-binary64 label-map reachability diagnostics; and
- Rust/Python/resource-contract coverage for those behaviors.

It does not establish:

- exact PID estimates or exact logarithms/probabilities;
- a new redundancy measure, PID lattice, or statistical estimator;
- a correction to the mathematics in a defining PID publication;
- a global floating-point, conditioning, or estimator-error bound;
- support, consistency, calibration, causal meaning, or real-world decision validity;
- universal source-permutation identity for every output or platform; or
- formal verification of Rust execution.

That narrower conclusion is intentional. It is stronger than an undocumented numerical patch
because its semantics, counterexamples, negative results, resource cost, API consequences, and
evidence limitations are all explicit—and weaker than claims the evidence cannot support.

## 11. Deferred numerical and ecosystem closure roadmap

The following work is intentionally **not** claimed by this change. It is retained as an ordered
roadmap rather than being compressed into an unjustified release cutoff:

1. Add a non-breaking typed reconstruction diagnostic for each supplied coordinate $I_1$, $I_2$,
   and $J$: supplied value, exactly reduced reconstructed value, signed-zero-aware ordered-position
   distance, policy revision, and admitted limit. Preserve `Pid2Result::from_estimate` as the
   compatibility wrapper. Carry the diagnostic through complete Rust reports, resource accounting,
   Python reports/stubs, hierarchy, pair screening, and cross-fit rather than exposing it in only one
   language or path.
2. Derive and review an IEEE-binary64 forward-error envelope from constituent absolute sums under
   explicit no-overflow premises. Report it beside a conditioning diagnostic; do not call it
   statistical accuracy, and do not use relative error at zero. Compare it against the inherited
   ordered-position policy before considering any behavioral change.
3. Expand retained adversarial coverage across signed zeros, subnormal/normal boundaries,
   cancellation scales, overflow-adjacent values, source permutations, serial/parallel modes,
   platforms, and compiler profiles. Include mutation controls and preserve exact generator,
   fixture, command, source, environment, and raw-output custody.
4. Run estimator-level experiments separately from constructor arithmetic: analytic Gaussian
   regimes where applicable, categorical exact oracles, varied dependence/support/sample-size
   regimes, and explicit abstention for unsupported mixed or singular laws. A constructor witness
   must never be relabeled as an estimator-dataset result.
5. Replace the current zero-credit performance observations with revision-bound benchmark receipts,
   repeated confidence intervals, warm/cold and batch latency, peak memory, and representative
   two-/three-/four-source workloads on deployment-class hardware. Optimize only after profiling,
   and require exact output parity plus resource/cancellation preservation for every fast path.
6. Design ecosystem APIs around report-first provenance and explicit latency/resource budgets:
   pre-fitted reusable quantizers, labels-only categorical transforms, batch PID2 reports, typed
   partial-failure retention for screening, and stable serialization. Do not introduce a new
   estimator merely to obtain lower latency; an estimator addition requires its own assumptions,
   calibration evidence, method provenance, and validation scope.
7. Re-run the full numerical, statistical, formal, API-snapshot, Python-wheel, cross-platform, and
   publication gates on the final exact source. Formal tools remain supporting evidence with stated
   bounds; mathematical and statistical review remain independent obligations.

The preferred long-term design is item 1, followed by item 2 as a separately scoped theorem-backed
diagnostic. Returning exact-dyadic expansions or splitting formula-synergy from closure-synergy are
research alternatives, but they would materially change the API and interpretation and are not
needed for the present repair.
