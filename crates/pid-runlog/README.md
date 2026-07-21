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
Schema 2 requires exactly one `config_logged` event before operational events; its lossless
canonical config hash must match both the logged config and `run_started.config_hash`. Schema 1
retains its historical optional-config behavior. A finalized schema-2 stream also requires every
bridge request to have exactly one response; schema 1 preserves the historical unresolved-request
warning for compatibility.
Records are not
prev-hash-chained. Colocated hashes and sidecars do not authenticate a log: tamper evidence
requires storing a digest in a trusted external or signed anchor.

The run-log schema, typed PID event, replay hashes, bounded readers, migration rules, and sidecar
protocol are **project-defined repository engineering**, not a new PID measure, statistical
estimator, or published calibration procedure. **“New in pid-rs” means implementation, API,
composition, diagnostic, or engineering work new to this repository; it is not a claim of
scientific novelty.** See
[`METHODS.md`](https://github.com/sepahead/pid-rs/blob/main/METHODS.md) and the machine-readable
[`method-catalog.json`](https://github.com/sepahead/pid-rs/blob/main/method-catalog.json) for the
authoritative distinction between paper-defined methods, paper-derived compositions,
project-defined infrastructure, external reference code, and requests for which no implementation
exists.

Schema 2 does not store the experimental typed Gaussian-noise declaration or application report.
Callers cannot encode that evidence as if schema 2 understood it. A future schema must define a
typed migration before pid-runlog can retain this project-defined Rust provenance.

Every path-based read is bounded by `RunLogLimits`. The default budget caps complete-file bytes,
line bytes, event count, JSON string bytes, array and object lengths, and nesting depth. Use a
`*_with_limits` API to opt into a different finite budget. `RunLogEventStream` parses one bounded
line at a time; `inspect_path`, validation, replay, summaries, manifests, and trace-hash path helpers
operate in bounded streaming passes rather than first loading the complete JSONL file. `ValidatedRunLog` is
returned only after lifecycle, causality, numeric, hash, and typed-provenance validation succeeds.
Already-decoded slices are not an unbounded bypass: replay, validation, canonical hashing, and
manifest construction enforce the same per-event line and aggregate ceilings, are fallible, use
finite defaults, and expose explicit-limit variants.
`RunLogWriter::append_with_limits` counts events and JSONL bytes (including newlines) appended
through that writer instance; a generic writer may contain pre-existing bytes which the wrapper
cannot discover. An underlying append write error poisons the wrapper, preventing a retry from
undercounting partially committed bytes. Schema migration applies its caller-supplied limits to
content rehashing and to the complete migrated stream it writes. Because migration accepts a
generic forward-only writer, an error discovered after output begins can leave a valid prefix in
that writer. Callers publishing to a path must stage the output and atomically install it only
after migration succeeds; the API does not claim transactional writes.
`sha256_file` uses the default finite file ceiling; `sha256_file_with_limit` is the explicit bounded
variant for other artifact sizes. Path-based manifest construction computes the whole-file digest
and all parsed identities from one opened file handle. `manifest_for_events` additionally rejects a
supplied event slice whose lossless ordered trace does not match that file. A manifest is a
point-in-time record of the opened file: construction compares pre/post handle metadata and checks
that the path still identifies that handle before returning. These checks detect common observable
changes, but same-length rewrites can evade coarse or preserved modification timestamps, and no path
API can prevent a separate process from changing the path after the final check. Callers must
quiesce or otherwise snapshot concurrently written logs before treating the recorded URI as
immutable.
Manifest construction records the supplied filesystem path without lossy conversion and therefore
fails closed when that path is not valid UTF-8. Sidecar filename derivation itself preserves raw
platform path units, so distinct non-UTF-8 Unix names cannot collapse onto one sidecar name.
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

Every command that writes JSON rejects any explicit or derived output which already identifies the
input file, including exact paths, symbolic links, and hard links. The public sidecar-writing Rust
API enforces the same check. This protects static aliases; it is not a filesystem synchronization
or authorization boundary, so callers must not concurrently retarget either path while the command
runs.

CLI exit codes are `0` for success/match/valid, `1` for a completed semantic check which reports a
non-match or invalid log/sidecar, and `2` for usage, I/O, parsing, resource-limit, or other
operational failures.

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
those compatibility fields are empty and never alias a newer digest. Historical sidecars without
an explicit `sidecar_schema_version` remain readable through the schema-1 additive-field
projection. Once a sidecar carries an explicit version marker, verification is exact: a schema-2
sidecar cannot omit lossless hash identities, and changing its marker to `1` is rejected rather
than treated as legacy. This compatibility policy does not authenticate sidecar freshness; use a
trusted external anchor when downgrade resistance against replacement by genuinely historical
bytes is required.

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
A legacy log without exactly one `config_logged` event immediately after `run_started` is not
migratable to schema 2 because the rewrite will not invent missing configuration evidence.

Typed `f64` fields reject integer JSON tokens that cannot be represented exactly;
arbitrary-precision integers inside generic JSON config, payload, diagnostic, and label values remain
lossless. Schema-2 validation also checks SHA-256 syntax and artifact URI/path syntax. Percent
escapes are validated across URI paths, queries, and fragments, and every decoded component must be
valid UTF-8 without controls, Unicode format characters, line/paragraph separators, or Unicode
whitespace. Raw local paths likewise reject control, format, and line/paragraph separator
characters while retaining ordinary filename spaces. In the URI path component specifically,
encoded parent segments and encoded path separators are also rejected. Percent signs encoded as
`%25` are not recursively decoded.

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
temporary file and never truncates the previous destination.
Each sidecar file is committed atomically, but the three-file validation/summary/manifest set is not
transactional: a later sidecar failure can leave earlier sidecars from the new generation in place.
Manifests can
carry optional `ExternalAnchor` entries for a trusted service, transparency log, DOI record, or
detached signature reference. The crate validates their syntax but does not create or authenticate
signatures itself.

See the [repository README](https://github.com/sepahead/pid-rs) for context.

## License

Licensed under either of [MIT](LICENSE-MIT) or [Apache-2.0](LICENSE-APACHE) at your option.
