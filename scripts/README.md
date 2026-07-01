# scripts

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

Operational helper scripts for maintaining **pid-rs** and its downstream consumers.

## `repin-pidrs.sh`

Bumps `pid_vla`'s `pid-rs` git submodule to a target **pid-rs tag** and refreshes
`pid_vla`'s root `Cargo.lock` so the `pid-core` / `pid-runlog` path-deps re-resolve to the
new version. It stages the gitlink (`git add pid-rs`) and the refreshed lock, then prints a
suggested commit — it does **not** commit or push.

```bash
# Pin pid_vla's pid-rs submodule to tag v0.3.0 (sibling pid_vla layout, auto-detected):
scripts/repin-pidrs.sh v0.3.0

# Or point at an explicit pid_vla checkout:
scripts/repin-pidrs.sh v0.3.0 /path/to/pid_vla
```

**Why an explicit fetch + checkout, never `git submodule update --remote`:** `pid_vla`'s
`pid-rs` submodule history *diverged* from canonical `sepahead/pid-rs` — the prior pin was
not an ancestor of canonical `main`. `git submodule update --remote` resolves the branch tip
recorded in `.gitmodules` and fast-forwards; with a diverged history that either fails or
lands on the wrong commit. Instead the script does `git fetch origin --tags --force` and
`git checkout --detach refs/tags/<tag>`, which pins the requested tag by name unambiguously,
regardless of ancestry.

The lock refresh prefers `cargo update -p pid-core -p pid-runlog`, falling back to a plain
`cargo check` (never `--locked`, which would refuse a stale-by-design lock after a bump).

## License

Licensed under either of [MIT](../LICENSE-MIT) or [Apache-2.0](../LICENSE-APACHE) at your option.
