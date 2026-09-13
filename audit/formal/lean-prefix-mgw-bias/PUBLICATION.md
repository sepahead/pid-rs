# Finite-prefix MGW bias: reading and evidence

Start with the [one-page summary](../../../output/pdf/prefix-mgw-bias-summary.pdf), then the
[full paper](../../../output/pdf/prefix-mgw-bias.pdf). Their standalone Markdown sources are
[SUMMARY.md](SUMMARY.md) and [EXPOSITION.md](EXPOSITION.md). The [theorem map](THEOREM_MAP.md)
lists all five locally accepted families, assumptions and proof steps. [RESULTS.md](RESULTS.md)
preserves the original accepted campaign.

The results bound the difference between a population MGW atom mean and the expectation of a
specified finite-prefix experiment. Sources and target have finite categorical alphabets; rows
are IID complete source-and-target observations, with unrestricted dependence within each row.
All information quantities use nats. Population support counts and mass floors are premises where
stated. Sample occupancy or a smallest observed frequency does not establish those premises.

These bounds quantify approximation error before sampling uncertainty is added. They can help
choose or reject a prefix horizon under a justified population model. They do not supply a
confidence interval, a deployed estimator, or evidence that PID improves a sensor decision.

The [historical portable replay](HISTORICAL_PORTABLE_REPLAY.md) records source-preserving local
kernel checks and their retained limitations. The [current PDF record](../latex/prefix-mgw-bias/CURRENT_REPRODUCTION.md)
separately records 316 inert control cases and eight exact full/summary builds on 12 September
2026. Neither reproduction nor clear presentation establishes scientific priority.

[Source correspondence](SOURCE_CORRESPONDENCE.md), [package status](PACKAGE_STATUS.json), and
the [replay boundary](REPLAY.current.md) distinguish these evidence classes. Hosted proof replay,
Rust correspondence, finite-sample coverage, dependent-row inference and application comparisons
remain open. No result transfers to continuous shared exclusions or another PID without a separate proof.
