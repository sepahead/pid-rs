# Correction ledger for `KSG-INTEGER-HARMONIC-001` revision 3

## C6 — revision-2 mutation count became stale

- **Observed:** revision 2 recorded 85 planned mutations; live implementation later closed six
  named gates and replayed 91.
- **Correction:** retain 85 and 91 as historical states; freeze a new final inventory only after
  KSG-only release, schema-v2, claim, and catalog routes settle.
- **Reach:** mutation adequacy and public evidence wording only; exact algebra unchanged.

## C7 — combined PID2/I_min release contamination

- **Observed:** four release strings combined KSG and PID2, and two unrelated I_min migrations were
  authorized by the KSG checker.
- **Correction:** revision 3 binds KSG-only bridge strings, protects the two I_min families, and
  requires 15 affected plus 20 protected families.
- **Reach:** release/catalog/identity and staged-commit order; no arithmetic implication.

## C8 — schema-revision-1 endpoint residuals

- **Observed:** exact structural endpoint cancellations carried 26 nonzero `1e-79`-scale Decimal
  residuals and 326 noncanonical zero spellings.
- **Correction:** schema revision 2 canonicalizes 354 structural endpoints to `"0"`, records the
  240/114 split, and retains 80-digit Decimal for nonendpoints.
- **Reach:** fixture/generator/checker/Rust custody. The 8-epsilon maximum, first maximum, 40 ties,
  and zero swap asymmetries are unchanged.

## C9 — evidence wording corrections

- `107/210` is the exact-real W1/W2 target; binary64 assertions pin the selected association.
- The KSG-only heuristic-family bridge changes through KSG MI inputs used by Python `compute_pid2`;
  it is not evidence for the later represented-input PID2 constructor correction.
- Error is absolute nats error, not ULPs; endpoint zero is selected-path positive zero, not global
  signed-zero preservation.

## Revision-preservation rule

Revisions 1 and 2, both route memos, all prior failures, and their hashes remain immutable. The
revision-3 evidence matrix and decision are created only after settled replay and then become
immutable. Any later claim, corpus, domain, release phase, or completion decision requires another
revision.
