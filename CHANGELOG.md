# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Added a standalone, non-migrating Lean 4.32.2 issue-14576 kernel-regression/custody packet while
  leaving the active scientific Lean project byte-for-byte on 4.32.0. It retains two exact upstream
  regression fixtures and a project-defined origin/mapping record. The latter binds exact but
  unauthenticated v4.32.2 `Shell.lean`, `LeanChecker.lean`, and `Environment.lean` path/blob/size/
  SHA-256 observations without retaining those source bytes or claiming source-to-binary
  provenance. On a future strictly qualified asset, the packet compiles the full/minimum fixtures
  and a precisely derived valid-projection near-neighbor under `--trust=0`, then replays three
  ordinary `.olean` files through the direct `leanchecker --fresh` leaf. An accepted future live
  result requires the selected emitted-byte probes to show a residual axiom-shaped `E : sorry` in
  both target oleans and absence of the attempted, rejected `E.mk` constructor in both. In the full
  fixture the synchronous failed inductive
  `addDecl` makes downstream `bad` thmDecl source unreachable and unattempted; a full-only probe
  finds that name absent, while the later separate `boom` command is rejected for its unknown
  identifier. The minimum fixture contains no `bad` declaration, reference, probe, or absence
  claim. Current local self-tests validate this result policy and synthetic wiring; they do not
  establish that runtime inventory. These same-route lookup controls are not an independent
  evidence implementation or a complete declaration inventory. `--fresh` checks emitted
  declarations/constants under the same
  selected implementation; it does not re-elaborate source, rerun `#guard_msgs`, replay the rejected
  constructor attempt, execute unreachable source, provide an external verifier, or establish the
  intended inductive declaration or theorem meaning.
  The exact one-parent release fix/backport `8be817b3…` has parent `f054605a…`, exact subject
  `fix: missing check at kernel inductive declaration (#14577)`, and is the sole parent of tag commit
  `f3b06c70…`. GitHub's provider field `merge_commit_sha` separately records one-parent pull-request
  result `a39eab69…` over `b1722ada…`; it diverges from the tag with observed merge base
  `4792cd22…` and a different tree. Those manually transcribed provider/API facts have no retained
  raw response or authentication, and the PR result is not claimed to be a two-parent merge commit
  or an ancestor of the release tag.
  POSIX isolated-child custody now captures the initial non-self PGID and performs bounded group
  cleanup after every normal, nonzero, timeout, and unexpected outcome in the kernel runner, outer
  bounded runner, zstd consumer, and nested wrapper. The escalation policy is TERM/500 ms then
  KILL/2,000 ms with 10 ms absence polling and a 2,000 ms direct-child reap bound; it is a policy,
  not a signal-delivery log. Early-leader return-code 0 and 7 controls verify delayed same-group
  descendants are absent for outer and nested routes. The positive nested wrapper test invokes the
  real outer function through an explicitly injected local child seam and earns synthetic wiring
  coverage only, not child/archive qualification. Cleanup observations are non-atomic, cannot rule
  out PGID reuse, do not reap non-child descendants, and do not continuously contain descendants
  that change process group or session. All private roots, query/olean paths, child HOME/TMPDIR,
  extraction destination, and staging directories have mode 0700 explicitly enforced after
  creation; restrictive and permissive umask routes are exercised.
  The sealed kernel checker is 117,195 bytes at SHA-256 `5292a087…bbeb4`; the outer checker is
  141,464 bytes at `cd9579f4…7697b`; canonical typed metadata is 12,671 bytes at
  `d60ace3f…602d4`. Normal and optimized isolated self-tests are byte-identical within each suite and
  respectively reject exactly 197 and 347 named negative controls while accepting 8 positive
  controls per mode; kernel retains three demonstrated no-credit counterexamples. Both official
  assets remain `hosted_pending`, so CI and `just lean-kernel-14576-packet` run only local source and
  positive/negative policy/custody controls—no live archive regression, new qualification, hosted
  success, project-proof replay, independent kernel, kernel-soundness proof, estimator change,
  mathematical claim, or PDF change is claimed. The earlier Darwin result remains historical and
  nontransferable through the exact committed 144,128-byte receipt `6820d85d…95f43`.
- Added the acyclic hosted-observation receipt for exact C3 publication commit `8905532`, tree
  `7f1f0b0`, directly over `e72c336`. Push CI run `31155454637` attempt 1 completed all 45
  expected jobs successfully; dynamic CodeQL run `31155454365` attempt 1 completed all four
  expected analyses successfully. The 35,193-byte typed
  JSON (`a7eeb570…`) retains every observed job's exact ID, name, run, attempt, head, status,
  conclusion, and opaque API timestamps; the 4,391-byte Markdown companion (`85465231…`) binds
  that frozen JSON one way. Exact 45-name and four-name rosters, typed counts, unique IDs/names,
  complete API-reported pages, terminal partitions, and exact run/attempt/head equality determine
  the bounded disposition. The receipt does not bind its own future commit/tree/blobs or future
  CI, and it grants no security-clean, scientific, theorem, PDF, release, or downstream credit.
  Three earlier capture packages remain rejected with zero credit: v1 omitted per-job
  `run_attempt`; v2 admitted Python's `True == 1` numeric equality; v3 could retain an exact token
  echoed by its expressly unauthenticated `gh` while claiming token nonretention. V4 scans exact
  token bytes in returned stdout/stderr before response-dependent errors, parsing, hashing, or
  writes, sanitizes external-data errors, structurally separates JSON null conclusions, and
  narrows GET and credential statements to testable claims. It explicitly does not exclude
  partial, encoded, hashed, encrypted, transformed, file, IPC, descendant-process, or side-channel
  leakage and does not authenticate `gh`, Python, GitHub, runners, actions, or the network.
  Normal and optimized generation were byte-identical; three generated-path and two installed-path
  isolated validations passed, with each normal/optimized pair byte-identical. Those routes share
  source/runtime lineage and are not independent implementations. Two exact-byte
  adversarial reviews found no remaining bounded contradiction, without institutional-independence
  credit. Five transient hosted-query transport failures, one monitor configured with a 20-second
  outer limit and interrupted with exit 130, and one later unavailable monitoring process remain
  zero-credit operational negatives. No
  estimator, theorem/proof source, numerical fixture, workflow, catalog, TeX, or PDF input changed,
  so no PDF was regenerated for this receipt-only milestone.
- Added schema-v2/revision-2 publication-custody evidence for exact unsigned receipt commit
  `e72c336`, tree `47c3da3`, directly over reviewed C3 subject `dbd3984`. The 1,473-byte local
  event (`629a700e…`) binds a 406,066-byte validator (`e141fea9…`) and 38,206-byte generator
  (`6fc18a0e…`) before the 144,128-byte machine receipt (`6820d85d…`) and 12,062-byte Markdown
  companion (`88160c13…`). Its time is only an unauthenticated pre-serialization lower bound, not
  receipt completion time, trusted time, execution attestation, authentication, or future-commit
  identity. Candidate-only and installed validation both passed under exact isolated normal and
  optimized Python commands, checking 258 schema objects and 258 injected-extra-key controls;
  within each mode pair stdout is byte-identical and stderr is empty. Those correlated routes do
  not constitute independent implementations. Two pre-event source freezes were rejected with
  zero credit for a control-flow overclaim and a hidden installed-pair dependency. The accepted
  receipt retains exactly 17 ordered negatives, `C3-PUB-N007`--`N023`, including the stale v5
  finalization and its self-incomplete archive manifest.
  The `e72c336` hosted state remains nongreen: manual CI `31128514121` reports 45/45 success,
  automatic push CI was not observed, and CodeQL `31128379468` reports two successes plus two
  cancellations and overall failure. The one authorized rerun process exited 1; a later captured
  response-body readback reported no registered attempt 2. Statuspage and GitHub response bodies
  are not authenticated here, and no outage-causation, zero-alert, zero-vulnerability, or
  security-cleanliness claim follows. The separately green `dbd3984` runs do not transfer.
  The persistent local retention mirror now contains 124 copied files totalling 552,692,414 bytes
  before its note: all 107 exact sealed-package leaves required by installed validation, the
  separate 72,708-byte Lean source-replay receipt, and 16 final-run capture files. It does not
  mirror live Git state, the object database, executables, standard libraries, dynamic libraries,
  transitive runtime dependencies, or future hosted events, and is not remote backup, WORM,
  authentication, or attestation. The separate exact-source Lean 4.32.2 replay passes all 14
  repository paths as 13 semantic byte units, with 321 path declarations, 243 named theorem/lemma
  axiom audits, and 12 acyclic dependency edges; ten anonymous examples receive no named-theorem
  credit. That same-kernel result and the issue-14576 custody replay establish neither an
  independent kernel, source-to-binary provenance, reproducible builds, theorem truth/relevance,
  nor cross-platform validity. Nothing transfers among KSG, Ehrlich continuous
  shared-exclusions PID, categorical Makkeh--Gutknecht--Wibral SxPID, Williams--Beer `I_min`,
  fitted quantized PID, project heuristics, or wrappers without a proved mapping whose premises
  hold. No estimator implementation, theorem/proof source, numerical fixture/value, or TeX/PDF
  source changes in this descendant; its future enclosing commit and hosted results require
  later external observation.
- Closed the bounded post-receipt C3 correction chain at exact subject `dbd3984`: CI run
  `31112402374` completed 45/45 jobs successfully and separate CodeQL run `31112399699`
  completed 4/4 at that same head. The two predecessor CI runs remain terminal non-green
  partitions of 43 successes, one failure, and one cancellation each; paired CodeQL success does
  not override either failure. The acyclic machine/human receipt pair preserves N001--N018,
  including the lost historical alternate index, invalidated and rejected review candidates, the
  failed partial CodeQL archive attempt, and the credential-in-argv/transcript incident. Three
  separately prompted exact-byte reviews returned bounded GO only after receipt-wide archive facts
  moved outside both hosted-run objects. Security cleanliness, credential noncompromise, complete
  containment, provider-state inspection, and institutional independence remain unproved. The
  correction changes no estimator, theorem, claim packet, certified job, Just recipe, TeX, PDF
  input, or scientific conclusion, so no PDF was regenerated. The receipt intentionally leaves
  its future commit/tree/blob identities null; publication requires a reviewed direct child of
  `dbd3984` and later external or descendant custody.
- Corrected the full-history secret scanner after exact-subject receipt commit `410a347` exposed
  two false positives on the receipt's public `job_api_sha256` fields. The exception is restricted
  to that exact dated JSON path and a complete lowercase SHA-256 line shape; its executable policy
  self-test now accepts 9 intended public-digest forms while rejecting 56 nearby-path, nearby-key,
  nonhex, prefixed, and malformed-syntax controls. The two admitted values separately match the
  retained duplicate GitHub job-API captures. CI run `31104508451` and its two findings remain
  non-green zero-credit evidence; a successor hosted run was required and is recorded above as
  exact run `31112402374`. This is a scanner classification correction, not secret-absence
  evidence, a broad digest exemption, or a scientific/PID/Lean claim.
- Closed the bounded exact-subject LuaLaTeX format-custody subgate for `dfb77a0` with an acyclic
  hosted receipt: CI run `31084336902` completed 45/45 jobs and 537/537 API steps successfully;
  the formal workflow-PDF job passed 313/313 frozen controls; separate CodeQL completed 4/4 while
  retaining 90 open alerts and incomplete Rust extraction; and a 191-node read-only capture was
  built twice into byte-identical canonical USTAR archives, separately audited, manually
  extracted, and replayed under exact isolated Python. All 53 identified negative routes remain
  zero credit. This closes only the exact format-custody engineering subgate: post-14576 Lean
  4.32.2 replay, KSG M1c, PID-family mathematics, security cleanliness, release readiness, and
  downstream authorization remain open.
- Captured LuaHBTeX's selected `lualatex.fmt` into an exact one-file private snapshot after hosted
  CI for map-free correction `e53dc427` failed closed on Ubuntu's ambient
  `/var/lib/texmf/web2c/luahbtex/lualatex.fmt`. The checker now requires the exact
  `$TEXMFSYSVAR/web2c/luahbtex/lualatex.fmt` source leaf, no-follow descriptor capture and rewalk,
  a single-link mode-0444 file beneath a mode-0555 root, exact size/digest replay before every
  compiler pass and once after both builds, a `TEXFORMATS` search path containing only that root,
  exact Kpathsea path/selection preflights, and raw/resolved `.fls` format sets equal to the private
  pathname. It does not admit
  `TEXMFSYSVAR` generally. Forty-seven separately counted controls cover exact capture and
  selection; empty, multiline, noncanonical, default-expanding, and source/result-mismatch queries;
  empty/oversized sources; source-order and allowlist mutations; no-follow/exclusive capture;
  source/destination rewalks; sealed modes/inventory/link count/digest; actual compiler-environment
  consumption; verifier ordering before every pass and after both builds; the complete final
  source/size/digest receipt; and lowercase, mixed-case, missing, extra, and aliased FLS formats.
  The frozen suite is now 313
  controls. A serial full-exact local replay rebuilt both isolated 51-page reports and retained
  the exact PDF/render/executable/pypdf/format receipts after one concurrent full attempt failed
  closed on missing decision-record custody; both outcomes are retained without splicing. Current
  color/grayscale visual review and two separately prompted source reviews found no surviving
  bounded local defect. The failed hosted run remains zero-credit evidence. This is bounded build-input
  custody, not format/toolchain authentication,
  pre-wrapper sandboxing, cross-platform byte identity, or a scientific/Lean/PID claim.
- Removed the mathematical-workflow PDF build's unnecessary dependency on LuaTeX's generated
  default `pdftex.map` after exact Noble predecessor `30c8fa8` passed the Latin Modern layout
  correction but failed closed on
  `/var/lib/texmf/fonts/map/pdftex/updmap/pdftex_dl14.map`. Each isolated build now enters through
  an exclusively created, descriptor-replayed, single-link mode-0444 wrapper whose first explicit
  operation suppresses the default map after the selected format loads. The wrapper refuses
  pre-existing described `find_map_file` handlers, denies later nonempty map-file lookups that
  reach `find_map_file` on the tested TeX `mapfile` and Lua `pdf.mapfile` routes independently of
  requested spelling, emits one exact pre-source sentinel, and loads
  the captured source under an explicit stable job name. A category-2 file-event callback is
  defense in depth only; raw and resolved `.fls` input map-path checks are secondary recorder evidence.
  The current 313-control suite freezes the partition 194 predecessor + 37 bounded-probe + 17
  entry-wrapper + 7 runtime-map + 8 FLS-map-path + 3 transitive-executable-custody + 47
  format-custody controls and retains renamed-map, absolute-path, TEXMF-shaped-path, `mapline`
  boundary, result-log,
  process-group, descriptor-replayed decision/readiness, wrong-mode/malformed-record,
  publication-stall, and watchdog-order cases. The
  liveness harness returns the command's shell-byte status on a clean ordinary-completion route
  after anchored process-group cleanup and parent-side process-group-absence adjudication. Only
  exact rejection statuses 1 and 2 receive named-mutation credit; the watchdog retains a delayed
  KILL fallback, while timeouts, custody failures, launch failures, and signal deaths receive no
  such credit.
  This is a bounded trusted-source/toolchain portability correction, not a
  hostile-TeX sandbox, syscall-complete trace, tool authentication, mathematical or PID
  validation, Lean result, or security-clean claim. Every rejected private-map, `TEXMFSYSVAR`,
  command-line-order, container-download, hanging-suite, mode-0444-fixture, liveness, and
  false-credit predecessor remains a zero-credit negative in the dated evidence report.
- Corrected the mathematical-workflow PDF checker's cross-platform font-layout premise after the
  exact Ubuntu Noble successor failed despite the required `lmodern`/`fonts-lmodern` payload being
  installed. Clean-environment Kpathsea selection is now checked against a filename-specific
  allowlist: all fonts may use their exact `TEXMFDIST` path, while only Latin Modern families may
  use Ubuntu/Debian's exact `/usr/share/texmf` overlay. A single no-follow descriptor-chain route
  now selects and copies the source, re-walks every source component, creates the destination
  beneath an opened private-root descriptor, and rejects namespace drift. Nineteen new controls
  cover both supported layouts and reject query-status, empty, multiline, outside-root,
  wrong-family-root, special-file, and symlink selections. That predecessor suite contained 194
  bounded same-checker controls; the later implicit-map correction expands and separately freezes
  the current inventory. Neither count is font-package authentication or an independent render
  implementation.
- Re-adjudicated the certified-SxPID2 claim checker's exact enclosing custody after the
  mathematical-workflow publication gate changed the CI/Just containers, shared script
  documentation, and formal-PDF dispatcher without changing the certified-SxPID2 job, local recipe,
  release-audit dependency, or exact-log-product leaf. The initial hosted run failed closed on the
  stale whole-workflow digest; the retained receipt records every old/new digest, unchanged slices,
  and the limited non-scientific scope of the rebind.
- Normalized Ubuntu's `luaotfload-tool` symlink target into the already first-ranked pinned
  `setup-python` executable directory before entering the formal-PDF clean environment. The first
  correction used a lower-ranked private subdirectory and failed a nested search-path replay after
  the checker reconstructed its canonical directory order; both failed hosted controls are retained
  with exact log digests. The gate byte-compares a same-directory staging file and publishes it with
  an atomically non-clobbering hard link, then captures and stability-checks the executed script and
  interpreter chain; it does not treat the copy as tool authentication.
  The exact successor passed all 175 workflow-PDF controls and the first six ordered paper checks,
  then exposed a separate clean-home Lean bootstrap defect: the checker correctly discarded
  `ELAN_*`, Elan auto-installed the tracked toolchain, and its informational stderr violated the
  silent version-probe contract. CI now rejects pre-existing clean-state paths, compares the
  requested Lean toolchain with the tracked pin, explicitly provisions it into a direct non-symlink
  `.elan` directory under the isolated temporary directory before evidence collection, ranks the
  pinned Elan proxy ahead of runner-image commands, and points both `HOME` and `ELAN_HOME` at that
  state. The strict no-stderr proof probe remains unchanged; explicit setup is not Lean archive
  authentication, kernel soundness, or independent-kernel evidence.
- Expanded the mathematical problem-solving workflow into a 51-page, source-synchronized
  publication artifact with four project-local vector figures and explicit PID-family,
  premise, claim-revision, invalidation, evidence-dependency, and durable-agent-state
  firewalls. Its isolated verifier now binds exact Markdown/TeX/helper/figure/tool inputs,
  PDF structure and navigation, deterministic color/grayscale renders, and a separately
  rebound page-review receipt. Normal and optimized Python replay their shared Python mutation
  cases, while the direct shell self-test separately replays 313 bounded controls across the
  synchronizer, log parser, render comparator, lock/bootstrap, captured read-only source snapshot,
  refresh/rollback, SVG, PDF, cache/import, race, liveness, result-log, LuaTeX map-operation, and
  contamination surfaces. The captured suite makes private writable mutation copies from its
  mode-0444 read-only source snapshot and removes all six outer workflow-custody variables before
  launching nested checker probes.
  The resulting custody is finite and toolchain-relative: it does not prove the document's
  mathematics, authenticate admitted executables, establish accessibility conformance, or
  make same-author reviews independent.
- Disabled routine Dependabot version-update pull requests for Cargo, GitHub Actions, and Python
  while preserving Dependabot security-update eligibility. This reduces automated version-update
  pull request and notification churn; it does not assert that dependencies are current or free of
  known vulnerabilities.
- Added an acyclic observational receipt for the exact C3 Noble hosted run at
  `791a39935fdca4cfe4e907829faa240e08520b6e`, including terminal CI, exact-head CodeQL,
  artifact-hash, and local external-custody facts. The evidence-only descendant cannot
  self-authenticate its receipt bytes, does not close KSG G1/M1a or M1c, leaves all 13 integration
  gates open at `integration_no_go`, and makes no security-clean, release, or downstream claim.
- Re-adjudicated the exact-count SxPID2 assurance route as claim revision 3. The producer report
  and resource-policy semantics remain at revision 2; the independent-verification schema is now
  revision 3 because its loaded-execution digest first normalizes nonsemantic CPython string-intern
  cache state. Isolated cold/warm and post-import code-mutation controls distinguish that cache
  transition from executable drift. A deterministic typed digest binds all 51 declared
  semantic/configuration globals, and a complete mutation sweep rejects each named change. The
  claim gate also binds the complete retained revision packet, reviewed machine-evidence
  projections, executable leaf checks, and assurance sources/PDFs; its hostile corpus includes
  Markdown/YAML/Just rendering and dead-command controls. This repairs runtime-local custody
  behavior without verifying CPython, proving the inventory complete, defining a portable
  executable identity, or enlarging the mathematical, statistical, or PID claim.
- Reassociated eligible positive-integer KSG local arithmetic through a deterministic
  Neumaier-compensated harmonic prefix and two sorted harmonic ranges. Public APIs, neighbor and
  shell rules, estimands, signed-value semantics, and nat units are unchanged; the binary64
  association can change persisted values in their last bits. This internal numerical change does
  not promote KSG, continuous shared exclusions, or PID validity.
- Unified the nine formal LaTeX/PDF artifacts under a restrained A4 academic visual system with
  consistent title hierarchy, running heads, section rules, link/listing treatment, embedded-font
  builds, alternating table row bands, and explicit shaded table headers that remain separable in
  grayscale. Added fail-closed visual-system lint and six mutation tests; these protect rendering
  conventions but do not enlarge any mathematical, numerical, or accessibility claim.

### Fixed

- Classified pid-rs explicitly as a standalone, protocol-neutral library and tooling project in
  the machine-readable ecosystem contract and its generated human view. pid-rs is not an NCP
  peer, provider, or consumer and receives no NCP role receipt; any NCP-facing integration remains
  a downstream, consumer-owned optional adapter. This correction does not claim consumer
  compatibility or qualification, change the published GitHub-only `v0.9.0` source-review
  prerelease, promote the proposed pid-rs 1.0 scope, or imply that an NCP candidate is released.
- Regenerated the foundational SxPID exact-rational evidence after the
  same-sample custody change altered its bound Rust kernel bytes. The fresh
  standard-library record differs only in `rust_kernel_sha256`, and both public
  Rust relation-witness tests pass. This repairs source-change detection; it
  does not re-adjudicate the mathematical claim or imply statistical,
  security-clean, integration, or release status.
- Split the former same-sample compatibility description into four machine-checked identities: a
  provenance-only Rust envelope, the project-defined exact-significand same-row transform,
  Williams–Beer `I_min`, and categorical Makkeh–Gutknecht–Wibral shared exclusions. The audit found
  that Python's former materialized-edge path and Rust's internal transform disagreed at ordinary
  binary64 boundaries: on `[0,1]` with ten bins, `0.3` entered bin 3 in the former route and bin 2
  in the Rust route. After its stricter legacy compatibility preflight, Python now calls the Rust
  wrappers directly; admitted calls share the Rust transform, and the rejected edge route is a
  permanent negative control. Python can still reject very large bin counts accepted by Rust, so
  accepted-domain equality is not claimed. The wrappers also apply their categorical estimator's
  aggregate resource gate before quantization; 64-bit first-rejection witnesses are frozen for
  SxPID2/3/4 at 17,676/5,555/1,119 rows (operations) and `I_min`2/3 at 813,441/110,924 rows (bytes),
  with direct, wrapper, and Python exception parity. An asymmetric four-source fixture guards
  source/mask order, and independent two-bit COPY guards the method boundary: identical mutual-
  information coordinates coexist with `I_min` redundancy `ln(2)` and MGW redundancy `ln(4/3)`.
  The audit additionally rejected two stale registry statements: the quantized SxPID bootstrap
  recomputes per-resample ranges and exact-significand labels rather than fitting or retaining an
  edge vector, and the provenance-only same-sample Rust envelope has no floating-point scientific-
  result layer. Its algebra, numerical, and statistical layers are therefore explicitly not
  applicable. These were source/provenance defects, not observed estimator-output defects.
  Expanding the two protected release families and six reviewed cross-lane catalog methods also
  raised the KSG revision self-test inventory from 176 to 186 mutations. The first replay rejected
  every mutation but failed its stale partition lock; the corrected 16/2/12/35/78/43 partition
  passes in normal and optimized Python, so no surviving mutation is hidden by the count update.
  These are bounded implementation, resource, and semantic-custody results—not a bin-selection
  theorem, population calibration, stable-edge equivalence, continuous-PID mapping, or scientific-
  novelty claim.
- Corrected cross-family PID terminology and assumptions across the README, method catalog,
  ecosystem contract, release scope, and software-identity references. Categorical MGW shared-
  exclusions atoms remain distinct from the gauge-dependent continuous Ehrlich construction, KSG
  mutual-information estimation, Williams–Beer `I_min`, fitted quantized SxPID, and project-defined
  wrappers or heuristics; no equality or validation result crosses those boundaries without an
  explicit mapping theorem. Exact semantic-authority and KSG catalog projections were
  re-adjudicated with coordinated-rebind and adjacent-method negative controls; these custody
  checks do not infer literature truth or estimator validity.
- Recorded a descendant erratum for two logical CodeQL runtime-resolution field errors
  repeated across four fields in the content-addressed retained compact summaries. The external
  artifacts remain unchanged, the incorrect values receive zero credit, and the observed values
  receive only bounded exact-subject-run log credit. C3 closure, security status, KSG status, and
  release status do not change. Exact erratum custody remains **NOT ESTABLISHED**.
- Restored the revision-3 certified-SxPID2 scripts-guide bytes after the method-catalog semantic
  authority update changed that frozen claim input. The semantic authority remains implemented and
  rendered in `METHODS.md`; this custody repair does not re-adjudicate or widen the SxPID2 claim.
- Corrected the frozen semantic-authority data domain for `testing.row-permutation` from method
  results to numeric matrices, matching its aligned `MatRef` inputs. Rebound the complete row and
  reviewed root, added a coordinated-rebind negative control, and documented explicit root
  re-adjudication. This remains change detection, not semantic or scientific truth inference.
- Added Ubuntu Noble's `texlive-luatex` to the cross-toolchain PDF job. The hosted successor had
  reached the eighth paper but `markdown` 2.23.0 selected deprecated mode 0 because
  `lt3luabridge.tex` was absent; the existing fail-closed log gate correctly rejected that warning.
  Installing the package-supplied bridge makes the same TeX source select supported mode 3 while
  retaining the existing fail-closed log-level warning rejection. This correction adds no allowlist
  or suppression and changes no theorem, estimator, formal source, or committed PDF; the unchanged
  cross-toolchain gate rejects extracted-text or page-geometry drift. The certified-SxPID2 gate's
  complete-workflow container digest is rebound to the exact corrected workflow; its extracted
  scientific commands and authorities remain unchanged.
- Added Ubuntu Noble's `texlive-plain-generic` package to the cross-toolchain PDF job after the
  exact f6 hosted run reached the mathematical-workflow paper and failed because its existing
  `gobble.sty` dependency was unavailable under `--no-install-recommends`. No TeX source, PDF,
  theorem, estimator, or numerical artifact is changed by this package correction. The expired
  current-`HEAD` direct-child custody command is also replaced with a no-local replay of exact
  follow-up commit `f6fde520...` at its own frozen tree. That preserves the direct-child topology
  check instead of weakening it to accept descendants; the replay does not adjudicate this new
  descendant or imply hosted, scientific, authenticity, or security-clean success. The wrapper
  normalizes its clone-creation umask to `022` after a restrictive-umask probe reproduced mode
  `0700` verifier checkouts and the intended exact-source permission rejection; the private
  scratch root remains owner-only. The superseded interrupted wrapper run retains zero final
  credit. Current operational recipes no longer invoke the f6-only direct checker a second time at
  descendant `HEAD`. The certified SxPID2 claim checker changes only its expected full-container
  digests for the transformed workflow, `justfile`, and scripts README; its extracted
  certified-job/recipe command slices, scientific authorities, claim logic, fixtures, formal
  sources, and PDFs are unchanged. A behavior-preserving Z3 setup cleanup also replaces
  `echo "$(dirname ...)"` with direct `dirname` output after pinned actionlint 1.7.12 identified
  the pre-existing `SC2005` style violation. The operational guide's stale KSG harmonic-revision
  self-test count is corrected from 175 to the source- and hosted-log-confirmed 176 mutations.
- Corrected three failure-diverse hosted-CI failures on the immutable C3 checkpoint without
  changing estimator, formal theorem, certificate, or PDF bytes. The Noble PDF job now installs
  the exact TeX package that provides the document's existing Libertinus wrapper, pins Ubuntu
  24.04, and retains a finite 60-minute ceiling. The
  software-identity final-status regression test now mutates its tracked fixture through a
  deterministic test-only callback immediately after the production first-status read, avoiding
  unrelated shell, workspace-root, and HEAD subprocesses while preserving fail-closed production
  behavior and the repeated final status. A pinned two-clone wrapper separately checks the clean
  C3 commit and reconstructs its byte-identical 16-modified/3-untracked parent-plus-overlay state
  for the normal and optimized 351-case hostile suites; an outer direct-child gate keeps this
  historical replay distinct from custody of the follow-up tree. That outer gate now freezes
  exact source sizes and digests, propagates true normal/optimized modes through every hostile
  child, rejects harness launch/signal/timeout/output failures rather than counting them as kills,
  and applies pre-allocation resource budgets with explicit hard-RSS/Git-internal/filesystem
  nonclaims. The dedicated verifiers require reviewed GIL-enabled CPython 3.11 through 3.14, the
  main and only enumerated Python thread, and actively replace inherited `SIGCHLD` actions with
  `SIG_DFL` before any `Popen`. Nonraising fixed-slot `SIGALRM`/`SIGINT` recorders and typed LIFO
  masks span each launch through reap, post-reap `ESRCH`, and local closure; deferred flags are
  adjudicated only after mask restoration. The fork child unblocks that pair in `preexec_fn` under
  the explicit no-unenumerated-native-thread premise; neither CPython/stdlib authenticity nor hard
  asynchronous deadline preemption is claimed. Process-group liveness is typed as
  absent/present/indeterminate: exceptional cleanup signals the owned original group only before
  reaping its leader, while every post-reap route is observe-only and accepts only explicit
  `ESRCH`; persistent presence or `EPERM` fails closed without risking a signal to a reused numeric
  group. Thirty-eight separately named deterministic harness controls cover the self-test helper
  and exact captured checker, including handler/mask/timer transactions and cat-file abort. CI
  compares checker receipts byte-for-byte and self-test receipts modulo only their
  required mode field. The reviewed overlay is exactly 13 paths (eight modified and five added),
  protects 552 anchor paths, and binds a 109-case/18-family source inventory with 88 declared
  mutation-target verifier launches. The existing SxPID2 claim checker changes only three exact
  digests for the mutable workflow, `justfile`, and scripts README containers; its revisioned
  authorities and adjudication logic are unchanged. The direct-child route is intentionally
  one-transition and must become an immutable replay in the immediate hosted-result receipt child.
  The exact-source runner also fixes its child-process umask at `0022`, so its private Git
  checkouts retain canonical `0644`/`0755` modes under a restrictive caller umask while their
  containing temporary directory remains private; pre-existing source modes are still checked.
  None of these engineering fixes implies KSG, shared-exclusions PID, statistical, remote,
  authenticity, or security-clean validation.
- Hardened the foundational Lean descriptor-factorization replay after the
  terminal 44/45 C2 run exposed a platform-bearing generated receipt. Every
  official C3 phase, descriptor, and foundational-wrapper entry in this route
  now requires Python `-I -S`; the phase gate executes
  digest-bound self-test bytes through isolated standard input, and the Lean
  route snapshots five single-linked tracked inputs plus the selected Lake
  target through POSIX descriptor-relative traversal. It then launches Lake
  from a descriptor-pinned private working directory and passes finite-name
  query files by relative path; a pathname swap/use/restore attack confirms
  the pinned child consumes the reviewed private project. The direct child
  receives `stdin=subprocess.DEVNULL`. After subprocess completion, the v4
  route captures standard output and standard error as raw completed buffers,
  validates the entire stdout buffer before the stderr buffer, and rejects raw
  carriage returns before strict UTF-8 decoding of each selected buffer. This
  is exact completed-buffer validation precedence, not child-stream emission
  chronology. The receipts retain the strictly parsed reported Lean version,
  source commit, Release build, and frozen project-input digests while
  validating but omitting the host platform. Five live raw-child transport
  families cover CRLF stdout, CR stderr, invalid UTF-8 on each channel, and
  same-stdout precedence of raw CR rejection over decoding. One stdin-isolation
  subcontrol and one completed-buffer cross-stream validation-order subcontrol
  are counted separately; these labels do not imply evidentiary independence
  or child-stream emission chronology. Six separately typed, correlated phase
  subcontrols attack the matching source/evidence contract without counting as
  six independent hostile families. Four
  exact-source controls, six snapshot attacks, three private-materialization
  controls, four retained negative controls, two distinct-platform fixtures,
  and nineteen hostile version probes are counted separately from the three
  proof mutations and three semantic countermodels. The expanded nineteen-path
  correction freezes all 351 hostile-suite cases, distinguishes
  externally pinned custody from `NO-CREDIT` local diagnostics,
  binds successful subprocess receipts to caller-supplied lifecycle plus exact
  one-line fields while requiring failure status/channel grammar, whole
  message consumption against templates derived from the unmutated suite-root
  checker and exact caller-held dynamic details. The source model freezes 383
  `require` sites, 43 direct message-producing error sites, and 408 distinct
  templates. The first post-navigation aggregate killed the stale 380/43/407
  seal before hostile-case credit; subtracting only the three-site navigation
  firewall recovers that earlier inventory. This is source-shape custody, not
  a claim of template disjointness, independence, or security completeness.
  Exactly three live typed
  untrusted diagnostic-tail routes admit nonempty tails: Git `cat-file` status
  128, a deleted candidate path, and external-tree whitespace. The former
  Lean-parser child route is retired and rejected. Caller-bound route prefixes
  and canonical tail transport do not establish operating-system or Git
  diagnostic truth. The correction also raises the sequential KSG
  assurance-job budget from 45 to 240 minutes based
  on retained hosted/local timing evidence. It also deterministically
  regenerates the foundational PDF after its displayed commands changed and
  applies four bounded, presentation-only path/digest layout repairs. A late
  independent navigation review found that the unnumbered `Primary sources`
  TOC and outline entries reused the preceding `Reproducibility record`
  destination. The source now creates a fresh adjacent anchor, and the
  foundational wrapper fail-closes over the source, TOC, bookmark auxiliary,
  and distinct page-15 destinations in both the built and committed PDFs, with
  a 72-point minimum vertical separation. Eight failure-diverse navigation
  mutations are rejected in both normal and optimized isolated Python. The
  PDF remains untagged, so this is not an accessibility claim.
  The route imposes no explicit regular-input or captured-output byte cap, and
  its timeout and wait cover only the direct child, with no process-tree
  cleanup. The passed project-CWD descriptor remains inherited by the direct
  child and potentially its descendants, while unrelated ambient inheritable
  descriptors are closed. These are residual capability, denial-of-service,
  and process-lifetime nonclaims, not independent custody evidence. Generic
  endpoint swap/use/restore, a query-subtree swap despite project-FD pinning,
  HOME-influenced launcher state, and live dependency-cache contents remain
  explicit negative boundaries; selected executable provenance remains
  unauthenticated, native Windows handle custody is unsupported, general
  cross-platform kernel equivalence is not claimed, and every directly
  path-invoked Python entry script's already-loaded bytes remain premise-bound
  pending repository-wide Python custody. Only the explicitly nested
  standard-input and exact-source loader routes bind source bytes before
  execution.
  The retained C2/API snapshot's 85 open CodeQL alerts remain unadjudicated
  security debt. The theorem source, Lean project pins, scientific prose,
  Rust/Python scientific code, estimands, and numerical results are unchanged.
  A fresh complete hosted rerun is still required; this is not binary
  identity, authenticity, general cross-platform kernel equivalence, security
  clearance, release readiness, or a scientific advance.
- Provision the pinned Lean/Mathlib environment in both the certified SxPID2
  and formal-PDF CI jobs, install `chktex` for the paper set, and make the
  foundational-paper route preflight its direct `lake` dependency. This
  explicitly provisions the fresh-Ubuntu execution paths; a complete hosted
  rerun is still required before integration can be adjudicated green.
- Fixed four failures observed in the first remote replay of the KSG revision-4 integration
  commit: a CPython 3.11 false rejection in the independent SxPID2 verifier fingerprint, inert
  `actions/checkout` `config.worktree` residue before the strict Git-phase gate, missing
  `lacheck`, and a KSG generator-source test that referred outside the packaged `pid-core`
  archive. Also corrected a latent cargo-deny 0.20.2 common-option-order defect found during
  hostile review. The package now carries a
  digest-pinned generator snapshot and still requires byte equality with the canonical workspace
  source when that source is present. Its absent-workspace branch executes as one exact extracted-
  archive test and requires a regular `.cargo_vcs_info.json` containing one unambiguous
  `path_in_vcs` string equal to `crates/pid-core`; duplicate bindings fail. That forgeable marker
  is package-layout context, not evidence Cargo produced the file and not archive authenticity or
  provenance. These are verification, packaging, and workflow repairs; they do not alter KSG or
  SxPID numerical results.
- Fixed two later local-replay custody faults, distinct from the four public-run failures above:
  the KSG harmonic gate now binds the 48 unchanged protected non-KSG catalog methods separately
  from the one reviewed certified-SxPID2 revision, and the ecosystem capability authority now
  binds the resulting current method-catalog bytes. The historical semantic and consumer
  projections remain unchanged; neither repair changes an estimator, PID atom, or integration
  disposition.
- Fixed a third local-replay custody fault: the finite SxPID2 non-syntactic-zero boundary command
  no longer overwrites its tracked historical receipt during ordinary qualification. It compares
  a fail-closed stable projection, emits the full fresh receipt to standard output, and reserves
  writes for explicit reviewed resealing. The projection removes only two outer execution
  digests, one shape-validated source-manifest leaf, and three shape-validated build-environment
  leaves while
  retaining a digest over every other payload field; 51 targeted controls and a 1,236-case
  exhaustive scalar-leaf sweep bind that policy. The
  observed same-host replay was
  scientifically unchanged but is not cross-platform validation, executable identity, or a
  portable semantic hash.
- Corrected the experimental scientific-contract test fixtures to use the cataloged continuous
  PID2 and unsupported mixed-support identities and origins. The mixed-support fixture now uses
  the contract-defined request regime. A canonical manifest supplies the Rust fixtures, and the
  method-catalog checker verifies their IDs, origins, maturity, and code availability. The tests
  now state that the constructor checks an entry-schema binding and internal axes. They do not
  imply a trusted runtime catalog lookup.

### Added

- Added a revision-4 bounded KSG local-arithmetic package: a standard-library-only 8,198-row
  harmonic/Decimal corpus, direct compiled full-corpus `+0/-0/nonzero = 354/0/7844` checks, a
  separately implemented bounded modular certificate, exact-rational directed enclosures,
  behavioral count-to-helper witnesses, strict fixture regeneration, and fail-closed
  custody/mutation gates. The selected association's maximum
  difference from `binary64(stored Decimal prefix text)` is `8 * f64::EPSILON` nats, attained on
  exactly 40 rows; its exact-rational maximum is uniquely enclosed below
  `9.761311 * f64::EPSILON` nats under the checker's stated Python `Decimal` directed-rounding
  semantics, including the fixed stress rows.
  Both remain under the `32 * f64::EPSILON`-nat finite-corpus ceiling. Exact-rounded references
  differ textually on 6,509 rows and numerically on 5,934 rows but have zero binary64 conversion
  mismatches. Exact `Fraction(Decimal)` subtraction and ordering covers all rows; the enclosure
  route rejects 29/29 scientific/custody mutations and a separately reported comparator firewall
  rejects 2/2 controls in normal and optimized Python. Recursive JSON shape/type/value equality
  similarly separates 28/28 modular scientific/custody mutations from 2/2 Boolean/integer
  controls. The composite `1000001=101*9901` control reaches deterministic u32 Miller--Rabin after
  bypassing the small-prime `2..37` prefilter, which is path coverage only. Odd-prime reflection
  explains the rejected field's four collisions as one event; the selected fields are not
  independent proofs. These are association-specific local-arithmetic results, not ULP or
  universal binary64 bounds, neighbor/estimator/support/PID validation, or
  repository-publication closure.
- Added revision-scoped conditional formal assurance for the positive-integer harmonic
  reassociation used by KSG local arithmetic. A pinned Lean 4 artifact checks 19
  finite-sum, monotonicity, index-map, symmetry, rational-bound, and rational-to-real
  bridge theorems; four premise-explicit Z3 obligations check cancellation, index maps,
  reassociation, and the local range bound. The Z3 checker now performs bounded complete
  S-expression parsing, exact statement profiles and type checks, validates correlated raw/token
  pins, and sends one-read in-memory snapshots to the solver over standard input. Normal and
  optimized fail-closed suites kill 14 Lean and 12 Z3 semantic mutations and separately reject
  52/52 Z3 checker controls (`16` lexer/parser, `25` profile/type, and `11`
  custody/transport/result). A retained well-typed wrong-theorem dual rebase keeps theorem intent
  explicit as a human/Git/receipt cut. The
  analytic positive-integer digamma identity remains a typed premise, and these artifacts
  do not prove Rust or binary64 refinement, neighbor geometry, estimator/support validity,
  continuous shared exclusions, PID semantics, calibration, or application validity.
  A post-observation `x+y <= n+k` set derivation and its stronger balanced lower bound remain
  conditional and unpromoted pending complete source/formal/compiled/mutation/provenance routes.
  Repository and publication integration remain a 13-gate **NO-GO**: canonical unsigned M1a must
  be pushed and verified before a separate descendant M1c can bind immutable final evidence and
  decision artifacts. The Decimal, modular, and SMT-LIB failure memos preserve the corrected
  claims, negative paths, checker repairs, and non-transfer boundaries.
- Added a standalone, source-only exact-count reference certifier for all 24 averaged categorical
  SxPID2 cumulative and Möbius-atom coordinates. It reconstructs exact rational log-linear
  expressions from a strict canonical count-table schema and adaptively encloses them with
  explicitly directed Rug/MPFR arithmetic and exact dyadic endpoints. The certificate binds its
  local source manifest, lockfile, lattice, extractor checks, precision and resource policies, and
  explicitly non-exhaustive build context while excluding `pid-core` binary64 refinement,
  population/statistical claims, pointwise and higher-source SxPID, $I_{\min}$, continuous PID,
  and downstream validity. Qualification includes exact identities, source/target vector-state
  metamorphisms, 1000-digit common-count scaling, 11,856 all-coordinate tolerance-overlap
  comparisons plus 1,482 direct-MI identity comparisons over 494 independently generated binary
  empirical tables, literal-pinned fixture and generator digests, strict parser and process-level
  CLI failures, a digest-pinned early resource-amplification rejection, 34 fail-closed
  static-policy mutations including both strict sign boundaries, reordered or aliased
  rounding-type escapes, and a falsified target-width report,
  stable/MSRV/rustdoc gates, a default locked Cargo-feature graph check, rejection of direct
  command-line native-sys feature injection, and a separate LGPL/native-library distribution
  boundary. The Decimal corpus is bounded numerical agreement, not a rigorous interval oracle.
  The static mutation gate is representative, not a complete semantic proof; CI uploads no
  compiled certifier target artifacts. A standard-library independent verifier now reconstructs
  11,856 coordinates, 1,482 direct-MI identities, and 5,928 cumulative event expressions by a
  separate row scan over the 494-table bounded domain; proves 72 live-certificate containments;
  checks 975 exact-rational logarithm enclosures; kills 23 semantic, one fixed-point-source, one
  event-extraction-source, and four cross-artifact binding mutations; rejects six structural
  adversaries for their intended reasons; and passes two transport/invocation controls under
  normal and optimized Python. It rejects Cargo source substitution and pins reviewed registry
  sources and checksums. These remain bounded fault-sensitivity and conditional executable
  evidence, not universal or formal verification.
- Hardened the auxiliary exact-product report checker so it plans every denominator-cleared
  exponent and both local and aggregate projected-bit admissions before any rational powering.
  Two fail-on-power sentinel controls now establish that locally rejected and aggregate-rejected
  plans make zero power calls. This is bounded control-flow evidence, not a time or memory theorem.
- Added a warning-free, reproducibly rendered LaTeX/PDF executable-assurance paper for the
  exact-count SxPID2 certifier. It derives the count-table specification, exact lattice transfer,
  conditional directed-enclosure theorem, dyadic and sign semantics, resource argument, 494-table
  qualification boundary, 34-mutation inventory, retained negative counterexamples, trusted
  computing base, and implemented independent-checker route. The paper explicitly excludes `pid-core`
  binary64 refinement, statistical confidence, continuous PID, and downstream authority claims.
  The formal-tool adoption record is reconciled with the implemented source-only lane and keeps
  Kani, Verus, Rocq Interval, and Aeneas as distinct future assurance layers, while documenting
  the now-implemented independent integer/Fraction rational-log containment checker as bounded
  executable evidence rather than formal verification.
- Added a closed machine-readable ecosystem capability and gap contract for exact historical
  snapshots of Prisoma, Galadriel, Haldir, and Crebain. It binds the method catalog, assurance
  registry, release scope, and retained repository snapshot by raw digest. The generated human
  matrix records local method maturity, assumptions, limitations, present and missing evidence,
  owned gaps, evidence paths, and negative challenges. All consumer integrations remain
  `not_claimed`; current compatibility, integration, qualification, operational validation, and
  application validity remain outside the claim. A reviewed semantic projection binds the
  source-derived needs, evidence obligations, responsibility assignments, retained boundaries,
  assumptions, limitations, exact present and missing evidence paths, and the bound authority
  records and digests. A 70-mutation fail-closed suite runs in CI.
- Added a new project-defined
  [mathematical problem-solving and blind-benchmark workflow](MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md).
  It summarizes the inspected external problem-solving sources and then defines versioned exact
  claims, obligation graphs, independent approach records, retained counterexamples, certificate
  conversion, five-category adversarial review, claim-to-evidence separation, and a pre-access
  holdout commitment. The commitment records source, generator, sealed-input, role, failure,
  independent-time, and first-result identities. It now also defines role-separated model runs,
  frozen run context, evidence labels, route memos, full semantic closure, an exceptional-case
  checklist, and layered go/no-go gates. A reviewed
  [correctness-audit intake](audit/evidence/correctness-audit-intake-2026-07-24.md) records source
  digests, conversion QA, adopted controls, rejected evidence substitutions, and unreplayed
  recommendations. A typed citation-edge application now retains the corrected vector-bundle
  source-arrow failure, immutable source spans, blast radius, exact finite `C2` countermodel, and
  fail-closed mutations. A pinned Lean/Mathlib artifact independently checks the same witness at
  the implementation layer through three image/kernel equalities, right-arrow bijectivity and
  surjectivity, adjacent-arrow negative conclusions, and nontriviality; five semantic proof
  mutations fail closed. The Python and Lean artifacts are explicitly one mathematical route,
  not two independent counterexamples, and neither formalizes motivic homotopy or any PID claim.
  The workflow is documentation. It is not estimator code, a proof of the imported theorem, a
  completed benchmark, automated enforcement for every future claim, or evidence that a
  scientific claim is correct.
- Added the project-defined `pid_runlog::experimental::schema3` Rust module. It contains checked
  types for a possible future scientific-outcome contract. The types record method classification,
  analysis plans, request ledgers, data lineage, split and support declarations, separate
  scientific gates, stage facts, named outputs, and numerical invariants. A typed validator checks
  exact terminal-outcome coverage for one request ledger with at most 1,024 entries. Failed reports
  do not change its counts. Three public encoders implement the supported matrix and split byte
  contracts. Schema 2 remains the active wire format. No schema 3 event, reader, replay path,
  sidecar, CLI path, or migration exists. This change adds no PID measure or estimator and no
  statistical interval-coverage procedure.
- Added `pid_core::software_identity()` and matching root/stable Python bindings. The closed typed
  envelope separates proposed-profile public Rust declaration-signature revision, package-safe
  source identity, selected build context, exact-byte forensic references, and an explicit `none`
  attestation state. This is project-defined software infrastructure with local code and no
  estimator-paper or scientific-novelty claim; schema, package, feature, serialization, Git/Cargo
  route, Rust/Python parity, and fail-closed mutation checks run in CI.
- Added a repository-history-relative public Rust declaration-signature registry with immutable
  revision-scoped snapshots, exact generation metadata, monotone source ancestry, and mutation
  checks. It binds declaration evidence only: it is not a cryptographic signature, compatibility
  proof, authenticity claim, external transparency log, or scientific-validity result.
- Added an authoritative method-provenance catalog and generated human matrix that distinguish
  paper-defined methods, paper-derived compositions, project-defined diagnostics/engineering,
  external reference code, and explicit non-implementations. Rust source markers, audience-specific
  documentation, scientific error/report wording, citation guidance, and a coherence checker now
  expose paper, code, feature, validation-boundary, and repository-contribution status without
  treating “new in pid-rs” as a claim of scientific novelty.
- Added a closed, machine-checkable review-evidence gate: a five-layer assurance, assumption, and
  gap registry for all 37 release-scope families; explicit dispositions for every `T000`–`T158`
  handoff task with zero 1.0 completions claimed; and an exact 21-column inventory of the 186 files
  in the immutable 0.9 tag. Bounded 0.9 implementations are distinguished from full task
  qualification, while the inventory explicitly remains unassigned and unreviewed. Canonical
  generation, schema validation, tag/blob/digest binding, and failure-injection tests run locally
  and in CI alongside standalone high-precision oracle corpora for 494 categorical SxPID2 count
  tables and 8,198 KSG local-arithmetic cases.
- Added three digest-pinned Z3 4.16.0 QF_LRA obligations for bounded two-source PID algebra, plus
  mutations that make each obligation satisfiable and verify fail-closed rejection. The recorded
  scope is limited to exact-real four-atom reconstruction, formula-level source exchange, and
  four-node Möbius inversion; no estimator, floating-point, or higher-source proof is claimed.
- Added two digest-pinned Z3 4.16.0 QF_LRA obligations for the complete 18-node PID3 lattice. They
  prove exact-real Möbius inversion, zeta reconstruction, and formula-level equivariance for two
  adjacent source swaps. The swaps generate all source permutations for three sources. Mutations
  make both obligations satisfiable and verify fail-closed rejection. These bounded proofs do not
  prove an estimator, asymptotics, Rust refinement, floating-point behavior, distributional
  properties, or a four-source lattice. The release audit and CI coherence gate run both the exact
  obligations and their mutation suite.
- Added a [finite-alphabet plug-in convergence](FINITE_ALPHABET_PLUGIN_CONVERGENCE.md) note as new
  project-defined theoretical validation. It proves exact-real convergence on fixed finite
  alphabets for SxPID with 2–4 sources, `I_min` with 2–3 sources, and selected Shannon invariants
  under i.i.d. or strictly stationary and ergodic sampling. It also gives local continuity bounds, a
  time-uniform i.i.d. envelope from Hoeffding's inequality and union bounds that needs known
  `p_min`, and a conditional corollary for frozen transforms. A training artifact must be
  independent of the raw evaluation sequence. The frozen map must be measurable with respect to
  the training sigma-field and raw input. It must return a valid finite output with conditional
  probability one. Evaluation rows must be conditionally i.i.d. given the training sigma-field. A
  pinned Lean project checks a deterministic continuity core plus finite keyed-event and
  fractional-cover modules. Its checker inventories all 225 source declarations, audits all 177
  source theorem axiom bases, and separately compiles ten digest-pinned paper-facing semantic
  examples. A fail-closed self-test kills seven source mutations for their intended reasons,
  including a heterogeneous-key regression that leaves the expected type text only in a comment.
  An independent 100-digit Decimal generator and Rust test check a bounded
  corpus. The note retains its derivations, counterexamples, and rejected stronger claims. The
  result also has a standalone LaTeX paper and a checked PDF rendering. The work does not prove
  binary64 asymptotics, dependence or drift guarantees, same-row fitting,
  general calibration, or scientific novelty. The method and implementation origins remain
  separate in [METHODS.md](METHODS.md).
- Added an exact-real
  [support-change-tolerant averaged categorical SxPID theorem](SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md).
  On one fixed complete finite Cartesian-product alphabet and fixed full redundancy lattice, it
  gives explicit total-variation moduli for joint-law-averaged informative, misinformative, and
  signed net cumulatives and atoms across support creation and deletion without a positive
  support-mass floor. Relative to total variation, component and signed-net envelope families have
  worst-case leading coefficients one and two; fixed-system, fixed-atom witnesses show that common
  family coefficients below those values are impossible, while lower-order constants may depend
  on the system. This is not an alphabet-independent or complete-modulus sharpness claim. Retained
  falsifiers rule out a global linear modulus, pointwise boundary continuity, an active-face
  entropy substitution, a signed-residual maximum shortcut, arbitrary truncated-lattice transfer,
  and an alphabet-free modulus. The evidence packet includes revisioned claims and failures,
  standalone LaTeX and reproducible PDF, partial Lean modules for finite-vector algebra,
  heterogeneous keyed events, and the equivalence-union load bound, plus an exact/high-precision
  generator, digest-bound fixture, and bounded stable-API Rust replay. It does not establish
  complete executable refinement, a binary64 interval enclosure, sampling calibration,
  independent review, scientific priority, or consumer validity.
- Added a separate
  [SxPID concentration under a dependency coloring](DEPENDENCY_COLORED_SXPID_CONCENTRATION.md)
  analysis.
  It gives finite-sample and all-prefix empirical-law bounds for a fixed deterministic coloring
  when all complete rows share one common finite law. Complete rows inside each color are mutually
  independent, and dependence across colors can be arbitrary. It also gives an explicit
  average-law drift envelope and a common-support SxPID continuity result. The new project-defined
  validation gives one $\Lambda$ bound for each cumulative informative, misinformative, and net
  term and exact Möbius-row transfer for a general source count. For two sources, redundancy and
  unique information retain $\Lambda$. An exact ordinary-diamond result and a sharp
  conditioned-diamond bound reduce the synergy modulus to $\Lambda-\eta$. Endpoint-specific
  ranges also sharpen the averaged synergy caps. The analysis retains counterexamples to applying
  that refinement to every atom and retains the superseded generic range route. These results
  validate the published functional; they do not define a new PID measure or estimator. The
  displayed envelope proves
  almost-sure exact-real plug-in
  consistency under the sufficient condition $V_n\log(n)/n^2\to0$; its drift envelope also needs
  the explicit bias term to tend to zero. The pinned Lean project checks deterministic lemmas. A
  fraction-exact and 400-digit Decimal standard-library challenge generator and a Rust fixture
  retain counterexamples, all displayed bounds on six committed two-source law pairs, one bounded
  near-tightness case, and one fixed-window law. They also audit all 64 ordered coordinate pairs in
  each of seven conditioned-diamond cases and all nine exact extremal regimes, including zero-lift
  and unnormalized algebra-only boundaries. Two cases attain the refined bound exactly; their
  ratio to the older reciprocal bound is $999/1000$. Each of three counterexamples has valid
  endpoints and exactly one negative componentwise lift. The expanded Lean source set checks the
  algebraic event-gradient coordinates and the exact ordinary-diamond diameter and attainment.
  It checks the exact five-coordinate conditioned-nested diameter and its algebraic
  non-subtraction witness. It checks the exact eight-coordinate conditioned-diamond extrema,
  sharp upper bound, normalized corollaries, and refined logarithmic linearization chain. It also
  checks range transfer, segment floors, and finite-average transfer. It does not formalize
  probability or path integration and does not compose the event layer, complete lattice,
  published sign premise, algebraic coordinates, and averaging into full SxPID atoms. It also
  does not prove Rust refinement or binary64 arithmetic.
  A fraction-exact Rust/Python check independently reconstructs the ordinary-diamond,
  conditioned-nested, and conditioned-diamond exact identities on the rational cases. A
  standalone LaTeX source, reproducible PDF, and fail-closed Markdown-math checker make the
  assumptions and evidence boundaries visible. The Rust fixture distinguishes scale-aware
  reconstruction checks from absolute categorical-output comparisons. Ten refined-modulus and
  six endpoint-ceiling binary64 cases now challenge branch seams, cancellation, ratio rounding,
  exact payload identity, the upper-route floor-ratio endpoint, and overflow near the
  strict-support boundary with normal or subnormal positive floors. The stable upper branch uses
  the represented floor ratio instead of an inverse quotient or two-log subtraction. It enforces
  the proved interval through `nextDown(1/2)` and uses runtime rounding-mode and gradual-underflow
  canaries. The schema-7 numerical records reject unknown fields. The cases use 400-digit
  references for the exact represented inputs.
  This project-defined validation adds no estimator, public API, binary64 theorem, external-review
  claim, or scientific-novelty claim.
- Added a project-defined finite-union small-ball limitation analysis for raw-radius PID3 branches.
  It proves minimum-exponent branch-weight dominance under stated regular expansions. Two analytic
  fixtures check an exact uniform example and show why regular marginal branch masses alone do not
  force a union coefficient. This standard consequence is new analysis in pid-rs, not a new PID
  functional, estimator, or scientific-novelty claim. It does not prove estimator inconsistency.
- Added an experimental typed contract for software-added Gaussian noise. It separates the ideal
  population kernel from each exact finite input and output. It also records the scientific
  purpose, units, stream inputs, generator revision, bitwise changes, resources, and cancellation.
  A declared resampling context does not prove that its indices produced the matrix. This
  project-defined software is new in pid-rs. It is not a new estimator or a scientific-novelty
  claim. The legacy `Jitter` primitive remains a separate unreported migration surface.

### Changed

- Replaced every unsupported named-operator command in Markdown math with GitHub-renderable
  notation. The Markdown-math checker and its mutation suite now reject this blocked command in
  inline and display math.
- Updated the pinned `cargo-deny` action from 2.0.20 to 2.1.1. This action uses
  `cargo-deny` 0.20.2. It fixes a failure that version 2.1.0 caused after it removed the
  `use-git-cli` input.
- Updated the pinned artifact upload and download actions as one compatible pair. Upload action
  7.0.1 keeps the existing archive behavior. Download action 8.0.1 rejects an artifact digest
  mismatch by default and handles direct-file artifacts without forced decompression.
- Updated the pinned GitHub release action from 2.6.2 to 3.0.2. This version runs on Node 24. It
  improves draft reuse, small checksum-file uploads, and release-error diagnostics.
- Updated the pinned build-provenance action from 2.4.0 to 4.1.1. Version 4.1.1 wraps
  `actions/attest` 4.1.1. The existing file-subject inputs and permissions remain valid. This
  dependency update does not issue an attestation.
- Categorical SxPID now uses non-interchangeable `SxPointwiseAtom` and `SxAveragedAtom` values;
  their private informative/misinformative components expose nats-labelled accessors and derive the
  signed net by construction. Serialized atoms and stable Python `SxAveragedAtom` values carry a
  revisioned, project-defined interpretation contract that names the shared-exclusions measure,
  distinguishes a distinct empirical-PMF realization from its uncorrected probability-weighted
  plug-in average, requires the containing coordinate/realization record, and explicitly declines
  standalone intent, causal, fault, per-source-responsibility, measure-independence, and
  population-unbiasedness inferences. Atom JSON keys are now nats-labelled; pointwise records
  replace `prob` with `empirical_probability` and retain `empirical_count`. The published atom
  definitions and estimator numerics are unchanged; this is new API/serialization safety work in
  pid-rs, not a scientific-novelty claim.
- Experimental quantized-SxPID bootstrap results now type the `signed_net_nats` summary separately
  from its averaged-atom estimand, expose atom summaries through a complete/unavailable status,
  and retain the bin count, percentile alpha, every replicate outcome, effective resample length,
  scheme, dependence declaration, seed, and algorithm revision. Replicate failures remain
  inspectable instead of being collapsed into an error after resampling.
- Experimental row-bootstrap schedules now record a digest of the exact ordered resample indices.
  Algorithm revision 2 also separates the schedule stream from each replicate and matrix
  perturbation stream. A change to perturbation scale or an earlier matrix width can no longer
  change later row schedules or unrelated matrix draws. This changes seeded experimental output
  from algorithm revision 1. Provenance now records the original row count for schedule replay.
  This work does not add a calibration theorem.
- `pid-core.infrastructure` advances from contract revision v1 to v2 because typed software
  identity and declaration-evidence symbols were added; no estimator or mathematical definition
  changed. Cargo-package metadata with no explicit dirty flag now reports `unknown`, and inherited
  ambient `CARGO_FEATURE_*` variables no longer masquerade as Cargo activations.
- `exp0` now serializes the typed software-identity envelope under its existing
  `build_provenance` key instead of maintaining a second ad hoc crate/Git/compiler/feature shape.
  Consumers of that nested JSON must migrate to identity format 1; its hashes are forensic
  references and do not attest executable or scientific validity.
- **Typed Exp0 outcomes and separated scientific verdicts.** Optional estimates and diagnostics
  now use explicit `not_requested` / `produced` / `abstained` states with stable reason codes;
  human, CSV, and JSON reports omit numeric fields for unavailable values, while run logs pair
  effective statuses with their scopes and retain complete produced estimates and valid-count
  metadata without fabricating numeric values for unavailable results. The default verdict is
  scoped only to high-dimensional MI/coherence, while `--strict-gate` enforces only curated
  analytic low-dimensional MI recovery. Shared-exclusions atom-measure validation remains
  `not_adjudicated` and atom-estimator validation remains `blocked`; the independent-additive
  scenario's positive redundancy is no longer compared with a measure-mismatched zero target or
  folded into any verdict.
- **Deterministic PID-pair ordering.** Experimental all-pairs PID2 screening validates finite atoms
  and uses descending numeric synergy order with source-index tie breakers, including signed-zero
  ties.

- Isolated feature-only APIs from stable and top-level types. Lorentz geometry now uses
  `experimental::hyperbolic::HyperbolicMetric` and typed KSG, support, distance, intrinsic-
  dimension, distance-concentration, and four-point entry points; enabling research features no
  longer adds variants, fields, or methods to the stable surface.
- Exploratory same-sample quantization functions now return
  `ExploratorySameSampleQuantizedResult<T>`, keeping exact bin-count provenance outside stable
  categorical encoding enums. This is an intentional breaking change to a default-off research
  API; callers can access `categorical_result` directly or consume the wrapper with
  `into_categorical_result()`.

### Fixed

- Limited the symlink-escape test helper to Unix test builds. Windows no longer compiles an unused
  helper under `-D warnings`, so its default and all-feature test jobs can run.
- Release workflow scripts now preserve a Git failure when they set `SOURCE_DATE_EPOCH`. Checksum
  generation writes each manifest outside the directory that it scans and then moves the manifest
  into place. Poll loops and workflow-output writes now satisfy the pinned shell checks.
- Allowed only the exact public API snapshot digest lines in the append-only signature registry
  during secret scanning. Other paths, keys, and line shapes remain covered by the scanner.
- Release-state mutation fixtures now include pending non-ignored files while respecting
  working-tree deletions, and isolate Git routing, configuration, attributes, replacement/graft
  overlays, hooks, and signing. Consequently, `just version-check` exercises new evidence files
  before their evidence commit instead of failing on obsolete tracked paths.
- Public Rust declaration history checks now examine every direct tip parent and every
  HEAD-reachable commit that touched the registry, rejecting buried truncation/reissue and
  merge-side drop/reissue histories. The same gate now classifies generic trait implementations
  across both trait and self types, applies complete-string schema patterns, rejects non-finite
  pseudo-JSON values, strips ambient Git routing/configuration, disables replacement and graft
  overlays, and requires Git's canonical worktree root to equal the repository being checked.
  Declaration regeneration now separates original generation host from an explicit rustdoc target,
  isolates compiler/Cargo configuration, rejects Cargo configuration throughout source ancestry,
  runs Cargo with a minimal environment allowlist, and
  validates raw retained source bytes and modes without Git filters after ignoring replacement refs
  and tar options while rejecting archive-altering attributes, tracked symbolic links, or submodule
  entries. A
  locked metadata preflight now rejects stale dependency resolution and lock mutation.
- Software identity now treats a present but unusable `.git` entry as a fail-closed Git route,
  distinguishes an omitted Cargo dirty flag from explicit cleanliness, ignores inherited
  feature-like environment variables, and checks the complete nested Python `TypedDict` graph.
  The stub gate also binds special-form imports, protected names, exact root/stable call
  signatures and returns, the stable alias, and public exports while rejecting decorators,
  shadowing, conditional redefinitions, executable bodies, and non-field record bodies. Dedicated
  fixtures cover source archives, unborn repositories, SHA-256 Git object identities, wrong or
  noncanonical Git roots, dangling Git entries, and 73
  software-identity evidence mutations.
- Workspace identity invalidation now follows exact primary/linked-worktree Git control files,
  split indexes, config origins, files/reftable refs, bounded attribute locations, and bounded
  `objects/info` metadata while retaining absent recovery watches for incomplete final probes,
  includes, and unsupported ref-storage payloads. Ambient config/ref/attribute routing plus
  replacement and graft overlays are neutralized. Symbolic-ref errors are distinguished from a
  detached or direct ref, and unchanged generated identity bytes are not rewritten. Effective
  `filter` attributes on tracked package paths (including unset, unconfigured, and sentinel-word
  values), `attr.tree`, tracked symbolic links, and tracked gitlinks report `unknown` without
  executing a clean-filter command under the documented stable-repository assumption. Git older
  than 2.45 cannot claim cleanliness; HEAD and status inputs are reread to catch ordinary concurrent
  changes. Home-directory routing inputs are watched, and adversarial fixtures cover route recovery,
  packed refs, reftable worktrees, replacement objects, missing objects, occupied sentinel names,
  and ref-storage payloads. A final build-script equality check aborts if the typed source, workspace
  layout, or bound reference bytes changed after the initial observation but before exit.
- Corrected the stable `I_min` release-scope revision identifiers to include the already-exported
  fitted-quantizer composition. This is a metadata record correction, not a change to the
  Williams–Beer definition or its numerical implementation.
- Corrected historical changelog wording that overstated scientific novelty, validation, and
  Gaussian-comparison scope; the amended entries now distinguish published definitions, bounded
  fixture agreement, descriptive percentile summaries, and fixed-sample comparisons.
- Corrected documentation that implied an explicit observation-noise model was sufficient for
  finite mutual information. Added nondegenerate Gaussian noise gives the declared ideal law a
  smooth positive density with full Euclidean support. Finite MI, iid rows, and estimator
  regularity remain separate assumptions.
- Python migration helpers preserve legacy configuration and structural validation precedence when
  directing hyperbolic MI callers to the typed report path.
- Rebound all compiled public-API snapshots to the exact post-isolation source commit, removed the
  eleven obsolete stable-namespace leak records after proving every feature profile has a zero
  stable-namespace delta, and isolated each source/profile build target so stale Cargo artifacts
  cannot mask or fabricate release-scope drift.
- Release-state failure-injection tests now clear inherited GitHub ref metadata when exercising
  local tag inference, so branch CI and local runs validate the same state transitions.
- The replay CLI integration suite now gates its Unix-only sidecar-path helper import with the
  tests that use it, keeping warning-denied Windows builds clean.

## [0.9.0] - 2026-07-14

This is the first public review release, authored by Sepehr Mahmoudian. As a GitHub source
prerelease, it presents the proposed 1.0 API/scientific boundary so reviewers
can comment before 1.x compatibility is promised. Its attached payload is limited to source, scope
records, review provenance, and checksums; crates.io, PyPI, docs.rs, binaries, SBOMs, and
separate build-provenance attestations are outside this review release. GitHub release immutability
automatically supplies a signed release attestation for its tag, commit, and six attached files. No
software DOI or Zenodo record has been assigned, no downstream ecosystem compatibility is claimed,
and earlier release commits remain reachable through immutable changelog links.

### Changed

- **Quantization provenance now distinguishes source bytes from categorical output.**
  `QuantizationReport::{training_data_hash, transformed_data_hash}` is replaced by the
  domain-separated `training_input_hash`, `transform_input_hash`, and
  `categorical_output_hash`; the last commits to the output labels and matrix shape. The fitted
  quantizer accessor is now `training_input_hash`. Python exposes the corresponding
  `*_hash_sha256` attributes and returns a read-only categorical NumPy array. The existing
  `record_training_data_hash` configuration spelling is retained for source compatibility, but it
  controls only the optional training-input identity.
- **Report and cancellation contracts now describe only implemented behavior.** The KSG report's
  permanently-false `backend_fallback_occurred` field is removed: `neighbor_backend` records the
  backend actually selected and backend failure remains an error. The single
  `SupportContract::intrinsic_dimension` scalar is removed because one number cannot coherently
  describe all required marginal and joint population laws. Sampled four-point geometry and
  symmetric-distance construction gain budgeted, cooperative-cancellation entry points.
- **The complete 1.0 capability boundary is now machine-checked.** The release scope assigns all
  393 direct `pid-core` exports to 34 unambiguous scientific/infrastructure families, records exact
  feature closure and non-claims, and discloses eleven research-feature mutations of stable
  types as blockers rather than promises. Ten pinned `cargo-public-api` profiles, byte-for-byte
  regeneration from both the frozen source commit and working tree, complete activation-profile
  diffs, canonical JSON-Schema validation, per-feature warning-free docs, and source plus
  compiled-signature mutation tests run in the dedicated `release-scope-coherence` CI job.
- **Full-history secret scanning now distinguishes public evidence digests from credentials.** A
  narrowly conjunctive gitleaks allowlist covers only the exact 64-hex
  `api_projection_sha256` lines in the canonical repository-cut JSON and
  `public_api_snapshot_sha256` lines in the pinned release-scope JSON; all other default rules and
  paths remain scanned.
- **Repository-local derived files are ignored without hiding reproducibility inputs.** Rust/fuzz
  targets, coverage/profiling output, Python/PyO3 environments and caches, maturin distributions,
  release staging, local credentials, editor metadata, OS noise, and agent scratch files are
  excluded. Lockfiles, audit/scope records, fuzz corpora, and byte-hashed fixtures remain explicitly
  trackable; native-library patterns are limited to the `pid_core_rs` extension instead of all
  shared libraries.
- **The 1.0 audit now starts from a reproducible five-repository cut.** A standard-library-only
  collector records each public HTTPS checkout's full commit/tree identity, clean status,
  submodules, locks, toolchains, tags, GitHub Releases, Git dependencies, and contract-file hashes.
  The canonical snapshot and its separate collection-time envelope explicitly mark every
  downstream integration `not_claimed`; deterministic and dirty/submodule/short-SHA
  failure-injection checks run in CI.
- **Review-release metadata says what actually exists.** The 0.9 publication is a
  GitHub-only source prerelease: reviewed source, proposed-1.0 scope records, review provenance, and
  checksums, with no crates.io, PyPI, docs.rs, binary, SBOM, separate build-provenance attestation,
  software-DOI, or Zenodo publication. GitHub release immutability automatically supplies a signed
  release attestation for the tag, commit, and six files. The README, release notes, dated CFF, and
  changelog identify the exact review prerelease. The 1.0 material remains explicitly proposed for
  review, and downstream ecosystem compatibility is not claimed. Obsolete pre-review tag refs are
  retired while their commits remain reachable through immutable changelog links.
  `scripts/check-release-state.sh`
  enforces candidate, Git-free review/final source, and direct annotated-tag state transitions; its
  positive paths and failure injections are part of CI. A separate manual review workflow binds
  exact `v0.9.0` to the dispatch-time `main` commit and its tag CI, requires an administrator's
  immutability preflight acknowledgement without storing an elevated secret, safely replaces only
  incomplete drafts on retry, and verifies the immutable six-asset prerelease and automatic GitHub
  release attestation. The heavyweight registry workflow is manual and v1-or-later only. Packaged
  Rust/Python READMEs, Rustdoc, and type stubs
  now identify 0.9 as a review surface proposed for 1.0 without making a 1.x compatibility promise.
  The citation metadata uses the CFF 1.2 dual-license array and is schema-validated in CI with
  pinned `cffconvert` 2.0.0.
- **`sha2` 0.10 → 0.11** (workspace dependency; `digest` 0.11). SHA-256 output is unchanged, so every
  committed content address, fixture digest, and run-log hash stays byte-identical — verified by the
  existing digest-pinned fixture tests. No source changes were required.
- **`criterion` 0.5 → 0.8** (dev-dependency, benches only). `criterion::black_box` is deprecated in
  favour of `std::hint::black_box`; `benches/estimators.rs` now imports it from `std::hint`, which
  keeps the benches building under CI's `RUSTFLAGS=-D warnings`.

### Fixed

- **Run-log manifests and hashes are now source-bound and uniformly bounded.** Path inspection and
  hashing use one open handle; `manifest_for_events` rejects a supplied event trace that differs
  from the file; explicit `RunLogLimits` propagate through summary, replay, logical/canonical hash,
  sidecar, manifest, migration rehashing, and aggregate JSONL-byte output (including record
  newlines); a partial writer I/O failure poisons that writer so retries cannot undercount bytes.
  Public file hashing has a finite default and an explicit ceiling variant. Manifest paths reject
  non-UTF-8 text instead of inventing lossy source identities, while derived sidecar filenames
  preserve raw platform path units. Artifact locations reject malformed or encoded traversal plus spoofing-prone Unicode
  format controls. Replay and the public sidecar writer refuse exact, normalized, hard-link, and
  symbolic-link input/output aliases (including derived sidecar aliases), and replay exit codes now
  distinguish completed semantic negatives from operational failures without reopening a bare-mode
  input for a second compatibility hash pass.
- **Diagnostics no longer publish success-shaped artifacts for a failed strict gate.** `exp0`
  validates output-path aliases before writing, runs the curated strict band before finalizing
  artifacts, records the strict-band metrics and enforcement result, emits a failed run status when
  enforcement fails, and records the complete enabled-feature provenance. PCA fitting now applies
  the caller's resource budget to its fallible allocations, and the multicomponent PLS
  score/weight identity has an explicit regression test and corrected documentation.
- **Python categorical inputs are copied from general sequences exactly once.** This closes a
  check/use race for mutable or hostile sequence implementations. Every NumPy borrow guard is now
  locally scoped to a callback-free bounded shape read or copy before Python signal polling or
  structured-error construction resumes. This prevents both signal handlers and monkeypatched
  exception methods from resizing an array behind a live Rust view or leaving a stale rust-numpy
  borrow key. Locally built review wheels test those contracts alongside immutable quantized
  outputs and the three distinct provenance hashes.
- **Stable `pid-core` consumers no longer inherit the run-log path dependency graph.**
  `pid-runlog` and the direct `same-file` dependency are optional normal dependencies activated by
  `experimental-all`; `pid-runlog` remains a dev-dependency for integration fixtures.
- **Release-state evidence now fails closed on stale or underspecified metadata.** Snapshot v2 has
  a closed schema plus semantic projection checks and reads remote HEAD/tags live, while the exact
  cached-ref/local-tag v1 cut remains digest-pinned and explicitly historical; final-source dates
  receive real calendar validation; the review workflow requires both the original and rerun actor
  to be the owner and records their provenance; the downstream repin helper verifies a clean,
  unreplaced canonical checkout, committed `.gitmodules`, an exact annotated unsigned live-remote
  tag, and the tag's workspace version. A canonical
  handoff-intake record preserves the frozen source, supplied evidence digests, known defects, and
  unresolved human/external approvals without treating them as completed work.
- **The `AGENTS.md` code map was stale and partly wrong.** The module table omitted eleven modules —
  most notably `pipeline.rs` (the entire `experimental::pipelines` surface: permutation nulls,
  Benjamini–Hochberg/Yekutieli FDR, PLS component selection, pair screening) plus `logistic.rs`,
  `hyperbolic.rs`, `hierarchy.rs`, and the kernel layer (`kdtree.rs`, `nn.rs`, `metric.rs`,
  `matrix.rs`, `par.rs`, `stats.rs`, `error.rs`, `distance_matrix.rs`) — and the `discrete_pid.rs`
  row named functions (`discrete_pid2`/`discrete_pid3`) that do not exist; the real surface is
  `imin_pid2`/`imin_pid3`. The table now lists every module with its feature gate, flags that
  `experimental-heuristics` baselines do not estimate the paper functional, the test-topology
  paragraph enumerates the actual `tests/` files, and the local command block and the `just doc`
  recipe (hence `just ci` / `just release-audit`) gain the two
  `cargo rustdoc … --lib -- --cfg docsrs` lines so the docs.rs CI gate is reproducible locally
  (its absence is how the broken gate entered the proposed 1.0 candidate).

- **Rustdoc/docs.rs CI gate could never pass.** `cargo rustdoc … --all-features -- --cfg docsrs`
  fails outright when a package exposes more than one buildable target, which `--all-features` does
  for both crates (the `exp0` bin, examples, benches). Both steps now pass `--lib`. The gate has
  been failing in the proposed 1.0 candidate; the equivalent `cargo doc` command in `AGENTS.md`
  is unaffected, which
  is why it went unnoticed.
- **Content-addressed fixtures broke on Windows checkouts.** Without a `.gitattributes`, git
  rewrote LF to CRLF in the JSON/JSONL test fixtures, so their bytes no longer matched the
  committed SHA-256 digests and both `ehrlich_ksg_matches_pinned_csxpid_on_committed_fixture`
  (`pid-core`) and `schema_one_golden_fixture_is_bounded_and_migratable` (`pid-runlog`) failed.
  Line endings are now pinned to LF, and byte-hashed assets (test fixtures, fuzz corpus) are marked
  `-text` so git never translates them.
- **Python binding test was platform-dependent.** `test_categorical_encoding_is_invariant_to_label_order_and_magnitude`
  fed `np.where(...)` results straight to the bindings; with Python int scalars that yields the
  platform default integer dtype, which is int32 on Windows under NumPy 1.x, while the bindings take
  int64. The dtype is now pinned explicitly.
- **SIGINT-cancellation test flaked on virtualized macOS CI runners.**
  `test_sigint_cancels_and_joins_long_rust_worker_promptly` now samples three post-join idle
  intervals and uses their minimum. A joined worker therefore tolerates an isolated VM scheduling
  spike, while a genuinely orphaned worker still burns roughly the whole of every interval and
  fails the unchanged 0.2 s bound.

## Proposed 1.0 change inventory included for 0.9 review

This review candidate prepares a possible first stable software/API release. “Stable” is deliberately
narrow: empirical
categorical PID, declared fitted quantization, and report-first Euclidean KSG MI form the default
surface. Continuous shared exclusions/PID, partial and full continuous PID3, hyperbolic KSG,
heuristics, hierarchy, and target-adaptive pipelines remain default-off experimental or
research-only features. API stability does not imply universal estimator validity; see
`KNOWN_LIMITATIONS.md` and `MIGRATION.md`.

### Added

- **Narrow 1.0 stable namespace and compile-time research boundary.** Empty default features expose
  empirical categorical PID, fitted quantization, conditional report-first Euclidean KSG, and
  general diagnostics. Continuous shared exclusions/PID, hyperbolic KSG, heuristics, hierarchy,
  mixed-dimensional PID3, and target-adaptive pipelines require individually named default-off
  features; `experimental-all` exists for testing only.
- **Reusable fitted equal-width quantizer.** Training-only `fit` plus held-out `transform` preserves
  exact bin edges, out-of-range policy, data hashes, occupancy, scaling provenance, and resource
  estimates. The result states that the estimand is PID of the quantized variables.
- **Report-first and resource-bounded publication surface.** Stable continuous output carries a
  versioned estimand identity, assumption ledger, support/boundary contract, local radius/count/MI
  quantiles, selected-backend state, warnings, provenance hashes, and memory/operation preflight.
- **Typed normalized Shannon-invariant states.** Average redundancy/vulnerability ratios return a
  `NormalizedInvariantReport` containing the exact definition, unit, numerator/denominator,
  explicit denominator-stability policy, and a defined/undefined status. Empty, non-finite,
  non-positive, too-small, or unrepresentable cases no longer escape as unexplained `NaN` values;
  `exp0` prints `undef` (and an empty CSV field) below its declared information-resolution floor.
- **Stable typed Python API.** Default wheels return result classes, ship `.pyi`/`py.typed`, copy and
  validate arrays before GIL release, poll Python signals while owned workers run, cooperatively
  cancel core work, always join workers before returning, and expose structured input, resource,
  numerical, and unsupported-operation exceptions. Pre-1.0 functions move to
  `experimental.migration` in an explicitly experimental source build.
- **Bounded run-log schema 2 and durable sidecars.** Streaming readers enforce file/line/event,
  string/container/depth budgets; typed PID provenance carries explicit hash identities; atomic
  sidecar replacement fsyncs the file on every desktop target and the parent directory on Unix;
  schema-1 fixtures remain readable. Decoded-event replay/validation, canonical hashing, manifest
  artifact/anchor construction, and JSON writing also enforce finite aggregate budgets and return
  structured errors.
- **Release assurance.** Cross-platform/default/MSRV/individual/all-feature/release/Python CI,
  deterministic property and fuzz corpora, coverage, semver/package review, zero-exception
  cargo-deny, SBOMs, checksums, artifact attestations, migration/limitations/reproduction guides,
  exact pre-registry package-archive compilation, explicit 1/2/3/4/available-thread identity
  fixtures, and a protected-environment release workflow form the 1.0 gate.
- **Categorical-label SxPID inputs.** `DiscreteMatRef` makes label equality—not numeric spacing—the
  contract of `discrete_sxpid2/3/n`. The old equal-width behavior is available explicitly as
  `quantized_sxpid2/3/n`. Results record the input encoding, observed cardinalities, and all
  non-empty source-subset mutual informations. This is a breaking 1.0 API change.
- **Python categorical/quantized split.** Stable `compute_categorical_sxpid*` functions take
  two-dimensional `int64` categorical arrays, while fitted quantizer objects define the explicit
  numeric-binning workflow. Stable calls return typed immutable result classes; deprecated
  pre-1.0 dictionary calls exist only in an explicitly experimental migration build.
- **Reusable experimental Python PLS model.** In the migration namespace,
  `PlsProjector.fit(x_train, y_train, out_dim)` returns a fitted projector that can transform
  held-out rows without target leakage. The compatibility `pls_transform` helper is explicitly
  training-only and absent from ordinary stable wheels.
- **Pinned CI supply chain.** Workflow and pre-commit actions use full commit SHAs; jobs have
  timeouts, repository checkout is non-persistent, maturin/NumPy/pytest are version-pinned, and
  weekly Cargo/Actions/Python Dependabot configuration is present.
- **External continuous-SxPID provenance.** A committed machine-readable fixture regenerates the
  two-source redundancy and all 18 three-source atoms with the authors' public `csxpid` package at
  commit `7bb984611a422cf7944ece68993fe3a27e2eadec`. The generator pins its SciPy kd-tree backend and
  minimal Python environment, records the bit-to-nat conversion, and emits a SHA-256 sidecar; Rust
  tests match every external value within `1e-12` nats.

- **Exact Chebyshev kd-tree for the KSG/`i^sx` hot loops** (`pid-core/src/kdtree.rs`).
  `ksg_local_mi_terms` and `ksg_local_mi_terms_xblocks` now build a kd-tree per space and
  answer k-th-neighbor and inclusive range-count queries with expected sublinear pruning when
  `metric = Chebyshev`, `n ≥ 128`, and joint dimensionality ≤ 16 (axis-aligned pruning
  degenerates in high dimensions, so the brute scan is kept there and for the hyperbolic
  metric). **Outputs are bit-identical to the brute scan** — same Chebyshev fold, the same
  `total_cmp` k-th distance value, the same inclusive counts on the `strict_radius`, and the
  same radius-collapse error. Worst-case queries can still scan the tree, so full-estimator
  complexity remains `O(n²)`. Enforced by
  parity tests that compare every local MI term to the brute backend bit-for-bit on smooth
  and tie-heavy (quantized) fixtures, below and above the activation threshold, plus
  duplicate-data and extreme-coordinate error parity.

- **Dependence-aware resampling nulls** (`PermutationScheme`): `permutation_pid3_with`
  and `permutation_rows_pvalue_with` accept an explicit scheme — `FullShuffle` (the historical
  Fisher–Yates null; exchangeable/i.i.d. rows only), `BlockShuffle { block_size }` (fixed,
  equal-sized block permutations; valid under whole-block exchangeability), or
  `CircularShift { min_shift }`, which rotates the shuffled variable's rows by a seeded
  pseudorandom offset `k ∈ [min_shift, n − min_shift]`, preserving its internal autocorrelation
  exactly (up to the wrap seam) while breaking cross-alignment — a stationary-series surrogate.
  The restricted offsets exclude the identity and do not form a transformation group, so their
  add-one tail fraction is explicitly an **approximate surrogate score**, not an exact
  randomization-test p-value. The original `permutation_pid3` /
  `permutation_rows_pvalue` delegate to `FullShuffle`, and the wrappers remain bit-identical to
  their explicit `_with(FullShuffle)` forms at the same seed. Full/block shuffles and circular
  offsets now use rejection-sampled bounded RNG draws rather than modulo reduction, eliminating
  the latter's minute finite-word bias. `CircularShift` validates
  `min_shift ≥ 1` and `n ≥ 2·min_shift + 1` (at least two distinct offsets), samples those
  offsets with replacement, and reports the resulting `n_valid`-based numerical floor.
  `BlockShuffle` requires `n % block_size == 0` and at least two blocks, so it covers every row
  without a short non-exchangeable tail. Both result types record the selected scheme; callers can
  therefore distinguish p-values from surrogate scores after the result leaves its call site.
- **Signed one-sided permutation alternatives** (`PermutationTail`):
  `permutation_pid3_with_tail` and `permutation_rows_pvalue_with_tail` accept `Upper` (null at least
  as large as observed) or `Lower` (null at most as large as observed) and record the choice in
  their results. Existing wrappers and `_with` APIs remain bit-identical `Upper` defaults. No
  absolute-value or implicit two-sided interpretation is applied to signed PID atoms.
- **Benjamini–Hochberg/Yekutieli FDR adjustments** (`benjamini_hochberg`,
  `benjamini_yekutieli`): step-up q-values for the many-atoms × sources × windows testing this
  crate's permutation p-values invite — closing
  the documented "no multiple-comparison correction" limitation. Missing, non-finite, or
  out-of-range p-values are rejected instead of propagated as unexplained `NaN` q-value sentinels;
  callers must resolve a typed, predeclared family policy upstream rather than drop failures
  post-hoc. BH documents its independence/positive-dependence contract; BY applies the harmonic
  correction for arbitrary dependence at a power cost. Hand-computed fixtures,
  clamping/monotonicity, and failure semantics are covered by tests. Feed either function genuine
  p-values under their stated null assumptions, not restricted circular-shift surrogate scores.
- **Lossless run-log CLI comparisons.** `pid-runlog-replay --compare-v2` and
  `--compare-logical-v3` expose the arbitrary-precision trace generations directly. Bare replay
  summaries now use the library's lossless fallback contract, print v2/v3 hashes, and remain usable
  for valid payload numbers outside finite `f64`.
- **Adversarial PID property suite.** Seeded skewed empirical laws now exercise 2-, 3-, and
  4-source SxPID pointwise parts, every subset down-set, source-permutation equivariance, all 18
  `I_min` cumulatives/atoms, and the Shannon bounds `1 <= Red° <= m` and `0 <= Vul° <= 1`.
- **Fail-closed continuous-support contracts and diagnostics.** `KsgConfig`, `IsxConfig`, and
  `Pid3Config` now require a caller-declared population-support contract. Their default
  `Unspecified` contract rejects estimation; ordinary ambient-coordinate Chebyshev/L∞ continuous
  estimators accept only an explicit full-dimensional absolute-continuity assertion, while standalone hyperbolic MI has a
  separate experimental smooth-manifold assertion. Exact per-coordinate and row multiplicities
  plus marginal/joint k-th-shell radius diagnostics are public in Rust and Python. Exact ties are
  conservatively rejected as incompatible with ideal i.i.d., unrounded continuous-sample
  conditions, while their cause and population support remain unidentified; all-unique finite
  samples are never presented as proof of continuity. This intentionally breaking API/behavior
  change is part of 1.0.
  Exp0 now reports and skips support-incompatible projection baselines (for example, an empty
  CountSketch bucket yielding a constant coordinate) instead of aborting the whole diagnostic or
  weakening the estimator contract; baseline gate cases remain unchanged.
- **Structured KSG provenance reports.** `ksg_mi_report` / Python `compute_mi_report` preserve the
  presented estimate, the unclamped signed estimate, n/k/metric/negative handling/support
  assertion, preprocessing and observation-model
  descriptions, marginal and joint radius/shell diagnostics, and stable warnings. Hyperbolic
  reports additionally require embedding-training provenance and record Lorentz-hyperboloid model,
  curvature `-1`, row-width-derived manifold dimensions, experimental status, and the absence of a
  consistency theorem.
- **Complete continuous-PID2 reports.** `pid2_isx_report` retains the three complete signed KSG
  constituent reports, the complete ISX source-union/radius/count/scaling/overlap report, aligned
  local-contribution covariance, per-atom cancellation/amplification diagnostics, provenance,
  resource accounting, experimental status, and warnings. The covariance is explicitly
  descriptive local-contribution covariance, not calibrated sampling covariance. Split-sample and
  cross-fit report helpers require train/evaluation identities and keep fold coordinates separate.
  `pid3_isx_report`,
  `pid3_isx_partial_report`, and both Python PID3 surfaces likewise require per-variable/observation
  provenance and keep it with experimental status and warnings. Provenance text is caller-declared
  and checked structurally, not independently verified.
- **Report-first continuous co-information.** Pairwise and triplet reports retain every signed KSG
  constituent, compensated alternating sums, cancellation/amplification diagnostics, and explicit
  warnings that co-information is not a PID and same-sample extremum selection is biased.
- **Held-out hierarchy selection.** Same-sample hierarchy calls are screening-only. The explicit
  split API records screening/evaluation IDs and input hashes, family size, selection rule/count,
  evaluates selected PID2 pairs only on the declared evaluation matrices, and supplies no
  post-selection p-values.
  Enabling `experimental-hierarchy` no longer enables or embeds the independently gated full
  mixed-dimensional PID3 implementation.
- **Fitted preprocessing identity.** Standardization has explicit `Drop`, `Error`, `Zero`, and
  `LeaveCentered` constant-column policies; canonical `fit`/`fit_transform` calls require the
  choice and aggregate-budget variants check simultaneous fitted-state plus output memory.
  Standardizer, PCA, CountSketch, and PLS fitted objects
  expose deterministic training/parameter hashes; PLS hashes every fitted mean, scale, weight, and
  loading.
- **Typed resampling, null, and cancellation contracts.** Generic callbacks are fallible and
  resource-declared; dependence/block-length declarations, permutation assumptions/calibration,
  family definitions, seeds, algorithm revisions, and signed tails travel with results. Every
  requested replicate/fold failure is retained and prevents selective-subset summaries. Long-running
  resampling, permutation, PLS-CV/fit, and logistic-fit paths support cooperative cancellation.
- **Dimension-compatible partial continuous PID3.** `pid3_isx_partial` dynamically estimates only
  redundancy nodes whose antichain branches have equal ambient dimensions. For equal-dimensional
  sources specifically, 15 of 18 redundancies and 8 of 18 atoms are available; the remaining
  values carry their exact missing Möbius dependencies—never zeros or imputed values. The
  structured result carries n/k/metric/support/dimension provenance,
  experimental status, and deterministic scientific warnings; the full 18-number implementation
  remains behind its independent research opt-in.
- **Accurately named sampled four-point diagnostics.**
  `sampled_four_point_delta_summary` returns the mean, median, p90, p99, sampled maximum,
  with-replacement Monte Carlo standard error, exact finite-dataset diameter, and normalized
  counterparts. Monte Carlo standard error is undefined only for one draw; tiny negative variance
  roundoff is clamped with a scale-aware bound, while materially invalid variance is an error. The
  historical `gromov_hyperbolicity` wrapper was removed from the compiled 1.0 surface because it
  returned only the sampled mean, not the sup-over-all-quadruples Gromov constant. Exp0 and Python
  expose the accurately named summary.

### Changed

- **Signed KSG estimates are now the default.** `KsgConfig::default()` and the stable Python report
  path use `NegativeHandling::Allow`; `ClampToZero` remains an
  explicit presentation-only transform. This prevents the default API from biasing weak-signal
  estimates upward or hiding finite-sample failures, and avoids accidental clamping before
  algebraic identities or inference. Reports always retain the raw signed estimate, so explicit
  presentation clamping is reversible after serialization. This is a breaking behavior change in
  1.0.
- **Continuous local-term means use deterministic compensated summation.** KSG direct/x-block,
  two-source shared-exclusions, partial PID3 Möbius combinations, and full experimental PID3
  redundancy averages now use Neumaier accumulation in deterministic order. The estimands and
  neighbor searches are unchanged, while cancellation roundoff is reduced and serial/parallel
  evaluation remains bit-identical; frozen outputs can change in their last bits for this
  numerical-accuracy correction.
- **Discrete PID/SxPID reductions are numerically hardened.** Categorical SxPID event
  probabilities now sum exact empirical counts before one division; averaged atoms and the fixed
  two-source, shared three-source, and general Möbius inversions use deterministic compensated
  accumulation. The shared three-source inversion also hardens discrete `I_min` PID. Estimands and
  canonical `BTreeMap` order are unchanged, and the external SxPID references remain matched within
  `1e-12`.
- **Jitter is no longer documented as a generic duplicate repair.** Estimator errors, Rust/Python
  documentation, preprocessing guidance, and resampling docs now state that added noise changes
  the estimated distribution. It is appropriate only under an explicit observation-noise model or
  as a seeded, reported noise-scale sensitivity analysis; otherwise callers should use a discrete,
  quantized, or mixed-support estimator.
- **Continuous shared-exclusions now enforces its small-ball dimension contract.** Two-source
  `isx_redundancy`/`pid2_isx` rejects unequal ambient source column counts; equality remains only a
  necessary guard and does not establish compatible intrinsic geometry or reference measures. The
  full continuous PID3 lattice necessarily includes singleton-vs-pair mixed-dimensional branches.
  The final 1.0 API removes it from default builds and requires the
  `research-mixed-dimension-pid3` compile-time feature (or an explicitly experimental Python
  source build), rather than a runtime Boolean in stable code. The path is retained for
  pinned-reference reproduction and labelled diagnostics, not presented as validated
  mixed-dimensional inference. Full results keep support, ambient dimensions, experimental status,
  and warnings attached instead of returning bare 18-number maps.
  This is a breaking API/behavior change in 1.0.
- **Continuous kNN estimators reject ambiguous positive neighbor shells.** KSG direct/x-block,
  continuous shared-exclusions, and experimental PID3 now require exactly `k−1` observations
  strictly inside the selected positive radius and one on its boundary. Structured
  `AmbiguousKthNeighborShell` errors report the query, radius, and shell counts; brute-force and
  kd-tree paths agree, and parallel execution deterministically returns the lowest-index failure.
  This prevents continuous rank formulas from silently accepting duplicate/quantized distance
  ties. Smooth, previously valid reference estimates remain bit-identical.
- **Same-sample supervised PLS pipelines require an exploratory opt-in.** Both
  `PlsPid3Config` and `PlsDiscretePid3Config` add `exploratory_allow_same_sample_fit`; the
  convenience wrappers reject the default-unacknowledged workflow. Inferential use must fit one
  fixed projector per variable and select hyperparameters on training rows before evaluating
  held-out rows; independently rotated foldwise coordinates must not be mixed into one kNN sample.
  This is a breaking API/behavior change in 1.0.
- **MSRV is now Rust 1.89.** PyO3 and NumPy were upgraded to 0.29, removing the previously ignored
  PyO3 buffer/provenance advisories. Nalgebra 0.35 and simba 0.10 remove the unmaintained transitive
  `paste` dependency, so the 1.0 cargo-deny policy has no advisory exception.
- **Quantized SxPID bootstrap naming is explicit.** `bootstrap_discrete_sxpid2` and its result type
  are now `bootstrap_quantized_sxpid2` and `QuantizedSxPid2BootstrapResult`.
- **Permutation result provenance is explicit.** Both result types retain the selected
  `PermutationScheme`; the per-atom finite count is now named `n_valid` instead of the ambiguous
  `n_perm`, while the result-level `n_perm` remains the requested draw count.
- **Permutation inference is coherent across transformations.** `permutation_pid3_with` and
  `permutation_rows_pvalue_with` retain every requested transform outcome. One failure makes the
  predeclared tail fraction unavailable instead of conditioning on a transform-dependent successful
  subset. Circular-shift results retain their explicitly approximate surrogate interpretation.
- **Bootstrap APIs report descriptive distributions honestly.** `block_bootstrap` and paired/row
  variants require at least two draws, a typed resampling-validity declaration, and fallible
  callbacks. They retain every outcome and expose raw mean, sample spread, and percentiles only for
  the complete predeclared distribution; no generic standard-error or confidence-coverage claim is
  made. This is a breaking API change in 1.0.
- **Deprecated continuous PID3 bootstrap removed.** The old with-replacement `bootstrap_pid3`
  surface is not compiled or re-exported in 1.0. Moving-block replacement duplicates rows and is not
  a generic calibrated KSG/PID interval. Use explicitly declared random-origin subsample
  diagnostics where scientifically appropriate and report their effective-m raw percentiles.
- **Strict kNN radii have one exact meaning.** `tie_epsilon` is now a reserved compatibility field
  that must be exactly zero in KSG, continuous shared-exclusions, and PID3 configurations. Strict
  `< radius` counts use the preceding representable float; subtracting a positive material epsilon
  silently eroded valid neighborhoods. The smallest positive subnormal radius remains valid.
- **More accurate digamma values update estimator last bits.** The recurrence now shifts to 8
  before applying the truncated Bernoulli expansion. Stopping at 6 left approximately
  `9.3e-13` bias in `psi(1)`; the revised implementation matches the analytic integer identity
  `psi(n) = H_(n-1) - gamma` within `5e-14`. Consequently, frozen KSG, continuous-SxPID, PID,
  and dependent bootstrap reference bits change for this scientific accuracy correction.
- **Checked PID2 atom construction.** `Pid2Result::from_estimate` now returns `PidResult` and rejects
  non-finite estimates or overflowing atom subtractions instead of constructing infinities. This
  is a source-breaking API change in 1.0.
- **Fallible original-unit PLS weights.** `PlsProjector::y_weights` now returns
  `PidResult<Vec<f64>>`. A fitted scaled model can remain predictive even when a nonzero
  original-unit weight is smaller than the least subnormal `f64`; the accessor and
  `coefficients()` report that unrepresentability instead of silently returning zero. This is a
  source-breaking API change in 1.0.
- **Fallible original-unit standardization scales.** `Standardizer::inv_std` now returns
  `PidResult<Vec<f64>>` instead of a borrowed slice. The fitted projector keeps a finite scaled
  representation even when an original-unit reciprocal standard deviation would overflow; callers
  that inspect the derived reciprocal must handle that explicit error. This is a source-breaking
  API change in 1.0.
- **Subsample output is labeled as diagnostic.** Random-origin circular-grid subsampling without
  repeated row indices reports raw effective-m-sample quantiles, not an unproved conservative
  confidence interval for the n-sample estimate, and rejects selecting the entire grid because that
  produces a deterministic zero-width pseudo-distribution. `RowBootstrapResult::effective_resample_len`
  records the rounded realized `m`. Block origins and choices use rejection-sampled bounded draws.
- **Run-log sidecars expose lossless hash generations.** The serialized 1.0 `RunLogSummary` and
  `RunManifest` shapes add `trace_hash_v2` and `logical_trace_hash_v3`. Their serde defaults keep
  pre-1.0 sidecars readable, and sidecar verification accepts old files which omit exactly these
  additive fields. Existing unversioned fields retain schema-1 hashes where representable and use
  the corresponding lossless digest only when a generic number exceeds finite `f64`.

### Fixed

- **Categorical and extreme-value correctness.** Empirical categorical SxPID is invariant to
  bijective label changes; equal-width quantization no longer collapses large-offset or
  `[-MAX, MAX]` finite data;
  matrix shapes and resampling arithmetic use checked operations. Net SxPID atoms are formed as
  informative minus misinformative by construction, and union probabilities use a direct support
  scan instead of cancellation-prone inclusion–exclusion.
- **PID and geometry identities survive extreme binary64 scales.** Checked PID2 construction now
  exactly accumulates represented atoms, recovers a finite synergy after overflow or catastrophic
  cancellation when one is representable, and rejects tuples that cannot encode all three defining
  MI identities. Lorentz products use an exact integer superaccumulator with one ties-to-even
  rounding; hyperbolic distance uses a factored rapidity difference and doubled-half-chord staging;
  Gromov diagnostics prevalidate every row and rescale before halving. These changes preserve
  analytic residuals such as `MAX - MAX + 50*MIN_SUBNORMAL`, `MAX² - MAX² + 1 = 1`, final
  subnormal distances, and the exact four-point `delta = 2^-52` fixture instead of returning zero,
  NaN, or a seed-dependent success.
- **PLS, logistic, and quantization avoid representable-result failures.** PLS cross-validation
  accumulates PRESS/total variation in scale-factored coordinates, and PLS affine predictions use
  binary exponent/significand accumulation so a centered overflow can cancel to `MAX` while the
  very next overflowing input is rejected. Constant logistic features reduce exactly to zero-weight
  intercept-only directions. Equal-width quantization computes `floor(fraction * num_bins)` from
  the binary64 significand in `u128`, so bin counts above `2^53` and adjacent subnormals map to the
  intended bins without rounding the integer count through `f64`.
- **Fallible APIs no longer hide capacity panics or dead diagnostic branches.** Distance/hash
  allocations, bootstrap/permutation schedules, and Exp0 seed generation reserve fallibly;
  zero-area matrix concatenation is constant-time, and a finite resample that overflows only after
  jitter is reported as numerical instability rather than a configuration error. Exp0 now treats a
  coherently failed bootstrap/permutation distribution as a gate violation and continues to emit
  the diagnostic summary, replacing the unreachable former `n_valid < n_boot/2` test.
- **Experimental pipelines have aggregate resource contracts.** Bootstrap, permutation, PID2 pair
  screening, and PLS cross-validation expose estimates and `_with_budget` variants; parallel
  resampling charges private worker stacks and simultaneously live resamples. PLS/logistic fitting
  preflights checked products and hard-caps nalgebra solver dimensions, while documentation
  explicitly excludes opaque callback work and nalgebra's internal infallible allocator from claims
  the crate cannot enforce. Heap-owning experimental models/results no longer derive `Clone`.
- **Extreme geometry and jitter scales fail safely.** Lorentz distance validates each upper-sheet
  unit-hyperboloid row and uses the exact hyperbolic-polar half-chord identity, retaining tiny radial
  separations far from the origin without Lorentz or Poincaré cancellation. Unverifiable rows fail
  closed. Distance-concentration moments and row-bootstrap jitter scales are invariant across tiny
  and huge uniform scaling; Gromov sampling draws four distinct rows and rejects zero requests.
  Its seeded sample stream changes because the unbiased distinct-index sampler replaces the former
  modulo/collision-skipping stream, so identical seeds can produce different diagnostic values.
  Box–Muller sampling now redraws only exact zero instead of clamping every uniform draw below
  `1e-12`, restoring the Gaussian tail; rare seeded streams containing such draws therefore change.
- **No successful non-finite fitted models or finite-distribution summaries.** Logistic regression,
  standardization, PLS, distance concentration, Gromov hyperbolicity, KSG kd-tree spans, and
  bootstrap summaries reject overflowing finite inputs instead of returning `Ok` with NaN/∞ state.
  Logistic fitting rejects one-class data, uses scale-invariant logit/gradient convergence, and
  errors on iteration exhaustion. PLS uses scale-safe centering/norms, initializes from the most
  informative target direction regardless of column order, uses a conditioned solve, and reports
  non-convergence. Its prediction path keeps source/target scales factored, so extreme models can
  produce finite predictions even when a standalone coefficient is not representable. Pair
  screening and every bootstrap API propagate estimator failures.
- **Scale-safe preprocessing and diagnostics.** Standardization, PCA, intrinsic-dimension log
  ratios, and degree diagnostics avoid representable intermediate overflow/underflow. PCA rejects
  truncation through a numerically tied eigenspace, preserves tiny variation beside huge constant
  offsets, and all large output allocations fail as errors rather than capacity panics.
- **Discrete MI validates empirical state spaces.** Empty and ragged matrix inputs are rejected,
  and joint states are counted as boundary-preserving row tuples, preventing concatenation aliases
  that could violate `I(X;Y) <= min(H(X), H(Y))`. The plug-in estimate is now accumulated directly
  as `sum p(x,y) log(n n(x,y) / (n(x)n(y)))`, with compensated summation and exact `u128`
  independence products. This avoids entropy-subtraction cancellation beyond `2^53`; only a
  roundoff-scale negative result is restored to the mathematical zero bound, while a material
  negative value reports numerical instability.
- **Run-log schemas are strict and new hashes are lossless.** Event, nested, and sidecar records
  reject unknown fields. New `replay_trace_hash_v2` and `logical_trace_hash_v3` digests preserve
  arbitrary-precision payload numbers, while the older hash generations intentionally reproduce
  their released finite-`f64` normalization so existing sidecars still verify. The new
  `canonical_json_hash_v2` gives payload/config fields a lossless content address; schema-1
  validation accepts either canonical generation and recognizes mixed v1/v2 config anchors. JSON
  writers validate and serialize completely before creating or truncating their destination, so
  NaN/∞ cannot silently become `null` or damage an existing file.
- **Python numeric boundaries remain exact and panic-free.** `distance_stats.pairwise_count` is a
  Python integer rather than a lossy float, and impossible hash-projection allocations raise a
  Python exception.
- **Pair screening validates its requested family.** `screen_pid2_pairs` now requires at least two
  sources instead of returning a misleading successful empty screen for zero or one source.
- **Canonical run-log payload hashes without breaking schema-1 replay hashes.**
  `canonical_json_hash` recursively orders object keys, rejects non-finite floats instead of
  colliding with JSON `null`, and retains its released schema-1 number normalization. Trace hashes
  reject the same invalid values while preserving released replay/logical serialization.
  `logical_trace_hash_v2` removes only an event's top-level wall clock without invalidating old
  sidecars; canonical-v2, replay-v2, and logical-v3 additionally retain arbitrary-precision generic
  JSON numbers.
- **Documentation now matches the guarantees.** The README distinguishes categorical label inputs
  from explicit quantization, scopes the four-atom equation to two sources, describes the Gaussian
  check as a fixed-sample paired Monte Carlo comparison, states kd-tree worst cases, and treats
  run-log digests as internal consistency checks rather than authentication.
- **`discrete_pid` module doc: plug-in `I_min` atoms are non-negative, full stop.** The doc
  claimed finite-sample plug-in atoms "can come out negative even though the population
  values are not" — wrong side of a cross-repo contradiction (prisoma's grandplan §8.1.6 and
  its pytest assert WB non-negativity, and they are right): a pure plug-in computes the
  Williams–Beer decomposition of the empirical (binned) pmf, and WB non-negativity applies to any
  valid distribution, so atoms are non-negative up to scale-aware binary64 roundoff (without a
  universal `1e-15` bound); a materially negative atom indicates a bug. The doc now distinguishes
  the estimator-mixing paths (`pid2_isx`) where small negative atoms *are* estimator error,
  and keeps the true caveat: plug-in atoms are biased/noisy estimates of the population
  atoms.
- **README overclaim**: "permutation tests that respect sample dependence" — the shipped
  permutation null was a full-row shuffle, which the Known-limitations section itself said
  does *not* respect autocorrelation. The highlight now states which scheme respects what,
  while `BlockShuffle` states its whole-block exchangeability condition and `CircularShift` is
  documented as an approximate stationary surrogate.

## [0.4.0] - 2026-07-06

> **Why 0.4.0, not 0.3.1:** this release removes public Python parameters (the no-op
> `negative_handling` from three functions), changes `compute_pid3`'s output key format, and
> changes numerical outputs (CountSketch hash projection for all seeds, moving-block bootstrap
> CIs, bias-corrected Levina–Bickel intrinsic dimension) — breaking under the 0.x
> minor-version convention.

### Fixed
- **`HashProjector` CountSketch sign is now independent of the bucket hash.** Both were derived
  from one `splitmix64` value, so for every even `out_dim` the ±1 sign was a deterministic
  function of the bucket (sign = bucket parity): colliding features always added constructively
  and the sketch degenerated to unsigned feature hashing (for correlated inputs
  `E[‖Pv‖²] ≈ d²/out_dim` instead of `‖v‖²`). The sign now comes from a second, salted splitmix
  stream, restoring the actual Charikar–Chen–Farach-Colton (2002) CountSketch, with an
  unbiasedness regression test. Hash-projected outputs change for all seeds.
- **`bootstrap_pid3` / `bootstrap_rows_stats` now implement the true moving-block bootstrap
  (Künsch 1989).** Both previously drew blocks only from the fixed non-overlapping grid (starts
  at multiples of `block_size`) — a Carlstein-style scheme in which the trailing
  `n mod block_size` rows could never appear in any resample — while the docs cited MBB. Block
  starts are now uniform over all `n − block_size + 1` overlapping positions
  (`⌈n/block_size⌉` blocks, truncated to `n` rows); bootstrap CI values change.
  (`RowResampleScheme::Subsample` keeps the fixed grid — distinctness is what guarantees a
  duplicate-free subsample — and now documents its tail exclusion.)
- **`exp0` computes its MI terms with `NegativeHandling::Allow`.** They feed the
  inclusion–exclusion synergy atom, co-information, and r̄/v̄; the repo convention forbids
  clamping a term before a subtraction, and the previous `ClampToZero` silently biased the
  reported synergy in high-d breakdown regimes. The curated strict-gate band is unaffected.
- **`RunLogWriter::append` refuses events that cannot be read back.** `serde_json` serializes
  non-finite `f64` as `null`, which `read_events` can never parse — a NaN metric silently
  corrupted the log and every replay/validate/compare path failed only after the run was over.
  `append` now round-trips each line before writing and errors immediately.
- **`intrinsic_dimension_levina_bickel` applies the MacKay–Ghahramani (2005) bias correction**
  (`k−2` normalisation instead of `k−1`; now requires `k ≥ 3`). The original pointwise estimator
  is biased upward by `(k−1)/(k−2)` (+12.5 % at the default `k = 10`); returned values shrink
  accordingly. `gromov_hyperbolicity` is redocumented as the mean four-point delta (a lower
  bound on the sup-defined Gromov δ), which is what it always computed.
- **Python API honesty:** removed the no-op `negative_handling` parameter from `compute_pid2`,
  `compute_co_information`, and `compute_invariants` — the core forces `Allow` on all three
  paths (correctly: the Möbius/co-information identities require it), so the knob was accepted,
  validated, and ignored. `compute_invariants` now computes its reported MI terms with `Allow`
  too, so the returned dict satisfies `co_information = mi_s1_t + mi_s2_t − mi_s1s2_t` exactly.
  Only `compute_mi` keeps `negative_handling`. `compute_pid3` now keys atoms by source-subset
  bitmask lists (e.g. `"[1, 6]"`), matching the discrete functions, instead of the `Antichain3`
  Debug dump (an unstable format that leaked internal zero-padding).
- **Test-integrity fixes:** `tests/ksg.rs` Gaussian MI/co-information tolerances (0.35/0.45
  nats) exceeded the analytic effect sizes (0.334/0.389 nats), so a dead-zero estimator passed
  both — tightened below the effect size with explicit zero-collapse bounds. Stale
  pre-correction comments asserting the false "I^sx Red → 0" expectation in
  `tests/gaussian_pid_atoms.rs` now state the fixed-sample ~0.225-nat comparison; a σ=0.7
  comment claiming "~0.9 nats" (closed form: 0.556) was corrected; the misnamed
  `bootstrap_mean_of_gaussian_has_narrow_ci` (uniform data) was renamed.
- **Provenance honesty:** the fixed-data expected values in `tests/isx.rs` / `tests/pid3.rs`
  are relabeled as frozen regression pins of this implementation — their historical csxpid
  attribution left no dataset or invocation artifacts in the repo, so they are not presented as
  external validation anymore (README updated to match; a reproducible csxpid cross-check of
  the continuous estimator remains pending).
- **Citation/doc corrections:** Ehrlich et al. cited as published — Phys. Rev. E 110, 014115
  (2024), DOI in `CITATION.cff`; Kraskov 2004 section cites fixed (§III, not §IV/§II); the
  Barrett-2015 comment no longer calls MMI "the unique PID consistent with the standard axioms"
  (the axioms underdetermine the PID); `pipeline` docs no longer call the continuous `pid3_isx`
  "SxPID"; the stale `n=500` strict-gate rationale now says `n=4000`; `pls.rs` no longer cites
  a nonexistent `findings.md`; a dangling `§8.1.6` citation and a truncated "Williams & Beer
  2010 §;" were replaced with real citations; the README comparison table was corrected (dit is
  discrete-only — no KSG — but does implement SxPID as `PID_SX`; IDTxl ships BROJA and SxPID
  estimators, not `I_min`); "15 functions" → 18 across READMEs; run-log content-addressing
  claims now state exactly which record types carry payload hashes.
- **`exp0 --csv` emits parseable labeled tables.** The strict band previously appended
  36-column case rows directly after the 7-column Gaussian table with no header, and the gating
  band's MI values were absent from CSV entirely; tables are now blank-line separated, each
  with its own header, and the band gate emits its measured-vs-analytic MI rows. The summary
  JSON's 16-hex parameter fingerprint was renamed `param_fingerprint_fnv64` (previously
  `config_hash`, colliding with the run log's incompatible 64-hex SHA-256 `config_hash`).
- **Tooling gates made reachable/faithful:** CI now triggers on `v*` tag pushes so the tag-mode
  version-coherence guard can actually run (fetching real tag objects first); the smoke job
  uses `--locked`; `just lint` no longer excludes `pid-python` from clippy; `just deny` matches
  CI's `--all-features --locked`; `just ci` runs the version-coherence script and documents
  what it skips; `build.rs` resolves git paths via `git rev-parse --git-path` instead of
  hardcoding `../../.git/…` (no more perpetual build-script reruns for registry consumers and
  git worktrees).

- **`hierarchical_pairwise` / `hierarchical_triplet` now honour the PID-identity convention.**
  Every MI term they compute is forced to `NegativeHandling::Allow` (they feed the CI screen and
  the Level-2 atoms — clamping a term before a subtraction broke both identities and made the
  hierarchical CI diverge from `co_information_triplet` exactly in weak-dependence regimes),
  and, when `compute_pid` is set, the KSG/ISX `k`/`metric`/`tie_epsilon` consistency contract of
  `pid2_isx` is enforced instead of silently mixing mismatched neighbourhood geometries. A
  regression test pins the CI identity in a genuinely negative-MI regime.
- **`IsxMethod::DisjunctionFromLocalMi` no longer misattributes its formula to `i^sx`.** Its doc
  presented the unweighted `log(e^{i1}+e^{i2}-e^{i12})` as "the disjunction form"; the true
  shared-exclusions forms are probability-weighted (discrete, MGW 2021) and density-weighted
  with **no** joint term (continuous limit, Ehrlich et al. 2024 Def. 2) — the doc now states
  the implemented heuristic honestly and cross-references the oracle test. `HeuristicSketch`
  also dropped a dead `O(n²)` `(S1,S2,T)` joint-radius pass it computed but never used.
- **Discrete entry points reject empty input** (`discrete_pid2/3`, `discrete_sxpid2/3/_n`
  previously returned a silent all-zero "decomposition" for 0 rows), and `RowCountMismatch`
  errors across `isx.rs`/`pid3.rs` now report the operand that actually mismatches.
- **SxPID axiom coverage:** new tests for MGW 2021 Theorem IV.3 (non-negativity of every
  pointwise atom's informative/misinformative part; canonical gates + random 2-/3-/4-source
  sweeps) and Theorem IV.2 (monotonicity of the cumulative `i^±_∩` down-set sums along the
  full 18-node lattice order); the module doc's false "COPY unique < 0" example was replaced
  (UNQ's uninformative source, `log(3/4) < 0`), the identity-axiom incompatibility is now
  correctly attributed (Rauh–Bertschinger–Olbrich–Jost 2014 for ≥3 sources; BROJA satisfies
  identity + non-negativity at 2), and a garbled AND-gate closed-form comment was corrected
  (`I(S1;T) = 0.75·ln(4/3) = 0.2157615543…`, `Syn = ln2/2`).

- **Triple-check follow-ups:** O-information is now attributed to its originators (Rosas,
  Mediano, Gastpar & Jensen 2019, Phys. Rev. E 100, 032305) instead of being folded into the
  Gutknecht et al. 2025 Shannon-invariants reference (which correctly covers only `r̄`/`v̄`);
  CONTRIBUTING.md's pre-0.3.0 `--strict-gate` description was updated to the curated-band
  semantics; AGENTS.md now says `RUSTFLAGS=-D warnings` applies workflow-wide in CI (not just
  the test job); a leftover temporary audit probe (`examples/audit_tmp_invariants.rs`, whose
  premise the hierarchy fix made false) was removed; `RunLogWriter::append`'s round-trip guard
  gained a regression test (NaN/±inf rejected, nothing written, finite events unaffected);
  the README's Validation/Known-limitations sections were refreshed (Gaussian-oracle wording,
  the no-longer-true "fixed-grid bootstrap" limitation, unambiguous redundant-copy gate), and
  `discrete_sxpid_n` (2–4 sources) is now mentioned in the README feature map.

### Added
- `LICENSE-MIT` / `LICENSE-APACHE` copies in every crate directory, so the published `.crate`
  packages and the Python wheel ship the license texts their metadata declares.

## [0.3.0] - 2026-07-01

### Changed
- Centralised the lint policy in `[workspace.lints]` (`unsafe_code = "forbid"`,
  `rust_2018_idioms`, `unreachable_pub`; adopted by `pid-core`/`pid-runlog`) and demoted five
  over-exposed `pub` helpers to `pub(crate)`. Bumped `anyhow` to clear a RUSTSEC advisory.
- Extended the bit-identical `parallel` (rayon) path beyond bare KSG marginal counting to the
  cost-dominating estimators: continuous `I^sx_∩` (`isx_redundancy`, `EhrlichKsg`), the 3-source
  redundancy loop (`redundancy_for_antichain` in `pid3_isx`), and the bootstrap resample loops
  (`block_bootstrap`, `block_bootstrap_paired`, `bootstrap_pid3`). All use an index-ordered
  collect followed by an index-ordered reduction (RNG streams are still drawn serially), so the
  `parallel` feature stays **`f64::to_bits`-identical** to the serial path.

### Added
- Criterion benchmark suite (`crates/pid-core/benches/estimators.rs`) covering the
  cost-dominating estimators (KSG MI, `I^sx_∩`, PID atoms, discrete SxPID).
- **Published categorical shared-exclusions PID `i^sx_∩` (`sxpid` module).** New
  `discrete_sxpid2` / `discrete_sxpid3` implement the Makkeh–Gutknecht–Wibral (2021,
  Phys. Rev. E 103, 032149) categorical SxPID definition. This added a categorical
  shared-exclusions implementation alongside the separately estimated continuous path; the
  previous categorical PID implementation was Williams–Beer `I_min`, a different redundancy
  functional. Redundancy of an
  antichain `α` is `i^sx_∩(t:α) = log[ P(𝔱 ∩ ⋃_j 𝔞_j) / (P(t)·P(⋃_j 𝔞_j)) ]` (informative
  `−log P(⋃𝔞_j)` minus misinformative `log[P(t)/P(𝔱∩⋃𝔞_j)]`), with `P(⋃𝔞_j)` by inclusion–exclusion
  over collections and standard Möbius inversion on the redundancy lattice (reusing the measure-
  agnostic `discrete_mobius_inversion_3`). Output is **pointwise** (per-realization, signed) *and*
  averaged atoms, each split into informative/misinformative parts. Units **nats**; atoms may be
  negative (never clamped). Exposed to Python as `compute_discrete_sxpid2/3` and the general
  `compute_discrete_sxpid_n` (2–4 sources).
  - **Cross-implementation fixture agreement** (`tests/sxpid_reference.rs`): pointwise atom vectors
    agree with the Abzinger/SxPID reference (`testing/test_gates.py`) for XOR, AND, UNQ, RDN, COPY,
    PwUnq, SUM, the
    **non-uniform** RndErr gate (probability-weighted averaging, independently re-derived), and a
    **multi-dimensional** source; the averaged values match **IDTxl's own**
    `test_estimators_multivariate_pid.py` to `1e-12` (e.g. `shared(AND)=0.12255624891826572` bits,
    3-source HASH `shared=0.1926450779…`, `pairs=−0.22686079…`, `syn=0.24511249…` bits — ×`ln 2`).
    The informative/misinformative split is pinned at the bottom *and* non-bottom lattice nodes, and
    a realization-keyed check guards the realization↔atom assignment.
  - **General `n`-source path** (`discrete_sxpid_n`, `2 ≤ n ≤ 4`, the count IDTxl's SxPID
    supports): same measure over the full antichain lattice, with a brute-force antichain
    enumeration (the 4-source lattice has the correct **166** nodes) and general Möbius inversion.
    Tests check agreement with `discrete_sxpid2`/`discrete_sxpid3` within `1e-12` and
    reconstruction plus exact source-swap symmetry at 4 sources. Raw bootstrap percentile
    summaries for the atoms are available through `bootstrap_quantized_sxpid2`; generic confidence
    interval coverage is not claimed.
  - **Axiom property tests** (`tests/sxpid_axioms.rs`): reconstruction (`Σ_α Π(α)=I(S;T)`),
    self-redundancy, source-swap symmetry, real negativity, and an honest identity-axiom comparison —
    on the two-bit COPY of independent sources `I_min` attributes the maximal **1 bit** of redundancy
    while `i^sx` attributes only `log(4/3)≈0.415` bits (SxPID does **not** force averaged red to 0;
    Rauh et al. (2014) place the identity/non-negativity incompatibility in the multivariate (at
    least three-source) lattice setting; two-source constructions can satisfy both).
- **`exp0` `--strict-band` / analytically-grounded `--strict-gate`.** `--strict-gate` no longer
  enforces a verdict on the default high-dimension sweep (whose `PIVOT`/`NO-GO` is the documented,
  expected outcome). It now enforces `GO` (exit code 3 otherwise) only on a **curated band** where
  `GO` is legitimately expected and is checked against a **closed-form analytic ground truth**: a
  grid of jointly-Gaussian systems at `d=1`, `n=4000` (an analytically checked, low-dimensional KSG
  regime) whose three
  measure-independent MI terms `I(S1;T)`, `I(S2;T)`, `I(S1,S2;T)` must match their Cover–Thomas
  Gaussian values within the existing scale-aware tolerance (Barrett-2015 MMI atoms are printed for
  reference only — I^sx ≠ MMI). `--strict-gate` implies `--strict-band`, which runs and reports the
  band without enforcing. The four synthetic scenarios are still run at `d ∈ {2,4,8}` as a
  **non-gating** diagnostic alongside the band; they are a known non-`GO` regime (a reported finding,
  not a regression) and the gate's tolerances are deliberately not loosened to accommodate them.
- **`tests/gaussian_pid_atoms.rs` — cited analytic and semi-analytic Gaussian PID-atom
  regressions.** The previous Gaussian test covered MI only; this adds bounded regression targets
  for the continuous `I^sx_∩` PID2 estimator. The identical-source construction
  (`S1==S2==T+noise`) is now retained only as an ignored, explicitly out-of-domain singular
  diagnostic; the independent-additive construction (`S1⟂S2`, `T=S1+S2+noise`) checks the
  fixed-seed synergy-dominant regime. The measure-independent MI terms come from the closed-form
  Gaussian-channel MI `I=-½ln(1-ρ²)` (Kraskov 2004; Cover & Thomas). A separate, clearly-labelled
  Barrett-2015 Gaussian **MMI** reference
  (`R_MMI=min(I(S1;T),I(S2;T))`) is a sanity comparison only (MMI ≠ I^sx).
- **Correction — `independent_additive` I^sx redundancy is positive, not zero.** An earlier version
  of `tests/gaussian_pid_atoms.rs` *assumed* `Red→0` for independent additive Gaussian sources
  ("derived, not assumed") and labelled the estimator's stable ~0.22 nats as over-attribution bias.
  That assumption was **wrong**. The bin-width→0 limit of the discrete shared-exclusions redundancy
  is `i^sx_∩(t:{1},{2}) → log[w1·e^{i1}+w2·e^{i2}]` (a probability-weighted average of pointwise-MI
  exponentials), which is **strictly positive** for this system. New
  `tests/sxpid_gaussian_oracle.rs` provides a **fixed-sample semi-analytic comparison**
  (~0.225 nats; closed-form pointwise terms, a finite-sample expectation, and its ordinary Monte
  Carlo standard error) and checks finite-sample KSG `I^sx_∩` agreement at the stated sample sizes
  and tolerances; the discrete `i^sx` values move toward the reference over the documented bounded
  bin range but do not reach it. These finite regressions are not population ground truth and do
  not prove convergence. The false `Red==0` assertion and the "estimator bias" framing were removed
  from `gaussian_pid_atoms.rs`, `bin/exp0.rs`, and `AGENTS.md`.
- **Analytic discrete-PID ground-truth gates (`discrete_pid.rs` tests).** Two canonical
  Williams & Beer (2010) logic gates are now anchored to their closed-form `I_min` PID atoms at
  machine precision (`tol = 1e-9`), on an *exactly enumerated* input distribution (each of the four
  binary `(S1,S2)` states repeated equally, so the empirical law is exact and there is no sampling
  error): **XOR** is pure synergy (`Red=Unq1=Unq2=0`, `Syn=ln 2`, `I(S_i;T)=0`), and **AND** matches
  the derived `H(T)=¼ln4+¾ln(4/3)`, `I(S_i;T)=H(T)-½ln2`, `Red=I(S_i;T)`, `Unq_i=0`,
  `Syn=H(T)-I(S_i;T)` (all values derived in-comment, not tuned). Both also assert the PID identity
  `Red+Unq1+Unq2+Syn=I(S1,S2;T)` exactly.

### Fixed
- **Numerical-stability hardening across estimators & preprocessing:**
  `hyperbolic_distance_lorentz` reformulated to the exact `2·asinh(½·√⟨x−y, x−y⟩_L)` form
  (avoids catastrophic cancellation; coincident far-from-origin pairs now return 0 instead of
  NaN); `PcaProjector::fit` rejects non-finite Gram matrices and eigenvalues at/below a
  rank-aware noise floor (new `Err` returns); `block_bootstrap`/`block_bootstrap_paired`
  validate `alpha ∈ (0, 1)`; scale-relative guards added in the PLS, geometry, and `isx`
  heuristic paths.

- **`discrete_pid3_redundant_sources_dominant` tested the wrong lattice node.** The test read
  `redundancies[6]` and called it "Redundancy", but index 6 (antichain `{{0,1,2}}`) is the lattice
  **TOP**, whose `I_min` is the joint MI `I(S0,S1,S2;T)` — so the old `red > 0.3·I(S0;T)` assertion
  was vacuous (joint MI always exceeds a marginal MI). It now checks the scientifically meaningful
  claims for the near-copy-plus-noise system: the pairwise redundancy of the two near-copies
  (`redundancies[7]`, antichain `{{0},{1}}`) is sizable, the global all-singletons redundancy
  (`redundancies[16]`, diluted by the noise source S2) cannot exceed it, and the TOP node carries
  at least `I(S0;T)`.

- **`pid-runlog` logical trace hash** — `logical_trace_hash` / `logical_trace_hash_from_path`
  digest the ordered event sequence with wall-clock (`timestamp_ns`) fields excluded (the
  run-log filesystem URI/path is never part of an event, so it is excluded by construction).
  Two runs that are logically identical but differ only in timestamps now share the same
  `logical_trace_hash` while their `replay_trace_hash` differs. The hash is surfaced on
  `RunLogSummary` and `RunManifest`, the `pid-runlog-replay` CLI gains `--compare-logical
  <a> <b>` (and prints `logical_trace_hash` in its default report), and a regression test
  (`logical_trace_hash_ignores_timestamps_but_replay_hash_does_not`) pins the contract.
- **`pid-runlog` crash-safe live logging** — `RunLogWriter::sync_all()` / `flush_durable()`
  flush the buffer to the OS and `fsync` the underlying file so already-written events survive a
  crash/power loss.
- **`exp0` build provenance** — a `build_provenance` block (crate version, source git commit or
  `"unknown"`, rustc version, enabled feature set) is added to `exp0`'s run-log `config_json` and
  thereby folded into the SHA-256 `config_hash`, distinguishing source/toolchain configurations.
  This is best-effort metadata, not executable attestation: it omits the binary digest and several
  build inputs. Commit/rustc are captured at compile time via `crates/pid-core/build.rs`.
- `tests/parallel_bit_identity.rs` — a serial==parallel bit-identity guard asserting
  `f64::to_bits` equality (against frozen serial reference bit-patterns) for `ksg_local_mi_terms`,
  the 2-/3-source PID atoms and redundancies, the continuous `I^sx_∩` redundancy, and a
  block-bootstrap result; runs in both the default and `--features parallel` configurations.

## [0.2.0] - 2026-06-20

### Added
- **`pid-python`** — Python bindings (PyO3 + maturin) exposing the `pid_core_rs` module: 15
  functions over NumPy arrays (MI, redundancy, co-information, 2-/3-source PID, discrete PID,
  Shannon invariants, geometry diagnostics, PCA/PLS/hash/standardize preprocessing), an abi3
  wheel for Python 3.11+, a `pyproject.toml`, a pytest smoke suite, and a CI `python` job
  (maturin build + import test on Linux and macOS). `extension-module` is an opt-in feature so
  the plain `cargo` workspace still builds/links without libpython. The crate is distributed as a
  Python wheel (via maturin) and is not published to crates.io (`publish = false`).

### Changed
- Repository moved to `github.com/sepahead/pid-rs` (GitHub account rename); all URLs updated.
- Documentation accuracy pass across every README/markdown file: scoped the `unsafe`-forbidden
  claim to `pid-core`/`pid-runlog`, corrected the `exp0`/`--strict-gate` framing (CI runs `exp0`
  without `--strict-gate`, so it does not enforce a `GO`), and aligned the build/test commands
  with CI.

## [0.1.0] - 2026-06-17

Initial public release.

### Added

- **`pid-core`** — continuous and discrete information-decomposition estimators:
  - KSG mutual information (Kraskov et al. 2004), L∞ joint metric, strict-radius marginal
    counting, optional bit-identical `parallel` (rayon) path.
  - Continuous shared-exclusions redundancy `I^sx_∩` (Ehrlich et al. 2024), disjunction
    neighbourhoods.
  - 2- and 3-source PID atoms (`pid2_isx`, `pid3_isx`) whose Möbius identities hold by
    construction; discrete `I_min` PID over the full 18-antichain lattice.
  - Shannon invariants: co-information, O-information, average degrees of redundancy/vulnerability.
  - Geometry diagnostics (intrinsic dimension, distance concentration, Gromov hyperbolicity),
    preprocessing (standardisation, PCA, PLS, hash projection, seeded jitter), block bootstrap
    and permutation tests, and the `exp0` diagnostic program (a
    GO/PIVOT/NO-GO gate that exits 0 by default; PIVOT/NO-GO is expected at high dimensions, and
    the opt-in `--strict-gate` flag exits non-zero unless the verdict is GO).
- **`pid-runlog`** — versioned, content-addressed run-log schema (per-record SHA-256 payload
  digests, a whole-trace replay hash, and a whole-file SHA-256 manifest; records are not
  prev-hash-chained) with a `pid-runlog-replay` validation CLI.
- Worked example (`cargo run --example ksg_and_pid`), CI (fmt / clippy `-D warnings` / tests /
  docs / MSRV / smoke), and an analytic-reference test suite (Gaussian-channel MI, XOR/COPY PID
  structure, PID identities to `1e-10`).

### Notes

This release incorporates fixes from an internal soundness audit: the default 2-source/
co-information paths no longer clamp MI terms before the algebraic identities; discrete-PID and
Shannon-invariant summation is now order-deterministic (`BTreeMap`); the permutation p-value uses
the add-one correction; and the public pipeline bootstrap/permutation helpers (`bootstrap_pid3`,
`permutation_pid3`, `bootstrap_rows_stats`, `permutation_rows_pvalue`) return `Err` instead of
panicking on invalid configuration (the lower-level `block_bootstrap`/`block_bootstrap_paired` keep
their documented `assert`-on-invalid-config contract). See the current
[scientific cautions](README.md#scientific-cautions) for estimator caveats.

[Unreleased]: https://github.com/sepahead/pid-rs/compare/v0.9.0...HEAD
[0.9.0]: https://github.com/sepahead/pid-rs/compare/ad489f5bf5e15c164c599d069a6bee0f338c0e48...v0.9.0
[0.4.0]: https://github.com/sepahead/pid-rs/compare/78b99531b386344c69f8b822537a6cd38f0addb1...ad489f5bf5e15c164c599d069a6bee0f338c0e48
[0.3.0]: https://github.com/sepahead/pid-rs/compare/85c92c71f6c3e90ddac641d6bc544474727ab842...78b99531b386344c69f8b822537a6cd38f0addb1
[0.2.0]: https://github.com/sepahead/pid-rs/commit/85c92c71f6c3e90ddac641d6bc544474727ab842
[0.1.0]: https://github.com/sepahead/pid-rs/commit/c8357751cccf7b6b6a4b3184c17d2ddf7d09817c
