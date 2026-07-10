# scripts

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

Operational helper scripts for maintaining **pid-rs** and its downstream consumers.

## `generate-csxpid-reference.py`

Regenerates the machine-readable continuous-SxPID cross-validation fixture used by the
`pid-core` bivariate and trivariate estimator tests. The upstream implementation is the public
package linked by Ehrlich et al. (2024), pinned to commit
`7bb984611a422cf7944ece68993fe3a27e2eadec`. The script rejects a different or dirty checkout and
an unpinned Python environment before importing upstream code.

```bash
git clone https://gitlab.gwdg.de/wibral/continuouspidestimator.git /tmp/continuouspidestimator
git -C /tmp/continuouspidestimator checkout --detach 7bb984611a422cf7944ece68993fe3a27e2eadec

uv venv --python 3.10 /tmp/csxpid-venv
uv pip install --python /tmp/csxpid-venv/bin/python \
  numpy==1.23.1 scipy==1.8.1 mpmath==1.2.1 setuptools==63.2.0

/tmp/csxpid-venv/bin/python scripts/generate-csxpid-reference.py \
  --csxpid-checkout /tmp/continuouspidestimator
/tmp/csxpid-venv/bin/python scripts/generate-csxpid-reference.py \
  --csxpid-checkout /tmp/continuouspidestimator --check
```

The tracked fixture contains the complete deterministic inputs, upstream estimates in bits, their
conversion to pid-rs's nats, the backend and environment pins, and the upstream source revision.
Its `.sha256` sidecar covers the complete JSON artifact; the current digest is
`d952e742879cb83bcdd2c46b779a9b90d9ee0729917a0fb312ad8d1918a40536`.

## `repin-pidrs.sh`

Bumps `prisoma`'s `pid-rs` git submodule to a target **pid-rs tag** and refreshes
`prisoma`'s root `Cargo.lock` so the `pid-core` / `pid-runlog` path-deps re-resolve to the
new version. It stages the gitlink (`git add pid-rs`) and the refreshed lock, then prints a
suggested commit — it does **not** commit or push.

```bash
# Pin prisoma's pid-rs submodule to tag v0.4.0 (sibling prisoma layout, auto-detected):
scripts/repin-pidrs.sh v0.4.0

# Or point at an explicit prisoma checkout:
scripts/repin-pidrs.sh v0.4.0 /path/to/prisoma
```

**Why an explicit fetch + checkout, never `git submodule update --remote`:** `prisoma`'s
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
