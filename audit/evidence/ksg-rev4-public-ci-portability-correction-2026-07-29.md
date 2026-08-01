# KSG revision-4 public-CI Lean evidence portability correction

Date: 2026-07-29
Status: `integration_no_go` pending a fresh, complete, all-green public CI run
Scope: M1a-C3 nineteen-path POSIX Lean replay, isolated Python entry,
evidence-custody, and foundational-publication correction only

## Adjudication

Public CI run `30431352389` is terminal. Forty-four of forty-five jobs
succeeded. The sole failed job exposed a cross-host serialization defect in
one generated Lean receipt: the checker embedded the host platform token from
`lean --version`, then the PDF wrapper required byte equality with evidence
generated on another platform.

This is an evidence-envelope failure, not a theorem failure, tool-provisioning
failure, scientific counterexample, estimator change, or numerical change. It
also means the complete run is not green. KSG repository/publication
integration therefore remains `NO-GO`.

The canonical machine receipt is
`audit/evidence/ksg-rev4-public-ci-run-30431352389-failure.json`, SHA-256
`73c8b509304f0a23382f531d9b94511c58f14f1e5a75ef1147d8cbb80bf02a20`.

## Frozen ancestry and scope

| Role | Commit | Tree | Disposition |
|---|---|---|---|
| M1a scientific integration | `dc7b8de0a87443ef2bcde71b19938642f1af2197` | `88b24c0ba4fcad4bd749b9146486143397b6a6eb` | Bounded KSG arithmetic core retained |
| M1a-C1 corrective parent | `af50935be9ecf9a81aeb30c56b45059652468746` | `ada3860eb696c9a5d634728365acdb5958e7c4e6` | Hosted tooling failures retained |
| M1a-C2 provisioning correction | `8b792bc143fff2d84f2d8e7817d1de7850741223` | `8e247b9a6c46fd6266fe4fc02fbe9c3142268215` | Subject of the terminal 44/45 run |
| This M1a-C3 correction | one direct child of exact M1a-C2 | must be externally pre-pinned before commit | Still `NO-GO` until a whole hosted rerun succeeds |

The schema-revision-6 C3 policy permits exactly these nineteen sorted paths:

```text
.github/workflows/ci.yml
AGENTS.md
CHANGELOG.md
FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md
audit/evidence/foundational-sxpid-descriptor-factorization-lean.json
audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json
audit/evidence/ksg-rev4-8b792-ci-portability-path-policy.json
audit/evidence/ksg-rev4-public-ci-portability-correction-2026-07-29.md
audit/evidence/ksg-rev4-public-ci-run-30431352389-failure.json
audit/formal/latex/foundational-shared-exclusions-pid-audit.tex
audit/tools/foundational_sxpid/README.md
justfile
output/pdf/foundational-shared-exclusions-pid-audit.pdf
scripts/check-certified-sxpid2-claim.py
scripts/check-foundational-sxpid-audit-pdf.sh
scripts/check-ksg-phase-isolation-self-test.py
scripts/check-ksg-phase-isolation.py
scripts/check-lean-descriptor-factorization-self-test.py
scripts/check-lean-descriptor-factorization.py
```

The historical receipt remains byte-for-byte historical. Its then-selected
four-file/v2 remediation is preserved as a fact about that failed run, but
later hostile review supersedes only that remediation choice as final
authority. The workflow and publication command bytes now change, so they are
not falsely described as frozen. The theorem source, Lean project pins,
scientific prose, method catalog, public API, identity, release state, Rust and
Python scientific code, numerical outputs, estimands, PID2, PID3, and frontier
mathematics remain frozen.

## Terminal hosted evidence

- CI run `30431352389`, workflow ID `297369773`, run `147`, attempt `1`,
  event `push`, branch `main`.
- Subject commit/tree:
  `8b792bc143fff2d84f2d8e7817d1de7850741223` /
  `8e247b9a6c46fd6266fe4fc02fbe9c3142268215`.
- Time envelope: `2026-07-29T07:21:26Z` through terminal update
  `2026-07-29T07:48:21Z`.
- Jobs: `45` total, `44` success, `1` failure.
- Actions steps: `534` total, `532` success, `1` failure, `1` skipped.
- KSG phase job `90509073372` succeeded, including its arithmetic,
  certificate, mutation, Git-phase, compiled-path, and serial/parallel steps.
  Its decoded REST log is `78318` bytes with SHA-256
  `f197b00e992f58f00695b68315e1864937f886e47f1823208d3ca177a716f087`.
- Certified SxPID2 job `90509073386` succeeded. Current steps 21--25
  recovered every substantive route that had failed or been skipped in the
  previous run; setup-python cleanup step 49 also succeeded. Its decoded log
  is `155426` bytes with SHA-256
  `a9415c629d36100514be65a193d2d30e7bc0e5188f42fd3c7d3ba5d37f4a206a`.

These are bounded command-execution facts. They do not make the complete run
green and do not establish universal correctness.

## Sole failure and credit boundary

Formal-PDF job `90509073390` failed in Actions step 8 with the exact error:

```text
foundational shared-exclusions PID audit PDF check: Lean factorization evidence is stale or not reproducible
```

The decoded REST job log is exactly `58025` bytes with SHA-256
`06c612a30cd02dc9f9a3957b47cdf96cd2d2e75ff08cf050272bcb518d49b234`.
Post-cache step 15 was skipped and receives no credit.

The composite shell step emitted completion markers for the PDF style checker,
its six-mutation self-test, and six paper routes: certified SxPID2,
dependency-colored SxPID, ecosystem compatibility, exact log-product,
finite-alphabet convergence, and formal-tool adoption. GitHub assigns no
independent Actions-step conclusion to those commands because their containing
step failed. The foundational route failed before its mutation checker and
PDF structural checks completed. The mathematical-workflow and
support-change-tolerant routes were unreached.

## Root cause from first principles

The committed wrapper uses `set -e`, runs the descriptor checker into a
temporary file, and prints the observed stale-evidence message only when the
checker has returned zero and raw `cmp` has found different bytes. Reaching
that message therefore implies, within the hosted execution model, that the
checker completed its pinned source/project checks and required exactly three
axiom-free theorem reports. This is a control-flow inference, not an
independently retained runner receipt and not an authenticity claim.

The C2 receipt is `788` bytes, SHA-256
`8c0d7e055acf4982854ce708e7b8c10ef7ef56fab12819e0831bf769363bd1e2`,
and records:

```text
Lean (version 4.32.0, arm64-apple-darwin24.6.0, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)
```

An exact Linux line with the same version, source commit, and release build but
platform `x86_64-unknown-linux-gnu` is retained in the different same-run
certified job `90509073386`, step 21, whose decoded log is `155426` bytes with
SHA-256
`a9415c629d36100514be65a193d2d30e7bc0e5188f42fd3c7d3ba5d37f4a206a`.
It is a host-output control, not the deleted descriptor-checker stdout or
temporary JSON from the failed formal-PDF job. Reconstructing the otherwise
deterministic descriptor receipt with that platform yields `788` bytes and
SHA-256
`5bfa5e4204c96ea96f719475944604692aaa372dc8ee5f9e729dbe5817d26184`.
That second digest is explicitly a deterministic reconstruction: the runner
temporary file was deleted and is not claimed as directly retained.

The control-flow evidence, same-run host-output control, and deterministic
reconstruction jointly support diagnosing the failed equality as equality of
a platform-bearing observation rather than disagreement about a theorem,
source hash, manifest, toolchain selector, version, source commit, build
flavor, theorem count, or axiom inventory. They do not directly retain the
failed job's descriptor output.

## Exact correction

The correction is layered because no single control establishes source,
process, dependency, theorem, publication, and Git custody.

### Isolated Python entry

Every official phase, descriptor, foundational wrapper, AGENTS, justfile, and
CI invocation now uses `python3 -I -S`; optimized coverage uses
`python3 -I -S -O`. Each phase and descriptor entry point also checks
`sys.flags.isolated`, safe path, no-site mode, and ignored environment before
its first non-builtin import. The guard is detection only under ordinary
Python: hostile `sitecustomize` and `usercustomize` code can execute before the
guard rejects the process. The retained containment route is the isolated
invocation, tested in normal and optimized modes under hostile current
directory, `PYTHONPATH`, `PYTHONHOME`, and startup-hook inputs.

The phase checker never executes the live descriptor self-test pathname. It
first binds the candidate self-test and descriptor-checker digests, writes
those exact bytes into a private directory, and executes the self-test bytes
from standard input with a fixed 373-byte builtins/`sys` bootstrap. The child
environment is a minimal finite map. Attacks remove standard input, substitute
the live pathname, weaken `compile(..., dont_inherit=True)`, widen the child
environment, and remove private checker materialization.

Every directly path-invoked C3 Python script is still initially loaded from
its requested pathname before its own checks can run. This includes the phase
checker and self-test and the wrapper's exact-rational, descriptor-checker,
and descriptor-self-test entries. Their settled-byte/no-concurrent-writer
identity is a premise, not an atomic loader guarantee. Respectively, the phase
checker's standard-input child route and the descriptor self-test's
exact-source child loader bind their child source bytes before execution; neither
retroactively proves which bytes a separate, already-running direct entry
loaded. The external tree/checkpoint binds the reviewed final bytes, not that
earlier runtime observation. Closing this repository-wide Python-entry cut is
the separately named post-C3 custody milestone.

### Exact-source and POSIX snapshot custody

The descriptor self-test demonstrates why ordinary `SourceFileLoader` plus
`PYTHONDONTWRITEBYTECODE` is insufficient: a pre-existing unchecked-hash
`.pyc` can substitute different code, and a parent-directory swap/use/restore
can control a live pathname. The selected bootstrap double-reads exact source,
checks its frozen SHA-256 before compile/exec, and rejects a malicious parent
substitution before execution. A post-digest parent-to-symlink substitution
also verifies that checker `SCRIPT_PATH` and repository root are derived
lexically rather than redirected by a second pathname resolution. This
digest-binds reviewed bytes and path semantics; it does not authenticate their
provenance or provide descriptor-topology custody for the already-running
bootstrap.

Full kernel replay is a separately typed POSIX route. It traverses every path
component with directory descriptors and no-follow flags, rejects symbolic
parent or leaf components and multiply linked tracked leaves, double-reads
each regular file, records endpoint identity, and replays the endpoint after
use. Five single-linked tracked inputs are covered: theorem source,
`lake-manifest.json`, `lean-toolchain`, `lakefile.toml`, and the descriptor
checker itself. The selected Lake proxy target is observed separately and may
have multiple links. Six hostile cases cover between-snapshot mutation,
symbolic leaf, mutation during double-read, symbolic parent, hard-linked leaf,
and parent replacement during snapshot.

Endpoint replay is not an atomic history. A demonstrated parent
swap/use/restore can evade it. The containment route for tracked project bytes
is private materialization: exact manifest, toolchain selector, and lakefile
bytes are written under their exact names to a private project before Lake is
invoked. The child working directory is opened by verified directory
descriptors, identity-matched, inherited, and selected with `fchdir`; every
finite-name Lean query is created relative to the identity-bound query
directory and passed to Lean as a relative path. A deterministic
fake-launcher attack swaps the private-project pathname after descriptor
pinning and confirms that the child consumes the reviewed project/query
rather than the substitute. Query and project endpoints are replayed after
use. This closes that tested whole-project pathname-substitution family. A
separate retained negative swaps only the `queries` child after the project
descriptor is pinned, consumes the attacker query, restores the reviewed child
before replay, and passes the endpoint checks. The project descriptor does not
pin that child entry; a settled query subtree and no concurrent privileged or
same-UID writer therefore remain explicit premises rather than a claim of
atomic filesystem history.

The explicitly passed private-project directory descriptor remains inherited
by the direct launcher/Lean child and may remain inherited by its descendants;
unrelated ambient inheritable descriptors are closed. This is an intentional
residual capability and process-lifetime nonimplication, not an additional
source-custody guarantee, independent custody evidence, or a scientific
failure.

The private project deliberately routes its `.lake/packages` entry to the live
dependency cache. A mutation control demonstrates that the cache remains
observable. Like the finite phase child environment, the Lean launcher
environment deliberately retains `HOME`; a separate negative demonstrates
that retained `HOME` reaches and can influence selected launcher state. If an
Elan proxy is selected, its ordinary home-relative state remains a live route;
the generic fixture does not itself authenticate or emulate Elan. Mathlib
checkout/olean/cache contents and HOME-influenced launcher/toolchain state are
therefore live and unauthenticated; the result must not be described as a
hermetic dependency snapshot. Python, Lean, Lake, the dynamic loader,
libraries, filesystem, kernel, and hardware are likewise not authenticated.

Native Windows full custody is unsupported and fails closed. Python's POSIX
directory-descriptor contract is not approximated by pathname `lstat`; a
future native route would require audited handle-relative traversal, reparse
point rejection, stable file identity, and rename/delete sharing controls.
The POSIX no-kernel controls exercise macOS arm64 and Ubuntu x86_64 output
shapes plus source/filesystem/environment custody; they are not a native
Windows run.

### Typed portable evidence

The descriptor checker treats the complete version process result as a typed
observation:

1. give the child `/dev/null` standard input rather than inherited parent
   input;
2. capture standard output and standard error as separate raw byte streams;
3. validate standard output before standard error, rejecting carriage returns
   before strict UTF-8 decoding in each stream;
4. require exit code zero;
5. require empty standard error;
6. require exactly one complete newline-terminated standard-output line;
7. parse the whole line with an anchored grammar;
8. require version `4.32.0`, exact reported source commit
   `8c9756b28d64dab099da31a4c09229a9e6a2ef35`, and build `Release`;
9. syntactically validate a nonempty multi-component platform token; and
10. serialize only version/commit/build in v4 evidence while stating that the
   platform observation was validated but not serialized.

The same v4 receipt separately serializes the frozen theorem-source,
manifest, `lean-toolchain`, `lakefile.toml`, and checker-source digests. The
selected Lake proxy target is observed and endpoint-replayed, but its
host-specific path and byte digest are deliberately not serialized into the
portable receipt. Those observations are local process-custody facts, not an
authenticated executable identity.

The byte pipes are drained through `subprocess.run`/`communicate`, but neither
captured stream has an explicit byte ceiling. A timeout terminates and waits
for only the direct child and does not guarantee descendant termination.
Regular source, project, checker, and launcher-target bytes are likewise
accumulated without an explicit input-size ceiling before their digest and
replay checks. These are denial-of-service and process-cleanup nonimplications,
not portability, theorem, or scientific claims.

On the current descriptor-route bytes, isolated normal and optimized direct
replays and full mutation/self-test replays were byte-identical within each
route. The installed direct v4 receipt is `3421` bytes, SHA-256
`63c124ceb985313083ec83aad0aea3c8f0fe328ed16abfe43fc91eb5c1fa68a6`;
the installed mutation v4 receipt is `13428` bytes, SHA-256
`b644060ac17f58a966aaebd996ceffe6c707fe4d489864fac20ef64cb0218bb9`.
Parser-only normal and optimized outputs are each `12166` bytes, byte-identical,
and SHA-256
`b08bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6`.
An independent review recomputed the receipt schemas, source/configuration
pins, theorem and mutation hashes, counts, pairwise-distinct probe hashes, and
parser-only equality. The full normal/optimized outputs were not retained as
two independent filesystem artifacts, so this is an execution observation
plus independent receipt-contract review, not a second independent full
kernel replay or runtime-authenticity claim. Earlier smaller provisional v3
outputs remain rejected and receive no credit. At audit time their normal and
optimized pairs were still present only in local temporary storage:
`/private/tmp/c3-lean-v3{,-opt}.json` are each `1731` bytes, SHA-256
`3d8e0d03b38d37af476b638d173b72f8511d9eac6ddbb3ec6b7c5659f7fc65ef`,
and bind obsolete descriptor-checker SHA-256
`cf78246c4dc0b61fd760d7060c9ea06912910b0f7da2c13bd10c339e3e11a61f`;
`/private/tmp/c3-mutations-v3{,-opt}.json` are each `5523` bytes, SHA-256
`2b1174621534e745813d7ecdd9eaff9ec3bb7083b57fdbd1a4ff51bd3cdd2aef`,
and bind obsolete self-test SHA-256 in the provisional mutation receipt's
then-named `checker_source_sha256` field:
`ef34983d60847abd58990a15550742abd74bf438fcec2b7c02bb16f3d8888b3b`.
These temporary files are not repository evidence and carry no retention,
authenticity, or final-byte claim.

The wrapper retains exact byte comparison. Two real macOS/Linux parser
fixtures must produce the same portable projection. Nineteen separately
counted hostile probes attack process failure, standard error, missing or
extra lines, whitespace/payload injection, version drift, malformed or
missing platforms, commit-label and 40-lowercase-hex drift, build drift, and
delimiter loss.

The portable-control inventory is frozen independently of the scientific
inventory:

| Family | Exact count |
|---|---:|
| Exact-source loader controls | 4 |
| Input-snapshot hostile cases | 6 |
| Private-materialization controls | 3 |
| Raw-process transport hostile cases | 5 |
| Child-stdin isolation subcontrols | 1 |
| Cross-stream precedence subcontrols | 1 |
| Retained negative controls | 4 |
| Distinct-platform parser controls | 2 |
| Hostile version probes | 19 |
| Scientific proof mutations killed | 3 |
| Finite semantic countermodels kernel-checked | 3 |

The exact-source, snapshot, private-materialization, raw-transport,
child-stdin, cross-stream, retained-negative, platform, and hostile-version
lists contain `45` probe records in total, and all `45` recorded probe hashes
are pairwise distinct. The scientific mutation and finite-countermodel counts
are separately typed and are not added to that probe-record total.

These are descriptor-route internal inventories. The fourth retained negative
is checked by the existing phase Lean-portability schema/count mutation and
does not create an additional top-level phase case; the separately contracted
phase aggregate changes only when a top-level hostile case is added.

The original scientific evidence remains separately stated: three theorems
kernel-checked with an empty axiom inventory, three proof mutations killed,
and three finite semantic countermodels kernel-checked. None of the parser,
source-loading, or custody cases is counted as a scientific proof mutation.
The Lean theorem source and all project pins are unchanged.

### Hostile phase-suite count authority

The policy freezes all contracted family inventories and the self-test rejects
missing keys, extra keys, per-family drift, total drift, and separate-control
drift. The independently summed contracted aggregate is 351 cases; credit
requires settled final-byte normal and optimized replays:

| Family | Cases |
|---|---:|
| Checker model | 44 |
| Python entry attacks | 18 |
| Policy authority | 44 |
| Path custody | 8 |
| External tree | 9 |
| Git context | 16 |
| Prior public-CI evidence | 21 |
| Public-CI portability evidence | 34 |
| Lean portability | 17 |
| Rebased semantic firewall | 76 |
| Lifecycle/history | 30 |
| Entry isolation | 5 |
| Success-receipt oracle | 11 |
| Failure-receipt oracle | 18 |
| **Total** | **351** |

The JSON type firewall has two additional controls and the retained
coordinated-self-reference boundary has one; both are typed separately from
the aggregate. These counts are contracted case inventories and describe
executed cases only after a suite completes. They do not claim independence,
completeness, statistical power, security coverage, mutation adequacy,
authenticity, or scientific correctness.

### Exact process-receipt oracles

The earlier subprocess wrapper treated success and failure asymmetrically:
successful runs were only beginning to acquire structured output checks,
while rejected mutations were accepted whenever any nonzero process placed an
expected substring anywhere in combined standard output and standard error.
That was a false-red oracle: an unrelated exit status, forged standard output,
or traceback could masquerade as the intended rejection.

Success now means exactly status 0, empty standard error, and one strict-UTF-8,
LF-terminated standard-output line with no carriage return. Fifteen ordered
fields must match independently held ancestry, path counts, lifecycle,
candidate tree, checkpoint, Git identity, and the exact nonclaim. The caller,
not the receipt, supplies the expected lifecycle. Eleven contracted mutations
cover a nonzero status, nonempty standard error, missing final LF, an extra
line, a carriage return, the expected prefix embedded mid-line, forged
candidate-tree and checkpoint values, trailing text, promotion of the
nonclaim, and a coordinated precommit-to-committed lifecycle/count forgery.

Failure now means exactly status 1, empty standard output, and one
strict-UTF-8, LF-terminated standard-error line with no carriage return,
beginning `ERROR: KSG phase isolation: `. Its nonempty canonical detail must
round-trip as exact `ensure_ascii` JSON-string content, contain the
independently expected reason, and be fully consumed by exactly one reason
template compiled from the unmutated suite-root checker source. That
premise-bound source model freezes 383 `require` call sites, 43 direct
message-producing `PhaseIsolationError` sites, and 408 distinct full-message
templates. The one generic `PhaseIsolationError(message)` forwarder inside
`require` is deliberately excluded rather than double-counted.
Per-observed-detail normalized-template uniqueness does not prove that all 408
regular-expression languages are globally pairwise disjoint, nor that a
matched normalized template identifies one originating call site; duplicate
template shapes exist.

The earlier 380/43/407 seal predated the final foundational-PDF navigation
firewall. The first ordinary-mode aggregate on the repaired wrapper stopped
before hostile-case credit with `checker failure-message call-site/template
inventory changed`; that run receives no aggregate or partial-family credit.
Two exact-AST derivations then reproduced 383/43/408. A subtractive derivation
removed only `validate_foundational_pdf_lake_preflight` and recovered exactly
380/43/407. The function contributes three `require` sites, no direct
`PhaseIsolationError` sites, and two local template shapes; its whole-wrapper
and finite-reversal checks deliberately share one existing diagnostic, so only
the unique-delimiter check adds a globally new template. The resulting
`+3/+0/+1` reseal changes no 351-family count and is source-shape custody, not
proof of global language disjointness, causal independence, or security
completeness.

An adversarial predicate review also showed why the reseal is not mutation
adequacy for those three call sites: replacing a new predicate by
`require(True, ...)` can preserve 383/43/408, as can coordinated replacement
of the wrapper plus its reviewed digest. Two of the three sites intentionally
share one diagnostic, and the whole-wrapper digest is checked on another
authorized route as well; they are not three independent guards. The eight
normal and eight optimized embedded-parser mutations exercise the stated
navigation branches, while exact full-wrapper custody, finite reversal to the
parent transform, independent review, and later external tree/checkpoint
custody are separate correlated lenses. C3 does not add three new contracted
phase cases or claim predicate-level mutation completeness for this firewall;
doing so would require a separately reviewed hostile-inventory revision rather
than relabeling the frozen 351-case contract.
Eighteen contracted mutations cover a different status, forged standard output,
missing final LF, a multiline traceback, carriage-return injection, loss of
the typed prefix, a wrong reason, invalid UTF-8, unrelated text before the
expected reason, forged text after it, both-sided reason forgery, a raw quote,
an invalid JSON escape, a valid but noncanonical JSON escape, substitution of
a caller-held dynamic path, an empty diagnostic tail, diagnostic-tail boundary
whitespace, and substitution of a caller-held diagnostic-route object ID. The
three prefix/suffix cases use a constant-message fixture.
Every exercised dynamic value is instead bound by a caller-constructed exact
whole detail. Only three closed route classes admit a nonempty stripped
diagnostic tail: Git `cat-file` status 128, a deleted candidate path, and
external-tree whitespace. The contracted suite assigns those classes to
three, one, and one mutations respectively. The former Lean-parser tail route
is retired and a nonempty parser-child diagnostic tail is rejected. The three
remaining exact route prefixes are caller-bound and the tail is canonical
transport evidence only; its operating-system or Git diagnostic truth is not
independently established. A canonical escaped multiline tail is a positive
transport control, not a nineteenth contracted hostile case.

The count history is explicit. The initial 319-case contract grew by ten
success-receipt shapes and one policy-authority mutation for that new family:
`319 + 10 + 1 = 330`. Caller-bound lifecycle added an eleventh success shape;
the initial eight failure-receipt shapes and the policy mutation freezing
their new family then gave `330 + 1 + 8 + 1 = 340`. Whole-template review
reproduced three residual reason-forgery shapes (prefix, suffix, and both),
giving `340 + 3 = 343`. These are review-stage inventory derivations, not
settled-run credit. Canonical JSON-string review added raw-quote, invalid-
escape, and noncanonical-escape cases: `343 + 3 = 346`. Dynamic-field,
empty-tail, and diagnostic-route substitutions first gave
`346 + 3 = 349`. A subsequent branch-adequacy review separated
diagnostic-tail boundary whitespace as an eighteenth case:
`349 + 1 = 350`. The 349-stage and 350-stage contracts received no settled-run
credit. A later direct `validate_c3_local_artifact_parity(...)` checker gate
added its matching top-level checker-model removal case, so `350 + 1 = 351`.
The current 351-stage contract also remains uncredited pending final-byte
replays. This arithmetic explains drift; it does not make the cases
independent or complete.

### Publication regeneration

Only three displayed commands change in the foundational Markdown and TeX
sources, adding `-I -S`; the tool README changes one displayed command and the
wrapper has the same three executable-command changes. Four additional
TeX-only, claim-neutral presentation transforms force two long paths to break
at semantic boundaries and locally reduce the size of two evidence paths and
one three-digest list. They preserve every visible path, digest, prose,
theorem, equation, and numerical byte. A separate fifth TeX change adds a
fresh `\phantomsection` immediately before the unnumbered `Primary sources`
heading. It changes navigation semantics, not visible text or scientific
content.

The navigation change closes a real late review finding. The first independent
16-page visual review was GO for rendering but NO-GO for navigation: both the
page-2 TOC link and the PDF outline entry for `Primary sources` reused
`section.15`, whose page-15 vertical coordinate was 451.245 at
`Reproducibility record`, rather than the lower `Primary sources` heading.
The repaired build assigns `Primary sources` the distinct `section*.13`
destination at page 15, vertical coordinate 199.122, while `section.15`
remains at 451.245. `pdfinfo -dests` and an independent pypdf 6.14.2 outline
traversal agree on the page and coordinates.

The wrapper now runs an isolated standard-library parser that binds the exact
source adjacency, page-15 TOC entry, decoded bookmark title/destination, and
the distinct built-PDF destinations. Its first replay failed closed because the
initial parser incorrectly assumed hyperref encoded every bookmark-title byte
as octal; the actual auxiliary uses a mixture of octal escapes and literal
ASCII. That negative was retained, the parser was corrected to decode both
forms, and the exact wrapper replay then passed. These checks establish the
bounded source/auxiliary/destination relationship; they do not establish PDF
tagging, accessibility, or arbitrary-PDF parser correctness.

That first green wrapper replay was then superseded by independent gate review.
The reviewer showed that hosted `--cross-toolchain` mode could validate only
the newly built destination while an old committed PDF—with identical visible
text and geometry—retained the broken destination. The final gate therefore
checks both the build-derived destination and the exact committed
`section*.13` destination, each against its own distinct `section.15`
record, and requires at least 72 PDF points of vertical
separation. This bound kills a near-identical 450-versus-451 destination but
does not prove either action target or heading semantics for arbitrary PDFs.

The exact embedded parser was also replayed from its wrapper bytes under
isolated normal and optimized Python. In each mode one positive control passed
and eight failure-diverse mutations were rejected: deleted source anchor,
stale TOC destination, duplicated TOC entry, bookmark/TOC mismatch, equal
Primary/Reproducibility vertical coordinates, wrong Primary page, and missing
Reproducibility destination, plus a stale committed-PDF destination that
leaves the built PDF valid. The four PDF-output mutations used a bounded
external `pdfinfo` fixture; this is mutation adequacy for the stated branches,
not authentication of Poppler, completeness, or part of the 351-case phase
inventory.

The PDF was rebuilt with `SOURCE_DATE_EPOCH=1784937600`, `TZ=UTC`, TeX Live
2024, pdfTeX 1.40.26, and Latexmk 4.83. Two same-toolchain builds were
byte-identical. The installed result is PDF 1.5, A4, 16 pages, 358668 bytes,
SHA-256
`ee715576c2e3a8f058747b2d7ed97b99bc42c20c16bf07038e85f4887310553b`.
The TeX source SHA-256 is
`10d1d5123376d8f4ec7363171b6f203ea2e38453d779142eb753364f9a1a33f9`
and the wrapper SHA-256 is
`bf473bf654565b616ec2d73703ace2b7ad1ecfe64d3d4c9879bd427e0fd8d3e4`.
Against the exact parent PDF read from commit
`8b792bc143fff2d84f2d8e7817d1de7850741223` (358292 bytes, SHA-256
`5904626fe91f4d606a09f0b842fcecad102d7585e6654a16e2bbb952ed0882df`),
the `pdftotext -layout` delta consists of the three isolated command changes
plus the deliberate page-11/page-12 path, evidence-path, and digest reflow.
After removal of layout whitespace, both full paths and the complete
Rust-regression digest are byte-identical to the source strings; the former
mid-identifier breaks and orphaned `ed;` continuation are absent. The exact
parent/current extracted-text diff is 4956 bytes, SHA-256
`3f5cc50c77f1714ee65991573f081cfe720cc2d4a2ec0f39521bd2ed976d440d`.

Poppler `pdftoppm` 26.06.0 rendered parent and current files with
`pdftoppm -r 144 -png INPUT.pdf PREFIX`; all four render output streams were
empty. Exact PNG-byte comparison with `cmp` found pages 1--10, 13--14, and 16
equal and pages 11, 12, and 15 different. All sixteen current pages were
visually inspected at 150 dpi, with pages 11 and 12 additionally inspected at
original render resolution. The intended path/digest repairs and page-15
`-I -S` commands fit without clipping, overlap, missing glyphs, or heading
orphans. Bounding-box maxima for the repaired long strings are at most
502.175 pt, inside the ordinary approximately 524.4 pt text edge. All fonts
are embedded, subset, and Unicode-mapped, and the settled build logs contain
no rejected warning, undefined-reference, overfull, or underfull diagnostic.
The repaired and pre-navigation current PDFs have byte-identical
`pdftotext -layout -enc UTF-8` output: 54683 bytes, SHA-256
`851e042522b5532fcb1efd7fe887eecdd6402a27deb981b30964f4fc613fc445`.
The PDF remains untagged, and Poppler's bbox extraction represents nine pairs
of visually correct scalable parentheses on pages 8--10 as C0 bytes `0x12`
and `0x13`; raw bbox XHTML is therefore not a clean accessibility artifact.
This is a same-toolchain and same-rasterizer reproducibility/visual-QA claim,
not a theorem, accessibility claim, or cross-toolchain identity claim.

### Exact command-byte transformations

The four phase commands change in each of CI, AGENTS, and justfile:

```text
python3 scripts/check-ksg-phase-isolation.py
→ python3 -I -S scripts/check-ksg-phase-isolation.py

python3 -O scripts/check-ksg-phase-isolation.py
→ python3 -I -S -O scripts/check-ksg-phase-isolation.py

python3 scripts/check-ksg-phase-isolation-self-test.py
→ python3 -I -S scripts/check-ksg-phase-isolation-self-test.py

python3 -O scripts/check-ksg-phase-isolation-self-test.py
→ python3 -I -S -O scripts/check-ksg-phase-isolation-self-test.py
```

CI appends the exact HEAD tree/checkpoint pair to both checker calls. AGENTS
and justfile instead append
`--diagnostic-without-external-custody` to both local checker calls; those
routes are explicitly `NO-CREDIT`. The foundational wrapper's three
command-byte transformations are exactly:

```text
python3 "$EXACT_CHECKER" ...
→ python3 -I -S "$EXACT_CHECKER" ...

python3 "$LEAN_CHECKER" ...
→ python3 -I -S "$LEAN_CHECKER" ...

python3 "$MUTATION_CHECKER" ...
→ python3 -I -S "$MUTATION_CHECKER" ...
```

The Markdown and TeX audit sources display the corresponding three isolated
commands; the tool README displays the isolated exact-witness command.
Separately, the wrapper adds the isolated Primary-sources navigation gate
described above; it does not alter or replace any exact-rational, Lean,
mutation, LaTeX, text, font, geometry, render, or cross-toolchain gate.
Historical failure logs and receipts retain the unisolated commands actually
executed at C2.

The KSG job timeout is also changed from 45 to 240 minutes. C2 executed 181
phase cases per mode and the whole hosted job took 26 minutes 5 seconds; C3
contracts 351 cases per mode, including costlier exact-source, descriptor,
external-tree, and publication checks. One invalidated local normal replay had
already exceeded 67 minutes. The larger timeout is a bounded execution budget,
not evidence that the suite passed or a weakening of any case.

## Rejected alternative retained as a negative path

An independent review proposed keeping platform-bearing v1 evidence and
teaching only `--cross-toolchain` shell comparison to ignore the platform
substring. That route was not selected. It would give one evidence schema two
comparison meanings and place the portability exception in a second parser at
the wrapper boundary. Within the historical C2 failure receipt, the selected
v2 route instead separated a validated host observation from an explicitly
portable projection, kept the wrapper's byte equality simple, and preserved
both old platform observations and v1 receipt digests.

That historical v2 choice remains true about C2. It is not the final C3
authority: exact-source substitution, parent traversal, private-project
descriptor pinning, Python startup contamination, HOME/Elan selection,
dependency-cache liveness, and
tree/checkpoint self-reference attacks required the expanded nineteen-path/v4
correction documented here.

This is a design judgment, not a theorem. A later system-wide Lean provenance
hardening milestone should share a single strict parser across all Lean
routes, retain optional nonportable observations separately, bind live output
to claim checkers, verify dependency checkout custody consistently, and run
formal jobs on multiple platforms before making an execution-level
cross-platform claim.

## Hostile review of the commit envelope

The first pre-freeze C3 phase gate checked the one-child topology but did not
inspect the raw commit object. Independent temporary fixtures demonstrated two
false-greens: a direct child carrying
`Co-Authored-By: Codex Agent <agent@example.invalid>` and a raw commit carrying
a `gpgsig` header were both accepted. Neither fixture was staged in the C3
worktree/index, entered the real candidate, or was pushed.

An intermediate lexical repair rejected those examples, but a second bounded
partition attack showed why open-ended natural-language recognition was the
wrong object. It still accepted such advertising as
`Generated-With: Claude Code`, `Generated with GitHub Copilot`,
`Authored by an artificial intelligence agent`, and `Tool: Codex`; it also
rejected legitimate non-attribution text about papers authored by AI
researchers, test data generated by an AI benchmark, and the human display
name `Ai Weiwei`. These are retained negative results, not credited proof
mutations.

C3 has only one permitted direct child, so the final gate replaces that
undecidable text-classification problem with a finite object:

- exact UTF-8 commit message
  `fix: harden Lean evidence portability and replay\n`, 49 bytes, SHA-256
  `35c9db2d9db534a6cff91f2581b970fe543d808509214243999d94c9f3b3f8de`;
- exact human author and committer identity
  `Sepehr Mahmoudian <sepmhn@gmail.com>`, with separately validated Git
  timestamps and time zones; and
- an independent raw-header prohibition on `gpgsig` and every `gpgsig-*`
  variant.

The machine-readable policy records the same derivation and fixture boundary;
the phase self-test mutates message, identity, signature, topology, and tree
state separately. This proves conformance of the finite C3 commit envelope,
not a general ability to classify natural-language attribution.

The first full normal aggregate replay after that correction stopped on one
self-test expectation-order mismatch. The deliberate `19` to `18` hostile
parser-inventory mutation was correctly rejected earlier by the exact
parser-output identity check at
`$/lean_version_hostile_cases_rejected`, rather than by the later
count-specific diagnostic the harness expected. The harness now expects that
earliest fail-closed route; no accepted state or gate obligation was weakened.
The interrupted aggregate receives no settled-run credit.
After the later source reseal, a normal aggregate launched as
`python3 -I -S scripts/check-ksg-phase-isolation-self-test.py` in unified-exec
session `86029` stopped on the first Python entry-isolation mutation. The
`phase-checker-isolated-flag-bypass` mutation was rejected by the source-model
guard with
`Python isolation preamble changed: scripts/check-ksg-phase-isolation.py`
where the harness still expected a changed-projection rejection, which cannot
occur for the deliberately self-unhashed checker path.
For that self-unhashed phase-checker mutation, the harness now caller-binds
the exact dynamic detail as the earliest rejection in both the baseline and
rebased legs; blob-bound descriptor-script mutations still require the
changed-projection rejection before rebasing. The mutation and production gate
are unchanged. The run used checker SHA-256
`2359ecade1447da49fd3e809de36191c4f285d1faad65dc084df77a18cae18b8`
and self-test SHA-256
`37c067f931bcbc38e89a281a36a2b7b1c9d2b07f2d86fa065eee093d632337a2`;
those bytes are superseded by this correction, and the run receives no
settled-run credit.
Two later targeted Python-entry-family harness attempts are also retained as
diagnostic-only negatives. The first digest-bound isolated standard-input
loader omitted registration of its dynamically executed module in
`sys.modules`; Python 3.14 `dataclass` processing raised `AttributeError`
before any mutation. The corrected loader in unified-exec session `56566`
completed and restored the first phase-checker mutation, then stopped before
the second mutation because the generic `if not (` delimiter was not unique
in the self-test source: that byte sequence also appeared in the mutation
harness itself. The mutation constructor now uses the exact unique
`import sys as _bootstrap_sys` through `del _bootstrap_sys` preamble bounds,
whose uniqueness is checked before replacement. Both attempts used checker
SHA-256
`b337be07077b9567ea313b428f76aaec38d2481d94336d2b894bef90eebf5375`
and self-test SHA-256
`2c5e22ff98aafcbbec8e4ab219057058d95a470a1a6472387c067a9e457b666b`;
neither is a full-suite, mutation-family, or source-custody credit.
A third targeted attempt in unified-exec session `3174`, after the delimiter
repair, completed and restored all four preamble mutations, then stopped at
the first child-command mutation. The source-model guard correctly reported
`child Python command lacks exact -I -S prefix:
scripts/check-ksg-phase-isolation.py`, while the harness still expected a
changed projection that cannot cover the self-unhashed checker. The two
self-unhashed child-command cases now caller-bind their exact dynamic semantic
detail on both legs; the five self-unhashed checker bootstrap/materialization
cases bind their constant semantic rejection on both legs. That run used
checker SHA-256
`67c5598284712b46df5d7c705f0474b282b672c8a40b40b96b21afcc25ce068d`
and self-test SHA-256
`3fde8666956ec4cca29987e461a7362560dff9e87b927277b413dea1832b4ebd`;
it receives no complete-family or settled-run credit.
Before another execution, two independent static reviews found that the
rebased foundational-wrapper mutation still expected its later PDF-transform
diagnostic even though the earlier official-invocation guard consumes that
mutation. The harness now caller-binds
`official isolated Python invocation changed:
scripts/check-foundational-sxpid-audit-pdf.sh`; no execution was credited and
neither production guard was removed or reordered.
A fourth targeted attempt in unified-exec session `27678` completed and
restored the first sixteen entry-family mutations, then stopped on the
seventeenth, the foundational tool-README invocation. Removing `-I -S` from
that file recreates its exact anchor bytes, so the path leaves the A/M delta
and the checker correctly reports
`candidate anchor delta differs from the separately reviewed A/M path policy`
rather than a projection mismatch. An independent in-memory replacement
against the exact anchor blob confirmed that equality and confirmed that the
other six official-surface mutations remain different from their anchor
blobs. The tool-README case now binds the A/M rejection before rebasing and
the exact path-bound official-invocation rejection afterward; the other six
retain projection-first then semantic ordering. That run used checker
SHA-256
`2714d37d374eb94f54cd0c358f633ec6e7fa29a8ed9d7a40befa015c3915c655`
and self-test SHA-256
`674642ab33e838babc1f8e2f86716590f86a85318e3c29b52acfdd65c31698d1`;
it receives no complete-family or settled-run credit.
Independent static review then showed that correcting only the first expected
receipt was insufficient: current-fact emission enforces the same A/M equality
and therefore could not rebase an anchor-restored path for the semantic leg.
Before the first checker receipt, a guard limited to the one exact
tool-README path and exact A/M reason loads the exact anchor blob and requires
the mutated bytes to equal it. Only after the exact A/M rejection does the
downstream seam replace `actual_delta == policy_delta` before mechanical fact
rebasing.
The rebased leg must still reach the exact official-invocation rejection and
restore both source files. This seam cannot make the initial mutation pass and
is not a production exception. No execution was credited for the static
finding.
A fifth targeted attempt in unified-exec session `56745` then completed all
18 Python entry-isolation mutations and asserted byte-exact restoration of
both sources. Its terminal line bound checker SHA-256
`cbb08b17ff09c967a6ac9e49ba071b279e22fb903fe1a75b501973b779edebc8`
and self-test SHA-256
`0cfd0480721ddce0df533b97ec28082a94202c2a67fd9c0121382466904ebaec`.
This is a complete targeted-family diagnostic on those bytes, not a full
350-case run, optimized-mode replay, final committed-tree custody result,
independent implementation, or scientific/security claim.
A fresh full normal aggregate in unified-exec session `62196`, launched as
`python3 -I -S scripts/check-ksg-phase-isolation-self-test.py`, later stopped
at `portability-receipt-duplicate-key`. After the first projection rejection
and receipt/memo digest rebind, mechanical fact emission rejected the stale
policy cross-binding. The rejection message was
`phase path policy historical remediation supersession value changed at`
`$/historical_receipt_sha256`. The run used checker SHA-256
`0151ff6813ed359ec850df2c83dc1f21ceebb485d9f8291262b2e7f5f5e5faf5`
and self-test SHA-256
`0cfd0480721ddce0df533b97ec28082a94202c2a67fd9c0121382466904ebaec`;
it receives no settled-run or partial-family credit.

The portability-receipt semantic helper now saves the policy, requires the
first uncoordinated projection rejection, rebinds the receipt digest in the
memo, checker, and policy, rebinds the resulting policy and memo digests in
the checker, and only then mechanically rebases for the parser/typed-value
semantic rejection. Same-length digest replacement preserves canonical policy
JSON; an independent in-memory duplicate-key mutation and exact re-encoding
check confirmed that route. The receipt, memo, policy, and checker are all
restored in `finally`, followed by a green baseline replay. This downstream
coordinated-rebind seam tests the semantic layer only; it does not weaken the
initial custody rejection or make coordinated mutation acceptable.
A targeted replay in unified-exec session `84056` then completed all 34
public-CI-portability evidence mutations and asserted byte-exact restoration
of the receipt, memo, policy, checker, and self-test. Its terminal hashes were
receipt `73c8b509304f0a23382f531d9b94511c58f14f1e5a75ef1147d8cbb80bf02a20`,
memo `9a4ec4b7ee663875039fbd996e48732cdae5c1f56592eb9d15ed627ba41b58ca`,
policy `2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3`,
checker `4ccb393e1089faf2f747c8469bc642b00e2323f7e4fd17dc976b1d90289b65c8`,
and self-test
`f2464399e6a497e2fcf1924e63c26c1016f2b49f06cc3392ae7666d8dd7fbad9`.
This is targeted-family diagnostic evidence only, not a full 350-case or
optimized replay, external-tree result, authenticity proof, or C3 closure.
An alternate-index tree
`fbcc8b68cf04caa44555313eb2ecda252a47a7e5` and unsigned local checkpoint
`ffbd24e668a57e8c8c20714998aa27c27085b3c2`, synthesized before this last
writer update, were explicitly invalidated and never pushed; they receive no
tree-custody or commit credit.

A later clean committed-tree replay exposed a second precredit failure:
`git diff --check` on tree
`229e24f3614b9e7fdd28d90cc291c6e6be2ce5f2` and unsigned checkpoint
`7e2812bd6d0b14234325b3ecd065017bec487d2a` rejected two trailing spaces in
this newly added memo. The earlier dirty-worktree invocation had not inspected
the then-untracked file. That tree and checkpoint were invalidated and never
pushed. Final custody now requires a clean committed-tree or equivalent
candidate-tree whitespace check that includes additions; a worktree-only
tracked diff is insufficient.

A later full normal phase-isolation aggregate, launched as
`python3 scripts/check-ksg-phase-isolation-self-test.py` in unified-exec
session `55661` with parent PID `92493`, receives no credit because an
external progress probe exposed its active custody clone to an unauthorized
in-clone operation; the replay is therefore treated as contaminated and
receives no credit. The probe invoked
`git -C /var/folders/5w/54mv55g13yq4x_7w3ld2csb40000gn/T/pid-rs-ksg-phase-self-test.rwuan5k5/candidate status --short`.
Git status may refresh an index or repository metadata. The checker then
failed closed with the exact diagnostic:

```text
ERROR: KSG phase-isolation self-test: unmodified phase checker did not pass:
ERROR: KSG phase isolation: Git executable, configuration, metadata, or visibility context changed during replay
```

The last exact pre-failure process sample recorded elapsed time `01:07:26`;
the exact terminal elapsed time was not captured and is not reconstructed.
The evidence does not identify a particular changed byte or metadata field,
and no such claim is made. The prevention rule is stricter than the failed
probe: never invoke Git or inspect filesystem metadata inside an active
custody temporary clone. Monitor only process IDs and process state from
outside the clone, for example with process-level `ps`. Any replay exposed to
an in-clone probe is invalidated and receives no settled-run credit.

The concurrently running optimized aggregate in unified-exec session `74678`
with parent PID `22724` also receives no credit, regardless of its terminal
result. It started on the prior policy/memo snapshot, and the writer updates
that recorded the normal-run contamination invalidated those input bytes
before the optimized run settled. Its exact terminal time and result were not
observed before invalidation. It was then deliberately stopped with `SIGINT`
and exited `130` with `KeyboardInterrupt` while executing
`run_public_ci_portability_evidence_attacks`. That controlled stop is neither
a checker failure nor a passed subpartition. Its exact terminal wall time was
not captured and is not reconstructed.

A fresh isolated normal aggregate in unified-exec session `54874`, launched
with `python3 -I -S scripts/check-ksg-phase-isolation-self-test.py`, exited
`1` at `portability-receipt-duplicate-key` and receives no aggregate,
partial-family, or restoration-replay credit. The terminal diagnostic
contained `mutation anchor count is not 2` for this memo. The run used memo SHA-256
`6da138c09e79191d565e9092dc6429561095da82899d5b567e82fabceb83b12f`,
checker SHA-256
`741a2ceb0f7924784a8b24005c065d0d0b8f42142c9e49a99008c6d9d6ac0ab8`,
and self-test SHA-256
`f2464399e6a497e2fcf1924e63c26c1016f2b49f06cc3392ae7666d8dd7fbad9`.
Independent post-failure inspection found all nineteen source paths restored,
the disposable candidate removed, and no new ordinary phase-checker bytecode
cache. That inspection is restoration evidence only: the exception occurred
before the helper's post-`finally` green replay.

The failure exposed a stale global-cardinality assumption, not a parser or
receipt result. The receipt digest has two live semantic bindings in this
memo—the canonical citation and the delimited parity field—and one immutable
historical observation of targeted session `84056`. Rewriting all three
during a synthetic receipt mutation would falsify retained run history. The
coordinated-rebind helper now uses unique contextual boundaries for the two
live memo fields, the checker constant and exact blob-map entry, and the
policy field; it separately requires the historical observation to remain
byte-exact. An independent pre-execution static review rejected the first
draft because `PHASE_PATH_POLICY_SHA256` was also a suffix of
`PRIOR_PHASE_PATH_POLICY_SHA256`; that draft was never executed and receives
no mutation credit. The corrected marker includes its leading line delimiter,
which is unique in the reviewed checker source. The first uncoordinated
projection rejection and final exact semantic rejection remain mandatory.
This correction is uncredited until fresh complete normal and optimized
aggregates pass on one later sealed source state.

A first bounded-family launcher in unified-exec session `51446` exited before
creating its disposable clone because the recorder requested nonexistent
module attribute `SELF_TEST_RELATIVE`; the reviewed constant is
`SELF_RELATIVE`. The loader had completed its static preflight and current-fact
read, but no hostile family, candidate restoration, or post-run checker was
executed. The invocation used `python3 -B -I -S -`, wrote no ordinary
phase-checker bytecode cache, and receives no targeted-family or partial credit.
A corrected launcher must run only after this negative is recorded and the
resulting source bytes are resealed.

The corrected bounded launcher in unified-exec session `97473` then completed
all `34/34` public-CI-portability evidence cases on memo SHA-256
`ca4c6c29fecbbb2c53fb6366cf9122008e8db16aba1018645b936d6b94508025`,
checker SHA-256
`b09c842b0c2ac2eb29087ff2581a2a384f28702b14cbbbc0331775c7fbc16cc6`,
and self-test SHA-256
`f76c79cd4ea86ff6012c30f6f92d473f04dd0c88a475499cb86e01ada84b2e1c`.
It directly compiled captured self-test source under `python3 -B -I -S -`,
cross-checked the observed count against the canonical policy, obtained
byte-identical baseline/final no-credit checker receipts, restored five
candidate targets by existence/bytes/mode/status, removed the disposable
no-local clone, and found the source's complete 187-path overlay plus scrubbed
Git status unchanged. This is targeted-family diagnostic evidence on the
stated prior bytes only. Recording it changes this memo, invalidates those
bytes as final C3 inputs, and supplies no full-350, optimized, external-tree,
scientific, hosted-CI, security, authenticity, or closure credit.

A subsequent complete normal aggregate was launched in unified-exec session
`8070` as
`python3 -I -S scripts/check-ksg-phase-isolation-self-test.py` on policy
SHA-256
`2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3`,
memo SHA-256
`42541915305928006faa54facd5d7964f7e8e074e5819d97dcc78e60a10c3406`,
checker SHA-256
`b6648e836cb9fea805c2f7892107c4abc790db092e2df7b9ab242c58366e6fa8`,
and self-test SHA-256
`f76c79cd4ea86ff6012c30f6f92d473f04dd0c88a475499cb86e01ada84b2e1c`.
The execution remained silent while its PTY was polled without repository or
candidate probes. At the 2026-07-30 continuation boundary the PTY handle was
no longer available, and a process-table-only query found no matching
self-test process. No terminal stdout, stderr, return code, or exact elapsed
time was recovered, so the observation cannot distinguish success, failure,
or external termination. It receives no full-run, subfamily, restoration, or
optimized credit.

Post-observation source inspection found the four stated hashes, exact
sixteen-modified/three-added worktree status, clean textual diff, and absence
of ordinary phase-checker bytecode unchanged. Those facts establish source
preservation only; they do not recover the missing terminal receipt or prove
disposable-candidate cleanup. Future long aggregates require an external,
separate-channel durable stdout/stderr/return-code capture outside the
repository, with the exact child command and source seal still checked.

A later final-tuple review rejected candidate tree
`601f2681bdd88673e658d1b9a6e96de1936c8215` and unsigned checkpoint
`266760007b59642a6b9e12ad47ce0dffda54be26` before either official one-shot
run. Two independently constructed fresh indexes agreed on that tree, but an
earlier cache-info construction had hard-coded mode `100644` and produced
rejected tree `f306fd04b0c2ac19ed06f513ed0e183af4fe688f` by stripping the
executable bit from three verifier scripts. The same failed launcher treated
the expected zero-match signature-header search as fatal under `set -e`.
Neither the mode-corrupted tree nor the unidentified, unreported commit object
from that stopped launcher receives custody credit.

The exact final-tuple review then ran the sealed phase self-test through the
pinned CPython 3.14.6 interpreter, finite environment, and exact worktree
command in normal and optimized modes. Both runs exited `1`, emitted empty
stdout, and emitted the same 423-byte stderr with SHA-256
`04f4450c545184139f7b3cdbfd1a8cbd7832f7285262f39a0ef13a1b2ac3d5c0`:

```text
ERROR: KSG phase-isolation self-test: lean-portability-self-test-hostile-inventory-reduced: phase checker rejected a mutation for the wrong reason; missing 'Lean portability parser replay identity value changed at $/lean_version_hostile_cases_rejected' in 'normal Lean portability parser controls failed: Lean descriptor-factorization self-test failed: Lean version positive/hostile probe hashes are not pairwise distinct'
```

The failure is deterministic rather than a parallel-run artifact. The mutant
removed one hostile Lean-version probe and changed its local inventory
assertion from `19` to `18`, but left the pairwise-distinct probe-hash
cardinality at `21`. The resulting two positive controls plus eighteen hostile
probes therefore failed the stale `21` assertion before the intended outer
replay-identity firewall. The two component reviews of the frozen supervisor
and verifier were green, but correlated component evidence cannot override
this end-to-end counterexample. An official launch would have produced child
exit `1`, a captured no-credit monitor receipt, supervisor exit `1`, and
verifier rejection while consuming the one-shot directory names. All four
official `final-003` directories remained absent, and no production monitor,
supervisor, or verifier main ran.

The correction changes only that coordinated hostile mutation: alongside the
case removal and `19` to `18` inventory change, it changes the mutant's
pairwise-distinct cardinality from `21` to `20`. A first bounded launcher for
the corrected source again omitted a `sys.modules` registration and stopped
in CPython 3.14 dataclass processing before cloning a candidate or executing
an attack; it receives no credit. Corrected bounded launchers registered an
explicit temporary module, ran all `17/17` Lean-portability attacks in normal
and optimized modes, obtained green baseline and final checker receipts, and
removed their disposable candidates. Those targeted runs used policy
SHA-256
`2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3`,
memo SHA-256
`3984f9438f9b1560db826b03d005d363f94fe619cbff1c290cbe52750f361dc3`,
checker SHA-256
`710a6124b23ec08bfb492d1c0fbdd1a4ce2d0a5744bccc7dfaa7ac7b51738fd4`,
and corrected self-test SHA-256
`a4d5152f752c8773f9fbceea0d4737a60a22a67696423a9cd709a0fec2c9e120`.
They establish the bounded failure-ordering correction only. Recording this
episode changes the memo again; fresh normal and optimized full aggregates,
external custody, candidate-tree, clean-tree, and hosted evidence remain
mandatory.

A subsequent v4 review cycle bound monitor
`5d093695331e1965c9855f22b5cc26da1ca5820ae0c5c53a78029935c7aa1aa0`,
supervisor
`498372124947ef06c1d4661b8bf0405d1fcfbb9014448e6dcd300b8fadbf6811`,
and verifier
`e8e1df74b4c17d665a202ad00a778c2e19a7c011017d1c6fe4231a46eab41576`
to candidate tree `eac26211c4d76989253ce78ae2e4936d370932e1` and unsigned
checkpoint `f0515e455d969eafe9a4f260f50341b0a120dc73`. The direct checker
accepted that tree/checkpoint in normal and optimized modes with byte-identical
645-byte stdout, SHA-256
`a5e0e7644066968be42a1ee502c3d52fd1338680fcda13390ff41c129fee29c7`,
and empty stderr. Independent component reviews covered forty-seven
monitor/supervisor and forty-six verifier lenses and returned bounded launch
GO. Those results cannot substitute for the full phase self-test.

A preliminary full-suite setup accidentally changed disposable clone files to
mode `0600`; the checker rejected immediately, no hostile case ran, and those
clones were discarded before the adjudicative runs. Two later pristine
normal and optimized custody runs passed the corrected Lean-portability
section but both exited `1` at a later rebased-semantic attack. Each emitted
empty stdout and the same 304-byte stderr, SHA-256
`7e5863cc8c11510e700af440b487b83e712b3d5ed9740677877e0998838ede2d`:

```text
ERROR: KSG phase-isolation self-test: foundational-paper-lake-preflight-removal: phase checker rejected a mutation for the wrong reason; missing 'differs from the exact lake-preflight transform' in 'authorized text path differs outside finite C2 transform: scripts/check-foundational-sxpid-audit-pdf.sh'
```

The failure is again deterministic and premise-ordering-specific. The mutant
removed `lake` from the foundational wrapper preflight and expected the later
`validate_foundational_pdf_lake_preflight` diagnostic, but the unchanged
critical sequence first ran `validate_python_entry_isolation`, whose exact
finite-C2 transform rejected the wrapper bytes. No full-suite, hostile-family,
or partial credit follows. The reviewer observed both actual outer exits,
restored every source/status seal, removed all disposable roots, and found all
four official `final-004` directories absent. No production external main ran.

The correction leaves the production checker and gate order unchanged. Only
the synthetic downstream mutation is coordinated: its private checker model
adds the same lake-removal transform to the earlier exact finite-C2 wrapper
projection, so that earlier validator accepts precisely the intended mutant;
the independent, unchanged lake-preflight validator must then reject it.
Targeted normal and optimized replays reached that exact validator, obtained
green baseline and final checker receipts, and removed their disposable
candidates. They used policy SHA-256
`2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3`,
memo SHA-256
`facb2ddaef514536215d9f1e747a1885534ff696bf6ed18145a991b2db4783b6`,
checker SHA-256
`919d1d778d7e805bf1b515ee5f95d21026ce873695d25ac194d2a1d19a084fc5`,
and corrected self-test SHA-256
`015203dc260a6b845ee0ed11eb5a0edb4a22b9d7c337bde5f3f4072d2550aaa9`.
This is bounded failure-order evidence only. Recording it invalidates the v4
memo/checker/external seals; another complete reseal and full normal/optimized
review remains mandatory.

## Local Lean routing negatives retained

An initial local `/usr/bin/time lake env lean --version` attempt did not
produce a version line and was terminated after `2521.35` seconds. A separate
orphaned `lake --version` process, PID `59119`, held the Elan toolchain lock
and was deliberately terminated. Invoking the descriptor checker with
`--help` is not a help-only path: the script began its ordinary environment
verification, blocked in the same Lake route, and was interrupted. No output
from any of these attempts is theorem or executable-identity evidence.

A subsequent Elan-managed installation attempt downloaded the 524.6 MiB Lean
4.32.0 Darwin arm64 release at roughly 50--100 KiB/s and was deliberately
stopped near 75 MiB rather than waiting several additional hours. This is an
operational routing/throughput negative, not a Lean failure.

The replacement route fetched the official Lean v4.32.0 GitHub release asset
`lean-4.32.0-darwin_aarch64.tar.zst` in independently ranged segments. The
release API reported 550037866 bytes, update time
`2026-07-13T12:13:22Z`, and SHA-256
`4faa4757f7ca5e7d9588a9de779550fa58bdf01498edb966f15029e2ea117e4e`.
The assembled archive had exactly that size and digest, and `zstd -t`
accepted its 2802083840-byte decompressed stream. Before the transient archive
was deleted, a streaming comparison covered every archive entry: 607
directories and 14671 regular files, no symbolic links, hard links, or other
entry types, with regular-file bytes, sizes, and modes equal and no extra
extracted entries. Twelve archived empty source directories absent from the
initial extraction were created with mode 0755; the normalized entry-set diff
then became empty. A local review also recorded
`a1b2864665d2925564e7d797fe9af4127c729e852fc3398b56edc62d28a908c3`
for an ad hoc normalized archive-tree projection. Its exact encoder, record
schema, and projected bytes were not retained, so that digest is opaque,
independently unreproducible, and receives no custody credit. The independent
stream-versus-tree comparison above does not validate that opaque digest.

The retained extracted binaries report:

```text
Lean (version 4.32.0, arm64-apple-darwin24.6.0, commit 8c9756b28d64dab099da31a4c09229a9e6a2ef35, Release)
Lake version 5.0.0-src+8c9756b (Lean version 4.32.0)
```

These are host-specific integrity and process observations for the selected
release bytes. They do not authenticate GitHub, the transport, the Lean
compiler, Lake, Mathlib, cached oleans, or the operating system; they do not
prove source-to-binary correspondence or cross-platform equivalence. The
archive checks do not receive theorem or C3 closure credit until the
final-byte checker and mutation replays settle and their receipts pass
independent custody.

## CodeQL execution and security boundary

CodeQL run `30431351202` completed successfully: four of four jobs and forty
of forty steps succeeded. Exact decoded REST log hashes are retained in the
machine receipt.

Execution success is not scan cleanliness. At `2026-07-29T08:04:23Z`, the
repository API exposed `85` open alerts projected on the C2 commit: `19`
Python and `66` Rust, comprising `19` critical and `66` high-severity alert
records. Their creation timestamps range from July 15 through July 27, before
this run. That chronology shows that the alert records predate C2; it neither
proves when an underlying defect entered nor adjudicates an alert as real or
false positive. Security remains open release debt. C3 does not adjudicate or
dismiss any alert and makes no intentional security-remediation or
scan-cleanliness claim. Because C3 changes verifier code, incidental alert
resolution or new alerts cannot be inferred before the hosted C3 scan.

## Retained local pre-seal no-credit incidents

Two local review-process incidents are retained rather than silently erased.
First, a syntax audit wrote or refreshed these six ignored CPython 3.14 cache
files:

```text
scripts/__pycache__/check-lean-descriptor-factorization.cpython-314.pyc
scripts/__pycache__/check-lean-descriptor-factorization-self-test.cpython-314.pyc
scripts/__pycache__/check-certified-sxpid2-claim.cpython-314.pyc
audit/tools/foundational_sxpid/__pycache__/check_lcr_relation_witness.cpython-314.pyc
scripts/__pycache__/check-ksg-phase-isolation.cpython-314.pyc
scripts/__pycache__/check-ksg-phase-isolation-self-test.cpython-314.pyc
```

Each exact path was verified ignored and present, then removed. Pre-existing
optimized caches were not deleted. A later `py_compile` audit recreated the
two phase-checker caches; both exact ignored paths were verified and removed a
second time before final source custody, while the pre-existing optimized
caches remained untouched. Ignored caches are outside the candidate snapshot,
but any import-contamination observation before the final removal receives no
credit.

Second, an intended recorder-only audit accidentally entered the first
prior-public-CI receipt attack and the first portability-receipt attack. Their
`finally` blocks restored the backed-up raw bytes and modes for the prior
receipt, prior correction memo, portability receipt, this memo, and phase
checker; both stopped on the already stale policy digest. File mtimes changed,
so every concurrent custody observation is invalidated even though no credited
phase, descriptor, or publication run overlapped the incident. All final hashes,
external-tree custody, and clean replays must be obtained after these incidents
and after writers stop.

## Failure-diverse verification lenses

Each lens requires three passes: design/premise inspection, hostile execution,
and settled clean-tree custody. Until the final-byte runs settle, this table is
the review contract rather than a claim that the third pass has completed. A
pass in one row cannot substitute for another row.

| # | Lens | Evidence and attack | Explicit boundary |
|---:|---|---|---|
| 1 | Premise and object typing | Process observation, portable projection, kernel result, receipt, PDF, Git object, and hosted job are distinct types | No unstated premise or cross-object promotion |
| 2 | Independent derivation | Historical control-flow diagnosis, strict parser derivation, exact-rational route, Rust witness, and Lean route | Shared inputs/dependencies are named and not counted as independent |
| 3 | Counterexamples | Swap/use/restore, live cache, ordinary-startup side effects, Lyu collision, and finite semantic countermodels | Each falsifies only its stated stronger claim |
| 4 | Formal proof | Three Lean theorems replay with empty axiom inventories and exact theorem source | No concrete SxPID binding or kernel authenticity follows |
| 5 | Certificate/serialization | Compact sorted v4 JSON, strict shapes/types/counts, normal/optimized byte equality | Receipt equality is not binary or semantic universality |
| 6 | Mutation adequacy | Three proof mutants, 45 distinct descriptor probe records, 351 typed phase cases, and separately typed controls | Enumeration is not completeness, independence, or security coverage |
| 7 | Property/metamorphic checks | Cross-platform parser identity, normal/optimized invariance, replay equality, and finite tree/path transformations | Tested metamorphisms do not imply arbitrary transformation invariance |
| 8 | Compiled production path | Historical hosted KSG and certified compiled jobs plus unchanged production-source pins | A C2 subjob success is not a C3 whole-run or unrelated-estimator result |
| 9 | Binary64/numerical freeze | Scientific Rust/Python bytes, numerical fixtures, estimands, and output-bearing paths are frozen | C3 supplies no new accuracy, stability, or floating-point theorem |
| 10 | Exact-source loading | `-I -S`, stdin bootstrap, digest-before-compile, unchecked-pyc negative, lexical-root post-digest race control | Does not authenticate Python/source provenance; all directly path-invoked entries and already-running bootstraps remain premise-bound, while only explicit nested routes bind source before execution |
| 11 | Cache/import contamination | Hostile cwd/path/home/startup hooks, private checker copy, retained HOME-to-launcher negative, independently observed Homebrew/Elan routing, and live dependency-cache negative | Mathlib checkout/oleans, HOME-influenced launcher state, and non-prefixed ambient state remain live; the generic fixture does not authenticate or emulate Elan |
| 12 | Race/TOCTOU | POSIX descriptor traversal, descriptor-pinned child CWD, relative queries, double reads, FD-cleanup regression, parent/leaf/link attacks, whole-project containment, and retained generic/query-subtree swap/use/restore negatives | Endpoint replay is not atomic history; the project FD does not pin its query child, the explicitly passed project FD remains inherited by the child/descendants, and no route covers a concurrent privileged/same-UID writer |
| 13 | Git/tree custody | Exact parent, nineteen-path A/M policy, alternate indexes, external tree/checkpoint pair, clean replay | Post-hoc self-consistency is not an external trust anchor |
| 14 | Identity/attribution | Exact human author/committer/message plus raw `gpgsig*` rejection and false-positive/false-negative fixtures | Finite C3 conformance is not general natural-language attribution detection |
| 15 | Platform portability | macOS/Linux parser shapes; POSIX full-custody gate; hosted Ubuntu rerun required | Native Windows custody and cross-platform kernel equivalence are unsupported |
| 16 | Reproducibility | Stable inputs, private queries/configs, normal/optimized receipts, two byte-identical PDF builds | Same-toolchain reproducibility is not hermeticity; input/output sizes are uncapped and direct-child timeout does not clean up descendants |
| 17 | Publication rendering and navigation | Source/text diff, 16 rendered pages, page-15 visual inspection, source/TOC/bookmark plus built/committed PDF-destination association with a 72-point bound, independent outline traversal, geometry, fonts, warning firewall | Named destinations and trusted hyperref auxiliaries are not a general PDF-action proof; PDF is untagged; Poppler bbox extraction retains 18 C0 parenthesis controls; no accessibility certification or transfer to the other PDFs |
| 18 | Literature/novelty/mapping | Method catalog, scientific prose, citations, theorem source, and estimand routes are frozen | No novelty claim and no transfer among KSG, Ehrlich PID, MGW SxPID, I_min, quantized PID, heuristics, or wrappers |
| 19 | Security scanning | Exact C2 CodeQL execution receipt and alert projection; no alert dismissal or intentional security-remediation claim in C3 | The 85-alert C2/API snapshot remains unadjudicated; C3 alert status awaits hosted scan, scan execution is not cleanliness, and no C3 SBOM result is claimed |
| 20 | Release/downstream authority | Exact no-release/no-integration status and a required all-green hosted C3 run after push | C3 cannot self-certify its push-triggered run or authorize later milestones |

## Canonical historical C2 failure-receipt human/machine parity projection

The following JSON is a strict projection of the historical C2 machine receipt,
not a statement that the current C3 workflow is unchanged. The sentinels are
part of the checked contract.

```text
PUBLIC_CI_PORTABILITY_FAILURE_PARITY_BEGIN
{
  "certified_job": {
    "conclusion": "success",
    "id": 90509073386,
    "restored_step_numbers": [
      21,
      22,
      23,
      24,
      25,
      49
    ]
  },
  "codeql": {
    "execution": {
      "conclusion": "success",
      "job_success_count": 4,
      "job_total_count": 4,
      "run_id": 30431351202
    },
    "open_alert_snapshot": {
      "critical": 19,
      "high": 66,
      "open_count": 85,
      "python": 19,
      "rust": 66,
      "scan_clean": false,
      "security_adjudication": "not_adjudicated"
    }
  },
  "failure": {
    "classification": "evidence_portability",
    "exact_error": "foundational shared-exclusions PID audit PDF check: Lean factorization evidence is stale or not reproducible",
    "job_id": 90509073390,
    "kernel_failure": false,
    "log_sha256": "06c612a30cd02dc9f9a3957b47cdf96cd2d2e75ff08cf050272bcb518d49b234",
    "log_size_bytes": 58025,
    "scientific_counterexample": false,
    "step_number": 8,
    "theorem_failure": false,
    "tool_provisioning_failure": false
  },
  "head": {
    "commit": "8b792bc143fff2d84f2d8e7817d1de7850741223",
    "tree": "8e247b9a6c46fd6266fe4fc02fbe9c3142268215"
  },
  "integration_disposition": "NO-GO pending a fresh complete public rerun",
  "job_counts": {
    "failed": 1,
    "success": 44,
    "total": 45
  },
  "ksg_job": {
    "conclusion": "success",
    "id": 90509073372
  },
  "receipt_path": "audit/evidence/ksg-rev4-public-ci-run-30431352389-failure.json",
  "receipt_sha256": "73c8b509304f0a23382f531d9b94511c58f14f1e5a75ef1147d8cbb80bf02a20",
  "remediation": {
    "scientific_claims_changed": false,
    "settled_full_ci": false,
    "whole_run_rerun_required": true,
    "workflow_changed": false
  },
  "run": {
    "attempt": 1,
    "conclusion": "failure",
    "id": 30431352389,
    "number": 147,
    "status": "completed"
  },
  "schema": "pid-rs/public-ci-portability-failure-human-parity",
  "schema_revision": 1
}
PUBLIC_CI_PORTABILITY_FAILURE_PARITY_END
```

## Independent precommit review ledger

This schema-revision-2 ledger is the canonical structured inventory for C3 precommit review. It
records exactly **18 bounded positive observations** and **46 negative observations**: **64 rows**
in total. The positive bucket distinguishes superseded bounded execution evidence from bounded
design-only review; neither class is active candidate credit. The negative bucket distinguishes
repository verifier/custody/publication defects, reviewer/tool/process negatives, candidate
supersessions, and a falsified review hypothesis. Historical C2 parity, artifact parity, and
external-v8 status remain separate obligations and are not silently promoted into this ledger.

Every row has exactly one narrative marker below. Each marker states only the row's typed event
class and credit disposition; omitted facts are not inferred.

### Canonical event narrative index

#### Bounded positive observations

- [C3 event: GEN0_PARSER_NORMAL_OPTIMIZED_BYTE_IDENTICAL] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN3_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN4_ROOT_FOCUSED_NORMAL_OPTIMIZED_34_CASES] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN4_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN4_STANDARD_AND_RAW_ALTERNATE_INDEX_TREE_EQUAL] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_56745_ENTRY_ISOLATION_18_CASES_COMPLETE] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_84056_PUBLIC_CI_PORTABILITY_34_CASES_COMPLETE] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_97473_PUBLIC_CI_PORTABILITY_34_CASES_COMPLETE] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: FINAL003_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: FINAL003_LEAN_PORTABILITY_NORMAL_OPTIMIZED_17_CASES] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: FINAL004_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: FINAL004_COMPONENT_REVIEWS_BOUNDED_GO] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: FINAL004_TARGETED_LAKE_PREFLIGHT_NORMAL_OPTIMIZED] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN0_FULL_NORMAL_OPTIMIZED_350_CASES_COMPLETE] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN0_THREE_ALTERNATE_INDEX_RECONSTRUCTIONS_EQUAL] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN0_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN1_DIRECT_NORMAL_OPTIMIZED_ACCEPTED] Typed as `superseded_bounded_positive` with credit `superseded_bounded_only`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: RAW_TRANSPORT_FIVE_FAMILY_STATIC_DESIGN_GO] Typed as `bounded_design_positive_no_runtime_credit` with credit `bounded_design_only`; no facts beyond the corresponding ledger row are asserted here.

#### Negative observations

- [C3 event: GEN0_FALSE_PARSER_DIGEST_AND_ABSENT_FULL_STDOUT_BINDING] Typed as `repository_custody_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN1_FAILURE_ORACLE_INVENTORY_NOT_RESEALED] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN2_TOP_LEVEL_MEMO_PIN_STALE_AFTER_BLOB_REPIN] Typed as `repository_custody_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN3_CORRELATED_MEMO_INVENTORY_MUTANT_INADEQUATE] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN3_NORMAL_FULL_SUITE_CONTROLLED_STOP_AFTER_REJECTION] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN3_OPTIMIZED_FULL_SUITE_CONTROLLED_STOP_AFTER_REJECTION] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN4_INDEPENDENT_OPTIMIZED_FOCUSED_RUN_ABORTED_FOR_SERIALIZATION] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN4_ROOT_NORMAL_FULL_SUITE_OVERLAPPED_FOCUSED_REVIEW] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN3_CONCURRENT_PDF_LEAN_VERSION_TIMEOUT_NO_CREDIT] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN1_PREDICTABLE_BSD_MKTEMP_TEMPLATE_REJECTED] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN1_RUFF_MECHANICAL_REFLOW_RESTORED_BEFORE_CANDIDATE] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: V8_REVIEW_TRACKED_RESUME_APPEND_RESTORED_BEFORE_CANDIDATE] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: PRE_OBJECT_REVIEW_LEDGER_NONCANONICAL_PRETTY_JSON] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_86029_ENTRY_ISOLATION_EXPECTATION_ORDER] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_56566_ENTRY_MUTATION_DELIMITER_AMBIGUOUS] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_3174_CHILD_COMMAND_EXPECTATION_ORDER] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_27678_TOOL_README_ANCHOR_ORDER] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_62196_PORTABILITY_DUPLICATE_KEY_STALE_POLICY] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_55661_CONTAMINATED_BY_IN_CLONE_GIT_PROBE] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_74678_PRIOR_SNAPSHOT_INVALIDATED_AND_STOPPED] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_54874_MEMO_ANCHOR_CARDINALITY_STALE] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_51446_WRONG_SELF_TEST_ATTRIBUTE] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: SESSION_8070_TERMINAL_RECEIPT_UNRECOVERED] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: TREE_FBCC_CHECKPOINT_FFBD_INVALIDATED_AFTER_WRITER] Typed as `candidate_supersession` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: TREE_229E_CHECKPOINT_7E_TRAILING_WHITESPACE] Typed as `candidate_supersession` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: TREE_6F6E_CHECKPOINT_C896_CHANGED_PROJECTION_STALE] Typed as `candidate_supersession` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: TREE_F306_EXECUTABLE_MODES_STRIPPED] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: FINAL003_SELFTEST_WRONG_REASON] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: FINAL004_PRELIMINARY_CLONE_MODES_0600] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: FINAL004_SELFTEST_WRONG_REASON] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GEN4_SUPERSEDED_BEFORE_PUSH] Typed as `candidate_supersession` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: COMMIT_ENVELOPE_CLASSIFIER_FALSE_GREEN_FALSE_POSITIVE_SEQUENCE] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: LOCAL_PRESEAL_SIDE_EFFECTS_INVALIDATED_CUSTODY] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: C3_SOURCE_GENERATION_SPLIT] Typed as `repository_custody_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: LOCAL_ARTIFACT_MEMO_PARITY_UNBOUND] Typed as `repository_custody_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: REVIEW_LEDGER_COMPLETENESS_AND_TYPED_VALIDATION_GAP] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: CANDIDATE_EXACT_SOURCE_AND_OVERLAY_CAPTURE_GAP] Typed as `repository_custody_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: RAW_TRANSPORT_TEXT_MODE_NORMALIZATION_GAP] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: RAW_TRANSPORT_FOUR_CASE_STATIC_REVIEW_NO_GO] Typed as `repository_verifier_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: PDF_FOUR_CONFIRMED_TYPOGRAPHY_FINDINGS] Typed as `repository_publication_defect` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: PDF_TOC_CROWDING_SUSPICION_FALSIFIED] Typed as `review_hypothesis_falsified` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: RUFF_E402_CUSTODY_GUARD_POLICY_MISMATCH] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: GITHUB_JOB_LOG_PARTIAL_FETCH_TIMEOUT_THEN_EXACT_REFETCH] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: LEAN_JSON_NONEXISTENT_KEY_THEN_CORRECT_PARSE] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: DESCRIPTOR_HELP_LAKE_VERSION_TIMEOUT] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.
- [C3 event: LOCAL_LAKE_ROUTING_STALL_AND_ABORTED_ELAN_DOWNLOAD] Typed as `reviewer_tool_process_negative` with credit `none`; no facts beyond the corresponding ledger row are asserted here.

The delimited block below is canonical pretty JSON: object keys are recursively sorted, indentation
is two spaces, text is ASCII, line endings are LF, and the block has exactly one final LF.

```text
C3_PRECOMMIT_REVIEW_PARITY_BEGIN
{
  "bounded_positive_observations": [
    {
      "candidate_commit": "524a1c6af46698f872dce1a04aa0a281ec025a5e",
      "candidate_tree": "40d288360b1b36e4276daff0f69361738fb4f029",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "GEN0_PARSER_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "stdout_sha256": "51fbdafb0a24e5763b2842f558bd5dde3bb4aed110a53ed5a5dea26d81ccaea8",
      "stdout_size_bytes": 7063
    },
    {
      "candidate_commit": "b7d346148c08e78a34d67ec8868ccc5faf1f3583",
      "candidate_tree": "61f9f2b18c0029022cfea3ce1cc193c08724ba40",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "GEN3_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "stdout_sha256": "dacb78d6e533a36ee7fd3a0029ae382ca09e5ea103400a6a67511a450d054633",
      "stdout_size_bytes": 645
    },
    {
      "candidate_commit": null,
      "candidate_tree": null,
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "normal_stdout_sha256": "22219398cfd1570894009f3a167fce11aa458f5a4b2f5372d3b2806c4099ef9b",
      "normal_stdout_size_bytes": 59,
      "observation_code": "GEN4_ROOT_FOCUSED_NORMAL_OPTIMIZED_34_CASES",
      "optimized_stdout_sha256": "d44046c5f910dad8148a67b3336f733267d45d8303ae02d9ce219cb69c2f246b",
      "optimized_stdout_size_bytes": 62
    },
    {
      "candidate_commit": "6bc0a15d3eaf15d593918e3f78934b08030d6b4f",
      "candidate_tree": "b66da0309727876a04fad05a332bda30265fe7f3",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "GEN4_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "stdout_sha256": "95b6f8a4a1e88df582a31561ca25199228409c5e1134fc24c1e8c4b0f3f8d46d",
      "stdout_size_bytes": 645
    },
    {
      "candidate_commit": "6bc0a15d3eaf15d593918e3f78934b08030d6b4f",
      "candidate_tree": "b66da0309727876a04fad05a332bda30265fe7f3",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "GEN4_STANDARD_AND_RAW_ALTERNATE_INDEX_TREE_EQUAL",
      "raw_index_sha256": "e62b876f7f674606accea88943e002e7ce223206a948caa162813d0d9ab133c0",
      "standard_index_sha256": "ba6598c187836bb3aaa171ed6df01c238d0e8e2642a684df238d601c751f48c0"
    },
    {
      "case_family": "python_entry_isolation",
      "cases_completed": 18,
      "checker_sha256": "cbb08b17ff09c967a6ac9e49ba071b279e22fb903fe1a75b501973b779edebc8",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "SESSION_56745_ENTRY_ISOLATION_18_CASES_COMPLETE",
      "restoration": "byte_exact_both_sources",
      "self_test_sha256": "0cfd0480721ddce0df533b97ec28082a94202c2a67fd9c0121382466904ebaec",
      "session_id": 56745
    },
    {
      "cases_completed": 34,
      "checker_sha256": "4ccb393e1089faf2f747c8469bc642b00e2323f7e4fd17dc976b1d90289b65c8",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "memo_sha256": "9a4ec4b7ee663875039fbd996e48732cdae5c1f56592eb9d15ed627ba41b58ca",
      "observation_code": "SESSION_84056_PUBLIC_CI_PORTABILITY_34_CASES_COMPLETE",
      "policy_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
      "receipt_sha256": "73c8b509304f0a23382f531d9b94511c58f14f1e5a75ef1147d8cbb80bf02a20",
      "restoration": "byte_exact_five_targets",
      "self_test_sha256": "f2464399e6a497e2fcf1924e63c26c1016f2b49f06cc3392ae7666d8dd7fbad9",
      "session_id": 84056
    },
    {
      "cases_completed": 34,
      "checker_sha256": "b09c842b0c2ac2eb29087ff2581a2a384f28702b14cbbbc0331775c7fbc16cc6",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "memo_sha256": "ca4c6c29fecbbb2c53fb6366cf9122008e8db16aba1018645b936d6b94508025",
      "observation_code": "SESSION_97473_PUBLIC_CI_PORTABILITY_34_CASES_COMPLETE",
      "overlay_path_count": 187,
      "restoration": "five_targets_and_overlay_status",
      "self_test_sha256": "f76c79cd4ea86ff6012c30f6f92d473f04dd0c88a475499cb86e01ada84b2e1c",
      "session_id": 97473
    },
    {
      "candidate_commit": "266760007b59642a6b9e12ad47ce0dffda54be26",
      "candidate_tree": "601f2681bdd88673e658d1b9a6e96de1936c8215",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "FINAL003_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "stdout_sha256": "5d95f7b57b61f82bb1155a85417c46d86a3cf9d1dabc4a5d8427df519c5da9b5",
      "stdout_size_bytes": 645
    },
    {
      "cases_completed": 17,
      "checker_sha256": "710a6124b23ec08bfb492d1c0fbdd1a4ce2d0a5744bccc7dfaa7ac7b51738fd4",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "memo_sha256": "3984f9438f9b1560db826b03d005d363f94fe619cbff1c290cbe52750f361dc3",
      "modes": [
        "normal",
        "optimized"
      ],
      "observation_code": "FINAL003_LEAN_PORTABILITY_NORMAL_OPTIMIZED_17_CASES",
      "policy_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
      "restoration": "green_baseline_final_and_candidate_removed",
      "self_test_sha256": "a4d5152f752c8773f9fbceea0d4737a60a22a67696423a9cd709a0fec2c9e120"
    },
    {
      "candidate_commit": "f0515e455d969eafe9a4f260f50341b0a120dc73",
      "candidate_tree": "eac26211c4d76989253ce78ae2e4936d370932e1",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "observation_code": "FINAL004_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "stderr_size_bytes": 0,
      "stdout_sha256": "a5e0e7644066968be42a1ee502c3d52fd1338680fcda13390ff41c129fee29c7",
      "stdout_size_bytes": 645
    },
    {
      "candidate_commit": "f0515e455d969eafe9a4f260f50341b0a120dc73",
      "candidate_tree": "eac26211c4d76989253ce78ae2e4936d370932e1",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "monitor_sha256": "5d093695331e1965c9855f22b5cc26da1ca5820ae0c5c53a78029935c7aa1aa0",
      "monitor_supervisor_lens_count": 47,
      "observation_code": "FINAL004_COMPONENT_REVIEWS_BOUNDED_GO",
      "supervisor_sha256": "498372124947ef06c1d4661b8bf0405d1fcfbb9014448e6dcd300b8fadbf6811",
      "verifier_lens_count": 46,
      "verifier_sha256": "e8e1df74b4c17d665a202ad00a778c2e19a7c011017d1c6fe4231a46eab41576"
    },
    {
      "checker_sha256": "919d1d778d7e805bf1b515ee5f95d21026ce873695d25ac194d2a1d19a084fc5",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "memo_sha256": "facb2ddaef514536215d9f1e747a1885534ff696bf6ed18145a991b2db4783b6",
      "modes": [
        "normal",
        "optimized"
      ],
      "observation_code": "FINAL004_TARGETED_LAKE_PREFLIGHT_NORMAL_OPTIMIZED",
      "policy_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
      "restoration": "green_baseline_final_and_candidate_removed",
      "self_test_sha256": "015203dc260a6b845ee0ed11eb5a0edb4a22b9d7c337bde5f3f4072d2550aaa9"
    },
    {
      "checker_sha256": "09d7816ccd2a245c12ac4db99c0e2502e905193208639abc8248a567da82f339",
      "contracted_total": 350,
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "memo_sha256": "ced18c5406491daccb490be8c1f83a9dc2067035412887810d7569e078acf9b1",
      "normal": {
        "exit_code": 0,
        "pid": 36409,
        "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "stderr_size_bytes": 0,
        "stdout_sha256": "b5c3d3d1eef00b68b90fb3d0f0002b9871d0389ee46f8f8974d4483982f933a3",
        "stdout_size_bytes": 726
      },
      "object_association": "post_hoc_not_atomic",
      "observation_code": "GEN0_FULL_NORMAL_OPTIMIZED_350_CASES_COMPLETE",
      "optimized": {
        "exit_code": 0,
        "pid": 36922,
        "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "stderr_size_bytes": 0,
        "stdout_sha256": "5f6c320dd6391ec6ef9c815fc09362059fdc02e99ade230c294f1d16ae6b77a4",
        "stdout_size_bytes": 729
      },
      "policy_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
      "self_test_sha256": "015203dc260a6b845ee0ed11eb5a0edb4a22b9d7c337bde5f3f4072d2550aaa9"
    },
    {
      "additions": 3,
      "cache_info_index_sha256": "e495746989cb1300f4eabdad595bebdf237d48a8901b92c938960901830075cf",
      "candidate_tree": "40d288360b1b36e4276daff0f69361738fb4f029",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "executable_path_count": 3,
      "explicit_root_index_sha256": "1f50af9e3eba8d7a01025e029c8320dd34fc267403f2377accffb28e2b891c39",
      "modifications": 16,
      "observation_code": "GEN0_THREE_ALTERNATE_INDEX_RECONSTRUCTIONS_EQUAL",
      "path_count": 19,
      "route_count": 3
    },
    {
      "candidate_commit": "524a1c6af46698f872dce1a04aa0a281ec025a5e",
      "candidate_tree": "40d288360b1b36e4276daff0f69361738fb4f029",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "normal_exit_code": 0,
      "observation_code": "GEN0_DIRECT_NORMAL_OPTIMIZED_BYTE_IDENTICAL",
      "optimized_exit_code": 0,
      "stderr_size_bytes": 0,
      "stdout_sha256": "20b5845d1442c8317c027a41d48af128ae79b569bb1f2d769e74d1bf782901a4",
      "stdout_size_bytes": 645
    },
    {
      "candidate_commit": "f62e7e8eafb6f5e2c86b64ac23a754ebf1afbd21",
      "candidate_tree": "75efda476f15da6a82b3e006d0989196436d1a4f",
      "credit": "superseded_bounded_only",
      "event_class": "superseded_bounded_positive",
      "normal_exit_code": 0,
      "observation_code": "GEN1_DIRECT_NORMAL_OPTIMIZED_ACCEPTED",
      "optimized_exit_code": 0
    },
    {
      "credit": "bounded_design_only",
      "event_class": "bounded_design_positive_no_runtime_credit",
      "live_process_families": [
        "crlf_stdout",
        "cr_stderr",
        "invalid_utf8_stdout",
        "invalid_utf8_stderr",
        "invalid_utf8_plus_cr_stdout_cr_before_decode"
      ],
      "observation_code": "RAW_TRANSPORT_FIVE_FAMILY_STATIC_DESIGN_GO",
      "phase_subcontrols": [
        "evidence_count_corruption",
        "text_mode_reintroduction",
        "cr_rejection_deletion",
        "permissive_decoding",
        "precedence_reversal_with_repaired_inner_custody",
        "declared_observed_payload_divergence"
      ],
      "review_sha256": "5771a95476c881c9550eedad8f996a71bc5d7783a20d84905bf5b3d33dde82b2",
      "review_size_bytes": 7904,
      "runtime_credit": false
    }
  ],
  "negative_observations": [
    {
      "candidate_commit": "524a1c6af46698f872dce1a04aa0a281ec025a5e",
      "candidate_tree": "40d288360b1b36e4276daff0f69361738fb4f029",
      "claimed_parser_sha256": "51fbdafb0a24d979695c8fa22ccb9c7e4e444273866635424c378e3041c06c42",
      "credit": "none",
      "event_class": "repository_custody_defect",
      "executed_parser_sha256": "51fbdafb0a24e5763b2842f558bd5dde3bb4aed110a53ed5a5dea26d81ccaea8",
      "reason_code": "GEN0_FALSE_PARSER_DIGEST_AND_ABSENT_FULL_STDOUT_BINDING"
    },
    {
      "actual_inventory": [
        296,
        40,
        331
      ],
      "candidate_commit": "f62e7e8eafb6f5e2c86b64ac23a754ebf1afbd21",
      "candidate_tree": "75efda476f15da6a82b3e006d0989196436d1a4f",
      "claimed_inventory": [
        294,
        40,
        329
      ],
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "exit_code": 1,
      "reason_code": "GEN1_FAILURE_ORACLE_INVENTORY_NOT_RESEALED",
      "stderr_sha256": "7829719b5026a2130c0cbf20ce40c14ed0c3f5f7af91a1b0212a3b55aeef72a9",
      "stderr_size_bytes": 99
    },
    {
      "candidate_commit": "0a2d7c6519ab3d16f8a5dee335409611b53ec574",
      "candidate_tree": "94ebbfc74f98e6899771907a042579a39416b615",
      "credit": "none",
      "event_class": "repository_custody_defect",
      "exit_code": 1,
      "memo_sha256": "dd5bd7a6c29bc158721617628fccfe1d5046b02bec49f9a7e369ec5cc74d98bd",
      "reason_code": "GEN2_TOP_LEVEL_MEMO_PIN_STALE_AFTER_BLOB_REPIN",
      "stale_top_level_sha256": "e25873fa9d3330adac390686a00e76aad57640b7dc19b9c51e98ada7077ad179",
      "stderr_sha256": "40bb691745229ea18fb2ad97f5e486add99a0e476c9ab09d1db6980c32c14fc7",
      "stderr_size_bytes": 91
    },
    {
      "candidate_commit": "b7d346148c08e78a34d67ec8868ccc5faf1f3583",
      "candidate_tree": "61f9f2b18c0029022cfea3ce1cc193c08724ba40",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "reason_code": "GEN3_CORRELATED_MEMO_INVENTORY_MUTANT_INADEQUATE"
    },
    {
      "candidate_commit": "b7d346148c08e78a34d67ec8868ccc5faf1f3583",
      "candidate_tree": "61f9f2b18c0029022cfea3ce1cc193c08724ba40",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 130,
      "reason_code": "GEN3_NORMAL_FULL_SUITE_CONTROLLED_STOP_AFTER_REJECTION",
      "session_id": 76847,
      "terminal_stage": "policy_authority"
    },
    {
      "candidate_commit": "b7d346148c08e78a34d67ec8868ccc5faf1f3583",
      "candidate_tree": "61f9f2b18c0029022cfea3ce1cc193c08724ba40",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 130,
      "reason_code": "GEN3_OPTIMIZED_FULL_SUITE_CONTROLLED_STOP_AFTER_REJECTION",
      "session_id": 1091,
      "terminal_stage": "policy_authority"
    },
    {
      "candidate_commit": "6bc0a15d3eaf15d593918e3f78934b08030d6b4f",
      "candidate_tree": "b66da0309727876a04fad05a332bda30265fe7f3",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "reason_code": "GEN4_INDEPENDENT_OPTIMIZED_FOCUSED_RUN_ABORTED_FOR_SERIALIZATION",
      "temporary_clone_recoverable_from_trash": true,
      "terminal_receipt_retained": false
    },
    {
      "candidate_commit": "6bc0a15d3eaf15d593918e3f78934b08030d6b4f",
      "candidate_tree": "b66da0309727876a04fad05a332bda30265fe7f3",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 130,
      "reason_code": "GEN4_ROOT_NORMAL_FULL_SUITE_OVERLAPPED_FOCUSED_REVIEW",
      "session_id": 15609,
      "terminal_stage": "python_entry_attacks"
    },
    {
      "candidate_commit": "b7d346148c08e78a34d67ec8868ccc5faf1f3583",
      "candidate_tree": "61f9f2b18c0029022cfea3ce1cc193c08724ba40",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 1,
      "reason_code": "GEN3_CONCURRENT_PDF_LEAN_VERSION_TIMEOUT_NO_CREDIT",
      "stderr_sha256": "168c1cd6c29375235f849b65770ee33cc8d3e01ada4f3426492273f5216ee203",
      "stderr_size_bytes": 136
    },
    {
      "candidate_commit": "f62e7e8eafb6f5e2c86b64ac23a754ebf1afbd21",
      "candidate_tree": "75efda476f15da6a82b3e006d0989196436d1a4f",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "path": "/private/tmp/pid-rs-c3-corrected.XXXXXX.index",
      "reason_code": "GEN1_PREDICTABLE_BSD_MKTEMP_TEMPLATE_REJECTED"
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "reason_code": "GEN1_RUFF_MECHANICAL_REFLOW_RESTORED_BEFORE_CANDIDATE"
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "reason_code": "V8_REVIEW_TRACKED_RESUME_APPEND_RESTORED_BEFORE_CANDIDATE",
      "restored_sha256": "5c21a28fe935a689b445004fcacb22395f6cc783e422d290fb157fe0906f3911",
      "transient_append_sha256": "f902596b2d8276c09fe0f1f5479fc2ea7735b480587079c6d6bc9edcb4e88f55"
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 1,
      "reason_code": "PRE_OBJECT_REVIEW_LEDGER_NONCANONICAL_PRETTY_JSON",
      "stderr_sha256": "a4e63b5d3c482acf4331e27e24f78398fbbef9a21718f80b40fdc1f68ac16296",
      "stderr_size_bytes": 118
    },
    {
      "checker_sha256": "2359ecade1447da49fd3e809de36191c4f285d1faad65dc084df77a18cae18b8",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "observed_detail": "Python isolation preamble changed: scripts/check-ksg-phase-isolation.py",
      "reason_code": "SESSION_86029_ENTRY_ISOLATION_EXPECTATION_ORDER",
      "self_test_sha256": "37c067f931bcbc38e89a281a36a2b7b1c9d2b07f2d86fa065eee093d632337a2",
      "session_id": 86029,
      "terminal_result": "stopped_on_first_mutation"
    },
    {
      "checker_sha256": "b337be07077b9567ea313b428f76aaec38d2481d94336d2b894bef90eebf5375",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "precursor_result": "missing_sys_modules_registration_attribute_error_before_mutation",
      "reason_code": "SESSION_56566_ENTRY_MUTATION_DELIMITER_AMBIGUOUS",
      "self_test_sha256": "2c5e22ff98aafcbbec8e4ab219057058d95a470a1a6472387c067a9e457b666b",
      "session_id": 56566,
      "terminal_result": "stopped_before_second_mutation_nonunique_if_not_delimiter"
    },
    {
      "checker_sha256": "67c5598284712b46df5d7c705f0474b282b672c8a40b40b96b21afcc25ce068d",
      "completed_preamble_mutations": 4,
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "observed_detail": "child Python command lacks exact -I -S prefix: scripts/check-ksg-phase-isolation.py",
      "reason_code": "SESSION_3174_CHILD_COMMAND_EXPECTATION_ORDER",
      "self_test_sha256": "3fde8666956ec4cca29987e461a7362560dff9e87b927277b413dea1832b4ebd",
      "session_id": 3174,
      "terminal_result": "stopped_on_first_child_command_mutation"
    },
    {
      "checker_sha256": "2714d37d374eb94f54cd0c358f633ec6e7fa29a8ed9d7a40befa015c3915c655",
      "completed_entry_mutations": 16,
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "observed_detail": "candidate anchor delta differs from the separately reviewed A/M path policy",
      "reason_code": "SESSION_27678_TOOL_README_ANCHOR_ORDER",
      "self_test_sha256": "674642ab33e838babc1f8e2f86716590f86a85318e3c29b52acfdd65c31698d1",
      "session_id": 27678,
      "terminal_result": "stopped_on_seventeenth_tool_readme_mutation"
    },
    {
      "checker_sha256": "0151ff6813ed359ec850df2c83dc1f21ceebb485d9f8291262b2e7f5f5e5faf5",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "observed_detail": "phase path policy historical remediation supersession value changed at $/historical_receipt_sha256",
      "reason_code": "SESSION_62196_PORTABILITY_DUPLICATE_KEY_STALE_POLICY",
      "self_test_sha256": "0cfd0480721ddce0df533b97ec28082a94202c2a67fd9c0121382466904ebaec",
      "session_id": 62196,
      "terminal_result": "stopped_at_portability_receipt_duplicate_key"
    },
    {
      "contaminating_command": "git -C /var/folders/5w/54mv55g13yq4x_7w3ld2csb40000gn/T/pid-rs-ksg-phase-self-test.rwuan5k5/candidate status --short",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "last_pre_failure_elapsed": "01:07:26",
      "observed_detail": "Git executable, configuration, metadata, or visibility context changed during replay",
      "parent_pid": 92493,
      "reason_code": "SESSION_55661_CONTAMINATED_BY_IN_CLONE_GIT_PROBE",
      "session_id": 55661,
      "terminal_elapsed_retained": false
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exit_code": 130,
      "parent_pid": 22724,
      "reason_code": "SESSION_74678_PRIOR_SNAPSHOT_INVALIDATED_AND_STOPPED",
      "session_id": 74678,
      "stop_signal": "SIGINT",
      "terminal_stage": "run_public_ci_portability_evidence_attacks",
      "terminal_time_retained": false
    },
    {
      "checker_sha256": "741a2ceb0f7924784a8b24005c065d0d0b8f42142c9e49a99008c6d9d6ac0ab8",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "exit_code": 1,
      "memo_sha256": "6da138c09e79191d565e9092dc6429561095da82899d5b567e82fabceb83b12f",
      "observed_detail": "mutation anchor count is not 2",
      "reason_code": "SESSION_54874_MEMO_ANCHOR_CARDINALITY_STALE",
      "restoration_green_replay_reached": false,
      "self_test_sha256": "f2464399e6a497e2fcf1924e63c26c1016f2b49f06cc3392ae7666d8dd7fbad9",
      "session_id": 54874,
      "terminal_stage": "portability_receipt_duplicate_key"
    },
    {
      "actual_attribute": "SELF_RELATIVE",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "hostile_family_executed": false,
      "invocation": "python3 -B -I -S -",
      "reason_code": "SESSION_51446_WRONG_SELF_TEST_ATTRIBUTE",
      "requested_attribute": "SELF_TEST_RELATIVE",
      "session_id": 51446,
      "terminal_result": "exited_before_disposable_clone"
    },
    {
      "checker_sha256": "b6648e836cb9fea805c2f7892107c4abc790db092e2df7b9ab242c58366e6fa8",
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exact_elapsed_retained": false,
      "memo_sha256": "42541915305928006faa54facd5d7964f7e8e074e5819d97dcc78e60a10c3406",
      "policy_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
      "reason_code": "SESSION_8070_TERMINAL_RECEIPT_UNRECOVERED",
      "self_test_sha256": "f76c79cd4ea86ff6012c30f6f92d473f04dd0c88a475499cb86e01ada84b2e1c",
      "session_id": 8070,
      "terminal_exit_code_retained": false,
      "terminal_result": "unknown",
      "terminal_stderr_retained": false,
      "terminal_stdout_retained": false
    },
    {
      "candidate_commit": "ffbd24e668a57e8c8c20714998aa27c27085b3c2",
      "candidate_tree": "fbcc8b68cf04caa44555313eb2ecda252a47a7e5",
      "credit": "none",
      "event_class": "candidate_supersession",
      "pushed": false,
      "reason_code": "TREE_FBCC_CHECKPOINT_FFBD_INVALIDATED_AFTER_WRITER",
      "result": "invalidated_after_writer_update"
    },
    {
      "candidate_commit": "7e2812bd6d0b14234325b3ecd065017bec487d2a",
      "candidate_tree": "229e24f3614b9e7fdd28d90cc291c6e6be2ce5f2",
      "credit": "none",
      "event_class": "candidate_supersession",
      "pushed": false,
      "reason_code": "TREE_229E_CHECKPOINT_7E_TRAILING_WHITESPACE",
      "result": "git_diff_check_rejected",
      "trailing_space_count": 2
    },
    {
      "candidate_commit": "c896731c74534417e2de8636d6faa58ab2a54f70",
      "candidate_tree": "6f6ea30c77b6cb92cbcd01770a167b467a6b546b",
      "credit": "none",
      "event_class": "candidate_supersession",
      "observed_detail": "candidate changed-byte projection digest mismatch",
      "reason_code": "TREE_6F6E_CHECKPOINT_C896_CHANGED_PROJECTION_STALE",
      "result": "rejected_before_projection_regeneration"
    },
    {
      "candidate_tree": "f306fd04b0c2ac19ed06f513ed0e183af4fe688f",
      "commit_reported": false,
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "reason_code": "TREE_F306_EXECUTABLE_MODES_STRIPPED",
      "stripped_executable_path_count": 3
    },
    {
      "candidate_commit": "266760007b59642a6b9e12ad47ce0dffda54be26",
      "candidate_tree": "601f2681bdd88673e658d1b9a6e96de1936c8215",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "exit_code": 1,
      "expected_pairwise_hash_cardinality": 20,
      "final_directory_created": false,
      "mutation": "lean-portability-self-test-hostile-inventory-reduced",
      "observed_pairwise_hash_cardinality": 21,
      "reason_code": "FINAL003_SELFTEST_WRONG_REASON",
      "stderr_sha256": "04f4450c545184139f7b3cdbfd1a8cbd7832f7285262f39a0ef13a1b2ac3d5c0",
      "stderr_size_bytes": 423,
      "stdout_size_bytes": 0
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "hostile_cases_executed": 0,
      "reason_code": "FINAL004_PRELIMINARY_CLONE_MODES_0600",
      "result": "checker_rejected_immediately_and_clones_discarded",
      "substituted_mode": "0600"
    },
    {
      "candidate_commit": "f0515e455d969eafe9a4f260f50341b0a120dc73",
      "candidate_tree": "eac26211c4d76989253ce78ae2e4936d370932e1",
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "exit_code": 1,
      "mutation": "foundational-paper-lake-preflight-removal",
      "reason_code": "FINAL004_SELFTEST_WRONG_REASON",
      "stderr_sha256": "7e5863cc8c11510e700af440b487b83e712b3d5ed9740677877e0998838ede2d",
      "stderr_size_bytes": 304,
      "stdout_size_bytes": 0
    },
    {
      "candidate_commit": "6bc0a15d3eaf15d593918e3f78934b08030d6b4f",
      "candidate_tree": "b66da0309727876a04fad05a332bda30265fe7f3",
      "credit": "none",
      "event_class": "candidate_supersession",
      "promotion_prohibited": [
        "tree",
        "commit",
        "direct_run",
        "focused_run",
        "interrupted_full_run"
      ],
      "reason_code": "GEN4_SUPERSEDED_BEFORE_PUSH",
      "result": "superseded_and_rejected_before_push"
    },
    {
      "accepted_advertising_variant_count": 4,
      "accepted_false_green_count": 2,
      "candidate_entry": false,
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "pushed": false,
      "reason_code": "COMMIT_ENVELOPE_CLASSIFIER_FALSE_GREEN_FALSE_POSITIVE_SEQUENCE",
      "rejected_legitimate_control_count": 3
    },
    {
      "concurrent_custody_invalidated": true,
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "initial_cache_file_count": 6,
      "reason_code": "LOCAL_PRESEAL_SIDE_EFFECTS_INVALIDATED_CUSTODY",
      "recorder_attack_count": 2,
      "recreated_phase_cache_count": 2,
      "restoration": "bytes_and_modes_restored_but_mtimes_changed"
    },
    {
      "audit_snapshot": {
        "descriptor_checker": {
          "sha256": "6f99ea81c8860e379a4b4e839900dd79d67b3f0cb7db8982ac54ee3ac1c9badb",
          "size_bytes": 40131
        },
        "descriptor_self_test": {
          "checker_pinned_sha256": "30a845e0142375c460142b7895a582029fc62d691561b60297fcdd2693e66f91",
          "sha256": "0ad1b86311bebaaf595a9d7f4eb4925b31f1ca53ca2657b3cd928d73c9389745",
          "size_bytes": 75984
        },
        "direct_evidence": {
          "internal_checker_sha256": "ec76cc1967ee86bb97be580ee7720b217111811602143ed4518a13fe90ecb0be",
          "schema_revision": 3,
          "sha256": "1b72971ba5343fce8e7d08b7a766515ef208a4643905ae2602c16161efa5f50d",
          "size_bytes": 2812
        },
        "memo": {
          "sha256": "ba75bb108327bc59e932417fdfec3b1de1ffa2d24c71c17d84545023a6dab06a",
          "size_bytes": 78065
        },
        "mutation_evidence": {
          "internal_checker_sha256": "ec76cc1967ee86bb97be580ee7720b217111811602143ed4518a13fe90ecb0be",
          "internal_self_test_sha256": "2bfdeba054e95f326e52a2b413f1485c4f1fea04abae6240501224b522e1c1f3",
          "schema_revision": 3,
          "sha256": "637e3748f2ce3f9f6572337f82cdc629d45c7b4046d56ff69255554b2c571f00",
          "size_bytes": 7992
        },
        "parser_pair": {
          "bound_self_test_sha256": "30a845e0142375c460142b7895a582029fc62d691561b60297fcdd2693e66f91",
          "sha256": "20a0ca2966488ba6539e2a80a98164586d907086555e55f7847f95dfe939cd7f",
          "size_bytes_each": 7968
        },
        "policy": {
          "checker_pinned_sha256": "2873e504e45f301546dd1c74f8c773e4bbdc4bac355ac70534dde83bef30b1d3",
          "sha256": "45583edafc24b0bad291ff25dc380bb995e1898bbef7516799dda918e9fb75d3",
          "size_bytes": 13180
        }
      },
      "credit": "none",
      "event_class": "repository_custody_defect",
      "reason_code": "C3_SOURCE_GENERATION_SPLIT"
    },
    {
      "credit": "none",
      "event_class": "repository_custody_defect",
      "previous_run_credit": false,
      "reason_code": "LOCAL_ARTIFACT_MEMO_PARITY_UNBOUND",
      "unbound_claim_fields": [
        "direct_evidence_size",
        "direct_evidence_sha256",
        "mutation_evidence_size",
        "mutation_evidence_sha256",
        "current_pdf_size",
        "current_pdf_sha256"
      ]
    },
    {
      "actual_code_substitution_count": 18,
      "base_negative_count": 13,
      "base_positive_count": 5,
      "base_projection_sha256": "2f18fbf1fda9cfdec1dd9ab58289bafe3d95293111f30174fdfd39098ef045fb",
      "base_projection_size_bytes": 5935,
      "base_total_count": 18,
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "missing_named_session_ids": [
        3174,
        8070,
        27678,
        51446,
        54874,
        55661,
        56566,
        56745,
        62196,
        74678,
        84056,
        86029,
        97473
      ],
      "missing_object_ids": [
        "229e24f3614b9e7fdd28d90cc291c6e6be2ce5f2",
        "266760007b59642a6b9e12ad47ce0dffda54be26",
        "601f2681bdd88673e658d1b9a6e96de1936c8215",
        "6f6ea30c77b6cb92cbcd01770a167b467a6b546b",
        "7e2812bd6d0b14234325b3ecd065017bec487d2a",
        "c896731c74534417e2de8636d6faa58ab2a54f70",
        "eac26211c4d76989253ce78ae2e4936d370932e1",
        "f0515e455d969eafe9a4f260f50341b0a120dc73",
        "f306fd04b0c2ac19ed06f513ed0e183af4fe688f",
        "fbcc8b68cf04caa44555313eb2ecda252a47a7e5",
        "ffbd24e668a57e8c8c20714998aa27c27085b3c2"
      ],
      "reason_code": "REVIEW_LEDGER_COMPLETENESS_AND_TYPED_VALIDATION_GAP",
      "self_test_comment_claimed_row_count": 17
    },
    {
      "credit": "none",
      "event_class": "repository_custody_defect",
      "live_copy_route": "clone_candidate_shutil_copy2_after_fact_emission",
      "path_loaded_routes": [
        "run_checker",
        "current_facts",
        "generated_block"
      ],
      "reason_code": "CANDIDATE_EXACT_SOURCE_AND_OVERLAY_CAPTURE_GAP",
      "top_level_loader_closed": false
    },
    {
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "pre_repair_report_sha256": "233ffd12855e08c4e43d041bf28393141f53c05980451df34b5426aa6b68bdf5",
      "reason_code": "RAW_TRANSPORT_TEXT_MODE_NORMALIZATION_GAP",
      "subprocess_text_mode": true,
      "universal_newline_transformations": [
        "crlf_to_lf",
        "cr_to_lf"
      ]
    },
    {
      "credit": "none",
      "event_class": "repository_verifier_defect",
      "reason_code": "RAW_TRANSPORT_FOUR_CASE_STATIC_REVIEW_NO_GO",
      "review_disposition": "NO_GO",
      "review_sha256": "0f962513e6ae650de165b4205aada4f74c93b1cd1954b76a3936013ffd45ca62"
    },
    {
      "credit": "none",
      "event_class": "repository_publication_defect",
      "findings": [
        "page_11_splits_PidDescriptorFactorization.lean",
        "page_12_splits_witness.py",
        "json_path_73_characters_protrudes_about_2.1_pt",
        "rust_regression_digest_orphaned_ed_semicolon_suffix"
      ],
      "no_observed_clipping_or_overlap": true,
      "pdf_pages": 16,
      "pdf_sha256": "56551da7dd2d72ca01502d20384021329732fea10ec6ab7ac43cfaa651552502",
      "pdf_size_bytes": 358685,
      "reason_code": "PDF_FOUR_CONFIRMED_TYPOGRAPHY_FINDINGS",
      "review_sha256": "54cbbea456e54376781b0c9d0d44eb634ec8d22d27a3e8fd66499b43916d983e",
      "review_size_bytes": 8814
    },
    {
      "approximate_clearance_pt": 144.5,
      "credit": "none",
      "event_class": "review_hypothesis_falsified",
      "is_defect": false,
      "reason_code": "PDF_TOC_CROWDING_SUSPICION_FALSIFIED"
    },
    {
      "credit": "none",
      "e402_finding_count": 53,
      "event_class": "reviewer_tool_process_negative",
      "formatter_file_change_count": 5,
      "reason_code": "RUFF_E402_CUSTODY_GUARD_POLICY_MISMATCH",
      "repository_c3_gate": false,
      "ruff_version": "0.15.18"
    },
    {
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exact_refetch_sha256": "f197b00e992f58f00695b68315e1864937f886e47f1823208d3ca177a716f087",
      "exact_refetch_size_bytes": 78318,
      "job_id": 90509073372,
      "partial_sha256_retained": false,
      "partial_size_retained": false,
      "reason_code": "GITHUB_JOB_LOG_PARTIAL_FETCH_TIMEOUT_THEN_EXACT_REFETCH"
    },
    {
      "corrected_parse_completed": true,
      "credit": "none",
      "event_class": "reviewer_tool_process_negative",
      "exception_type": "KeyError",
      "parser_receipts_affected": false,
      "reason_code": "LEAN_JSON_NONEXISTENT_KEY_THEN_CORRECT_PARSE",
      "wrong_key_spelling_retained": false
    },
    {
      "command": "/opt/homebrew/bin/lake env lean --version",
      "credit": "none",
      "descriptor_theorem_credit": false,
      "event_class": "reviewer_tool_process_negative",
      "reason_code": "DESCRIPTOR_HELP_LAKE_VERSION_TIMEOUT",
      "timeout_seconds": 60
    },
    {
      "credit": "none",
      "download_rate_kib_per_second_range": [
        50,
        100
      ],
      "elan_download_stopped_near_mib": 75,
      "elan_download_total_mib": 524.6,
      "event_class": "reviewer_tool_process_negative",
      "lake_version_line_produced": false,
      "lake_version_route_terminated_seconds": 2521.35,
      "lean_failure": false,
      "orphaned_lake_pid": 59119,
      "reason_code": "LOCAL_LAKE_ROUTING_STALL_AND_ABORTED_ELAN_DOWNLOAD"
    }
  ],
  "parent": "8b792bc143fff2d84f2d8e7817d1de7850741223",
  "schema": "pid-rs/c3-precommit-review-ledger",
  "schema_revision": 2
}
C3_PRECOMMIT_REVIEW_PARITY_END
```

Canonical compact JSON projection (recursively sorted keys, no insignificant whitespace, ASCII, and
one final LF): **27611 bytes**, SHA-256
`cb4e83dc9ad4f296f1c310f7468e57d84bd6963f86e39d2f1bb1ab259ea19736`.

## Local artifact parity

The schema-revision-1 object below cross-binds three current repository
artifacts, the already executed normal and optimized parser-only bytes, and
the exact-parent PDF Git blob. Repository paths, evidence schemas, retention
classes, byte sizes, and SHA-256 values are independently fixed; array order
is part of the contract. The local parser receipts are review artifacts, not
repository artifacts or independent kernel executions. Equality of their
bytes does not authenticate Python, Lean, Lake, or their dependencies.

The object intentionally contains no memo, phase-checker, descriptor-checker,
self-test, current candidate tree, checkpoint, or current candidate-commit
self-reference. Its only commit field identifies the exact parent Git blob,
and its root `parent` has the same fixed ancestry meaning. Candidate/current
artifact facts flow into this object; the object does not regenerate those
artifacts or feed a memo-derived value back into them.

The delimited block is canonical pretty JSON: object keys are recursively
sorted, indentation is two spaces, text is ASCII, line endings are LF, and the
block has exactly one final LF.

```text
C3_LOCAL_ARTIFACT_PARITY_BEGIN
{
  "candidate_repository_artifacts": [
    {
      "evidence_schema": "pid-rs/lean-descriptor-factorization-check/v4",
      "path": "audit/evidence/foundational-sxpid-descriptor-factorization-lean.json",
      "retention_class": "candidate_repository_artifact",
      "sha256": "63c124ceb985313083ec83aad0aea3c8f0fe328ed16abfe43fc91eb5c1fa68a6",
      "size_bytes": 3421
    },
    {
      "evidence_schema": "pid-rs/lean-descriptor-factorization-mutations/v4",
      "path": "audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json",
      "retention_class": "candidate_repository_artifact",
      "sha256": "b644060ac17f58a966aaebd996ceffe6c707fe4d489864fac20ef64cb0218bb9",
      "size_bytes": 13428
    },
    {
      "path": "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
      "retention_class": "candidate_repository_artifact",
      "sha256": "ee715576c2e3a8f058747b2d7ed97b99bc42c20c16bf07038e85f4887310553b",
      "size_bytes": 358668
    }
  ],
  "local_review_artifacts": [
    {
      "evidence_schema": "pid-rs/lean-descriptor-factorization-version-parser-posix-custody-self-test/v4",
      "execution_mode": "normal",
      "retention_class": "local_review_artifact",
      "sha256": "b08bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6",
      "size_bytes": 12166
    },
    {
      "evidence_schema": "pid-rs/lean-descriptor-factorization-version-parser-posix-custody-self-test/v4",
      "execution_mode": "optimized",
      "retention_class": "local_review_artifact",
      "sha256": "b08bb2e76019f1d2a88a0b4da6cda6a83225d1ef5adf51e8e3dffee2f46a3ae6",
      "size_bytes": 12166
    }
  ],
  "normal_optimized_parser_bytes_equal": true,
  "parent": "8b792bc143fff2d84f2d8e7817d1de7850741223",
  "parent_repository_artifacts": [
    {
      "commit": "8b792bc143fff2d84f2d8e7817d1de7850741223",
      "path": "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
      "retention_class": "exact_parent_git_blob",
      "sha256": "5904626fe91f4d606a09f0b842fcecad102d7585e6654a16e2bbb952ed0882df",
      "size_bytes": 358292
    }
  ],
  "schema": "pid-rs/c3-local-artifact-parity",
  "schema_revision": 1
}
C3_LOCAL_ARTIFACT_PARITY_END
```

Canonical compact JSON projection (recursively sorted keys, no insignificant
whitespace, ASCII, and one final LF): **1845 bytes**, SHA-256
`e339a45df06939c6719a16219ba2288208b9476287a893bf6c84562657238e5c`.

The earlier memo-only insertion intentionally did not re-bind the phase
checker or self-test; that was a historical integration gap. The current
candidate closes the code-level gap: the phase checker enforces schema-v2
key/type/value/marker rules and both projection pins, while the self-test
attacks them through 85 review-ledger executions and 19 local-artifact-parity
families comprising 21 executions. C3 nevertheless remains open until the
settled final-byte suites and external custody gates pass.

## Candidate, custody, and no-credit rule

Before commit, the settled nineteen-path candidate must pass:

- direct v4 descriptor evidence and the full descriptor self-test under
  isolated normal and optimized Python, with byte-identical committed
  receipts;
- parser-only normal and optimized controls, byte-identical with `2/2`
  accepted platform controls, `19/19` rejected hostile probes, and exact
  `4/6/3/5/1/1/4` source/snapshot/private/raw-process/child-stdin/
  cross-stream/retained-negative inventories;
- the foundational wrapper in exact and cross-toolchain modes, including
  exact-rational, Lean kernel, mutation, LaTeX, extracted-text, geometry,
  font, rendered-page, and Primary-sources navigation checks;
- the complete formal-paper set without transferring this PDF result to any
  other paper;
- the phase checker and all 351 policy-frozen hostile cases under isolated
  normal and optimized Python, with the two JSON-type, six phase-Lean
  raw-transport, and one coordinated self-reference controls reported
  separately;
- unchanged KSG science, certified-SxPID2 scientific rules, method catalog,
  identity, release-scope, package, and static-workflow gates applicable to
  C3;
- two independently constructed alternate-index trees from the exact parent,
  both equal to the pre-pinned candidate tree;
- a clean-worktree replay of that exact tree and a scrubbed full-delta
  whitespace check that includes additions; and
- one unsigned, attribution-free, single-parent direct child with exact human
  identity and exact message, pushed by normal fast-forward only after a
  fresh `origin/main` equality check.

Supplying neither candidate tree nor checkpoint is permitted only with the
explicit `--diagnostic-without-external-custody` flag and must print
`NO-CREDIT`. Supplying only one is rejected. A post-hoc tree constructed after
coordinated checker/policy mutation is consistency evidence, not an external
trust anchor.

Only settled-byte runs after every writer stops receive credit. A fresh
hosted C3 run must then complete all CI jobs successfully. CodeQL execution
must also complete, while its open alerts remain explicit release/security
debt pending separate adjudication. The push-triggered hosted result cannot be
honestly embedded in the commit it tests; its terminal receipt belongs to the
next separately authorized milestone.

## Nonclaims and remaining work

C3 does not change PID mathematics, KSG arithmetic, estimator output, bounds,
formal theorem statements, concrete SxPID witnesses, scientific prose,
scientific novelty, or release status. It does change verification commands,
one generated PDF, workflow/wrapper bytes, two portable evidence receipts, and
dependent custody digests. It does not prove identical Python, Lake, Lean,
dynamic-loader, library, dependency, architecture, filesystem, kernel, or
hardware behavior; it does not establish native Windows custody or general
cross-platform reproducibility. It imposes no explicit captured-output or
regular-input byte ceiling, guarantees timeout cleanup only for the direct
child rather than its descendants, and deliberately leaves the passed private-
project directory descriptor as a residual child/descendant capability while
closing unrelated ambient inheritable descriptors. None of those process
boundaries is independent custody or a scientific failure. It does not close KSG M1c, repository-wide
Python custody, PID2 revision 4, SxPID3 Programs A--E, frontier research,
publication, release, or downstream integration.

The two known mathematical-workflow PDF line-break defects and the complete
CodeQL alert adjudication remain explicit later milestones. No result is
promoted beyond its stated object, domain, assumptions, and evidence route.
