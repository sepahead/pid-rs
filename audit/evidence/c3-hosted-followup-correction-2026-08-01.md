# C3 hosted-portability follow-up correction receipt

**Receipt date:** 2026-08-01; updated 2026-08-02
**Disposition:** **NO-GO / f6 follow-up rejected for hosted closure; correction pending**
**Scope:** bounded engineering correction rooted in three failures observed on the immutable C3
checkpoint plus retained follow-up PDF-dependency and restrictive-umask falsifiers; this is not a
new KSG, PID, formal-mathematics, statistical, PDF-content, release, or security result.

## Immutable anchor and lifecycle

The only accepted C3 anchor for this follow-up is:

```text
C3 commit: 8fa6e992d9124229c7a175c4508bf10df336675a
C3 tree:   059dc980d4a86066c07687188a452cf2459899eb
parent:    8b792bc143fff2d84f2d8e7817d1de7850741223
subject:   fix: harden Lean evidence portability and replay
```

The accepted implementation follow-up is unsigned direct child
`f6fde520b841c61b7752cdd053af59bda763d3d1`, tree
`1ce2d75081bf85d9a30da180539c162a2c5a5c86`, with the reviewed human author/committer name and
email metadata. This mechanical metadata check does not authenticate who created the bytes or
commit. No earlier provisional tree, reconstructed candidate, interrupted run, or post-hoc local
snapshot is accepted as follow-up custody. The original 2026-08-01 source intentionally omitted
the then-nonexistent self-determining commit/tree; this dated update records the later external
commit and tree observations without claiming that the f6 document predicted or self-certified
them.

Two lifecycles are distinct and must remain distinct:

1. The immutable C3 historical replay verifies the exact clean C3 commit and separately recreates
   the exact parent-plus-overlay C3 candidate needed by the historical hostile self-test.
2. A separate outer gate verifies the new direct-child correction, its exact allowed paths and
   blobs, every protected C3 blob, its source loader, and its caller-supplied alternate-index tree
   and checkpoint. That gate accepted exact f6 locally; the later hosted PDF failure still
   prevents whole-run GO.

A successful historical replay cannot authorize the follow-up tree. Conversely, follow-up custody
cannot replace the historical parent-plus-overlay lifecycle required by the C3 hostile suite.

## Hosted evidence that forced this correction

GitHub Actions [CI run
`30688494783`](https://github.com/sepahead/pid-rs/actions/runs/30688494783) executed the exact C3
commit above. Its terminal result was **failure**: exactly 42 of 45 jobs succeeded and the following
three jobs failed. This run therefore has no all-green hosted-CI credit.

| Failed job (exact hosted name) | Job ID | Bytes | Retrieval interval (UTC) | Job-log API response SHA-256 | Observed boundary |
|---|---:|---:|---|---|---|
| [Formal LaTeX / PDF inventory and cross-toolchain structure](https://github.com/sepahead/pid-rs/actions/runs/30688494783/job/91338863181) | `91338863181` | 66,399 | `2026-08-01T14:55:50Z`–`14:55:52Z` | `f5e201ddb8891986aa33264d5f8d2f187bf8454ecd604fd2d2cce2efd1020bc6` | Seven earlier PDFs passed; the mathematical-workflow build then stopped because `libertinus.sty` was unavailable. The ninth PDF was not reached. |
| [KSG integer-harmonic arithmetic and phase isolation](https://github.com/sepahead/pid-rs/actions/runs/30688494783/job/91338863225) | `91338863225` | 58,554 | `2026-08-01T14:55:52Z`–`14:55:57Z` | `ec45056d40c5263c181f4a92b7bdb038830e44fa0107b64e50992512615288e4` | The checker passed in normal and optimized Python on the clean checkpoint. The first hostile self-test then failed with `clone semantic facts differ from frozen source facts`. |
| [Core experimental-heuristics](https://github.com/sepahead/pid-rs/actions/runs/30688494783/job/91338863305) | `91338863305` | 81,547 | `2026-08-01T14:55:57Z`–`14:56:00Z` | `9f8449a2b09b30f954b4c88b2508d4283938181bfd95dc60def275f1863fb0bd` | In `software_identity_build`, 50 tests passed and `final_status_reread_observes_a_post_status_worktree_change` failed: the probe returned fail-closed `Unavailable` / `git_unavailable`, while the harness expected `Dirty`. |

For each row, the digest domain is the exact byte stream emitted after redirect handling by
`gh api repos/sepahead/pid-rs/actions/jobs/<id>/logs`, including the response's UTF-8 BOM and ANSI
escape bytes. The authenticated retrieval streamed those bytes without retaining raw files. There
is therefore no in-repository raw-log artifact locator, and the digests are not independently
replayable from repository artifacts alone.

These are three failure-diverse defects: one missing hosted TeX dependency, one invalid evidence
lifecycle, and one shell-coupled, environment-sensitive test harness around a deliberately
fail-closed production probe. Passing results from the other 42 jobs do not cancel any of them.

## Diagnosis and bounded corrections

### 1. Existing Libertinus PDF source lacked its hosted provider

The failing document already selects the Libertinus LaTeX wrapper. On the Ubuntu Noble hosted
image, `libertinus.sty` is provided by `texlive-fonts-extra`; the prior workflow installed related
TeX packages but not that provider. The correction pins the job to `ubuntu-24.04`, adds
`texlive-fonts-extra`, and raises its finite ceiling from 30 to 60 minutes without substituting
fonts or editing canonical TeX/PDF sources. Ubuntu's mutable Noble package record identifies
version `2023.20240207-1`, package size 614,365.4 kB, and installed size 1,731,869.0 kB
([Ubuntu package record](https://packages.ubuntu.com/noble/all/texlive-fonts-extra), observed
2026-08-01). At correction-design time those package facts justified headroom only. The later f6
run established `texlive-fonts-extra` availability but not PDF completion: it progressed past
Libertinus and then failed at the separate `gobble.sty` dependency reported below.

The KSG custody job is likewise pinned to `ubuntu-24.04` and its finite ceiling is raised from 240
to 360 minutes because the retained historical wrapper alone required less than but close to 175
minutes locally before the new outer suites and Rust gates. GitHub's mutable documentation lists
360 minutes as the default job ceiling and currently lists explicit `ubuntu-24.04` alongside a
26.04 preview label
([workflow timeout](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idtimeout-minutes),
[hosted runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners),
observed 2026-08-01). This is scheduling headroom, not evidence the job will finish. Pull-request
custody explicitly checks out `github.event.pull_request.head.sha`, following the pinned checkout
action's documented PR-head route, rather than GitHub's synthetic merge commit
([checkout scenario](https://github.com/actions/checkout/blob/9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0/README.md#checkout-pull-request-head-commit-instead-of-merge-commit),
observed 2026-08-01). The checker is not weakened to accept a merge.

The immutable Ubuntu 24.04 runner-image inventory revision recorded for this review lists Git
2.54.0 and cached Python 3.11.15
([runner image inventory](https://github.com/actions/runner-images/blob/5f2a66081d82b78ce32a6cae217b7efcbd9f3c09/images/ubuntu/Ubuntu2404-Readme.md)).
Those versions satisfy the checker's explicit Git 2.45 and workflow Python 3.11 lower premises.
The YAML image label does not freeze that inventory: only the exact hosted job log can establish
which image and tool versions a particular run actually received.

The first local nine-paper replay failed only at the foundational paper's absent local Lake cache;
it receives no full-set credit. A direct cache download then stalled and was interrupted, also with
zero credit. After the exact Lean manifest was compared with the preserved C3 cache source, that
cache was copied on write into this isolated worktree, `lake build` completed 2,213 jobs, and the
uninterrupted cross-toolchain wrapper completed all nine papers. The installed foundational PDF
remained SHA-256 `ee715576c2e3a8f058747b2d7ed97b99bc42c20c16bf07038e85f4887310553b`;
the mathematical-workflow PDF remained
`b283c69c5b8f05a57ef06e0db2c3d77b5a601e6149e5d9258e0995f30cd5aebf`.
Across that cross-toolchain replay and a separate read-only exact rebuild, both modes passed for all
nine PDFs, covering 186 pages in total. Poppler rendering and page-by-page inspection covered all
186 pages; the foundational paper's page 4 intentionally uses rotated landscape content. No
clipping, overlap, missing glyph, broken table, or layout defect was observed. In the committed
PDFs, all fonts were embedded/subset and had ToUnicode maps. The PDFs are untagged, so this is
bounded local source/artifact and visual evidence, not hosted package-availability evidence, proof of
mathematical truth, accessibility certification, or a general cross-toolchain rendering theorem.
The original hosted run still preserves no successful ninth-paper result.

### 2. The historical hostile suite was launched from the wrong lifecycle

The C3 phase checker supports a committed checkpoint, but its hostile self-test reconstructs and
mutates the reviewed precommit candidate. Starting that self-test from the already committed C3
tree erased the fixture delta. The four semantic differences reported by the audit were exactly:

- `HEAD`: parent-versus-checkpoint;
- lifecycle: `precommit-worktree` versus committed checkout;
- tracked changes: 16 versus 0; and
- untracked additions: 3 versus 0.

This was not attributed to Git 2.54 and did not falsify the previously passing normal/optimized
main checker. The correction introduces a pinned two-clone historical wrapper:

- a no-local clean C3 clone runs the exact C3 checker in normal and optimized isolated/no-site
  Python; and
- a second no-local clone starts from the exact parent, restores the exact 19-path C3 overlay,
  checks the frozen status and real/alternate indexes, and runs the historical checker and hostile
  suite in normal and optimized modes.

The wrapper pins the C3 parent, parent tree, checkpoint, checkpoint tree, exact status bytes and
digest, changed-path encodings and counts, and historical verifier source digests. Git ambient
routing and configuration are scrubbed. The historical sources remain immutable; the follow-up
does not rewrite the old checker or self-test to make the new lifecycle pass.

Two diagnostic wrapper launches reached the main checks and entered the long hostile self-test,
then were intentionally interrupted. They retain **zero** hostile-suite and **zero** full-wrapper
credit.

An earlier uninterrupted wrapper began at epoch `1785575428` and terminated with exit 0 before
the terminal observation at epoch `1785585918` (10,490 seconds is an observation-window upper
bound, not a stopwatch measurement). Both normal and optimized lanes rejected the frozen 351-case
aggregate and the wrapper ended with `committed=2/2; precommit=2/2;
hostile=normal+optimized`, exact parent `8b792bc143fff2d84f2d8e7817d1de7850741223`, checkpoint
`8fa6e992d9124229c7a175c4508bf10df336675a`, and tree
`059dc980d4a86066c07687188a452cf2459899eb`. That observation preceded the settled follow-up
source/custody endpoint and therefore has scoped immutable-anchor diagnostic value but zero final
candidate-wrapper credit. The aggregate is exactly
`44+18+44+8+9+16+21+34+17+5+11+18+76+30=351`; the printed fixed-pin-first and
deliberately-repinned 76 values are observations of that same 76-case group, not additional cases.
Loader 8, anti-fraud 107, review-ledger 85, parity 19 families/21 executions, descriptor 18, JSON 2,
Lean raw-transport 6, and self-reference 1 remain explicitly nested or separate. It does not close
the final historical-wrapper requirement.

A later final isolated replay did close that one historical requirement. It ran from a clean f6
clone and exited 0; its stdout is 9,488 bytes with SHA-256
`4d8d84bbecee03e751563bb1660aa4fe45f51ab40a431ba70b86c07abf8f2390`, and stderr is empty with
SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. The stdout file's
creation-to-final-mtime interval was `2026-08-02T09:26:58+0200` through
`12:16:10+0200` (2 h 49 min 12 s); this is a file-timestamp interval, not a monotonic stopwatch.
It contains both 351-case hostile-suite mode receipts and the final immutable-checkpoint line.
This grants exact immutable-C3 replay credit only; it does not authorize f6 or a later tree and
does not imply scientific, remote-authenticity, hosted-CI, or security success.

### 3. The Rust regression test coupled its race to unrelated subprocess behavior

The crate-visible production probe deliberately reads status, checks index visibility, reads
status again, and fails closed if any required Git observation is unavailable or inconsistent. The hosted log proves
that the old shell-wrapper test reached the fail-closed `git_unavailable` result; it does not reveal
which transient wrapper, workspace-root, or `HEAD` subprocess condition caused that unavailability.
It would be an overclaim to assign a more specific hosted root cause.

The correction factors the existing production sequence through a private helper and adds a
test-only callback immediately after the first status read. The regression test uses that callback
to change a tracked fixture deterministically and then verifies that the unchanged final status
reread reports `Dirty`. The crate-visible production entry still supplies an empty callback.
Production ordering, repeated status, index-visibility check, and fail-closed treatment of unavailable Git
evidence are unchanged; no retry and no acceptance of `Unavailable` was introduced.

The same Cargo feature and CLI selection as the hosted-failing `experimental-heuristics` job passed
locally, including all 51 `software_identity_build` tests. The corrected regression also passed 32
concurrently launched, same-host process repetitions; these are correlated stress observations,
not 32 independent routes. Targeted Clippy with warnings denied, Rust formatting, YAML parsing, Bash
syntax, ShellCheck, `just` formatting, and the hosted-like
`experimental-pipelines`/no-default-feature profile passed. These failure-diverse local checks
support the bounded harness correction, but do not reproduce the original transient subprocess
failure, establish source/binary timing identity, replace the full exact settled feature matrix,
or substitute for platform and all-green hosted replay.

## Direct-child custody boundary

The reviewed follow-up overlay is bounded to 13 paths: eight existing engineering/documentation
paths and five new custody/evidence paths. Its intended changes are the workflow dependency and
exact commands, deterministic Rust test seam, command documentation, changelog, this receipt, the
immutable-C3 replay wrapper, the outer checker/runner/self-test, and a digest-only rebind of
`scripts/check-certified-sxpid2-claim.py`. That rebind changes exactly the three mutable container
digests for the reviewed workflow, `justfile`, and scripts README; all frozen revision-1/2/3
authorities, evidence, formal/PDF bindings, semantic checks, and mutation logic remain unchanged.
The outer checker is required to bind the exact final modes, sizes, and SHA-256 values rather than
trust this prose inventory.

The custody design is intentionally acyclic:

- two separately constructed, failure-diverse alternate indexes (path-scoped `git add` versus
  captured-blob hashing plus `update-index`) yield the same tree, and a detached direct-child
  checkpoint binds the complete candidate; these remain correlated custody views because they
  share the clone, process, Git executable, object store, and source capture;
- the exact-source shell runner binds the checker and self-test source digests and executes captured
  bytes with `python3 -I -S` in normal and optimized modes;
- the checker binds the self-test and every other non-self allowed blob, while its own source and
  the runner are bound by the runner and external tree; and
- protected full-tree equality plus named science, formal/claim, and Cargo projections prevent an
  allowed engineering correction from silently importing later scientific work.

Every commit and tree object used by the gate is rehashed by the checker rather than trusting only
Git's object name. The tree parser first obtains and validates declared object size, then walks raw
objects recursively, rejects unsupported modes, noncanonical ordering, cycles, empty directory
objects, and explicit depth/object/byte/path bounds. Blob sizes and their aggregate logical budget
are approved before bodies are streamed through SHA-1/SHA-256. This is algorithmically distinct
from trusting `rev-parse`; it is not an external source of repository authenticity. The working
snapshot uses preflighted, capped, no-follow, nonblocking descriptor-relative reads; single-link
and canonical-mode checks turn symlink, hardlink, FIFO, and mode substitutions into rejections
rather than hangs or aliases.

The first 81-case V6 replay stopped at case 40 because both `git ls-files --others` and porcelain
status omitted an untracked FIFO; the checker therefore returned success before attempting a
nonblocking leaf read. That is a retained **real inventory counterexample**, and the entire V6 run
has zero credit. The correction adds a separate bounded, sorted, no-follow descriptor walk of
the worktree. It excludes only the validated root `.git` entry; requires the exact regular-file set
and every implied nonempty parent directory; and rejects undecodable/noncanonical names, extra or
empty directories, symlinks, hardlinks, FIFOs, sockets, and device nodes. This topology is captured
in the typed snapshot and repeated at the endpoint. Git inventory and filesystem topology are now
failure-diverse lenses rather than aliases of the same command.

The later 82-case V9 development replay also receives zero final credit. Its outer optimized
self-test was compiled with `-O`, but all 74 mutation-phase subprocess attempts silently used
normal Python because the mode default was never overridden. Its subprocess harness had no timeout
or output bound, mapped launch failure to synthetic return code 126, and accepted any nonzero or
signal result as a rejected mutation. In particular, making the exact-source runner non-executable
could earn false credit from an operating-system launch failure. The repaired self-test therefore
uses a required typed mode on every route, actively resets the dedicated interpreter's `SIGCHLD`
action to `SIG_DFL` before any `Popen`, verifies that invariant at each launch, applies bounded
pre-reap cleanup of the owned original process group, uses observe-only post-reap absence proof,
and retains typed harness failures plus case-specific return-code and stderr markers.
`mutation_target_family` values are bookkeeping
labels for correlated mutation targets; they are not counts of independent defenses or evidence.

A subsequent workflow-comparison draft redirected the four receipts to random files outside the
worktree, closed those producer descriptors, and reopened their paths for `cmp`/JSON validation.
That leaves a same-user replacement window and lets an unbounded producer fill disk before the
later receipt-size check. The draft is rejected with zero credit. The final workflow invokes a
single exact-source supervisor that retains capped pipe bytes in memory, enforces child deadlines,
signals the owned original process group only before its leader is reaped on exceptional paths,
requires explicit post-reap `ESRCH`, and compares the four child receipts without a reopenable
evidence path.

The private real index is bracketed before and after the complete inventory. Its no-follow
descriptor must name one regular link with safe non-executable permissions; the raw `DIRC` header,
version, entry count, SHA-1 trailer, and bounded size are checked, while Git's independent stage-zero
and `-v` views must match the exact HEAD tree with only `H` flags. Split-index routing and lock files
are rejected. Raw absence of `FSMN`, `link`, and `sdir` is deliberately a one-sided fail-closed
extension test: an incidental occurrence elsewhere in an otherwise benign index could reject it,
but an actual forbidden extension cannot pass. This route replaced a provisional boolean
`core.fsmonitor=true` query after that query created daemon metadata on macOS; the provisional run
and metadata observation receive zero credit. Git 2.45 or newer is required before any index read.
Outer checker/self-test Git children have explicit output and 60-second command bounds. Under the
hosted supervised route, each checker validation has a 300-second whole-validation deadline and
each child has its declared process deadline; the supervisor also has a finite child-suite
deadline. The standalone runner self-test route resets and verifies `SIGCHLD=SIG_DFL`, bounds child
I/O/deadlines, pre-reap owned-group cleanup, and post-reap absence retries but has no separate
whole-suite deadline, so its top-level ceiling must come from its caller or hosted job.
Local configuration plus Git/common/private-index paths are endpoint-bound. The private index
itself is descriptor-checked before `--shared-index-path` or any other index-reading Git command, so
a symlink, hardlink, directory, FIFO, or socket substitution cannot enter Git first.

The exact-source runner freezes the declared checker or self-test size and SHA-256 before opening a
no-follow/nonblocking leaf reached by a descriptor walk from `/`, bounds the capture at 262,144
bytes, verifies the captured bytes against those declarations before compilation or execution,
executes only those bytes with isolated/no-site Python and neutral loader/spec/cache fields, then
freshly walks `/` through every physical ancestor and compares directory device/inode/type before
reopening and bounded-comparing the leaf. Directory identity intentionally excludes
child-list size and timestamps so unrelated sibling creation cannot create a false race failure;
the leaf retains the full size/time/link identity and bracketing comparisons. The canonical receipt
separates externally supplied tree/checkpoint custody from `diagnostic_pass_no_credit`, binds the
real-index and local-config digests, and explicitly withholds Bash/PATH, Python standard-library,
dynamic-loader, concurrent-metadata, hosted-CI, scientific, and security conclusions.

These are application-visible limits, not a hard process-RSS or denial-of-service theorem. They do
not bound Git's internal allocation/decompression, kernel buffers, filesystem/backend liveness, or
the historical shell wrapper's individual children. The hosted historical wrapper instead has the
job-level 360-minute cancellation ceiling; it does not claim portable process-group cleanup.
The dedicated verifier requires reviewed GIL-enabled CPython 3.11 through 3.14, the main and only
enumerated Python thread, and actively replaces any inherited `SIGCHLD` action with `SIG_DFL`
before its first `Popen`. It verifies that disposition before every launch; this clears inherited
`SIG_IGN`/`SA_NOCLDWAIT` auto-reap semantics needed for the local ownership argument. It also
requires unblocked and unpending `SIGALRM`/`SIGINT`, installs nonraising fixed-slot recorders, and
holds a typed LIFO `pthread_sigmask` capability from before `Popen` through leader reap, post-reap
`ESRCH`, pipe/selector closure, and prior-mask restoration. Deferred flags are adjudicated only at
explicit child-free or complete-cleanup safe points. The fork child unblocks the pair in
`preexec_fn`; [Python documents that hook as unsafe in the presence of
threads](https://docs.python.org/3.11/library/subprocess.html#subprocess.Popen), so absence of
unenumerated native threads is an explicit unauthenticated premise, not an inferred fact. Other
signal dispositions and masks are neither normalized nor authenticated. On an exceptional path the
outer supervisor can signal descendants only while `Popen.returncode` remains unset under the
no-external/native-waiter premise.
After any leader reap, it sends no nonzero signal and accepts only explicit `ESRCH` within the bounded retry; persistent
`PRESENT` or `EPERM` fails closed without attempting reclamation. A retained counterexample moved
a grandchild to a new process group with
`setpgid(0, 0)` while keeping it in the launched session, closed the captured pipes, and survived a
successful leader exit. Therefore no containment of deliberate process-group or session escape is
claimed.
The source/path endpoint bracket also does not defeat a same-user ABA actor that transiently swaps
an alternate repository into the live `__file__` path during execution and restores the original
physical chain before the endpoint walk. Deterministic size, digest, replacement, and race attacks
cover narrower failures; concurrent same-user exclusion remains an explicit premise.

The final gate must also reject path additions/deletions, mode or link substitutions, protected
blob changes, staged-index contamination, replacement/graft/alternate-object overlays, forbidden
configuration overlays,
wrong parents or descendants, signatures or identity changes, command weakening, source-loader
substitution, and normal/optimized receipt divergence. The settled source inventory contains 109
deterministic hostile cases in 18 bookkeeping families. Its accounting declares 88
mutation-attributable verifier-target launches (86 checker and two self-test launches); 22 of the
109 are local-receipt cases with no target launch, while 38 separately named harness controls are
outside both the 109-case and 88-launch counts. Before the terminal hosted replay, those counts
were source-inventory facts only. The exact-f6 hosted run later executed both Python modes as
recorded below; any source change reopens both inventory and execution credit, and no result
transfers to f7.

### Retained outer repair counterexamples

Focused success never overrides a later falsifier. The following post-V9 counterexamples and
superseded executions permanently retain zero credit. Their repaired exact-f6 boundaries later
passed in both Python modes where stated below; that new execution does not transfer credit
backward or to f7. At this point in the chronology, the restrictive-caller f7 wrapper replay was
still pending; only the later terminal one-shot run recorded below closes that bounded local
requirement:

- After the workflow switched to the supervisor, the hostile
  `workflow_bypass_exact_source_runner` constructor still searched for the deleted normal-checker
  command. It aborted before invoking the checker, so it tested neither the blob nor workflow
  boundary.
- The first child-receipt comparator checked mode equality but did not bind the child suite's
  reconstructed tree or declared checker/self-test sizes and digests to the outer runner state.
  The first repair then incorrectly equated the child's deterministic fixture checkpoint with the
  real outer checkpoint. Those are distinct roles: the child tree and C3 parent must match the
  outer candidate, its internal fixture checkpoint must be a well-formed value adjudicated by the
  child lifecycle, and only the outer checker binds the real commit envelope. Forcing equal OIDs
  would either false-reject an honest current-time commit or encourage false commit-time metadata.
- On Darwin, the optimized output-overflow harness once raised `EPERM` while probing an already
  terminated original process group; a subsequent process listing found no member. A later
  2,000-launch `/usr/bin/true` control using `start_new_session=True`, `wait()`, then
  `killpg(pid, 0)` independently observed one transient `EPERM` despite that workload spawning no
  descendants. Those are false rejections, not cleanup evidence. Mapping `EPERM` to presence and
  signaling after `wait()` also risked targeting a reused numeric group. The correction uses typed
  absent/present/indeterminate states, retries post-reap only to explicit `ESRCH`, never signals
  after `Popen.returncode` is set, and has deterministic exact-helper controls for transient and
  persistent states. Separately, the explicit `setpgid(0, 0)` grandchild above is a true escape
  from the original group and proved the earlier "launched session" wording false.
- A still-deeper counterexample set `SIGCHLD=SIG_IGN`, launched an isolated `/usr/bin/true`, and
  observed `Popen.returncode is None` after the kernel had already auto-reaped the child and
  `killpg(pid, 0)` returned `ESRCH`; a later `poll()` merely filled in return code zero. Thus
  `returncode is None` alone was not an ownership token, and the prior pre-reap signal rule could
  target a reused numeric group under inherited `SIG_IGN` or `SA_NOCLDWAIT`. The repaired exact
  checker and self-test actively install `SIG_DFL` before any `Popen`, check it again immediately
  before every launch, and run a deterministic inherited-`SIG_IGN` counterexample/reset/spawn
  control in both Python modes. This normalizes `SIGCHLD` and the explicitly owned
  `SIGALRM`/`SIGINT` lifecycle only, not all signal actions or masks.
  Two full exact-source self-test groups on the superseded pre-reset bytes (resolved process-group
  IDs `62336` and `62337`) were terminated after this falsifier arrived; their interrupted outputs
  receive zero credit and are not represented as completed hostile runs.
- The initial rejection classifier accepted a checker marker followed by unrelated text, an
  argparse error with an injected line, an unrelated traceback ending in the expected size-error
  suffix, and an arbitrary `OSError` mentioning the checker basename. Substring/suffix agreement
  is not proof that the intended boundary rejected a mutation.
- The checker's first bounded `cat-file --batch-command` session set its `finished` flag before
  deadline, trailing-output, stderr, and wait checks completed. A separate monkeypatched
  sleeping child made `finish()` fail after that assignment; `abort()` then skipped termination,
  and the owned process remained alive until the reviewer killed its process group. Constructor
  failures after `Popen` had a related cleanup hole.
- A later real-signal falsifier delivered `SIGALRM` after a replacement `Popen` returned a live
  child but before the caller published the handle. The then-raising Python handler unwound the
  constructor with no cleanup authority. This invalidates provisional tree
  `71fdb8dcf1ec7f304a04d93aeae9e20a61df4ea7` and every earlier 109-case receipt, even where all
  reported cases passed. The repair uses nonraising terminal flags plus a mask capability; real
  `SIGALRM` and `SIGINT` controls now require complete child, selector, pipe, and mask cleanup before
  the deferred error is surfaced.
- Transactional probes then found that the first handler installation could succeed while the
  second failed, a `pthread_sigmask` wrapper could change the kernel mask and then raise, failed mask
  restoration could discard its only live capability, and out-of-order nested restoration was not
  explicitly tested. Independent controls now require rollback of both handler dispositions,
  retained fail-closed depth on an unproven restore, and exact LIFO recovery. A separate injected
  timer-disarm failure proves handlers are not restored until zero timer state is observed.
- `GitCatFileSession.__enter__` could raise after construction even though Python would not call
  `__exit__`; selector error formatting could itself fail before pipe/mask cleanup; and one `wait()`
  exception could skip the second reap observation. The repaired session owns local process,
  selector, and mask references before publication, aborts inside a failing `__enter__`, stores raw
  cleanup exceptions until every close is attempted, makes two bounded reap attempts, and performs
  only signal-free group observation after a published reap.
- Ordinary `fstat` failures immediately after `open` exposed unretained descriptor windows in the
  first exact-source/bootstrap draft, while sequential close loops could skip later descriptors.
  Every just-opened directory/leaf is now retained before its first metadata query, all close loops
  attempt every descriptor, and close failures retain rather than replace an initiating exception.
  Hard OOM between native side effects and Python publication is not claimed recoverable.
- A hostile replacement of `subprocess.Popen` can start a child and raise without returning its
  handle. The caller cannot identify that process from the exception, so arbitrary standard-library
  mutation is an explicit nonclaim rather than a fabricated containment theorem. Likewise, direct
  external/native waiters, deliberate process-group escape, `SIGTERM`/`SIGHUP`/`SIGKILL`, and
  unenumerated native threads remain outside the proved lifecycle premise.
- The first independent source-loading probe omitted `-B` and created an ignored `__pycache__`
  artifact. That cache was quarantined outside the worktree, the tree was rechecked, and the probe
  earns zero credit. Subsequent review loads use byte capture/`compile` under isolated Python and
  explicitly verify that no cache or ignored entry appeared.
- During the first repaired 38-control normal/optimized executions, an unrelated local Lean version
  probe created the ignored but empty `audit/formal/lean/.lake/packages/` directory. Both suites
  happened to exit 0, but the concurrent ABA contamination makes both receipts zero-credit. The
  Lean process group was terminated, the cache was moved recoverably to
  `/private/tmp/pid-rs-c3-lake-contamination.ItdBte`, and an ignored/cache census returned empty
  before any replacement run. No result from those executions is transferred.
- The next normal and optimized replacement executions were launched from a clean, cache-free
  source tree under caller `umask 077`. Both failed before any hostile case because Git propagated
  that umask into the self-test's private anchor checkout and the checker correctly rejected
  `.claude/settings.json` mode `0600` instead of canonical `0644`; both stdout files were empty and
  both 156-byte stderr files had SHA-256
  `6c8b5830f9063a94eaff77bf761423f77c4f92c9d5c9d4fd5005b22948078765`. These identical setup
  failures have zero mutation or harness credit. The exact-source runner now normalizes only its
  child-process umask to `0022`; `TemporaryDirectory` still creates the containing scratch root as
  `0700`, and existing source modes remain subject to exact checking. A replacement run under the
  same restrictive caller umask was therefore required. The later terminal one-shot run below
  supplies that bounded execution; these two failed predecessors retain zero credit.
- The first supervisor normalizer accepted two identical but hollow child receipts containing only
  a mutation count and empty harness/lifecycle objects. Mode equality cannot substitute for exact
  nested receipt authority. The earlier label `mutation_process_attempts=83` was also too broad.
  The current 109-case source inventory instead names 88 mutation-attributable verifier-target
  launches (86 checker and two self-test launches); its 22 local receipt mutations launch no
  verifier target.
  Git fixture subprocesses, 38 explicit harness controls, and positive-lifecycle checker launches
  are outside that launch count. At that stage these were source-inventory facts, not execution
  credit. The later terminal exact-f6 run supplied the bounded execution credit reported below.
- Independent review rejected self-test source
  `b9b6c351f65c3392113d7825be60db583d0076e183a678ee35fbf9369414108c` and detached commit
  `a5aa366a258fe95242d6015e61ff4477d2e806e2`:
  timeout/output controls accepted their expected primary exception even when process-group cleanup
  failed, because the cleanup failure was attached only as a note. That tree, commit, replay, and
  receipts have zero final credit. The correction promotes group-cleanup failure over the initiating
  exception, rejects any expected-class control carrying cleanup diagnostics, and injects a failure
  after real cleanup under both timeout and output-overflow paths. The combined adequacy control is
  separately named, raising the harness-control inventory from 37 to 38 without changing the 109
  mutation cases, 18 bookkeeping families, or 88 mutation-attributable verifier launches.
- `git rev-parse --is-shallow-repository` returning `false` proves only that Git reports a
  non-shallow repository; it does not exclude partial/promisor routing or prove complete reachable
  history. Exact objects used by this gate are individually framed and rehashed. Any stronger
  history-availability statement must additionally reject or account for promisor state; it cannot
  be inferred from the shallow bit.

These findings came from different mechanisms: live process behavior, synthetic classifier
counterexamples, source-state inspection, receipt-model mutation, and Git model review. They are
not independent statistical replications, but neither are they collapsed into one passing lens.

## Frozen scientific surface and non-implications

The correction is constrained not to change estimator implementations, estimator constants,
formal theorem statements or proofs, formal/certificate corpora, mathematical claim packets,
method definitions, release scientific scope, canonical PDF sources, or committed PDF artifacts.
That constraint must be demonstrated by exact tree/blob projections and final verification; it is
not inferred from filenames or reviewer intent.

### Pre-existing protected formal-surface defect

Independent mathematical review found one pre-existing cross-artifact defect, present in the
protected paper since commit
[`d16e166fe80536e36a3efe5552460a0327d80a83`](https://github.com/sepahead/pid-rs/commit/d16e166fe80536e36a3efe5552460a0327d80a83).
The canonical [Markdown](../../SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md) and frozen
[claim-v2](../../claims/SX-SUPPORT-FREE-CONTINUITY-001/claim-v2.md) correctly introduce the barred
statistical-transfer envelopes only for `K >= 2`. The canonical
[TeX](../formal/latex/support-change-tolerant-averaged-sxpid-continuity.tex) and
[PDF](../../output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf) Section 8
transcription omits that premise while its global setup permits `K = 1`. An earlier exact-envelope
paragraph correctly notes that `K = 1` forces total-variation distance `eta = 0`; the later transfer
section nevertheless defines bars containing `log((K - 1) / epsilon)` and
`log(floor(K^2 / 4) / epsilon^2)` for a conservative positive radius, then asserts
`A = K - 1 >= 1` and `B = floor(K^2 / 4) >= 1`. Those expressions and assertions are invalid at
`K = 1`.

This does not falsify the closed-simplex continuity theorem, whose one-cell case is trivial; it
does invalidate the unqualified printed statistical-transfer bars and table at `K = 1`. Exact and
cross-toolchain wrapper reproducibility reproduced the protected artifacts but did not establish
cross-artifact semantic parity or mathematical validity. The protected TeX/PDF are intentionally
unchanged in this engineering child. The immediate post-C3R science/PDF milestone must add the
missing `K >= 2` premise and an explicit singleton zero branch, regenerate the PDF, and renew the
projection, checker, paper, and cross-artifact review. Until that occurs, this receipt grants no
blanket mathematical or PDF-content GO.

Even after the engineering gates pass, this follow-up by itself will not establish:

- correctness, consistency, bias, calibration, convergence, or support validity of KSG;
- correctness or a mapping theorem for continuous Ehrlich PID, categorical MGW shared-exclusions
  PID, `I_min`, fitted quantized PID, heuristics, mixed-dimensional PID3, or wrappers;
- transfer of any result among those distinct estimands and implementations;
- mathematical validity merely from PDF compilation, or PDF identity merely from source intent;
- binary64 equality across platforms, statistical power or uncertainty calibration;
- compatibility, authenticity, provenance beyond the bounded Git evidence, or a transparency log;
- package, release, downstream, or hosted-platform qualification; or
- absence of vulnerabilities, secrets, supply-chain defects, or security alerts.

## Security receipt

CodeQL [run `30688494457`](https://github.com/sepahead/pid-rs/actions/runs/30688494457)
completed successfully for the exact C3 commit, with all four analyses successful:
[actions job `91338863331`](https://github.com/sepahead/pid-rs/actions/runs/30688494457/job/91338863331),
[JavaScript/TypeScript job `91338863313`](https://github.com/sepahead/pid-rs/actions/runs/30688494457/job/91338863313),
[Python job `91338863343`](https://github.com/sepahead/pid-rs/actions/runs/30688494457/job/91338863343), and
[Rust job `91338863352`](https://github.com/sepahead/pid-rs/actions/runs/30688494457/job/91338863352).
That is execution evidence, not an alert disposition. [Retained in-repository
evidence](ksg-rev4-public-ci-run-30431352389-failure.json) binds a six-field projection retrieved at
`2026-07-29T08:04:23Z`: it is 16,315 bytes, has SHA-256
`69fb93eb779a87cbc639193b00521877dc07f83568ff5de04b1c0aedcfc2ad7e`, and records 85 open alerts
(19 critical, 66 high). A same-session 450,549-byte raw API array with SHA-256
`67be540405ea12fea27a38f2b64c421f53c74acbb504c54e75f889b836d69527` was observed, but that raw
payload has no in-repository artifact locator; its digest records ephemeral custody only and does
not claim settled repository preservation.

An earlier correctly quoted and paginated query at `2026-08-01T11:17:20Z` produced the counts
below, but its exact invocation and response bytes were not retained; it is only corroborating count
evidence. The superseding authenticated query requested
`GET https://api.github.com/repos/sepahead/pid-rs/code-scanning/alerts?per_page=100` through
`gh api --paginate --slurp` from `2026-08-01T15:34:55Z` through `15:34:58Z`. It returned 132
records in two pages and the following mutable repository snapshot:

```text
open alerts:      86
  critical:       20
  high:           66
dismissed alerts: 46
fixed alerts:      0
```

The exact two-page GitHub CLI slurp serialization was 779,718 bytes with SHA-256
`90186906056dcbb7d8d79c4aaf2fdf57b1e6d197029c7218c36ef68dfba2d55c`. That digest domain is the
CLI's JSON-array serialization, not raw HTTP-page bytes. A canonical projection sorted by alert
number encoded objects with exactly the fields `created_at`, `most_recent_commit` (from
`most_recent_instance.commit_sha`), `number`, `rule_id`, `security_severity` (from
`rule.security_severity_level`), and `state` as compact sorted-key UTF-8 JSON plus LF. It was 25,375
bytes with SHA-256 `ce8ba8a30f12b8d6cc67bc5a08cc7fcc752bfe8ffd983e07e00ae9e5474ee632`.
Both byte streams were deleted after hashing and have no in-repository artifact locator; their
digests are ephemeral and are not independently replayable from repository artifacts. A preceding
14:59 retrieval fetched data but its local summary crashed while comparing `None` with string sort
keys; that route has zero evidentiary credit.

Accordingly, the accurate statement is **CodeQL workflow execution succeeded**. It is not a
security-clean result, not an adjudication of the 86 open alerts, and not evidence that dismissed
alerts were correctly classified. [Alert `#132`](https://github.com/sepahead/pid-rs/security/code-scanning/132)
is the newly detected open `py/code-injection` finding at
`scripts/check-lean-descriptor-factorization-self-test.py:183`, created
`2026-08-01T06:51:08Z`; detection by the exact-C3 analysis is not proof that C3 introduced it, that
it is exploitable, or that it is a false positive. An immediately preceding unquoted zsh API path
glob failed; its meaningless zero summary has zero credit. This follow-up cannot claim a security
gate until the separate authorized security process adjudicates or remediates the open alerts.

## Retained f6 hosted failure and the next bounded correction

The settled follow-up implementation is unsigned commit
`f6fde520b841c61b7752cdd053af59bda763d3d1`, tree
`1ce2d75081bf85d9a30da180539c162a2c5a5c86`, with sole parent
`8fa6e992d9124229c7a175c4508bf10df336675a`. Exact push run
[`30743459839`](https://github.com/sepahead/pid-rs/actions/runs/30743459839), attempt 1,
executed that SHA. It cannot receive all-green credit: job
[`91484882912`](https://github.com/sepahead/pid-rs/actions/runs/30743459839/job/91484882912),
`Formal LaTeX / PDF inventory and cross-toolchain structure`, completed with `failure`. The job
started at `2026-08-02T10:18:54Z` and completed at `10:22:31Z`; its rebuild step ran from
`10:21:49Z` through `10:22:29Z` and exited 1. The 2,952-byte job-API response retrieved from
`10:43:08Z` through `10:43:10Z` has SHA-256
`2a56aeeb81655d0d284d1d4577adc64739359292631bbc2ab593879523a6c3bf`. It is retained outside
the repository at `/private/tmp/pid-rs-f6-pdf-failure-retry.UDzBDg/job-91484882912.json`; that
ephemeral path is not a repository artifact, external archive, or transparency log.

The first redirected log retrieval failed during its TLS handshake and has zero byte-custody
credit. A later uninterrupted `gh api repos/sepahead/pid-rs/actions/jobs/91484882912/logs`
retrieval ran from `2026-08-02T10:42:37Z` through `10:42:50Z`. Its exact output is 76,753 bytes,
SHA-256 `6c72da56e383a42a9d5d57535a818e10f2fd1d75708eed27093926f24c9fee65`, retained only at
`/private/tmp/pid-rs-f6-pdf-failure-retry.UDzBDg/job-91484882912.log`. The digest domain is the
GitHub CLI's post-redirect response body. The local path and colocated digest are preservation and
change-detection evidence, not authentication or independent replayability.

That log proves `texlive-fonts-extra` installed successfully and repaired the earlier Libertinus
failure. Seven preceding PDF gates then completed, including the foundational paper. The next
mathematical-workflow build stopped at exactly `LaTeX Error: File 'gobble.sty' not found`, followed
by `mathematical workflow PDF check: LaTeX build failed`. The apt transaction listed
`texlive-plain-generic` among packages not installed under the explicit
`--no-install-recommends` command. Ubuntu Noble's package inventory places `gobble.sty` at
`/usr/share/texlive/texmf-dist/tex/generic/gobble/gobble.sty` in
[`texlive-plain-generic`](https://packages.ubuntu.com/noble/all/texlive-plain-generic/filelist).
The bounded correction therefore adds that package; it does not edit a TeX source or substitute a
PDF. Package metadata is mutable, and only a new hosted run can show that the dependency is
available and all nine papers complete on the selected image.

A separate read-only dependency-closure audit mapped all nine TeX sources and the shared local
style. [Upstream Markdown 2.23.0](https://github.com/Witiko/markdown/tree/2.23.0) requires both
`gobble` and the later strike-through dependency `soulutf8`; Noble's `texlive-plain-generic`
inventory supplies both files. [Noble's `texlive-latex-extra`
inventory](https://packages.ubuntu.com/noble/all/texlive-latex-extra/filelist) supplies the already
reached Markdown/FVExtra/CSV/Paralist support, and f6 had already loaded or executed the remaining
base, recommended, pictures, binary, font, Poppler, and wrapper dependencies. The unreached ninth
paper introduces no package family absent from earlier successful f6 papers. This finds no
predictable next missing package; it is not a compilation pass and cannot prove warning freedom,
PDF text/geometry equality, font embedding, or future runner-image stability. Those claims remain
reserved for the exact successor hosted run.

A clean f7-clone macOS replay supplied a narrower pre-push lens. The shared style gate and its six
mutations passed, as did the first six paper gates. The set wrapper then correctly exited 1 before
the foundational paper because this clone has no `audit/formal/lean/.lake/packages`; borrowing a
different lane's dependency tree was rejected as contamination. Individually running the later
mathematical-workflow and support-change-tolerant gates also passed, so eight of nine current paper
scripts rebuilt warning-free and cross-toolchain structurally equivalent. The foundational paper
was not freshly adjudicated in this clone, the whole-set attempt has no green credit, and neither
result transfers Noble package availability. `git diff` confirms that f7 changes no TeX or PDF
path. The earlier complete local 186-page replay and exact-f6 hosted foundational pass remain
separate observations; the successor must build its own pinned Lake tree and pass the whole set.

Run `30743459839` is now terminal. It was created at `2026-08-02T10:17:44Z`, updated at
`11:53:02Z`, and completed with `failure`: the paginated jobs response reports exactly 45 jobs,
all terminal, with 44 successes and the single PDF failure above. In particular, KSG job
[`91484882859`](https://github.com/sepahead/pid-rs/actions/runs/30743459839/job/91484882859)
completed successfully from `10:17:47Z` through `11:53:01Z`; its exact-phase-envelope step ran
from `10:29:13Z` through `11:50:29Z` and succeeded. This closes the observation without changing
the run's red disposition. KSG subjob success cannot erase the PDF failure or establish KSG
science, PID validity, publication validity, security cleanliness, or cross-platform identity.

The terminal capture is retained outside the repository at
`/private/tmp/pid-rs-f6-hosted-terminal.kn2HyT`. Its 12,098-byte run record has SHA-256
`29dc6f84ae8d08bb5cedc055a0e44842df1bf4cc27971d732dbfbde9b437a99d`; its 144,143-byte jobs
page has SHA-256 `78d2702e8adc45172088e01719e33ebca5f99840d2669b059f57c0b58ef4e297`;
and its 3,812-byte KSG job record has SHA-256
`670b93dcc723c8ad48d1758591b19d7a9c68ea5f03b4338b4e82fa8ba86514e0`. The uninterrupted
116,489-byte KSG log has SHA-256
`b580d0e763f6c1df2966d0403606bfae0bd6a02ce4184f8dbd4aec5da721a919`. The manifest and its
per-file checksum list have respective SHA-256 values
`ee44e1b801af721b85c4490b7b593b3da502795038d294a44c070b66cdb4d068` and
`1e8a2447aa4a2aef3a88dc0902290acaba26589faf8f86fd0772274fea1ae00c`; a checksum replay passed.
The bounded main-ref observations before and after capture both named exact f6, but that equality is
not an atomic-history or immutability result. The capture manifest records two transient polling
TLS failures and an initial zero-output PDF-record attempt as zero-credit negatives; it also records
that no security endpoint was queried in this terminal-capture lane. Those operator observations
are not inferred from the finite successful response files themselves.

The KSG log records the 351-case hostile suite passing once in normal mode and once under
optimized Python. It also records a successful exact-f6 mode-comparison receipt: checker receipts
were byte-identical with SHA-256
`9572baec58747384e22a832b9b757253875af897d7f09dc096c116797380ce2c`, and the outer
exact-source self-test passed a 109-case mutation suite across 18 bookkeeping labels. It reports 88
mutation-attributable verifier launches (86 checker plus two self-test launches); 22 of the 109 are
local-receipt cases with no target launch; and 38 separately named harness controls are outside the
109-case and 88-launch counts. Those counts describe finite, correlated deterministic controls
rather than independent replications or exhaustive security coverage. They close the exact-f6
bounded mutation execution that was previously open; they do not transfer to the f7 wrapper or its
eventual descendant.

The separate exact-f6 CodeQL run
[`30743459484`](https://github.com/sepahead/pid-rs/actions/runs/30743459484), attempt 1, completed
successfully at `2026-08-02T10:20:13Z` for exact head
`f6fde520b841c61b7752cdd053af59bda763d3d1`. Its four completed analyses were Rust job
`91484882885`, JavaScript/TypeScript job `91484882913`, Actions job `91484882927`, and Python job
`91484882943`. This is exact-f6 analysis-execution evidence only. It does not transfer the earlier
C3 alert snapshot, adjudicate an alert, or establish security cleanliness. A mutable query-time
observation found 87 open ref-scoped code-scanning alerts; repository-level Dependabot and
secret-scanning queries each returned zero open alerts. Those endpoint scopes are not
interchangeable, and repository-level results are not attributable to f6 merely because `main`
equaled f6 during the query. These mutable observations are separate from—and neither contained in
nor corroborated by—the terminal CI bundle above; they receive no security-gate credit. The first
secret-scanning request also omitted `hide_secret=true`; its empty response exposed no secret
value, but that unsafe request is unpromoted and must be replaced by a privacy-safe successor
capture with raw scoped custody.

The f6 workflow's outer gate derived its candidate tree and checkpoint from current `HEAD`. That
command is intentionally invalid at a later descendant: the checker requires exactly one direct
child of the C3 anchor and requires the supplied committed checkpoint to equal its evaluated
`HEAD`. The correction does not expand that acceptance set. Instead, the immutable C3 wrapper now
creates a third no-local clone, checks out exact f6, rejects alternate/graft/shallow/replacement
routing, and invokes the f6-owned digest-bound supervisor with the exact f6 tree and checkpoint.
This supplies historical conformance of f6 only. The new descendant remains unadjudicated until a
separate acyclic receipt binds its tree, push, hosted run, and honest security observations.

A first full execution of the extended wrapper was deliberately terminated and receives zero final
credit after a distinct restrictive-umask probe exposed a portability defect in the wrapper itself.
With caller umask `077`, Git materialized the three frozen f6 runner/checker sources as mode `0700`;
the exact-source bootstrap then exited 1 at its intended `exact-source leaf has noncanonical
permissions` refusal point. The interrupted run exited 143 after a targeted `SIGTERM` to its
verified private process group; its partial stdout is 2,582 bytes / SHA-256
`643b20e2055cf3df8bf7f529e32a45a51a123d425c14c7aa7c08862f58753224`, and its 15-byte stderr
(`Terminated: 15` plus newline) has SHA-256
`ed9c25996224e994b23a6681b4fa359c4224ae02bbf8fa3835e6d1c147257e3a`. Those files are retained
only under `/private/tmp/pid-rs-f7-extended-wrapper.4j0odf/`. The correction now sets umask `022`
before any clone, matching the frozen runner's canonical `0644`/`0755` permission contract while
leaving the private `mktemp` root owner-only. A bounded positive mechanism probe began with caller
umask `077`, applied that normalization, observed all three f6 verifier paths at mode `0755`, and
reached an exit-zero diagnostic checker at `/private/tmp/pid-rs-f7-umask-positive.6YYvlS/worktree`.
The diagnostic receipt is explicitly no-credit. The first replacement full replay started under
caller umask `077` at `2026-08-02T11:40:25Z`, but did not survive the conversation/tool-session
interruption. Its 5,217-byte partial stdout has SHA-256
`03d436911f46f20749f3726e6cd4f3880729c0d86ee3d68484e8998db2b5c772`; stderr is empty; no
terminal-status artifact exists; and no process remained when custody resumed. It had completed the
normal hostile lane and entered the optimized lane, but receives zero whole-run, terminal, or final
credit. A detached `nohup` replacement was reaped before launch metadata, and a `launchctl submit`
mechanism test failed closed under launchd's minimal `PATH` because Apple's older Python lacks
`sys.flags.safe_path`; both are separately retained zero-credit launcher negatives.

The sole creditable replacement was the one-shot LaunchAgent
`org.pidrs.c3f7.20260802t1552`. Its supervisor inherited umask `022`, deliberately applied
wrapper-invocation umask `077`, started the wrapper at `2026-08-02T13:52:33Z`, and ended with
wrapper exit 0 at `21:46:54Z` (a 28,461-second wall interval, not a CPU-time claim). Exact `HEAD`
remained
`f6fde520b841c61b7752cdd053af59bda763d3d1`; the wrapper SHA-256 remained
`c81c5600bea1080ded89681acf46be5b0884b574308ad36bc05f52b9b92c83db`; and the pre-run/post-run
status projection remained
`f1c48722036e471a5f902cb2cdb696fccf05569a8b4e23613b452ff5095bf931`. Its 44,356-byte stdout
has SHA-256 `76c72729cb591694e66bfdcfeb9bcc0eb5c51d4fa4944618996d7e3dbd38f109`, and stderr is empty with
SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. The checker receipts
were byte-identical across normal and optimized Python
at SHA-256 `ed2cbd939c5bc6f0e1f5e16bd7bb839e978e0b3087a18cb82a61db773249c3f6`; deleting only the
recorded mutation-target Python mode also left the normalized self-test receipt byte-identical. The
run executed all 109 deterministic cases in 18 bookkeeping families: 88 mutation-attributable
verifier-target launches (86 checker plus two self-test), 22 local-receipt cases, and 38 separately
named harness controls outside both counts. Its final external-tree/checkpoint receipt passed at
exact f6 tree `1ce2d75081bf85d9a30da180539c162a2c5a5c86`, parent
`8fa6e992d9124229c7a175c4508bf10df336675a`, with 552 protected paths, endpoint equality, framing
and rehashing of the exact traversed anchor/candidate/checkpoint objects, and 33 explicit
non-implications. These are finite, correlated, bounded local custody and mutation-execution facts
for immutable f6. They do not adjudicate the eight-path successor, complete reachable history or
object-store coverage, hosted CI, PDF content, KSG or PID science, authenticity, or security
cleanliness.

The bounded successor overlay contains exactly eight modified paths: the workflow, immutable
wrapper, AGENTS command guide, scripts README, `justfile`, changelog, this evidence record, and
`scripts/check-certified-sxpid2-claim.py`. The direct f6-only commands are removed from the current
`just ksg-revision` recipe because the immutable wrapper already supplies that exact lifecycle and
the direct checker correctly rejects a descendant. The claim-checker edit only rebinds the complete
workflow, `justfile`, and scripts-README container digests required after those files changed. Its
extracted certified-job and recipe command slices, revisioned scientific authorities, semantic
checks, fixtures, formal sources, and PDFs remain unchanged and are rechecked by the ordinary and
optimized claim gate plus its mutation suite. This is a custody-container transition, not a new
SxPID2 result.

A fresh f7-clone local pre-push sweep completed successfully after the receipt correction: format;
stable workspace tests excluding the PyO3 crate; pid-core no-default, parallel, all-feature debug,
and all-feature release tests; clippy over the workspace/all targets/all features with warnings
denied; no-default pid-core and all-feature workspace rustdoc; docs.rs-style pid-core and
pid-runlog rustdoc; Bash syntax; ShellCheck; `just` formatting; workflow YAML parse; Markdown-math
gate plus 17 mutation cases; certified-SxPID2 claim checks in normal and optimized Python plus 111
mutations per mode; and `git diff --check`. These executions cover unchanged Rust/scientific bytes
and the current eight-path overlay locally; they do not transfer platform, hosted, Python-binding,
PDF, or science credit. Generated `target/` and Python bytecode caches were moved recoverably to
separate `/private/tmp` quarantines. The subsequent ignored/cache census is empty and the overlay
still contains exactly the eight named paths.

The earlier “actionlint unavailable” observation remains a zero-credit tool-absence negative. A
later official-release-API query selected the [official actionlint `v1.7.12`
release](https://github.com/rhysd/actionlint/releases/tag/v1.7.12) for Darwin arm64. The 2,164,202-byte
archive's API digest, downloaded checksum-file entry, and local SHA-256 all agree at
`aba9ced2dee8d27fecca3dc7feb1a7f9a52caefa1eb46f3271ea66b6e0e6953f`; the checksum file itself
agrees with its API digest
`433028cf0ba3c42163ea1a668dedce30fcdbe84fe912b1a5e288c006eab8a4f5`. The extracted Mach-O
arm64 binary reports actionlint 1.7.12 built with Go 1.26.1 and has SHA-256
`8db11704dc296f096216db4db65d86cd7f0ebfdf4c38453a1da276b137b88388`. Its first exact-workflow
run exited 1 on pre-existing ShellCheck style finding `SC2005` at the Z3 setup's
`echo "$(dirname ...)"`; that negative is retained. Replacing the command with direct `dirname`
output is behavior-preserving, removes the finding, and actionlint then exits 0. The certified
workflow-container digest is rebound and the normal/optimized claim checks plus both 111-mutation
self-tests pass again. Release API, checksum file, and binary are correlated maintainer/GitHub
custody, not reproducible-build or binary-authorship proof; actionlint success is not hosted
Actions execution.

The second exact-overlay review also found one stale command-guide count in the already modified
`AGENTS.md`: it said 175 KSG harmonic-revision mutations, while the source inventory sums
`16+2+12+35+74+37=176` and exact-f6 hosted log lines independently report 176 in both modes. The
guide now says 176. This is a documentation correction, not a new mutation execution or independent
scientific result.

That read-only-intended review also demonstrated a custody hazard: ordinary Python invocations of
the claim and Markdown checkers created three ignored bytecode files under `scripts/__pycache__`.
No tracked or staged byte changed, but the prior empty-ignored statement became temporarily stale.
The cache was inventoried, moved recoverably to
`/private/tmp/pid-rs-f7-cache-quarantine.EHHMtm/scripts-__pycache__-second-overlay-review`, and the
ignored/cache census returned empty. Subsequent custody rechecks use `-B`; “read-only checker” does
not imply “filesystem-side-effect-free” without that entry premise.

## Required evidence before any GO disposition

The original pending list is now classified rather than left stale:

| Obligation | Exact f6 status | Successor obligation |
|---|---|---|
| Immutable-C3 clean/precommit replay in both modes | **Closed locally** by the final 9,488-byte replay above; earlier interrupted and umask failures remain zero-credit. | **Closed locally for the current command route** by the terminal one-shot replay above. It replays immutable f6 only and does not adjudicate or transfer to the successor tree. |
| Outer direct-child checker and exact external tree/checkpoint | **Closed for exact f6** by its committed direct-child gate. | f6 is replayed only at f6; a later receipt must bind the successor separately. |
| Frozen outer mutation suite in both modes | **Closed for exact f6 only.** Hosted KSG job `91484882859` passed the 351-case suite in normal and optimized modes. The exact-source outer self-test then passed 109 cases across 18 bookkeeping families with 88 mutation-verifier launches; 22 of those 109 are no-launch receipt cases, while 38 harness controls are outside both counts. Checker receipts were byte-identical at SHA-256 `9572baec...`. Old contaminated, restrictive-umask, provisional-source, and interrupted runs remain zero-credit. | **Closed locally for immutable f6 through the corrected wrapper** by the terminal result above. Finite correlated mutations are neither independent evidence nor successor-tree, hosted, scientific, or security adjudication. |
| Two alternate indexes, tree, unsigned direct-child commit, clean endpoint | **Closed for f6**; both constructions yielded tree `1ce2d750...`, and the clean unsigned commit/push is `f6fde520...`. The two index routes are correlated custody views, not independent authentication. | Construct and bind the successor acyclically without using `git add -A`. |
| Rust, feature, compiled, and platform gates | **Closed only as enumerated f6 subjobs, not as a run-level GO.** The terminal run has 44 successful jobs and one PDF failure; the long KSG job is among the 44 successes. | Require a terminal all-green exact-successor run; passing f6 jobs do not transfer. |
| Nine PDF source/artifact and visual checks | **Closed only for the bounded local 186-page replay**; exact f6 hosted PDF execution is red at `gobble.sty`. | Re-run the unchanged nine sources/artifacts with the added package and require hosted completion; package availability is not inferred. |
| Clean worktree, isolated exact source, cache/import/race/contamination, snapshot, and command transformation | **Closed for the bounded exact-f6 route.** The clean endpoint, positive exact-source route, snapshot, command transform, and terminal normal/optimized outer mutation execution are recorded. This is finite hostile-family coverage under explicit runtime premises, not generic attack resistance. | Recheck the eight-path successor and its immutable-f6 command transform; f6 custody does not adjudicate it. |
| Independent review | **Closed only as a scoped implementation/tree review** by the retained f6 review; it is not institutional independence or scientific review. | Obtain read-only review of the exact successor and later of the acyclic receipt. |
| Fast-forward push, hosted result, security disposition | **Push closed; hosted GO failed.** Exact-f6 CodeQL run `30743459484` succeeded as execution evidence, while the 87 open code-scanning alerts and repository-level observations remain unadjudicated and security-cleanliness is denied. | Push only a reviewed unsigned fast-forward successor, require all-green CI, and bind category-correct security observations without commit-attributing repository-level endpoints. |

The direct-child checker remains deliberately valid for exactly one transition. Because f6 is red
and a package correction necessarily creates a descendant, the correction replaces the expired
current-`HEAD` invocation now, not after a fictional f6 all-green result. It replays f6 at f6 and
does not accept a merge or arbitrary descendant. The successor's tree, commit, push, hosted result,
security capture, and acyclic receipt remain **pending**; no provisional identifier or passing f6
subjob may fill those fields. The original C3 run remains a retained 42/45 failure, and f6 remains
a retained hosted failure, until the exact successor completes every applicable gate on its own
exact run.
