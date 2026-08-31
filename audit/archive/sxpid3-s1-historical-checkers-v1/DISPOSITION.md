# SxPID3 S1 historical checker archive disposition

Status: **inert historical checker sources; non-authoritative negative evidence**.

This directory preserves the exact source bytes of two superseded SxPID3 S1
correspondence checkers and the exact revision-3 false-green record from source snapshot
`dfdfd0b5c46b765338cc66a27973524d531b3388` (tree
`8636722bce447e972817b5349849049b7e16961e`). The exact checker bytes resolve
through the integration snapshot's archive paths. That snapshot records v1 under
historical commit `92f6c2e633eed756b3e11c84ac19e51248e8cc90` and v2 under historical commit
`94c9983ad6f0fa0bd1bf8e6c054165001db4adda`. Those older commit/tree strings are
retained as historical metadata; this packet does not claim an independent resolution
of those older objects.

The revision-3 record carries seven historical mutation recipes: five for v1 and two
remaining alternate-`--source-record` false greens for v2. Each has normal and
optimized stdout-digest observations, for fourteen observations in total. These are
checker counterexamples, not mathematical counterexamples. The archive retains the
vulnerable source bytes and the record as inert engineering evidence, but does not
execute them and does not fill S1, H1, or any review route.

The same source snapshot contains a revision-3 pending-only protocol. Its own exact
decision is **S1 NO-GO/open**, **H1 open**, and **Programs A--E closed: 0 of 5**.
Only its false-green record is copied, under a `.json.txt` data filename, to preserve
the mutation recipes and output digests. Candidate source-map, protocol, and positive
claim fields necessarily remain inside those exact frozen bytes, but none is adopted
as current evidence or authority. The separate revision-3 schema, checker,
self-test, and review protocol are not copied or promoted into the active claim
surface. They remain an unaccepted open packet. Statements and paths embedded in the
historical record
describe its old snapshot and do not become current facts merely because the bytes are
retained. `INDEX.json` binds the copied record and the four excluded companions to the
named source snapshot. No part of this custody action may be read as acceptance.

Run only the archive-integrity check:

```text
python3 -I -S -B scripts/check-inert-negative-archives.py
python3 -O -I -S -B scripts/check-inert-negative-archives.py
```

The check validates exact payload bytes, source bindings, and Python syntax; it does
not replay the historical false greens or parse the copied record as current review
authority. The archive establishes neither source correspondence nor
review independence, authorship, chronology, custody, Rust refinement, estimator
validity, or a defect in Makkeh--Gutknecht--Wibral shared exclusions.

This directory deliberately has no `README.md`: it is an evidence archive, not a
published package, directly consumed command, or browsed-asset directory.
