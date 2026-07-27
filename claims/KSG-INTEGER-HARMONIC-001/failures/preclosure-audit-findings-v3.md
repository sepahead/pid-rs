# Revision-3 pre-closure audit findings

## Classification

**Result: NO-GO for revision-3 completion; retained negative assurance result.**

Revision 3 was frozen before its evidence matrix or decision existed. Hostile review then found
that its arithmetic core was supported but several completion and custody statements were not yet
true. The frozen revision-3 files are not edited to conceal that chronology. Revision 4 must close
or explicitly weaken every item below.

## Findings

1. **No claim-packet custody route.** The KSG checker recognized evidence-path strings but did not
   hash or semantically validate the revision-3 claim, obligations, routes, formal boundary,
   implementation note, correction ledger, or failures. Deleting or changing those files could
   leave the arithmetic, catalog, and release routes green.
2. **Stale revision index.** `revision-index.md` named revision 2 as active and contained no
   revision-3 hashes. Git retention alone did not satisfy revision 3's stronger D1 wording.
3. **Formal bound overstatement.** The revision-3 prose attributed the exact `-D <= T <= D` bound
   to formal routes, while the frozen Lean source proved algebra/index consequences but no
   harmonic monotonicity or bound theorem, and the three Z3 files had no premises sufficient to
   derive harmonic-value bounds.
4. **Historical Lean custody gap.** The only live untracked Lean path was edited after a
   revision-2 document had pinned its earlier SHA-256. Until identical revision-2 bytes were
   retained separately, Git history did not preserve the pinned source.
5. **Mutation inventory drift.** The retained first result was 85 mutations, followed by observed
   91, 99, 129, and 133-state runs while routes were still moving. None was a final revision-3
   inventory, and no final result may be selected retrospectively from those runs.
6. **Ambiguous W3 wording.** The 150/354 ordinary-left nonzero observation uses the selected
   Neumaier prefix table. With a naive prefix the corresponding count is 121/354. An unqualified
   “ordinary left association” therefore failed to identify the prefix path.
7. **Endpoint split was trusted by consumers.** The generator recomputed the 240 exhaustive and
   114 stress endpoint rows, but the Python checker and Rust corpus test initially asserted split
   metadata rather than deriving both counts from fixture rows.
8. **Ordered W1 production gap.** The external integration test independently derived row 5's
   ordered counts `(4,1)`, but the public local scalar is source-symmetric. No production-private
   diagnostic assertion initially proved that the implementation itself produced that order.
9. **Release/catalog projections were incomplete.** Revision fields were checked, but unrelated
   fields in affected release objects, top-level release metadata, protected catalog methods,
   catalog references, and catalog metadata were not all exact negative controls. The 20 catalog
   bindings were also hard-coded without deriving the 21-node reverse dependency closure and its
   single non-numerical shared-config exclusion.
10. **Evidence-path existence was not enforced.** Catalog validation required path strings but did
    not require their targets to be regular repository files.
11. **KSG-only phase isolation was not machine enforced.** The ambient worktree also contained
    later PID2 exact-sum and I_min work. A green KSG source route did not prove that a proposed Git
    tree excluded those changes, including unrelated hunks in shared `stats.rs` and parallel-oracle
    files.
12. **Audience evidence remained stale.** Generated `METHODS.md`, release-scope Markdown,
    review-evidence records, dispositions, assurance registry, and software-identity hashes still
    referred to earlier KSG evidence or pre-migration bytes.

## Required revision-4 response

Revision 4 must preserve this failure, retain the exact historical Lean bytes, prove only the
formal statements actually encoded (including any rational-to-real bridge it claims), add
hash-first and semantic claim custody with hash-rebased semantic mutants, recompute endpoint split
counts in both consumers, bind ordered W1 diagnostics in production, freeze the selected-prefix
150/354 result in executable routes, use full-object release/catalog projections and derived
dependency closure, require evidence targets to exist, and validate an isolated Git candidate
derived from the declared parent. Generated audience and identity artifacts must be rebuilt only
after every writer has settled.

No item here changes the KSG estimator definition or the Makkeh--Gutknecht--Wibral PID functional.
This is a correction to pid-rs evidence and release claims.
