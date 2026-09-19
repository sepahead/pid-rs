# Gradient publication: current dependency correction

The publication commit `7f653c5a85b407033383daf7c5e8d34c39ae782e` added the categorical MGW
gradient paper and the support-change counterexample. Its
[hosted CI job](https://github.com/sepahead/pid-rs/actions/runs/35439952960/job/105888927109)
failed on 19 September 2026. The certified-SxPID2 claim checker still expected the preceding
`scripts/README.md` bytes. Inspection found the same omission for the formal-PDF aggregate script.

The earlier exact-count reference tests and seven-target Lean checks in that job passed. The
reported failure was a source-binding mismatch. It did not report a false theorem or an incorrect
numerical reference value. The failed job remains failed; a later correction does not change it.

## Correction

Review the complete changes to both current containers, then replace only these two digest
literals in `scripts/check-certified-sxpid2-claim.py`:

| Current dependency | Previous SHA-256 | Reviewed publication SHA-256 | Change being bound |
| --- | --- | --- | --- |
| `scripts/README.md` | `87daed8e93d635b5cf0a9b4d2cb2567ffa02835e2864e3ebb3faa6435d0ec99d` | `bf7b33f204ad5576680cd1112991ebc23f340d42dfff80b7b046288f3ed5cc35` | Add gradient and counterexample publication instructions. |
| `scripts/check-formal-pdf-set.sh` | `dc5b7e7ca0bd3adbe348e63815f39b5e61a7edc8955f50e5ec849852285bf0e9` | `322c2a7b879b630e1b74d81eb2959cfa7ceced55a7c1520a290b6046da44b3bd` | Add the two papers, bounded dispatch and explicit unsupported-mode refusals. |

The checker source changes from SHA-256
`6d2e9e51d85bf0eb5d04ec6104e2a308a7a93675d6f61aea2cf6b3816fc843e1` to
`92da1e8bace0d5e44e3cf44df879e7a44b295e73b9b9dc624c59f7d4b3f4d21b`.
Both complete-byte checks remain mandatory. The claim, mathematical definitions, historical
evidence, scientific reference values and checker logic keep their exact bytes. The current Lean
operational map must bind the corrected checker and changelog; its historical map is preserved.

The [earlier container correction](certified-sxpid2-post-publication-container-rebind-2026-09-02.md)
explains the same current-versus-historical distinction. It supplies no execution evidence for
this correction.

## Verification and prevention

The applicable verification is the certified claim checker and its unchanged hostile suite in
normal and optimized Python, followed by current freeze, source-state and publication-link checks.
The containing commit needs its own post-commit identity and exact-SHA hosted checks before main
promotion. An earlier green run does not satisfy those obligations.

The publication producers, their inputs and the reviewed PDF bytes are unchanged by this
correction. Their retained reproduction evidence keeps its original scope. No new Lean replay,
mathematical theorem, estimator calibration or application result follows from this binding change.

The missed dependency was the certified checker's complete-byte guard on two general-purpose
publication files. Future edits to either file must inspect this guard as well as the current Lean
operational map. In particular, a later change to the scripts guide requires a fresh current
documentation binding; it cannot inherit this exact digest. Repeating the unchanged failed CI run,
omitting the guard or rewriting a historical receipt would not repair this dependency.
