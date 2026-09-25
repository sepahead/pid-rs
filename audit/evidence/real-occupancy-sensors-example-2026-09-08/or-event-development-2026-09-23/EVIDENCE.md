# OR-event pooling: evidence and portable calculation

Author: Sepehr Mahmoudian. Study year: 2026.

The OR-matching forecast has greater log loss and binary Brier score than light alone and joint matching on all three previously examined recordings. Direct task loss rejects this forecast as an improvement over those baselines. This is a negative result for the five stated rules, not evidence that PID improves prediction, training or sensor placement, and not a rejection of all possible uses of categorical MGW.

The scientific object is a project-defined forecast inspired by the categorical Makkeh–Gutknecht–Wibral source-matching event. The input is the published empirical count table of two fixed four-bin sources and recorded binary occupancy. Each rule uses the original 8,143-row training counts and one pseudocount per target label after selecting its event. Evaluation uses training and two recordings of 2,665 and 9,752 rows, all examined before this follow-up was designed. The earlier file predates training. These are development comparisons with no untouched confirmation, IID assertion, population confidence interval or calibration claim.

## Full recorded precision

These values are copied from the retained [reference result](reference/RESULTS.json), without recomputing the forecasts. They retain the binary64 values serialized by the original calculation, not exact real-number loss values. The [CSV](FIVE_RULE_RESULTS.csv) contains the same 15 rows. Lower is better for both scores. Brier is the binary mean `(P(Y=1)-Y)^2`, not a sum across both labels.

| Recording | Rule | Rows | Log loss (nats per row) | Binary Brier |
|---|---|---:|---:|---:|
| datatraining.txt | constant | 8143 | 0.5170269303852334 | 0.16724575070146 |
| datatraining.txt | light | 8143 | 0.052882540010084404 | 0.011546637244820206 |
| datatraining.txt | co2 | 8143 | 0.3059815325178903 | 0.08438539495005636 |
| datatraining.txt | joint | 8143 | 0.048245580479750985 | 0.011360925169473101 |
| datatraining.txt | or | 8143 | 0.19014818746854573 | 0.050374728754283914 |
| datatest.txt | constant | 2665 | 0.716747644380514 | 0.25490520489179164 |
| datatest.txt | light | 2665 | 0.0977729357742339 | 0.024603060389190846 |
| datatest.txt | co2 | 2665 | 0.38953629465758083 | 0.11275264458790704 |
| datatest.txt | joint | 2665 | 0.08974404392437282 | 0.022241142792912526 |
| datatest.txt | or | 2665 | 0.2224311765551816 | 0.061581351034960666 |
| datatest2.txt | constant | 9752 | 0.514119073047541 | 0.16596946251889572 |
| datatest2.txt | light | 9752 | 0.04744305077272907 | 0.011556000266268865 |
| datatest2.txt | co2 | 9752 | 0.5065597371399897 | 0.16431099649635308 |
| datatest2.txt | joint | 9752 | 0.05076201919167954 | 0.011683151859365975 |
| datatest2.txt | or | 9752 | 0.21867695366675108 | 0.06128035888954198 |

The complete result also retains all 80 query-specific forecast probability pairs as exact fractions and floats, 96 integer inclusion–exclusion witnesses, historical comparisons, the three same-law unsmoothed MGW identity checks and all 244 specified check results. Six joint training query cells are empty; all 16 OR query pools are nonempty. The empty-event fallback is checked separately. The smoothed constant in this table differs from the original report's unsmoothed prevalence baseline; its separate historical control is retained.

## Inputs and historical execution

The [frozen original protocol](PROTOCOL.json) and [freeze record](reference/FROZEN.json) are exact historical bytes. The input files are [descriptive-comparisons.json](../descriptive-comparisons.json), SHA-256 `15798710c848225b45276134fa26ae5c04f9ffb0535f2bea23e33a4e19cd3487`, and [runtime-results.json](../runtime-results.json), SHA-256 `5f62b1de0c802fb14cd595a0a2afdfa04c27bb6c8084f0088a7228fb642380eb`. The former supplies published count tables; the latter supplies retained Rust redundancy. No raw-sensor parse, quantizer fit or Rust run was repeated in the follow-up.

The exact [historical calculator](reference/calculate.py) has SHA-256 `72d17b31f3ba82afaded00a3382d85e655b08b854e148f2223c5be0ea7c0cceb`; its [results](reference/RESULTS.json) have SHA-256 `5a1cfb4e368004d0cb9a5f8d01bfb73678d4dfc8b7c35fbb1a707847fa404bcc`. Its original clock and relative-directory assumptions are preserved. It is historical executed source, not the portable entry point. Do not remove its expired guard and call that a replay of the original attempt.

The [portable execution receipt](reference/EXECUTION.portable.json) retains the historical times, exit zero, interpreter version and output hashes, while removing machine-specific argv and working-directory paths and retaining the original receipt digest. [stdout](reference/stdout.txt) and [stderr](reference/stderr.txt) are unchanged. The original receipt reports about 0.030 seconds under a 55-second subprocess timeout; this single small reference calculation is not a comparative runtime benchmark.

The alternate [dense marginal calculator](root-recompute.py), its [freeze record](ROOT_RECOMPUTATION_FREEZE.json) and [result](ROOT_RECOMPUTATION.json) are also preserved exactly. It reproduced all five-rule metrics with zero recorded binary64 difference. It shares the inputs, formulas and Python logarithm implementation with the reference; this checks implementation arithmetic, not independent data or field validity. Its expired historical guard is retained as well.

## Portable successor entry point

The new [calculate.py](calculate.py) accepts an explicit input directory, reads and verifies the two exact input byte hashes above, and uses the historical scientific arithmetic and fixed tolerance `1e-12`. It includes no expired wall-clock condition or host installation locator. It writes a complete JSON object with sorted keys and no timestamps or installation-dependent metadata. Results are deterministic for these input bytes and the same arithmetic implementation; cross-platform last-bit identity is not asserted.

From the repository root, run:

```text
python3 -I -S -B audit/evidence/real-occupancy-sensors-example-2026-09-08/or-event-development-2026-09-23/calculate.py --data-dir audit/evidence/real-occupancy-sensors-example-2026-09-08 --output or-event-reproduction.json
```

The optional output path must not already exist. Without it, JSON is written to standard output. A mismatched input hash raises an error. A completed calculation returns zero only if its specified checks pass; a failed check returns one and remains in the output. The 24 September replay returned zero in about 0.044 seconds and passed all 244 checks. Its [complete output](reproduction/RESULTS.json) reproduces every retained scientific result field exactly, including 80 forecast pairs, 96 union witnesses and all 30 primary metric values. The [readback](reproduction/ROOT_READBACK.json) and [portable execution record](reproduction/EXECUTION.portable.json) bind that comparison to the exact calculator and inputs. This is one fixed-input reproduction, not a runtime benchmark, new experiment or cross-platform numerical guarantee. Operational limits belong to the caller; the historical protocol's expired clock was not reused.

## Mathematical boundaries

For the same empirical law, the unsmoothed query-indexed OR posterior satisfies `R = H(Y) - L(q)` using natural logs. The defining MGW paper uses base-2 logs; multiplying its bit values by `ln(2)` gives the report's nats. The forecast uses both observed source values to select the union, with intersection rows counted once. It is not a missing-sensor protocol or a fixed coarsened channel. A training-smoothed predictor's loss under another recording law is not that recording's MGW atom. Negative signed contributions do not establish a harmful sensor or causal effect.

## Rust implementation and computational cost

This is a Python reference calculation over 4×4×2 counts. The existing Rust example exposes empirical categorical MGW calculation, not this forecast or a PID-guided learner. For K occupied training states and source alphabets K_A,K_B, forecast construction uses O(K_A K_B K) arithmetic operations for a fixed number of rules and binary target. Precomputed probabilities give one lookup per source query. Scoring a recording with K_e occupied states costs O(K_e); the separate same-law identity check costs O(K_e²) because it rescans the event for each occupied state. Dense forecast storage uses O(K_A K_B) entries. Integer bit costs depend on count size. Raw feature extraction, quantizer fitting and data acquisition are separate costs. No Rust forecast API, latency guarantee or comparative speedup is claimed.

Source: Makkeh, Gutknecht and Wibral, *Introducing a differentiable measure of pointwise shared information*, [arXiv:2002.03356v5](https://arxiv.org/abs/2002.03356v5). Data: Luis Candanedo (2016), *Occupancy Detection*, [UCI DOI 10.24432/C5X01N](https://doi.org/10.24432/C5X01N), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Data hashes identify bytes and do not authenticate measurements or labels.

Suggested citation: Sepehr Mahmoudian (2026), *OR-event pooling: evidence and portable calculation*, supplement to *Recorded office sensors: what categorical and continuous shared exclusions can establish*. Include the exact repository commit or release. For the software, use [CITATION.cff](../../../../CITATION.cff).
