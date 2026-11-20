# PID2 represented-coordinate arithmetic after the Shannon ratio correction

Sepehr Mahmoudian · 20 November 2026

The two-source PID constructor sums already represented binary64 numbers. Its shared Rust accumulator changed when normalized Shannon reports acquired a rounded quotient. The PID2 reconstruction rule, its four input coordinates, the independent exact-rational comparison and the accepted reconstruction distance of 32 adjacent binary64 positions keep their revision-4 definitions. [Represented-coordinate arithmetic](../../PID2_REPRESENTED_COORDINATE_ASSURANCE.md) · [Shannon ratio arithmetic](../research/normalized-shannon-ratios/README.md)

The historical checkout is `0f3122a96e48a099581ad4faf3e3d5d9138367f6`. The production correction is `03325745f64becf437b9b3042b51a9d925450579`. The current PID2 checker differs from its historical source in one full-file SHA-256 entry. Its other three source files, exact model, test partitions and hostile controls have the same bytes. Each checker accepted its own four source files and rejected the other accumulator in normal and optimized Python. [Current checker](../../scripts/check-pid2-represented-coordinate-v4.py)

| Complete file | Historical SHA-256 | Current SHA-256 |
|---|---|---|
| `crates/pid-core/src/exact_binary64.rs` | `6e7d6be525878638e4be253aff9bd74d25dd94afb53f1b520fb8e4e1a0a8cdfb` | `c3d047917b9f1c5d162c325e3128183787f0f874205fe80ba0bb6c2dd68042c5` |
| PID2 source checker | `47b77161b41ff94da2ce47b83adc7d3a5e5604a4e2a5cd8822e86129fa6f8051` | `452a954ab7301d860ea7fdc63cffc5efaa2b39ea1f74c211fc0d8c10f95639cb` |

For the sum, the magnitude is an integer number of minimum-subnormal units, each equal to two to the power of −1074. The new shared rounding function receives 1,074 fractional bits and a zero division remainder on this path. If the highest occupied bit has index below 52, the magnitude fits directly in the subnormal significand. Otherwise the sum keeps the top 53 bits, rounds once using the guard and lower bits, and chooses an even significand on an exact tie. Equal positive and negative magnitudes still produce positive zero. The direct quotient uses a separate scale and remainder. [Rust accumulator](../../crates/pid-core/src/exact_binary64.rs)

At source-profile commit `54b6c186aedacbba046cdd6ee81886d5ace43764`, the working `invariants.rs` had SHA-256 `00e57e312888783928ce967aa44b3d2769f4c39e3f4ae377b3cbd8c1f6b390d5`. The revised Rust documentation states that for one empirical distribution, rounding each exact marginal, leave-one-out and joint mutual information once to nearest preserves their order. Separate estimation or numerical errors in the computed inputs can violate that order. The documentation replaces precisely two Rust comment paragraphs. The resulting complete source file has SHA-256 `99cfbc6b26ae86964e305bdf7aa81f842220044f1c833fe9ad7e7df76fd86589`. [Exact documentation profile](../../scripts/check-pid2-shannon-rustdoc-profile.py)

With complete Git history, run the following in the two-paragraph documentation profile at `9411667f972af0547d391a0be6d95b011b515171`. The first command derives the revised file from the production commit and verifies both the committed and working copies. It also checks the other 12 production inputs and the two earlier checker programs byte for byte. The second exercises one accepted projection and eleven required refusals. Repeat each command with `-O` immediately after `python3`.

```sh
python3 -I -S -B scripts/check-pid2-shannon-rustdoc-profile.py source
python3 -I -S -B scripts/check-pid2-shannon-rustdoc-profile.py controls
```

For the original source comparison, run `scripts/check-pid2-shannon-source-profile.py source --repo-root <production-checkout>` with Python, pointing it to a checkout of the exact production commit above. It replays the historical and changed accumulators against both checker versions and requires the two crossed pairs to fail. Its `controls` operation exercises one accepted and eight rejected native logs. The workflow retains these results separately from the documentation checks.

The hosted workflow checks out the production commit independently of the review checkout and uses Rust 1.99.1 on Ubuntu 24.04. In each of debug and release, it records all three exact-sum tests, including the original 561-case corpus, all 17 PID2 unit tests, all 18 integration tests and all 34 `exp0` tests. It checks every executed test name, the counts, the exit status and the result summary. It also executes the canonical revision-4 full checker in both Python modes. The run artifact identifies the checkout, compiler, commands and native logs. These finite checks concern represented scalar arithmetic. Estimation, calibration and executable refinement require separate evidence. [Hosted workflow](../../.github/workflows/pid2-shannon-source-profile.yml) · [Observer and fixed input hashes](../../scripts/check-pid2-shannon-source-profile.py)


## Which functions return the typed report

The stable Rust functions for the target-based average degrees of redundancy and vulnerability, including their explicit-policy variants, return `NormalizedInvariantReport`. They take supplied mutual information values in nats. The source-only categorical diagnostics `red_degree_discrete` and `vul_degree_discrete` take columns of labels and return a scalar in `PidResult<f64>`. The revised rustdoc names the target-based report and shows why both source-only formulas coincide with the published degrees when the target copies the full source tuple and joint entropy is positive. It also distinguishes exact-real threshold passage from a rounded denominator equal to the floor, and stationary ergodic cumulative prefixes from arbitrary moving windows. The checker derives five documentation regions from the preceding profile.

To check the documented successor, run both commands in the checkout that contains it. Repeat with `-O` immediately after `python3`. The source check verifies the predecessor’s exact checker, both Git and working files, and the registered Git mode and blob transition. The controls accept the documented projection and require 13 specific refusals. Native PID2 and exact-sum observations retain their original production commit. [Successor checker](../../scripts/check-pid2-shannon-report-label-profile.py) · [Predecessor checker at its source](https://github.com/sepahead/pid-rs/blob/9411667f972af0547d391a0be6d95b011b515171/scripts/check-pid2-shannon-rustdoc-profile.py)

```sh
python3 -I -S -B scripts/check-pid2-shannon-report-label-profile.py source
python3 -I -S -B scripts/check-pid2-shannon-report-label-profile.py controls
```
