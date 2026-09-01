# Worktree and branch preservation receipt (2026-08-27)

## Scope and boundary

This receipt records bounded Git and byte-level checks performed before any branch or worktree
cleanup. It preserves recovery routes; it does **not** promote archived drafts, certify their
mathematics, or make them part of the active release surface. A later artifact superseding an
older blob does not erase the older blob while its commit remains reachable.

The integration candidate at the start of the original audit was commit
`535d7a44e2f8108f806af48cc27b86009239ec4e` on
`sepahead/pid-rs-release-integration-r4`. No source branch or worktree was deleted or rewritten
during that audit.

## Recovery incident and reconstruction status

An uncommitted temporary integration repository was lost after a computer restart. Its private
object store contained a staged 87-path synthesis and a later four-path working-tree delta. The
temporary object store and its synthetic staged commit are not known to survive in any verified
bundle or reachable object database. Consequently, this receipt does **not** claim byte-identical
recovery of that synthesis.

The exact remote parent remained available and was fetched into a new recovery repository. The
scientific source states feeding the synthesis had already been captured independently as Git
bundles. Recovery therefore proceeds by re-integrating and re-verifying those source states, with
new commits, hashes, generated artifacts, and visual receipts. Old PDF, staged-tree, and receipt
hashes are comparison clues only; they are not authorities for reconstructed bytes.

This incident demonstrates why a staged index is not durable storage. A milestone is considered
durable only after its commit is reachable from a pushed ref and, for designated recovery states,
from a separately verified bundle.

## Preserved branch and detached tips

The primary repository's seven named branch tips and one detached recovery tip were copied to
local archive refs before comparison.

| Preserved tip | Commit | Relation to the original integration candidate |
|---|---|---|
| detached C4 recovery | `bc3aa80fb6025e709c2906a08bce25a4fac40578` | ancestor |
| KSG revision-4 candidate | `a9aa60c962261a6e0e6698b05551fbcdbf7bf41c` | ancestor |
| KSG M1a CI correction | `dc7b8de0a87443ef2bcde71b19938642f1af2197` | ancestor |
| PDF CI correction | `af50935be9ecf9a81aeb30c56b45059652468746` | ancestor |
| primary `main` | `9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56` | ancestor |
| primary review branch | `9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56` | ancestor |
| workflow integration branch | `bd5ea639e303e2f9d57d13b502dd68d3da6ada73` | one divergent commit; content accounted below |
| workflow publication branch | `1bec7a4fdcf80b4b0b7d5f03d4491bb5f8319709` | one divergent commit; content accounted below |

The six ancestor results were checked with `git merge-base --is-ancestor`, not inferred from
commit subjects.

## Divergent workflow commits

Both divergent tips contain the same 29-path workflow-publication change applied to different
parents. Commit `9031230d0ab6e0878fe8b9ba38578a80c9439776`, which is an ancestor of the
original integration candidate, preserves that publication change:

- The stable patch ID from `git show <commit> --pretty=format: | git patch-id --stable` is
  `0578f029482cae13ea538af721c8a85c88ccdc6e` for both `bd5ea639...` and `9031230...`.
  With `git show --binary`, both produce binary-form patch ID
  `0537137f69a14949b9e70b0c67a8636cfc198dbc`; the command mode is recorded because the two
  representations intentionally hash differently.
- For all 28 changed paths other than `CHANGELOG.md`, the post-commit blob IDs of `1bec7a4...`,
  `bd5ea639...`, and `9031230...` are pairwise identical; mismatches: `0`.
- Each commit adds the same 13 changelog lines. Their SHA-256, including the terminating newline,
  is `d01b5454c28ad4394ecc362b9498d835e1c96a0986acfe0a8779dcf7386713ec`.
- A range-diff attributes the different whole-patch ID of `1bec7a4...` to different changelog
  parent context, not to a different workflow artifact.

Thus neither divergent commit contains a workflow-publication delta missing from the integration
history. The archived refs remain a second recovery route until final cleanup.

## Exact dirty-primary snapshot

The primary worktree contained useful drafts, negative evidence, superseded verifiers, and
modified files that were not all reachable from existing refs. They were captured without changing
the primary index or worktree:

- parent: `9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56`;
- archive commit: `86faa9a0850ca416f54a467230106b01d4162687`;
- archive tree: `4f6fddb80754645cf6fa0fa48cdb82db457bb478`;
- recovery ref: `refs/archive/dirty-primary-pre-integration-20260827`;
- delta: 225 files (`156` added and `69` modified), 60,078 insertions and 1,223 deletions;
- archived-path comparison: 225 checked, 0 byte mismatches;
- excluded path: one worktree-local application identifier, whose absence from the archive tree
  was checked explicitly.

The complete bundle has SHA-256
`5f5b5060e8da0d3549269eb9ae813e8f089a7b8a1a62303698d60867d3ae9f19`, size
11,584,500 bytes, and advertises the exact archive commit above. `git bundle verify` reports a
complete history. Its storage locator is intentionally outside the public repository surface.

### Formal-artifact revision drift retained as negative evidence

The archived primary snapshot also makes one verification-chain failure reproducible. The
untracked Lean checker, SHA-256
`b8d4128c34cb4a95a830ebb9ff7ff7c7c61202a9cb026a0b8bf0a1a7f79936eb`, selects
`audit/formal/lean-ksg-harmonic/v3/PidKsgIntegerHarmonic.lean`, but the archive tree contains only
the unversioned retained source, `v2`, and `v4`; the `v4` source has SHA-256
`32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4`. The untracked Z3
checker, SHA-256 `aee09f4ca8d4470a0be5eda13905d087bcff679a4e2538d717ba040c2dd8f657`, names
`ksg-local-bound-v3.smt2`, while the archive contains `ksg-local-bound-v4.smt2`, SHA-256
`33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31`. Both missing-name
conditions are exact inventory facts, not a judgment about theorem truth.

The mixed snapshot is retained as typed negative workflow evidence. It is not promoted to the
active verification lane. The accepted source tree instead binds the revision-4 Lean and Z3
artifacts through the active checkers and their hostile self-tests. Removing a revision predicate,
accepting whichever filename exists, or resealing a digest without adjudicating the intended
revision would make the evidence weaker and is prohibited.

## Independently verified bundle inventory

The following filenames are logical recovery labels, not public storage locators. On 2026-08-27,
each listed file was read afresh, hashed, and accepted by `git bundle verify`; every bundle reports
a complete history using Git's SHA-1 object format. The advertised object is the single archive ref
for dirty snapshots, or the relevant `HEAD`/integration head for complete clean-repository bundles.

| Recovery label | Bytes | SHA-256 | Advertised object |
|---|---:|---|---|
| `c10-forensic-dirty-worktree-2026-08-27.bundle` | 23,650,436 | `d07c43bea4a920f37de5650db4168de95a95cb8635a6c9f8693d7c3d83735b6c` | `9cef1844d9994e72eab0c7069f3c02b03124b7f0` |
| `c10-recovered-dirty-worktree-2026-08-27.bundle` | 29,651,890 | `705616b5cad333e02b8d14553edef0dbcc612ea94a9e7f60ca2609348ba256d4` | `690c7a4c748173bed4d522b841c4c453da73280b` |
| `dependency-doc-clean-repository-2026-08-27.bundle` | 30,512,102 | `081fdb9b43e4fecbfb4639fc94caa86fd009afbffaa98c097bd50c2e67040dcf` | `56e91781d1a2cf88b250ee0287d8260921b9bc0e` |
| `fable5-archive-clean-repository-2026-08-27.bundle` | 30,367,012 | `b9cdf25b9d48ad362d25e27760a4fe01ee9d1693c2ca307b9ee113a5314e33ee` | integration ref `3c057e8733fa9463ffd5809e2a746d4bb278db0e` |
| `legacy-copy-dirty-worktree-2026-08-27.bundle` | 160,320 | `548c7e981bd6f7584d5fba8e448129a847610c404ee2ea02f85a6f194a4276b8` | `e7a841f2263d827d38d721ca8af1ccf51966838f` |
| `milestone-archive-clean-repository-2026-08-27.bundle` | 30,382,519 | `0635ed934e7dc4cc1530ac3c4088a9e6b505236f11857a5373dc14ed6fa12f4e` | `c94202db75472380d53a7177c2dfedd04ee5c1c0` |
| `milestone1-clean-repository-2026-08-27.bundle` | 29,880,437 | `40a06fd0815c600e6df0eccf7cd8dd24dd877b69113a449fc0e4898983290058` | `fd718f20198ab61b669a1d3cf20155d21aa36368` |
| `milestone2-clean-repository-2026-08-27.bundle` | 30,319,870 | `29d8a06df72ac2aa5d1994c1a5457b88579f141e8fbddd93fe20533a434d7f47` | `544c4ceba92228c249de656c01ac5b5214d65d37` |
| `milestone3-dirty-worktree-2026-08-27.bundle` | 30,566,702 | `a5a5628f4baae73f11fd0dffef0dd901dea9a5c41de74098237c274a3861b889` | `92b21928c67c98be97c8a0184d57b764ef2db73b` |
| `numerical-r2-clean-repository-2026-08-27.bundle` | 33,585,190 | `5c60563ae64e4f6df24157043e8e458bf1d7479147e03d2d669d71e84503501c` | integration ref `b9fd77ce43ef7379eb9792dd2f4814649f35b316` |
| `orca-integration-source-dirty-worktree-2026-08-27.bundle` | 31,402,700 | `3b1ad6ce4039f1e77f0b309d0f06938bafeddcdd04e19d8361f968a960bc79e8` | `9da582d95d0edae44e0a40570525923e63fd0c72` |
| `p1-replay-audit-dirty-worktree-2026-08-27.bundle` | 27,280,169 | `383ac59b9782266e689d2b2c79a6e089d5168b0eca2b46a08c4d2661308808e8` | `060a9c8d803d738ed5e5673ee826d9d35faa6938` |
| `p5-rehearsal-clean-repository-2026-08-27.bundle` | 27,420,357 | `a6b3e44a1f3dc2757319f38312c07324e0944d4b5017804402b247d54137a92c` | `44328e3279dee896f6ece83ae9c5d9fd0a28a09b` |
| `pid-rs-dirty-primary-pre-integration-2026-08-27.bundle` | 11,584,500 | `5f5b5060e8da0d3549269eb9ae813e8f089a7b8a1a62303698d60867d3ae9f19` | `86faa9a0850ca416f54a467230106b01d4162687` |
| `primary-ksg-rev4-dirty-worktree-2026-08-27.bundle` | 11,361,236 | `532ebec0a2a5f2757ccc872925888e1257a082031312d9c7fd4042f6c40cad40` | `4c199f75b80b1d0a5660c629d905dab41a0d2d96` |
| `primary-m1a-dirty-worktree-2026-08-27.bundle` | 11,761,811 | `df4fa378a5a9faf97aa3410ed14a26a0fa870699945b1d91e6b73d2fa72ff2b3` | `6e46fe99edeac6621417c6e046ab77650f827583` |
| `program-dossier-complete-2026-08-27.bundle` | 201,246 | `65cbb4554e6c19f26baa28da365a0a001c3c5846b8fe63609d7c34da98a99b35` | `6b1f789bba99e76cd2fbedd5251ef1ec89698066` |
| `publication-synthesis-dirty-worktree-2026-08-27.bundle` | 28,452,952 | `9bcb73c67808178d5cb470b62a92b32d624982f4d5b85e043eede67dccc4d249` | `df22846a66bf439b5ee8642166b0599de03a7835` |
| `science-synthesis-dirty-worktree-2026-08-27.bundle` | 28,715,028 | `d6f7f373c4026e1b5c262270f3c65c96ab07eadb2c53c2433db56e74926d199c` | `9565b0eda6e9671bea2b9bed6c4a7641dcbfb9fc` |
| `sxpid3-independent-dirty-worktree-2026-08-27.bundle` | 22,740,768 | `fd26553961d90777a381bfbe446966368b1eebd27b3ce4707cb19aeeeb7efc37` | `30095a7c6cad0f6e7bc2e13bc7ac43e838d30357` |

`git bundle verify` checks bundle structure and prerequisite closure; it does not prove media
durability, authenticity, semantic completeness, or freedom from coordinated source errors. The
SHA-256 values bind observed bundle bytes but are not signatures.

### C12 terminal-evidence worktree disposition

The clean worktree labelled `pid-rs-c12-terminal-evidence-20260824` was re-read explicitly rather
than inferred from the bundle table:

- local branch: `codex/c12-terminal-evidence-20260824`;
- exact HEAD: `f7811023da638fe7ede921b7b51c32fef8eb2c80`;
- worktree status: clean;
- remote reachability: the exact commit is `refs/heads/main`; the local descriptive branch name is
  not separately published;
- ancestry: this commit is an ancestor of the recovery branch and is 24 commits behind its first
  recovery milestone, with no commit unique to the terminal-evidence side;
- workflow PDF: 83 A4 pages, 824,560 bytes, SHA-256
  `6abf5af2ab7fb5cf0b40c37977dc38156d4bdf251b6f2948815c472fc77f1288`;
- integration comparison: those PDF bytes are identical at the terminal-evidence HEAD, the
  original integration parent, and the recovery milestone;
- bundle custody: the verified `numerical-r2-clean-repository-2026-08-27.bundle` advertises the
  exact terminal-evidence commit both as its named branch and as the worktree HEAD.

No cherry-pick is required. The integration line contains later changes to the workflow PDF
checker, so copying the older checker from this worktree would be a regression even though the PDF
itself is already preserved. The worktree remains subject to the cleanup preconditions below.

## Bounded advisory-council accounting

The inert public archive at `audit/archive/advisory-councils-20260725-20260726/` accounts for an
exactly bounded 30-path subset of the protected dirty-primary snapshot: five exact,
non-executable prompt payloads and 25 hash-only companion records. The hash-only set contains ten
Fable companions, 14 Opus-family artifacts, and one final-PID2 adversarial prompt. None of those 25
raw companion payloads is imported into the public archive or active evidence surface.

A fresh direct comparison against the preserved dirty-primary Git objects matched all 30 indexed
paths, byte lengths, and SHA-256 values, with zero missing objects and zero mismatches. The checker
reports `payloads=5`, `withheld_hash_only=25`, and `rederivation_candidates=10` identically under
ordinary and optimized isolated Python. Its hostile suite kills 64 mutations identically under
both modes. These checks establish bounded byte accounting and named fault sensitivity only. The
private quarantine remains pending semantic, privacy, rights, and publication review.

The one preserved zero-byte stderr stream has SHA-256
`e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. Because that is the universal
empty-byte digest, it cannot identify or authenticate any execution. Five additional historical
Fable/Opus mathematical-workflow files lie outside this bounded archive because their bytes already
remain in the integration history and in the dirty-primary snapshot.

## Follow-up retirement audit (2026-09-01)

This follow-up is bounded to the **primary repository's common Git directory**, its four registered
worktrees, and the named hosted refs. The live snapshot ran from `2026-09-01T07:06:55Z` through
`2026-09-01T07:08:48Z` with Git 2.55.0 using SHA-1 Git objects; the restricted bundle itself was
created earlier at `2026-09-01T06:42:30Z`. It is not a fresh global inventory of sibling `pid-rs*`
repositories, standalone custody repositories, or copied directories. At this primary-snapshot
boundary, those sibling locations—including the clean C12 terminal-evidence repository—remained
retained pending a separate registry/byte/process ledger; the sibling follow-up below now supplies
that dated ledger. Historical C12 wording binds its dated commit; it does not identify the later
remote-`main` tip.

Within that boundary, this follow-up re-read the live worktree registry, local namespaces, and
hosted branch tips before cleanup. The pre-documentation closure candidate was
`30e6d19bf020b18ef1cc1f9478c2d4acba62ccf1`; hosted `main` was
`eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9`. The candidate was six commits ahead and zero behind,
with that hosted `main` object as its merge base. A later documentation commit necessarily replaces
the candidate. Every ancestry, remote-head, CI, worktree, and ref disposition must therefore be
re-read against the final object before retirement. No branch, ref, or worktree was removed during
this follow-up.

The exact machine-readable projection of this follow-up is
[`worktree-and-branch-retirement-ledger-2026-09-01.json`](worktree-and-branch-retirement-ledger-2026-09-01.json),
validated against its closed schema by
`scripts/check-worktree-and-branch-retirement-ledger.py`. The JSON record, schema, and checker are
the authority for exact counts and ordered manifests; this prose explains their meaning and limits.

### Registered worktrees

| Lane | Observed state | Follow-up disposition |
|---|---|---|
| Primary review lane, `9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56` | 69 tracked modifications and 160 untracked leaf paths. Of the 229 paths, 224 retain the earlier snapshot bytes. Three newly visible archive payloads are exact blobs in the closure candidate; one local device identifier remains private; and current `METHODS.md`, blob `5497329c5ccd7693f3a426ef90d002b156ce3274`, matches neither the August archive blob `5f30f4ae7ed0367ee42791043a35fad58bdf73ae` nor the candidate blob `883921a8c1fe123cd7426054472ba64b39547bd7`. | **Retain.** The distinct methods narrative and private path require separate adjudication. Do not overwrite this tree with the candidate. |
| Detached C4 recovery, `bc3aa80fb6025e709c2906a08bce25a4fac40578` | Clean, with no ignored payload found; commit is in the candidate ancestry. | **Conditionally removable only after final-main gates.** Re-read cleanliness and ancestry immediately before Git-aware removal. |
| KSG revision-4 lane, `a9aa60c962261a6e0e6698b05551fbcdbf7bf41c` | 38 tracked changes and 72 untracked paths are byte-covered by archive commit `4c199f75b80b1d0a5660c629d905dab41a0d2d96`; the resulting tree equals candidate ancestor `dc7b8de0a87443ef2bcde71b19938642f1af2197`. Remaining ignored state is build/cache material or empty temporary structure. | **Conditionally removable only after final-main gates and a fresh 110-path comparison.** Reverify the named bundle and advertised archive head first. |
| M1a correction lane, `dc7b8de0a87443ef2bcde71b19938642f1af2197` | 34 tracked changes and 11 untracked paths are byte-covered by archive commit `6e46fe99edeac6621417c6e046ab77650f827583`; its tree equals candidate ancestor `af50935be9ecf9a81aeb30c56b45059652468746`. Ignored `tmp/pdfs/` contains 115 rendered PNGs, four distinct intermediate PDFs, and 24 TeX auxiliary files, totaling 45,141,911 bytes. | **Retain pending ignored-output adjudication.** The files appear to be derived presentation intermediates, but differing rendered text and PDF bytes are not deleted merely because newer publications exist. |

### Local ref namespaces

The ordinary branch list was incomplete. The common Git directory also contains three
`refs/archive/` refs, five `refs/codex/checkpoints/` refs, and 48 refs below
`refs/pid-rs/quarantine/20260825/`. Most quarantined histories have distinct patch histories. The
August bundle roster did not advertise this quarantine namespace. The namespace is therefore
retained as a class pending path/blob and semantic adjudication. Only checkpoint
`refs/codex/checkpoints/ksg-rev4-m1a-110path-v2-20260727T205617Z`, at
`dc7b8de0a87443ef2bcde71b19938642f1af2197`, was immediately shown to be redundant with candidate
ancestry; that observation alone does not authorize its deletion before the global gate.

To remove the local-only recovery gap, restricted custody record `RCR-20260901-01` was created for
a private complete bundle from the primary
repository with all then-visible refs. It has 32,474,415 bytes and SHA-256
`89a751a60cb221e0aa336b348b5873f458417b0947a9d5d7920f9332ec82b7f7`; its 71-head manifest has
7,354 bytes and SHA-256
`f2700d0f1a79a64d7798f8bddda7ad4abae4cd0e64ac2cdb524e31f18052b467`. The copied destination
passed `git bundle verify` and a fresh bare-repository drill. The drill restored 67 proper refs;
the other four advertised names were checkout or bundle pseudo-heads, and all 71 advertised object
IDs were present in the recovered object database. The storage locator is intentionally outside
the public repository surface. Access is limited to maintainer-authorized restricted storage. No
deletion date is authorized: retain the record until every advertised ref has a terminal semantic
disposition, every required byte has a separately verified durable successor, and an explicit
maintainer decision closes the retention obligation.

This new bundle preserves reachable Git objects only. It does not contain current dirty primary
bytes, ignored M1a PDF intermediates, stashes, indexes, hooks, configuration, reflogs, or scientific
dispositions. It supplies no authenticity, independent-custody, mathematical, or publication
claim and is not deletion authority.

### Hosted branches

The following seven hosted branches are retirement candidates only after the final candidate is
exactly remote and local `main`, a `push`-event workflow on that exact mainline SHA succeeds, and
each remote tip is re-read and lease-matched:

| Hosted branch | Observed tip |
|---|---|
| `sepahead/ci-pandoc-toolchain-fix` | `b45a7eb2e15364d37ecffc3061bf4f9ac5812b7f` |
| `sepahead/documentation-closure-v1` | `30e6d19bf020b18ef1cc1f9478c2d4acba62ccf1` |
| `sepahead/galadriel-placement-main-v1` | `eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9` |
| `sepahead/openaction-compat-candidate` | `9ed6831d20de43467b1cff8adc8ee421a484f7fd` |
| `sepahead/pdf-annotation-portability-corrected` | `0af14fc97b7c5fe8c4df0361e37cd9cefaa9c6ba` |
| `sepahead/pid-rs-release-integration-r4` | `535d7a44e2f8108f806af48cc27b86009239ec4e` |
| `sepahead/pid-rs-release-integration-r4-recovered` | `008ee7fa615aa8370623566c21eb99862680c7b1` |

Ten divergent hosted archive/diagnostic branches remain mandatory retention: the six composite-v5,
v6, and v9 rejected/draft branches; `archive/exact-log-product-verifier-draft-20260828`;
`archive/real-r-constructor-v8-public-disposition`;
`codex/primegaps-pid-blueprint-20260819`; and
`diagnostic/c3-pdf-capture-20260830`. Each retains branch-only commits.

Five more hosted branches remain under adjudication rather than cleanup:

- `sepahead/exact-log-hostile-v1` retains an earlier hostile-receipt blob that the candidate replaces;
- `sepahead/galadriel-placement-guide-v1` retains earlier guide, PDF, and figure variants;
- `sepahead/pid2-rev4-behavior-v1` retains a distinct historical source-state receipt;
- `sepahead/pid2-rev4-assurance-v1` retains an earlier assurance document and source-state receipt;
  and
- `sepahead/python-custody-m0-v1` retains a 5,473,991-byte registry preimage that the candidate
  intentionally represents only by digest and blob object ID.

The last item is a concrete example of the rule that a digest does not replace a retrievable
preimage. None of these five branches may be removed until the distinct bytes are either retained
under an explicit scientific/archive disposition or proved reproducible and non-load-bearing.

## Sibling-registry follow-up (2026-09-01)

A second read-only snapshot covered ten Git registries and twelve observed worktrees from
`2026-09-01T07:32:07Z` through `2026-09-01T07:38:43Z`, using Git 2.55.0. It deliberately
excludes the primary repository's common Git directory, which the preceding follow-up covers, and
excludes non-Git copies whose independent object registry was not established. No active owner
process was observed during the bounded process check. That negative observation is not proof of
abandonment.

The exact public projection is
[`sibling-registry-retirement-ledger-2026-09-01.json`](sibling-registry-retirement-ledger-2026-09-01.json).
Its closed schema and
`scripts/check-sibling-registry-retirement-ledger.py` bind the recorded bytes, identities,
arithmetic, cross-record relations, and non-authorizing disposition. The checker is a deterministic
snapshot-integrity validator. It does not revisit the registries, open restricted custody
artifacts, replay bundles, contact hosted refs, inspect the network, or authorize cleanup. A fresh
external observation remains mandatory before any mutation.

Across the twelve worktrees, the snapshot recorded five clean and seven dirty trees, with zero
staged, 122 unstaged, and 110 untracked status entries. It bound nine custody artifacts. It also
recorded 52,718,612,480 allocated bytes as preliminary cache candidates. That byte total is not a
complete cache-directory census, proof of reproducibility, ownership decision, or deletion
authority. The ledger authorizes no cache deletion.

The selected-path comparison rows keep their target explicit. In particular:

| Selected corpus | Integration candidate | Live remote `main` |
|---|---:|---:|
| C12 numerical, 50 committed paths | 22 exact, 28 evolved, 0 absent | 23 exact, 27 evolved, 0 absent |
| C12 Orca integration, 118 observed dirty paths | 9 exact, 79 evolved, 30 absent | 6 exact, 77 evolved, 35 absent |

The C12 terminal workflow comparison is a separate five-path corpus: all five selected blobs were
exact against live remote `main`. The aggregate comparison census is 65 exact, 270 evolved, and
101 absent over ten target-specific rows. It is not a count of unique paths because the C12
numerical and Orca corpora each appear once per target. Exact means byte identity for the selected
blob; evolved means a selected successor exists with different bytes; absent means no selected
successor was identified. None of these labels establishes semantic equivalence, scientific
validity, or whole-tree equality.

Four audit corrections are material to the process:

1. Comparison counts must remain attached to their target. The integration-candidate counts and
   live-remote-`main` counts above cannot be exchanged.
2. The C10 forensic registry is a `blob:none` partial clone with one promisor remote and six
   promisor-pack markers. With lazy fetching disabled, zero missing objects was established only
   for objects reachable from the exact observed `HEAD`. It is not a global object-completeness
   result. A separate isolated bare-repository replay established custody only for the exact
   advertised archive commit in its identified bundle.
3. Three C12 commits were unreachable from the observed live-ref set but were exact advertised
   objects in verified public-receipt-bound bundles. Their custody is therefore bound even though
   their live-ref reachability is false. Those three pairs create no pair-specific registry
   retention requirement; unrelated unadjudicated refs, worktree bytes, ignored material, and
   semantic dispositions still require retention.
4. The publication-synthesis checkpoint is the full SHA-1
   `df22846a66bf439b5ee8642166b0599de03a7835`, with tree
   `77cf10062d9dce6fcf123187c10ac288694185e0` and single parent
   `662505cd1bba27a34fdd720d5867b6ed791aefc9`. A malformed identifier missing its leading
   hexadecimal digit is not an acceptable exact identity.

The resulting decision is `retain_and_adjudicate`. Retention is based only on genuinely
unadjudicated scope; it is not justified by the three custody-bound pairs. Promotion, remote
mutation, ref deletion, registry deletion, worktree removal, garbage collection, and cache deletion
all remain unauthorized. This follow-up corrects the earlier “siblings pending” boundary; it does
not convert a dated snapshot into live cleanup authority.

## Cleanup preconditions

No worktree or branch may be removed merely because this receipt exists. Cleanup additionally
requires all of the following:

1. integration changes are committed in coherent unsigned milestones;
2. local exact gates and the required hosted matrix are green at the exact pushed head;
3. integration history is fast-forwarded to both local and remote `main`;
4. every designated recovery bundle is reverified and remains readable;
5. scientifically valuable drafts and negative results receive an explicit disposition: active
   integration, clearly labelled archive, superseded-but-retained, or rejected with reason;
6. branch ancestry and worktree dirtiness are re-read immediately before each cleanup action;
7. any cleanup command names an exact resolved target and is followed by a reachability audit.

This receipt is evidence for recoverability and migration discipline only. It is not evidence that
archived mathematical statements are true, that old verifiers are trustworthy, or that every
archived item belongs in a publication.
