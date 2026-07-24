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

The permitted claim is conditional:

> For the accepted exact count table and the recorded definition, lattice, source wrapper, locked
> dependencies, build context, and precision policy, each returned dyadic interval encloses the
> exact-real value of the expression that this tool encodes.

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
  "resource_policy_id": "sxpid2-certification-default-v1",
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
- sign status, with exact zero reserved for an empty symbolic expression;
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

## Resource policy

The versioned policy bounds input bytes, row count, token widths, count sizes, precision growth,
terms per expression, total terms, estimated exact-term JSON bytes, and final canonical payload
bytes. Resource rejection occurs before MPFR evaluation when the exact-expression term limits are
exceeded and before exact-term strings are materialized.

The default precision sequence is 128, 256, 512, 1024, 2048, and 4096 bits. Every coordinate must
reach width at most $2^{-160}$. Successive enclosures are intersected. An empty intersection is
an internal soundness failure.

## Local qualification

Run these commands from the repository root:

```text
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

## Distribution and license boundary

The new source in this directory uses the repository's MIT OR Apache-2.0 license. Rug,
`gmp-mpfr-sys`, MPFR, and GMP add LGPL-3.0-or-later obligations to a compiled linked executable.
The tool is outside the published `pid-rs` Cargo workspace. The project does not distribute its
compiled binary as a release artifact.

Users build the tool locally from source. Any binary distribution requires a separate license
review and an LGPL-compliant source and relinking route. The dependency configuration must not
enable `use-system-libs`. The committed standalone lockfile is part of the source evidence
boundary.
