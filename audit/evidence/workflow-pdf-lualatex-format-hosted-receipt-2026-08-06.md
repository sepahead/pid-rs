# C3 LuaLaTeX format-custody hosted receipt

- **Receipt date:** 6 August 2026
- **Exact subject:** `dfb77a0b200c772b7c00cb615fda70d31ee18334`
- **Disposition:** **closed for the bounded exact-subject LuaLaTeX format-custody subgate**
- **Wider PID program:** open
- **Machine companion:**
  `audit/evidence/workflow-pdf-lualatex-format-hosted-receipt-2026-08-06.json`, SHA-256
  `c2ef8214dc01ca081113b8e92f252760f3ada6cc9296b39e9a7ffb44ee7ddd44`

The machine companion is the typed authority for the values summarized here. It deliberately
does not hash itself or this Markdown, and both artifacts leave their future receipt commit, tree,
and blob identities null. The required direct parent is the exact subject above. This keeps the
receipt acyclic: subject-run evidence can establish facts about `dfb77a0…`, but cannot authenticate
receipt bytes that did not yet exist in that subject.

## Executive result

The bounded conjunction is now true:

1. the exact unsigned subject, tree, parent, eight-path delta, and retained prehost evidence agree;
2. the subject was published to `main` by a literal non-force fast-forward;
3. exact-subject CI run `31084336902`, attempt 1, completed **45/45 jobs and 537/537 API-recorded
   steps successfully**;
4. its formal workflow-PDF job completed 313/313 frozen controls on Ubuntu while privately replaying
   the exact selected `lualatex.fmt` bytes;
5. separate exact-subject CodeQL run `31084335829` completed 4/4 jobs successfully, with its warnings
   and 90 open alerts retained rather than relabelled as clean;
6. repeated run, job, log, coverage, and SBOM captures were reconciled through frozen exact-source
   auditors and typed hostile controls; and
7. the complete 191-node external capture was sealed without write bits, built twice into the same
   canonical USTAR bytes, audited in four modes, manually extracted into a fresh directory, and
   replayed from that extracted copy without changing its manifest.

This closes only the engineering-portability subgate stated above. It gives **no scientific result**
to KSG, Ehrlich continuous shared-exclusions PID, categorical Makkeh--Gutknecht--Wibral SxPID,
Williams--Beer `I_min`, fitted quantized PID, heuristics, or project wrappers. It does not close the
post-Lean-14576 replay, KSG M1c, PID2 revision 4, MGW SxPID3 Programs A--E, the 108-coordinate
program, release readiness, or any downstream authorization.

## Exact subject and source boundary

| Object | Exact identity |
|---|---|
| commit | `dfb77a0b200c772b7c00cb615fda70d31ee18334` |
| tree | `60b01bcd466f832315b482960d9453dce08a12bc` |
| direct parent | `e53dc427d082dd936024782f62c795db743fc893` |
| C3 ancestry root | `8b792bc143fff2d84f2d8e7817d1de7850741223` |
| subject | `fix(ci): capture exact LuaLaTeX format` |
| signature observation | Git `%G? = N`; GitHub `verified=false`, reason `unsigned` |

The signature fields are observations, not authorship or authenticity proofs. Two byte-identical
GitHub API captures agreed with the local commit/tree/parent tuple. The subject tree contains the
exact prehost JSON and Markdown blobs, including `C3-FMT-N001` through `C3-FMT-N014`. Hosted jobs
checked out the exact head, but this receipt does not claim a content rehash of every checkout path
in every job.

The 53,145-byte CI workflow is Git blob
`4148eba6e443ee2a76166f73ad38c48a46cf21dd`, SHA-256
`fd93c27452fa6b09a9e93b143193a6caeb35e3256e7bfdd839e7b8664e4cd5d0`. Its seven unique
third-party action references are full 40-hex pins. That binds repository workflow bytes, not the
GitHub service, runners, operating systems, mirrors, toolchains, dynamic loaders, or hardware.

The subject retains the current 51-page Darwin-built workflow PDF as Git blob
`ad453cf8c6bbe00800586c57a7d5558842b50f14`, 626,770 bytes, SHA-256
`f372256011d1173a020d39b86cba5ab7959fb07cea09cf1a2b7eeb292a83cafe`, plus its 11,249-byte
rendering receipt at SHA-256
`847685d91b6a565ba37c077515396e3bb83fb1ed18d295a14b4eb3ebe9bedcaf`. Presence and byte
identity do not prove the document's mathematics, citations, visual correctness, or publication
acceptance.

## Alternate-index and publication custody

The private alternate index was written to tree `60b01bcd…`, changed to mode 0400, and not reopened
through Git before subject commit construction and push. It is 71,520 bytes, SHA-256
`3e0b5471d79df241665918638927f6e641da59cea12b217133da95ad35d167c4`, with one observed
link. Semantic review used copies; independent prompts re-derived the same tree and eight paths,
while the original digest remained unchanged through commit construction and push. During this
receipt review, however, a reviewer incorrectly ran `git write-tree` against the original. Git
returned the same tree and preserved its content digest, size, and link count, but changed mode 0400
to 0644 and advanced filesystem metadata. Mode was restored to 0400; continuous post-review raw-
metadata custody is false and the incident is `C3-FMT-N048`. The bounded pre-commit/pre-push custody
and already published Git object remain true. This is not a canonical Git-tree property, tamper-
proof seal, remote archive, or institutional review.

The first push attempt remains `C3-FMT-N015` with zero credit. Zsh interpreted `:r` in an unbraced
variable expression, so Git received an invalid source refspec and rejected it locally; remote
`main` stayed at e53. A later non-login Bash command used the literal refspec
`dfb77a0b200c772b7c00cb615fda70d31ee18334:refs/heads/main` and fast-forwarded e53 to dfb.
The successful retry does not reclassify the failed attempt.

## Terminal exact-subject CI

[CI run `31084336902`](https://github.com/sepahead/pid-rs/actions/runs/31084336902), attempt 1,
run number 174, was triggered by a push to `main` at `2026-08-06T08:18:09Z` and completed success at
`2026-08-06T09:53:14Z`.

| Capture | Repetitions | Bytes | SHA-256 |
|---|---:|---:|---|
| run API JSON | 4 | 12,096 | `391bc0210021386455e5547da64ce41bc505892e01efe1aa4c52307393fb664a` |
| jobs API JSON | 4 | 144,755 | `08305e087ac707be95e2edf4253edd4d88b76f21f7035fe7751fb9af546fa12e` |
| attempt log ZIP | 2 | 851,761 | `9bb9e0889cb01d4d5266d313d0703f258ec506426f4cf95b5e434d6ded1f90ed` |

The job API contains 45 unique typed IDs and names, one head SHA, 45 initial checkout steps, and 45
post-checkout steps. All 45 jobs and all 537 API steps concluded success. The 105-member log archive
contains 45 top-level combined logs, 45 system logs, and 15 duplicate KSG per-step views. The exact
current-roster mapper bijects both top-level and system names to the API roster. This is a bounded
mapping for these bytes; GitHub does not provide a cryptographic job-object-to-log-member binding,
and the result is not a general filename theorem.

The canonical 45-log view contains 755 Rust test-summary text occurrences. Two are literal grep
commands, leaving 753 parsed result records whose repeated-record sums are 8,357 passed, zero failed,
85 ignored, zero measured, and 2,043 filtered. These are textual record aggregates, not unique test
identities or executions; ignored tests were not executed. Eight Python matrix summaries aggregate
188 passed and 300 skipped across four Ubuntu, two macOS, and two Windows job labels. Quiet logs do
not retain individual skip reasons.

The run is not “warning free.” It contains 78 Node DEP0040 punycode deprecation lines across 39
top-level logs, 41 Git default-branch advisory blocks, one cargo-publish dry-run warning, and two
exact-key cache reservation failures. Forty-three composite-action conditional skips are internal
log events rather than API steps. The bounded scan found zero GitHub error/warning/notice/debug
annotations and zero exact `panicked` or `fatal` word markers, but makes no claim that all failure
vocabulary is absent.

The default `exp0` diagnostic reported 12 cases, three geometry warnings, geometry `PIVOT`, and
MI/coherence `NO-GO`, with three monotonicity/CMI and one normalized-invariant violation. Shared-
exclusions measure validation remained `not_adjudicated`, and atom-estimator validation remained
`blocked`. Those are expected, non-gating diagnostic outcomes under the documented `exp0` contract;
they are neither regressions nor transferable estimator-validation evidence.

## Formal workflow-PDF gate

Formal job `92560152057` completed 14/14 API steps successfully. Its two direct 113,085-byte logs
are identical at SHA-256
`11c39cab4d44913154e68180b3eb04c4a94f6ec376568a4025219cef48d76122` and reconcile to the
whole-run member. The frozen self-test passed exactly
`194 + 37 + 17 + 7 + 8 + 3 + 47 = 313` controls.

On Ubuntu image version `20260720.247.2`, with `texlive-luatex` package
`2023.20240207-1`, the checker selected and privately replayed
`/var/lib/texmf/web2c/luahbtex/lualatex.fmt`: 12,242,215 bytes, SHA-256
`bf4be0e903eec66820a8a71c31ae253d4d052abfc4a23cb4330d1776af6861e7`. It rebuilt the
51-page workflow PDF at SHA-256
`5a17eccfd113f87767a8aa3a40ecbd848cca34f1b125e9d424a10f928d76d726`, with rendering,
executable, and pypdf receipt hashes retained in the machine companion. The hosted output bytes were
not uploaded. Their difference from the retained Darwin PDF is expected and is not cross-platform
byte identity.

`C3-FMT-N016` retains two cache-save reservation failures and one sibling successful save for the
same exact subject key. The jobs stayed successful because their substantive gates had already
passed. Cache content equality, persistence, and future reuse remain unproved.

## Coverage and SBOM artifacts

The saved-artifact metadata pair is byte-identical at 1,361 bytes, SHA-256
`fe92f63724f004c05bfc387d1205b71d860fef299aebe963506c466069e7064e`, and names exactly
`coverage-lcov` and `workspace-sbom`. The supplied archive sizes and digests agree with it. This
does not authenticate GitHub or prove freshness beyond the captures.

The repeated coverage archives are 259,177 bytes at SHA-256
`93eea1067a11a076ed38ab0baaeeb06718de194e7accf30f81456bddd6e7fd7e`. Their 2,247,997-byte
`lcov.info` has SHA-256
`291985479443fae48ffb59fde8ef231bbf77f3b100864a64f157c773951d48e4`. The producer declares
39,474 lines found and 33,927 hit, plus 3,192 functions found and 2,787 hit. The accepted parser
also reports selected detail counts and their differences, but explicitly does **not** rederive the
producer summaries, validate the full LCOV grammar, or establish coverage adequacy.

The repeated SBOM archives are 22,405 bytes at SHA-256
`6dcaa4646498d84198ef256badf64069d4b246d4484efec84430f440e27a687a`. Their bounded internal
projections contain roots `pid-core`, `pid-python`, and `pid-runlog`, all version 0.9.0, with
48/61/22 non-root components and 76/109/28 dependency edges respectively. This is not CycloneDX
schema validation, SBOM completeness, freshness, or source correspondence.

## KSG M1c and Lean soundness firewalls

KSG phase job `92560151969` completed 15/15 steps successfully, and its direct job/log bytes
reconcile to the whole run. Its own retained revision-4 receipt still says `integration_no_go`,
70 mapped files, 35 historical hashes, and
`preclosure_core_manifest_must_be_regenerated_at_m1c`. Therefore KSG M1c remains open. The hosted
job's success cannot reverse that typed scientific/integration disposition.

Three hosted logs observe Lean 4.32.0 commit
`8c9756b28d64dab099da31a4c09229a9e6a2ef35`. The captured logs record those execution
observations; they receive zero post-fix kernel-soundness credit. The [official Lean kernel-bug postmortem](https://leodemoura.github.io/blog/2026-8-1-postmortem-for-kernel-soundness-bug-14576/)
describes the soundness defects and the need for patched releases. The selected fixed replay target
is the official [Lean 4.32.2 release](https://github.com/leanprover/lean4/releases/tag/v4.32.2),
commit `f3b06c705e6c85f5314019d5d3baab0fec5b580c`.

The 4.32.0 observation is **not itself a witness that any repository theorem is false**, and it does
not imply that “all the math was wrong.” The next separate milestone must replay every exact Lean
source on 4.32.2 with the repository-required minimal trust setting and a fresh independent-kernel
route. `--trust=0` minimizes the trust level admitted by the Lean gate; it is neither an independent
kernel nor a cure for a faulty kernel. That is why both fixed official Lean and a separate checker
are required. No fixed-Lean result is spliced into this dfb receipt.

## Honest security receipt

[CodeQL run `31084335829`](https://github.com/sepahead/pid-rs/actions/runs/31084335829) is a separate
GitHub-managed dynamic workflow, not part of the 45-job CI run. It completed 4/4 jobs successfully.
Its repeated 295,792-byte, 48-member log archives are identical at SHA-256
`16b6a57b4e23b221d3dc5a5259951333ae2d5a86463e4f99ebe3753e895fda7a`.

The exact-head snapshot contains 90 open alerts: 21 critical and 69 high. It also contains 46 closed
high-severity Rust path-injection alerts, 43 dismissed as used in tests and three as false positive;
this receipt records, but does not independently re-adjudicate, those dispositions. No current alert
location intersects the subject's eight changed paths, and none was created during the run window.
Those observations do not prove non-causation or absence elsewhere.

The Rust combined extractor log contains 2,219 warning records: 2,212 macro-expansion failures and
seven suppression-summary records across 74 paths. The seven displayed integers sum to 1,072; that
sum is not the warning count. Rust extraction completeness and security acceptance are false. No
SARIF artifact was retained.

The full-history secret-scan job completed 7/7 API steps and logged 145 commits, approximately
26,897,426 scanned bytes, and “no leaks found.” Its exact tool archive, executed binary digest, and
version output were not retained, so the execution is credited while a repository-wide secret-
absence claim is not. With 90 open CodeQL alerts and incomplete Rust extraction, the only honest
disposition is `security_clean_claim=false`.

## Canonical external capture and replay

The sealed capture manifest is 32,169 bytes, SHA-256
`5ebdc4b7651aa7b0d890906103e9f2ee16759af039db6d2a1d36125a01a6d1bd`. It records 23
directories, 168 regular files, and 11,156,416 regular-file bytes. Five observations—post-seal A,
independent scan B, post-build scan C, fresh extraction, and post-replay extraction—are byte-
identical. The modes comprise five directories at 0500, 18 at 0555, 26 files at 0400, and 142 at
0444: no write bits, but no tamper-proofness.

The manifest covers portable relative path, node type, POSIX permission bits, regular-file size,
and regular-file SHA-256. It excludes ownership, timestamps, ACLs, extended attributes, BSD flags,
resource forks, and Finder metadata. The observation is sequential and repeatedly stable, not an
atomic filesystem snapshot.

Two separately built canonical USTAR archives are byte-identical:

```text
11,298,304 bytes
6565282572287d25781591afcc3e856e8d5d3cc7fa2db0d9e97090eebb7d0ea5  SHA-256
```

Normal and optimized audits of each archive produced the same 621-byte result at SHA-256
`95fa5f247e840c55d41631c9386c077470ab3dc44e9db59316ed76c062ef403b`. A manual dirfd/no-follow
extraction into a fresh empty destination matched the manifest exactly and did not use system
`tar` or `extractall`.

The 14,752-byte read-only replay entry, SHA-256
`529e3d314a3007b85f44cb40584a512e09129e6a32161c0deb6be05a85ec7e21`, invoked exact Python
3.14.6 bytes under `-I -S -B`, an empty ambient environment, fixed locale/time/hash settings, and
direct compilation of digest-checked source snapshots. Original normal/optimized and extracted
normal/optimized executions all produced the same 5,083-byte seven-entry result at SHA-256
`15a9b569dff342947edddd8a30a95ba4015b49d9d1ad40df13a319eedb4e5a94`; all four standalone
summaries are now mode 0400. The frozen suites are:

| Suite | Controls | Accepted source tuple |
|---|---:|---|
| narrow ZIP | 77 | `85b017e6…` / `5b2e61f0…` |
| coverage/SBOM artifact | 27 | `6a9bfb9c…` / `e09e78b6…` |
| terminal CI reconciliation | 50 | `d1f46e71…` / `ffea3f60…` |
| canonical USTAR | 44 | `73ffd9a4…` / `64a21260…` |

These controls are task-diverse but finite and correlated; they are not 198 independent scientific
replications, and mutation adequacy is not exhaustive. The archive is local `/private/tmp` custody,
not remotely durable, authenticated, externally attested, a transparency log, a general ZIP/tar
security theorem, or a defense against malicious same-UID or privileged mutation.

## Negative ledger

The sealed capture retains 14 prehost negatives plus 28 hosted/capture negatives,
`C3-FMT-N015` through `C3-FMT-N042`, in a 14,041-byte ledger at SHA-256
`e65537d5692b21adc87fab6271c5b760ccbc7f472614dead5991197db097a8a9`. Every rejected ZIP,
artifact, terminal, and USTAR tuple remains zero credit.

Eleven later receipt-process negatives are recorded here, outside the already sealed capture:

- `C3-FMT-N043`: a pre-seal `scan` correctly rejected writable root mode 0700 with
  `WRITE_BIT_PRESENT`; its 116-byte error result is not a manifest and receives zero custody credit.
- `C3-FMT-N044`: the first duplicate-key validation snippet referenced its hook before defining it
  and raised `NameError` before parsing; that run receives zero validation credit. The corrected
  isolated parser parsed the JSON, found no duplicate keys, and enumerated only the four intentional
  acyclic null fields.
- `C3-FMT-N045`: independent archive review found the four standalone replay summaries outside both
  sealed trees at mode 0644. The pre-fix packaging receives zero credit. Only those modes changed to
  0400; all four contents remained 5,083 bytes at `15a9b569…`, and no sealed-tree or archive byte
  changed.
- `C3-FMT-N046`: the first receipt draft guessed a nonexistent full Lean release SHA from GitHub's
  seven-hex display. That identity receives zero credit. Exact `git ls-remote` resolution of
  `refs/tags/v4.32.2` supplied the corrected 40-hex commit before publication.
- `C3-FMT-N047`: the first attempted Markdown update for N045/N046 used mismatched multi-line patch
  context; `apply_patch` rejected it atomically, so it receives zero documentation credit. A smaller
  exact-context patch then made the intended update.
- `C3-FMT-N048`: a scope reviewer ran `git write-tree` directly on the original sealed index after
  subject publication, violating the copy-only rule. The tree, size, SHA-256, and link count stayed
  exact, but Git changed mode 0400 to 0644 and advanced metadata. Mode is back to 0400; continuous
  post-review raw-index metadata custody remains false. Pre-publication custody is unaffected.
- `C3-FMT-N049`: the first direct-source Markdown-math checker invocation failed before inspection
  because its transient dataclass module was not registered in `sys.modules`. It receives no
  validation credit. The corrected exact-source loader registered the module and found zero receipt
  findings; separate untracked-file whitespace checks also passed.
- `C3-FMT-N050`: the first unqualified receipt timestamp still named draft start after later review
  findings had been added. It receives no final-time credit. The machine receipt now distinguishes
  `draft_started_at_utc` from the post-review `finalized_at_utc`.
- `C3-FMT-N051`: the first Lean prose said captured hosted logs proved execution, despite the
  receipt's service/runner-authenticity nonclaim. It receives no prose credit. The corrected sentence
  says only that the captured logs record those observations.
- `C3-FMT-N052`: the first ledger prose called unpublished receipt-process findings durable even
  though exact receipt self-custody is unestablished. It receives no durability credit. The
  corrected text says the findings are recorded here.
- `C3-FMT-N053`: the first resume hash-update patch included one mismatched multi-line context, so
  `apply_patch` rejected the complete edit. It receives no resume-update credit; no file changed in
  that attempt, and smaller exact contexts were used afterward.

Thus 53 identified negatives are in scope. This count does not assert that no unlisted failure
exists, and no failed or superseded route is reclassified as success.

## Typed gate derivation and non-implications

| Predicate | Value |
|---|---|
| exact subject lineage, tree, and delta | true |
| exact prehost evidence present | true |
| pre-commit/pre-push alternate-index and non-force publication custody | true |
| continuous post-review raw-index metadata custody | false |
| exact-subject terminal CI 45/45 and 537/537 | true |
| exact formal-PDF job 14/14 and 313/313 | true |
| separate exact-subject CodeQL 4/4 execution | true |
| external canonical archive, extraction, and replay | true |
| no cross-run splicing | true |
| no estimator-family transfer | true |
| exact-subject LuaLaTeX format-custody subgate | **closed** |
| post-14576 fixed-Lean replay | open |
| KSG M1c | open |
| security clean / secret absence | false / not claimed |
| wider scientific and release program | open |

This receipt does not establish TeX Live or format authenticity, format-generation provenance,
pre-wrapper sandboxing, syscall-complete FLS tracing, privileged replace-and-restore defense,
cross-platform PDF/format byte identity, general parser safety, coverage adequacy, SBOM completeness,
mathematical truth, citation or novelty correctness, estimator validity, statistical calibration,
application validity, publication acceptance, package/release readiness, or downstream authority.

Most importantly, it does not equate method families. Categorical MGW SxPID and Ehrlich continuous
PID are related shared-exclusions research lines with different domains, constructions, estimators,
and premises; neither supersedes the other in general. KSG supplies continuous mutual-information
estimation machinery, not a categorical SxPID theorem. `I_min`, fitted quantized PID, heuristics,
and wrappers keep their own estimands and provenance. No result moves between them without an
explicit mapping theorem whose premises are established for the application.

## Next exact sequence

1. Publish these receipt/resume/changelog bytes as one small unsigned direct child of `dfb77a0…`,
   then observe the descendant's hosted CI externally without pretending that it self-authenticates
   its own pre-existing receipt.
2. Replay every exact Lean source on official 4.32.2 with the repository's trust-zero route and a
   fresh independent-kernel check; retain the 4.32.0 evidence as stale assurance, not theorem
   invalidity.
3. Close repository-wide isolated Python verifier custody and KSG M1c with acyclic typed receipts.
4. Continue the premise-explicit semantic audit, PID2 revision 4, categorical MGW SxPID3 Programs
   A--E and all 108 coordinates, bounded frontier mathematics, publication artifacts, and the final
   release/downstream gates—without crossing estimator-family boundaries absent a mapping theorem.
