# pid-runlog

[![CI](https://github.com/sepehrmn/pid-rs/actions/workflows/ci.yml/badge.svg)](https://github.com/sepehrmn/pid-rs/actions/workflows/ci.yml)
[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

A versioned, hash-chained **run-log schema** and replay/validation helpers for reproducible
partial-information-decomposition pipelines (used by [`pid-core`](../pid-core)). Each record is
content-addressed (SHA-256), so a run can be replayed and integrity-checked offline.

```text
# validate a run-log produced by an experiment
cargo run -p pid-runlog --bin pid-runlog-replay -- --validate run.jsonl
```

See the [repository README](https://github.com/sepehrmn/pid-rs) for context.

## License

Licensed under either of [MIT](../../LICENSE-MIT) or [Apache-2.0](../../LICENSE-APACHE) at your option.
