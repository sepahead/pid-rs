# C3 LuaTeX map-free workflow-PDF correction

- **Evidence date:** 6 August 2026
- **Disposition:** **all required local replays passed; final tuple review/staging and hosted
  closure remain pending**
- **Machine companion:**
  `audit/evidence/workflow-pdf-luatex-map-free-correction-2026-08-06.json`, SHA-256
  `8312e5bfba9e16184ea39fac09a22baee2e38e82bc19629672da8ce8dafa22ad`
- **Declared C3 ancestry root:** `8b792bc143fff2d84f2d8e7817d1de7850741223`
- **Immediate parent and `origin/main` observed before local replay:**
  `30c8fa831407ad3d485f8ed636c52a2d85d03ffa`, tree
  `f7808e1db0195c0c0b6c65b828a068e5f3d64f55`

This is a pre-host implementation report. It intentionally does not contain a self-determining
implementation commit or tree, an alternate-index tree that includes this report, or future hosted
run identifiers. Those facts cannot be placed into their own ancestor without a digest cycle. A
strict-descendant receipt must bind them after an unsigned fast-forward implementation commit is
pushed. “Pending” below is a lifecycle state, not an unresolved evidence field and not evidence of
success.

## Executive result

The exact Noble predecessor is terminal red. GitHub Actions run `31027991226` executed exact commit
`30c8fa8`: 44 jobs succeeded, one failed, and none were cancelled, skipped, or left nonterminal.
Formal-PDF job `92381239226` failed after LuaHBTeX selected
`/var/lib/texmf/fonts/map/pdftex/updmap/pdftex_dl14.map`, outside the admitted `TEXMFROOT` closure.
The 96,604-byte raw job-log digest is
`75dfa1b67a6f9232faf99813b13964836fb8e8aa2ffbd9891136550bdbbcc00a`.
The successful KSG job `92381239220` (119,501-byte raw log SHA-256
`c9120f2298ea43dee2eebfbdc1babfb3340f0a0ce78cff41deef88c0859d2903`) and four successful CodeQL
jobs in run `31027989770` do not repair that failure and are not transferred into the correction.

The bounded correction removes the exact report build's inherited default-map action instead of
admitting mutable system-variable TeX state. Each isolated report build now enters through an exact
generated wrapper. Its first explicit operation is `\pdfextension mapfile {}`. After that operation, the
wrapper refuses a nonempty described `find_map_file` callback inventory, installs an
operation-specific denial for later nonempty map-file lookups reaching `find_map_file` on the
tested TeX `mapfile` and Lua `pdf.mapfile` routes, installs a
category-2 `start_file` guard only as defense in depth, emits one exact pre-source sentinel, and
loads the exact captured report source under a stable explicit job name.

The current correction candidate freezes a target of 266 controls with exact partition
`194 + 37 + 17 + 7 + 8 + 3`. Its primary exact-source self-test and a separately launched,
same-source correlated replay both passed 266/266. The isolated exact checker then passed on an
unchanged four-source pre/post tuple and reproduced the 626,770-byte, 51-page PDF, rendering
receipt, executable manifest, and `pypdf` manifest exactly. Two earlier 246-control passes, their
correlated replay, and the earlier exact-workflow run retain zero current closure credit because
their source bytes moved; no later pass is transferred backward.

The frozen local tuple establishes bounded engineering evidence on one Darwin arm64 toolchain; it
is not Ubuntu evidence. C3 remains open until the final tuple is independently reviewed and staged,
an exact implementation commit has terminal all-green hosted CI and CodeQL, and a strict-descendant
receipt records those facts without splicing jobs across runs.

## Exact question and bounded answer

The question is not whether LuaTeX can consume map information under arbitrary code, format, or
filesystem behavior. The exact question is:

> Under the captured mathematical-workflow source, admitted LuaHBTeX toolchain and format, and
> declared local filesystem/process premises, can both isolated builds complete without a covered
> map-file input while preserving the exact report artifact contract?

The frozen local answer is **yes on the tested route under the declared premises and exclusions**.
The credited primary, correlated, and exact executions share one frozen shell-source pair; the
exact route additionally binds the README and certified-SxPID2 checker in its four-source tuple.
Together they exercise the following four conjuncts:

1. the wrapper's first explicit operation suppresses the inherited default `pdftex.map` action after
   the selected format has loaded and before the captured report source runs;
2. later nonempty map-file lookups reaching `find_map_file` on the tested TeX and Lua routes
   encounter the denial independently of requested path spelling;
3. every retained recorder input path is checked in both raw and resolved form for a case-insensitive
   `.map` suffix and adjacent case-insensitive `fonts/map` components; and
4. two isolated same-toolchain builds reproduce the exact committed PDF, text, geometry, font,
   navigation, and dual-render contracts already enforced by the checker.

Conjuncts 2 and 3 are deliberately different. The runtime controls use the toolchain-selected map
bytes under neutral names; the FLS checks intentionally cannot classify those renamed bytes. The
two conjuncts diversify failure mechanisms but are not institutionally independent.

## Why removal is narrower than admission

The Noble path was a generated system-variable artifact, not a repository source. Enlarging the
closure to all of `TEXMFSYSVAR` would admit mutable maps, caches, indexes, and unrelated generated
state. Copying one selected map would still not prove which operation requested it, whether the
recorder used the same spelling, or whether another path supplied equivalent bytes. From first
principles, closure expansion is justified only for a semantically necessary dependency that can
be bounded without silently expanding the trusted input set.

The report uses captured OpenType fonts through LuaOTFLoad and reproduced its existing bytes with
the default map disabled. That is an observation about this source and toolchain, not a theorem
that OpenType documents never use map files. The correction therefore removes one demonstrated
unnecessary action and leaves future engine/source combinations to fail closed.

## Manual-source custody and semantic boundary

The semantics were checked against two local primary manuals rather than inferred from callback
names or test labels:

| Source | Bytes | Pages | SHA-256 | Use in this correction |
|---|---:|---:|---|---|
| LuaTeX 1.18 manual, `luatex.pdf` | 1,793,812 | 328 | `bffa086270c356b8cffb4b0bb4aae2120df598dac369cde8358a0dc67380389f` | Separates `find_map_file` from encoding discovery and identifies `start_file` category 2 as a font-map coupling event. |
| pdfTeX manual, `pdftex-a.pdf` | 970,535 | 84 | `1d4a6db648c5da8e3250564fab54f8a4b9de006514afd581efed39965c88ee56` | Supports the early empty-map operation used to suppress the inherited default map. |

The bridge is explicit rather than inferred from similar names. The pinned LuaTeX manual defines
the compatibility primitive `\pdfmapfile` as `\pdfextension mapfile` and says `pdf.mapfile`
replaces the `\pdfmapfile` primitive inherited from pdfTeX. The pinned pdfTeX manual supplies the
early-empty-call/default-map semantics; exact A/B execution supplies evidence for that bridge on the
admitted LuaHBTeX 1.18 toolchain. This is not a theorem about future engines or other formats.

The locally selected `pdftex.map` path was
`/usr/local/texlive/2024/texmf-var/fonts/map/pdftex/updmap/pdftex.map`, resolving to
`pdftex_dl14.map`; its 5,467,645 bytes had SHA-256
`9e626e7661728390063e2bc6d3ef3cc7c7bfedd3219ed86dfa34494935ad3bd9`.
Those exact bytes supplied the renamed-path runtime attacks. Their digest is fixture custody, not
font-map authenticity.

The ordering claim begins at the first explicit operation in the generated wrapper. Format loading,
format-embedded state, `\everyjob`, and other engine-supplied pre-wrapper activity may occur first
and are outside the claim. The empty-map operation does not rewind prior state.

## Mechanism in execution order

### 1. Wrapper capture

For each isolated build, an isolated Python invocation constructs
`pid-rs-map-file-free-entry.tex` with `O_EXCL`, `O_NOFOLLOW`, and `O_CLOEXEC`. It writes through the
open descriptor, synchronizes the content, replays the exact bytes through that descriptor,
requires a single-link regular file, applies mode 0444, and compares descriptor/path identity and
size fields. The wrapper begins with the literal bytes for `\pdfextension mapfile {}\n`.

LuaHBTeX subsequently reopens the pathname. Mode 0444 is a permission observation, not filesystem
immutability. The owner or a privileged actor can replace or restore the object under broader
premises. Content is synchronized before the final mode change; final mode metadata and the parent
directory entry have no crash-persistence theorem. These are explicit boundaries, not omitted
attacks.

### 2. Operation-specific map denial

Immediately after default-map suppression, the wrapper requires an empty
`luatexbase.callback_descriptions("find_map_file")` inventory and installs a handler that raises on
every later nonempty map-file lookup reaching that callback on the tested routes. Runtime controls
cover:

- the exact selected map bytes renamed to a neutral leaf and requested by the TeX primitive;
- the same operation through an absolute path;
- the same bytes under a TEXMF-shaped path without a map-shaped name;
- a neutral-name Lua `pdf.mapfile` request;
- an absolute-path Lua `pdf.mapfile` request;
- a simulated category-2 file event.

The wrapper then emits exactly one pre-source sentinel and inputs the exact captured source.
`-jobname=mathematical-problem-solving-workflow` preserves the output stem.

### 3. Deliberate boundary controls

File-free TeX/Lua `mapline` state changes are accepted and named as a nonclaim. A hostile captured
source could replace callbacks or use arbitrary Lua I/O; that is excluded by the trusted-source
premise, not prevented by this wrapper. The category-2 callback is defense in depth and is not
evidence that every encoding or font resource is denied.

### 4. Recorder closure

Every retained pass requires its exact generated wrapper in the `.fls` input inventory. Raw input
paths and resolved input paths are checked separately. Raw checking catches a map-shaped alias whose
target has a neutral name; resolved checking catches a neutral alias into `fonts/map`. A named
accepted renamed-content control demonstrates why FLS input paths are not content classification.
FLS is compiler recorder evidence, not a syscall trace, and capture is not atomic with earlier
reads.

### 5. Executable custody

The checker resolves its admitted command set before lock/re-exec, immediately before manifest
capture, and after build/validation consumers but before final executable/Python custody and any
optional refresh. Exact executable bytes and shebang/interpreter closure are captured and
revalidated. Independent review found that new external `sleep`, existing external
`basename`, and literal `/bin/bash` fixture launches were outside or could diverge from that
custody. The candidate source adds `basename`, `ps`, and `sleep` exactly once to the manifest,
mutates each command's absence, and routes the eight formerly literal `/bin/bash` fixture calls through the one resolved
path stored in the read-only `SELF_TEST_BASH` shell variable. Other bare `bash` probes remain under
captured `PATH` and command-resolution custody, not that fixed path. This is byte custody within
admitted roots, not executable authenticity.

## Liveness, cleanup, and rejection typing

Controls routed through the common accept/reject wrappers give the probe/watchdog decision phase a
180-second deadline. Dedicated liveness controls use one- or two-second decision deadlines. This
parameter is not a strict end-to-end wall-clock bound: record/readiness publication, the sole
five-second readiness grace, the watchdog's two-second escalation, the five-second `ps` call,
group-absence polling, and reaping are subsequent bounded stages under the declared
cooperating-kernel/progress premise. Direct fixture setup, extraction, and post-refresh checks do
not each have an inner deadline; the aggregate run still depends on the outer local or hosted job
deadline.

For a bounded probe, Bash monitor mode gives the probe anchor and watchdog distinct process groups.
Completion and timeout race through one exclusively created decision directory. A successful
claimant publishes at most one canonical record; a claimed directory without one is custody
failure. Before branch selection, the parent no-follow descriptor-replays exactly one single-link
mode-0600 completion, timeout, or watchdog-error record, checks its bounded exact payload, and
captures the typed classification rather than rereading the pathname later. The anchor catches
TERM with a no-op handler rather than exporting `SIG_IGN` across `exec`. After the
completion-record publisher child exits, the anchor installs its `USR1` release trap, opens a
no-clobber mode-0600 readiness node with shell builtins, writes the exact payload, and self-stops.
The one-second control induces an empty-node window; it does not prove that a descheduled parent
observes it. A visible completion record ends the outer loop without a preliminary
readiness-existence grace. After central decision-record capture and watchdog reap, the parent
starts the sole five-second readiness validator. Path existence is not readiness: the parent
retries no-follow/nonblocking descriptor and
leaf replay until their stable identity and exact canonical bytes agree. Failure to become
canonical within that grace becomes custody status 125. The handshake is scheduling evidence, not
crash durability. On ordinary completion, the parent validates
expected group ownership, sends group
`SIGSTOP`, takes a bounded `ps` membership snapshot, and releases only a lone anchor. Unexpected
members after proven ownership trigger an attempted group `SIGKILL`. Missing/mismatched ownership,
inspection failure, or other uncertainty triggers bounded cleanup attempts, expected-PGID absence
adjudication, and custody status 125; it does not prove that an observed or possibly foreign group
was killed. Timeout/error routes attempt cleanup of the still-anchored expected group. Every
post-launch decision route polls for expected-PGID absence before exposing its status.

The parent normally attempts to kill and reap the watchdog after a visible record and performs final adjudication. If
the parent is descheduled past the watchdog's two-second grace, the watchdog's delayed KILL may win
first. Later group absence does not identify which signal won. Shell `wait`, process inspection,
and cleanup are finite only under the declared cooperating-kernel/progress premise; this is not a
hard asynchronous preemption or pidfd containment theorem.

The admitted trusted fixtures give rejection statuses exact meanings: status 1 is detected
artifact/semantic drift and status 2 is a prerequisite/environment contract violation. Only
`{1,2}` receives named mutation credit. Status 124 (timeout), status 125 (the broader custody
failure class), launch failures, and signal-derived statuses remain uncreditable even if output
contains the expected marker. Marker plus status is not a causal type theorem for an arbitrary
hostile command.

The target bounded-probe family covers normal zero and nonzero return, an induced empty-readiness
window, noncanonical readiness bytes, wrong-mode and malformed decision records, a canonical
watchdog-error record, default-TERM and TERM-ignoring descendants, ordinary-exit orphan rejection,
a preclaimed publication stall with a descendant, cleanup-helper failure, membership-command
failure, post-cleanup group absence, signal status 143, and source-order mutations. The sole
five-second readiness grace is separate from the one/two-second watchdog decision deadline.

External cancellation remains distinct. Deliberately interrupting one provisional piped exact run
left its already-launched source-snapshot self-test as process group 56603. The exact path and
PGID were checked, only that group was terminated, and absence was confirmed. This run has zero
credit. The event demonstrates an outer runner/process-tree boundary; it does not contradict the
inner bounded-probe result and must not be hidden by it.

## Frozen source and local evidence

### Source objects

| Object | Mode | Bytes | SHA-256 |
|---|---:|---:|---|
| `CHANGELOG.md` | 0644 | 134,916 | `953476d708cc52e9e4d11dddaf06dc3c4a1d96e0f16a6fa193dade48eedc3ab3` |
| `scripts/README.md` | 0644 | 95,618 | `c688611be7460766804ef3a497e2a63c3395ee92a94140ebce75591a94667f2b` |
| `scripts/check-mathematical-workflow-pdf.sh` | 0755 | 211,004 | `df7dc39c85220e16b94a230c964e52619f9b623e446c181e198a3b3a755540e1` |
| `scripts/check-mathematical-workflow-pdf-self-test.sh` | 0755 | 222,422 | `b33dd4d52d788fe5d88aefb8db575c032bbb509fabadb3288f5926cb7f490f3c` |
| `scripts/check-certified-sxpid2-claim.py` | 0644 | 67,251 | `b3725b9a2a85005c342c9277a34ba7651249a954f19d70a707038a8ec648b040` |

### Toolchain observation

The local run used Darwin arm64 25.5.0, Bash 3.2.57, Python 3.14.6, ShellCheck 0.11.0,
LuaHBTeX 1.18.0 / TeX Live 2024 development id 7611, Kpathsea 6.4.0, Poppler 26.06.0,
`pypdf` 6.14.2, and Apple Git 2.50.1. Version observation does not authenticate any binary.

### Static and dynamic gates

| Gate | Exact result | Receipt boundary |
|---|---|---|
| Bash syntax, both shell files | pass on the current shell tuple | Static analysis only; rerun after any shell edit. |
| Full ShellCheck, both shell files | pass on the current shell tuple | Version 0.11.0; static analysis is not execution. |
| Whole-tuple whitespace checks | pending final Markdown/JSON freeze and alternate-index staging | Whitespace/patch structure only; must include the two initially untracked evidence files. |
| Primary complete self-test | 266/266, exit 0, 108 s | Exact self-test `b33dd4d5…`, production `df7dc39…`; 20,343-byte session-local log SHA-256 `b23a3ed810b83ab2d78a3656aae56a4088611489b981d197e36c7011a1bc921c`. |
| Separately launched correlated replay | 266/266, exit 0, 110.34380087489262 s | Exact source pair; child PID and derived PGID 26102; 706 samples observed 1,579 descendant PIDs/417 descendant PGIDs, with zero rows in the immediate post-exit snapshot and follow-up. Log `b23a3ed8…`; 6,720-byte metadata `a923fde7…`. Same host/toolchain/validators/fixtures; correlated corroboration only. |
| Exact workflow-PDF checker | pass, exit 0, 373 s | Frozen four-source tuple `130c091c…` before/after; 416-byte session-local log SHA-256 `bccde8f5f98bfdf5214dbc17c83a604c17e716d4f7d125f895eb07309578466b`; exact PDF/render/executable/`pypdf` identities below. |
| Certified-SxPID2 claim, normal and `-O` | pass/pass, exit 0 | Final README `c688611b…`; both 93-byte logs SHA-256 `09dacad5…`; documentation custody only. |
| Certified-SxPID2 mutations, normal and `-O` | 111/111 rejected in each mode, exit 0 | Both 58-byte logs SHA-256 `1e4027c2…`; same mutation implementation, so optimized replay is not independent. |

The raw local logs and raw correlated metadata are session-local and are not repository artifacts.
Their terminal facts, selected metadata, and digests are retained here and in the JSON companion.
That is weaker than retaining the raw bytes in a durable archive and is not described otherwise.

The correlated replay used `/bin/bash --noprofile --norc` from the exact worktree under a fully
replaced eight-variable environment recorded in the JSON. Python 3.14.6 launched it with a new
session and sampled `/bin/ps -A -o pid= -o ppid= -o pgid= -o command=` every 0.1 seconds, deriving
descendants by fixed-point PPID ancestry without baseline subtraction. Its survivor check is an
immediate PID-or-observed-descendant-PGID snapshot plus one follow-up, not containment: sampling
gaps, escape, PID reuse, and the immediate observation boundary remain. The exact checker used
`/usr/bin/env -i`, explicit `PATH`, `HOME=/nonexistent`, `TMPDIR=/tmp`, `LC_ALL=LANG=C`, and
`TZ=UTC`; its ordered four-source `shasum -a 256` stdout stream had the same second-order SHA-256
before and after execution.

## PDF currency and visual review

The final exact checker rebuilt the report twice from captured source and produced the already
committed artifact byte-for-byte on the frozen tuple. The earlier source-superseded checker remains
zero-credit history; the final artifact observations are:

| Object | Observation |
|---|---|
| PDF | 626,770 bytes, 51 pages, PDF 1.7, SHA-256 `f372256011d1173a020d39b86cba5ab7959fb07cea09cf1a2b7eeb292a83cafe` |
| Dual-render receipt | 11,249 bytes, SHA-256 `847685d91b6a565ba37c077515396e3bb83fb1ed18d295a14b4eb3ebe9bedcaf` |
| Executable manifest | SHA-256 `5053eb6d7deb625d42cb23590e6fb8529043b9f26d01b28ba364c3c58cdc1d85` |
| `pypdf` manifest | SHA-256 `dc0d7ee2d29c666298f5fce601068b2459a4f89057dd42beda343e002b432863` |
| Fonts | 25 embedded/subset/Unicode-mapped fonts under the existing contract |

All 51 color and 51 grayscale page renders were reviewed in page order. Fresh original-resolution
spot checks covered pages `3,4,9,10,15,18,20,27,30,37,40,43,47,51`. No blank, clipped,
overlapping, misordered, corrupt, or grayscale-illegible page was observed. The prior visual receipt
remains bound to the unchanged bytes at
`audit/evidence/mathematical-workflow-visual-receipt-2026-08-04.md`, SHA-256
`ad11eed69ca56401f32e12fb1fb47d59682c6aa65b26deb36d89be2c87c708cb`.

No artificial PDF byte change was made: the canonical source did not change, and replacing the PDF
only to manufacture a Git diff would weaken reproducibility. The current PDF is already present on
`origin/main`; the final corrected route reproduced it exactly. Visual review does not validate
equations, citations, accessibility, or scientific conclusions.

## Frozen control inventory

The final direct suite freezes exactly:

| Family | Controls | What it means |
|---|---:|---|
| Predecessor | 194 | Existing source, snapshot, publication, SVG, PDF, render, cache/import, race, contamination, and semantic controls. |
| Bounded probe | 37 | Liveness, descriptor-replayed decision/readiness, typed status, descendant cleanup, result-log, guard mutations, and source-order controls. |
| Entry wrapper | 17 | Wrapper order, exact capture, sentinel/jobname, callback and bypass mutations. |
| Runtime map | 7 | Relative/absolute TeX and Lua requests, one TEXMF-shaped TeX request, category-2 event, and accepted `mapline` boundary. |
| FLS map path | 8 | Map-free acceptance; raw suffix/components; resolved suffix/components; a hidden `.MaP` leaf; a raw `.map` symlink to a neutral target; and renamed-content nonclassification. |
| Executable custody | 3 | Missing `basename`, missing `ps`, and missing `sleep` mutations. |
| **Total** | **266** | Frozen target arithmetic; not an independence count. |

These controls are correlated deterministic fault probes. They share source, author, host,
toolchain, validators, and many fixtures. “266 controls” must never be rewritten as 266 independent
defenses, replications, or proofs.

Readiness source mutants remove no-follow, regular/link, mode, descriptor/leaf-identity, and
exact-payload guards. Decision source mutants bypass root-mode, regular/link, identity, timeout
equality, and watchdog-error allowed-reason guards; dynamic hostile records separately exercise
decision mode and status-payload rejection. The shared two-occurrence flags invariant detects
either descriptor-flags deletion, although the named no-follow mutant edits readiness. The
decision record's 256-byte early size diagnostic has no separately credited semantic mutant:
descriptor reading remains capped at 257 bytes and the closed exact grammars reject every
oversized payload even if that early guard is removed. This is a redundant-guard classification,
not a claim of line-complete mutation coverage.

## Frozen negative-results ledger

Every row remains negative. Later green evidence does not retroactively promote it.

| Seq. | Observation | Classification |
|---:|---|---|
| 1 | Commit `da6bdfe`, run `31018088910`, job `92347360785`, rejected the real Noble Latin Modern layout after package installation; raw log `37058400…`. | Real font-layout failure; zero closure credit. |
| 2 | Exact parent `30c8fa8`, run `31027991226`, job `92381239226`, exposed the generated Noble map path. | Real map portability failure; parent remains red. |
| 3 | A private map-copy draft bound a path/name but not the requesting operation. | Rejected design. |
| 4 | A private `TEXMFSYSVAR` draft admitted/hid mutable format, cache, configuration, and index state. | Rejected overbroad design. |
| 5 | A command-line suppression draft had invalid operation order; renamed bytes bypassed path-only checking. | Rejected; motivated first-wrapper-operation and operation-level routes. |
| 6 | First isolated Noble image acquisition ended after a 220,200,960-byte partial download. | Transport failure; no Ubuntu evidence. |
| 7 | Second isolated Noble acquisition failed during connection/transfer before any checker. | Transport failure; no Ubuntu evidence. |
| 8 | A nominal 232-control suite stopped after control 215 and slept for more than 16 minutes. | Entire run has zero credit. |
| 9 | The first watchdog sent TERM before durable timeout classification. | Real ordering race; pre-repair runs invalid. |
| 10 | The first attempted order mutation raised a generic exception, not its claimed diagnostic. | Zero mutation-adequacy credit. |
| 11 | A captured mode-0444 hostile fixture was copied without restoring write permission before mutation. | Fixture-preparation failure; log `88155791…`; zero hostile credit. |
| 12 | Normal timeout classification preceded late process-group mismatch adjudication. | Real second ordering race. |
| 13 | An exact-sequence reproduction returned 124 while a TERM-ignoring descendant survived. | Real containment failure; survivor explicitly cleaned. |
| 14 | A provisional repair reported 237/237. | Superseded after later lifecycle gaps; zero final credit. |
| 15 | Normal leader exit returned zero with a live same-group child in two reproductions. | Real ordinary-completion gap; survivors cleaned. |
| 16 | A marker-bearing self-SIGTERM returned 143 and met the old rejection predicate. | Real false-credit gap. |
| 17 | A direct hosted-log retry hit TLS timeout and left a zero-byte redirection. | Zero retrieval credit. |
| 18 | A no-op anchor originally used `SIG_IGN`; the inherited disposition prevented a nested shell restoring TERM. | Real signal-semantics defect. |
| 19 | Crediting only status 1 rejected a legitimate prerequisite status 2. | Real typing defect; admitted set corrected to exactly `{1,2}`. |
| 20 | A complete 243-control run passed every case but failed its stale frozen-total gate. | Zero final credit despite case passes. |
| 21 | A later 243-control suite and exact checker passed, then review found uncaptured `basename`/`sleep` and two early absence gaps. | Both runs invalidated; no closure credit. |
| 22 | Two external advisory review attempts exhausted provider allocation without usable artifacts. | No review evidence. |
| 23 | A 246-control candidate passed before selected-Bash, scheduler-race, and exact prose corrections settled. | Source moved afterward; zero final credit. |
| 24 | A reviewer replay read concurrently edited self-test bytes and stopped after 71 controls; log SHA-256 `373d916c…`. | Mixed-source run; zero credit and empirical quiescence warning. |
| 25 | Eight fixture calls used literal `/bin/bash`, while the manifest captured selected `bash`; publication/malformed fixtures claimed only after readiness waits. | Real executable-custody and scheduler-race gaps. |
| 26 | Review found overclaims about every-control deadlines, parent-only KILL, final-mode fsync, clean-anchor KILL, and universal no-record causality. | Documentation defects corrected before final execution. |
| 27 | A provisional exact run was interrupted after those blockers; its log was empty. Its source-snapshot self-test remained as PGID 56603 until exact cleanup. | Zero run credit; retained outer-cancellation boundary. |
| 28 | A log-hash command used zsh's special `path` variable and lost command lookup inside that shell. | Operational evidence-command failure; corrected command reran with a non-special variable. |
| 29 | The first alternate-index whitespace gate found four Markdown hard-break spaces in this then-untracked report; the earlier tracked-worktree check could not see them. | Staging stopped before a tree was written; whitespace was removed, while bindings and prior reviews were invalidated. |
| 30 | Fresh review found that the first 29-entry report prematurely said every review had been rerun while that tuple and the durable resume still declared fresh review pending. | The contradictory tuple was rejected before alternate-index staging; wording and bindings require another fresh review. |
| 31 | A cleanup-helper or `ps` failure could emit the diagnostic reserved for observed surviving members even though membership was never established. | Diagnostic overclaim; status 3 is now limited to observed members and broader uncertainty uses custody status 125. |
| 32 | Prose said every fixture shell used the fixed selected-Bash path, while only eight formerly literal `/bin/bash` calls did. | Scope corrected; remaining bare `bash` probes use captured `PATH` and command-resolution custody. |
| 33 | Evidence said every retained recorder path was checked, while the implementation checks `.fls` input paths. | Scope narrowed to recorder inputs; `.fls` remains non-syscall evidence. |
| 34 | A marker said command resolution occurred after all consumers, although final executable/Python custody and optional refresh follow it. | Marker and prose now bound the post-validation checkpoint without a universal after-use claim. |
| 35 | Liveness prose inferred whole-group stop/kill and knowledge before ownership/membership was established. | Rewritten to distinguish attempted signals, observed membership, expected-PGID absence, and unknown cleanup provenance. |
| 36 | The report initially transferred pdfTeX empty-map semantics to LuaTeX spelling without a primary-source bridge. | Added the exact LuaTeX compatibility bridge plus toolchain A/B evidence; no future-engine theorem. |
| 37 | A review command assigned zsh's read-only special variable `status` and aborted. | Operational review failure; no review credit transferred from the aborted command. |
| 38 | Executable-custody mutations covered `basename` and `sleep` but omitted newly admitted `ps`. | Mutation-adequacy gap; a missing-`ps` mutant was added. |
| 39 | Documentation called the entire `\pdfextension mapfile {}` construct the first token. | Terminology corrected to first explicit wrapper operation. |
| 40 | Source said an exclusive decision claimant always publishes a record, ignoring a stall after directory creation. | Claim narrowed to successful publication at most once; claimed-without-record is custody failure. |
| 41 | `Path.suffix` did not recognize a literal hidden `.MaP` leaf. | Real case-insensitive suffix bypass; fixed with full-name suffix matching and a hostile control. |
| 42 | The changelog implied the liveness harness preserves only statuses 1 and 2. | Corrected: ordinary success preserves any shell-byte status; only named rejection credit is `{1,2}`. |
| 43 | `probe-status` became visible before publisher exit, release-trap installation, and anchor readiness. | Real completion/readiness race; the release-readiness protocol was introduced. |
| 44 | The JSON companion omitted the exact local map fixture and resolved-target custody. | Machine evidence was extended with path, target, size, digest, and bounded role. |
| 45 | TeX had relative/absolute coverage while Lua `pdf.mapfile` had only a relative neutral-name route. | Added the absolute Lua route; no independence claim. |
| 46 | A local calendar date was mislabeled as an instant recorded in UTC. | Replaced with local evidence date plus `Europe/Berlin` timezone. |
| 47 | The FLS matrix lacked a raw-neutral alias resolving to a `.MaP` leaf. | Added the resolved-suffix hostile cell. |
| 48 | Prose said every later `mapfile` invocation was denied, although an empty operation may trigger no lookup. | Claim narrowed to tested nonempty lookups reaching `find_map_file`. |
| 49 | Self-test source `48f45e61…` made the malformed-status fixture publish no readiness node, so the intended parser branch was unreachable. | Dynamic-control regression; that source has zero credit. |
| 50 | Static replay on the same `48f45e61…` source failed ShellCheck 0.11.0 with SC2016 at then-lines 1332–1333. | Static red; no later pass transfers backward. |
| 51 | Source `c0a020d0…` opened the final readiness pathname before writing bytes and equated early visibility too closely with publication. | Partial-visibility race; parent now descriptor-retries exact bytes rather than trusting existence. |
| 52 | Reviewer command `bash scripts/check-mathematical-workflow-pdf-self-test.sh` failed after controls 1–19 while preparing control 20 because the trap mutation target occurred three times. | Exit 1 in 10 s; 1,660-byte log `/tmp/c3-reviewer-selftest-254.log`, SHA-256 `8d69f3a29236cf8038c9b7b6ecec27fb4f7e0cfd55fac485ec9fffed08add66f`; measured pre/post self-test `c0a020d0…` and production checker `df7dc39…`. Exact c0a bytes were not retained or reconstructed. |
| 53 | A mutant changed only the `find_map_file` registration description but was labeled as removal of the denial handler. | Mutation-semantics mislabel; renamed as description drift while the separate return mutant tests semantic denial removal. |
| 54 | Timeout/error branches selected pathnames without the mode, identity, and exact-payload custody claimed for completion status. | Protocol mismatch; all three record kinds now share exact descriptor replay before branch capture. |
| 55 | The report attributed complete executable-manifest custody to a direct standalone self-test that can inherit ambient startup/search state. | Claim narrowed; enclosing exact-checker custody and separately recorded correlated replay are distinguished. |
| 56 | Source `fe19ac5e…` first waited up to five seconds for readiness-path existence and then began another five-second descriptor retry. | Double-grace timing defect; completion-record visibility now ends the outer loop without a preliminary readiness grace, and the sole timer begins after decision capture/watchdog reap. |
| 57 | The same source called a status-only handoff mutation “readiness removal,” although its descriptor validator still enforced readiness and the mutation was beneficial. | Harmless mutant received no adequacy credit; replaced by an exact-payload-validation bypass mutant. |
| 58 | A stage tuple with Markdown prefix `d952388c…` and JSON prefix `e41929d2…` mixed stale lifecycle, count, hash, and pass labels. | Contradictory evidence tuple; rejected and retained as zero-credit history. |
| 59 | Review found missing report propagation for absolute Lua coverage, the eighth FLS cell, `ps`, the TeX-only TEXMF-shaped route, partial-readiness semantics, and phase-versus-wall-clock timing. | Documentation defects corrected before replay; none changes a PID or PDF claim. |
| 60 | The first canonical watchdog-error control used `sleep 1`, so a sufficiently descheduled watchdog could lose to ordinary completion. | Scheduler-race control defect; the fixture now cannot complete within the parent's publication bound and must be killed after watchdog-error adjudication. |
| 61 | Self-test `68948f27…` reported 257/257 in 105 s, but review found that its wrong-mode fixture exposed canonical mode 0600 before `chmod 0644`. | Entire pass has zero credit; 19,517-byte log `/tmp/pid-rs-c3-selftest-257-20260806.log`, SHA-256 `67c0385e6a4711dc7d4d61fe58fa1197f35460a8ed78ef26fb74f5587ccbbbf4`. The replacement publishes complete bytes atomically with mode 0644 already set. |
| 62 | The same 257/257 source directly created the canonical status for its invalid-readiness fixture, so the parent could reject empty/partial status before exercising readiness validation. | Control-branch race; all hostile status records now use one atomic exact helper, and the 689 pass remains wholly zero-credit. |
| 63 | The delayed-readiness control's elapsed-time lower bound could be satisfied by scheduler delay and did not prove the parent observed an empty node. | Adequacy claim narrowed to successful execution with an induced window and observed elapsed lower bound; exact payload enforcement comes from the runtime invalid-payload control and structural mutant. |
| 64 | The first atomic invalid-readiness repair published valid status before it finished the invalid marker, so the parent could fail on absent/partial readiness rather than complete `release_ready=0`. | Handoff-order defect; complete invalid readiness is now closed before atomic status visibility, and the control requires the exact payload diagnostic. |
| 65 | README/report prose said status visibility immediately entered the five-second readiness grace. | Timing error; decision capture and watchdog reap intervene, and only then does the sole validator timer begin. |
| 66 | Readiness regular/link, mode, no-follow, and descriptor/leaf-identity guards existed without targeted source mutations. | Mutation-adequacy gap; four guard-bypass/removal mutants were added and frozen. |
| 67 | Three-kind decision custody lacked targeted mutants for private-root mode, record regular/link, and descriptor/leaf identity. | Mutation-adequacy gap; three guard-bypass mutants were added. The redundant size diagnostic is explicitly classified, not counted as covered. |
| 68 | Timeout equality and watchdog-error allowed-reason parsing had positive executions but no structural bypass mutants. | Mutation-adequacy gap; two exact-condition bypass mutants were added, producing the 266-control target. |

The 243-control log SHA-256 `c3a79ad0…` and its one-line exact log SHA-256 `47bc3165…` remain
historical negative receipts. Two superseded 246-control transcripts share SHA-256 `7a437444…`;
that equality itself shows why output text without both self-test and production-checker source
hashes cannot identify the executed source revision.

## Twenty-five-lens adversarial adjudication

The lenses are failure-oriented views, not 25 independent proofs.

| Lens | Question | Final disposition |
|---:|---|---|
| 1. Ancestry | Is the correction rooted in the declared C3 history? | `8b792bc` is an ancestor; immediate parent and `origin/main` were exact `30c8fa8` before replay. |
| 2. Delta isolation | Can unrelated science enter? | Alternate-index staging must enumerate only correction/docs/rebind/evidence paths. |
| 3. Exact source | Are consumers using captured bytes? | Snapshot and re-exec routes bind source; final hashes are recorded. |
| 4. Executables | Are transitive commands captured? | `basename`, `sleep`, `ps`, Python, selected Bash, TeX and document tools are captured/revalidated; authenticity not inferred. |
| 5. Wrapper order | Can source tokens precede suppression? | Empty `mapfile` is the first explicit wrapper operation; format/`everyjob` remains outside. |
| 6. Manual semantics | Is the mechanism inferred from names? | Two exact primary manuals and actual A/B execution support the bounded route. |
| 7. Prior callbacks | Can described earlier map handlers weaken it? | Nonempty described `find_map_file` inventory aborts; arbitrary undisclosed engine state is not excluded. |
| 8. TeX operation | Does denial depend on `.map` spelling? | Renamed, absolute, and TEXMF-shaped TeX controls reject. |
| 9. Lua operation | Is Lua's named map route separately exercised? | Relative neutral-name and absolute `pdf.mapfile` controls reject; they share callback/toolchain with TeX. |
| 10. Category 2 | Is defense-in-depth confused with primary evidence? | Explicitly secondary and simulated; no encoding-universe claim. |
| 11. `mapline` | Is a file-free state operation silently treated as denied? | Named accepted boundary prevents that overclaim. |
| 12. Raw FLS | Can a map-shaped alias hide a neutral target? | Raw-path check rejects. |
| 13. Resolved FLS | Can a neutral alias enter `fonts/map`? | Resolved-path check rejects. |
| 14. FLS completeness | Is recorder output called a syscall trace? | Explicitly no. |
| 15. Wrapper object | Can ordinary symlink/hardlink substitution enter capture? | Exclusive no-follow, single-link, descriptor replay, mode, identity, and exact FLS entry checks. |
| 16. Reopen/durability | Is mode 0444 called immutable or crash durable? | No; pathname reopen, same-UID/privileged replacement, post-chmod and directory durability are bounded out. |
| 17. Source trust | Can hostile source replace callbacks or read directly? | Yes outside premise; exact source is admitted and captured. |
| 18. Decision ordering | Can TERM or membership adjudication precede typed custody/readiness? | Exact record replay captures the branch; completion then requires canonical readiness before membership, and source-order mutations reject bypasses. |
| 19. Descendants | Can leader exit hide a child? | Bounded membership snapshot/cleanup and explicit orphan controls fail closed. |
| 20. Status typing | Can timeout/signal/launch failure earn mutation credit? | Only exact `{1,2}` is creditable under trusted fixtures. |
| 21. Result log | Can FIFO/symlink/hardlink reset hang or corrupt evidence? | No-follow/nonblocking/single-link descriptor checks reject named objects; later shell reopen remains a declared private-root race boundary. |
| 22. Inventory arithmetic | Can one family grow while another disappears? | Exact family counters freeze the target partition and sum; the frozen 266-control replay passed. |
| 23. Artifact identity | Did map suppression alter the report? | The final frozen route reproduced the exact PDF and structural/render contracts. |
| 24. Cross-platform | Does Darwin success establish Noble? | No; hosted exact-commit job remains mandatory. |
| 25. Science/security | Does engineering success validate PID, Lean, math, or security? | Explicitly no; unchanged enumerated science/PDF sources and exact artifact bytes are the only neutrality evidence. |

## PID-family and formal-evidence firewall

This correction changes no estimator, theorem, Lean source, mathematical-workflow Markdown/TeX,
figure source, method catalog object, Rust/Python numerical path, or statistical routine. The
certified-SxPID2 checker change binds only the new complete `scripts/README.md` digest.

Therefore no result transfers to:

- KSG mutual-information estimation, consistency, bias, or support eligibility;
- Ehrlich's purely continuous, gauge-dependent shared-exclusions functional;
- categorical Makkeh–Gutknecht–Wibral shared exclusions;
- Williams–Beer `I_min`;
- project-defined fitted-quantized SxPID compositions and their quantized estimands;
- continuous or categorical PID2/PID3 atoms;
- heuristics, wrappers, run logs, ecosystem decisions, or application validity; or
- any Lean theorem or kernel-soundness claim.

The unchanged PDF bytes are evidence that the tested engineering route did not change that
artifact. They are not evidence that every statement inside it is true.

## Honest security disposition

This work uses adversarial mutation and custody techniques because they are appropriate for
publication/reproducibility engineering. It is not a cybersecurity attack and it produces no
“secure,” “vulnerability-free,” or “security-clean” certification.

The bounded positive statement assumes trusted captured TeX/Lua source, admitted executable roots,
the selected format/toolchain, ordinary same-UID filesystem behavior during checked transitions,
working Bash job control, accurate `ps`, no deliberate process-group escape, no external anchor
death, no hostile PGID reuse, and a cooperating kernel/runtime. It excludes arbitrary Lua/native
I/O, callback replacement by hostile source, pre-wrapper format state, privileged or same-UID
replace-and-restore races, recorder incompleteness, crash durability, external cancellation
containment, tool/package authenticity, and future engine behavior.

The security receipt is therefore: **the frozen local tuple passed its bounded custody and negative
controls; security cleanliness is not claimed; hosted security-scanner status remains pending the
exact implementation commit.**

## Acyclic closure protocol

Before C3 can close:

1. independently review this report and JSON companion against the final frozen source and logs;
2. build a task-specific alternate index from exact parent `30c8fa8`, staging only enumerated paths;
3. verify the alternate-index tree, protected paths, file modes, source hashes, PDF currency, and
   all local gates without modifying the ambient dirty worktree;
4. create a small unsigned no-attribution commit and require it to be a fast-forward child of the
   freshly fetched `origin/main`;
5. push directly to `main` without force;
6. wait for terminal all-green CI and CodeQL on that exact commit, including the Noble formal-PDF,
   KSG, certified-SxPID2, Python, package, platform, and security jobs already in the workflow;
7. retain every red successor as a new negative and never splice successful jobs between runs; and
8. add a strict-descendant receipt that binds implementation commit/tree, exact hosted run/job/log
   facts, unsigned observation, alternate-index custody, and the honest security disposition.

Until final tuple review/staging and the hosted closure steps finish, the correct lifecycle
statement is **local replay passed, hosted pending, C3 open**.
