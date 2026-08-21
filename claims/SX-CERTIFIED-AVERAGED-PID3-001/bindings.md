# Prospective bindings for SX-CERTIFIED-AVERAGED-PID3-001

## Binding status

These are required revision-1 identifiers and limits for a future implementation. No producer,
certificate schema, independent verifier, 108-coordinate report, or compiled-Rust refinement is
accepted at the time of this decision. Reserving an identifier does not make an artifact with that
identifier valid.

An accepted run must bind exact source and artifact bytes after they exist. It must not fill an
open field with a historical two-source digest, an external-audit digest, a branch name, or an
abbreviated Git identifier.

## Version identifiers

| Object | Required identifier |
|---|---|
| Claim | `SX-CERTIFIED-AVERAGED-PID3-001` |
| Claim revision | `1` |
| Input schema | `pid-rs/categorical-sxpid3-count-table/v1` |
| Definition revision | `makkeh-gutknecht-wibral-2021-empirical-sxpid3-nats-v1` |
| Event semantics | `mgw-sxpid3-dnf-target-intersection-v1` |
| Antichain registry | `sxpid3-antichains-18-masklex-v1` |
| Zeta/Möbius registry | `sxpid3-zeta-row-cumulative-column-atom-v1` |
| Coordinate registry | `sxpid3-averaged-108-v1` |
| Exact-product schema | `pid-rs/exact-positive-rational-product/v1` |
| Dyadic interval schema | `pid-rs/outward-dyadic-interval/v1` |
| Producer report schema | `pid-rs/certified-averaged-sxpid3-report/v1` |
| Independent-verification schema | `pid-rs/certified-averaged-sxpid3-independent-verification/v1` |
| Resource policy | `sxpid3-certification-proposed-v1` |
| Units | `nats` |

Unknown identifiers, unknown fields, duplicate JSON members, noncanonical integer strings,
coordinate drift, or a self-consistently resealed alternative registry are fail-closed errors.

## Canonical input bytes

The proposed input is an ASCII-only subset of JSON serialized according to RFC 8785 JSON
Canonicalization Scheme and followed by exactly one line-feed byte. Before canonical
reserialization, the parser must reject duplicate member names. It must then require the original
bytes to equal the canonical reserialization plus that line feed.

The top-level object has exactly these members:

```text
{
  "definition_revision": "...",
  "rows": [...],
  "schema": "...",
  "sources": 3,
  "units": "nats"
}
```

Each row has exactly:

```text
{
  "count": "<positive canonical decimal integer>",
  "source_states": [
    ["<token>", "..."],
    ["<token>", "..."],
    ["<token>", "..."]
  ],
  "target_state": ["<token>", "..."]
}
```

A token is 1--128 bytes from ASCII `[A-Za-z0-9._:-]`. A state is a nonempty array of at most 64
tokens. Counts match `[1-9][0-9]*`. Rows are strictly increasing under lexicographic comparison of
the four token arrays `(source_states[0], source_states[1], source_states[2], target_state)`.
Repeated complete states, unsorted rows, empty rows, non-ASCII text, JSON numeric counts, and
noncanonical escapes are rejected.

The exact bytes, not an implementation's in-memory map order, are the input identity. SHA-256 is
computed over those bytes. The schema describes supported empirical states only; it makes no claim
about unobserved population categories.

## Coordinate and lattice bindings

The node list, stable keys, source-bit convention, exact redundancy order, zeta row signatures,
Möbius rows, and six-block 108-coordinate order are normative in
[conventions.md](conventions.md).

Every certificate coordinate carries all of:

- the exact coordinate identity;
- the stable antichain key;
- informative, misinformative, or net component;
- cumulative or atom scope;
- exact positive-rational product record;
- normalized outward dyadic interval;
- exact sign/zero decision; and
- the input, claim, registry, resource-policy, and source-manifest digests.

The verifier reconstructs these fields from the input. It never trusts a producer-supplied
position, matrix row, sign label, or rational product.

## Exact-product resource policy

The following ceilings are part of revision 1. They are conservative admission limits, not
performance promises or scientific assumptions.

| Limit | Value |
|---|---:|
| Positive support rows | 1,024 |
| Terms in one normalized coordinate expression | 8,192 |
| Maximum absolute denominator-cleared exponent | 1,048,576 |
| Projected numerator-plus-denominator bits per coordinate | 262,144 |
| Aggregate projected product bits over 108 coordinates | 8,388,608 |
| Event-predicate primitive comparisons | 100,000,000 |
| Planned peak heap | 536,870,912 bytes |

For a reduced rational factor $a/b>0$ with integer exponent $e$, the preflight contribution is

$$
|e|\bigl(\mathrm{bitlen}(a)+\mathrm{bitlen}(b)\bigr).
$$

The projected coordinate cost is two plus the sum of these contributions. This upper bound is
computed from normalized factor metadata before any power or large product. The aggregate bound is
checked over all 108 plans before any coordinate power is constructed.

The parser may materialize only the bounded input required to derive these plans. Resource
rejection produces no exact decision and cannot be relabeled `verified`. A future change to a
limit or cost formula requires a new claim revision; silently raising a limit under the same
policy identifier is forbidden.

## Parser, report, and interval limits

| Limit | Value |
|---|---:|
| Accepted input bytes | 4 MiB |
| Producer report bytes | 64 MiB |
| Independent-verification report bytes | 16 MiB |
| Decimal digits in one count | 4,096 |
| Total-count bit length | 8,192 |
| Absolute dyadic exponent | 65,536 |
| Canonical payload bytes | 60 MiB |
| One source-manifest member | 4 MiB |
| Complete source manifest | 32 MiB |
| Verifier source bytes | 2 MiB |

The producer working-precision schedule is

```text
128, 256, 512, 1024, 2048, 4096 bits
```

and the independent rational-log schedule is

```text
256, 384, 512, 768, 1024, 1536, 2048 bits.
```

The producer interval must have width at most $2^{-160}$. The independent route accepts only
when its interval is a subset of the producer interval. Schedule exhaustion is rejection, not a
wide or unresolved certificate.

## Complete source binding required for acceptance

A future accepted verification must record a length-delimited manifest containing every byte that
can affect:

1. canonical parsing and duplicate-member rejection;
2. state and count decoding;
3. event-count reconstruction;
4. antichain generation or registry loading;
5. zeta and Möbius construction;
6. exact expression normalization and product preflight;
7. interval production;
8. independent interval reconstruction;
9. exact sign/zero comparison;
10. report serialization and verification;
11. the lockfile, compiler/toolchain selection, and enabled features; and
12. the mutation and bounded-corpus gates used by the decision.

The manifest member list and exact digests are currently **open** because the corresponding
implementation does not exist. A Git commit can bind repository source after the files settle. It
does not by itself attest to a compiled binary, native dependencies, authorship, external custody,
or reproducibility.

## Primary semantic source

The controlling categorical source is:

Abdullah Makkeh, Aaron J. Gutknecht, and Michael Wibral, “Introducing a differentiable measure of
pointwise shared information,” *Physical Review E* 103, 032149 (2021),
[DOI](https://doi.org/10.1103/PhysRevE.103.032149),
[final arXiv v5](https://arxiv.org/pdf/2002.03356v5).

The audited arXiv-v5 PDF SHA-256 is
`5939ce0f4c727f1998040421c07a1689af1b8d9a35a0ee3c83fe25cd85263dc6`.
Relevant source locations are Eqs. (4), (6)--(8), (12)--(15), and (17), Theorems IV.2 and IV.3,
and Appendix Eq. (A1) and Theorem A.1.

The cited paper uses bits in displayed examples. This packet uses the same finite categorical event
and decomposition with natural logarithms. A citation and matching vocabulary do not prove that
the packet or an implementation transcribes the paper correctly; that correspondence remains an
explicit route obligation.

## Current Rust source is not positionally bound

The current specialized Rust three-source path obtains its 18-node array from
`discrete_antichains_3`; its positions 2 and 3 are `(4)` and `(3)`, respectively. The registry in
this claim uses `(3)` and then `(4)`. The general $n$-source path enumerates valid mask
combinations in yet another order.

This is not a semantic disagreement if results are keyed by canonical antichain. It is a direct
counterexample to positional comparison. No current Rust source or binary digest is bound as
refining this packet.

## External audit intake, not accepted binding

The final external handoff supplied a bounded Python mirror and a second script. Their inspected
raw-byte digests are:

| Artifact | SHA-256 |
|---|---|
| `scripts/audit_sxpid3.py` | `13eef143a60028366ca2271bed0836b68d29fc517d730e019e5b514c378e852b` |
| `scripts/sxpid_core.py` | `8599ffaef49ce2ec79dfbb5a4dd4e95c614f7de8462736f25e6ebb3726bd2226` |
| `scripts/verify_sxpid3_independent.py` | `4d0705a2e2e5d72d3a92f1b8e89a20578183a1dc576ddade1326d2e56467b2aa` |
| `sxpid3-summary.json` | `1468d38b6c101f23a848825b3934be1e4e40467a3ef889e3bc19b5faa0c52b48` |
| `independent-verification.json` | `3445416c4dbc2864e4b5e7d7525a656f765b03422a8c41e141c23d546a3247eb` |

These files are advisory intake. In particular, the alleged independent script imports the
primary script's cell enumeration, weak compositions, event predicate, antichain generator,
Möbius generator, exact computation, and sign helper. Its brute-force node list, SymPy inverse,
`Fraction` products, and direct floating path add useful differential checks, but its event and
count bridge is not dependency-disjoint. The external artifacts are not copied into this claim,
not part of the future trusted source manifest, and not sufficient to change the claim
disposition.

## Remaining immutable-record obligations

Before any conditional support:

1. record final raw-byte SHA-256 values for every claim, source, schema, formal, certificate,
   executable, bounded-corpus, and mutation artifact;
2. bind a full Git commit containing those exact bytes;
3. record compiler, target, features, dependency lockfiles, proof kernels, solver versions, and
   permitted axiom inventories;
4. preserve first-result and mutation receipts;
5. replay from a fresh extraction rather than the working tree; and
6. retain a separate independent-custody record if assurance beyond local Git history is claimed.
