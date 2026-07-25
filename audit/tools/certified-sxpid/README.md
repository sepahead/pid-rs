# Certified two-source categorical SxPID reference tool

## Accepted scope

This directory contains a standalone, offline audit tool. It is not a `pid-core` backend, a stable
API, or a published package.

The tool accepts one canonical exact count table. It returns outward dyadic intervals for all 24
coordinates of the complete, averaged, two-source categorical shared-exclusions decomposition:

- four cumulative nodes and four atoms;
- informative, misinformative, and net components for each node or atom; and
- natural-logarithm units (nats).

The implementation encodes the empirical categorical $I^{\mathrm{sx}}_\cap$ definition of
Makkeh, Gutknecht, and Wibral (2021). It uses exact integer event counts, exact rational
coefficients and logarithm arguments, the pinned two-source Möbius matrix, and MPFR operations with
explicit downward or upward rounding.

For every averaged coordinate whose bounded preflight succeeds, the tool additionally clears the
common empirical denominator $n$ and compares the exact positive rational product

$$
R=\prod_j q_j^{n c_j},
\qquad
V=\sum_j c_j\log q_j=\frac1n\log R.
$$

It therefore decides $V=0$, $V>0$, or $V<0$ by the exact comparisons $R=1$, $R>1$, or $R<1$.
This is an exact rational-product comparison, not prime factorization and not a floating-point
sign heuristic. It is a second, explicitly bounded decision field; it does not alter the directed
interval or make an interval-local claim that its endpoints do not establish.

The permitted claim is conditional:

> For the accepted exact count table and the recorded definition, lattice, source wrapper, locked
> dependencies, build context, and precision policy, each returned dyadic interval encloses the
> exact-real value of the expression that this tool encodes. When a coordinate's separately
> bounded exact-product record has status `compared`, that record additionally certifies exact
> equality to zero or strict sign by exact rational-product comparison after integer denominator
> clearing; the dyadic endpoints remain the enclosure authority and the interval-local decision
> is not rewritten.

The standalone
[conditional-assurance paper](../../formal/latex/certified-sxpid2-executable-assurance.tex) gives
the exact count reduction, directed-enclosure argument, retained counterexamples, trusted
computing base, and claim-to-evidence map. Its
[rendered PDF](../../../output/pdf/certified-sxpid2-executable-assurance.pdf) is checked as a
warning-free reproducible artifact.

The tool does not certify:

- `pid-core` binary64 output;
- pointwise SxPID;
- $I_{\min}$;
- fitted quantization or equivalence to an unquantized estimand;
- three-source or four-source SxPID;
- continuous KSG, continuous $I^{\mathrm{sx}}_\cap$, or continuous PID;
- population support, dependence, stationarity, sampling, consistency, or calibration;
- input authenticity or scientific meaning;
- GMP, MPFR, Rug, the compiler, or the native ABI; or
- downstream application validity or all of `pid-rs`.

The certificate reports locked crate versions, manifest-requested Rug features, and sanitized
Cargo profile metadata. It deliberately has no direct `gmp-mpfr-sys` dependency: the official
qualification gate proves that Cargo rejects direct command-line injection of
`gmp-mpfr-sys/use-system-libs` and that the default locked metadata graph resolves the transitive
native-sys crate with only `mpfr`. This does not turn the runtime report into a complete feature
attestation. The build context remains explicitly non-exhaustive: it does not bind effective
dependency-feature resolution, compiler wrappers, effective encoded flags, Cargo, the
linker/native compiler, or cache contents. It also does not report compiled native version
constants or claim native archive or executable digests. An external build-evidence envelope must
supply those bindings when they are required.

## Input contract

The command accepts exactly one JSON file path. Use `-` to read standard input. Rows must be
strictly increasing in lexicographic order. Each complete categorical state must occur once.
Counts are positive canonical decimal integers.

```json
{
  "schema": "pid-rs/categorical-sxpid2-count-table/v1",
  "definition_revision": "makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1",
  "units": "nats",
  "resource_policy_id": "sxpid2-certification-default-v2",
  "rows": [
    {
      "source_states": [["0"], ["0"]],
      "target_state": ["0"],
      "count": "1"
    },
    {
      "source_states": [["1"], ["1"]],
      "target_state": ["1"],
      "count": "1"
    }
  ]
}
```

The input parser rejects unknown JSON fields, duplicate keys, zero counts, noncanonical count
strings, duplicate states, unsorted rows, inconsistent widths, unsupported schemas, and resource
limit violations.

## Output and failure semantics

Success produces one compact JSON certificate and exit status 0. The certificate contains:

- raw-input and semantic-input SHA-256 digests;
- exact log-linear terms and a digest for every coordinate;
- exact dyadic lower and upper endpoints;
- an interval-local sign status, with its `certified_exact_zero` value reserved for an empty
  canonical expression;
- a separate bounded exact-product status, decision source, resource trace, and product-one zero
  witness when denominator clearing and the product preflight succeed;
- lattice, extractor, precision, resource, arithmetic, manifest-requested dependency, and build
  evidence;
- numerical cross-check counts; and
- the permitted and excluded claim boundary.

The payload digest uses JSON with recursively lexicographic object keys. No certificate field uses a
JSON floating-point number. The runtime source-manifest digest uses a domain tag, unsigned
64-bit big-endian path and content lengths, path bytes, and file bytes.

Failure produces one compact rejection envelope:

- exit status 3 means that the versioned precision policy was exhausted;
- exit status 2 means invalid input or another fail-closed rejection; and
- exit status 1 means that the result envelope could not be written.

The tool emits no partial certificate after a rejected check.
The current stdout transport is not atomic: an external write failure can leave a truncated JSON
prefix before exit status 1. Consumers must require exit status 0, exactly one complete JSON
document through end of file, successful schema parsing, and a recomputed payload digest.

## Independent integer/rational-log verification

`scripts/verify_certificate.py` is a second implementation path. It uses only the Python standard
library and does not import the Rust certifier, `pid-core`, Rug, MPFR, GMP, NumPy, SymPy, or the
Decimal oracle. Given the original canonical count table and a certificate, it:

1. strictly parses and rehashes both inputs;
2. independently reconstructs source marginals, target intersections, the shared-exclusions
   disjunction by exact integer inclusion-exclusion, and all twelve cumulative log-linear
   expressions;
3. applies an independently declared integer Möbius matrix and checks exact zeta reconstruction
   as an arithmetic self-consistency test;
4. checks the three self-redundancy coordinates against separately reconstructed direct-MI
   expressions;
5. requires all 24 report identities and exact term lists to equal that reconstruction;
6. independently clears every empirical denominator, repeats the bounded rational-product
   comparison, and validates the distinct exact-product decision and resource trace;
7. validates normalized dyadic endpoints, the precision trace, every pinned structural and
   transient resource ceiling, exact resource-accounting fields, the complete arithmetic,
   build-context, distribution, and claim-boundary records, schema bindings, and the report and
   source-manifest digests; and
8. proves that every reported interval contains the reconstructed exact-real value.

The final step is not a floating-point comparison. For each positive rational argument it writes
$x=2^e y$ with $1\leq y<2$, sets $z=(y-1)/(y+1)$, and evaluates the positive series

$$
\log y=2\sum_{k=0}^{\infty}\frac{z^{2k+1}}{2k+1}.
$$

Here $0\leq z\leq 1/3$. Every multiplication and division is outward-rounded with exact Python
integers at a power-of-two fixed-point scale. After $m$ terms the omitted tail is bounded by

$$
0\leq R_m
\leq \frac{2z^{2m+1}}{(2m+1)(1-z^2)}
\leq \frac{9z^{2m+1}}{4(2m+1)}.
$$

The geometric series converges uniformly on $[0,1/3]$, so its termwise integration is valid on
the complete reduced domain. The cached $\log 2$ interval is computed separately, without
recursive range reduction, by applying the same recurrence at $y=2$, hence $z=1/3$. The identity
$2=(1+z)/(1-z)$ and the endpoint-inclusive tail bound establish that base enclosure.

The verifier adaptively increases its scale from 256 through at most 2048 bits. It accepts only
when its independently derived enclosure is a subset of the certificate's dyadic interval.
Overlap is insufficient. If containment cannot be proved, it fails closed.

```text
CARGO_TARGET_DIR=target/certified-sxpid cargo run --quiet --locked \
  --manifest-path audit/tools/certified-sxpid/Cargo.toml -- input.json \
  > certificate.json

python3 audit/tools/certified-sxpid/scripts/verify_certificate.py \
  input.json certificate.json
```

The default verifier also requires the certificate's runtime source-manifest and `Cargo.lock`
digests to match the reviewed source tree beside the script. It rejects a valid report from a
different source snapshot rather than silently weakening that binding. Source-manifest members
must be bounded regular non-symlink files. The verifier reads each member through one file
descriptor, checks its identity before and after the read, and requires the complete manifest and
verifier-source digests to remain unchanged across verification. These checks detect the declared
local change cases; they are not an atomic filesystem snapshot or executable-provenance proof.
The arithmetic binding also rejects Cargo `[patch]` and `[replace]` source substitution, requires
the standalone `[workspace]` table to remain empty, and pins the registry source and checksum of
the locked `rug` and `gmp-mpfr-sys` packages. Ambient Cargo configuration, downloaded registry
custody, native archives, and executable bytes remain outside this local source check.

Python 3.11 and later can impose a process-wide decimal integer-text limit. The verifier requires
that limit to be unlimited or at least 4,096 digits, records the effective value, and rejects
canonically before parsing if the runtime is too restrictive. The certificate payload is
independently canonicalized and limited to 10 MiB.

This route removes Rug, MPFR, GMP, the Rust compiler, the certifier executable, and the
*correctness* of certificate-supplied expressions, lattice values, signs, and endpoints from the
containment trusted base. Those fields are still parsed as untrusted candidate evidence, and the
producer endpoints define the candidate outer interval in the subset test. It does not formally
verify Python or the verifier itself. Python arbitrary-precision integer and `Fraction` semantics,
JSON and SHA-256 implementations, this verifier source, the reviewed logarithm bound, and the
locally bound certifier source remain trusted. The scientific and downstream exclusions listed
above are unchanged.

## Resource policy

The producer's versioned policy is:

| Producer limit | Value |
|---|---:|
| Input bytes | 4 MiB |
| Rows | 4,096 |
| State width per source or target | 32 tokens |
| Token bytes | 128 |
| Count digits | 1,024 |
| Total-count bits | 8,192 |
| Terms per exact expression | 4,096 |
| Total exact terms | 8,192 |
| Cumulative extraction terms | 1,638 |
| Estimated exact-term JSON bytes | 8 MiB |
| Canonical certificate payload bytes | 10 MiB |
| Terms in one exact-product comparison | 256 |
| Absolute denominator-cleared exponent | 16,384 |
| Projected product bits per expression | 262,144 |
| Projected product bits over all coordinates | 1,048,576 |

Resource rejection occurs before MPFR evaluation when the exact-expression term limits are
exceeded and before exact-term strings are materialized. The cumulative-extraction limit is
checked incrementally. The 4,096-row value is a structural maximum, not a promise that every
4,096-row table is accepted: a generic table can hit the 1,638 cumulative-term ceiling much
earlier, and the retained growing-support witness is rejected at 410 rows.

The exact-product route first computes integer exponent and conservative bit-growth evidence
without powering any rational. A per-expression failure records
`not_compared_per_expression_preflight_limit`; an aggregate failure records
`not_compared_total_preflight_limit`. Those are bounded fallbacks, not certificate failures: the
directed interval remains authoritative for enclosure. Only admitted plans allocate powers. The
8,192-bit total-count parser ceiling must not be confused with permission to exponentiate an
8,192-bit count.

The policy bounds memory-shaped objects and iteration counts, not wall-clock time. The current
producer performs eight complete event-mass scans per accepted row, so this extraction stage is
quadratic in the number of support rows, in addition to state-vector and arbitrary-precision
integer costs. No latency, throughput, or denial-of-service resistance claim follows from these
limits.

The default precision sequence is 128, 256, 512, 1024, 2048, and 4096 bits. Every coordinate must
reach width at most $2^{-160}$. Successive enclosures are intersected. An empty intersection is
an internal soundness failure.

The independent verifier adds these limits and re-enforces all applicable producer structural
limits:

| Independent-verifier limit | Value |
|---|---:|
| Accepted input bytes | 4 MiB |
| Producer-certificate bytes | 11 MiB |
| Token bytes | 128 |
| Total-count bits | 8,192 |
| Absolute dyadic exponent | 65,536 |
| Fixed-point bits | 2,048 |
| Fixed-point schedule | 256, 384, 512, 768, 1,024, 1,536, 2,048 |
| Report integer-string digits | 4,096 |
| JSON numeric-integer-token digits | 24 |
| Canonical payload bytes | 10 MiB |
| One source-manifest member | 4 MiB |
| Complete source manifest | 32 MiB |
| Verifier source bytes | 2 MiB |

Exhausting the fixed-point schedule without proving subset containment is a rejection.

## Local qualification

Run these commands from the repository root:

```text
cargo fetch --locked \
  --manifest-path audit/tools/certified-sxpid/Cargo.toml

just certified-sxpid
just formal-certified-sxpid2-assurance-pdf
scripts/check-certified-sxpid2-assurance-pdf.sh --cross-toolchain

CARGO_TARGET_DIR=target/certified-sxpid cargo test --locked \
  --manifest-path audit/tools/certified-sxpid/Cargo.toml

CARGO_TARGET_DIR=target/certified-sxpid cargo clippy --locked \
  --manifest-path audit/tools/certified-sxpid/Cargo.toml \
  --all-targets -- -D warnings

RUSTDOCFLAGS="-D warnings" CARGO_TARGET_DIR=target/certified-sxpid \
  cargo doc --locked --no-deps \
  --manifest-path audit/tools/certified-sxpid/Cargo.toml

cargo fmt --manifest-path audit/tools/certified-sxpid/Cargo.toml --all --check

python3 audit/tools/certified-sxpid/scripts/check-static-policy.py
python3 audit/tools/certified-sxpid/scripts/check-static-policy-self-test.py
python3 audit/tools/certified-sxpid/scripts/check-independent-verifier.py
python3 -O audit/tools/certified-sxpid/scripts/check-independent-verifier.py
python3 audit/tools/certified-sxpid/scripts/check-exact-products.py
python3 audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py
python3 audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py

cargo deny --manifest-path audit/tools/certified-sxpid/Cargo.toml check \
  --config audit/tools/certified-sxpid/deny.toml
```

The test suite includes exact analytic XOR atoms, exact logarithm identities, strict-schema
negative cases, precision exhaustion, resource-amplification rejection, 11,856 certified
interval-versus-Decimal-tolerance overlap comparisons covering all 24 coordinates over 494
independently generated binary empirical count tables, and 1,482 additional comparisons of the
three net cumulative coordinates with a separately evaluated direct-MI formula. Reviewed literals
pin both fixture and generator bytes; the sidecar is not trusted by itself. The Decimal fixture
provides independently generated numerical agreement, not a rigorous oracle enclosure. The static
policy self-test must reject every representative arithmetic, sign-boundary, event, lattice,
native-feature, and unsafe source mutation.

The denominator-cleared qualification checks 11,856 expression products and exact signs over the
494 tables. A separate boundary exhaustion covers all 12,869 nonzero binary tables with total
count at most eight (308,856 coordinates). No nonempty canonical expression with exact product
one occurs below total eight. At total eight there are exactly 16, all five-support net unique
atoms. The minimized retained witness has counts
`[0,0,1,1,1,4,1,0]`: its five-term interval remains `unresolved_sign`, while its separate exact
product is one and is therefore `certified_exact_zero`. This is the negative counterexample that
invalidated the former empty-term-only completeness assumption; the old behavior is retained as a
failed result, not erased.

The self-contained proof and retained failure analysis are available as
[`EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md`](../../formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md),
its [LaTeX source](../../formal/latex/exact-log-product-sxpid2-assurance.tex), and the
[rendered PDF](../../../output/pdf/exact-log-product-sxpid2-assurance.pdf). The PDF is checked by
`scripts/check-exact-log-product-sxpid2-pdf.sh` from the repository root.

The static policy suite kills 34 registered mutations, including an explicit unsafe-function
surface.

The independent verifier qualification separately reconstructs 11,856 coordinates, 1,482
direct-MI identities, and 5,928 cumulative event expressions by a direct row scan over the same
494-table bounded domain. The direct scan does not use the verifier's inclusion--exclusion
shortcut. It proves all 72 coordinates in three live certificates (singleton, XOR, and an
asymmetric sparse table), rejects 22 self-consistently resealed certificate mutations, and rejects
reuse of a certificate with another count table. The suite therefore reports 23 killed semantic
mutations. It also passes under `python3 -O`; it does not depend on removable Python assertions.
These mutations include:

- a false zero interval;
- collapse of a certified-positive interval to its own downward-rounded lower endpoint;
- strict positive/negative exact-product intervals that touch zero at an impossible endpoint;
- a forged exact expression with updated expression and payload digests;
- replacement of the redundancy union by the joint event;
- noncanonical and resource-amplifying dyadics;
- a forged sign, duplicated identity, false width flag, and inconsistent precision trace;
- forged source, arithmetic, build-context, and distribution bindings;
- false exact-term counts and serialization estimates;
- Boolean-for-integer substitutions in ordinary evidence and the pinned lattice;
- a broadened permitted claim;
- a build-host value inconsistent with the embedded `rustc -vV` text;
- reuse of a certificate with another count table.

The logarithm implementation is qualified independently of producer certificates on 975
precision/argument cases. An exact-`Fraction` partial sum and exact rational tail enclosure must
fit inside every fixed-point result. A retained source mutation that subtracts 70 fixed-point
units from the $\ln 2$ upper endpoint must fail this exact-rational grid. This is a named
fault-sensitivity result; it does not establish which other evidence routes would accept the
mutant.

One retained event-extraction source mutation replaces the target-restricted disjunction count
with `max(source_one_target, source_two_target)`. Internal nesting, the three direct-MI identities,
and the XOR analytic pin do not kill that mutant. The new direct row scan does.

Four cross-artifact adversaries require rejection after a post-import verifier-source change,
after a self-consistently rehashed change to the standalone Rug version contract, after Cargo
`[patch]` substitution, and after a locked Rug checksum substitution. Separate structural controls
reject duplicate JSON keys, a lone Unicode surrogate, a
producer-valid table whose cumulative expression transiently reaches 1,640 terms against the
1,638-term ceiling, and a producer-valid 1,000-digit count under an insufficient Python
integer-text limit. A fifth structural control invokes the CLI with an invalid POSIX filename byte
and requires one bounded canonical rejection without a traceback; a sixth invokes the complete
CLI under an insufficient process-start integer-text limit. The qualification harness compiles the
exact verifier source bytes itself instead of consulting a bytecode cache. Two additional
transport/invocation controls require a symlinked script path to bind the real source and a closed
stdout to return status 1 without a traceback. Repeated CLI runs under different Python hash seeds
must be byte-identical.

Every structural negative control checks its intended rejection reason. A rejection for an
unrelated parser or ordering defect does not count as evidence for the target guard.

## Distribution and license boundary

The new source in this directory uses the repository's MIT OR Apache-2.0 license. Rug,
`gmp-mpfr-sys`, MPFR, and GMP add LGPL-3.0-or-later obligations to a compiled linked executable.
The tool is outside the published `pid-rs` Cargo workspace. The project does not distribute its
compiled binary as a release artifact.

Users build the tool locally from source. Any binary distribution requires a separate license
review and an LGPL-compliant source and relinking route. The dependency configuration must not
enable `use-system-libs`. The committed standalone lockfile is part of the source evidence
boundary.
