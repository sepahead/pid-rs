# Lean exact-log checker archive adjudication, revision 1

Status: **negative result retained; archived production rewrite rejected; hostile-test ideas
rewritten against the current frozen checker**.

- Date: 2026-08-30
- Current baseline: `855605a2a2098fa82fccb07521bae5cc382fa747`
- Archived draft: `archive/exact-log-product-verifier-draft-20260828`, commit `6077443`
- Archived checker SHA-256: `a02486dfec8550e6cf6a85f3afea68fbdb8a44d71b3d890ed06e86033b73b905`
- Archived self-test SHA-256: `76b183e5460102002cb117c5fa322fbb17787bab1e377e78cc86e164304643ba`
- Retained production checker SHA-256:
  `52510a18ac5fa8b94113bfeba84f61cb28bdbe56be278fc76fb4d55407cb2dcd`

## Decision

Do not cherry-pick the archived checker rewrite. Retain the current production checker byte for
byte. Add a new isolated hostile suite that tests the current checker's actual contract, records
accepted scope probes as scope probes rather than mutation kills, and preserves the current raw
proof-escape policy.

This decision does not change a Lean theorem. The seven current theorem declarations still compile
under the pinned Lean 4.33.0/Mathlib project, and their queried axiom inventories still contain only
`propext`, `Classical.choice`, and `Quot.sound`. The failure is in an archived Python lexical guard
and declaration-inventory claim. It is not evidence against the proved algebra.

## Reproduced counterexample

The archived draft tried to remove comments and strings with a handwritten scanner before it
searched for `sorry`, `admit`, `axiom`, or `unsafe`. Lean character literals were not in that
scanner's model. Appending the following valid Lean fragment before the namespace end creates a
live unqueried axiom:

```lean
def quoteCharOne : Char := '"'
axiom unexpected_unqueried_axiom : False
def emptyString : String := ""
def quoteCharTwo : Char := '"'
```

The complete mutated Lean source is 5,492 bytes with SHA-256
`891323ef49a0a9e2bf8f4306de1301301aa961886121329dcf9b11847d823e03`. After a deliberate
test-only source-digest rebind, the archived checker returned success. The retained production
checker rejects the same bytes because its raw token search sees `axiom`. Nothing in the production
path rebinds the immutable source digest.

The archived exact declaration regular expression also omitted an unrelated added `lemma` and an
unrelated added `private theorem`. Both compile and leave the seven queried theorem results
unchanged after a test-only digest rebind. This shows the named query's scope. It does not create a
production bypass while the production source digest is fixed.

## Salvage and rejection matrix

| Archived change | Decision | Reason | Replacement |
|---|---|---|---|
| Handwritten comment/string masker | Reject | The character-literal witness makes a live axiom invisible. A partial lexer is unsafe as an acceptance broadener. | Keep raw-token rejection. |
| Raw comments/strings become acceptable | Reject | This weakens the current fail-closed policy and is unnecessary for the frozen source. | Comments and strings containing proof-escape words remain rejected controls. |
| Exact declaration regular expression | Reject | It misses valid declaration forms, including `lemma` and `private theorem`. | Treat extra declarations as explicit digest-rebound scope probes; rely on exact source custody in production. |
| Checker-side theorem inventory equality check | Reject in this form | A second mutable list in the same Python process does not provide independent custody. | Pin exact checker bytes in the hostile loader and retain a shortened-list limitation probe. |
| Nine semantic Lean mutations | Salvage | Each mutation reaches Lean or the named axiom audit only after a deliberate test-only digest rebind. | Reimplement against the captured current checker and count only actual rejections. |
| Checker-inventory mutation counted as a kill | Reject as credit | The current checker accepts a shortened in-memory theorem list; that is a custody boundary, not a killed mutation. | Record one accepted known limitation, with no mutation credit. |
| Nested-comment/string decoy accepted | Reject as desired behavior | Acceptance requires the flawed lexical broadening and gives no theorem benefit. | Retain it as an expected raw-policy rejection. |
| Ordinary and optimized execution | Salvage and strengthen | Python optimization must not remove a control. | Require exact `-I -S -B`, permit only normal or one `-O`, and compare canonical outputs. |
| Temporary mutated Lean files | Salvage | They isolate hostile inputs from the tracked theorem source. | Use a private temporary directory and recheck tracked bytes after replay. |
| Production checker edits | Reject for this milestone | The current checker is already source-digest closed and has the safer raw rule. | Keep `check-lean-exact-log-product.py` byte-identical. |
| Archived self-test as a whole | Reject | Its pass result depends on the unsafe production rewrite and its accounting overstates inventory credit. | Replace it with the version-1 isolated hostile suite. |

## Alternatives considered

1. **Do nothing.** Safe for theorem acceptance, but it loses the archived failure and adds no
   regression for the character-literal witness.
2. **Cherry-pick the archive unchanged.** Rejected because it broadens acceptance through an
   incomplete lexer.
3. **Patch the handwritten lexer for `Char`.** Rejected because Lean lexical syntax, escapes,
   quotations, and future syntax extensions make repeated partial repairs fragile.
4. **Use another regular expression for declarations.** Rejected because modifiers, commands,
   generated declarations, namespaces, and future syntax still defeat an ad hoc grammar.
5. **Adopt a third-party Lean parser.** Deferred: it adds a dependency and parser-version custody
   problem and is unnecessary for this immutable source.
6. **Inspect Lean elaborator information trees for every declaration.** Promising for a future
   versioned registry, but it changes the proof project's evidence protocol and needs its own
   adversarial qualification.
7. **Enumerate all environment constants and query all axiom dependencies.** Stronger in scope but
   requires a precise admitted-declaration policy for Mathlib imports and generated helpers.
8. **Move the checker to Rust.** It can improve file and process custody, but it does not remove the
   need for Lean-aware declaration semantics and is disproportionate for this milestone.
9. **Generate a fixed Lean query wrapper and hash it.** Useful future hardening, but it still needs
   an authenticated theorem registry and does not justify accepting comments or strings now.
10. **Keep the current checker and add an isolated byte-bound hostile harness.** Selected. It adds
    evidence without weakening acceptance or changing theorem bytes.
11. **Replace the current checker with only the hostile harness.** Rejected: a self-test cannot
    substitute for the production Lean run.
12. **Treat exact source SHA-256 as complete proof.** Rejected: the digest closes source drift only;
    it does not establish theorem truth, checker correctness, or application validity.

## Thirty-five hostile review lenses

| # | Lens | Finding |
|---:|---|---|
| 1 | Scientific object | The object is generic finite log/product/sign algebra, not a PID estimator. |
| 2 | Semantic transfer | No result is transferred from lexer behavior to theorem truth. |
| 3 | Lean kernel | Kernel checking remains the positive proof authority for the seven declarations. |
| 4 | Lean lexical syntax | A handwritten subset is not a complete Lean lexer. |
| 5 | Character literals | The archive failed on quote-valued `Char` literals. |
| 6 | String literals | Strings can change a partial scanner's state without changing Lean command scope. |
| 7 | Nested comments | Supporting one nested-comment pattern does not qualify all lexical forms. |
| 8 | Line comments | Comment removal can only be trusted with a complete grammar or conservative rejection. |
| 9 | Escapes | Escape rules are a future counterexample surface for partial scanners. |
| 10 | Raw-policy strength | The retained raw scan rejects more inputs and therefore does not weaken acceptance. |
| 11 | Source custody | Exact production source SHA-256 rejects every tested added declaration before Lean. |
| 12 | Checker custody | Exact captured checker SHA-256 is required before the hostile harness executes it. |
| 13 | Theorem inventory | Only seven qualified names are queried. |
| 14 | Extra lemma | A rebound extra lemma is outside that named query and is recorded as scope. |
| 15 | Private theorem | A rebound private theorem is likewise outside the query. |
| 16 | Live extra axiom | Raw policy rejects the character-literal/live-axiom witness. |
| 17 | Permitted axioms | The expected list remains exact and ordered. |
| 18 | Test-only rebinding | Digest rebinding exists only inside the hostile process and is restored after each case. |
| 19 | Production rebinding | CI invokes the immutable production constants with no rebind option. |
| 20 | Positive controls | Baseline and two declared scope acceptances are counted separately from rejections. |
| 21 | Mutation credit | Only nine semantic rejections receive mutation-kill credit. |
| 22 | Raw/digest credit | Six policy cases are a separate category, not theorem-mutation credit. |
| 23 | Known limitation | Shortening the in-memory theorem tuple is accepted and explicitly retained. |
| 24 | Python assertions | Normal and `-O` runs must emit the same canonical evidence. |
| 25 | Python isolation | `-I -S -B` is mandatory; no ambient site packages or bytecode cache are admitted. |
| 26 | Captured-byte execution | The loaded module is compiled from the bytes whose digest was checked. |
| 27 | File races | Descriptor double-read and repeated metadata checks bound ordinary mid-read changes. |
| 28 | Link attacks | Source and checker leaves must be single-linked regular non-symlink files. |
| 29 | Parent substitution | Lexical parent identities are checked before and after each captured read. |
| 30 | Global restoration | Source path, source digest, and theorem tuple are restored in `finally`. |
| 31 | Output transport | Status, separate stdout/stderr, final LF, duplicate keys, nonfinite values, and canonical JSON are checked. |
| 32 | CI cost | The small theorem file and bounded 19-case suite fit the existing Lean job. |
| 33 | Rust boundary | No Rust or binary64 refinement follows from the generic Lean result. |
| 34 | Statistical boundary | No population, estimator, sampling, calibration, or uncertainty statement follows. |
| 35 | Publication boundary | The archive failure is publishable engineering evidence only with the negative result and nonclaims attached. |

## Evidence and nonclaims

The machine-readable current result is
`audit/evidence/sxpid2-exact-log-product-hostile-4.33.0.json`. It binds the exact production
checker, tracked Lean source, replacement self-test, each mutant digest, accepted scope probes, and
the known limitation. Normal and optimized runs must be byte-identical.

This evidence does not prove that the Python checker is correct, that its raw token scan classifies
all Lean syntax, that SHA-256 is an authenticity mechanism, or that no concurrent filesystem attack
is possible. It does not formalize the SxPID event extractor, redundancy lattice, canonical
certificate bytes, Rust implementation, binary64 arithmetic, sampling law, estimator behavior,
calibration, or downstream use.
