# Phase-A verification record, 2026-07-25

> **Historical transcript plus follow-up repair.** The quoted 9+5 mutation output below is the
> original Phase-A observation. A later critical review found that a valid same-name weakening of
> `empirical_law_nonnegative` escaped that gate. The current checker now SHA-256-binds the complete
> bridge, the semantic contract additionally fixes nonnegativity, and the current self-test closes
> the demonstrated route as 10 static plus 5 isolated mutations. The original output is retained
> rather than rewritten.

## Run context

- Branch: `main`
- Base `HEAD`: `ca2eaf31ce7b719d04a43e0d6e1d2c21c6ff06a7`
- Final replay time: `2026-07-25T21:11:25Z` (record creation time)
- Toolchain reported by the checker: Lean 4.32.0,
  `arm64-apple-darwin24.6.0`, commit `8c9756b28d64dab099da31a4c09229a9e6a2ef35`
- Semantic-contract SHA-256:
  `f9080b1ff1a4e544fa328ff303fbac16adce0583741948a8c66b0b690efacb7d` (historical Phase-A bytes;
  superseded by the repaired contract binding recorded in the current checker)

The worktree contained concurrent changes outside this claim. This record binds the commands and
reported outcomes below, not a clean Git tree or committed artifact identity. Final package and
software-identity binding remains a phase-B obligation.

## Pinned formal checker

Command:

```text
python3 scripts/check-lean-finite-convergence.py
```

Reported outcome:

```text
OK: checked 9 Lean sources with an exact ordered 263-declaration inventory across 7 imported modules, all 201 source theorems against the permitted axiom basis, and the separate event/count/fractional-cover/generic-Mobius semantic contract
```

The checker performs the Lake build, Lean kernel replay, separately compiled semantic contract,
dependency checkout checks, and generated complete source-theorem `collectAxioms` audit.

## Fail-closed mutation replay

Commands:

```text
python3 scripts/check-lean-finite-convergence-self-test.py
python3 -O scripts/check-lean-finite-convergence-self-test.py
```

Both reported:

```text
OK: Lean finite-convergence gate self-test killed all 9 static source mutations and all 5 isolated Lean semantic mutations for their intended reasons
```

The isolated suite first compiled an unmodified temporary bridge, then required proof failure after
source swap, redundancy-union replacement, target-restriction erasure, joint-to-marginal change,
and positive-support weakening. Static mutations additionally covered imports, inventories,
semantic digest, forbidden declarations, dependent-product regression, a contradictory scope
claim, and native-evaluator injection.

## Follow-up source-custody repair, 2026-08-10

At `2026-08-10T06:21:39Z`, normal and optimized Python independently replayed both the complete
checker and its self-test after the critical same-name theorem-weakening finding. The repaired gate
binds:

- `TwoSourceCountEventBridge.lean` SHA-256
  `c0c92e4f9974b2770b3033a6ebca1d16939417707301aac4531a102649b7a16c`; and
- `PidFiniteConvergenceSemanticContract.lean` SHA-256
  `c1c8e21280c887667225d4837da341fefd42b031731d2fc334e0f3d178c80b0c`.

The semantic contract keeps 16 examples while adding empirical-law nonnegativity to its final
universal example. The new static control replaces the valid theorem
`empirical_law_nonnegative` with a same-name tautology; the exact declaration inventory still
matches, but the whole-bridge digest rejects the weakened source for its intended reason.

Both normal and optimized self-test runs reported:

```text
OK: Lean finite-convergence gate self-test killed all 10 static source mutations and all 5 isolated Lean semantic mutations for their intended reasons; kernel decide remains required and the observed native evaluator axiom was PidFiniteConvergence.SemanticScratch.binary_key_univ_eq._native.native_decide.ax_1_1
```

In that recorded output, expected-message matching mechanically bound the ten static failures. For
each isolated Lean mutation, the harness required a compiling unmodified baseline followed by
nonzero Lean status and an error diagnostic; it did not bind a theorem-specific diagnostic. A
fresh-source audit located the current first failures in `sx_pid2_node_collection_semantics`
(source swap, redundancy-to-joint, and joint-to-marginal),
`sx_pid2_redundancy_target_restricted_event_eq_union` (target erasure), and
`positive_mass_support_empirical_law` (support weakening). The current checker output uses the
narrower mechanical wording.

Both complete checker runs reported the unchanged 9-source, 263-declaration, 201-named-theorem,
7-module inventory and explicitly confirmed both SHA-256 bindings. This follow-up is a new replay;
it does not alter the quoted July 25 process output above.

## Additional hygiene

- Python byte compilation passed for both checker scripts.
- `git diff --check` passed on all modified tracked phase-A files.
- No trailing whitespace was found in the new Lean module or claim packet.
- No executable Lean source contained the `native_decide` token.
- The bridge inventory is exactly 38 declarations, including 24 theorems.
- The semantic contract contains 16 examples: the prior 10 plus 6 count/event examples.

The repository-wide Markdown-math checker was also sampled but remained red on pre-existing or
concurrent findings in `KNOWN_LIMITATIONS.md` and `claims/KSG-INTEGER-HARMONIC-001/`. No finding
named a file in this claim packet. Those unrelated files were not changed here.

## Five-lens disposition

| Lens | Phase-A disposition |
|---|---|
| Mathematical | Exact event unions, inclusion-exclusion, singleton joint event, positivity, log algebra, and averaging chain close for all four fixed nodes. |
| Formal | All 201 source theorems pass the permitted assumption audit; semantic examples use kernel reduction. |
| Fault injection | Four distinct asymmetric arguments and 14 then-current named mutations exercise the shared node/event/support cut. |
| Implementation boundary | Rust, bytes-to-counts, floating point, parser, certifier, resource, and atom-refinement edges remain explicit and open. |
| Reproducibility | Pinned checker and mutation commands are retained and rerunnable; commit/content identity awaits phase B. |

The follow-up source-custody repair preserves the theorem inventory and all 16 example slots. It
changes the current semantic-contract digest, adds whole-bridge SHA-256 custody, and adds the
same-name weakening to the static registry. Current counts and digests are authoritative in the
checker, `decision-v2.md`, and `evidence-matrix.md`; the transcript above remains historical.
