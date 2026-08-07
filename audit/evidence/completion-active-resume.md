# Active completion-run resume manifest

## Current top checkpoint — Lean A published; stale downstream workflow seal failed closed — 2026-08-07

This checkpoint supersedes every lower execution instruction. Goal
`019fadc8-9091-7950-890f-bde9e9b75e02` remains active. Do not restart closed C3 work. Preserve the
dirty primary checkout and its stale local `main`; use only explicit paths in detached worktrees or
fresh alternate indexes, never `git add -A`. Whole-program progress remains the evidence-weighted
**29%** planning estimate with a **24–34%** interval, not a scientific statistic.

Lean Milestone A was independently reviewed and published as exact unsigned commit
`9572f89d8ea5e0d4b0eb432841f800ee2f127cde`, tree
`b37c44f22e0f57a532233ce1ccf59b2780fbc92c`, sole parent
`684d82bab284cbde81cf34e5bbbad3a82f9211e9`. Fresh `ls-remote`, provider-ref metadata, and the
tracking ref agreed on that exact remote `main`; the exact 13-path provider/local delta and all
eight sealed blobs independently matched. Local `refs/heads/main` remains the untouched ancestor
`9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56`, exactly 36 commits behind remote, not divergent.

Exact-head CodeQL run `31195289015`, attempt 1, is terminal success: all four expected jobs and all
36 declared steps plus four runner-generated completion epilogues succeeded, with no missing,
extra, stale-head, skipped, or cancelled item. Exact-head CI run `31195290680`, attempt 1, is not
eligible for hosted-success credit. Its `Exact-count directed-rounding SxPID2 reference` job failed
at `python3 scripts/check-certified-sxpid2-claim.py` after every preceding job step passed. The
checker expected the pre-A whole-workflow SHA-256
`07c6e514027653925abac0268f79739a49a6d83d2d70ce152db706b90d0791ad`, while the reviewed A
workflow is 54,392 bytes at SHA-256
`bd24d70002d532f95a179241924556df367eb2b73b0fd05dcd87aa3b277e4589`. The failure is a real
fail-closed transitive-custody finding, not a mathematical failure or a flaky-run waiver. It also
invalidates every prior statement that A already had all-green CI. Preserve the failed run and its
skipped downstream steps as zero-credit evidence; do not rerun or relabel it.

The first local one-field correction then failed closed on the separately stale full-Justfile
digest: expected pre-A `39440fdf…605`, observed 18,718-byte A bytes at
`68ce656068c270e94ae10d8811c49082a2fa659b398c78509861fa78935336c7`. It has no passing-result
credit. The narrow correction changes both full-container expectations to `bd24d700…e4589` and
`68ce6560…36c7`, updates this checkpoint and the changelog, and must retain all semantic job and
Just-recipe digests. Before publication, require the claim checker and its mutation suite in normal
and optimized Python, the Lean A four-command packet, exact full-file/semantic-container hash
checks, `git diff --check`, and independent review. Publish only an unsigned one-parent
fast-forward child of `9572f89…` through an explicit three-path alternate index after a fresh
remote-tip check. Then require fresh exact-child CI and CodeQL terminal success; the failed parent
run cannot transfer.

Milestone B remains separate. A fresh Darwin-arm64 `--observation-only` run against the exact
v4.32.2 archive produced canonical 12,027-byte JSON at SHA-256
`374bc2eb53881cae4c7b989944dff3daff0fc02c2340ce39bd920a4ddb08723a`. Independent lifecycle/
custody review found no candidate-field inconsistency, but grants no qualification: the run began
from `hosted_pending`, explicitly returned `observation_only_unqualified`, did not run the nested
regression, and marks same-run promotion `not_qualified_same_run`. Darwin pin promotion, acyclic
resealing, changed-byte mutations/lifecycle review, and a fresh strict same-extraction regression
remain required; Linux remains pending. Do not transfer any of this to kernel soundness, theorem
truth, PID mathematics, Rust/binary64 behavior, PDFs, release readiness, or the independent nanoda
obligation.

## Current top checkpoint — Lean 4.32.2 local packet settled; assets still pending — 2026-08-07

This checkpoint supersedes every lower execution instruction. The exact detached base is
`684d82bab284cbde81cf34e5bbbad3a82f9211e9`; the C3 publication closure already present there is
settled, so lower C3 publication/commit/push steps are historical and must not be resumed. The
checkpoint was prepared against an uncommitted working tree for final coordinating review. Do not
discard or mutate the frozen packet leaves. The coordinating root may publish them only by the
explicit-path, alternate-index, unsigned, one-parent fast-forward route below after rechecking the
exact base and remote tip; no hosted-success credit exists until the resulting exact commit's runs
are terminal and independently captured. Do not run a release archive, migrate the active Lean
project, or regenerate PDFs from this Milestone A checkpoint. Both Lean 4.32.2 asset entries remain
`hosted_pending`; this milestone has local source/policy/custody self-test credit only and no live
Lean/archive qualification.

### Exact settled packet leaves

Every leaf below is currently a direct regular mode-0644 file with one hard link:

```text
audit/formal/lean-kernel-regression/issue-14576/issue_14576.lean
    2,460 bytes  SHA-256 0aaec9548df29266061467e37026935391a05bf6142fd027915f40c687a889e2
audit/formal/lean-kernel-regression/issue-14576/issue_14576_min.lean
      804 bytes  SHA-256 77769c1ce88649f56bf1fc8a0ae89fafdef25eae17b744fc7f28cb7b9519cbb5
audit/formal/lean-kernel-regression/issue-14576/origin.json
    3,949 bytes  SHA-256 fd725d7ba4b08071f40ac6acaca62ecad09aefa11aa3c78cb94d2873cc5ddde1
audit/formal/lean/toolchain-release-v4.32.2.json
   12,671 bytes  SHA-256 d60ace3f69e554cd73853fef89fcff0b387ef8381c3c18eb7253b320330602d4
scripts/check-lean-kernel-14576.py
  117,195 bytes  SHA-256 5292a087393565746678e64cdf1e037d27bb46889f520b647b483d05624bbeb4
scripts/check-lean-kernel-14576-self-test.py
  100,077 bytes  SHA-256 e38e415417634fce51422d064639d53d4acf0d46b7b6d5a32048a9467e4aee01
scripts/check-lean-toolchain-custody.py
  141,464 bytes  SHA-256 cd9579f4efbdac5427d36e74667ec0c4eda3a9fb25c3b3aa8f0b3f586357697b
scripts/check-lean-toolchain-custody-self-test.py
  162,967 bytes  SHA-256 39fa4ccc65dd815d816961b3ab1e06519a49ae4e2ac16102b7d8f42da254b1dd
```

The remaining five literal publication-support paths—and no implicit directory or wildcard—are:

```text
.github/workflows/ci.yml
AGENTS.md
CHANGELOG.md
audit/evidence/completion-active-resume.md
justfile
```

The canonical metadata policy projection—omitting only the finalized outer/nested checker byte and
SHA fields named by its acyclic policy—is SHA-256
`5daa464b790cd6d683375d7fb48b86fa457835b82db8a3191a54bdf51fdf1a6a`.
`origin.json` is project-defined mapping metadata, not a third upstream source file. It records, but
does not retain, exact unauthenticated v4.32.2 implementation-source observations:

```text
src/Lean/Shell.lean        blob 9362f91601943cac8b4c0a52da42337775517c3b
  22,896 bytes  SHA-256 6ffb68a347815e43fe5771205bd02236e1508132b9197c27a3d805fe1cad7ab7
src/LeanChecker.lean       blob 48cb20f85c581365e425e803b2cb9352d07eb29b
   4,785 bytes  SHA-256 eb5dee411837629f09c5c18d63cc833d30335a46048bc586642742e90aa65d5f
src/Lean/Environment.lean  blob cf5faa124bc5fee64aca6ad40754b0540498997f
 133,867 bytes  SHA-256 100b207523d1005ae87f62f4e1693806854a35c59cd9b3210dfeeaa875d0ff98
```

Those observations narrowly support selected CLI/replay/trust semantics. They authenticate neither
the provider nor release binaries and establish no source-to-binary provenance.

### Exact local executions

These four route-executing local commands passed from this worktree:

```text
python3 -I -S -B scripts/check-lean-kernel-14576-self-test.py
python3 -O -I -S -B scripts/check-lean-kernel-14576-self-test.py
python3 -I -S -B scripts/check-lean-toolchain-custody-self-test.py
python3 -O -I -S -B scripts/check-lean-toolchain-custody-self-test.py
```

`just lean-kernel-14576-packet` also passed and traversed those four commands. Its combined four
JSON lines are 138,830 bytes at SHA-256
`1611083f1d7f6036c0b52273de2429179b6cfb75dd57d354d8969ec87785c349`; Just's four-command echo on
stderr is 264 bytes at `4e4b5eaf0a06d6c31c64cd21907c6bdc9cfa2d3206f1a4054f60b8287a44193e` and contains no checker
diagnostic. The capture is `/private/tmp/pid-rs-just-packet-final.fPM9we` and has the same temporary,
owner-mutable non-evidence boundary as the per-suite captures below.

Kernel normal/optimized stdout is byte-identical: 25,749 bytes, SHA-256
`939c617646e6a255e3a83f0a480a10503891a421b367f92f4d4f091e9fe9ccaf`; both stderr captures are
empty. Each mode rejects 197 uniquely named negative controls, accepts 8 uniquely named positive
controls, and reports 3 retained demonstrated no-credit counterexamples. Custody normal/optimized
stdout is byte-identical: 43,666 bytes, SHA-256
`d8d68f3d6fee1bb562a639c411359f52b2fd9afb9911b4cffa9d6d50ebde97b7`; both stderr captures are
empty. Each mode rejects 347 uniquely named negative controls and accepts 8 uniquely named positive
controls. Positive and negative names are globally disjoint in both suites. Exact custody negative
category counts are:

```text
metadata_and_source 89; tar_members 24; tar_inventory 11;
extraction_and_manifest 9; versions_and_diagnostics 18;
nested_kernel_regression 150; environment_substitution 7; process_bounds 6;
zstd_process_groups 2; file_custody 8; nested_checker_source_binding 6;
historical_receipt_semantics 3; host_and_pending_state 5; isolated_invocation 9.
```

The captured local outputs are currently under
`/private/tmp/pid-rs-kernel-selftest-final.JlHGo3` and
`/private/tmp/pid-rs-custody-selftest-final.3WcayT`. Those owner-mutable temporary paths are convenience
copies only—not durable storage, authentication, trusted time, WORM evidence, or attestation.

The kernel positives exercise the exact-source loader, real per-child private HOME/TMPDIR under
umasks 000 and 777, early direct-leader exits 0 and 7 through real `run_process`, shared-group
non-signalling, and direct private-directory mode enforcement. Custody positives exercise the real
outer `run_nested_kernel_regression` with a deliberately injected local child command, real bounded
process success/timeout-override and early-leader exits 0 and 7, real zstd zero-exit cleanup, and the
private root/HOME/TMP/destination/extraction helpers under umasks 000 and 777. The injected nested
case proves synthetic wrapper wiring, subprocess/result parsing, outer validation, and binding
callbacks; it does not execute the real nested checker against an asset and earns no qualification
or end-to-end child-regression credit.

### Exact declaration and lineage boundary

The accepted future live-result schema requires a selected emitted-olean probe and intentionally
does not call it a complete declaration inventory. If produced by the exact qualified route, both
target oleans must render the residual axiom-shaped declaration `axiom E : sorry` left by the failed
inductive route; that selected lookup fact would prove neither the intended E type nor acceptance as
the intended inductive. `E.mk` must be attempted, rejected, and absent in both selected target
oleans. In the full fixture, the synchronous failure at the inductive `addDecl` makes downstream
`bad` thmDecl source unreachable and unattempted; the schema requires a full-only absent-name lookup
and the later separate `boom` unknown-identifier guard. The minimum fixture contains no `bad`
declaration, reference, probe, or absence claim. Current local self-tests validate these exact
policy/schema clauses and synthetic wrapper wiring; they do not establish this runtime declaration
inventory. Known-present/known-absent lookup sentinels bracket the same lookup mechanism and are not
an independent implementation or evidence lens. LeanChecker `--fresh`, if reached on a qualified
asset, checks emitted declarations/constants under the selected implementation; it does not
re-elaborate source, rerun `#guard_msgs`, replay rejected source attempts, execute unreachable code,
or provide an independent kernel.

Typed manually transcribed GitHub-provider observations record:

```text
release fix/backport: 8be817b3f6310f62f220861b0c92dbabb951115d
  sole parent: f054605aea4b840552cca2e725580bffd1e1b704
  tree: ddf459e027f32e994e9a7781b1c4b28f90b0203e
  exact subject: fix: missing check at kernel inductive declaration (#14577)
tag commit: f3b06c705e6c85f5314019d5d3baab0fec5b580c
  sole parent: 8be817b3f6310f62f220861b0c92dbabb951115d
provider field merge_commit_sha PR result: a39eab69e1eee9ad38f4efe507907b1026a77808
  history shape: one parent, not a two-parent merge commit
  sole parent: b1722adad3d00ad4443a08709b1efb93a78b477c
  tree: c789d5c648cc81bae0a4cdeaefe4ae451cc65320
  relation to tag: divergent
  merge base: 4792cd22887c8b529a351f6563b693426ff2a8f8
```

The shared exact 59-byte subject does not collapse the distinct commits or trees. Provider reports
for the release fix/tag are unsigned; the PR result is provider-reported verified/valid. All are
authentication=`none`, observed date `2026-08-07`, manually transcribed from exact typed API routes,
with `raw_provider_response_retained=false`. The divergent PR result is not claimed to be an
ancestor of the release tag.

### POSIX lifecycle and remaining limitations

Kernel `run_process`, custody `run_bounded_process`, zstd consumption, and the outer nested wrapper
now clean the captured initial non-self process group after every applicable normal, nonzero,
timeout, and exception outcome. The nested checker never signals its shared outer group; its outer
supervisor owns cleanup. The exact escalation/absence policy is TERM with 500 ms grace, then KILL
with 2,000 ms grace, 10 ms polling, and a 2,000 ms direct-child reap bound. `EPERM` is treated as
group existence and must resolve within the same bounded policy. The TERM/KILL array is an allowed
escalation sequence, not evidence that either or both signals were delivered in every case.

This is endpoint custody, not atomic containment. Probe/signal races and PGID reuse remain possible;
a descendant can evade the captured group by changing process group or session, and no continuous
no-detach monitor is proved. Python reaps only its direct child, not non-child descendants. Same-UID
or privileged source/tool swap-use-restore races remain outside the endpoint snapshots; the retained
no-credit controls are exactly `unchecked_hash_pyc_substitution_no_credit`,
`same_uid_source_parent_swap_use_restore_survives_endpoints`, and
`same_uid_tool_parent_swap_use_restore_survives_endpoints`. Descriptor-bound outer repo reads and
exact-source loaders narrow but do not eliminate concurrent-writer, executed-inode, loader,
filesystem, OS, Python, zstd, hardware, or dependency premises.

An independent local lifecycle audit of this exact resealed checker/self-test/metadata chain
returned `GO` with no blocker: all 20 captured groups and 30 captured PIDs were absent on the
independent late probes, the helper-process scan was empty, all source hashes remained exact, and
the four normal/optimized self-tests matched the counts above. Its 558,394-byte evidence is
`/private/tmp/pid-lean4322-lifecycle-audit.resealed.TQ7d6c/evidence.json` at SHA-256
`0e4eb60a374891807bcb83c7d1022a6ec1bec28ec09fb916be9d7a2e21cbf260`; the 25,609-byte independent
validation is the adjacent `validation.json` at
`a9d27175f3126d4c16617edef3b4a70174a78e8198ccafc36cd0b37494907ecb`. These owner-mutable temporary
receipts are convenience audit output, not durable storage, authentication, trusted time, WORM
evidence, or attestation.

An earlier moving-byte implementation incorrectly gated group cleanup on direct-leader liveness;
auditor evidence at `/private/tmp/pid-lean4322-lifecycle-audit.initial.wtdMtD/evidence.json`
demonstrated zero-exit descendant survival for the then-current kernel/custody helpers. It receives
no current credit and is retained as the motivating negative. A later pre-seal sanity at
`/private/tmp/pid-lean4322-draft-sanity.hmosw07u/evidence.json` exercised only provisional hashes and
also receives no final-hash credit. Initial post-fix runs additionally failed closed on transient
permission-denied group observation and on stale expected control counts; those failures led to the
bounded `EPERM` policy and freshly derived 197/347 inventories rather than being erased.

The active `audit/formal/lean/lean-toolchain`, `lakefile.toml`, `lake-manifest.json`, scientific Lean
sources, Mathlib cache, TeX sources, and PDFs remain outside this packet and unchanged from exact
base `684d82b…`. The historical 144,128-byte Darwin receipt at SHA-256 `6820d85d…95f43` remains
bound but nontransferable because its checker/metadata bytes differ. No asset authentication,
source-to-binary proof, reproducible build, theorem truth, kernel soundness, complete defect absence,
scientific transfer, estimator result, release readiness, or downstream authorization follows.

### Immediate continuation

1. Treat the eight packet leaves and their acyclic seals as frozen; do not reseal unless a concrete
   finding changes bytes.
2. Preserve local capture/audit paths only as owner-mutable convenience output; do not promote them
   to durable evidence, authentication, trusted time, or attestation.
3. Inspect authoritative remote publication state first. If an exact reviewed 13-path child of
   `684d82b…` with the expected tree is already published on `main`, do not recreate or repush it;
   bind its exact commit/tree/parent and continue with hosted observation. An interrupted local-only
   commit object receives no automatic credit and must not silently substitute for remote state.
4. If that exact child is not published, require local `HEAD`, `origin/main`, and a fresh
   `ls-remote` observation all to equal exact base `684d82b…`; stage only the 13 literal paths
   enumerated above through a fresh alternate index; prove the index/worktree complement is empty;
   create one unsigned one-parent commit from the reviewed tree; recheck the remote tip; and push the
   literal commit object to `main` without force. Reconstruct/revalidate rather than trusting an
   interrupted local-only candidate. Never use `git add -A` or mutate another worktree.
5. After publication, bind the exact commit/tree/parent and require every expected hosted CI and
   CodeQL job to reach terminal success before granting hosted closure. Preserve every failed,
   cancelled, skipped, missing, stale-head, or superseded run as zero-credit evidence.
6. Milestone B remains separate: fresh asset observation, reviewed pin promotion in new bytes, and
   later strict replay are required before any live qualification; active-project migration and PDF
   regeneration require a distinct milestone.
7. The independently custodied external-checker obligation also remains open and separate. The
   official postmortem names nanoda as that distinct assurance layer; this packet does not map
   LeanChecker to nanoda, has no current external-checker credit, and transfers no historical
   external-checker result.

## Live checkpoint — exact C3 publication head all-green; acyclic hosted receipt settled — 2026-08-07

This section supersedes every lower checkpoint for execution state. Goal
`019fadc8-9091-7950-890f-bde9e9b75e02` remains active. Whole-program progress remains the
evidence-weighted **29%** planning estimate with a **24–34%** interval; that estimate is not a
scientific statistic. C3 now has exact-subject terminal hosted evidence and settled receipt bytes,
but fixed-Lean assurance, repository-wide Python custody, KSG M1c, PID2 revision 4, categorical
MGW SxPID3 Programs A–E/all 108 coordinates, frontier mathematics, publication artifacts, release
readiness, and downstream authorization remain open.

After compaction, read only:

1. `audit/evidence/codex-goal-prompt-2026-07-26.md`;
2. this top checkpoint;
3. `c3-post-correction-publication-hosted-receipt-2026-08-07.{json,md}`;
4. live `origin/main` and exact-head hosted state;
5. `/private/tmp/pid-rs-c3-hosted-receipt-890.uLmoy4/worktree` if it still exists;
6. the named `2026-08-07-c3-890-*` roots under
   `/Users/torusprime/Development/sepahead-github/pid-rs-audit-custody`; and
7. a lower checkpoint only to resolve a named provenance conflict.

### Exact pre-existing subject and terminal hosted observations

```text
subject commit: 89055322401fc531aaa3ac7fbfb27304c1ef2634
subject tree:   7f1f0b09055dd9eabd33a43cc0ba782a4558c0c0
sole parent:    e72c33684331a79a8cfe220fd32cde8d81920f10
subject:        docs(audit): finalize C3 publication custody
signature:      unsigned
subject delta:  exactly CHANGELOG, completion resume, and publication-custody JSON/Markdown
CI:             31155454637 attempt 1, completed success, 45/45 exact expected jobs
CodeQL:         31155454365 attempt 1, completed success, 4/4 exact expected analyses
CI update:      2026-08-07T08:28:33Z (opaque unauthenticated API text)
CodeQL update:  2026-08-07T06:55:08Z (opaque unauthenticated API text)
```

The KSG integer-harmonic/phase-isolation job is one of the 45 terminal successful CI jobs. No
elapsed-duration claim is made: the receipt retains provider timestamps only as opaque text and
does not validate chronology. These observations belong only to exact commit `8905532…`, attempt
1. They do not transfer the parent `e72c336…` nongreen CodeQL result,
authenticate the provider, inspect logs/artifacts/SARIF/alert inventory, establish extractor
completeness or security cleanliness, prove a theorem or estimator, validate a PDF, authorize a
release, or bind the future receipt-bearing commit.

### Receipt-source correction history and accepted v4 boundary

Three frozen source roots remain rejected and receive no live-capture or receipt credit:

1. v1 `/private/tmp/pid-rs-c3-890-hosted-receipt-source.JP4Hpt` validated job run/head but omitted
   each job's `run_attempt`;
2. v2 `/private/tmp/pid-rs-c3-890-hosted-receipt-source.SlRMqj` used bare Python numeric equality
   at identity/custody boundaries, allowing boolean/integer collapse such as `True == 1`; and
3. v3 `/private/tmp/pid-rs-c3-890-hosted-receipt-source.pmOsEj` gave the expressly
   unauthenticated `gh` the credential and could write exact token bytes echoed inside an otherwise
   ignored response field while claiming that no token value or digest was recorded. It could also
   echo attacker-controlled duplicate keys/filenames or publish a child-stderr digest on failure.

Persistent copies label those roots `source-v1-rejected`, `source-v2-rejected-preliminary`, and
`source-v3-rejected-credential-claim`; the v3 copy was renamed without changing its four files.
Accepted v4 is `/private/tmp/pid-rs-c3-890-hosted-receipt-source.IAXCbg`, mirrored as
`2026-08-07-c3-890-hosted-receipt-source-v4-final`. Its sealed local projection is:

```text
root:                         mode 0500, exactly four regular leaves
README.txt:                   8,803 bytes, mode 0400, nlink 1, SHA-256 2e7d7a9d23ad59b56d677f8b225e15f75aaa0cb5dde1c3c42602635603d08a1e
capture_exact_head.py:       27,785 bytes, mode 0400, nlink 1, SHA-256 29614a3d1e8ca2c4030cdf6cde188f57a232a7d7db0ffcb56e22322793d12a75
generate_hosted_receipt.py:  50,812 bytes, mode 0400, nlink 1, SHA-256 ec3b468f15f4717f88b426f8881f2c986be5176fbe3f4fad5c82c6b168b31f35
validate_hosted_receipt.py:  63,748 bytes, mode 0400, nlink 1, SHA-256 0c1d9e0d44857c5db70ae703c8ec89c5c53fc1acc7898c30427417b0775403ec
```

V4 passes syntax/Ruff, normal/optimized/fresh-post-seal routes, 14 capture rejects, the retained 24
boolean/integer mutations, five credential-boundary mutations, nongreen/renamed-roster no-credit
controls, exact roster/constants checks, and five critical token/error-channel rejections. One
source-building review and one separately prompted read-only adversary returned bounded GO on the
same exact bytes; both remain model-mediated and provide no institutional independence.

The credential is supplied to `gh` through the environment. The source intentionally places it in
neither `gh` argv nor its manifest/receipt fields, and exact token bytes are rejected if present in
returned stdout or stderr before return-code interpretation, response-dependent errors, parsing,
hashing, or writes. This proves only that narrow execution predicate. The supplied executable can
access and transform the credential. No claim excludes partial, encoded, hashed, encrypted, split,
transformed, file, IPC, other-file-descriptor, descendant-process, memory, or side-channel leakage.
The exact-byte scan occurs after fully buffered subprocess return; there is no streaming cap, RSS
hard limit, complete process-tree containment, or executed-inode attestation. GET is only the method
requested in the supplied argv. Actual network behavior and remote effects are not established.

The capture also does not pin every parent directory against concurrent rename/symlink replacement
or bind uid/gid, ACLs, extended attributes, flags, mount semantics, WORM state, trusted time, crash
durability, or remote durability. File modes and hashes are mutable local observations. The source,
Python, `gh`, dependencies, credential, GitHub, runners, actions, toolchains, operating systems,
hardware, network, and clock remain unauthenticated.

### Exact live capture, deterministic generation, and validation

The first authorized v4 live capture succeeded without a partial retry. It used the requested
`/opt/homebrew/bin/gh`, resolved to `/opt/homebrew/Cellar/gh/2.95.0/bin/gh`; the resolved file was
38,265,282 bytes, mode 0555, nlink 1, SHA-256
`798882434e7f6ae5846194191263ecc59d56bc201f13f016270f44cb4f34499e`. That is a local file
observation, not executable/dependency authenticity or proof of actual network behavior.

Capture root `/private/tmp/pid-rs-c3-890-hosted-live.LRZIRB/capture` and persistent mirror
`2026-08-07-c3-890-hosted-capture-final` contain exactly ten response leaves plus the manifest,
all mode 0400/nlink 1 beneath a mode-0500 root. The manifest is 11,686 bytes at SHA-256
`7282860fd045e3c240a87d033503b3f6cde6264bd554bc8a246c041a79353740`. Each exact endpoint was
captured twice, and each pair is byte-identical:

```text
subject commit:  40,638 bytes each, SHA-256 881bfd3e8a7ad45a9621a704c3d1fc1812059c619531e9c8c3137998fd247ef4
CI run:          12,130 bytes each, SHA-256 213ff345e9178d43e3985dd88f59b8021c0e3e21fedd663f715af93ab5ea5781
CI jobs page:   144,755 bytes each, SHA-256 e5907f4b3a11d1096df7af253425859cf57f6e47869e1689e49d885781133b95
CodeQL run:      12,122 bytes each, SHA-256 d2e876337dc4db7280c35926cc6164237e3caa8757a30b54c8f7d91d437f0e43
CodeQL jobs:     10,032 bytes each, SHA-256 c5ae4361025c023eb2ab8f87790f3915c34669a0114cd5904c503f32a1981bcf
```

Duplicate responses are correlated observations, not independent replications or a transparency
log. Pagination completeness is only relative to each response's `total_count`. API timestamps are
retained as opaque text without format or chronology validation.

Normal and `-O` generators wrote byte-identical sealed pairs:

```text
machine JSON:      35,193 bytes, SHA-256 a7eeb570f2d6173a8a32eb91ab6604d352dc92226d963f349771b5e23b7bd055
Markdown companion: 4,391 bytes, SHA-256 85465231690ad083e15cc77cce4c1d3b599b4c7cf407e4f23e2ecbe687191120
```

Three validator executions passed: normal and `-O` against the normal-generated pair produced
byte-identical 2,154-byte validation JSON at SHA-256
`74fe520889642c62ded0ca7c56507bd62fcc2bb56b4944f3ee0194f8eed70ef1`; normal validation of the
optimized-generated path produced a 2,160-byte path-distinct result at SHA-256
`4343a6a4c5439df446e96e673d5ab53de02243fe8cdd7ace86451523d2f9d419`. These executions share
source, inputs, runtime lineage, and most failure mechanisms. They are deterministic route
agreement, not independent implementations or execution attestation.

After the pair was installed at its exact repository paths with mode 0644, isolated normal and
`-O` validation both passed and produced byte-identical 2,186-byte output at SHA-256
`20f183394d55d5a1c2ea1ec56533f2e090b9f6f89fbc37f1fe66469683975a1f`. Later edits to this
resume and the changelog do not alter the validated receipt-pair bytes; candidate-tree review must
bind all four final paths separately.

Final candidate-only method-catalog, release-scope, review-evidence, ecosystem-capability, and
software-identity checkers passed under `/opt/homebrew/bin/python3` 3.14.6 in both normal and `-O`
modes. These paired routes share source/runtime lineage and are not independent implementations.
An earlier attempt through Apple `/usr/bin/python3` 3.9.6 failed closed for method-catalog and
software-identity because they require Python 3.11 or newer, and release-scope stopped because that
runtime lacks `tomllib`; those three invocations receive zero credit. Review-evidence and
ecosystem-capability happened to pass under the older runtime but add no independence claim. The
receipt validator's separately declared isolated Python route is not inferred from these repository
checker results, and no Python executable or dependency authenticity is claimed.

The machine receipt is the typed authority. It derives bounded exact-subject closure only because
the actual terminal partitions, 45/4 exact name rosters and counts, unique IDs/names, full observed
job projections, API-reported page lengths, and exact run/attempt/head predicates all hold. Its
future receipt commit/tree/JSON-blob/Markdown-blob fields are null; it does not hash itself or the
Markdown. The Markdown points one way to the already frozen JSON. Membership or nonmembership of
the future receipt paths in the subject tree is deliberately not adjudicated inside the receipt.
An external alternate-index/tree certificate must establish that fact and the enclosing commit.

### Retained hosted-monitoring negatives

Five transient read-only hosted-query failures were observed before terminal state: one CodeQL TLS
handshake timeout in the original monitor, one PDF-job-detail TLS timeout, two later recoverable TLS
timeouts, and one recoverable unexpected EOF. They receive no job or run credit and were not spliced
into the terminal capture. A read-only monitor configured with a 20-second outer limit was
interrupted with exit 130 and replaced by a 55-second monitor. The later monitor process became
unavailable while the run still reported in-progress; no cause is inferred and its last state
receives no terminal credit. A fresh
read-only monitor observed the same immutable run to terminal success. The v4 live capture was then
performed from scratch only after both exact-head runs were terminal and the sealed source had two
bounded GO reviews.

### Immediate continuation

1. Run final whitespace, exact schema, source-stability, and bounded repository checks on the
   settled four-path candidate.
2. Build a fresh alternate index from exact parent `8905532…` containing only `CHANGELOG.md`, this
   resume, and the two hosted-receipt paths. Prove all remaining tracked mode/blob entries equal the
   parent and prove the future receipt paths were absent from the subject tree.
3. Obtain exact-tree and claim-boundary review, create one small unsigned one-parent commit, and
   non-force push it only if remote `main` still equals `8905532…`.
4. Externally observe that future commit/tree/blobs and its hosted checks without rewriting the
   acyclic receipt or requiring an infinite receipt chain.
5. Close the isolated Lean 4.32.2 kernel-regression/custody milestone, then separately migrate the
   active proof project with a new immutable packet and regenerated/visually inspected PDF.
6. Continue repository-wide Python custody, KSG M1c, PID2 revision 4, MGW SxPID3 A–E/all 108,
   bounded frontier work, papers/PDFs, release gates, and authorized downstream integration.

No estimator implementation, theorem/proof source, numerical fixture/value, workflow, method
catalog, TeX source, or PDF input changes in this four-path receipt milestone. Regenerating a PDF
would create an unrelated byte change and no new semantic assurance, so the PDF set remains exactly
the already validated parent set. Never transfer results among KSG, Ehrlich continuous
shared-exclusions PID, categorical MGW SxPID, Williams–Beer `I_min`, fitted quantized PID, project
heuristics, incomplete/mixed-dimensional PID3, or wrappers without a premise-explicit mapping
theorem whose assumptions hold.

## Live checkpoint — C3 schema-v2 custody validated; four-path publication pending — 2026-08-07

This section supersedes every lower checkpoint for execution state. Goal
`019fadc8-9091-7950-890f-bde9e9b75e02` remains active. Whole-program progress remains the
evidence-weighted **29%** estimate with a **24–34%** planning interval. The exact C3 engineering
subject `dbd3984…` remains terminal all-green. Its published receipt commit `e72c336…` has a green
manual CI run but a terminal nongreen dynamic CodeQL run; the sole full-rerun request was rejected
with “This workflow run cannot be retried.” Those states are separate; no job, run, commit,
estimator, theorem, or toolchain result is spliced or transferred.

After compaction, read only:

1. `audit/evidence/codex-goal-prompt-2026-07-26.md`;
2. this top checkpoint;
3. `c3-post-correction-hosted-receipt-2026-08-06.{json,md}` and its independent-review record;
4. `c3-post-correction-publication-custody-2026-08-06.{json,md}` at exact installed schema-v2
   hashes `6820d85d…`/`88160c13…`, `/private/tmp/pid-rs-c3-v6-final-run.yoKN2q`, and
   `/Users/torusprime/Development/sepahead-github/pid-rs-audit-custody/2026-08-07-prepublication-v6/v6-artifact-review-2026-08-07.md`;
5. live `origin/main`, exact-head hosted runs, and goal state;
6. the publication worktree
   `/private/tmp/pid-rs-c3-publication-descendant.hwkCju/worktree` and Lean worktree
   `/private/tmp/pid-rs-lean4322-e72-integration.GjTymL/worktree`; and
7. a lower checkpoint only to resolve a named provenance conflict.

### Exact published object and terminal hosted state

```text
published commit:  e72c33684331a79a8cfe220fd32cde8d81920f10
tree:              47c3da31da389c9b108ca53b0440eac6ef56edf4
sole parent:       dbd3984adab1547dccd87690f2e5582b65fbd206
subject:           docs(audit): publish C3 correction receipt
signature:         unsigned
delta:             exactly five reviewed documentation/receipt paths
remote main:       e72c33684331a79a8cfe220fd32cde8d81920f10 at the sealed readback
manual CI:         31128514121 attempt 1, completed success, 45/45 jobs successful
automatic CI:      not observed in the bounded exact-head page; zero credit
CodeQL:            31128379468 attempt 1, completed failure
CodeQL partition:  JavaScript/TypeScript + Python success; Actions + Rust cancelled
CodeQL attempt 2:  run remained attempt 1; exact attempts/2/jobs route returned HTTP 404
```

The literal non-force push advanced exact live parent `dbd3984…` to `e72c336…`; two later
`ls-remote` observations agreed. The 263-byte unsigned commit contains no attribution trailer.
Three separately prompted reviews reconstructed the exact tree and returned bounded GO, while
explicitly making no institutional-independence claim. A one-commit gitleaks run reported no
finding, but one scanner over one commit is not a security-clean result.

The manual CI result is direct evidence for `e72c336…`; the missing automatic run remains missing.
The original engineering subject's CI `31112402374` (45/45) and CodeQL `31112399699` (4/4) remain
separate evidence for exact `dbd3984…`. None of those green results changes the failure conclusion
of CodeQL run `31128379468` on `e72c336…`.

### Schema-v2 validation, rejected v5 finalization, and negative ledger

The installed publication-custody pair is now the reviewed schema-v2/revision-2 pair, not the
rejected v5 bytes. Exact candidate and installed bytes agree:

```text
validator:              406,066 bytes, mode 0400, nlink 1, SHA-256 e141fea9eb331f114753150a30fe2fcf6306682cd30a572663e5212c58d01385
generator:               38,206 bytes, mode 0400, nlink 1, SHA-256 6fc18a0e42c04631e15730170885aeb97def2a3260eb7041aba6c010a46a4f96
event:                    1,473 bytes, mode 0400, nlink 1, SHA-256 629a700e460a80fe611efc26c2b9f32b23503ecd4d0235b721802ce2b60ba7f1
candidate machine:      144,128 bytes, mode 0400, nlink 1, SHA-256 6820d85dad4bada7ec2c52923a7f1c6d1b389c4d705f0dcb26277886b3595f43
candidate Markdown:      12,062 bytes, mode 0400, nlink 1, SHA-256 88160c132605c04f5569de126e9cda44bc952283e1d79c9cbc790e51bbf689db
installed machine:      144,128 bytes, mode 0644, nlink 1, same SHA-256 6820d85d…
installed Markdown:      12,062 bytes, mode 0644, nlink 1, same SHA-256 88160c13…
event issue time:       2026-08-07T06:01:51.090725000Z
schema controls:        258 exact schema objects + 258 extra-key rejection controls
negative ledger:        exactly 17 entries, ordered C3-PUB-N007 through C3-PUB-N023
```

The event binds the already frozen validator/generator source bytes; the receipt binds the event;
the Markdown companion binds the machine receipt. Human source review found the intended event
seal before first actual-final receipt serialization, but the validator only binds and
stability-rechecks source bytes and later metadata: it does not parse or prove generator control
flow or attest which bytes executed. The event time is only a declared, unauthenticated
pre-serialization lower bound. It is not post-write completion time, trusted time, authentication,
attestation, or a future enclosing-commit identity, and the local clock and metadata are mutable.
The inherited `drafted_at_utc` is the first-draft time of the receipt lineage, not a claim that the
schema-v2 bytes existed then.

Exact candidate-only validation passed in normal and optimized modes with identical 6,534-byte
stdout at SHA-256 `73b60920e68ca4d68b2a674c709c59dc2fdcd130d58a5b9b7e8d4636c4f75046`
and empty stderr. Exact installed validation passed in normal and optimized modes with identical
6,564-byte stdout at SHA-256
`6a98bbe578e42bd3dc765e5de4b2a3e96f9bf290805e008fce6c83a7e3bbd905` and empty stderr.
Candidate outputs explicitly have no installed/final credit; installed outputs establish only the
declared bounded local receipt checks. Normal and `-O` runs share source, runtime family, inputs,
and most dependencies and are not independent implementations.

The rejected v5 machine document declared `finalized_at_utc: 2026-08-07T00:45:00Z`, before later
validator/generator changes, candidate/installed modifications, and validation outputs. The
19-file archive at `/private/tmp/pid-rs-publication-stale-finalization-v5.b1G198` preserves it.
`C3-PUB-N022` assigns the stale finalization zero credit. The archive manifest also inventoried
itself mid-write and before the directory-wide mode change: 13/19 entry pairs fully match, five
non-self entries differ only in mode `0644` versus `0400`, and the self-entry differs in size,
mode, and digest. `C3-PUB-N023` assigns that defect zero credit; only direct outer stable reads and
rehashes support the bounded current validation.

Two later pre-event freezes also receive zero publication credit. Validator/generator
`b7dbda09…`/`6fab6da1…` overclaimed mechanical proof of generator control flow. The next
`380f95a3…`/`6fc18a0e…` pair retained a hidden generation-time dependency on the rejected installed
pair. They were superseded before any event; their hashes and failure reasons are retained, but
their exact bytes are not claimed recoverable. No `C3-PUB-N024` is assigned because neither draft
created or received credit for an event or candidate pair.

Important hosted boundaries remain:

- the original outage observation remains explanatory context only and proves no pid-rs cause;
- two retained Statuspage responses reported overall operational, Actions operational, and the
  incident at `monitoring`, not `resolved`; their local bytes do not authenticate the service;
- a reviewed helper was frozen at 37,802 bytes, mode 0400, one link, SHA-256
  `d6acea7436270e469edfc6059a14ef358620af59267bb2c55e2e0dde1e7755d7`;
- its sole authorized full-rerun command was issued once; the pinned `gh` command exited 1 with
  exact stderr saying that run `31128379468` cannot be rerun; no service-authenticity claim or
  automatic retry is permitted; and
- a later sealed GET-only capture found unchanged attempt 1, an absent attempt-2 jobs route, the
  same exact-head two-run inventory, and remote `main` still at `e72c336…`. Thus a rerun may have
  been ambiguous at command return but was not registered at that bounded readback.

The terminal capture root is
`/private/tmp/pid-rs-c3-e72-terminal-hosted.Z27GIA`. The helper JSONL is 194,251 bytes at SHA-256
`9759ce033b3f1eefaba54016063c9767099f262d6eac33949d25df3113b29ade`; the GET-only readback script
is 4,262 bytes at SHA-256 `7800f64a00211fc211fd7cb0ce62ffd21343358a80ba8f7e066063fcf16dcee9`.
The terminal root contains exactly 44 retained capture files at the bounded snapshot. The v5
machine receipt bound those 44 files and the 15 then-identified `N007`--`N021` negatives, but its
false finalization field invalidates publication credit. These hashes identify bytes; they do not
authenticate GitHub or turn correlated evidence into independence.

The **rejected** v5 machine receipt is 100,170 bytes at SHA-256
`71fb3d7738b7f51fc9538ea8a2cd56e00351a86ad30b05aa731356ac7b183e89`; its Markdown companion is
5,792 bytes at SHA-256 `477a0e662a5f17450f332a8adfa159d6b8c90f08c26671f3bad07227020c5153`.
The rejected external validator v5 is 290,229 bytes at SHA-256
`4931b70782788d6516984c0da338e42f36769f8e3bb9e4f35312818c27421c6e`; isolated normal and
optimized runs against the then-installed repo paths exited zero with identical 3,235-byte output
at SHA-256 `03db0fa5cd139e4ad63bd3d0bb03f30c7a77b4a9a122f7e62f6aaaf4f527e49d`.
Those passes show what v5 checked; they do not cure its stale timestamp and receive no publication
credit. The schema-v2 exact tuple and four successful v6 validation outputs are recorded above;
none transfers a v5 conclusion.

Here and in the schema-v2 receipt, **sealed** means only a bounded observation of a local
regular file's mode, link count, and digest. An owner or root can replace or chmod these bytes; the
observation is not WORM, tamper-proof, authenticated, or durable storage. The `/private/tmp`
originals now have a read-only local mirror at
`/Users/torusprime/Development/sepahead-github/pid-rs-audit-custody/2026-08-07-prepublication-v6`.
Its 124 copied regular files total 552,692,414 bytes: all 107 exact sealed-package leaves required
by installed schema-v2 validation, the separate Lean source-replay receipt, and 16 final-run
capture files. One 3,670-byte coordinator review transcription brings the selected non-note set to
125 files and 552,696,084 bytes. All 32 schema-v2 copied additions passed direct byte comparison
and equal permission-bit, link-count, byte-count, and nanosecond-mtime projections; the initial 92
copied files have only integer-second mtime projection evidence. The 550,165,784-byte Lean
archive also rehashed to
`ea99ead969901b9fe4c7e7bf350b812a0249e9a5cea20474a737c0cc64746bc0` through `shasum` and OpenSSL;
that is route agreement, not independence. The 5,724-byte custody note is SHA-256
`d1f7c7ad62c04d46469c86b729eee1a3a35e53c437214888675feeec086ba588`; the review transcription is
SHA-256 `b7847c22932893e72e2e109833cfbadf3f1db7ca9bf61bafbf6b0d62628f39e7`.
The mirror omits live Git state/object storage, runtime executables and transitive dependencies,
and future hosted events. It mitigates ordinary temporary-directory cleanup but remains mutable by
an owner or root and is not remote backup, WORM, authentication, trusted time, or attestation.
Committed hashes and projections alone do not preserve bytes.

Under the trigger configuration observed at `e72c336…`, a direct user-authenticated, non-force
`main` push of an exact one-parent four-path documentation/receipt child is eligible to create an
automatic push CI run and a dynamic default-setup CodeQL run; registration and success are not
guaranteed. A workflow `GITHUB_TOKEN` push must not be used. The child must first preserve the
nongreen e72 result. Any fresh runs belong only to that new exact commit. A later typed receipt may
bind those runs and an exact four-path allowlist/complement certificate: enumerate changed
paths/modes/old+new blob identities and prove every other tracked path retains its e72 mode/blob
identity. That is Git-byte complement identity only—not whole-tree, functional, CI-input, CodeQL
database/extractor/query-pack/action/runner/environment, or execution equivalence. It may not
rewrite e72 as green. Even a successful CodeQL execution does not establish zero alerts, zero
vulnerabilities, or security cleanliness.

### Lean 4.32.2 bounded qualification and open integration

#### Historical provisional Milestone A snapshot — superseded, zero current credit

This lower checkpoint originally contained a provisional packet table, provisional control counts,
and provisional self-test-output hashes. Subsequent source-control-flow, process-lifecycle,
typed-lineage, strict-JSON, and custody corrections changed every checker/self-test seal and the
metadata/origin records. The obsolete table and result claims are deliberately removed rather than
left with present-tense wording. They grant the settled packet no identity, execution, declaration-
inventory, archive, hosted, or qualification credit. The only current Milestone A identities,
counts, command results, pending states, and limitations are in the top checkpoint. The two `.lean`
leaves remain exact upstream fixtures; `origin.json` is project-defined mapping metadata, not a
third upstream source file. The earlier Darwin extraction/replay remains bound only as historical,
nontransferable evidence through the 144,128-byte committed receipt at SHA-256
`6820d85dad4bada7ec2c52923a7f1c6d1b389c4d705f0dcb26277886b3595f43`.

`--trust=0` is retained only on the future live regression compilation route. It asks Lean to
trust no macros and to typecheck every imported module; it still trusts the selected Lean
implementation/runtime and does not mean a zero trusted computing base, repair a faulty kernel,
or provide an independent implementation. `leanchecker --fresh` replays imported and defined
constants into an empty environment under that same implementation; Lean's own LeanChecker source
says it is not an external verifier. It does not re-elaborate source or rerun `#guard_msgs`, and
it is not a fresh kernel. This packet is confined to local formal-assurance
regression/custody and contacts no external target. It proves no general kernel soundness,
theorem meaning/truth, source-to-binary
provenance, reproducible build, scientific PID result, Rust/binary64 correspondence, or transfer
among KSG, continuous Ehrlich PID, categorical MGW SxPID, `I_min`, fitted quantized PID,
heuristics, or wrappers.

The following paragraphs retain the predecessor observations and their negative history. Their
old `qualified` metadata label and missing nested-checker policy pin are historical facts only;
they do not override the current `hosted_pending` classification above.

The exact Darwin arm64 archive remains 550,165,784 bytes, mode 0400, one link, SHA-256
`ea99ead969901b9fe4c7e7bf350b812a0249e9a5cea20474a737c0cc64746bc0`. A preserved v2 custody
replay now passed on its third attempt under Python 3.14 `-I -S -B`:

```text
decompressed streams:        2,802,083,840 bytes each, preflight and extraction equal
archive members:             15,278 = 607 directories + 14,671 regular files
regular-file bytes:          2,790,173,642
tree-manifest SHA-256:       8107a285be608bdba37cc145270dcd133070b766d79ce8c033e88d7df9ce40a2
Lean version/commit/build:   4.32.2 / f3b06c705e6c85f5314019d5d3baab0fec5b580c / Release
nested regression:           three --trust=0 compilations and three leanchecker --fresh replays
```

Attempt 1 failed before the checker body because system Python 3.9 lacks `sys.flags.safe_path`.
Attempt 2 failed closed because copied metadata mode 0400 violated the required 0644 runtime input.
Both receive zero qualification credit. Attempt 3 establishes exact archive/extraction/tool-leaf
custody and the bounded issue-14576 full/minimum/benign regression only. `--trust=0` reduces one
trust input; it does not mean a zero trusted computing base. `leanchecker --fresh` uses a fresh
environment under the same Lean kernel and is not an independent kernel. This route establishes no
scientific theorem meaning or truth; it establishes only bounded same-kernel acceptance/rejection
behavior of the three issue-14576 regression sources. It does not cover all 14 repository
scientific Lean sources, binary provenance, reproducible builds, or Linux. Because the outer v2
metadata/checker does not policy-pin its nested checker hash, the replacement external validator
must separately require exact nested-checker SHA-256
`f3bd7cfa08db1343ffbd875f05887e9dac66b89a910f061a70929e051f0d5967`.

The active Lean integration worktree is
`/private/tmp/pid-rs-lean4322-e72-integration.GjTymL/worktree`; it remains based on `e72c336…` and
must not push directly. Its separate exact-source replay now passes for all 14 repository Lean
paths under pinned Mathlib `905b95818eb32af7874a58b427f50c1711a5e96c`: 13 semantic byte units,
321 declarations, 243 named theorem/lemma axiom audits, 12 acyclic DAG edges, and 14 same-kernel
fresh replays. The allowed axiom union is exactly `propext`, `Classical.choice`, and `Quot.sound`.
Its 72,708-byte receipt is SHA-256
`02edc0bde4ed020caad6faafabc31b5cfa0945c485dec17b77db3439fb3f8091`. The 14 custody paths are
only 13 semantic byte units because the KSG root/v2 sources are byte-identical. Ten anonymous
`example`s receive no named-theorem axiom-audit credit. This exact-source result remains isolated
and neither repairs nor receives credit from C3 publication custody. Only a distinct
source-changing milestone may replace those examples with named declarations, record new hashes,
and replay them. Same-kernel checks remain bounded; the external-checker route remains exploratory
with zero credit until it passes. Any settled patch must be transplanted onto the then-live main
parent with a fresh exact-tree review.

### Process-advisory lens and ordered actions

`/Users/torusprime/Downloads/frozen-bytes-audit.md` was read in full at exact SHA-256
`f6a10caf227ae41a55e2909d14ced10d661e341bd376206d6f236a63ebb71d70`. It is advisory, not an
authority. Its useful distinctions—functional versus epistemic versus institutional independence,
hash identity versus authenticity, and a cost/benefit test for every freeze—must be integrated into
the standalone mathematical workflow and PDFs. C3 custody is retained because it binds external
hosted events and fail-closed decisions; same-model review counts never create institutional
independence.

Immediate actions:

1. Treat the schema-v2 event/pair, four validation outputs, persistent-mirror note, and separately
   scoped artifact review as settled exact bytes. Only if live remote `main` remains exact
   `e72c336…` and no equivalent child exists, build the exact four-path tree through a fresh
   alternate index, prove the tracked complement unchanged, obtain a separately prompted
   exact-tree review, create one small unsigned one-parent commit, and push by a literal non-force
   refspec. If that exact child is already published, do not recreate or push it; bind its
   commit/tree externally and proceed.
2. Observe that new eligible commit's automatic CI and dynamic CodeQL to terminal state. Coordinate
   a single writer: no `main` push by any writer until both runs are terminal. CI is known to use
   `cancel-in-progress: true` on the same ref; no CodeQL concurrency policy is inferred. Preserve
   every missing/cancelled/failed result, and create a later acyclic hosted receipt only after exact
   terminal evidence.
3. Finish the isolated Lean 4.32.2 integration; regenerate every affected Markdown/TeX/PDF from
   settled canonical sources, compare extracted text, render and inspect every page, then commit
   and push as a separate reviewed milestone.
4. Close repository-wide Python-verifier custody and KSG M1c; then PID2 revision 4, categorical
   MGW SxPID3 Programs A--E/all 108 coordinates, bounded frontier mathematics, process papers,
   release gates, and authorized downstream work.

Never transfer claims among KSG, Ehrlich continuous shared-exclusions PID, categorical
Makkeh--Gutknecht--Wibral SxPID, Williams--Beer `I_min`, fitted quantized PID, project heuristics,
or wrappers without an explicit mapping theorem whose premises are established for that
application.

## Live checkpoint — C3 final receipt frozen and reviewed; publication candidate next — 2026-08-06

This section supersedes every lower checkpoint for execution state. Goal
`019fadc8-9091-7950-890f-bde9e9b75e02` remains active. The evidence-weighted whole-program
estimate remains **29%**, with a deliberately wide **24–34%** planning interval. C3's exact
engineering subject has terminal all-green hosted observations and the corrected receipt pair has
three bounded exact-byte GO reviews, but the receipt-bearing commit does not yet exist. Fixed-Lean
assurance, Python custody, KSG M1c, PID2 revision 4, categorical MGW SxPID3 Programs A--E/all 108
coordinates, frontier mathematics, publication artifacts, release readiness, and downstream
authorization remain open.

After compaction, read only:

1. `audit/evidence/codex-goal-prompt-2026-07-26.md`;
2. this top checkpoint;
3. `audit/evidence/c3-post-correction-hosted-receipt-2026-08-06.{json,md}`;
4. `audit/evidence/c3-post-correction-hosted-receipt-independent-review-2026-08-06.md`;
5. live `origin/main`, hosted-run, worktree, download, and goal state; and
6. a lower checkpoint only to resolve a named provenance conflict.

### Exact C3 subject and hosted closure

```text
subject commit:      dbd3984adab1547dccd87690f2e5582b65fbd206
subject tree:        72b35f9a3ab7eb53878b25e8588806a8908ebb06
direct parent:       dc50e0afde843ad891ade6660e487083d6112038
C3 ancestry root:    8b792bc143fff2d84f2d8e7817d1de7850741223
signature status:    unsigned
origin/main:         dbd3984adab1547dccd87690f2e5582b65fbd206
terminal CI:         run 31112402374, 45/45 success
terminal CodeQL:    run 31112399699, 4/4 success
```

The exact subject changes only `CHANGELOG.md`,
`audit/evidence/completion-active-resume.md`, and
`scripts/check-certified-sxpid2-claim.py`. Its final checker change rebinds the complete workflow
digest after the scanner correction; the certified-job and Just projections are unchanged. The
checker passes in normal and optimized isolated modes, and all 111 registered claim mutations are
rejected in both modes.

Predecessor CI run `31104508451` at `410a347…` is terminal cancelled with 43 successes, one
secret-scan failure, and one cancelled KSG job. Run `31108555449` at `dc50e0a…` is terminal
cancelled with 43 successes, one directed-rounding SxPID2 custody failure, and one cancelled KSG
job. Their separate CodeQL runs each succeeded 4/4; neither overrides the associated CI failure,
and no cancelled work receives partial closure credit.

### Frozen receipt pair and review

```text
receipt worktree: /private/tmp/pid-rs-c3-final-receipt.t4O7pi/worktree
machine receipt:  27880 bytes, SHA-256 412bd80d1908cb61bc9ce6af9a5be499c69fd04b18c21ddea38999fd82518932
human receipt:    16435 bytes, SHA-256 040629b3a7d8bc4fef57ebd02ad5a5b08adb2d3b03b995388656f2528ab99d9c
review record:     8430 bytes, SHA-256 11bb94e64070cff85c7171c5447ce7fb59667e36cbf07b48f3bd02ce6b7e43a0
pair-only tree:   88aa87177d7aa110edbe88195b8447d2e95b5189
sealed pair index: /private/tmp/pid-rs-c3-receipt-pair-index.Ne68Ii/index
index custody:     72056 bytes, mode 0400, one link, SHA-256 24b9e48e3c4feabb1ae4f5393dcb616dbd60a985dc89c4083c3d192a260f8dd4
```

Three separately prompted reviews independently reconstructed the subject objects, workflow/Just
projections, 13 duplicate API pairs, all hosted partitions, strict JSON serialization, the raw
subject index, N001--N018, security boundaries, cross-PID firewall, and the pair-only prospective
tree. All returned exact-byte bounded GO and found no surviving defect. This is not institutional
independence or three scientific replications. Any receipt edit invalidates every GO.

N018 preserves the rejected 26,684-byte `c23e115c…` / 15,666-byte `61c3bc4b…` pair and its
one-GO/one-NO-GO outcome. In the final JSON, receipt-wide partial-archive facts are a top-level
boundary outside both terminal run records; the Markdown explicitly denies attribution of the
failed partial CodeQL download attempt to either run. No prior GO transfers.

The receipt intentionally leaves its future commit/tree/blob fields null. The review record binds
the final pair and pair-only tree but cannot contain the identity of the larger tree that contains
itself. Build the final five-path tree only after all publication files are frozen, then obtain an
external exact-tree review. A later strict descendant or external observation is required to bind
the resulting receipt-bearing commit.

### Security and negative-evidence boundary

N001--N018 remain explicit and zero-credit where rejected. They include both non-green hosted
runs, interrupted/malformed local routes, the rejected N006 commit, missing historical index,
invalidated receipt-review requests, three rejected and one superseded frozen receipt pair, and
the N018 containment defect.

The earlier authenticated archive attempt expanded a credential into process argv, and a later
process-status check copied that argv into an internal transcript. The exact secret and its digest
are not stored in the receipt. Four known processes were observed terminated or absent, but the
primary-worktree scan was cancelled incomplete after 1,109,780 paths and receives no credit. The
then-existing incident-capture root later disappeared. Credential rotation/revocation,
noncompromise, complete containment, and provider-side audit/last-used/rate-limit/authentication
state remain unproved. Therefore `security_clean_claim`, `credential_noncompromise_claim`, and
`incident_complete_containment_claim` are all false.

No complete valid hosted log archive was retained or used. Three partial invalid CodeQL ZIPs from
the failed attempt are absent and receive no log or archive credit. The replacement capture
contains only 26 duplicate-paired API JSON files totalling 1,075,330 bytes plus its 2,516-byte
manifest. API success supplies no log-text, step, test-count, coverage, SBOM, SARIF, alert,
extractor, runner, service-authenticity, or security-clean conclusion.

### Local checks and post-freeze negatives

The first frozen five-path publication tree, `16743e86c5158445c495e80d63c247cf7f1e5186`,
received one bounded exact-tree GO and one exact-tree NO-GO. The NO-GO found stale present-tense
successor-run wording in the changelog and the incorrect classification of N016 as rejected rather
than superseded. That tree and its sealed 72,200-byte index at
`/private/tmp/pid-rs-c3-final-candidate-index.Z6WIIY/index` receive no commit or publication
credit. During that review, one no-index diagnostic accidentally created then removed an exact
zero-byte temporary sink outside the repository; it changed no candidate, capture, index, Git, or
remote bytes.

The receipt validator, certified-claim checker, and 111-mutation self-test pass under both normal
and optimized isolated Python. Markdown math and the documented method-catalog, release-scope, and
review-evidence gates pass. Five explicit one-file gitleaks scans using the repository config and
unambiguous redaction syntax report no leak across the publication paths, with no broader security
credit.

Three catalog/scope/review validators were first launched under unsupported `python3 -I` and
failed before validation because their sibling `json_schema_subset` module was excluded. Those
runs receive no credit; the documented entry points passed. A `git diff --no-index --check` probe
against `/dev/null` returned status 1 because a new file differs and receives no staged-tree
whitespace credit. The first gitleaks invocation supplied two positional paths to a command that
documents one `[path]`; its clean exit receives no exact-pair credit. The five explicit one-file
replays above supersede only that command-shape ambiguity. The final alternate index must run the
correct cached-tree check.

### Worktree, PDF, and next Lean custody

The receipt worktree is detached at exact `dbd3984…`. A separate clean audit worktree remains at
`/private/tmp/pid-rs-c3-dbd-clean-audit.cFUQXv/worktree`. The primary checkout remains heavily
dirty and 32 commits behind its tracked remote; none of its changes were staged, reset, copied, or
modified by this C3 receipt work.

C3 changes no estimator, theorem, TeX source, figure, font, or PDF input. No PDF was regenerated:
artificial byte churn would not improve this custody edge. PDF regeneration belongs to the later
Lean/documentation milestone when its actual inputs change.

Exact recovered, read-only Lean 4.32.2 candidate sources currently exist outside Git:

```text
kernel checker:   64595 bytes, SHA-256 96acc6aed4c06a6e2e96f5599723445ba7cb68e596e50efd596edd4dedccd982
kernel self-test: 63116 bytes, SHA-256 56748ada55071293c32e0512f7503d2ccaa5bba2a58b2c0136573cf832ebe834
custody checker:  63659 bytes, SHA-256 87f6130e7fc148c55ad3b807db5807a255f85ea0922fd925cc9f40cc45f1c079
custody self-test:39734 bytes, SHA-256 1920bd48db90d624d9fe629a3afe731053caa905a6d6893fdd1fef9b69a73f03
metadata:          8458 bytes, SHA-256 f890a0e452fabaaf4ba884113941ddc8cce0e194bbaf00aefb7bab3ef33e7e92
recovery root:    /private/tmp/pid-rs-lean4322-recovery
Darwin download:  /private/tmp/pid-rs-lean4322-darwin.orHE2a
```

A fresh official-source audit confirms that v4.32.2 is the latest stable release and that its
exact tag commit `f3b06c…` directly descends from the issue-14576 fix `8be817b…`. The newer
v4.33.0-rc2 is a prerelease with additional kernel fixes and must not silently replace the stable
regression target; a later final-4.33 replay is a separate typed gate. The recovered files are not
runnable in their recovery layout because required root-relative fixtures and metadata paths are
absent, so they receive byte-recovery credit only. Recovered receipt names such as
`fresh_kernel_replays` are semantically wrong: `leanchecker --fresh` creates a fresh environment
under the same Lean kernel. Before integration, bump the schema and rename every such field to a
`same_kernel_fresh_environment_*` or `leanchecker_fresh_environment_*` form. The recovered route
also replays only its first issue-14576 fixture through `leanchecker --fresh`; complete
repository-wide exact-source replay and an independently custodied external checker remain open.

The latest checkpoint observation found the Darwin archive reacquisition incomplete; it receives
no credit until completion, exact 550,165,784-byte size, SHA-256 `ea99ead…`, bounded extraction,
tree/leaf checks, and fresh proof replay all pass. The Linux archive remains hosted-pending.
Repository Lean files still pin 4.32.0 until a separately reviewed 4.32.2 milestone is built.
`--trust=0` checks imported declarations
at minimal admitted trust; it is not an independent kernel or generic repair.
`leanchecker --fresh` uses the same Lean kernel and a fresh environment; it is likewise not
independent.

### Immediate ordered actions

1. Freeze exactly five publication paths: changelog, this resume, the final receipt JSON/Markdown,
   and its independent review. Build a fresh alternate index from live `dbd3984…`, verify the
   exact delta/tree/blobs/modes, run full-tree checks, and obtain external exact-tree review.
2. Create one small unsigned/no-attribution direct-child commit, recheck live remote, push a
   literal non-force refspec to `main`, and verify the remote object. Preserve any rejected commit
   or push route as zero-credit evidence.
3. Observe the receipt-bearing commit externally and retain its hosted CI/CodeQL result without
   calling that run self-authentication. Use a strict descendant receipt if commit/tree custody
   must be recorded in-repository.
4. Complete fixed-Lean 4.32.2 archive/toolchain/source replay, independent-kernel route or honest
   zero-credit classification, documentation, TeX/PDF regeneration, and visual/textual review.
5. Close repository-wide isolated Python verifier custody and KSG M1c; then continue PID2 revision
   4, categorical MGW SxPID3 Programs A--E/all 108 coordinates, bounded frontier mathematics,
   papers/artifacts, and every remaining release/downstream gate.

Never transfer claims among KSG, Ehrlich continuous PID, categorical MGW SxPID, Williams--Beer
`I_min`, fitted quantized PID, heuristics, or wrappers without a mapping theorem whose premises
are established for the application.

## Live checkpoint — C3 scanner correction pushed; SxPID workflow custody rebind next — 2026-08-06

This section supersedes every lower checkpoint for current execution state. Goal
`019fadc8-9091-7950-890f-bde9e9b75e02` remains active. Whole-program progress remains the
evidence-weighted **29%** estimate with a deliberately wide **24–34%** planning interval. The
exact-subject C3 format-custody subgate is closed, but the two post-receipt successor runs are not
yet an all-green closure: the receipt run exposed a secret-scanner false positive, and the scanner
correction run then exposed the certified-SxPID2 gate's deliberately fail-closed whole-workflow
binding. Fixed-Lean assurance, KSG M1c, all remaining PID science, release readiness, and
downstream authorization remain open.

After compaction, read only:

1. `audit/evidence/codex-goal-prompt-2026-07-26.md`;
2. this top checkpoint;
3. `audit/evidence/workflow-pdf-lualatex-format-hosted-receipt-2026-08-06.{json,md}`;
4. live `origin/main`, hosted-run, worktree, agent-review, and goal state; and
5. a lower checkpoint only to resolve a named provenance conflict.

### Published receipt and pushed scanner correction

```text
receipt commit:       410a34774c76506cb46a2650f6b9dd3eb5145d57
tree:                 97eeb9974f8894ca70bccc5e13a50f735a493a6b
sole parent:          dfb77a0b200c772b7c00cb615fda70d31ee18334
subject:              docs(audit): close exact-subject C3 receipt
signature status:     unsigned
delta:                exactly CHANGELOG + resume + receipt JSON + receipt Markdown
remote observation:   origin/main = 410a34774c76506cb46a2650f6b9dd3eb5145d57
isolated worktree:    /private/tmp/pid-rs-c3-hosted-descendant.eMLngC/worktree

scanner correction:   dc50e0afde843ad891ade6660e487083d6112038
tree:                 e776eaf2e0daa500d15b1bebbf922ee1c0ca4ac8
sole parent:          410a34774c76506cb46a2650f6b9dd3eb5145d57
subject:              fix(ci): classify exact receipt digests
signature status:     unsigned
remote observation:   origin/main = dc50e0afde843ad891ade6660e487083d6112038
```

The literal non-force push advanced `main` from exact reviewed parent `dfb77a0` to `410a347`.
After detached-HEAD advancement, the ordinary worktree index still described the old parent and
temporarily produced paired staged/unstaged status entries. `git read-tree HEAD` refreshed only
that isolated index; all four working blobs already equaled the commit and the worktree then
verified clean. The separately sealed precommit alternate index remains mode 0400, one link,
71,800 bytes, SHA-256 `14066468…7365d`; no later Git command was run against it.

Receipt-commit CI run
[`31104508451`](https://github.com/sepahead/pid-rs/actions/runs/31104508451) reached 43 successful
jobs, one failed secret-scan job, and one still-running KSG job at the last pre-correction
observation. The separately triggered CodeQL run
[`31104506082`](https://github.com/sepahead/pid-rs/actions/runs/31104506082) completed 4/4
success on exact head `410a347`; that does not override the CI failure or establish security
cleanliness. The repository workflow uses `cancel-in-progress: true`; pushing the correction may
cancel the already-doomed remaining KSG job. Preserve that terminal cancellation if it occurs and
give it no credit. The successor must rerun the complete workflow to terminal green.

### Exact scanner finding and bounded correction

Secret job `92626080608` installed gitleaks 8.30.1 from the workflow's pinned Linux archive and
passed the pre-existing 8-intended/48-rejected policy self-test, then scanned 146 commits and
26.98 MB. It failed with exactly two `generic-api-key` findings in the new receipt JSON:
`job_api_sha256` at lines 349 and 675. Those strings are not treated as secrets merely by
assertion: they equal the retained duplicate public GitHub job-API capture bytes:

```text
KSG job API:     3812 bytes, 5b16aa62c5ca73b39b37364af611a95d247c1522c17222aa141c121434a2fc0d
secret job API:  2140 bytes, 894bda2f3532ebdf396075733b77b9c2b4efc79c8ebba36fd1328a9656b3e805
capture paths:   ci/{ksg,secrets}/job-{a,b}.json in the sealed C3 capture
```

The staged correction changes `.gitleaks.toml` and the CI self-test. Its allowlist requires both
the exact dated receipt path and the complete lowercase `job_api_sha256` JSON-line shape. The
updated gitleaks 8.30.1 policy test passes 9 intended cases and rejects exactly 56 controls:
36 path/key/value/prefix mutations plus 20 syntax/key-family mutations. A current-config scan of
the exact 146-commit `origin/main` history scanned 26.98 MB and reported no findings. That local
Homebrew binary was version-observed but not authenticated, so it is supporting evidence only; the
pinned hosted successor is required. Commit `dc50e0a` is the reviewed four-path correction; its
private alternate index was sealed mode 0400 with one link, 71,800 bytes, and SHA-256
`6ac932764242bb6e8dc1af8ede3f011dd20268b97e7f4178203eb32c0ac01a10` before the unsigned,
non-force fast-forward push.

### Successor failure: enclosing certified-SxPID2 workflow custody

Successor CI run
[`31108555449`](https://github.com/sepahead/pid-rs/actions/runs/31108555449) executed exact head
`dc50e0a`. At the latest observation, 43 of its 45 jobs were successful, the long KSG job remained
in progress, and job `92640085894` had failed. Separate CodeQL run
[`31108550526`](https://github.com/sepahead/pid-rs/actions/runs/31108550526) completed 4/4 success;
that does not override the CI failure.

The failed directed-rounding SxPID2 job first passed the compiled exact-product routes, the bounded
5,921-table evolutionary search, the Lean exact-log-product checker, and the exact certified-job
projection. It then failed closed in `check-certified-sxpid2-claim.py` because the complete
workflow SHA-256 still expected
`fd93c27452fa6b09a9e93b143193a6caeb35e3256e7bfdd839e7b8664e4cd5d0`, while the exact
scanner-corrected workflow is
`07c6e514027653925abac0268f79739a49a6d83d2d70ce152db706b90d0791ad`. The certified job,
Just recipe, release-audit dependency, estimator, theorem, versioned claim packet, and retained
evidence projections did not change. Whole-file custody is intentionally stronger than the job
projection, so this is a valid negative control rather than a flaky failure.

A separately prompted read-only review independently rehashed both workflow versions and the
semantic slices: the certified-job projection remains
`3a31891c2ec40575700ad6b9547148566590c3ffd7b81d4d07635577002e6c9b`; the complete Just file,
certified recipe, and release-audit line also remain at their previously reviewed digests. The
dependency direction is acyclic: the checker hashes the workflow, while the workflow invokes the
checker without embedding the checker bytes or digest. This is separately prompted review, not
institutional independence.

The next correction changes only that expected complete-workflow digest plus changelog/resume
state. In a clean isolated checkout, both normal and optimized `python3 -I -S -B` executions of
the claim checker pass, and both modes reject all 111 registered mutations. The suite includes
separate whole-workflow/Just-container attacks as well as job-local control-flow attacks. These
local results do not substitute for a fresh terminal hosted run. No PDF is regenerated: neither
the certified mathematical content nor any PDF input changed, and artificial PDF churn would add
unreviewed bytes without repairing this enclosing custody edge.

A separately prompted read-only review returned bounded GO after rehashing both duplicate capture
pairs, reconciling the 9/56 arithmetic, parsing the workflow YAML, and checking the four-file diff.
It retained one boundary: this is a shape-based exception, not an exact-two-value exception, so a
future 64-lowercase-hex replacement under that same field and exact dated path would also be
exempt. The receipt is currently immutable at the finalized hashes below; any future edit requires
new receipt-hash review and must not inherit this GO automatically.

Retained post-receipt negatives receive no C3 receipt credit:

- `C3-POST-N001`: run `31104508451` found the two unallowlisted public-digest lines and is
  non-green.
- `C3-POST-N002`: an initial local `--all` scan traversed private refs absent from the fresh
  hosted checkout and was manually interrupted; it is neither a hosted replica nor a pass.
- `C3-POST-N003`: the first patch invocation omitted the patch-format header and changed no file.
- `C3-POST-N004`: detached-HEAD advancement exposed the stale ordinary-index state described
  above; no committed or working bytes differed, and the index-only refresh restored cleanliness.
- `C3-POST-N005`: successor run `31108555449` failed its certified-SxPID2 job on the stale
  complete-workflow digest after the narrower certified-job projection passed. It receives no
  hosted-closure credit and is retained as evidence that the enclosing custody gate failed closed.
- `C3-POST-N006`: the first correction push command used an unbraced zsh variable immediately
  before `:refs/heads/main`; zsh interpreted the suffix as a parameter modifier and Git rejected
  the malformed refspec before contacting/updating the remote. `origin/main` remained `dc50e0a`.
  Rejected unsigned commit object `b901ef2136b7b58458a9186ea676dcea3d5cd2d5` and its sealed
  alternate index at `/private/tmp/pid-rs-c3-sxpid-rebind-index.L6Gxrk/index` are preserved; the
  index is mode 0400, 71,800 bytes, one link, SHA-256
  `c16a5b14d1fac64d4338d7b29b36e45b4e4be16f84b0d988308c9f038c167430`. They receive no
  publication or hosted-run credit. The retry must use a braced literal refspec and a new index.
- `C3-POST-N007`: the next orchestration call attempted to place a braced shell variable inside a
  JavaScript template literal; the orchestration layer rejected the undefined JavaScript name
  before launching any shell process. It created no index, commit, file change, or remote request
  and receives no credit. The corrected call terminates the quoted shell expansion before the
  literal refspec suffix.

Do not edit the finalized receipt JSON/Markdown to hide this later finding. No PDF changed in this
scanner-only correction: the current 51-page PDF is already the exact pushed `dfb77a0` subject
blob, and an artificial rebuild would destroy rather than improve that custody statement.

### Immediate ordered actions

1. Independently review the exact complete-workflow digest rebind; create a small unsigned direct
   child of live `main` containing only the checker, changelog, and this resume; push non-force.
2. Observe that correction commit's complete CI and CodeQL workflows to terminal state; do not
   call them self-authentication. Preserve both earlier non-green runs and give cancelled work no
   credit.
3. Repair the fixed-Lean 4.32.2 candidate's genuine active-packet/documentation integration
   mismatch, regenerate current receipts, and close that as a separate milestone. The latest
   stable Lean release observed through GitHub on 2026-08-06 is 4.32.2; 4.33.0-rc2 is prerelease.
4. Close repository-wide isolated Python verifier custody and KSG M1c with acyclic typed receipts.
5. Continue PID2 revision 4, categorical MGW SxPID3 Programs A–E/all 108 coordinates, bounded
   frontier mathematics, papers/artifacts, and every remaining release/downstream gate.

Never transfer claims among KSG, Ehrlich continuous PID, categorical MGW SxPID, Williams--Beer
`I_min`, fitted quantized PID, heuristics, or wrappers without a mapping theorem whose premises
are established for the application. Preserve the dirty primary checkout, the Lean candidate,
every other dirty/divergent worktree, rejected result, and external capture.

## Historical checkpoint — exact-subject C3 format custody closed; acyclic receipt publication next — 2026-08-06

This section supersedes every lower checkpoint for current execution state. Goal
`019fadc8-9091-7950-890f-bde9e9b75e02` remains active; do not mark it complete and do not restart
closed milestones. The evidence-weighted whole-program estimate is **29%**, with a deliberately wide
**24–34%** interval. The percentage is planning state, not a scientific statistic. The exact-
subject LuaLaTeX format-custody engineering subgate is closed; fixed-Lean assurance, KSG M1c, every
remaining PID-science milestone, release readiness, and downstream authorization are still open.

After compaction, read only:

1. `audit/evidence/codex-goal-prompt-2026-07-26.md`;
2. this top checkpoint;
3. `audit/evidence/workflow-pdf-lualatex-format-hosted-receipt-2026-08-06.{json,md}`;
4. live `origin/main`, hosted-run, worktree, and goal state; and
5. an older record only to resolve a named provenance conflict.

### Acyclic receipt state

```text
receipt worktree:       /private/tmp/pid-rs-c3-hosted-descendant.eMLngC/worktree
required direct parent: dfb77a0b200c772b7c00cb615fda70d31ee18334
subject tree:           60b01bcd466f832315b482960d9453dce08a12bc
subject direct parent:  e53dc427d082dd936024782f62c795db743fc893
C3 ancestry root:       8b792bc143fff2d84f2d8e7817d1de7850741223
prepublication remote:  origin/main = dfb77a0b200c772b7c00cb615fda70d31ee18334
machine receipt:        43967 bytes, SHA-256 c2ef8214dc01ca081113b8e92f252760f3ada6cc9296b39e9a7ffb44ee7ddd44
human receipt:          23049 bytes, SHA-256 21512ff9450ecb71ac914461d14c7262512a6a71d05254c07129ad83ee4152e8
receipt identity:       future commit/tree/blob fields null by design
```

The receipt JSON does not hash itself or the Markdown. The Markdown hashes the finalized JSON. This
resume hashes neither itself nor a future commit. Therefore these bytes cannot identify or
authenticate the commit that will contain them. Publication must use an unsigned one-parent commit
whose exact parent is dfb, followed by a literal non-force fast-forward and an external observation
of the resulting commit/tree/blobs. A run of that future commit is only a later post-commit
observation; it cannot retroactively place its own identity inside these bytes.

At the final prepublication observation, the isolated receipt worktree was detached at dfb and
`origin/main` was dfb. The intended milestone delta is exactly four paths: `CHANGELOG.md`, this
resume, and the receipt JSON/Markdown. Use a fresh private alternate index; enumerate those four
paths; never use `git add -A`; verify the cached tree against dfb plus the four exact files; build a
small professional unsigned/no-attribution direct-child commit; recheck live remote dfb; push with
a literal non-force refspec; fetch and verify. Do not encode the future commit into the receipt.

### Exact subject hosted closure

[CI run `31084336902`](https://github.com/sepahead/pid-rs/actions/runs/31084336902), attempt 1,
completed success on exact head dfb at `2026-08-06T09:53:14Z`: 45/45 jobs and 537/537
API-recorded steps. Four repeated run snapshots are 12,096 bytes at
`391bc021…664a`; four jobs snapshots are 144,755 bytes at `08305e08…a12e`; two attempt-log ZIPs
are 851,761 bytes at `9bb9e088…90ed`. Exact-source terminal auditing reconciled the 45 unique API
jobs, 45 top-level logs, 45 system logs, three direct critical jobs, and the bounded current-roster
name mapping. Repeated downloads are custody checks, not independent scientific replications.

Formal job `92560152057` passed 14/14 API steps and exactly 313/313 frozen controls with partition
`194 + 37 + 17 + 7 + 8 + 3 + 47`. On Ubuntu image `20260720.247.2`, it captured the selected
12,242,215-byte `lualatex.fmt` at `bf4be0e9…61e7` and logged a rebuilt 51-page PDF at
`5a17eccf…d726`. Hosted rebuilt bytes were not uploaded; this is no cross-platform byte-identity or
mathematical-content result. The current retained Darwin PDF remains the exact 626,770-byte,
51-page subject blob at `f3722560…cafe`; no artificial PDF change belongs in this receipt commit.

The expected `exp0` geometry `PIVOT` and MI/coherence `NO-GO` remain non-gating diagnostics; atom
measure validation is `not_adjudicated` and estimator validation is `blocked`. KSG revision 4 still
says `integration_no_go` and `preclosure_core_manifest_must_be_regenerated_at_m1c`; no hosted-job
success transfers into KSG M1c closure.

Separate CodeQL run `31084335829` completed 4/4, but the exact-head snapshot retains 90 open alerts
and 2,219 Rust extractor warning records; extraction completeness and security acceptance are
false. The full-history secret job completed 7/7 and logged no leaks, but the executed binary
identity was not retained, so secret absence is not claimed. Coverage and SBOM artifact bytes were
reconciled, while LCOV summary rederivation, coverage adequacy, CycloneDX schema validation, SBOM
completeness, and source correspondence remain false.

### External capture and negative custody

```text
sealed capture: /private/tmp/pid-rs-c3-dfb-hosted-capture.X86sht
manifest:       32169 bytes, 5ebdc4b7651aa7b0d890906103e9f2ee16759af039db6d2a1d36125a01a6d1bd
nodes:          23 directories + 168 files = 191; 11156416 regular-file bytes
archive A/B:    11298304 bytes each, 6565282572287d25781591afcc3e856e8d5d3cc7fa2db0d9e97090eebb7d0ea5
archive audit:  621 bytes, 95fa5f247e840c55d41631c9386c077470ab3dc44e9db59316ed76c062ef403b
fresh extract:  exact manifest equality; manual dirfd/no-follow; no system tar/extractall
replay x4:      5083 bytes each, mode 0400, 15a9b569dff342947edddd8a30a95ba4015b49d9d1ad40df13a319eedb4e5a94
```

The replay uses exact Python 3.14.6 bytes under isolated/no-site/no-bytecode settings and directly
compiles digest-checked source snapshots. Frozen suites are ZIP 77, artifact 27, terminal 50, and
USTAR 44 controls. These are correlated bounded mutation suites, not 198 independent replications
or exhaustive attack coverage. The sequential manifest excludes ownership, timestamps, ACLs,
xattrs, BSD flags, resource forks, and Finder metadata. The local archive is not atomic,
authenticated, tamper-proof, remotely durable, externally attested, or a transparency log.

The sealed capture contains prehost `C3-FMT-N001`–`N014` plus hosted/capture `N015`–`N042`.
The acyclic receipt additionally records `N043`–`N053`. Thus 53 identified negatives remain zero
credit; absence of unlisted failures is not claimed. In particular:

- N045 records and repairs four external replay summaries initially left at 0644;
- N046 corrects a guessed full Lean tag SHA to exact
  `f3b06c705e6c85f5314019d5d3baab0fec5b580c`;
- N048 records a reviewer violating the copy-only rule by running `git write-tree` on the original
  sealed alternate index after subject publication. The semantic tree, 71,520 bytes, digest
  `3e0b5471…7c4`, and one-link count remained exact; Git changed mode 0400 to 0644 and advanced
  metadata. Mode is restored to 0400, but continuous post-review raw-index metadata custody is
  false. Pre-commit/pre-push custody and the published subject object remain true.
- N050 replaces a stale unqualified draft timestamp with distinct draft-start/finalized fields.
- N051–N052 remove execution-proof and premature-durability wording from the human receipt.
- N053 records a rejected no-op multi-file resume patch whose context did not match.

Independent archive review returned bounded GO after N045 correction, with original and extracted
manifest/content fingerprints unchanged. Independent exact JSON review returned bounded GO for
the 43,967-byte `c2ef8214…ddd44` machine receipt. Scope review found no PID-family, security,
mathematical, or closure transfer after N048 was explicitly time-scoped. These are separately
prompted reviews, not institutional independence.

### Lean 14576 next exact stop

Hosted dfb logs observe Lean 4.32.0 commit
`8c9756b28d64dab099da31a4c09229a9e6a2ef35`. They receive execution credit and zero post-fix
kernel-soundness credit; they are not themselves a witness that any theorem or all mathematics is
false. The fixed target is official Lean 4.32.2 tag commit
`f3b06c705e6c85f5314019d5d3baab0fec5b580c`.

Preserve and resume the existing dirty candidate, not a reconstruction:

```text
candidate: /private/tmp/pid-rs-lean14576-work.WGq8oG
base HEAD: f6fde520b841c61b7752cdd053af59bda763d3d1
receipts:  /private/tmp/pid-rs-lean14576-receipts.Ts6khF
state:     12 tracked modifications + audit/formal/lean-security/ + two new 14576 checker files
```

Prior observations are candidate evidence only: the affected 4.32.0 issue witness under
`--trust=0`, and fixed 4.32.2 replay 14/14 under the selected Lean executable and same-kernel
`leanchecker --fresh`, with 321 declaration slots, 243 theorem slots, 215 distinct qualified
theorem names, and 28 duplicate-name slot excess. This is not a theorem-body-equivalence count.
Re-run normal and optimized exact-source routes, independently review sources/receipts, retain
every negative, and make a separate small milestone. `--trust=0` requests checking of imported
declarations and declines macro trust; it is neither an independent kernel nor a repair for a
faulty kernel. `leanchecker --fresh` rebuilds an empty environment and replays declarations through
Lean's same kernel, so an independent-kernel route remains open.

### Remaining ordered program

1. Publish and externally observe this four-path acyclic receipt milestone; observe its hosted CI
   without calling that run self-custody.
2. Close the fixed Lean 4.32.2 exact-source/trust-zero/independent-kernel milestone above.
3. Close repository-wide isolated Python verifier custody and KSG M1c with acyclic typed receipts.
4. Complete the premise-explicit semantic audit and PID2 revision 4.
5. Complete categorical MGW SxPID3 Programs A–E and all 108 coordinates.
6. Complete bounded falsifiable frontier mathematics, the research-process and method papers,
   machine/PDF artifacts, and every final formal, numerical, compiled, statistical, property/fuzz,
   coverage, security, SBOM, identity, package, platform, Python, release, and authorized downstream
   gate.

Never transfer claims among KSG, Ehrlich continuous PID, categorical MGW SxPID, Williams--Beer
`I_min`, fitted quantized PID, heuristics, or wrappers without a mapping theorem whose premises are
established for that application. Preserve the dirty primary checkout, the Lean candidate, every
other dirty/divergent worktree, rejected tuple, and external capture. Use isolated worktrees and
alternate indexes; never stage wholesale; make small unsigned fast-forward commits directly to
`main`.

## Historical checkpoint - C3 hosted format-custody correction in progress - 2026-08-06

This section supersedes every lower checkpoint for execution state. Goal
`019fadc8-9091-7950-890f-bde9e9b75e02` remains active. The evidence-weighted whole-program estimate
is 28% with a 23-33% uncertainty interval; C3 is about 95% but is not closed. Counts are not
scientific replications and no later milestone receives credit from C3.

### Exact state and retained hosted negative

```text
correction worktree: /private/tmp/pid-rs-c3-hosted-receipt.65QZZA/worktree
HEAD:                e53dc427d082dd936024782f62c795db743fc893
origin/main:         e53dc427d082dd936024782f62c795db743fc893
status:              bounded local gates/reviews green; alternate-index commit/push pending
CI run:              31071608249 (exact e53dc427; not green)
formal-PDF job:      92520513307 (terminal failure; zero closure credit)
CodeQL run:          31071608063 (4/4 success; no transfer to failed CI)
```

The formal-PDF job failed because build-a pass 1 loaded ambient
`/var/lib/texmf/web2c/luahbtex/lualatex.fmt`. Its 109,239-byte raw job log has SHA-256
`233ed7c120190d245241e40ee8e056f82b71fbc7ab4dd7d675f94cd6acdd8730`. Preserve that result as the
hosted counterexample that invalidated the broader portability claim. The historical pre-host
`workflow-pdf-luatex-map-free-correction-2026-08-06.{md,json}` tuple and 266-control partition are
frozen history; do not rewrite them as hosted success. At the last poll, the same CI run had 43
successful jobs, this one failure, and one still-running KSG assurance job. The terminal roster is
now known: 45 CI jobs, with 44 successes and this one failure; KSG job `92520513310` ultimately
succeeded but receives no C3 transfer credit. CodeQL is a separate four-job workflow. Across both
workflows there are 49 jobs, 48 successes and one failure; this is not a single 49-job run and
those facts do not splice into a future correction run.

### Current narrow correction

The checker now requires the exact selected
`$TEXMFSYSVAR/web2c/luahbtex/lualatex.fmt`, captures its bounded bytes through no-follow
descriptors, re-walks the source path, publishes one exclusive single-link mode-0444 copy beneath
a sealed mode-0555 one-file root, and verifies its exact size/digest before each compiler pass and
after both builds. Literal `TEXFORMATS` has no leading/trailing colon; clean Kpathsea preflights
require both `--show-path=fmt` and selected-format outputs to equal the private root/path. The FLS
validator requires raw and resolved `.fmt` sets to equal that pathname and admits it by exact
equality, not by allowing `FORMAT_ROOT` or `TEXMFSYSVAR` generally.

The following tuple was the first 280-control implementation reviewed and is now source-superseded:

```text
8c4002ebe799c767f1b32bffcdc77ec426b064425abc1c1d4682ad0e03b96454  scripts/check-mathematical-workflow-pdf.sh
b7934c8f2420665f738f884559194e6fd6c58b89258ae6486ff69ce2ce85f033  scripts/check-mathematical-workflow-pdf-self-test.sh
2df32319f872cb69e6aebb504945d178afab8a21f9efc7e9cfb525d8cbb528a8  scripts/README.md
44cd09a29bcaecca30409f7093802a95f5cd9305c938cfb4376b842ea9401480  CHANGELOG.md
f372256011d1173a020d39b86cba5ab7959fb07cea09cf1a2b7eeb292a83cafe  output/pdf/mathematical-problem-solving-workflow.pdf
847685d91b6a565ba37c077515396e3bb83fb1ed18d295a14b4eb3ebe9bedcaf  output/pdf/mathematical-problem-solving-workflow.rendering-receipt.tsv
```

The direct suite passed exactly 280/280 controls, and an isolated exact checker on that source
passed with a 416-byte log `bccde8f5...`, but both results now have zero closure credit. Two
separately prompted reviews found that the separately implemented format capture/replay code could
not inherit the font helper's symlink/FIFO/race tests and that the final log omitted the captured
format size/digest. A later 301-control exact run produced a 597-byte green log with SHA-256
`017a55a2c593af3bd4f2341f969c5a9fcd3e7658583cb25fa0456de2e4cb5846`; it too has zero closure
credit because a fresh mutation review found surviving empty/oversized-source,
compiler-environment-consumption, verifier-order, and complete-receipt mutations. The next exact
311-control replay produced a 23,990-byte green self-test log with SHA-256
`1a6be60a819ec74cc240cf5994a882927ed35c0afc12b31b9c94c4be01a90c70`, but its outer zsh receipt
wrapper then tried to assign the reserved read-only parameter `status` and exited 1 before writing
the intended post-source tuple. It receives no final credit. More importantly, the adversarial
review found two surviving case-sensitivity mutations in raw versus resolved FLS format
classification, so those 311 source bytes are superseded regardless of the wrapper defect.

The current candidate target is 313 controls with frozen partition
`194 + 37 + 17 + 7 + 8 + 3 + 47`. Its exact production-checker source is
`6e1fc6eef6286b9e475d758419400e6c9a102d369bb5e1fd98b00a3b68ced833` and its exact self-test source
is `c7902373cca3cbcdf042cd2e093d1601f1f81929afdf189ba44c665153a2eae1`. The two added controls
separate (1) a mixed-case raw `.FMT` alias resolving to a neutral target from (2) a neutral raw
alias resolving to a mixed-case `.FMT` target; together they kill independent raw-classifier and
resolved-classifier case-sensitivity mutations.

The final direct replay passed 313/313 in 121.28 seconds. Its 24,164-byte log has SHA-256
`9f6c91de47bbc5fb7d36f0fd55885b25402909b7ebe8cef8495c8461ef8e0166`; its before/after two-source
manifests are byte-identical with SHA-256 `2a869a2b8ef7f77dfb43bcad9ee0e6d447dfadb0ad96045590f1a905d75a038e`.
Two separately prompted reviews returned bounded GO on the exact production/self-test tuple. The
adversarial review observed the raw-only casefold mutant die at control 134 and the resolved-only
mutant die at control 135. These reviews are not institutionally independent.

The first full exact attempt failed closed after 833.63 seconds because the unsafe-root probe
published no atomic decision record; custody status 125 is not creditable. Concurrent reviewer
replays make contention plausible but do not establish cause, and a later focused status-2
reproduction does not repair that failed run. The subsequent serial full exact checker passed in
765.72 seconds with an unchanged seven-object source manifest SHA-256
`24a08a3efdc65fa8d7ac579c07904ded089ba9980853386b0c2234c34172de0a`. It rebuilt both isolated
reports and retained PDF `f3722560...`, rendering `847685d9...`, executable `5053eb6d...`, pypdf
`dc0d7ee2...`, and format `e254bc4c...` receipts. All 51 color and 51 grayscale pages were reviewed
in order; 22 high-risk pages were opened at original render resolution; no visual defect was found.
The certified-SxPID2 enclosing checker passed normal/optimized execution and 111 mutations in each
mode after rebinding only the final scripts-documentation digest.

Earlier diagnostic attempts also receive zero credit: a non-unique heredoc extraction marker,
malformed expected source-literal bytes, an overbroad fixture edit that created
`format/lualatex.fmt` as a directory, and an absent sparse-file fixture that raised
`FileNotFoundError` before the intended oversized-source mutation. Each failed closed or aborted
before a credited final replay.

The first successor precommit verification also receives zero credit. Its zsh loop used the
special tied array parameter `path` as a loop variable, which rewrote `PATH`; later `git` calls
failed with command-not-found before commit construction or push. `HEAD` and `origin/main` remained
`e53dc427d082dd936024782f62c795db743fc893`. The previously checked 71,520-byte alternate index
(SHA-256 `d794bb5b...`, tree `a7a91dcb...`) is now intentionally superseded because recording this
negative changed the evidence bytes. Build a fresh index and never reuse that tree.

A second successor index and local commit also receive zero credit. The 71,520-byte index was
shared by pathname with a reviewer; a later Git operation rewrote index cache metadata, changing
its SHA-256 from `06e4b87d...` to `d1228eba...` while leaving semantic tree `a34b461c...`
unchanged. The delayed review returned NO-GO after unsigned direct-child commit `eecea3d...` had
been created locally. It was never pushed: remote `main` remained e53, and detached `HEAD` was
returned to e53 with `git update-ref --no-deref` without changing worktree files. The replacement
must keep the final original index private and byte-frozen, give reviewers only copies, construct
the commit from the already verified tree, and prove the original index hash unchanged afterward.

This correction does not authenticate TeX Live, attest format generation, establish cross-platform
format or PDF byte identity, sandbox pre-wrapper execution, make FLS a syscall trace, defeat
privileged/same-UID replace-and-restore, validate mathematics, or transfer assurance among KSG,
Ehrlich continuous PID, categorical MGW SxPID, Williams-Beer `I_min`, fitted quantized PID,
heuristics, wrappers, or Lean.

### Next sequence

1. Finalize and cross-check the new acyclic successor evidence MD/JSON, including every local red
   predecessor and the bounded local GO routes above.
2. Stage only enumerated paths through a task-specific alternate index; verify tree, modes, hashes,
   whitespace, parent projection, unsigned/no-attribution commit, and fast-forward push.
3. Require a new exact-commit terminal all-green CI and CodeQL run. Only a strict descendant receipt
   may close C3.
4. Next, replay all Lean sources on fixed stable v4.32.2 with exact-source `--trust=0` and
   `leanchecker --fresh`; preserve v4.32.0 receipts as stale assurance rather than calling theorem
   sources invalid. Then close Python/KSG custody and the separately scoped PID-family work.

The semantic audit remains queued outside this engineering correction: repair Python scalar/report
family identity, Barà versus Schick-Poland attribution, the false blanket deterministic-map/infinite-
MI sentence, MGW/Ehrlich naming, heuristic language, target-free degree naming, categorical
alphabet/frozen-map premises, and ecosystem routing before PID2/MGW publication closure. No such
semantic repair should be smuggled into the format-custody commit.

## Live checkpoint — C3 map-free workflow-PDF correction, local evidence frozen and reviewed — 2026-08-06

This section supersedes every lower live checkpoint for current execution state. Lower sections are
dated history only. Goal `019fadc8-9091-7950-890f-bde9e9b75e02` remains active; do not mark it
complete or restart closed milestones. After compaction, read only:

1. `codex-goal-prompt-2026-07-26.md`;
2. this section;
3. `workflow-pdf-luatex-map-free-correction-2026-08-06.md` and its JSON companion;
4. live Git/agent state; and
5. a named older record only to resolve a concrete provenance conflict.

### Exact current state

```text
candidate:   /private/tmp/pid-rs-c3-wrapper-mapfree.SXEX3D/worktree
HEAD:        30c8fa831407ad3d485f8ed636c52a2d85d03ffa
HEAD tree:   f7808e1db0195c0c0b6c65b828a068e5f3d64f55
origin/main: 30c8fa831407ad3d485f8ed636c52a2d85d03ffa (last authenticated candidate parent)
C3 root:     8b792bc143fff2d84f2d8e7817d1de7850741223 (verified ancestor)
lifecycle:   precommit; local exact tuple frozen/reviewed; alternate-index commit/push and hosted CI/CodeQL pending
```

The ambient checkout and every other dirty/divergent worktree remain user-owned and must not be
cleaned, reset, pruned, or staged wholesale. Use a task-specific alternate index, enumerate every
path, and never use `git add -A`.

Current reviewer-candidate bytes are:

```text
953476d708cc52e9e4d11dddaf06dc3c4a1d96e0f16a6fa193dade48eedc3ab3  CHANGELOG.md
c688611be7460766804ef3a497e2a63c3395ee92a94140ebce75591a94667f2b  scripts/README.md
df7dc39c85220e16b94a230c964e52619f9b623e446c181e198a3b3a755540e1  scripts/check-mathematical-workflow-pdf.sh
b33dd4d52d788fe5d88aefb8db575c032bbb509fabadb3288f5926cb7f490f3c  scripts/check-mathematical-workflow-pdf-self-test.sh
b3725b9a2a85005c342c9277a34ba7651249a954f19d70a707038a8ec648b040  scripts/check-certified-sxpid2-claim.py
2397e8da3d45818a72418bc3894ac8e9d73bbbb7400886c6c03b24df78c6e944  audit/evidence/workflow-pdf-luatex-map-free-correction-2026-08-06.md
8312e5bfba9e16184ea39fac09a22baee2e38e82bc19629672da8ce8dafa22ad  audit/evidence/workflow-pdf-luatex-map-free-correction-2026-08-06.json
```

These are the final precommit evidence bindings. If any artifact moves, recompute the tuple and
discard mixed-byte review. The JSON froze first, its digest is bound into the Markdown, and this
resume was updated last. This resume file does not attempt to hash itself.

### Current evidence disposition

- Bash syntax and ShellCheck 0.11.0 passed on exact self-test `b33dd4d5…` and production checker
  `df7dc39…`. JSON schema/count/arithmetic, all declared source/artifact mode-size-digest checks,
  tracked and initially untracked whitespace checks, and session-log digest checks passed. Any
  source/evidence edit invalidates the relevant result; alternate-index cached-tree gates remain.
- The current direct-suite target is exactly 266 controls with frozen partition
  `194 predecessor + 37 bounded-probe + 17 entry-wrapper + 7 runtime-map + 8 FLS-map-path + 3
  executable-custody`. The primary replay passed 266/266 in 108 seconds on exact self-test
  `b33dd4d5…` and production checker `df7dc39…`; its 20,343-byte log is `b23a3ed8…`.
- Two 246-control passes, one correlated replay, and the earlier exact checker are
  source-superseded. Their historical facts remain in the dated ledger but have zero closure
  credit. No result transfers from those superseded sources.
- A separately launched exact-source correlated replay passed 266/266 in 110.34380087489262
  seconds. Its 20,343-byte log is again `b23a3ed8…`; 6,720-byte raw metadata `a923fde7…` records
  child PID and derived PGID 26102, 706 samples, 1,579 descendant PIDs, 417 descendant PGIDs, and
  zero rows in the immediate post-exit snapshot and follow-up. It is
  same-source/host/toolchain/validator/fixture corroboration, not independent scientific evidence
  or generic containment. The raw log/metadata are session-local; only their digests and selected
  facts are durable.
- The fresh isolated exact checker passed in 373 seconds on unchanged four-source tuple
  `130c091c…`. Its 416-byte session-local log `bccde8f5…` binds the 626,770-byte, 51-page PDF
  `f3722560…`, rendering receipt `847685d…`, executable manifest `5053eb6d…`, and `pypdf` manifest
  `dc0d7ee…`. The prior source-superseded exact pass remains zero-credit history.
- All 51 color and grayscale pages were rerendered/reviewed; fresh original-resolution spot checks
  covered pages `3,4,9,10,15,18,20,27,30,37,40,43,47,51`. The PDF source and bytes are unchanged,
  so no artificial PDF diff was created.
- The certified-SxPID2 checker is rebound to final README `c688611b…`. Normal/optimized claim
  checks passed and 111/111 mutations were rejected in both modes; logs are `09dacad5…` and
  `1e4027c2…`. This is enclosing custody, not new SxPID mathematics.
- A separately tasked terminal review and its child schema audit independently returned content GO
  on frozen JSON `8312e5bf…` and the pre-bind Markdown. The digest-only JSON binding produced final
  Markdown `2397e8da…`; both reviewers verified the 68-entry ledger, 266 arithmetic, source/artifact
  custody, raw-metadata projection, exact tuple, premises/nonclaims, PID-family firewall, and
  tracked/untracked whitespace. This is independent review execution, not independent scientific
  evidence.
- Two authenticated reads of predecessor KSG job `92381239220` and one independent-agent read
  matched 119,501 bytes SHA-256 `c9120f2298ea43dee2eebfbdc1babfb3340f0a0ce78cff41deef88c0859d2903`.
  The failed PDF job `92381239226` matched 96,604 bytes SHA-256 `75dfa1b6…`. Predecessor run
  `31027991226` remains 44 success / 1 failure / 0 other; CodeQL run `31027989770` is 4/4 success.
  No predecessor success transfers into the correction.

The dated report currently freezes 68 negative results. In particular, reject all 237/243
provisional runs, the stale-count run, the uncaptured-command run, the mixed-source reviewer run, the pre-final
246-control run, and the interrupted exact run. The latter left one outer source-snapshot self-test
group after deliberate Ctrl-C; exact PGID 56603 was cleaned and absence confirmed. External
cancellation containment remains an explicit nonclaim. The first alternate-index attempt also
stopped before tree creation when its staged whitespace gate found four hard-break spaces in the
then-untracked evidence report. A subsequent 29-entry tuple was also rejected before staging
because one row prematurely claimed review completion while the same tuple declared review
pending. Later retained failures include unreachable malformed-status custody, ShellCheck SC2016,
direct-final partial visibility, a 19-control reviewer replay failure, mislabeled/harmless mutants,
incomplete three-kind decision-record custody, standalone executable-custody overclaim, double
readiness grace, contradictory stage metadata, missing prose propagation, and a scheduler-racy
watchdog-error fixture. A subsequent 257/257 pass on `68948f27…` is also zero-credit because its
wrong-mode fixture transiently exposed mode 0600 before `chmod 0644`, and its invalid-readiness
fixture could expose partial canonical status; its retained log is `67c0385e…`. The replacement
uses one atomic status helper. The elapsed-delay control was also narrowed because it does not prove
parent observation of partial readiness. Subsequent review also corrected invalid-readiness
handoff order, exact timer sequencing, and missing decision/readiness guard mutants; the target is
now 266 controls after adding timeout/watchdog payload-condition mutants. The corrected artifacts
passed fresh review/replay; alternate-index staging remains.

### Bounded scientific and security scope

The correction is engineering-only. It changes no PID estimator, mathematical source, Lean source,
figure source, Rust/Python numerical path, method object, or statistical result. It establishes no
mapping or transfer among KSG MI, Ehrlich continuous shared exclusions, MGW categorical SxPID,
Williams–Beer `I_min`, project-defined fitted-quantized SxPID compositions, heuristics, or wrappers.
It makes no mathematical,
Lean-kernel, citation, accessibility, authenticity, vulnerability-absence, or security-clean claim.

The source-level semantic audit completed alongside C3 found targeted later blockers, not wholesale
mathematical invalidation: Barà uses Williams–Beer `I_min`; Python report/scalar wording and aliases
can blur families; several top-level descriptions say “Wibral PID” too broadly; target-free degree
ratios are misnamed in one map; ecosystem categorical routes need explicit alphabet/transform and
held-out-fit premises; and the pending SxPID3 certificate should enforce nonnegative informative
and misinformative component atoms while allowing signed-net atoms. Do not edit those families
inside C3. Route them as the first semantic-custody milestone after C3 closure.

### Next exact sequence

1. **Current:** build an alternate index from exact `30c8fa8`; stage only the five
   implementation/docs/rebind paths, two dated evidence artifacts, and this resume update. Verify
   the alternate-index tree, modes, hashes, parent projection, and absence of unrelated changes.
2. Re-fetch `origin/main` and require exact `30c8fa8`. Create one small professional unsigned
   no-attribution commit, verify it is a fast-forward direct child, and push directly to `main`.
3. Wait for terminal exact-commit CI and CodeQL. Formal-PDF, KSG, certified-SxPID2, Python,
   package/platform, and security jobs must all be green in their own runs; never splice jobs.
4. If any hosted job fails, retain the exact failure and create a new correction child. If all are
   green, add a strict-descendant hosted/security/alternate-index receipt that binds implementation
   commit/tree and run/job/log facts without self-reference, commit/push, and wait for its gates.
5. Only then close C3 and begin the queued repository-wide Python verifier/semantic custody wave,
   followed by KSG M1c, PID2 revision 4, categorical MGW SxPID3 Programs A–E/all 108 coordinates,
   bounded frontier work, process paper/PDFs, and final release/downstream gates.

Do not mark the active goal complete at this checkpoint.

## Live checkpoint — KSG revision-4 settled pre-M1a replay — 2026-07-27 18:47 UTC

This section supersedes every lower “Live checkpoint” section. Those sections are dated evidence,
not current Git, hash, mutation-count, or gate authority. After compaction read, in order:

1. `codex-goal-prompt-2026-07-26.md`, SHA-256
   `dc984b2586970c71a6eafe262604dd9e8d6b988723a8aa6b46df8ae7d58adab2`;
2. `completion-handoff-2026-07-26-ksg-rev4.md`, SHA-256
   `61ba9897f7323a88bccc9f683d752cbb0a1408e1ec71268615c5619d9aeacf29`;
3. this top live section;
4. `claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json`; and
5. live Git/agent state. Read raw external-model responses only for a named disputed allegation.

Goal `019f9ec9-2763-7ae3-9532-2169a23307f0` is active with the compact continuation objective below.
At the user's explicit request, the goal service replaced its earlier blocked objective while
retaining the same thread ID; the complete normative scope remains pinned by this file and its two
authenticated entry documents. Do not mark the goal complete until all milestones actually finish.

### Compact continuation goal for `/goal`

Use this bounded prompt in a fresh goal; the full objective and state live in this file:

```text
Continue the unfinished pid-rs/Wibral PID scientific program from the authenticated durable resume at /Users/torusprime/Development/sepahead-github/pid-rs-ksg-rev4-candidate/audit/evidence/completion-active-resume.md. Authenticate origin/main and start at the first genuinely incomplete milestone; do not redo closed work. Close KSG M1c if open, then PID2 revision 4, categorical MGW SxPID3 Programs A--E/all 108 coordinates, bounded falsifiable frontier work, the research-process paper and complete PDFs, final release gates, and only authorized downstream integrations. For every claim require at least five failure-diverse lenses, exact/formal/numerical/compiled/statistical/custody evidence as applicable, mutations and counterexamples, explicit bounds and negative results, no transfer or overclaim, and small unsigned fast-forward commits pushed to main.
```

If this worktree is later removed, use the repository-relative path
`audit/evidence/completion-active-resume.md` from the authenticated `origin/main` checkout.

```text
candidate:   /Users/torusprime/Development/sepahead-github/pid-rs-ksg-rev4-candidate
branch:      codex/ksg-rev4-candidate-20260726
HEAD:        a9aa60c962261a6e0e6698b05551fbcdbf7bf41c
HEAD tree:   88a8dd7a39fed07fcf4be03f3ec3ae6fd7c17e6f
origin/main: a9aa60c962261a6e0e6698b05551fbcdbf7bf41c
policy:      110 exact anchor-delta paths = 38 M + 72 A; no deletions
baseline:    142 changed paths and 401 protected paths
lifecycle:   precommit-worktree; candidate-tree=not-requested is diagnostic only
```

The ambient checkout is the preserved mixed multi-wave tree. Never stage it wholesale, never use
`git add -A`, and never import later PID2/MGW/PDF bytes into this milestone. The candidate is an
ordinary isolated Git worktree. `afc45ff27e5af7fe04e44f2bb9f4147fb472c81e` is only a provisional
historical checkpoint; it is not canonical M1a and cannot authorize M1c.

### Scientific and lifecycle state

The bounded positive-integer KSG arithmetic core is GO only on the declared arithmetic/helper and
finite-corpus domains. Repository/publication integration remains **NO-GO** with all 13 final gates
open by construction. `x+y<=n+k` is a conditional source-set lemma requiring the eligible
positive finite unique-shell, strict-radius/predecessor, exact-count, and correct-map premises. It
is not promoted into the revision-4 theorem inventory. The stronger balanced lower-bound candidate
remains unpromoted. No result here transfers to KSG consistency, support, Ehrlich calibration,
PID2/PID3, categorical MGW SxPID, fitted quantized estimands, uncertainty calibration, or consumers.

Settled current authorities are:

- active packet `898414abc5bed5af483a966399bf68cbad8892a3c67da241555947d565c55585`,
  70 mapped files, 35 frozen historical hashes, `integration_no_go` preclosure stage;
- method catalog `1d1f1765209062b8fdc31faed1870de960c53f50ac8d3925a8ac27198aeab313`
  and generated METHODS `93bb2ee315813c2b6eef659fbfa9b98dba9573530f42f143ff24fb35b2dbdf00`;
- assurance registry `5ceb2e47469dda5b8750ba8627014a7b634596ea4ae74c0b52873e19fe8d8a9a`
  and checker `6f5c34a8bcfcb3b1b3cb666f955c6ef35b024cc4073214fbe677aa1b61140ade`;
- ecosystem contract `7dfcbc634d7f055142be0e698f0bf030c39a27d3d7b10d14600c4160db7284fc`,
  identity reference `00c24c8633e469490ab701fbc0ebe6c771d87d92000176f88f7398d7c15c65be`,
  and unchanged release scope `4fe9e5e4ba7b31a609b73127ee7c34ffcd33765e87363c1b50f3d26145c4319d`;
- manually reviewed phase policy
  `dd2c6fe127c8cd129a85f630a298317c6b20893f4b71a802a16e9df64c4894c9`.

### Settled replay and retained negative results

- Claim custody passed normal/optimized and rejected `141 = 3 + 65 + 73` mutations. The broader
  route suite passed normal/optimized and rejected `175 = 16 + 2 + 12 + 35 + 74 + 36` mutations.
- Exact rational/enclosure replay checked all 8,198 rows, 6,920 exhaustive outer-box containments,
  all 8,198 exact `Fraction(Decimal)` differences, `29/29` registered mutations, and separate
  `2/2` comparator controls in both modes. The exact maximum is
  `409/(5*10^78) = 8.18e-77` at row 7952.
- Modular replay classified `354` endpoints and `7,844` nonendpoints in each selected field and
  rejected `28/28` mutations plus separate `2/2` strict-JSON controls in both modes. The retained
  four rejected-prime rows are one reflected `H_999999-H_3` event. Composite
  `1000001=101*9901` reaches the bounded Miller--Rabin witness-loop path; it is not a primality
  theorem.
- Z3 passed four positive preflights/four negated obligations and `12/12` semantic countermodels,
  with `52/52` lexer/profile/type/pin/snapshot/stdin/result controls separate. The well-typed wrong
  theorem still passes after deliberate raw+token dual rebase; statement intent remains a human
  and independent-route cut.
- Lean passed 19 kernel-checked theorems and `14/14` mutations in both modes with the reviewed
  Lean 4.32 binary. A plain `/opt/homebrew/bin/lake` run first timed out while elan downloaded the
  toolchain; it is retained as an operational failure and is not counted. Final Lean commands must
  prepend `/Users/torusprime/.local/engram-reviewed-tools/lean-4.32.0/bin` to `PATH`.
- Phase policy-only advisory promotion and obligation-promotion rebases are rejected. The hostile
  suite passed 79 attacks plus two separate JSON-type controls. C43 deliberately retains the
  unavoidable self-reference result: coordinated policy+checker mutation passes internally and
  with a post-hoc tree, while a pristine pre-pinned tree rejects it (`1/1` retained boundary,
  separate from killed attacks). Therefore M1a requires an independently recorded alternate-index
  tree and detached checkpoint; the two phase scripts obtain byte custody only there.
- The direct compiled fixture assertion now scans the full `+0/-0/nonzero = 354/0/7844`
  partition, checks finite reference/actual/swapped values, and retains W1/W2/W2b mappings. The
  complete settled-byte Cargo/Python/CI matrix still must be rerun before M1a.
- A naive whole-directory Gitleaks scan was rejected as evidence after traversing 1.59 GB of
  ignored build output, timing out, and reporting unadjudicated matches. An exact source-only scan
  then isolated 17 `generic-api-key` false positives: every candidate was a public 64-hex SHA-256
  under an API-snapshot or SMT token-stream digest field, and none had a known credential prefix.
  A first combined token-stream exception was itself wrong: independent differential testing found
  that it also suppressed 16 cross-syntax, half-quoted, and wrong-key mutants. That route is retained
  as a rejected overbroad allowlist. The correction uses four separate path/key/syntax-bound full-line
  rules. Gitleaks 8.30.1 then scanned 543 exact source files with no `.env` input: the default rule
  found 62 intended public digests, the corrected policy found zero, and all 48 negative controls
  (32 path/key/value controls plus the 16 syntax mutants) remained detected. The full-history scan
  also found zero. CI now regenerates eight distinct intended fixtures and all 48 mutants, requiring
  only the intended lines to be suppressed. Rerun both scans on the final commit before crediting
  the security gate. The
  earlier independently reconstructed 109-path tree `8e75dce68905ac0c7b07b666668cd0b455796ac6`
  is superseded process evidence only and is forbidden as M1a custody.
- The pinned seven-target fuzz smoke passed 128 deterministic runs per target, but running it in
  the candidate worktree also refreshed a pre-existing stale `fuzz/Cargo.lock` after the earlier
  `same-file` dependency addition and emitted 195 untracked learned corpus inputs. Those operational
  mutations were restored/removed and are excluded from M1a. A separate gate-hardening milestone
  must update and lock-check the fuzz dependency graph and run mutable corpus discovery in a
  quarantined copy; the successful smoke is evidence about those executions, not clean-tree
  reproducibility and not KSG science.
- The certified-SxPID2 umbrella replay passed its Rust/MSRV/static-policy/independent-verifier,
  exact-product, 308,856-coordinate nonsyntactic-zero exhaustion, 5,921-table evolutionary
  falsifier, Lean exact-log-product, claim, and mutation sub-gates. The evolutionary result is only
  a seeded bounded failure to find a counterexample. The first umbrella attempt used the wrong
  Homebrew `lake` route and timed out; the reviewed Lean 4.32 route passed. The second attempt then
  exposed a real final-command defect: cargo-deny 0.20.2 rejected `--config` after `check`. The
  corrected global-option order independently passed advisories, bans, licenses, and sources, and
  the recipe now runs that cheap policy/CLI preflight before every evidence-producing command. Both
  attempts transiently rebound a protected SxPID evidence file to a locally rebuilt executable;
  exact anchor bytes were restored (SHA-256
  `2c663e0b6f9db2c8c70385515fff475ecb891afc9da491f79e67f3aadfc9db96`). No uninterrupted umbrella
  pass is credited on this KSG-only tree; future unrelated-gate replays must use a quarantined copy
  unless that milestone explicitly owns the evidence update.
- The nine deterministic formal PDFs rebuilt with their canonical hashes after prepending the
  reviewed Lean path. A root contact-sheet/page pass was followed by independent individual
  inspection of all 182 rendered pages by a read-only Sol Max reviewer. Visual/layout disposition
  is GO: no clipping, overlap, blank or
  truncated pages, broken glyphs, malformed visible equations, or unreadable tables/citations.
  Workflow-paper pages 23--24 and 27 retain readable but inelegant inline-code wraps for the later
  comprehensive-PDF typography pass. This visual result does not validate the mathematics,
  citations, semantic parity, or scientific claims; those remain separately gated.
- A fresh primary-source applicability audit matched KSG Algorithm 1's strict marginal counts and
  `+1` arguments (DOI `10.1103/PhysRevE.69.066138`), Ehrlich's strict disjunction/target counts
  including the query anchor (DOI `10.1103/PhysRevE.110.014115`), and DLMF equation `5.4.E14`'s
  positive-integer digamma identity to the exact objects used here. The official 2011 KSG erratum
  (DOI `10.1103/PhysRevE.83.019903`) retracts only the Appendix covariance-only extremum/lower-bound
  claim; an exhaustive source-tree search found no use of that claim. Empirical paper language such
  as “minimal bias” or “exact for independent distributions” is not promoted to a theorem or project
  guarantee.

Five Fable 5 Max calls completed against context SHA-256
`fe0798be2f1902f7043a3615201ec0ddf691967dd936cb9515699786da5be49a`; receipt SHA-256 is
`affcbbd127bf417473ae1a8bba030845e52b796174bb3293561e4c1adeb249ab`.
All five configured Anthropic aliases are provider-confirmed `credit_exhausted`; make no further
Fable 5 or Opus 5 calls unless credit externally changes. Their 14 files are exactly pinned as
advisory attack records and excluded from claim authority, catalog evidence, and assurance rows.
Use independent Codex agents instead. A stale unbounded Fraction process was sampled and stopped;
it produced no artifact and is not evidence.

### Next exact sequence

1. Reseal the generated phase facts once more after this resume update; rerun phase normal/-O and
   the complete 79+2+retained-1 suite in both modes on the final bytes.
2. Obtain independent Gitleaks and alternate-index custody verdicts only after explicit final
   quiescence; no earlier reconstructed tree is reusable.
3. Run focused compiled witnesses, Rust debug/release/serial/parallel/no-default/all-feature tests,
   fmt, clippy, rustdoc/docs.rs, review/catalog/ecosystem/identity/release checkers and self-tests,
   Python wheel tests, packaging/security/SBOM/API/coverage/property/fuzz/MSRV gates required by
   the normative handoff. Re-run any gate whose input moves.
4. Build an exact alternate index from the 110 policy paths, write a detached checkpoint child of
   the declared anchor, record tree/commit/checker/self-test hashes outside the two scripts, and run
   the phase checker with both explicit custody arguments.
5. Synthesize only those exact paths into the small unsigned no-attribution M1a commit, push to
   GitHub `main`, verify the remote SHA/tree and CI, and write the receipt while integration remains
   NO-GO.
6. Only from pushed M1a create the separately re-anchored M1c evidence matrix, decision, and final
   KSG receipt. Then proceed sequentially to PID2 revision 4, MGW SxPID3 Programs A--E/108
   coordinates, bounded frontier work, complete-detail PDFs, final release, and authorized
   downstream integrations.

Before any stop, refresh this top section without introducing a digest cycle. Never promote a
bounded route universally, count correlated runs as independent proofs, or weaken a gate to obtain
green.

## Live checkpoint — durable KSG recovery and assurance hardening — 2026-07-27

This section supersedes every temporary-worktree path below. Lifecycle goal
`019f9ec9-2763-7ae3-9532-2169a23307f0` remains active. Read, in order:

1. `codex-goal-prompt-2026-07-26.md`, SHA-256
   `dc984b2586970c71a6eafe262604dd9e8d6b988723a8aa6b46df8ae7d58adab2`;
2. `completion-handoff-2026-07-26-ksg-rev4.md`, SHA-256
   `61ba9897f7323a88bccc9f683d752cbb0a1408e1ec71268615c5619d9aeacf29`;
3. `ksg-rev4-recovery-ledger-20260727.md` and its JSON companion; and
4. this live section. Load older narrative only to resolve a named provenance conflict.

The durable candidate is:

```text
/Users/torusprime/Development/sepahead-github/pid-rs-ksg-rev4-candidate
branch: codex/ksg-rev4-candidate-20260726
HEAD:   ca24ab8ebade81a94ffc001531abaf5a5579d5e9
origin/main: ca24ab8ebade81a94ffc001531abaf5a5579d5e9
reconstruction base: 118e1de6a2d6d2ae33fe7bdc224736257e42a83f
```

The ambient checkout remains the preserved mixed multi-wave tree and must never be staged
wholesale. The absent `/private/tmp/pid-rs-ksg-rev4.E11L9g/tree` path is historical only.

### Durable state and evidence credit

Recovery checkpoint 1 is:

```text
ref:    refs/codex/checkpoints/ksg-rev4-recovery-source-1
commit: 94813b96990ae9ec2b9f2db368fe06e2de797dd6
tree:   04669a046910c7fa7f4e33cedca31aecd402a03d
bundle: /Users/torusprime/Development/sepahead-github/pid-rs-recovery-checkpoints/
        ksg-rev4-recovery-source-1.bundle
bundle SHA-256: 7b0bf3c63d82e28b58fd9a0150d2c6878adade08db4ba33a03ef92529ead295a
```

Recovery checkpoint 2 seals the byte-recovery-complete tree:

```text
ref:    refs/codex/checkpoints/ksg-rev4-recovery-complete-2
commit: 7eb959e3e3fd4bc2893cef83e6728b1594f8691b
tree:   423dd61a5284717db41a7dbda5702f7d81bd48f7
parent: 118e1de6a2d6d2ae33fe7bdc224736257e42a83f
paths:  109
bundle SHA-256: 23a1db4ae281c03723094093c4fa9e726867d07fd6406847f29542ec418f8078
external receipt SHA-256:
858c429e91418a3883cfd62a755c4da32dbb5be4c1fe7b801cef86930f83f6e2
```

The bundle was restored into a new durable bare repository; commit, tree, parent, strict `fsck`,
and source/restored archive digest all matched. This is recovery integrity, not authenticity,
scientific verification, or release closure.

The 21-path recovery/adjudication milestone was committed unsigned and fast-forward pushed:

```text
ca24ab8ebade81a94ffc001531abaf5a5579d5e9
audit: preserve KSG recovery evidence
parent: 118e1de6a2d6d2ae33fe7bdc224736257e42a83f
origin/main verified by ls-remote
```

This audit commit contains no scientific source promotion and does not change the integration
NO-GO disposition. Remaining candidate changes are unstaged.

Every lost preclosure byte has now been reconstructed and hash-verified. In particular:

```text
21a08acd99bfc5c5881a6d267382bc808075fb69bca9ae6f76b103775c5f3ee3  old Fable context
cfdf84ba5ca1e51c215b7785d577c7378e4836d213de12230caf5449f33e010b  old Fable receipt
b4cac94ca6b636d8f5433bc3e2112f5cee7c118aa60cff9a321ea1fdcaf7dd9a  old Fable response
```

The offline recovery program and 31-artifact manifest are stored beside those records. The
recovery used no network or `.env` access and passed secret-pattern, byte-count, UTF-8, and digest
gates. It recovers historical bytes; it does not rerun the model or establish integration.

The fresh max-effort Fable sweep attempted all five configured aliases. Three advisory reviews
completed (137339 output tokens, 100885 thinking tokens); two aliases returned insufficient-credit
HTTP 400. Receipt SHA-256:
`8f3308ecc873628bd675df3e974593eb130e855e591def8ce25e001fde56327b`.
Do not retry exhausted aliases merely to seek agreement. Continue with native agents and local
proof/numerical tools. No model output is proof.

Normal/optimized Z3, modular-certificate, directed-enclosure, and claim-only runs matched recorded
outputs after recovery. They are diagnostics, not final passes. Lean failed closed because the
former temporary Mathlib dependency checkout was absent; a pinned rebuild is in progress. Only a
complete replay after all writers stop on the exact isolated staged tree can support GO.

The old and fresh model allegations have been independently adjudicated in
`fable5-ksg-rev4-adjudication-20260727.{md,json}`. The human rendering SHA-256 is
`19d284f357eaaecdd63580663c184838f6d31b09fac01d4f08c90e177bb4afec`; the machine rendering
SHA-256 is `0fa2904476cd400720a752e497c8e463a4c54855d1f3091eeae89cb61b4c2919`.
The adjudication found no new bounded-core blocker. It accepted targeted hardening, rejected the
false universal `1/(n-1)` nonzero gap and the unproved universal `28 epsilon` claim, and preserved
all deferred routes as non-evidence.

### Current scientific disposition

The bounded positive-integer KSG arithmetic core remains GO on its declared exact and finite-corpus
domains. Repository/publication integration remains NO-GO. Do not transfer this result to KSG
consistency, continuous Ehrlich shared exclusions, continuous PID2, categorical MGW SxPID, I_min,
fitted quantization, PID3, wrappers, consumers, or applications without a separate mapping theorem.

The highest-priority open obligations are:

1. add a kernel-checked analytic/recurrence bridge for the digamma premise if the pinned Mathlib
   theorem really supports it; publish `#print axioms`, a subtraction-free statement, mutations,
   and shared cuts;
2. turn the independently checked all-unique W2 endpoint counterexample into a compiled regression,
   distinguish structural-zero endpoints from range extrema, and replace ambiguous “maximum
   harmonic denominator” prose with “maximum reciprocal summand denominator/index”;
3. harden phase isolation to use the current pushed anchor, an independently reviewed `A`/`M`
   policy, no deletions, exact ordered critical calls, strict Git/config/attribute custody,
   metadata replay, and an external tested-tree receipt;
4. regenerate moving claim/catalog/release/review/ecosystem/identity facts only after the preceding
   bytes settle; and
5. run every formal, mutation, exact, binary64, Rust debug/release/serial/parallel, docs, Python,
   release, security, and isolated-tree gate before a small unsigned fast-forward push.

Fable's proposed cvc5 proof objects, Kani/CBMC, Gappa/Flocq, MPFR/Arb, TLA+/Alloy, statistical
bounds, and exact categorical prime-log vectors are research tasks, not accepted results. A method
enters the evidence matrix only after its exact obligation, bridge, trust base, mutations, and
boundedness are demonstrated. The proposed exact prime-log representation is especially promising
for later categorical MGW SxPID3 but is not a KSG theorem.

### Compaction rule

After context compaction, reload only the four authorities at the start of this section, query the
active goal, inspect `git status --short --branch`, list agents, and authenticate the latest
checkpoint/bundle receipt. Do not reload whole model transcripts or deferred PID packets. Expand
only for a named disputed obligation. Before any stop or commit, update this live section and the
recovery ledger with exact paths, hashes, negative results, and the next executable action.

## Live checkpoint — KSG revision-4 preclosure integration — 2026-07-26

Read `completion-execution-plan-2026-07-26.md` and
`completion-handoff-2026-07-26-ksg-rev4.md` before the older narrative below. Lifecycle goal
`019f9ec9-2763-7ae3-9532-2169a23307f0` is active. The clean candidate is
`/private/tmp/pid-rs-ksg-rev4.E11L9g/tree`; the ambient checkout remains a preserved, contaminated
multi-wave worktree and must not be staged.

Candidate `HEAD` and `origin/main` are
`118e1de6a2d6d2ae33fe7bdc224736257e42a83f`
(`audit: record KSG formal milestone receipt`). The local `main` ref in the ambient worktree
remains at the delivery parent `9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56`; do not update it by
checking out or merging the mixed ambient tree. The M1a implementation commit is the unsigned
`afc45ff27e5af7fe04e44f2bb9f4147fb472c81e`.

The exact arithmetic core remains GO on its declared domain; repository/publication integration
remains NO-GO. The isolated candidate now contains the KSG-only production reassociation, W1/W2
bridges, recaptured 12-test serial/parallel constants, canonical modular and exact-enclosure
routes, revision-4 preclosure claim custody, 20-method catalog / 15-family release propagation,
review and ecosystem bindings, software identity, audience documentation, and KSG-only
automation. The active packet SHA-256 is
`aa88850c46644f899538bfeef0445f62b048e39a4c71e07f62a6cca04a740108`
and explicitly says `integration_no_go`.

Current bounded counts are: 19 Lean theorems / 14 mutations; four Z3 obligations / 12
countermodels; 8,198 corpus rows; 354 structural endpoints / 7,844 nonendpoints; 26 modular
mutations; 6,920 exact `Fraction` containments / 29 enclosure mutations; 49 claim mutations; and
161 integration mutations plus two scope-isolation preflights. The rounded-reference maximum is
exactly `8 * f64::EPSILON` nats on 40 rows. Under the stated Python `Decimal`
directed-rounding premise, the exact-rational maximum is uniquely below
`9.761311 * f64::EPSILON` nats. These are local arithmetic facts, not Rust-refinement, neighbor,
estimator, support, Ehrlich/MGW PID, calibration, or consumer theorems.

Hostile source and claim/document reviews found no remaining arithmetic or semantic defect after
their corrections. The full Rust profile matrix was green; Clippy subsequently found one
test-only range-loop warning, which was corrected and followed by green affected source/oracle,
Clippy, and rustdoc replays. The final full settled-byte replay is still required.

The immediate order is:

1. finish and hostile-review the exact Git phase checker and its mutations;
2. stop all writers, recustody moving hashes, and run the complete settled-byte gate matrix;
3. rerun the final generous Fable 5 review on the settled facts and independently adjudicate it;
4. construct and verify the alternate-index commit from the declared parent;
5. commit unsigned, fast-forward push `main`, then add immutable evidence/decision receipts without
   overstating the bounded arithmetic result.

## Status and authority

### Manual-resume handoff override — 2026-07-26

The user requested a comprehensive `/goal` handoff and a clean stop. Before using the older active
workstream narrative below, read these two newer authorities completely:

1. `audit/evidence/codex-goal-prompt-2026-07-26.md` — the detailed objective to pass to `/goal`;
2. `audit/evidence/completion-handoff-2026-07-26-ksg-rev4.md` — exact scientific state, hashes,
   failures, contamination boundaries, agent stop reports, and milestone exit criteria.

They supersede the older revision-2/91-mutation stop description below. The active KSG arithmetic
core is mathematically GO on its declared bounded domain, but repository/publication promotion is
NO-GO. Frozen revision 3 failed pre-closure audit; revision 4 is required. The multi-wave ambient
worktree must not be committed wholesale. The dedicated formal checkers are temporarily
incoherent with newly revision-scoped v4 Lean/Z3 paths, generated catalog/release views and software
identity are stale, no settled full mutation replay is creditable, and no isolated KSG candidate
has been synthesized. Resume from the handoff, not from an earlier green line.

Updated: **2026-07-26**. Active branch: `main`. Parent durable commit when this manifest was written:
`626ded7b24c62e24ee6cdda21b04bec63675272b` (`audit: bound durable compaction recovery`), pushed
to `origin/main`.

This mutable file is the first document to read after context compaction. It is process state, not
scientific evidence. The append-only historical record remains
`completion-run-ledger-2026-07-25.md`; claim packets, formal artifacts, certificates, compiled
tests, and release gates remain the authorities for their own evidence classes. Never use this
manifest to promote a theorem, estimator, implementation, or consumer disposition.

Authority order for the active work is:

1. current system/user instructions and `AGENTS.md`;
2. `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md` and the active frozen claim revision;
3. replayable source, exact counterexamples, formal/certificate artifacts, tests, and checkers;
4. this coordination manifest and the historical ledger; and
5. audit reports and Fable/Opus outputs as recommendation or attack input only.

## Bounded bootstrap after compaction

Do not reload the whole project history by default.

1. Read this file completely. Query `get_goal`; run `git status --short --branch`; list native
   agents. Confirm the last commit and exact stop point below.
2. Authenticate the governing files. Current expected SHA-256 values are:

   ```text
   d7b161e749d21e6df64d54e2ce969f4115586c8f78b04d09bc174ac19e8c9830  AGENTS.md
   717015b862995b1003d66badceccfc4535f5bb231681212a9b2ceff3b8204f94  MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md
   7c4aec062863c88f496176188eaace3baaae06201e2c85aa2c1ed200ac1d1330  final Wibral audit Markdown
   ```

   If `AGENTS.md` or the workflow digest differs, read the changed file completely and update this
   manifest before acting. If unchanged and their contents are already present in the resumed
   prompt, apply them directly; otherwise read `AGENTS.md` and the workflow's protocol portion
   beginning at `## AI model operating protocol`. The source-observation history is not a routine
   compaction dependency.
3. Read the complete **active revision**, obligation graph, routes, evidence matrix, decision, and
   every retained failure named in the active-workstream section below. Verify frozen historical
   hashes without rereading historical prose unless custody fails or a semantic diff is disputed.
4. Read only source/checker/catalog/release regions named below. A truncated read is rejected; use
   bounded calls. Do not run broad repository searches when an exact path or symbol is known.
5. Reconstruct the current decision through at least five applicable lenses. For PID work the
   default set is semantic/estimand, exact mathematical, formal/certificate, binary64/numerical,
   compiled executable, statistical, provenance/release, and downstream-authority. Record shared
   proof cuts; model-name agreement is not independence.
6. Continue `review -> plan -> edit -> implement -> test -> verify`. Preserve counterexamples,
   failed routes, open obligations, negative atoms, frozen revisions, and first-result records.
7. Before a coherent milestone commit, update this file's stop/test/queue fields and append a
   short delta checkpoint to the historical ledger. Commit unsigned, without agent attribution,
   and push `main`. Record the resulting commit in the next advancing milestone; a file cannot
   truthfully contain the hash of the commit whose bytes include that file. Do not append
   repetitive full-replay narratives.

Expansion rules prevent stale context:

- load another claim packet only when its workstream becomes active or a shared dependency must be
  audited;
- load an old audit/report only to resolve a named provenance or recommendation question;
- load an external model transcript only to adjudicate a specific retained attack;
- if bytes, counts, or results conflict, stop promotion, retain both records, and reopen the
  smallest disputed obligation; and
- when switching workstreams, replace the active-workstream section and move the old state into
  one ledger delta rather than accumulating multiple active narratives here.

## Scientific invariants carried across every compaction

- The primary scientific object is Makkeh--Gutknecht--Wibral shared-exclusions PID. `I_min`, KSG,
  categorical SxPID, continuous shared exclusions, fitted quantization, and incomplete/full PID3
  are distinct objects until an explicit mapping theorem closes the transfer.
- Freeze domains, ranges, quantifier order, assumptions, units, non-solutions, falsifiers, evidence
  classes, and completion checks before changing a scientific result.
- Separate exact-real mathematics, formal semantics, certified numerics, Rust conformance,
  statistical calibration, consumer qualification, release identity, and external custody.
- Major claims require dependency-aware independent routes, a counterexample route, mutation
  assurance, and an adversarial audit. A formal proof of a surrogate or a test of bounded cases
  cannot close a stronger statement.
- Continuous support is declared, not inferred. Added noise changes the estimand. Negative SxPID
  atoms are valid. Information units are nats. PID atom construction must not clamp MI terms.
- Preserve negative/open results. Exact-versus-Neumaier PID2 guard equivalence remains open; a
  failed search is not evidence.
- Scientific PDFs are release artifacts and must contain definitions, assumptions, domains,
  ranges, full derivations, obligations, counterexamples, negative/open results, implementation
  correspondence, independent-method cuts, hashes/receipts, limitations, and replay commands.
  Render and visually inspect every page and check semantic parity before release.

## Publication-grade PID discovery and assurance protocol

The scientific process itself is a required publication artifact, not merely internal agent
instructions. It will be authored as a canonical Markdown methods paper with a semantically paired
LaTeX/PDF rendering. The paper must be reproducible, falsifiable, and useful to an expert team
without access to this conversation. It must include:

1. a precise problem class for mathematical/statistical PID claims and an explicit firewall among
   MGW shared exclusions, other PID functionals, estimators, implementations, and consumers;
2. frozen-claim construction, quantifier/domain/range/assumption tables, non-solutions,
   falsifiers, and version-preserving correction rules;
3. AND/OR obligation hypergraphs, minimal critical-cut-set accounting, dependency-aware evidence
   independence, and a formal rule for when multiple agents count as one route;
4. agent roles, task decomposition, dispatch/decision gates, information-flow controls,
   source-blind and proof-blind attacks, conflict escalation, liveness/termination criteria, and
   durable handoff/recovery semantics;
5. the complete discovery loop from conjecture generation through exact reduction, certificate
   construction, formalization, compiled refinement, statistical calibration, and release;
6. adversarial review across semantic, combinatorial, analytic, probabilistic, formal, numerical,
   compiled-executable, statistical, provenance, resource, portability, and downstream-authority
   lenses;
7. negative-result and failed-route retention, smallest-witness minimization, mutation design,
   correction-ledger dependency reach, and reopen conditions;
8. evidence aggregation without pseudo-independence, including shared oracles, shared imported
   theorems, shared generators, shared source text, and correlated model families;
9. worked pid-rs case studies covering a successful bounded bridge, a false transfer between PID
   definitions, a binary64 threshold counterexample, a mixed-rank estimand obstruction, an open
   failed discriminator search, and a proposed frontier claim that remains NO-GO;
10. measurable process outcomes and limitations: defect discovery, mutation sensitivity, replay
    coverage, wall/compute cost, unresolved obligations, specialist-review boundary, and threats
    to validity; and
11. executable schemas/checklists, artifact and digest conventions, exact replay commands, and a
    page-by-page PDF semantic/visual verification record.

This paper may describe a project-defined research protocol and report scoped case-study evidence.
It must not claim that orchestration guarantees truth, that model agreement is mathematical
evidence, that the process is scientifically novel without a literature review, or that a bounded
pid-rs result validates an unbounded theorem. Before release it requires independent hostile
methodological review, citation/source checks, exact correspondence to the live workflow and claim
packets, negative mutations of its machine-readable schema, extracted-text parity, and rendered
page inspection under the PDF workflow.

## Active workstream: KSG integer-harmonic integration

Active claim: `KSG-INTEGER-HARMONIC-001`, revision 2 retained as the frozen pre-implementation
claim/evidence decision. The active decision is whether the completed implementation and expanded
mutation evidence require a new revision 3 and how to land a KSG-only release milestone before
PID2. This is a narrow integer-argument arithmetic and bounded binary64 result used by KSG and the
continuous shared-exclusions estimators. It is not a theorem about estimator consistency,
population support, MGW PID atoms, or downstream statistical validity.

Read now:

- `claims/KSG-INTEGER-HARMONIC-001/{revision-index.md,claim-v2.md,correction-ledger-v2.md,
  obligations-v2.md,routes-v2.md,evidence-matrix-v2.md,decision-v2.md,behavioral-witnesses-v2.md,
  formal-assurance-v2.md,implementation-v1.md,call-site-map.md}`;
- every file under `claims/KSG-INTEGER-HARMONIC-001/failures/` plus the route memo and its v2
  erratum;
- `scripts/check-ksg-harmonic-revision.py` and
  `scripts/check-ksg-harmonic-revision-self-test.py` completely before changing their contract;
- the Lean/Z3 KSG checker and mutation scripts, their exact source artifacts, and only the
  `stats.rs`, `ksg.rs`, `isx.rs`, `pid3.rs`, fixture, generator, and test regions they bind; and
- the 20 catalog entries, 15 release families, review-evidence records, CI/just wiring, and
  software-identity reference only when constructing the isolated KSG milestone.

Verify, but do not edit, these current revision-2 hashes:

```text
2a114fca75c52d65410bc2b80bd561c7a1858035d5643a2d660044a53823f7f3  claim-v2.md
2c108aef29e833a6bf9f41968f917ad05b645606b377fc55ff3b0f9bccc1d389  obligations-v2.md
5cfe75c9572ee7742a2428dcd119018a6ae1bd92c7cfb1ed0bce5257f7691ab5  routes-v2.md
6b750c010a00debde29ec2b3959e1bd55751f7ebe9c136beac202503b1b6196c  evidence-matrix-v2.md
540d7f468bbcbc8771adeae8ce3ee103dad5d98d7bc5298a8c1e91a67a19fd26  decision-v2.md
0c65acef2b96bcac208be78a1d781bccb6c079b249076544d2227b3634e5b61b  correction-ledger-v2.md
e8e3d936d94bc25ed1eaa49e22d3cbdee0e65a649192f613e76dce8c22a99151  behavioral-witnesses-v2.md
1068d90dcfe7a20b5237305c0468a6a74eedeb5b91196ff6bfe9969dec300c10  formal-assurance-v2.md
```

Settled facts and live discrepancies to preserve:

- For positive integer `m`, `psi(m)=H_(m-1)-gamma`; hence for `n>=2`, `1<=k<n`, and valid
  integer arguments `x,y`, the four-term score is
  `H_(k-1)+H_(n-1)-H_(x-1)-H_(y-1)` with coefficients `(+1,+1,-1,-1)` in nats.
- Exclusive KSG counts require `k-1<=nx,ny<n` and use `x=nx+1`, `y=ny+1`. Inclusive Ehrlich
  shared-exclusions counts require `k<=x,y<=n` and pass the arguments without a successor. These
  domains and mappings are not interchangeable.
- The selected Neumaier-prefix plus symmetric-range binary64 implementation has, on the frozen
  8,198-cell Decimal corpus, maximum absolute error `8*EPSILON` nats, 40 maximum-error ties, and
  zero source-swap asymmetries. The allowed `32*EPSILON` absolute gate is bounded evidence, not an
  ULP bound, a correct-rounding theorem, or a universal error theorem.
- The exact `Fraction` route covers 6,920 feasible tuples through `n=16`. Lean proves 14 narrow
  exact algebra theorems conditional on the typed integer-digamma premise. Z3 checks three
  premise-explicit QF_UFLIRA obligations with uninterpreted harmonic values. Lean and Z3 share the
  analytic premise and the human sign/index mapping; neither proves binary64 or estimator validity.
- The v1 route memo incorrectly labelled 16/764 maximum-error cells as compensated. The retained
  erratum records the actual comparison: plain 8/0/39, Neumaier 8/0/39, selected symmetric range
  8/0/40. The extra selected tie is first `(4096,1,2048,2048)`.
- Live source/checker work now closes six gates that revision 2 records open: maximum-tie custody,
  generator drift and reseal custody, and three source dataflow shadows. The self-test therefore
  rejects 91 mutations (`4+2+19+66`), while revision-2 public text still says 85. Do not rewrite
  revision 2 after observing this result; issue a new revision or explicitly retain the six gates
  open.
- Four release families eventually combine KSG and PID2 revision strings. A PID2-first commit is
  false because parent `626ded7` lacks the KSG implementation. The KSG milestone must use the
  intermediate KSG-only revision for those four families; the later PID2 milestone advances them
  to the combined revision.

Exact stop point: PID2 source/checker hardening passes on the combined dirty tree with 129
registered mutations, two bidirectional scope-isolation preflights, 18 distinct compiled tests in
debug and release (36 invocations), focused Rust tests, Rustdoc, catalog, release, review-evidence,
and identity gates. It is deliberately held uncommitted until a coherent KSG parent exists. Two
external hostile reviews independently confirmed the PID2 arithmetic but found that two inventory
mutations read live artifacts while public prose says copied artifacts; that wording defect must
be corrected before PID2 release. One review additionally requested revision-1 custody, per-scope
copied-root baselines, and two pin mutations; another requested a compiled-test name mutation and
toolchain receipt. These are open hardening decisions, not silently accepted conclusions.

The active next action is to finish hostile KSG mathematical and release-slice audits, decide and
author a non-destructive revision 3 if required, harden the 91-mutation suite against false-green
diagnostics, construct KSG-only intermediate release identities, and validate the exact staged
snapshot before a small unsigned push. The full-tree clippy run is currently red only in an
unrelated uncommitted Imin boundary test (`needless_range_loop`); no KSG/PID2 scientific conclusion
is inferred from that failure.

## Long-horizon milestone queue

This table is the durable to-do authority after compaction. Advance a row only with the named exit
evidence; never infer completion from effort, elapsed time, model agreement, or an unrelated green
test. Update the exact stop point above whenever work is interrupted.

| ID | Milestone | State | Next advancing action | Exit evidence |
|---|---|---|---|---|
| M0 | relevance-bounded recovery and durable planning | complete at pushed `626ded7` | keep this manifest and append-only ledger current before every milestone | subsequent resumes authenticate the manifest and bounded routing |
| M1 | KSG harmonic assurance integration | active | reconcile frozen v2 with live 91-mutation evidence; create a retained v3 if required; land KSG-only intermediate release identities | exact/Decimal/Lean/Z3/source/compiled/mutations/CI/catalog/release/identity gates replay on an isolated staged snapshot; qualified wording; small unsigned push |
| M2 | PID2 checker/source/catalog/release closure | verified on combined tree; pending KSG parent and final hardening adjudication | replay against pushed KSG parent; correct live-vs-copied evidence prose; adjudicate domain/endpoint/custody/toolchain findings; create a new revision rather than edit frozen bytes if the claim changes | truthful mutation inventory; exact scopes normal/`-O`; compiled debug/release; catalog/release/review/identity and focused Rust/rustdoc; small unsigned push |
| M3 | categorical SxPID3 Programs A--E | pending on M2 | activate proposed SxPID3 packet; freeze producer and independent-verifier interfaces before code | all 108 coordinates bound through event/count/Mobius/certificate/compiled/archive routes; bounded corpus and mutations replay; open gates stated |
| M4 | publishable PID discovery/orchestration methods paper | pending; specification pinned above | literature/source map, frozen paper outline, process schema, and independent hostile-method review | canonical Markdown/LaTeX parity; citations checked; case evidence reproducible; schema mutations killed; no novelty/evidence overclaim |
| M5 | comprehensive scientific PDFs | pending on settled source artifacts | generate each PDF from canonical sources, extract text, render every page, inspect, and bind hashes | complete-detail semantic parity plus zero visual defects and reproducible render receipts |
| M6 | final release/identity/cross-repository closure | pending on M1--M5 | run full CI/release/identity/archive matrix; then inspect each sibling repo independently | all pid-rs gates green on settled bytes; scoped dispositions; small main commits pushed; only clean/authorized sibling changes pushed |

The active lifecycle goal tool remains paused and cannot change its objective text without replacing
the unfinished goal. This queue records the user's later Wibral, formal-assurance, publication,
PDF, compaction, and small-milestone requirements without falsely completing or replacing it.

## Deferred routing table — do not load until activated

| Workstream | Entry point when activated | Current boundary |
|---|---|---|
| PID2 represented-sum hardening | `claims/PID2-REPRESENTED-SUM-001/` | binary64 checked-constructor contract; combined-tree replay green; KSG parent, evidence wording, domain/endpoint revision, and release isolation open |
| Imin tie/swap | `claims/IMIN-TIE-SWAP-001/` | Williams--Beer object; never MGW evidence |
| two-source count/event bridge | `claims/SX-COUNT-EVENT-BRIDGE-001/` | bounded supplied-count categorical MGW bridge |
| certified SxPID2 | `claims/SX-CERTIFIED-AVERAGED-PID2-001/` | conditional bounded containment/product-sign assurance |
| categorical SxPID3 | `claims/SX-CERTIFIED-AVERAGED-PID3-001/` | proposed 108-coordinate target; Programs A--E open |
| continuous mixed-rank repair | final Wibral audit lines 242--339 and 375--382 | common-radius bridge refuted on smooth torus; replacement theorem open |
| publishable discovery protocol | `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md` plus this manifest's publication obligation | canonical methods paper, schema, adversarial review, and verified PDF open |
| comprehensive PDFs/release | LaTeX sources, output PDFs, release/identity gates | full-detail semantic and visual audit open |
| sibling repositories | `ECOSYSTEM_CAPABILITIES.md` plus each clean repo status | no cross-repo push until pid-rs authority and repo cleanliness permit it |

The older `first_pid_rs_audit_gpt5-6pro`, superseded Wibral report bodies, old compaction
checkpoints, inactive claim packets, and complete Fable/Opus transcripts are intentionally absent
from the default recovery set. Their paths remain in the historical ledger and claim packets.
