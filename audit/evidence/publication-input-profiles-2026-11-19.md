# Exact publication runs for the revised November method catalog

On 19 November 2026, two local publication profiles reproduced their existing
PDF references after a change to the generated method catalog. Both source
documents link to that catalog. The recorded office-sensor v6 and finite MGW
v9 controls had rejected the revised file in normal and optimized Python with
`input size changed: METHODS.md`. Their original profiles and September run
are available in the [September execution record](cross-implementation-reverification-2026-09-26/results/publication-profile-rebuilds.txt).

The runs used a working copy based on commit
`15d9bd89b4b41303fd18addb68b1e9d1995132eb` with the November finite-study
and statistical changes. The revised [method catalog](../../METHODS.md) has
567,476 bytes, mode 0644 and SHA-256
`e00863d3763ebe47c30a6a6ca3efac286af118907837a83d273cb9aa114ee17d`.
The office-sensor profile binds 39 files and the finite MGW profile binds
134. In each file map only the catalog entry changed. The native tools,
article, figure and reference PDF identities are those of the preceding
profile for each paper.

| Publication input profile | Profile SHA-256 | Builder SHA-256 |
|---|---|---|
| [Recorded office sensors v7](../formal/latex/real-occupancy-sensors/publication-inputs-v7.json) | `4867cd29aa1b4d34869c7d13abede0405f02ebeb5c53cad5f0a662e9bcfcd6e8` | `2197b6c29a4af1ef250fe55cbe98a5431e8a674a96f9a43133409403941288fa` |
| [Finite MGW v10](../formal/latex/mgw-fixed-world/publication-inputs-v10.json) | `cabc7e31bfbc1e24fb61a613f5e861a13e92dd27811da979249977f27c5be171` | `d1c62a3b936e774650c0271575d34f2e769d450d20d75f353eb29d5051b49205` |

The local machine ran macOS on arm64 with CPython 3.14.6 and the registered
TeX Live 2024 toolchain. Both profiles ran the following commands in normal
and optimized Python. Set `<name>` to `recorded-office-sensors` or
`mgw-fixed-world`. Use a fresh work directory for each invocation that takes
one. Insert `-O` immediately after `python3` for the optimized runs.

```text
python3 -I -S -B scripts/check-<name>-pdf-self-test.py --work-dir <fresh-control-work>
python3 -I -S -B scripts/build-<name>-pdf.py --exact --check --tex-root <canonical-tex-root> --work-dir <fresh-build-work>
python3 -I -S -B scripts/build-<name>-pdf.py --cross-toolchain
```

Each of the four exact invocations exited 0 with two fresh builds and
`exact_reference_reproduced`. The two PDFs and the four local exact-run
`RESULT.json` digests are identified below. Receipt files include
machine-specific run times and working locations.

| Paper | Pages | Bytes | Reference and rebuilt PDF SHA-256 |
|---|---:|---:|---|
| Recorded office sensors | 13 | 278,311 | `54b20e1cea7ce38b7a001674f6fb1854e38db30d3129f5fd4aad1ea7b3c30a8d` |
| Finite MGW | 9 | 231,810 | `6fc4cfbe5bb71037515c4ebdd3119b20e6e970ce6f117e1b9659b44a728b565a` |

| Paper | Normal exact receipt SHA-256 | Optimized exact receipt SHA-256 |
|---|---|---|
| Recorded office sensors | `97070f693fdec01fde10679c62d71e67cb5393f1d585cff5a93641d868ab70d1` | `ce5755db8303bc9afcc8ea1873f69c2d9249e54cc712cec4885c7a44cf834625` |
| Finite MGW | `d4520702daae4a1cbc6c466cabe9d2ddbb96f3226921287a3a390af9ed1ff345` | `1c7c76e9ac9b1a9dc03d2aba50cafffaa620e3e8736ae1634910add6b3b0d2ec` |

Each office-sensor self-test exited 0 for 23 controls. Each finite MGW
self-test exited 0 for 72 publication controls, eight direct Markdown
citation controls and five direct SVG citation controls. All four
cross-toolchain calls returned the specified refusal status 2. These
observations establish local execution of the two publication checks.
Mathematical and visual evidence for each paper retains its previously
recorded scope.
