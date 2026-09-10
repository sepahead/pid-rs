# Finite MGW publication receipt

**Local exact PDF aggregate completed; final source and commit qualification pending.**

The [finite comparison](mgw-fixed-world-added-information-2026-09-09.md) and its [nine-page PDF](../../output/pdf/mgw-fixed-world-added-information.pdf) use independent fair bits $A,B,U$, target $Y=(A,B)$, and baseline $A$. Adding $U$ or $B$ gives the same categorical MGW synergy, $\log(4/3)$, although $I(U;Y\mid A)=0$ and $I(B;Y\mid A)=\log 2$. All values are in nats. This fixed-law comparison shows why equal synergy alone does not determine additional conditional information.

The PDF contains 231,798 bytes and has SHA-256 `24c16b51c970d9cec8847f923d76f0d7e8a0bd137f54512e028de0e2712ec378`. Its [publication profile](../formal/latex/mgw-fixed-world/publication-inputs-v1.json) and the unchanged [source map](mgw-fixed-world-added-information-2026-09-09/source-map.json) identify the document inputs.

On 10 September 2026 at 02:35:58 UTC, `scripts/check-formal-pdf-set.sh --exact` completed with exit status 0. The aggregate covered all declared papers, including two exact MGW PDF builds and 61 MGW builder controls in each of normal and optimized Python modes. It also reported 111/111 hostile publication-link controls in each mode and passed 110 typed-publication-inventory controls.

The current certified-SxPID2 and Lean-toolchain binding checks also passed in both Python modes, with 126 and 147 rejected mutations per mode, respectively. The notice correction passed its focused builder, figure and dependent-PDF checks before the successful aggregate. These checks preserve the existing mathematical claims and historical replay records.

The aggregate stdout has 63,912 bytes and SHA-256 `ca124b7803d5f544a38ba9f13dd3f70057bc0896b96d9a10ab229b78d1e81373`. Its 4,070-byte stderr, SHA-256 `0ed865a71d0bc864c80fef5053cc6ea2866d6f79820eb388132e0dc6185ad9c2`, contains two successful 13-test unittest reports.

Two earlier aggregate attempts remain failed records:

- The first stopped with status 1 at the mathematical-workflow PDF source-snapshot guard: an in-checkout temporary build root placed generated font-cache files under the source tree. The successor used external scratch.
- The second stopped with status 1 in the mathematical-results-guide builder self-test. The added MGW notice changed the whole third-party-notice digest, leaving current notice pins and dependent digests stale. The narrow current dependency closure was corrected; historical hosted evidence and the existing checks were preserved.

This receipt summarizes recorded local execution; its raw operational logs remain local recovery records. The successful aggregate did not include this final receipt or the final source-state file. Their final publication-link and source-state checks, containing-commit identity, postcommit checks, and hosted/mainline qualification remain to be recorded.

The [archival guide](../formal/lean-mgw-fixed-world/PUBLICATION.md) identifies the preserved 21-target Lean evidence. The PDF aggregate checks document reproduction; it does not rerun those proofs. No fresh dedicated hosted proof replay is claimed. The archival result does not establish statistical calibration, sensor-deployment value, or scientific priority.
