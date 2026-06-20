---
name: Bug report
about: Report incorrect behaviour, a panic, or a wrong numerical result
title: ""
labels: bug
---

<!-- Before filing, please skim the README's "Known limitations" and "Scientific cautions"
     sections: a near-zero/noisy atom at high dimension or a flagged-degenerate input may be
     expected behaviour rather than a bug. -->

**Describe the bug**
A clear description of what is wrong. If this is a *wrong-number* report, please say what makes
the expected value correct (an analytic value, a cited paper, or a cross-check against another
tool) — not just that it "looks off". Remember all information quantities are in **nats**.

**To reproduce**
Minimal code or command (Rust, the `pid_core_rs` Python module, or a CLI like `exp0`/`pid-runlog-replay`), ideally with a small fixed dataset/seed:

```rust
// ...
```

**Expected vs actual**
What you expected, and what happened (include the numerical value or panic message).

**Environment**
- pid-rs version / commit:
- Rust version (`rustc --version`):
- (if using the Python bindings) Python / NumPy / maturin versions:
- (if relevant) `parallel` feature on/off, and whether the serial and `--features parallel` paths
  disagree (they are expected to be bit-identical):
- OS:

**Additional context**
Anything else that helps reproduce: estimator config (`k`, metric, neighbour handling),
dimensionality of `S1`/`S2`/`T`, sample size, and the RNG seed if applicable.
