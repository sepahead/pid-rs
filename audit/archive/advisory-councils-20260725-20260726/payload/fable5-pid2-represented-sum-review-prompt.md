# Fable 5 Max adversarial brief — `PID2-REPRESENTED-SUM-001` revision 1

You are an external, read-only adversarial reviewer. Do not edit, commit, push, or weaken any gate.
Use scratch space only under `/tmp`. Model agreement is not evidence. Re-derive, falsify, and
measure from first principles; label every unretained scratch result as diagnostic.

## Frozen context

- Repository: `/Users/torusprime/Development/sepahead-github/pid-rs`
- Base commit: `ca2eaf31ce7b719d04a43e0d6e1d2c21c6ff06a7`; the worktree is intentionally dirty with a
  completion-run candidate, so hash every live file you use.
- Date: 2026-07-25; units: natural logarithms/nats.
- Rust/Cargo lock SHA-256:
  `2a390c1a3f468ed938e8c2e6597e78b26b933761c6200b0bf5e01d4b75f3c81d`.
- Target under review: macOS/aarch64 local execution plus source-level portability reasoning.
- Claim packet SHA-256 at prompt freeze:
  - `claim-v1.md`: `f465defcc596c9187e819a083be3611c69a103738d9699161613313ad3c5fbca`
  - `obligations.md`: `d459a0803a64efe5bd055739ff17b66d514b5fe93766a158bafaff25a0a50a80`
  - `routes.md`: `e93be499ca31e08325c29f460faf7ec401e815893eee25eebabdbfff28a29c81`
  - raw witness: `c7b80aba96a5ae0569e8f79d612580dff54fee5ef9a367a7cebf5cbfa505f6c3`
- Live source/test SHA-256 at prompt freeze:
  - `crates/pid-core/src/pid2.rs`:
    `cdeabfbbb1f0017746a2255b1c41de19dcd9e14013b9d22b3d84affec1d5c2dc`
  - `crates/pid-core/src/stats.rs`:
    `481a1e9c2dd33df01a2a98e32ebd5218f99478b2e7baf308f832851457ee9d96`
  - `crates/pid-core/tests/pid2.rs`:
    `72a3949ff68227fe9cf20085fdc75bab9a4307574bcf1e782cba9c61c104c101`
- Provisional release/catalog SHA-256:
  - `release-scope-1.0.json`:
    `6b50a2d8f87384ac7e483ed1d211cd10c9db63cc13187b0c25cc0e9e0bead515`
  - `method-catalog.json`:
    `59e815d1b1fc8dfa6944948caaba33d1d17701c723bddebd14cf3cfc663faf35`

Read completely before judging:

- `AGENTS.md` and `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md`;
- every file in `claims/PID2-REPRESENTED-SUM-001/`;
- revision-2 `IMIN-TIE-SWAP-001` claim, obligations, routes, evidence, and raw grouping failures;
- `crates/pid-core/src/{pid2,stats}.rs` and all relevant PID2 tests;
- KSG/PID2 catalog and release-scope entries and their reverse dependants; and
- the current Git diff for these paths.

## Exact claim under attack

For every finite binary64 `Pid2Estimate` accepted by `Pid2Result::from_estimate`, return in
`synergy` the round-to-nearest, ties-to-even binary64 value of the exact represented-input linear
form

```text
J - I1 - I2 + R,
```

computed once by the fixed-limb accumulator. Keep unique-atom arithmetic and every current
finite/identity rejection unchanged. This gives the four represented inputs a source-order-
independent meaning. It does not correct upstream KSG/shared-exclusions errors, prove whole-result
source symmetry, change the paper definition, or validate statistics/support/applications.

## Required attacks

1. Re-derive the fixed-bit witness independently. Verify whether current `from_estimate` really
   returns `+2^-56` versus `+0` and whether both paths pass the existing identity guard.
2. Prove or refute that one exact represented-input sum is definition-preserving and strictly
   stronger than left association, regrouping, compensated heuristics, or returned-atom residuals.
3. Search for accepted finite quadruples where replacing the current direct/fallback selection
   with the unconditional exact sum changes accept/reject behavior. If any exist, retain the
   smallest raw-bit example and classify whether the old or new behavior better matches the
   constructor's documented invariant.
4. Attack the accumulator correspondence: term signs, duplicate use, positive-zero rule,
   non-finite premise, overflow capacity, and 32-ordered-bit identity check. Do not confuse the
   generic helper theorem with this call-site binding.
5. Inventory every reachable Rust, Python, example/diagnostic, catalog, assurance, and release
   consumer. Independently confirm or refute the proposed four emitting release families and five
   catalog reverse dependants. Do not over-bump unrelated families.
6. Design the smallest discriminating behavior and mutation suite. State which fault each test
   uniquely kills and distinguish compiled behavior from textual source checks.
7. Review compatibility honestly: estimator bits change, but definition and public declarations
   do not. Decide whether the already-open KSG estimator migration makes this the right release
   boundary or whether a separate revision is required.
8. Apply semantic, mathematical, numerical, executable, formal-boundary, statistical,
   provenance, portability, resource, and downstream-authority lenses. Seek counterexamples, not
   reassurance.

## Required output

- `GO`, `CONDITIONAL GO`, or `NO-GO`, with exact blockers;
- corrected obligation graph and minimal critical cut sets;
- accepted and rejected alternatives with raw-bit or exact evidence;
- exact affected dependency/release closure;
- minimal regression/mutation plan;
- strongest permitted wording and prohibited promotions; and
- at least ten concrete adversarial failure scenarios paired with gates.

Do not call finite or model-generated evidence a theorem, formal verification, calibration,
compatibility proof, or consumer qualification.
