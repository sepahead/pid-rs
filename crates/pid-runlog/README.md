# pid-runlog

[![CI](https://github.com/sepahead/pid-rs/actions/workflows/ci.yml/badge.svg)](https://github.com/sepahead/pid-rs/actions/workflows/ci.yml)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

A versioned, content-addressed **run-log schema** and replay/validation helpers for reproducible
partial-information-decomposition pipelines (used by
[`pid-core`](https://github.com/sepahead/pid-rs/tree/main/crates/pid-core)). Action,
intervention, and bridge-request payloads are individually content-addressed (SHA-256). **All**
records are covered by a derivable order-sensitive whole-trace replay hash and, when sidecars are
generated, a whole-file SHA-256 manifest, so a run can be replayed and checked for internal
consistency offline. The current run-log schema version is `2` (`RUN_LOG_SCHEMA_VERSION`);
schema 1 remains readable through the bounded compatibility reader and can be explicitly migrated.
Records are not
prev-hash-chained. Colocated hashes and sidecars do not authenticate a log: tamper evidence
requires storing a digest in a trusted external or signed anchor.

Every path-based read is bounded by `RunLogLimits`. The default budget caps complete-file bytes,
line bytes, event count, JSON string bytes, array and object lengths, and nesting depth. Use a
`*_with_limits` API to opt into a different finite budget. `RunLogEventStream` parses one bounded
line at a time; `inspect_path`, validation, replay, summaries, manifests, and trace-hash path helpers
operate in bounded streaming passes rather than first loading the complete JSONL file. `ValidatedRunLog` is
returned only after lifecycle, causality, numeric, hash, and typed-provenance validation succeeds.
Already-decoded slices are not an unbounded bypass: replay, validation, canonical hashing, and
manifest construction are fallible, use finite defaults, and expose explicit-limit variants.
Failed replay application leaves the logical replay state unchanged.

```text
# validate a run-log produced by an experiment
cargo run -p pid-runlog --bin pid-runlog-replay -- --validate run.jsonl
```

The `pid-runlog-replay` binary also supports:

```text
pid-runlog-replay <run-log.jsonl>                       # replay and print a summary
pid-runlog-replay --validate <run-log.jsonl>            # schema + internal consistency checks
pid-runlog-replay --compare <left.jsonl> <right.jsonl>          # compare whole-trace replay hashes
pid-runlog-replay --compare-v2 <left.jsonl> <right.jsonl>       # lossless whole-trace comparison
pid-runlog-replay --compare-logical <left.jsonl> <right.jsonl>  # schema-1 logical hash compatibility
pid-runlog-replay --compare-logical-v2 <left.jsonl> <right.jsonl> # only top-level clocks excluded
pid-runlog-replay --compare-logical-v3 <left.jsonl> <right.jsonl> # lossless top-level-clock comparison
pid-runlog-replay --summary-json <run-log.jsonl> <out.json>
pid-runlog-replay --manifest-json <run-log.jsonl> <out.json>
pid-runlog-replay --write-sidecars <run-log.jsonl>     # write validation/summary/manifest sidecars
pid-runlog-replay --verify-sidecars <run-log.jsonl>    # re-derive and check sidecars
```

## Hash compatibility

The Rust API retains the released schema-1 digests for existing sidecars:
`replay_trace_hash`, `logical_trace_hash`, and `logical_trace_hash_v2` reproduce serde_json's
former finite-`f64` normalization for decimal/exponent literals and integers outside the
`i64`/`u64` range when those values remain finite. The corresponding CLI comparisons use those
compatibility hashes.

For new lossless comparisons, use `replay_trace_hash_v2` and `logical_trace_hash_v3` (or their
`*_from_path` helpers), or the CLI's `--compare-v2` and `--compare-logical-v3` modes. These
explicitly versioned functions preserve arbitrary-precision numbers inside generic config,
payload, and label JSON. New sidecars include `hash_identities`, which binds each digest to `sha256`
and an explicit byte contract such as `replay_trace_v2` or `logical_trace_v3`. The older scalar
fields remain solely for schema-1 compatibility; when a legacy numeric normalization is impossible,
those compatibility fields are empty and never alias a newer digest. Older sidecars remain readable
and verifiable deliberately.

Payload and config content addresses follow the same split. `canonical_json_hash` preserves the
schema-1 number normalization, while `canonical_json_hash_v2` is lossless and required by schema 2;
`canonical_json_hash_identity_v2` additionally binds the digest to SHA-256 and the exact canonical
contract. Because schema-1 payload/config hash fields have no generation marker, schema-1
validation accepts either digest; this also permits a `run_started` v1 config hash to anchor a
matching `config_logged` v2 hash (or vice versa). Schema 2 never performs that ambiguous fallback.

Schema 2 adds `pid_estimate`, a typed publication-facing metric event. It records scientific status,
definition and estimator revisions, data and preprocessing hashes, split identities, support and
metric declarations, `k`, diagnostics, and warnings together with the value. Legacy `pid_metric`
events remain readable but are not silently upgraded with invented provenance. `migrate_runlog`
updates a schema-1 declaration in a streaming rewrite and reports every preserved legacy PID metric.

Typed `f64` fields reject integer JSON tokens that cannot be represented exactly;
arbitrary-precision integers inside generic JSON config, payload, diagnostic, and label values remain
lossless. Schema-2 validation also checks SHA-256 syntax and artifact URI/path syntax.

## Rust API evolution

Extensible enums and generated/inspection records are `#[non_exhaustive]`. Public-field input DTOs
such as `Actor`, `Pose`, and the typed PID payload are the exact schema-2 wire shapes shipped for the
0.9 review. They are proposed freeze candidates for 1.0, but 0.9 makes no 1.x compatibility promise.
Any pre-1.0 field-level wire change will be explicit in the changelog and schema/type identity; once
1.0 is released, such a change will require a separately versioned schema/type (or a major Rust
release) rather than being slipped into those exhaustive DTOs.

## Durable sidecars and external anchors

JSON summaries, manifests, and sidecars are written in the destination directory using a unique
temporary file, `flush` + `sync_all`, and atomic rename. Unix targets also `sync_all` the parent
directory before reporting success. Rust does not expose a portable Windows directory-flush
primitive, so Windows guarantees atomic replacement and a flushed new file but not persistence of
the renamed directory entry across immediate power loss. A failed write cleans an uncommitted
temporary file and never truncates the previous destination. Manifests can
carry optional `ExternalAnchor` entries for a trusted service, transparency log, DOI record, or
detached signature reference. The crate validates their syntax but does not create or authenticate
signatures itself.

See the [repository README](https://github.com/sepahead/pid-rs) for context.

## License

Licensed under either of [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE) at your option.
