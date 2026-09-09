# Current operational-binding failure and correction

Commit `f045cf3cb8aaee3db84cb69e5a3860432dbddfc4` updated two publication-support
hashes in the certified SxPID2 checker and documented that change. It omitted the
dependent current hashes in the Lean toolchain gate. The
[formal job](https://github.com/sepahead/pid-rs/actions/runs/34400102693/job/102629583810)
failed at 20:41:55 UTC on 9 September 2026, before its later steps could run.

The first reported mismatch was `CHANGELOG.md`: the gate expected
`f584cf2c0f01a4b10dd32f2b664b0d04b0615aab056ea4b17dfecc575de66c74`, but the
file hashed to `296dbfa2b696baa951c48f74c194b2daa07d142d302b662650d8746ff88a0738`.
Source review also found the unreached mismatch for
`scripts/check-certified-sxpid2-claim.py`: expected
`72ff1b39074c45d51cf79c5b4f0897cf4c511d2197a280240a6f522a2af74f27`, actual
`2cbd13279ad8309995d3a7b59be58e6de25b4ec3d5824b2d42286e66ba634735`.
The failing repository source and inputs remain in the named commit.

The correction updates both entries in `EXPECTED_OPERATIONAL_WIRING_HASHES`.
Its changelog hash binds the final changelog, including this correction's entry.
The current-source-state manifest is regenerated after those edits. Historical
r14 inventories, receipts, mathematical sources and proof/certificate predicates keep
their existing bytes and meaning.

Updating only the first mismatch would leave the second defect. Repeating the
same hosted inputs would not repair either binding. Removing the hash checks or
rebinding a historical receipt would weaken or misstate the evidence. The failed
run retains its outcome; the correction requires its own checks and exact-commit
hosted evidence. This is an operational consistency correction, with no new
mathematical or estimator claim.
