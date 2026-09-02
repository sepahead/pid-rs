# Post-publication custody and cleanup receipt

**Observation:** dated snapshot; phases are recorded below\
**Record:** `PPC-20260902-02`\
**Repository:** `sepahead/pid-rs`\
**Machine record:** [`post-publication-custody-2026-09-02.json`](post-publication-custody-2026-09-02.json)\
**Human PDF:** [`post-publication-custody-2026-09-02.pdf`](../../output/pdf/post-publication-custody-2026-09-02.pdf)

## Purpose and boundary

This receipt records a dated observation made after the documentation-closure commit was
published and after the named cleanup actions passed their bounded custody predicates. Here,
"mainline-published anchor" means the exact commit identified below was reachable from
`refs/heads/main` at the recorded observation; it does not mean that every ancestor is
mathematically or scientifically accepted. This record is not a live monitor. Re-observe every
ref, process, path, and bundle before a later mutation.

The identity below is the snapshot anchor for this receipt. Adding this receipt or later
documentation to `main` can create a newer commit; that does not retroactively change the
recorded observation. Treat the receipt as dated evidence with an explicit boundary, and create a
new observation when the live tip or retained state changes.

The receipt does not rewrite either dated retirement ledger. The primary ledger and the sibling
ledger remain immutable, bounded observations made on 1 September 2026 before publication and
cleanup. Their fields that say *no cleanup authority* describe those observations. They are not a
statement that cleanup never occurred later. This receipt supplies the missing later observation so
that a reader does not confuse a historical precondition with the present disposition.

The c499 closure changed documentation, workflow/checker configuration, formal-artifact routing,
and repository custody records. This follow-up adds this receipt and its presentation assets. The
cleanup operations did not alter Rust/Python estimator code, formal theorem source, test fixtures,
or numerical result bytes. Those process changes are bounded and are not scientific validation.
No claim here upgrades algebraic formalizations to probability theorems, turns a finite exhaustive
check into a population result, or validates an estimator in a new dimension.

![Post-publication custody state machine](../formal/figures/post-publication-custody/state.pdf)

The diagram is a process aid. Its colors and ordered patterns follow the repository-local ink,
lapis, turquoise, mineral-blue, bronze, and ivory publication palette. The pattern is redundant
with the labels, so the state distinction remains readable in grayscale. The SVG source is retained
beside the PDF figure for inspection and regeneration. The local figure PDF is a presentation
derivative, not a proof artifact.

## Observation phases

The first snapshot was opened at `2026-09-02T00:06:18Z`. The named cleanup and packed-ref
reconciliation actions were recorded complete at `2026-09-02T00:07:35Z`; this operator-supplied
time is not inferred from a filesystem timestamp. The final local/remote observations occurred
later. The machine record keeps separate
`observation_started_at_utc`, `actions_completed_at_utc`, and `final_observed_at_utc` fields; it
does not silently replace the initial timestamp. The final time is `2026-09-02T04:43:02Z`, the
timestamp recorded immediately before the bounded pre-follow-up remote-head query and local
checks. A later push of this receipt creates a newer `main` tip; it does not rewrite this c499
snapshot.

## Machine check and exact remote manifest

The exact remote-head preimage is retained as
[`post-publication-remote-heads-2026-09-02.tsv`](post-publication-remote-heads-2026-09-02.tsv).
Each line has one lowercase Git SHA-1 object ID, one TAB, and one `refs/heads/...` name. The
file has LF line endings and one final LF. It is a byte preimage of the direct hosted query; it
is not a live branch list.

Run this standard-library-only checker from the repository root:

```text
python3 -I -S -B scripts/check-post-publication-custody.py
python3 -O -I -S -B scripts/check-post-publication-custody.py
```

The two runs must print the same success line. The checker reads only the JSON record and the TSV;
it makes no network request, reads no local Git registry, and performs no mutation. It rejects
duplicate JSON keys, non-finite values, private absolute locators, malformed object IDs or ref
names, reordered or changed manifest bytes, mismatched digest projections, changed publication
identities, altered hosted-run census, weakened cleanup predicates, and missing retention or
nonclaim boundaries. The expected snapshot identities are repeated in the checker on purpose. A
changed observation therefore requires a reviewed checker update or a new dated receipt, rather
than silently changing the meaning of this one.

The `retired_refs_absent_from_observed_manifest` flag has a narrow meaning: the nine named
retired ref names are absent from this observed 14-line manifest. It does not prove that a ref can
never be recreated, that every copy of its objects is gone, or that a later remote query will be
identical. The
`remote_post_absence` cleanup note records the separate live query made at the time; this static
checker does not repeat that query.

## Mainline-published observation anchor

The documentation-closure commit observed on the hosted and local `main` refs was:

- Commit: `c499653e4ac89733cb35330bf1a13c93a40ee385`.
- Parent: `30e6d19bf020b18ef1cc1f9478c2d4acba62ccf1`.
- Tree: `1a1f8dc9782d2f5d6cc9c3342b5395bc7240b975`.
- GitHub `refs/heads/main`: `c499653e4ac89733cb35330bf1a13c93a40ee385`.
- Local primary `refs/heads/main`: `c499653e4ac89733cb35330bf1a13c93a40ee385`, read from the
  primary common Git directory with `git -C <primary-repository> rev-parse refs/heads/main`.
- Primary checked-out worktree: `refs/heads/review/sx-count-event-bridge-r2`.
  Its exact checked-out OID is:

  `9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56`
- Primary checked-out state: dirty and intentionally retained. It was not overwritten, reset, or
  merged into by this closure.

The distinction in the last rows is intentional. "Local `main` points to the published commit"
does not mean that the currently open primary checkout is clean or is on `main`, and the detached
receipt checkout is not evidence for the primary local ref.

After the publication and cleanup checks, the primary common Git directory had stale duplicate
values in its packed-ref file: the loose `main` and `origin/main` values were current, but the
packed file still named older values. I copied the original packed file to the durable
preservation path recorded in the JSON, then ran the narrow Git operation
`git pack-refs --all --prune`. The resulting packed file contains `main = c499653e...`,
`review/sx-count-event-bridge-r2 = 9bbcf5ef...`, and `origin/main = c499653e...`. The status
digest and checked-out OID were identical before and after. This is ref-metadata reconciliation;
it is not garbage collection and it does not alter the dirty review files.

A direct `git ls-remote --heads` query observed 14 hosted heads. Its raw-byte SHA-256, including
the final newline, is
`b8fee7265e8a6ea38adbd03324cbc22e07785689e5b55e4a51d2101fce018b82`. The same digest results
from the explicit canonical ref-name sort `LC_ALL=C sort -t $'\t' -k2,2` because the server returned
the lines in ref-name order. For clarity, the whole-line (`OID` first) sort has the different
digest `1806619eb44aad84806eb63085da1859fa146492611cb72aafefbdac2d3b23c3`. These hashes bind
the observed snapshot; the direct query remains the authority for hosted-ref absence. A local
remote-tracking cache can still contain names that the host no longer serves, so cached names are
not counted as live branches.

The primary clone also contained one stale remote-tracking ref,
`refs/remotes/origin/sepahead/pid-rs-release-integration-r4` at
`535d7a44e2f8108f806af48cc27b86009239ec4e`. A direct hosted absence check succeeded, the exact
old object was verified, and that tracking ref was pruned. The object remains available through
the retained archive and bundle routes. This local metadata action does not delete the hosted
branch history a second time.

## Hosted and local verification

Five required workflow classes ran against the exact publication anchor. Every job completed
successfully. The required set is the preregistered push-triggered closure set; the scheduled
CodeQL run below is supplementary and is not substituted for a required class.

1. **CI.** Run [33547094635](https://github.com/sepahead/pid-rs/actions/runs/33547094635):
   47 jobs, success; completed 2026-09-01 23:05:44 UTC.
2. **SxPID3 informative-invariance verification.** Run
   [33547094668](https://github.com/sepahead/pid-rs/actions/runs/33547094668): 3 jobs,
   success; completed 2026-09-01 19:39:05 UTC.
3. **CodeQL.** Workflow name `CodeQL`, display `Push on main`, event `dynamic`; run
   [33547093983](https://github.com/sepahead/pid-rs/actions/runs/33547093983): 4 jobs,
   success; completed 2026-09-01 19:11:34 UTC.
4. **Bounded SxPID3 keyed-scalar audit expressions.** Run
   [33547094598](https://github.com/sepahead/pid-rs/actions/runs/33547094598): 1 job,
   success; completed 2026-09-01 19:11:19 UTC.
5. **KSG M1a composite v12 terminal preservation.** Run
   [33547094741](https://github.com/sepahead/pid-rs/actions/runs/33547094741): 1 job,
   success; completed 2026-09-01 19:02:01 UTC.

The exact required census is therefore **5/5 runs, 56/56 jobs, zero failures, zero skipped jobs,
zero cancellations, zero timeouts, zero action-required jobs, zero neutral jobs, and zero stale
attempts**. Here, “stale” is a project-derived count, not a native GitHub field: it means a
declared required attempt that was non-completed or superseded at the final observation. A later
scheduled CodeQL run, [33558833307](https://github.com/sepahead/pid-rs/actions/runs/33558833307),
also completed successfully; it is supplementary and is not needed to establish the required
census.

The separate throwaway clean c499 validation checkout passed the local `just ci` block and the
focused formal, hostile, source-state, method-catalog, publication-link, and PDF checks. The
validation checkout was
separate from the dirty primary review lane and from the source checkout used to prepare this
receipt. The workflow and blueprint PDFs have separate, artifact-specific
rendering receipts and 20-lens visual reviews. The closure commit contains no new mathematical
implementation.

## Remote branch retirement

The following nine remote refs were deleted with exact expected-old-object leases after the
published anchor and hosted checks passed. This is a bounded operator action record; the
post-action query and route predicates are evidence of the observed state, not an independently
witnessed execution transcript:

1. `sepahead/ci-pandoc-toolchain-fix` at
   `b45a7eb2e15364d37ecffc3061bf4f9ac5812b7f` - superseded by the mainline-published anchor.
2. `sepahead/documentation-closure-v1` at
   `30e6d19bf020b18ef1cc1f9478c2d4acba62ccf1` - direct predecessor of the mainline-published anchor.
3. `sepahead/galadriel-placement-main-v1` at
   `eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9` - old main snapshot.
4. `sepahead/openaction-compat-candidate` at
   `9ed6831d20de43467b1cff8adc8ee421a484f7fd` - superseded compatibility candidate.
5. `sepahead/pdf-annotation-portability-corrected` at
   `0af14fc97b7c5fe8c4df0361e37cd9cefaa9c6ba` - superseded portability candidate.
6. `sepahead/pid-rs-release-integration-r4` at
   `535d7a44e2f8108f806af48cc27b86009239ec4e` - integrated release line.
7. `sepahead/pid-rs-release-integration-r4-recovered` at
   `008ee7fa615aa8370623566c21eb99862680c7b1` - recovered predecessor; bundle custody remains.
8. `archive/composite-v5-unqualified-draft-20260818` at
   `f7c6122d25ea098a36fa1fc6d672d78f25b783bb` - exact content is contained by the retained
   rejected-umask archive ref.
9. `sepahead/pid2-rev4-behavior-v1` at
   `03c0980f256c2a66b3d64bff1686a8d116d76138` - exact content is contained by the retained
   PID2 assurance ref.

"Contained" means that an exact object and its relevant evidence are reachable through the named
retained archive or assurance route. It does not mean that all historical prose is scientifically
equivalent. The remote was queried again after the deletion. The remaining archive and diagnostic
refs are listed by the live remote, not inferred from an old local cache.

## Local worktree and temporary-state retirement

Three primary linked worktrees were removed only after process, cleanliness, ancestry, path, and
recovery predicates passed:

1. C4 recovery, former head `bc3aa80fb6025e709c2906a08bce25a4fac40578`. The head is in the
   published candidate ancestry. A retained same-device bundle observation was 30,416,592 bytes
   with SHA-256 `503fa4917ab80c801b203c4cb3ee0d0683bb444ba39857eec481cf9a8917ff59`, and
   `git bundle verify` reported a complete bundle. The private filesystem path is deliberately
   not reproduced in this public receipt.
2. KSG revision 4, former head `a9aa60c962261a6e0e6698b05551fbcdbf7bf41c`. Its 110
   tracked/untracked paths matched the preserved archive head. The historical bundle observation
   was 11,361,236 bytes with SHA-256

   `532ebec0a2a5f2757ccc872925888e1257a082031312d9c7fd4042f6c40cad40`. The raw historical
   bundle preimage is not present in the current bounded filesystem inventory; this is a recorded
   historical observation, not a claim of present local retrievability.

3. M1a correction, former head `dc7b8de0a87443ef2bcde71b19938642f1af2197`. Its
   tracked/untracked paths and ignored-output disposition matched the preserved archive. The
   historical bundle observation was 11,761,811 bytes with SHA-256

   `df4fa378a5a9faf97aa3410ed14a26a0fa870699945b1d91e6b73d2fa72ff2b3`. The raw historical
   bundle preimage is not present in the current bounded filesystem inventory; this is a recorded
   historical observation, not a claim of present local retrievability.

The following temporary state was also removed after exact guards:

- separate throwaway clean c499 validation checkout (not this receipt source checkout);
- clean release-audit checkout at the documented predecessor;
- duplicate render and source-state scratch directories whose hashes matched durable copies or
  current tracked artifacts;
- the clean `available-audit` clone at `dc7b8de0`, after proving that its refs, reflog objects,
  and sole unreachable tag were present in the candidate and that its head was an ancestor of
  c499; and
- the selected named throwaway Rust build-target and render-cache paths that were inventoried for
  this closure. They are rebuild inputs, not scientific records. The primary checkout's `target/`,
  `tmp/`, and unrelated sibling caches are outside this item and were not globally removed.

The operator record states that no broad repository path was used. Each named target was resolved,
checked for links, checked for writers, and removed separately; those details are not an
independently witnessed execution transcript. The force option on `git worktree remove` was used only after
those checks were reported to show that no required bytes remained; the option itself is not
evidence of safety.
The recovery bundles and archive refs were not deleted. Git garbage collection was not used as a
substitute for an evidence decision. The exact control methods are machine-readable in the
`cleanup_controls` object of the JSON record.

## State deliberately retained

The cleanup is not a claim that every branch or copy is obsolete. The following state remains
protected because the available evidence does not prove redundancy or because another registry
still depends on it:

1. The dirty primary review worktree at
   `9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56` remains untouched. Its methods narrative,
   private identifier, unpublished packets, and untracked material require a separate semantic
   and privacy decision.
   A fresh private custody package was captured at `2026-09-02T04:36:04Z`. Its exact
   byte-level inventory is:

   - v2/NUL status projection:
     `991b4d72b2388d05ababf526af40a4eafdf836a3b6a9a2dc0daee269a2407e3a`;
   - tracked worktree patch, 1,549,131 bytes:
     `d5b089ef4a5a93d8b96c7ef95d2da6b23c8c08bc75603ced11bdd2216f3537f1`;
   - empty staged patch:
     `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`;
   - private untracked archive, 1,008,981 bytes:
     `ae94bffad48b7eabae3d6a794fbb7676dbeb6230ea0c63755264e8f5d759ac40`;
   - all-ref Git bundle, 36,426,597 bytes:
     `07562762e2a68cffd41f3a44ae76f18fba118802927217f91cf47da5f94259ed`;
   - bundle verification output, exit status 0:
     `80aaef8688091f51c56ed399697238506f0e7921f99308da390a1bc475716265`;
     and
   - package manifest:
     `a14d4822846bf90c626c0266f283cfaa857abe37705d625647565d0ab395e9c9`.

   The package captured 159 of 160 untracked leaves after excluding the exact local
   device-identifier path.
   These are private byte-preservation facts, not public locators or scientific acceptance.
2. Local `codex/integration-20260804` and `codex/workflow-publication-20260804` remain because
   each has a divergent publication commit. Their equivalent workflow content is accounted for,
   but branch removal is not needed for this closure and would erase a useful recovery route.
3. The primary `refs/archive/dirty-primary-pre-integration-20260827`, KSG/M1a archive refs,
   checkpoint refs, and quarantine refs remain. They preserve negative results, restricted
   preimages, and recovery history. A quarantine ref is not an accepted method or release.
4. Remote archive and diagnostic refs remain, including rejected composite experiments, the
   exact-log hostile route, the PrimeGaps transfer blueprint, the Galadriel guide, PID2 assurance,
   Python-custody preimage, and C3 diagnostic capture. A side ref is historical evidence, not
   active `main`.
5. The C12 common registry, its dirty R4 linked worktree, hosted-failure evidence, and L12
   evidence remain. They contain nonancestor numerical or custody material that is not reproduced
   byte-for-byte in the mainline-published anchor.
6. The C11 fresh clone remains because C12 has a configured `c11-source` URL that points to it.
   Removing it now would leave that URL dangling and break recovery commands until it is rebound.
7. The C3 guide-reproduction clones remain because the divergent capture and two old monolithic
   SVG blobs have explicit side-ref custody requirements. The current mainline has split
   replacements, but that is not proof that the old visual history is disposable.

These retained objects are not unfinished accepted work. They are labelled recovery, negative,
restricted, or pending-adjudication state. A future retirement must make a new exact comparison and
must not infer safety from this receipt.

## Presentation artifact and portability boundary

The human-readable PDF is built from this Markdown with
`scripts/build-post-publication-custody-pdf.sh`. The builder uses Pandoc 3.10.2, LuaHBTeX 1.18.0
(TeX Live 2024), librsvg `rsvg-convert` 2.62.3, and an explicit Lua filter. The filter projects
repository-relative evidence links to HTTPS `github.com/sepahead/pid-rs/blob/main/...` navigation
links in the standalone PDF; it does not change the Markdown source or make the remote target
immutable. The machine record binds the builder, header, filter, SVG source, and derived figure
hashes after the final build. The PDF is intentionally untagged; no PDF/UA or assistive-technology
conformance claim is made. A separate structural check rejects relative/file links and `/GoToR`
actions; external URL reachability remains outside this offline check.

## Council and lens review

The publication closure was reviewed through the seventy named lens/outcome rows preserved in
`PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md`, section “Dated 1 September 2026
adversarial publication closure”: twenty mandatory lenses and fifty additional artifact-specific
lenses. The separate PDF receipt records a twenty-lens color/grayscale visual review. This was a
self-review council of recorded agents and checks, not independent human or scientific review. The
count records process coverage; it is not an assurance probability or a proof of correctness. This
custody addendum groups the most relevant questions into the following ten prompts; it does not
replace the named seventy-row record:

- Does the mainline-published anchor identify one exact tree, parent, remote ref, and local ref?
- Are the dirty primary checkout and the clean validation checkout kept distinct?
- Does each deletion have a process-free check, an exact target, a reachability or bundle route,
  and a post-action observation?
- Are branch containment, byte identity, tree identity, ancestry, and semantic equivalence kept
  as different predicates?
- Are historical ledgers left immutable and clearly dated?
- Are negative, restricted, and failed routes retained without promoting them to `main`?
- Does any wording imply mathematical, statistical, estimator, or application validation that was
  not performed?
- Are local paths, private identifiers, and temporary build outputs excluded from the public
  custody claim?
- Can a future agent resume from the JSON record and re-observe the live state?
- Do the Markdown links and PDF references resolve from the repository root?

The disposition is **green with explicit retention caveats for this custody operation**. The council
found no source change in this process-only closure that would require altering the PID mathematics;
that is not a mathematical endorsement. It also found no basis for an "all branches are gone"
claim.

## Nonclaims and next observation rule

This receipt does not:

- prove any PID definition, theorem, probability law, estimator consistency, calibration, or
  downstream sensor-placement benefit;
- authenticate a Git object, bundle, executable, model, or hosted runner;
- turn hosted success into independent scientific review;
- independently witness the operator's deletion commands or prove unrecorded process history;
- make remote-main equality imply a clean working tree;
- make Git reachability, a bundle digest, and a filesystem copy interchangeable;
- provide a global inventory of all disks, sibling directories, hidden processes, or private
  storage; or
- authorize future ref deletion, worktree removal, cache deletion, or garbage collection.

Before another cleanup action, re-run the remote-ref query, local-ref query, worktree/process
inventory, exact status and ignored-path check, bundle verification, and post-action reachability
check. If any identity or status differs, stop and create a new receipt. Keep the historical ledgers
and this receipt as separate observations. This is the durable process boundary that prevents a
new agent from treating a stale snapshot, a branch name, or a polished PDF as authority for a
different context.
