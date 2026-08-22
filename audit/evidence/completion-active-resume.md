# Current completion pointer — Lean 4.33.0 freeze

The active Lean project is frozen at `leanprover/lean4:v4.33.0`, source commit
`d8b18978322de05a8f3dba51ef03cf5461676c17`. Follow
[`LEAN_4_33_FREEZE_AND_REPLAY.md`](../formal/LEAN_4_33_FREEZE_AND_REPLAY.md), the machine-readable
[`toolchain-freeze-policy.json`](../formal/lean/toolchain-freeze-policy.json), and the versioned
[`4.33.0 current replay receipt`](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json).
The [first 11 August replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json)
and [first 12 August replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12.json)
and [finalized r2 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r2.json)
and [finalized r3 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r3.json)
and [finalized r4 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r4.json)
and [finalized r5 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json)
and [finalized r6 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r6.json)
and [finalized r7 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r7.json)
and [finalized r8 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-14-r8.json)
and [finalized r9 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-15-r9.json)
and [finalized r10 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-18-r10.json)
and [finalized r11 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-18-r11.json)
and [finalized r12 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-18-r12.json)
and [finalized r13 replay](lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r13.json)
are preserved as prior evidence, not current runner custody. Here `r14` is the fourteenth accepted
slot in the sequence beginning 12 August. Counting the separate 11 August historical receipt, it is
the fifteenth receipt in the accepted/historical lineage. Rejected same-slot artifacts are
additional zero-credit documents; no total count of every generated receipt is claimed. The suffix
does not denote a calendar date, schema, theorem, review, assurance tier, or independence revision.
The route receives current execution credit only when the exact receipt
exists and validates.

Published C8's repository CI and dedicated-v8 route both ended at the exact marker
`certified SxPID2 claim check failed: release-audit just dependency line exact digest changed`.
That is the first reached comparison, not a complete mismatch inventory.

The same relative `r14` path in candidate
`0a6ece9c525ad7aad061f55b3edea83554891b42`, tree
`1d5446f19d34b742feeb51429bf58a0706750757`, which was not observed accepted or published on `main`
as C9 in the bounded provider/history checks, is not the current receipt. Those 145,611 bytes have
SHA-256 `2a882358e158ebeae06dbdf8d1cd35637d698f59ce217c1e2fbecf1d8787dfb7` and are archive-only
outside `prior_replay_*`. The required inherited-`umask 077` composite run's last confirmed output
line was `ok 273 - refresh writer reports an injected second-replacement failure`; the next
observed stable diagnostic had prefix `refresh destination mode drifted: ` and path suffix
`/root/output/pdf/workflow.pdf`. No complete raw transcript or whole-run digest of that required run
was retained. A separate direct workflow-PDF self-test under `umask 022` passed 366/366 controls but
is documentary only, was not checker-replayed as a C9 qualification run, and receives zero
qualification credit. No L8 record is installed; no operator-invocation history is claimed. No L9
exists; GitHub exposed no workflow run for the candidate on 21 August and
still resolved `main` to exact C8. Mutable provider ref
`refs/heads/archive/composite-v9-rejected-workflow-pdf-umask-20260821` was observed at the candidate
commit but is only a mutable recovery locator, not authentication, durability, or accepted-on-main
C9 publication. The deterministic checker binds the recorded identifiers but does not query the
provider archive, main, or workflow-run endpoints or require the sibling commit object. The candidate
and receipt receive zero accepted-on-main C9 publication status or credit,
qualification, accepted-current-replay, scientific, hosted, or independence credit. Do not merge
or cherry-pick the rejected commit or reuse/copy its `r14` or evidence. Reapplying reviewed
non-evidentiary source/contract bytes onto a fresh C8 child is permitted; byte reuse transfers no
execution, replay, qualification, or acceptance credit.

A second precommit candidate is likewise rejected with zero credit. Unsigned archive commit
`113cbad2e58a9cfa40cf43b1c0ffc260b566aa92`, tree
`ae3204d72c012dddaa5b634d9f5c4c745d5823d2`, was observed on 22 August through mutable provider
recovery ref `refs/heads/archive/composite-v9-rejected-r14-fixed-point-20260822`; the ref then pointed
to the commit, `main` remained exact C8, and GitHub exposed zero workflow runs for it. Its final
145,356-byte same-slot `r14` has SHA-256
`9ae3b4915f3cf4fd062723c8b80d80e0319ddc9db250662c50584b3f764d373c` (provisional SHA-256
`41fafe5dfdfbaf23c206ae366913082ff255e6e5f92217f02cfc95b83a5fc048`); all 39 receipt records
carry `exit_code: 0`, but the artifact and candidate receive zero credit. The mandatory precommit
certified-SxPID2 baseline failed in normal and optimized modes with exact stderr SHA-256
`5994ccdfb8dcfe35fac7646050c15ef4f19eee8524233b1cd57f651d19d78611` over 255 bytes: expected
justfile digest `74fb7bfd4500d8b121666a738a412fbdb409e7acf673b156645d215453ab310f`, observed
`93399171cfbb743dba93c7be1ec85e446a33193e41ada3977d198b0e4ecc6437`. Its 124-mutation self-test was
operator-observed passing in both modes with identical 58-byte stdout SHA-256
`2f163d400569a0897533ef5f5bdae357bd97962d0888ac2bbf68cfa5fe753351`, but therefore did not
establish the baseline. Independent review also found that three documents conflated named
self-test output with `r14` command custody. The archived `r14` exact argv roster contains zero
records for the certified baseline, certified self-test, Lean-freeze self-test, or C9 self-test;
ten other named self-test command records are present. Canonical receipt bytes contain zero literal
`live-pre-replay-ready` occurrences, but stream payloads retain only byte-count/SHA-256 descriptors,
so that is not a raw-stdout absence claim. Separate normal/optimized Lean-freeze self-test outputs
were operator-observed identical at 268 bytes with SHA-256
`a77c6d4634ad134975d9a42520a4dc16cd696d51879614a1a4f711eab8ce9f93` and report 132 mutations,
including `live-pre-replay-ready`; this is outer observation, not `r14` invocation/stdout custody.
At a separate generator call site, the same validator implementation evaluates the equivalent
live-cut predicate once before the replay command sequence. Full static checks and custody snapshots
precede the sequence; full static checks and custody/executable comparisons follow it before
publication. These correlated, common-mode endpoint checks are not per-command or atomic custody,
and source custody is not invocation/stdout custody. The observed mutable ref was a recovery
locator, not authentication or durability. No L9 was issued for the candidate, and the bounded
provider/history check observed no accepted-on-main C9 publication; there is no permission to reuse
its `r14`. A fresh current `r14` must exclude both rejected same-slot artifacts from current and
`prior_replay_*` lineage. During fresh recovery review, the first `justfile` repin exposed a second
fail-fast baseline edge at `scripts/README.md`: expected
`daedd86d0307984df8885849528ddfdd2d096a7b9d2799e308358ad4af59b33a`, observed
`c7fd28e0180bc19ebb09644840266e47f5a93c9b5af7e9062c7f0bbd2012e857`; its exact 273-byte stderr
has SHA-256 `e94271b9e1c1b7e885fb78d1839b2d8dacebf79aa6a72e6233db5773ded93ade`. This was an
operator-observed recovery-worktree diagnostic, not archived-candidate qualification or `r14`
custody. The repair now binds all five mutable certified surfaces plus the exact CI job and just
recipe sub-blocks.

Retain the exact PDF/source/production
gate, correct only the six synthetic pre-existing refresh-destination fixture modes, and generate a
completely fresh one-shot `r14` after every corrected operational byte settles. The fresh C9
changed-path set contains 32 paths; the rejected candidate's changed-path set contained 31. The
sole path-set membership difference is the fresh C9 addition of
`scripts/check-mathematical-workflow-pdf-self-test.sh`; this is a set-membership statement, not a
claim that shared paths have identical bytes. It is not a sixth stale binding, production-writer,
PDF, theorem, or estimator change. Local-recipe and hosted-post-setup qualification select exact
GIL-enabled CPython 3.14.6. One hosted pre-setup checkout-normalizer call plus four normal/optimized
action-pin checker/self-test calls remain runner-Python surfaces outside that lane. Exact
source-slice equality observed on CPython 3.11.13, 3.12.11,
3.13.7, and 3.14.6 is documentary only and receives no qualification or portability credit; the
bounded preflights do not authenticate interpreter bytes, prove atomicity or TOCTOU absence, or
enumerate every transitive process. The AST/source-route checks and hostile mutations are finite
regression evidence for a fixed lexical roster, not proofs of semantic soundness, causal execution,
or non-bypass. Dynamic namespace mutation and arbitrary execution custody remain outside those
analyses. Exact whole-file, tree, replay, and human-review custody remain authoritative within their
stated bounds.

A newer Lean release alone is not a migration trigger.

The prior 4.32.2 route-correction resume is retained byte-for-byte at
[`completion-active-resume-lean-4.32.2-route-correction-2026-08-08.historical.md`](completion-active-resume-lean-4.32.2-route-correction-2026-08-08.historical.md),
SHA-256 `4d636774f58d48212ac5ae83ea68fff106c07bb407b2dbf449503d792490e2e0`.
It is historical execution/custody evidence, not a current instruction, active toolchain pin, or
authorization to rerun, migrate, publish, or transfer any of its scoped claims.
