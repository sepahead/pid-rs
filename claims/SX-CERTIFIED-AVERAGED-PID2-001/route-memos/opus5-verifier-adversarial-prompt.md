# Opus 5 Max adversarial prompt: independent SxPID2 verifier

Claim ID: `SX-CERTIFIED-AVERAGED-PID2-001`

Role: read-only adversarial reviewer. Try to refute, narrow, or repair the executable-assurance
claim. Do not edit files. Do not treat passing tests, polished prose, another implementation's
agreement, or any model review as proof. You have no tools and must reason only from the supplied
snapshot.

The narrow claim under review is:

> Let $B$ be accepted count-table bytes, let $X=\mathrm{normalize}(B)$ be their canonical
> exact count-table semantics, and let $C$ be a producer certificate accepted for $B$. The
> independent Python verifier reconstructs all 24 averaged informative, misinformative, and net
> cumulative and atom expressions of the pinned two-source categorical SxPID definition from
> $X$. It independently encloses each exact rational-log expression in $J_j$ and accepts only
> when $J_j\subseteq I_j(C)$. Conditional on the explicitly stated verifier trusted computing
> base, a `verified` result establishes $F_j(X)\in I_j(C)$ for all 24 coordinates. It does not
> refine `pid-core` binary64, establish population or statistical validity, cover pointwise,
> higher-source, or continuous PID, or certify downstream decisions.

Attack from first principles:

1. Re-derive the Makkeh--Gutknecht--Wibral two-source source-event and target-restricted event
   semantics, count weighting, informative/misinformative signs, fixed antichain order, Möbius
   inversion, zeta reconstruction, and direct-MI identities. Look for a producer/verifier shared
   transcription error.
2. Re-derive range reduction, the separate $\log 2$ base case, uniform-convergence step,
   atanh-series identity, tail bound, fixed-point power recurrence, every floor/ceiling operation,
   negative-coefficient endpoint swap, finite accumulation, and subset predicate. Seek a minimal
   inward-rounding counterexample.
3. Attack the accepted byte grammar and normalization: duplicate keys, unknown keys, JSON numeric
   constants/floats, booleans, decimal strings, Unicode and surrogates, key order, whitespace,
   row ordering, state widths, integer limits, exact-expression normalization, and ambiguous
   multiple encodings.
4. Attack resource accounting and denial-of-service closure, including work done before each
   bound, Python integer conversion limits, dyadic exponent shifts, report integer strings,
   term explosions, payload canonicalization, source reads, and retry schedules.
5. Attack source/manifest/Cargo/build-host bindings, file identity checks, post-import drift,
   TOCTOU windows, symlinks, loader/source mismatch, compiled-byte mismatch, and every provenance
   or custody sentence. Distinguish parsed endpoint values from endpoint-generation correctness.
6. Attack the qualification harness. Find source or certificate mutations that pass for the wrong
   reason, correlated producer/verifier logic, weak oracle comparisons, incorrect mutation-count
   claims, or evidence that is described more broadly than it supports.
7. Classify each step as analytic proof under premises, executable proof under trusted runtime
   semantics, bounded exhaustive evidence, mutation sensitivity, bibliographic premise, or prose
   only. Reject evidence substitution.
8. Audit the assurance TeX and claim packet for internal contradictions, undefined symbols,
   unproved claims, stale/future-state language, and any statement a mathematically literate
   newcomer could misread.

For every concrete finding, report:

- severity (`critical`, `high`, `medium`, or `low`);
- confidence from 0 to 1;
- exact supplied file and line or uniquely identifying text;
- a minimal counterexample or failure mode;
- the smallest safe correction;
- one regression or mutation that must fail before and pass after;
- whether it generalizes beyond the retained corpus; and
- whether it changes the narrow claim, its evidence label, or only its documentation.

Report all positive and negative findings with confidence at least 0.80. A positive finding must
name the exact argument independently re-derived; it must not be generic praise. If no qualifying
flaw exists, say so and name the five largest residual trusted assumptions. Do not reveal or
request private chain-of-thought; provide concise derivations and checkable conclusions only.

End with exactly one disposition:
`block`, `approve_with_fixes`, or `approve_narrow_claim`.

State `claude-opus-5`, effort `max`, and review date `2026-07-24` in the response.
