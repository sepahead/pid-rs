# Lean 4.33.0 replay addendum for `KSG-INTEGER-HARMONIC-001` revision 4

## Authority split

This addendum records the current Lean replay without rewriting the earlier execution record.
The three objects have distinct roles:

| Object | Role | SHA-256 |
|---|---|---|
| `formal-assurance-v4.md` | historical Lean 4.32.0 execution and scope record, preserved byte-for-byte | `322c3f633d0e1316a401e92b10afb541ee82cb9ba94afef88f4a2937c934b6ff` |
| `../../audit/evidence/lean-ksg-integer-harmonic-4.33.0.json` | current machine-readable Lean 4.33.0 theorem and axiom-inventory evidence | `d25f18530305e404d1d24a6eab2bda5f57b226d3db97c50ba4265c0c85ee9c35` |
| this file | current human-readable version boundary and replay route | bound by `active-packet-v4.json` |

The historical file's 4.32.0 toolchain, Lean commit, Mathlib revision, and project-file hashes are
historical observations. They are not current 4.33.0 identities. Conversely, this addendum does
not retroactively claim that the earlier execution used Lean 4.33.0.

## Current exact environment

The current replay is pinned to:

| Artifact | Identity |
|---|---|
| Lean toolchain | `leanprover/lean4:v4.33.0` |
| Lean source commit | `d8b18978322de05a8f3dba51ef03cf5461676c17` |
| observed evidence execution | `Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit d8b18978322de05a8f3dba51ef03cf5461676c17, Release)` |
| Mathlib source revision | `db584cd6d46c92f209a44c0f1c829460d327499d` |
| `audit/formal/lean/lean-toolchain` | `302cd63c54178885b89e669f33b38f12f4dd7ae7e5cac537b3203e3768d8fb2b` |
| `audit/formal/lean/lakefile.toml` | `ec5def1f5f0aa36218f767993c144a1b76ed9b77d6a429028dd5bb8f857354e0` |
| `audit/formal/lean/lake-manifest.json` | `6527e482d9bdbcbf48bf47a420df1ccf9b99958ea0152693446816891cc910af` |
| revision-4 Lean source | `32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4` |
| Lean checker source | `020034884471ace9bcae1c8aa0b303a223758964278b6a0b1ac9ff5eeea94684` |
| Lean self-test source | `0bb0c999ad8bc20137deda54620d2983a5bd0ecaf4a74f81cbde23f997560517` |

The full displayed Lean version is the host-bounded identity captured by the current evidence on
Darwin arm64. A replay on another supported platform must still match version 4.33.0, source
commit `d8b18978322de05a8f3dba51ef03cf5461676c17`, and the `Release` build, but its observed platform
field is a distinct runtime fact and must not be represented as the Darwin execution above.

The revision-4 proof source is unchanged by the toolchain migration. The current checker requires
the exact Lean release identity, project pins, source hash, 19 named theorem declarations, and the
complete permitted-axiom inventory. The baseline-first self-test retains 14 semantic mutations.
The unversioned and `v2/` Lean sources remain identical historical revision-2 objects with SHA-256
`812188bd1e0d76d8a19f4f2b410b566b6909c7bddb5b0024f6a272a4f240f943`.

## Scope and non-transfer boundary

The 4.33.0 replay rechecks exactly the finite-sum, monotonicity, cancellation, index-map,
range/symmetry, rational-tail-bound, and rational-to-real bounded-combination conclusions already
declared by the revision-4 Lean source. `PositiveIntegerDigammaPremise` remains a typed unproved
premise. This replay does not establish count geometry, binary64 refinement, the full KSG
estimator, estimator consistency or calibration, continuous-support validity, shared-exclusions
semantics, any PID atom, Rust refinement, or application validity.

The separately encoded Z3 obligations and all earlier numerical/certificate evidence keep their
own authority and limitations. Re-executing the Lean source under 4.33.0 neither makes those routes
failure-independent nor promotes the packet from its recorded `integration_no_go` lifecycle
state.

## Required replay

```text
python3 scripts/check-lean-ksg-integer-harmonic.py
python3 -O scripts/check-lean-ksg-integer-harmonic.py
python3 scripts/check-lean-ksg-integer-harmonic-self-test.py
python3 -O scripts/check-lean-ksg-integer-harmonic-self-test.py
```

The machine-readable 4.33.0 evidence is the execution record for the checker route. The active
packet binds that evidence, this addendum, the exact checker/self-test sources, and the historical
4.32.0 assurance record as separate objects; none substitutes for another.
