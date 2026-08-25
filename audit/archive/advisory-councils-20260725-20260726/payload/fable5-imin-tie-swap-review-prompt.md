# Fable 5 Max adversarial review: `IMIN-TIE-SWAP-001`

You are an external read-only mathematical/numerical/software reviewer. State that the model is
`claude-fable-5`, effort `max`, and the review date is 2026-07-25. Do not edit files, commit, push,
or treat agreement with another model as evidence.

The repository is `/Users/torusprime/Development/sepahead-github/pid-rs`. Its frozen intake commit
for this claim is `ca2eaf31ce7b719d04a43e0d6e1d2c21c6ff06a7`; the worktree now contains concurrent uncommitted
completion-run changes, so distinguish frozen-source observations from live-worktree observations.

Read completely:

- `AGENTS.md`;
- `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md`;
- every file under `claims/IMIN-TIE-SWAP-001/`;
- the relevant implementation in `crates/pid-core/src/discrete_pid.rs`;
- the fixed-size exact binary64 accumulator and its callers in `crates/pid-core/src/pid2.rs`;
- relevant tests, method-catalog/release-scope entries, and public/Python result shapes.

The new packet separates an exact target-specific `I_min` tie from a different public source-swap
defect in left-associated synergy reconstruction. Attack the packet rather than accepting it.

Required review:

1. Re-derive or refute both retained counterexamples, including exact rational-log algebra,
   binary64 hex values, source-swap field mapping, and dependency reach.
2. Audit the declared exhaustive domain of 12,869 binary count tables through total eight, its tie
   and source-swap counts, minimality/orbit claims, and what it cannot establish.
3. Decide whether always computing synergy as the correctly rounded exact sum of the four
   represented finite binary64 terms `J - I1 - I2 + Red` is the strongest justified repair. Inspect
   the existing accumulator algorithm for finite/subnormal/signed-zero/ties-to-even/overflow and
   permutation behavior. Identify any proof or executable gaps. Compare at least two genuinely
   different alternatives, not mere reassociations.
4. Analyze the three identities `Red+U1=I1`, `Red+U2=I2`, and
   `Red+U1+U2+Syn=J` under separately rounded returned atoms. State precisely what exact summation
   can and cannot guarantee for arbitrary consumer grouping and whether a report/abstention design
   would be scientifically preferable.
5. Inspect the currently total but `unwrap_or(0.0)` target-map fallbacks. Decide how they should
   fail closed without changing valid results or creating an unbounded resource path.
6. Design a complete, discriminating regression/property/mutation suite: both witnesses, exact
   corpus cardinality, source/relabel permutations, exact tie orbits, genuine tiny nonzero atoms,
   ordinary/release/parallel/Python/wrapper paths, and mutations that cannot pass on a dead
   baseline. Reject tolerance-only tests that would allow clamping.
7. Identify every estimator/method/release/software identity and documentation boundary that must
   move if output bits change. Do not call a version pin semantic compatibility.
8. Give a GO / NO-GO / conditional decision with an obligation graph, minimal critical cut sets,
   strongest honest wording, residual boundaries, and at least ten adversarial failure scenarios.

Use semantic, exact-mathematical, numerical-analysis, formal/algorithmic, executable, statistical,
provenance, and downstream-authority lenses. Model prose is advisory only; cite exact file paths,
line ranges, formulas, executable commands, and small witnesses that the coordinator can replay.
