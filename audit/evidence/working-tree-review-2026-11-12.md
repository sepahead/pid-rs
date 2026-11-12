# Working-tree and advisory-archive review, 12 November 2026

This is a bounded operational review, not a scientific acceptance decision. It records the
disposition of the retained primary checkout and six historical advisory texts. NCP, ignored
research stores, other agents' workspaces, caches and whole-worktree retirement are excluded.
Machine-specific recovery locations and the complete path inventory remain in ignored local
records.

## Observed state and preservation

Remote `main` was queried directly and resolved to
`802ed56dbaf44b7a0037fa8337065c1d55f6e2f1`; the clean current integration matched it. The
retained primary checkout remained on `review/sx-count-event-bridge-r2` at
`9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56`, with 69 modified and 157 untracked files and no
staged changes. All 226 paths, totalling 10,775,832 bytes, exactly matched preservation commit
`d1d80f0a11dcdfaefb0de035e3ba410939005a77`, including Git mode. This was checked before the
separate navigation update described in the local handoff.

The existing 11,576,201-byte bundle has SHA-256
`0fea9885c8ca51d2667874f4fc135db251cb17234bbb323576f23108d29ccad4`.
Its verification passed. An isolated bare recovery store explicitly fetched the advertised
preservation ref; all 226 blob preimages were then retrieved and compared by length and SHA-256.
The first ordinary bare-clone command reported an empty repository because the bundle advertised
only a custom preservation ref, with no branch heads. That diagnostic is retained locally; the
explicit-ref retrieval supplied the actual successful recovery check.

| Comparison with current main's tree, by exact bytes and mode | Paths |
|---|---:|
| Same path, exact | 48 |
| Exact nonempty payload at a different path | 17 |
| Different bytes at the same path | 103 |
| Absent, including an empty capture with no meaningful successor | 58 |

The relocations comprise five advisory prompts, eleven numerical witnesses and the pre-v4 KSG
revision index. An unrelated empty file is not a recovery successor for an empty stderr capture.
Only 73 exact blobs from the 226-path inventory were found reachable through current main's
history. The preservation ref, bundle and recovery drill supply local recovery, not off-host
custody, accepted-mainline status for every old byte, or authority to delete the primary tree.

All 30 July advisory artifacts were additionally copied into an inert ignored local archive,
with exact byte/mode readback and a per-file manifest. Its 25 withheld companions retain their
existing privacy and rights boundary. The existing public hash observations do not supply their
preimages. Originals remain available in the retained checkout and preservation snapshot.

## Dispositions

The numerical review found no missing production fix to port from the old working tree. All 23
changed or untracked crate paths have current counterparts; four are exact and nineteen have
later versions. The old exact reducer has a current successor in `exact_binary64.rs`; the PID2
represented-coordinate revision-4 assurance and the current numerical-boundary tests supersede
the old claim/checker paths. The eleven useful failure/correction witnesses remain byte-exact in
the [numerical history archive](../archive/numerical-claim-history-20260725/DISPOSITION.md).
This is a bounded source comparison, not a proof of all numerical behavior.

The [new advisory archive](../archive/advisory-review-history-20260724-20260725/DISPOSITION.md)
preserves six unconsumed historical texts, including an unresolved prompt/receipt digest mismatch.
Its index records original paths and exact identities. Old model suggestions remain advisory.

The filename `active-plan` does not make a file current. The August program plan, July goal prompt
and completion plan stay at their existing paths because retained lifecycle/freeze consumers bind
them. Current AGENTS and claim indices already mark those lifecycles as historical. Current claim
decisions, negative controls and formal receipts keep their authority within their stated scope;
age alone does not make them obsolete. In particular, KSG revision 4's integration NO-GO, exact
C12's terminal outcome, the formal-integrity hold and the five open SxPID3 programs remain.

## Routes and independent-first review

Three separate initial model reviews examined preservation, archival coupling and numerical
successors before cross-member discussion. They shared repository sources, Git and tools, so
their conclusions are correlated advisory observations, not independent human or institutional
review. The primary reviewer independently checked the exact preservation inventory, recovered
the bundle payload, inspected the archive inputs and retained the receipt mismatch.

| Route | Decision, assumption and reconsideration condition |
|---|---|
| No action | Preserves the tree but leaves stale intake clutter; fallback if byte or ownership checks fail. |
| Inventory only | Simplest non-PID route; necessary evidence, but does not organize the advisory files. |
| Delete older advisories | Rejected: useful questions and failed-attempt evidence remain. Only separately disposable material could qualify. |
| Bulk merge the retained tree | Rejected: would reintroduce superseded claims and implementations. |
| Move every old evidence document | Rejected: current authority and hash-bound history have path consumers. |
| Rewrite old prompts as current guidance | Rejected: destroys the historical questions; use separate current guidance. |
| Archive six unconsumed texts together | Selected: exact, reversible preservation with a narrow reference surface. Stop if a live consumer is found. |
| Publish withheld companions | Rejected: the existing privacy/rights disposition remains unresolved. |
| Make private exact advisory copies | Selected: clearer local recovery without public disclosure; no off-host credit. |
| Refresh navigation and source-state | Selected after preserving preimages; present observations stay distinct from history. |

Fifty review lenses were applied as a coverage checklist, with the following concrete
dispositions. Their count is not proof or an independence claim.

| Lenses | Disposition |
|---|---|
| Source revision; Git blob; raw bytes; length; digest; mode; original path; successor path; historical date; review class | Exact identities retained; historical review status is not promoted. |
| Runtime imports; scripts; CI; claim paths; catalog; assurance registry; release scope; freeze hashes; PDF builders; intra-packet references | Archive only the six texts with no discovered active consumer beyond source-state and packet peers. |
| Tracked/index separation; untracked coverage; ignored coverage; bundle scope; recovery retrieval; main-history reachability; empty-file ambiguity; negative evidence; withheld preimages; off-host custody | Recover the declared 226-path scope; leave ignored coverage, off-host custody and retirement open. |
| MGW identity; Ehrlich identity; Williams–Beer identity; KSG identity; exact-real scope; binary64 scope; population premises; calibration; application value; novelty | Make no scientific change or transfer; retain current decisions and open obligations. |
| Writer ownership; NCP exclusion; dirty-tree preservation; private/public separation; existing rights boundary; relative links; README placement; source-state; post-commit identity; rollback | Use the clean pid-rs integration for the bounded archive; preserve the primary tree and other projects. |

## Validation scope

Applicable checks are exact archive/preimage and mode comparison, tracked-reference search,
publication-link checks, existing advisory and inert-archive checks and hostile suites, current
Lean operational-wiring checks, release-scope and source-state consistency, and post-commit
identity. Normal and optimized Python modes are compared where provided. The only frozen-checker
edit rebinds the current CHANGELOG digest; preserved replay maps and receipts remain unchanged.

The numerical spot checks use `check-pid2-represented-coordinate-v4.py --scope model-source` and
the no-write exact-binary64-sum oracle generator in both modes. They do not run compiled Rust,
Python wheels, solvers or proof kernels, and establish no estimator or application result.
This text-only archival milestone requires no numerical change or PDF rebuild. Exact commands
and outputs are retained in the ignored local review record; final completion requires the
applicable checks and a clean unsigned commit. No hosted result is claimed for that later commit.
