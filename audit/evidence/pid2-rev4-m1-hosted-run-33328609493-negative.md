# PID2 revision-4 M1 hosted operational-binding failure

## Evidence identity

- Workflow run: [33328609493](https://github.com/sepahead/pid-rs/actions/runs/33328609493)
- Formal job: [99303079208](https://github.com/sepahead/pid-rs/actions/runs/33328609493/job/99303079208)
- Head branch: `sepahead/pid2-rev4-behavior-v1`
- Head commit: `03c0980f256c2a66b3d64bff1686a8d116d76138`
- Event: manual workflow dispatch
- Run conclusion: `cancelled`
- Formal-job conclusion: `failure`
- Formal-job interval: 2026-08-30 18:39:28Z through 19:04:06Z

The GitHub job API was read on 2026-08-30. It reports steps 1 through 13 as successful, step 14 as
failed, steps 15 onward as skipped, and the formal job as failed. The complete run was later
cancelled; it must not be described as an all-green M1 run.

## Exact failure boundary

The only failed formal-job step was:

```text
python3 -I -S -B scripts/check-lean-toolchain-freeze.py
```

The hosted diagnostic, reproduced from a fresh checkout of the exact head commit, was:

```text
Lean toolchain freeze check failed: current C12 operational wiring digest mismatch: CHANGELOG.md: expected 1708b9bf6ea359d049a65d9460ad09c9b4aec06e5412c86278f7a5b210349433, found 2a399a33b244cab8cdc3d6a07fa61a81aeaf9a6b812861f5bc31b982cf7d8fdd
```

The observed digest is the exact SHA-256 of `CHANGELOG.md` at the M1 head. M1 intentionally changed
that file, but did not rebind the mutable `EXPECTED_OPERATIONAL_WIRING_HASHES` entry. The checker
therefore failed closed as designed.

## Successful prefix and its limit

Before the custody mismatch, the job successfully:

1. checked out and normalized the reviewed Git state;
2. checked the local Lean 4.32.2 source and policy/custody controls;
3. installed the pinned Elan and restored the cache;
4. fetched the Mathlib cache and built;
5. replayed formal declarations with Lean's kernel checker;
6. ran the finite-convergence checker in normal and optimized Python; and
7. ran its self-test in normal and optimized Python.

The captured run reported the expected 339 declarations, 246 theorems, and 49 self-test groups
before the operational-binding failure. These successful prefix steps do not turn the failed and
then cancelled run into an all-green run. The optimized freeze check, freeze self-tests, and later
formal steps were skipped after step 14 failed.

## Corrective disposition

Revision-4 M2 must update only the live current operational hashes after every operational file has
reached final bytes. The preserved historical r14 maps and receipt remain immutable. The freeze
checker and its self-test must then pass in normal and optimized Python.

This incident is operational custody evidence. It is not evidence against the PID2 arithmetic,
the Lean theorem statements, or Lean's kernel; it also does not independently validate any of
those objects.
