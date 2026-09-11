# Retained negative results from the finite target-copy MGW proof

This archive records failed development routes for the finite categorical target-copy
construction of Makkeh, Gutknecht, and Wibral. It is an inert research record. The Lean files
listed here are not imported by the accepted source graph, and a failed candidate proof is not
evidence that the mathematical proposition is false.

The accepted scope is the finite law $S_1\in A$, $S_2\in C$, $U\in B$, $T=(S_1,U)$, with a
normalized nonnegative law on finite alphabets and the target-copy condition on every positive
key. The target-copy identities and bounds are documented in
[the accepted theorem note](../../evidence/finite-target-copy-mgw-synergy.md).

## Route dispositions

| Route | Observed failure | Correction or disposition |
|---|---|---|
| Namespace-shadowing L1-L4 attempt | The candidate was elaborated before the required interface namespace was available. The registered run exited nonzero before a theorem result. | Closed as a setup failure. It does not test the MGW statement. |
| Original finite-push L1 layout | The first L1 layout failed on a finite push type/injectivity obligation. | Replaced by the accepted L1 construction with an explicit finite bridge. |
| Original L2 membership proof | The first L2 layout confused `Finset` membership with the required logical equivalence. | Replaced by an explicit membership bridge. |
| Original L5 identities proof | The first L5 source exited with four identity errors. Its outer process observation was incomplete. | Repaired in the accepted explicit-decider L5 source; the incomplete observation remains incomplete. |
| First L5 filter repair | The first filter repair still produced four errors. | Closed after the diagnostic below identified the cause. |
| L5 expanded diagnostic | A private helper used `Classical.propDecidable` while the expected filtered equality used a supplied `DecidableEq`. The propositions agreed, but the proof terms did not reduce under the attempted simplifier. | Added an explicit `[DecidablePred p]` helper and two `Finset.mem_filter` rewrites. The accepted source proves the intended proposition without weakening its type or premises. |

## What the failures do and do not show

The failures identify elaboration, representation, and decider-alignment problems in candidate
proofs. They do not refute the finite MGW identities, the OR-across-collections and
AND-within-collection event semantics, the entropy bounds, or source-law invariance. The final
correction preserves the original alphabets, quantifiers, premises, imported definitions, and
target statements.

The expanded diagnostic is load-bearing negative evidence because it distinguishes a proof-term
decidability mismatch from a false proposition. Changing a decider or adding a rewrite can repair
elaboration. Changing a quantifier, support premise, event connective, or target type would change
the scientific claim.

## Custody and redaction

Exact failed source bytes, registrations, command streams, and decisive outputs remain in ignored
local custody recorded by the session handoff. Some raw diagnostics contain machine-specific
absolute paths, so this public projection records hashes and dispositions without publishing those
paths. The archive contains no executable candidate payload and is not part of any Lean import
path. Reconsideration requires a new registered task packet and a new review; it must not revive an
old candidate lifecycle.

The accepted fresh replay passed 17 exact source compilations and one same-kernel replay. That
result gives no credit to a failed candidate and does not make the replay independent-kernel
verification.
