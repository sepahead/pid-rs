# C3 LuaLaTeX format-custody correction

- **Evidence date:** 6 August 2026
- **Disposition:** **bounded local GO: direct 313-control, serial full-exact, current visual,
  enclosing-custody, and two separately prompted source reviews passed; alternate-index custody,
  commit, and fresh hosted CI/CodeQL remain pending**
- **Machine companion:**
  `audit/evidence/workflow-pdf-lualatex-format-custody-correction-2026-08-06.json`, SHA-256
  `d2f58e8e751f4636f3b29fafc277737c8f96362613b9654807075899fc4b49fc`
- **C3 ancestry root:** `8b792bc143fff2d84f2d8e7817d1de7850741223`
- **Correction parent:** `e53dc427d082dd936024782f62c795db743fc893`, tree
  `6f222b0f6eba9933faa659fc8d2a362ea40b0f6b`, unsigned

This is a precommit local evidence report, not a C3 closure receipt. It does not name its own
candidate tree or implementation commit, and it contains no future hosted run identifier. Those
facts do not exist yet and cannot be inserted into an artifact that is itself a candidate-tree
input without creating a digest cycle. A strict descendant must bind the eventual commit, tree,
this exact evidence pair, and terminal hosted evidence.

## Executive result

The historical map-free implementation at exact commit `e53dc427` is terminal red. CI run
`31071608249` completed all 45 jobs with 44 successes and one failure. Formal-PDF job
`92520513307` failed when build-a pass 1 loaded ambient Ubuntu input
`/var/lib/texmf/web2c/luahbtex/lualatex.fmt`. Its 109,239-byte raw job log has SHA-256
`233ed7c120190d245241e40ee8e056f82b71fbc7ab4dd7d675f94cd6acdd8730`.
The failure is retained as a real build-input portability counterexample. It is not a mathematical,
Lean, KSG, PID, or citation counterexample.

CodeQL run `31071608063` separately completed four of four jobs successfully. Across the two
workflows, the exact e53 roster is 49 jobs: 48 successes and one failure. This is not a single
49-job run, not an all-green result, and not a basis for transferring successful jobs into a later
correction. The KSG job eventually succeeded, but it neither repairs the failed CI run nor closes
KSG M1c.

The narrow correction captures the one Kpathsea-selected LuaLaTeX format into a private one-file
snapshot, makes only that snapshot searchable through `TEXFORMATS`, verifies it around every
compiler use, and requires exact raw and resolved recorder-format sets. The current direct
self-test passed all 313 controls on an unchanged exact source pair with partition
`194 + 37 + 17 + 7 + 8 + 3 + 47`. This is positive mutation-suite evidence only: the self-test's
own final line states that no report compilation was performed.

A subsequent serial full exact checker passed on an unchanged seven-object source tuple. It rebuilt
both isolated reports and replayed the exact PDF, dual-render, executable, pypdf, and private-format
receipts. The current 51-page color/grayscale review found no visual defect, two separately prompted
source reviewers returned bounded GO dispositions, and the certified-SxPID2 enclosing custody
passed normal and optimized checkers plus 111 mutations in each mode. These routes are correlated
local evidence on one Darwin host; they do not establish Ubuntu portability or any PID result.

C3 therefore remains open. Alternate-index staging, a direct-child commit/push, terminal all-green
hosted CI and CodeQL, and a strict-descendant receipt are still required.

## Acyclic evidence boundary

The custody graph is deliberately one-way:

1. the immutable historical 266-control JSON/Markdown pair is bound by exact e53 Git blobs and
   SHA-256 values;
2. this Markdown binds the finalized successor JSON digest;
3. the successor JSON does not hash itself or this Markdown;
4. neither file claims a candidate tree, implementation commit, or future run identifier; and
5. a later strict-descendant receipt must bind those post-report facts.

An implementation commit's own hosted run can execute bytes already in that commit, but it cannot
retroactively place its commit identifier or run result into its own ancestor report. Same-repository
hashes also do not authenticate authorship, origin, or runner integrity.

## Exact question and current answer

The intended full question is:

> Under the exact captured report source, the toolchain-selected LuaLaTeX format leaf, admitted
> LuaHBTeX/Kpathsea executables, and declared filesystem/process premises, can two isolated builds
> use one exact private format snapshot, avoid a covered map-file input, and preserve the committed
> report contract?

The current bounded local answer is **yes under the recorded Darwin/toolchain/filesystem/process
premises**. The exact direct self-test answer remains narrower:

> On the frozen production/self-test source pair, all 313 accepted and rejecting controls completed,
> the seven family counts matched their frozen values, the before/after source manifests were
> identical, and the suite exited zero without compiling the report.

The serial full checker separately demonstrated real local selection, two report builds, and exact
artifact replay. This separation still matters: mutation adequacy can falsify missing checks or
ordering, while one local full replay cannot demonstrate that Ubuntu accepts the correction.

## Why the additional format custody is necessary

The preceding map-free correction bounded a generated default font-map dependency, but its input
closure treated the selected LuaLaTeX format as an admitted toolchain premise without requiring its
runtime pathname to lie in the recorded closure. That happened to pass locally because the Darwin
format lived beneath the broad TeX installation tree. Ubuntu instead placed its generated format at
`/var/lib/texmf/web2c/luahbtex/lualatex.fmt`, outside the admitted installation-root closure. The
hosted failure therefore refuted the broader portability claim.

Widening the closure to all of `TEXMFSYSVAR` would admit mutable caches, indexes, maps, formats, and
unrelated generated state. The correction instead admits one semantically necessary leaf by exact
selection and bytes. This is narrower than admitting the generated-state root, but it does not make
the format authentic or safe. LuaHBTeX loads the format before the repository wrapper runs, so later
callback guards cannot retroactively constrain format initialization or `\everyjob` behavior.

## Mechanism in execution order

### 1. Select one exact source leaf

The checker obtains `TEXMFSYSVAR` and asks Kpathsea for `lualatex.fmt` with exact
`--engine=luahbtex`, `--progname=lualatex`, `--must-exist`, and `--format=fmt` selectors. The result
must be one nonempty, absolute, LF-free, canonically spelled path equal to
`$TEXMFSYSVAR/web2c/luahbtex/lualatex.fmt`. Empty, multiline, relative, redundant-slash,
wrong-leaf, and outside-root results fail closed.

The source must be a regular file from 1 through 67,108,864 bytes. The upper bound limits capture
memory and rejects an oversized sparse fixture before reading it.

### 2. Capture and rewalk the source

Required directory components and the leaf are opened through descriptor-relative no-follow
operations. The file is read to the exact observed size with truncation and growth rejection.
Name/descriptor identity and stable metadata are compared before and after the read. The checker
then rewalks the absolute root and relative `web2c/luahbtex` chain to reject ordinary component or
leaf retargeting across capture.

These checks narrow ordinary races; they do not defeat a privileged or same-UID actor capable of a
perfect replace-and-restore between observations.

### 3. Publish one private snapshot

The destination leaf is created with exclusive, no-follow, nonblocking descriptor flags. It must
begin as a zero-byte, single-link regular file. After a complete write, the checker fsyncs the file,
changes it to mode 0444, fsyncs again, replays the bytes through the descriptor, and rewalks the
destination chain. The containing root becomes mode 0555 and must contain exactly
`lualatex.fmt`.

This is file-content and checked-transition custody. It is not a claim of crash-durable directory
publication because the parent directory entry is not presented as durably fsynced.

### 4. Remove ambient format search fallback

`TEXFORMATS` equals only the private root. A leading, trailing, or doubled colon is forbidden
because it can expand to ambient Kpathsea defaults. Before compilation and inside each isolated
build environment, `kpsewhich --show-path=fmt` must return exactly the private root and the selected
format query must return exactly its `lualatex.fmt` leaf.

The actual `lualatex` process receives that environment. Source mutations separately reject
removing the compiler's private format environment, moving verification before the pass loop,
moving it after compiler use, and moving final verification before both builds.

### 5. Verify every use and recorder set

The mode, one-link inventory, size, path/descriptor identity, and SHA-256 receipt are replayed before
every LuaLaTeX pass and after both isolated builds. Each retained FLS pass must classify `.fmt`
case-insensitively in both raw and resolved paths, with each set equal to the one private format
path. Missing, extra, aliased, and mixed-case paths fail closed.

Raw and resolved checks are separate. The final two controls were added after review found that a
mixed-case raw `.FMT` alias resolving to a neutral target and a neutral raw alias resolving to a
mixed-case `.FMT` target killed different classifier mutations.

## Historical 266-control evidence remains immutable

The predecessor pair is preserved exactly, not rewritten as hosted success:

| Object | Bytes | Git blob | SHA-256 |
|---|---:|---|---|
| `workflow-pdf-luatex-map-free-correction-2026-08-06.json` | 32,215 | `9a07c14741ae90ef723d2e6a4b11e0a1c8912470` | `8312e5bfba9e16184ea39fac09a22baee2e38e82bc19629672da8ce8dafa22ad` |
| `workflow-pdf-luatex-map-free-correction-2026-08-06.md` | 46,089 | `621e296242c8abae7e52fe6738ecae304e3b28e5` | `2397e8da3d45818a72418bc3894ac8e9d73bbbb7400886c6c03b24df78c6e944` |

Its exact partition was `194 + 37 + 17 + 7 + 8 + 3 = 266`. Its 68-entry negative ledger remains
bound by the exact JSON rather than copied into this report. Its bounded Darwin-local observations
remain historical evidence under their stated premises, but its hosted portability credit is false
and none of its runs receive current-candidate credit.

## Terminal e53 hosted custody

### CI

- run `31071608249`, attempt 1, run number 173, exact e53;
- created `2026-08-06T04:33:55Z`, terminal update `2026-08-06T06:06:06Z`;
- 45 jobs: 44 success, one failure;
- 537 recorded steps: 534 success, one failure, two skipped; and
- every job reported exact head e53.

The failed formal-PDF job ran from `04:33:57Z` to `04:44:54Z`. Step 10, “Rebuild papers and check
cross-toolchain text, geometry, fonts, and workflow renders,” emitted the exact ambient-format
failure. No command after that point is inferred to have run, and successful commands inside the
failed composite step do not receive an independent Actions-step conclusion.

### CodeQL and the combined roster

CodeQL run `31071608063` completed four jobs and 40 steps successfully on exact e53. No alert
adjudication was performed here, so execution success is not a clean-scan or vulnerability-absence
claim.

The machine companion carries all 49 job IDs, names, and conclusions. It also binds a canonical
roster projection of 13,471 bytes with SHA-256
`ca1abbf3245d412d70eca7d67eb1c2447741813f69325f02ccc6b38c5023e68d`.

Two byte-identical REST run-log ZIP downloads were observed for each workflow:

| Workflow | ZIP bytes | Entries | SHA-256 |
|---|---:|---:|---|
| CI | 856,315 | 105 | `8323acddf6578aafa6384b7b5a69c5185fedd94b02c789d2700ba62f206b3ce3` |
| CodeQL | 138,139 | 8 | `6c47b671810920ae8d612574eff79e5883b76d8a5c5959ec810c908edef3c632` |

Those diagnostic ZIPs are not committed and therefore have local-ephemeral, not repository or
remote-durability, custody. ZIP bytes, extracted entries, per-job REST bytes, API roster JSON, and
separately constructed bundles are different digest domains.

## Exact 313-control source and pass

| Executed source | Bytes | Mode | Git blob if hashed now | SHA-256 |
|---|---:|---:|---|---|
| `scripts/check-mathematical-workflow-pdf.sh` | 231,236 | 0755 | `68e92460c530d240e94416d5d89a136e78818ba9` | `6e1fc6eef6286b9e475d758419400e6c9a102d369bb5e1fd98b00a3b68ced833` |
| `scripts/check-mathematical-workflow-pdf-self-test.sh` | 252,763 | 0755 | `4df1475de765d0c998daf0497bc33ecc5af4f3d9` | `c7902373cca3cbcdf042cd2e093d1601f1f81929afdf189ba44c665153a2eae1` |

The before and after two-line source manifests are each 228 bytes with SHA-256
`2a869a2b8ef7f77dfb43bcad9ee0e6d447dfadb0ad96045590f1a905d75a038e`.
The 24,164-byte, 314-line self-test log has SHA-256
`9f6c91de47bbc5fb7d36f0fd55885b25402909b7ebe8cef8495c8461ef8e0166`.
It contains 313 ordered `ok` rows followed by the exact frozen-family summary and exited zero.
The time receipt records 121.28 seconds real, 74.36 seconds user, and 34.45 seconds system.

The exact launcher argv was not retained in the supplied receipt, so this report does not invent
one. The log and source/time receipts currently live under `/private/tmp` and are not claimed as
repository-retained raw evidence.

The frozen partition is:

| Family | Controls |
|---|---:|
| predecessor | 194 |
| bounded probe | 37 |
| entry wrapper | 17 |
| runtime map | 7 |
| FLS map path | 8 |
| executable custody | 3 |
| format custody | 47 |
| **total** | **313** |

These are correlated deterministic fault probes sharing source, fixtures, validators, host, and
toolchain. They are neither 313 independent defenses nor 313 scientific replications.

## Serial full-exact replay

The first full-exact attempt on the 313 source failed closed after 833.63 seconds. The
Kpathsea/XML-unsafe repository-root probe produced no atomic decision record, so the bounded
harness returned custody status 125 rather than crediting an arbitrary nonzero result. Two reviewer
mutation replays overlapped that attempt; contention is a plausible explanation, not an established
cause. A focused execution after those heavy replays stopped returned the intended exact status 2
and unsafe-root diagnostic. That diagnosis does not convert the failed full attempt into a pass.
The failure remains `C3-FMT-N012` below.

The subsequent serial full-exact invocation was:

```text
working directory: /private/tmp/pid-rs-c3-hosted-receipt.65QZZA/worktree
argv:              scripts/check-mathematical-workflow-pdf.sh
exit:              0
real/user/system:  765.72 / 440.19 / 104.11 seconds
```

The seven-object before and after source manifests are each 802 bytes with identical SHA-256
`24a08a3efdc65fa8d7ac579c07904ded089ba9980853386b0c2234c34172de0a`. The 597-byte terminal log
has SHA-256 `017a55a2c593af3bd4f2341f969c5a9fcd3e7658583cb25fa0456de2e4cb5846`.
That log happens to equal the superseded 301-run success log because the terminal success line does
not encode the mutation count. No source credit is transferred: this run is bound by its current
unchanged source tuple and execution receipt.

The final local receipts were:

| Object | Exact observation |
|---|---|
| workflow PDF | 626,770 bytes; 51 pages; SHA-256 `f372256011d1173a020d39b86cba5ab7959fb07cea09cf1a2b7eeb292a83cafe` |
| dual-render receipt | SHA-256 `847685d91b6a565ba37c077515396e3bb83fb1ed18d295a14b4eb3ebe9bedcaf` |
| executable manifest | SHA-256 `5053eb6d7deb625d42cb23590e6fb8529043b9f26d01b28ba364c3c58cdc1d85` |
| pypdf manifest | SHA-256 `dc0d7ee2d29c666298f5fce601068b2459a4f89057dd42beda343e002b432863` |
| private format snapshot | 12,255,194 bytes; SHA-256 `e254bc4c8dc1304a4cc099c92ad6e4d81da90805d113069c954da5a69d04bffa` |

The log/time/source files live under `/private/tmp`; they are locally ephemeral, not
repository-retained raw evidence.

## Current visual and enclosing-custody replay

Poppler `pdftoppm` 26.06.0 rendered all 51 pages at 120 DPI in color and grayscale. Nine contact
sheets in each mode were inspected in page order. Pages 3, 4, 9, 10, 14, 15, 18, 20, 21, 27, 30,
32, 36, 37, 40, 42, 43, 45, 47, 48, 50, and 51 were also opened at original render resolution.
No blank, clipped, overlapping, misordered, visibly corrupt, unreadable-grayscale, broken-glyph,
table, figure, header/footer, or pagination defect was observed. Page 51 is intentionally sparse
but contains 888 extracted characters. The contact-sheet, color-page, and grayscale-page ordered
manifest digests are respectively `78ab0fe5cc3045fcc75a21c4bb0be9f1ade2ec3198e31353f5fea8343afcd1ba`,
`32533ed8e02bcb09c28eb040acedbbe042f638bda7f23c4c89376cdad47aad1c`, and
`9b4e0478cf7636fa2e8a09f72724dee94276078ffa50cd8ed840c2cd46c95b2b`.
The render files live under ignored `tmp/pdfs/`; their manifest digests bind this local observation,
but the files are not repository-retained or remotely durable.

After rebinding the final `scripts/README.md` SHA-256
`3a64f5e7987b85ea665abad646182f67bfdfee86a11ca4bdff9ef256784e0404`, the certified-SxPID2
enclosing checker passed in normal and optimized Python, and its self-test rejected 111 mutations
in each mode. This is only enclosing documentation-digest custody; it is not a new or upgraded
SxPID result.

## Current artifact observations

| Artifact | Bytes | Current observation | SHA-256 |
|---|---:|---|---|
| workflow PDF | 626,770 | 51 pages, PDF 1.7, bytes unchanged | `f372256011d1173a020d39b86cba5ab7959fb07cea09cf1a2b7eeb292a83cafe` |
| rendering receipt | 11,249 | bytes unchanged | `847685d91b6a565ba37c077515396e3bb83fb1ed18d295a14b4eb3ebe9bedcaf` |
| historical visual receipt | 1,237 | historical bytes unchanged | `ad11eed69ca56401f32e12fb1fb47d59682c6aa65b26deb36d89be2c87c708cb` |

Byte equality preserves the exact historical artifact. The serial full checker regenerated both
isolated report copies and obtained those same bytes; the current visual review inspected fresh
renders. No PDF content was regenerated by the standalone direct self-test.

The bounded local format observation is:

```text
/usr/local/texlive/2024/texmf-var/web2c/luahbtex/lualatex.fmt
12,255,194 bytes
SHA-256 e254bc4c8dc1304a4cc099c92ad6e4d81da90805d113069c954da5a69d04bffa
source mode 0644; one link
Kpathsea 6.4.0; LuaHBTeX 1.18.0 / TeX Live 2024
```

Future Ubuntu bytes are expected to be recorded independently. Cross-platform format-digest
equality is neither required nor claimed.

## Retained successor negatives

| ID | Finding | Final credit |
|---|---|---|
| `C3-FMT-N001` | Exact e53 hosted job loaded the ambient Ubuntu format. | terminal negative only |
| `C3-FMT-N002` | First diagnostic used the wrong Kpathsea query and stopped before evidence files. | none |
| `C3-FMT-N003` | Green 280-control/direct and 416-byte exact runs lacked format-specific attacks and a final receipt. | none; source superseded |
| `C3-FMT-N004` | Heredoc extraction marker was not unique. | none |
| `C3-FMT-N005` | Expected source-literal fixture bytes were malformed. | none |
| `C3-FMT-N006` | Overbroad fixture edit created `format/lualatex.fmt` as a directory. | none |
| `C3-FMT-N007` | Missing sparse fixture raised `FileNotFoundError` before the oversize mutation. | none |
| `C3-FMT-N008` | Green 301 exact run, 597 bytes and SHA-256 `017a55a2…`, was invalidated by later mutations/source changes. | none; source superseded |
| `C3-FMT-N009` | Green 311 suite was followed by a zsh wrapper assignment to reserved read-only `status`; wrapper exited 1 before its after-source tuple. | none; incomplete receipt |
| `C3-FMT-N010` | Raw and resolved mixed-case `.FMT` classifier mutations survived the 311 source. | none; source superseded |
| `C3-FMT-N011` | Historical alternate-index command used zsh `$C3_TREE:audit` path-modifier syntax and failed before verification. | none |
| `C3-FMT-N012` | First 313 full-exact attempt produced no atomic decision record for the unsafe-root probe and returned custody status 125; a later focused branch check does not repair that failed run. | none; terminal local negative |
| `C3-FMT-N013` | A successor precommit loop assigned repository names to zsh's special tied `path` array, thereby rewriting `PATH`; later `git` calls were not found, and no commit or push occurred. The already checked index/tree became stale when this negative was added and must not be reused. | none; operational negative |
| `C3-FMT-N014` | A fresh 71,520-byte index was shared by pathname with a reviewer; Git later rewrote cache metadata, changing its SHA-256 from `06e4b87d…` to `d1228eba…` while preserving tree `a34b461c…`. Local provisional commit `eecea3d…` was therefore rejected, never pushed, and detached `HEAD` was returned to e53 without touching worktree files. | none; local provisional commit rejected |

The 311 self-test log is 23,990 bytes with SHA-256
`1a6be60a819ec74cc240cf5994a882927ed35c0afc12b31b9c94c4be01a90c70`.
Even if its outer receipt wrapper had succeeded, the mixed-case mutation findings independently
make those source bytes uncreditable for final closure.

## Review lifecycle

The 280 candidate received two separately prompted NO-GO reviews. They are task-diverse views, not
institutionally independent review. Their valid findings led to format-specific symlink, FIFO,
race, replay, and final-receipt controls.

The 301 review found missing source bounds, compiler-environment consumption, verifier-order, and
complete final-receipt mutation adequacy. The 311 review then separated raw and resolved FLS
case-sensitivity. Each superseded candidate and negative finding remains in the record rather than
being rewritten as part of the final pass.

Two separately prompted reviewers returned bounded GO dispositions on exact production SHA-256
`6e1fc6ee…` and self-test SHA-256 `c7902373…`. The capture-design review found no surviving
format-custody counterexample. The mutation review additionally killed a raw-classifier-only
casefold mutant at control 134 and a resolved-classifier-only casefold mutant at control 135; their
mutant/log identities are retained in the JSON. These reviews are neither institutionally
independent nor execution substitutes; the serial full checker is recorded separately.

## Twenty-lens adjudication

| Lens | Current disposition |
|---|---|
| 1. lineage | Exact e53 parent/tree and C3 root bound; successor commit pending. |
| 2. acyclicity | JSON does not hash itself/Markdown; commit/tree/run facts deferred. |
| 3. source bytes | Exact production/self-test hashes, sizes, modes, and current blob hashes recorded. |
| 4. execution identity | Direct and serial-full before/after manifests match; full argv and working directory recorded. |
| 5. dependency semantics | One necessary pre-wrapper format leaf identified; no general SYSVAR admission. |
| 6. query grammar | Empty, multiline, relative, redundant, wrong-leaf, and outside-root cases covered. |
| 7. source capture | No-follow descriptors, size bound, identity checks, and complete rewalk covered. |
| 8. destination publication | Exclusive one-link file, mode, fsync, replay, inventory, and rewalk covered. |
| 9. search semantics | Exact no-colon `TEXFORMATS` and Kpathsea path/selection preflights covered. |
| 10. compiler consumption | Environment and verifier-order source mutations covered. |
| 11. raw FLS classification | Exact set and independent mixed-case raw alias control covered. |
| 12. resolved FLS classification | Exact set and independent mixed-case resolved target control covered. |
| 13. mutation adequacy | 313 direct controls passed; correlated, not independent. |
| 14. artifact currency | Serial full exact replay and current 51-page color/grayscale visual review passed. |
| 15. hosted portability | e53 is terminal red; new exact-commit run does not yet exist. |
| 16. archive custody | Exact digest domains recorded; diagnostic ZIPs remain locally ephemeral. |
| 17. review | Earlier NO-GO findings retained; two exact-313 bounded source-review GOs recorded. |
| 18. security | CodeQL executed; no security-clean, sandbox, or authenticity claim. |
| 19. PID semantics | Explicit firewall prevents transfer among KSG, Ehrlich, MGW, `I_min`, fitted PID, and wrappers. |
| 20. lifecycle | Staging, commit, push, hosted replay, and strict-descendant receipt remain open. |

## Premises, exclusions, and nonclaims

The correction assumes trusted captured source; the tested Bash/Python/TeX/Poppler/pypdf behavior;
ordinary descriptor and filesystem semantics; exact Kpathsea search behavior; and sufficient
process-inspection and reaping progress. It excludes hostile pre-wrapper format behavior,
privileged or same-UID perfect replacement races, deliberate process-group escape, PID/PGID reuse,
and crash-durable directory publication.

It does **not** establish:

- format, package, toolchain, executable, runner, kernel, or Git authenticity;
- a hostile-TeX/Lua sandbox or generic process containment;
- syscall-complete or atomic I/O evidence from FLS;
- cross-platform format or PDF byte identity;
- mathematical truth, citation correctness, novelty, accessibility, or publication acceptance;
- security cleanliness or vulnerability absence;
- KSG consistency, support eligibility, bias, or KSG M1c closure;
- Ehrlich continuous shared-exclusions PID validity;
- categorical Makkeh-Gutknecht-Wibral SxPID validity;
- Williams-Beer `I_min`, fitted quantized PID, heuristic, wrapper, ecosystem, or downstream validity;
  or
- any mapping among those distinct families without a premise-explicit mapping theorem.

## Pending gates and closure protocol

Bash syntax, ShellCheck, direct 313 replay, serial full exact replay, current visual review,
exact-source review, and certified-SxPID2 enclosing custody are closed locally for the recorded
tuple. The following fields intentionally remain pending in the machine companion:

1. final machine/Markdown consistency, source/artifact/log replay, and whitespace gates;
2. a fresh task-specific alternate index containing only enumerated paths;
3. a small unsigned no-attribution direct-child commit and fast-forward push;
4. terminal all-green CI and CodeQL on the same exact implementation commit; and
5. a strict-descendant receipt binding all post-report facts and every retained red predecessor.

The historical e53 alternate index remains historical only:

```text
/private/tmp/pid-rs-c3-alt-index.dWftY3/index
71,232 bytes
SHA-256 9a05d0b95dbac1c8e84572b6f4c669aa7d2593ad9034aeb3ddfb2bcc6400361d
tree 6f222b0f6eba9933faa659fc8d2a362ea40b0f6b
```

It must not be reused for the successor. The new index must be seeded from freshly authenticated
e53, stage only explicit paths, verify modes/blobs/hashes/whitespace/protected projections, and
write a tree without editing this report afterward. Only the later descendant may bind that tree
and commit without a cycle.
