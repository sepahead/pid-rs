# Fable 5 Max adversarial prompt: independent SxPID2 verifier

Claim ID: `SX-CERTIFIED-AVERAGED-PID2-001`

Role: read-only adversarial reviewer. Try to refute or narrow the executable-assurance claim.
Do not edit files. Do not treat passing tests, polished prose, another model's conclusion, or a
producer/checker agreement as proof.

Read only these repository paths and the directly called helpers within the same standalone tool
when essential:

- `audit/tools/certified-sxpid/scripts/verify_certificate.py`
- `audit/tools/certified-sxpid/scripts/check-independent-verifier.py`
- `audit/tools/certified-sxpid/Cargo.toml`
- `audit/tools/certified-sxpid/Cargo.lock`
- `audit/tools/certified-sxpid/src/`
- `audit/tools/certified-sxpid/README.md`
- `audit/formal/latex/certified-sxpid2-executable-assurance.tex`
- `claims/SX-CERTIFIED-AVERAGED-PID2-001/`

The narrow claim under review is:

> For one canonical exact two-source empirical count table and the pinned categorical SxPID2
> definition/lattice, the independent Python verifier reconstructs all 24 averaged
> informative/misinformative/net cumulative and atom log-linear expressions from counts and proves
> that its own rational-log enclosure is contained in every Rust producer interval. Conditional
> on the verifier's explicitly stated trusted computing base, a `verified` result establishes
> containment of those exact-real coordinates. It does not refine `pid-core` binary64, establish
> population/statistical validity, cover pointwise/higher-source/continuous PID, or certify a
> downstream decision.

Attack from first principles:

1. Re-derive the event semantics, four-node Möbius transform, direct-MI identities, and count
   weighting. Look for a shared producer/verifier transcription error.
2. Re-derive the range reduction, fixed-point outward operations, coefficient-sign handling, and
   the `9*z^(2m+1)/(4*(2m+1))` tail bound. Find any argument for which an endpoint can be inward.
3. Attack strict JSON, integer/rational parsing, canonicalization, resource accounting, duplicate
   keys, booleans-as-integers, Unicode, extreme exponents, and denial-of-service bounds.
4. Attack source/manifest/Cargo/build-host bindings, post-import drift checks, TOCTOU windows,
   symlinks, loader/source mismatch, and claim-envelope overstatement.
5. Attack the qualification harness itself. Construct minimal source or certificate mutations that
   survive for the wrong reason. Pay special attention to correlated checks and weak
   plausibility/oracle comparisons.
6. Identify what is formal proof, executable proof under trusted semantics, bounded exhaustive
   evidence, mutation sensitivity, or prose only. Reject evidence substitution.

For each concrete finding, provide:

- severity (`critical`, `high`, `medium`, or `low`);
- confidence from 0 to 1;
- exact file and line evidence;
- a minimal failure mode or counterexample;
- the smallest safe fix;
- one regression or mutation that must fail before and pass after;
- whether the issue generalizes beyond the tested input.

Report only findings with confidence at least 0.80. If no such flaw is found, say so and name the
three most important residual trusted assumptions. End with one disposition:
`block`, `approve_with_fixes`, or `approve_narrow_claim`.

State `claude-fable-5`, effort `max`, and the review date in the response.
