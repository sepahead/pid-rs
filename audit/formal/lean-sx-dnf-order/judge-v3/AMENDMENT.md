# Reporting amendment after candidate compilation

Judge revision 3 retains mathematical contract revision 2. It corrects an elaboration error in
thirteen reporting statements. The candidate already existed and compiled before the correction.
This is an after-candidate judge amendment. It is not pre-candidate registration, an independent
candidate proposal, or external custody.

The predecessor freeze SHA-256 is
`e4baedd90547d230e18bcfee1867d54e9697238f44ff306cbbd2529bc34b1d05`.
The candidate SHA-256 is
`76298a9baaad74f831b5254ccdeb5eeda019ac67769df9fabf2a317694fc4a65`.
The contract SHA-256 remains
`569bf11314d02ff599309bfcfa0d80109bf0f121032d5d665e8519513219a5c0`.
The candidate author's failed full-run receipt is
`74d9aec375c5dd8919c541ab47c547803b4228dd2e62751ac4066062b9bda676`.
The coordinator's independent original-judge failure receipt is
`f14e29462e063ecc5f1e07a6128ffc6f3df48e1333b5031741505a07ad315d30`.
Both attempts remain terminal failures and count against the unchanged campaign.

`SemanticJudge.lean` opened `Lean.Elab.Command` and used its command-specific `liftIO` inside
`liftTermElabM`. All thirteen sites produced `CommandElabM Unit`. Twelve required `TermElabM Unit`; the final
site required `TermElabM ?m.4`. The
replacement is direct `IO.println` in the same term-elaboration block, with the same structured
JSON value and prefix. Pinned Lean compiles and executes the direct action in the reporting
smoke control. No theorem was accepted by the failed reporting commands.

The seventy original controls did not compile that complete reporting path. Their positive
type fixtures discarded results and used `pure ()`. A small reporting smoke fixture could
have detected the error before a candidate existed. Preserve this coverage gap as negative
evidence. The old control results retain their original bounded meaning.

The verifier and coordinator wrote initial amendment recommendations before reading each
other's conclusions. Both retained the mathematical predicates and proposed a separate,
truthful successor. The verifier authored the original judge, so this review does not establish
external independence. The initial verifier recommendation SHA-256 is
`f6379c20dd24e0f285e01f4759237fdfdf3dbc25cc6acacf71fae1a0ddf8a8a9`.
The initial records and the original frozen judge remain in the local evidence archive.

Seven Lean files other than `SemanticJudge.lean`, plus the theorem roster, remain byte-identical
to revision 2. In `judge.py`, only the version label and amendment-freeze metadata enforcement
change. The semantic type checker, allowed axiom set, candidate source policy, strict evidence
parser, source pins, copied module roster, process controls, and fresh-kernel command remain
unchanged. Documentation, the mutation roster, and self-test status labels now describe the
actual chronology. The self-test retains all seventy prior controls, adds two reporting controls,
and rejects three invalid amendment identities. The positive control closure also includes the
reporting smoke module.

`reporting-regression.py` is a separate direct compiler control. After a bound complete positive
run, it restores all thirteen original reporting calls and verifies the original semantic-module
hash. It requires the thirteen observed monad mismatches, including the twelve concrete Unit
expectations and the final term-result metavariable. Complete selected and cosmetic candidate runs
must emit thirteen actual records and pass fresh kernel replay in normal and optimized modes.
No complete candidate replay occurs before coordinator adoption of the successor freeze.

The original campaign deadline is 08:32:36 UTC on 2026-09-05. Its limits remain 64 development
compilations and eight full wrapper runs. The two old full-run failures remain consumed. The
worker uses full runs 3 and 4 for the selected candidate, then 5 and 6 for the declared cosmetic
variant. The coordinator uses runs 7 and 8 for selected-candidate acceptance. Direct reporting
compilations are recorded as regression controls. No resource or scientific claim expands.
