# Verifier and publication-custody review — 5 September 2026

Disposition: **repair is useful; publication consistency remains open**.

This is an independent-first advisory review of the inherited working changes in the handoff
checkout at branch baseline `ab0c6970050e1b87216fbd0846911143a92c3904`. The reviewer read the
current `AGENTS.md` and `SESSION_HANDOFF.md`, inspected the changed verifier and publication
scripts, and ran the commands recorded below. No repository file was changed by this reviewer.
No archive payload was executed. This report is a scratch coordination artifact until its permitted
content is preserved in an accepted repository record.

The review covers Program-A literal comparison, the SxPID3 PDF builder and its launcher, the
blueprint receipt contract, and current-versus-historical Lean wiring. It is not a review of every
theorem, the complete repository, or the source papers. Root conclusions were not supplied before
the reviewer formed the findings. The parent later requested documentation dependency locators.
Both reviewers share the tool environment, filesystem, project sources and model system. This
review supplies neither human review nor external custody independence.

## Findings that must be resolved before publication

### F1. Blueprint evidence pins do not describe the current files

The actual command

```text
bash scripts/check-pid-discovery-verification-blueprint-pdf.sh --exact
```

returned status 1 before building. Its first diagnostic was:

```text
typed-equality negative evidence identity drifted:
expected f45c44f7ab5e41ef04a63c75453631f16dc89cef0aa5eedea9a0823db77ca5a1,
observed 5ea3d1f818b1ff225d8312d4885df09f5d42bddc657c095806712f8fa536a323
```

This is a causal byte-binding rejection, not a renderer failure. Other known stale fields remain:
the gate declares 30 pages, old source size/digest, old PDF digest and old visual receipt; the
handoff declares that the current PDF has 31 pages. Those later failures were not reached by this
command. Do not describe the current PDF as accepted until the actual visual inspection, receipt
update, exact gate and hostile self-test all finish.

The consistency set includes:

- `PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md` and its root PDF;
- the current visual receipt dated 2026-09-03;
- `scripts/check-pid-discovery-verification-blueprint-pdf.sh`, especially source/PDF/receipt and
  negative-evidence pins, page-count assertions and receipt-scope assertions;
- `scripts/check-pid-discovery-verification-blueprint-pdf-self-test.sh`, including the static
  source-fragment contract around lines 388–407 and page-scope mutations around lines 779–788;
- current SxPID3 correspondence/decision/index/matrix and the machine semantic-bridge record;
- the typed-equality failure record and the checkout-integrity incident record.

Update only current bindings. Historical decision-v2 and archive identities are preserved evidence.
Rehash each exact file after intended edits. A pin update alone does not perform the review named
by a receipt.

### F2. Current Lean operational wiring is stale, and must remain separate from r14

The actual command

```text
python3 -I -S -B scripts/check-lean-toolchain-freeze.py
```

returned status 1 with the first current operational mismatch at `AGENTS.md`: expected
`d234e179bb1e6340bb906126f197b47e20b4bdb3b686d7abe397a202787d8527`, observed
`45c03b361a0b1991cfe90c5fd67442a5ba044353378d5df6957ea68501388cd7`.

A separate static AST inspection, without importing the checker, enumerated exactly three
mismatched entries in `EXPECTED_OPERATIONAL_WIRING_HASHES` at that observation:

| Current operational file | Observed SHA-256 |
|---|---|
| `AGENTS.md` | `45c03b361a0b1991cfe90c5fd67442a5ba044353378d5df6957ea68501388cd7` |
| `CHANGELOG.md` | `6fef34ed8693dae631720e9af0d5903779747c79ab73a47f44a59f311e5ee924` |
| `scripts/README.md` | `6711de3114032c582000e7c76fad5f20857e1e1be8e8ca8156eb15150826aec0` |

These observations will become stale after the parent edits those files. Compute final values
after the document and verifier changes are complete.

The map locations in `scripts/check-lean-toolchain-freeze.py` are consequential:

- `PRESERVED_R14_OPERATIONAL_WIRING_HASHES` starts at line 504; its AGENTS row is at line 512.
  Leave this map unchanged.
- `EXPECTED_OPERATIONAL_WIRING_HASHES` starts at line 664 and overlays the preserved map; its
  current AGENTS row is at line 671. Rebind only the current overlay.
- Receipt validation around lines 2690–2695 still compares r14 to the preserved maps. The split
  checks around lines 2474–2506 constrain current and historical path differences.

The first message sent to the parent accidentally reversed the line labels for the two maps. A
later message corrected that locator error before any edit was requested. The map names and the
explicit locations above are the corrected review finding.

### F3. The handoff's focused list omits two applicable downstream pin dependencies

`scripts/check-ksg-harmonic-revision-v4-preservation.py:60–82` binds the current
`scripts/check-method-catalog.py` hash in `EXPECTED_COMPONENT_SHA256`, then binds the roster.
The inherited catalog-checker edit changes those current bytes. A coherent current-component
rebind and roster update are therefore required before the preservation gate can pass. This must
not change the pinned historical checker, historical source tree, retired lifecycle status, or
expected scientific outputs. The wrapper and its self-test must run after this repair.

`scripts/check-certified-sxpid2-claim.py:173` binds `scripts/README.md` under
`EXPECTED_REVIEWED_DOCUMENTATION_SHA256`. That file is already dirty. Its final current
documentation binding also needs review and update. Preserve the audit-tool README, old receipts,
and actual theorem/evidence boundaries. Follow the claim checker's documented current projection
contract before changing any descendant pin that also binds this checker.

These dependencies were found by source inspection; their full gates were not executed in this
review. They are additional integration dependencies, not newly established mathematical defects.

## Program-A repair assessment

The new `exact_typed_equal` at
`scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py:365` checks concrete type before
value, recursively checks lists and tuples, checks dictionary length, and requires exactly one
type-correct match for each expected key. For the acyclic JSON and Python literal objects used by
this verifier, that construction prevents Python's `False == 0`, `True == 1`, and integer/float
coercions from satisfying the comparison. In particular, the dictionary comparison does not rely
only on Python's coercive key-set equality.

The changed `validate_record` at lines 967–1052 applies this comparator to each verdict-bearing
top-level field, including nested derivation and source/compatibility identities. The compatibility
route at lines 526–595 applies it to the parsed registries. `ast.literal_eval` does not execute the
registry files. Its result types are checked against locally derived integer/string/tuple
objects. Internal arithmetic comparisons outside these input checks still compare locally
constructed integers; the patch does not need to replace every `==` in the program.

The self-test preserves the important causal pattern: mutate the record or compatibility literal,
coherently reseal the affected byte identities, then require rejection at the semantic/type
comparison. It does not claim success from an unrelated digest failure. It also deliberately
accepts the coordinated prose/record/checker reseal boundary diagnostic. That diagnostic correctly
records the remaining owner-controlled-authority limit.

No new correctness blocker was found in this bounded equality repair. Its result is verifier
hardening. It does not change a PID quantity, reconstruct new mathematics, close Program A, create
an externally held judge, or close Programs A–E.

## SxPID3 builder and launcher assessment

The inherited builder patch rejects noncanonical temporary names and escaped parents, records
device/inode identity, and requires publication temporary files to be owned regular files with
one link and zero initial size. It checks that identity before and after copying and before
rename. Those checks directly address the specified hard-link overwrite and same-name replacement
failures. The outer checker starts child Bash processes with `/usr/bin/env -i`, which removes
exported functions as well as `BASH_ENV`; `--noprofile --norc` or an in-script `unset` alone does
not supply that boundary. `EXIT` cleanup and signal exits are separate.

The bounded self-test passed. It reports nine accepted controls, 38 hostile cases, eight source
aliases and five static guards. This review did not perform a full real-tool PDF build, a separate
pre/post Git-object canary, syscall tracing, or a signal campaign. The inherited incident record
clearly limits its one canary observation and leaves causation unresolved. Keep those limits.

Residual limits that are not new findings of universal security:

- `capture_path_identity(..., "directory")` proves current directory type and owner, not that the
  directory was newly created or initially empty. An arbitrary faulty `mktemp` that returns an
  already existing owned directory inside the allowed parent with the accepted basename pattern
  would satisfy that predicate. Freshness still depends on trusted standard `mktemp` semantics.
  The script error text says “fresh-object custody”; do not expand that phrase into a standalone
  freshness theorem. This static observation was not executed as a new hostile fixture.
- Identity checks followed by `cp`, `mv` or `rm` remain separate operations. A concurrent actor can
  race between them. The patch and incident record explicitly withhold a hostile-filesystem
  theorem, which is appropriate.
- The first Bash can process caller startup state before line one. The outermost launch needs a
  clean external environment for the incident's accepted execution protocol.
- `PATH` tools are not authenticated. Clearing the environment does not establish binary custody.
- The blueprint builder and self-test do not receive the same new identity checks and clean-child
  launch changes merely because the SxPID3 builder has them. The response is explicitly scoped to
  three SxPID3 scripts. Do not generalize its safety language to all PDF builders.

Those limits do not invalidate the stated trusted-tool bounded controls. Stronger adversarial-host
claims would require a separate threat model and implementation scope, not additional digest pins.

## Safe entry-document rewrite boundaries

The requested rewrite can simplify entry sections and navigation while retaining the substantive
current policy. A broad deletion based on duplicated prose is unsafe because several paragraphs
also carry operational semantics or exact checker markers.

| Surface | Current dependency | Safe boundary |
|---|---|---|
| `AGENTS.md` | Lean freeze current map and semantic markers | Rewrite entry guidance, preserve the proof/custody and terminal-lifecycle rules, and rebind only current wiring after review. |
| AGENTS r14 paragraph | `check-lean-toolchain-freeze.py:2058–2108` | Retain the r14 leaf, every finalized r6–r13 reference, “execution credit only”, “exists and validates”, and the sequence explanation unless the corresponding meaningful checks receive a reviewed redesign. |
| AGENTS C12 paragraph | `check-lean-toolchain-freeze.py:2193–2233` | Retain exact C12 record name/hash/OID, Q12/R12/L12 outcomes, refusal and preservation commands, “zero new”, and historical-lifecycle label. |
| `CLAUDE.md` | No direct script binding found by the repository-script search | Keep `@AGENTS.md`, one authoritative operational source, unsigned commits, human authorship and evidence firewalls. Add startup guidance without a competing policy copy. |
| Root `README.md` | `check-version-coherence.sh:354–423` and `check-release-state.sh:308–355` | Preserve exact actual release status, GitHub-only registry statement, absent 1.x promise, MSRV and the source-offer/inventory/model-review boundaries. |
| README KSG arithmetic text | `check-ksg-harmonic-revision.py:73–81` | Preserve its outer-box/runtime-image distinction. The old script contains whitespace-sensitive markers. Check which marker path the current preservation wrapper actually runs before removing or moving text. |
| Root README and all changed sources | `check-current-source-state-v1.py:57` and full source projection | Regenerate the self-excluding manifest last. Root README is also in the release-documents subprojection. |
| All three Markdown entries | Markdown math, publication links and review/source inventories | Run applicable text/link gates. The publication-link check validates staged inputs, so an unstaged-only inspection is not the final gate. |

Do not run retired M1a/C9/C12 routes to make historical README or AGENTS constraints pass. Retained
historical scripts and exact-tree replay should remain historical. No progress percentage or
“project finished” claim follows from an entry-document rewrite.

## Ten materially distinct routes considered

These are advisory integration choices. They do not constitute a scientific candidate attempt or
mathematical evidence.

| Route | Assessment |
|---|---|
| 1. Leave the inherited files untouched | Useful preservation baseline, but known stale gates prevent milestone completion. |
| 2. Revert all inherited changes | Reject: loses useful type and filesystem repairs and current scientific corrections. |
| 3. Apply only the Python comparator | Insufficient: leaves causal controls, failure record, current documents and PDF evidence inconsistent. |
| 4. Replace input validation with a JSON schema | Potential separate design; it does not cover parsed Python registries without additional typed contracts. |
| 5. Compare only canonical serialized JSON bytes | Useful transport binding; it does not replace type-aware comparison of parsed Python literals or owner-control boundaries. |
| 6. Freeze all documents to historical r14 bytes | Reject: would restore obsolete operational guidance and misapply historical execution evidence. |
| 7. Rebind every historical and current digest | Reject: destroys evidence separation and can relabel old execution as current. |
| 8. Use only standard software correctness checks without a new PID theorem | Applicable simplest non-PID route: causal parser and filesystem controls repair this engineering defect without scientific overclaim. |
| 9. Redesign all verifiers and PDF builders at once | A later bounded program; too broad for this consistency milestone and supplies no immediate external custody. |
| 10. Finish the coherent current repair packet, review rendered artifacts, rebind current dependencies, replay gates, then verify exact hosted/mainline evidence | Selected route. It preserves useful parts and records failures while keeping the scientific claim open. |

## Fifty hostile review lenses and scoped dispositions

The names below describe review coverage, not fifty independent reviewers or proofs. They share
the sources and execution environment described above. Several remain open outside this task.

| Lens | Finding or boundary |
|---|---|
| 1. Scientific object identity | Comparator repair does not change categorical MGW into continuous Ehrlich PID. |
| 2. Defining source revision | Existing MGW-v5 source record remains bound; the source paper was not reread in this review. |
| 3. Estimand | No new estimand is introduced by exact typed equality. |
| 4. Units | Nats/bit conversion is unchanged; no numerical term was modified. |
| 5. Alphabet | Finite categorical and bounded fixture scopes remain distinct. |
| 6. Population support | No support or continuous-estimator claim follows. |
| 7. Row roles | Input registry repair does not change fit/evaluation/sampling roles. |
| 8. Program status | Exact integer zero and five are enforced; 0/5 remains open. |
| 9. Formal statement identity | No Lean statement changed in the inherited equality patch. |
| 10. Paper-to-formal correspondence | Still open where the current claim says it is open. |
| 11. Formal-to-executable refinement | Literal compatibility is not a refinement theorem. |
| 12. Binary64 semantics | No binary64 improvement or theorem is claimed by these changes. |
| 13. Calibration | No estimator calibration credit. |
| 14. Deployment value | No application or performance credit. |
| 15. Boolean/integer aliasing | Directly rejected by concrete type comparison. |
| 16. Integer/float aliasing | Directly rejected by concrete type comparison. |
| 17. Container shape | Type and length checked recursively. |
| 18. Dictionary-key aliasing | Keys match through typed comparison; coercive set equality is not the comparator. |
| 19. Nested literals | Recursion reaches nested verdict-bearing fields and tuple registries. |
| 20. Optimized Python | Actual optimized-host self-test passed; its child checker runs include normal and optimized modes. |
| 21. Assertions removed by optimization | Changed comparisons use `require`, not runtime `assert`. |
| 22. Arbitrary code execution | Compatibility files are parsed with AST/literal evaluation, not imported. |
| 23. Alternate input routes | Four self-test rejection observations passed. |
| 24. Causal negative controls | Resealed type mutants fail at expected semantic diagnostics. |
| 25. Positive controls | Two Program-A baseline executions and nine builder accepted controls passed. |
| 26. Judge ownership | Coordinated reseal remains an intentionally accepted no-credit boundary. |
| 27. Human review | Not provided by this model review or existing owner-held pins. |
| 28. Institutional independence | Not established. |
| 29. Data independence | No held-out empirical data are supplied by these checks. |
| 30. Initial interpreter custody | In-script clearing cannot undo pre-line-one startup execution. |
| 31. Nested environment | SxPID3 children cross external `env -i` boundary. |
| 32. Exported functions | Builder hostile control passed; cleared in nested launch environment. |
| 33. PATH custody | Trusted-tool assumption remains explicit. |
| 34. Directory containment | SxPID3 canonical parent/name checks reject the tested escaped path. |
| 35. Directory freshness | Still relies on ordinary trusted `mktemp`; identity is not creation proof. |
| 36. Hard-link overwrite | Publication temporary requires link count one; hostile control passed. |
| 37. Symlink aliases | Required-source and output alias controls remain present and passed. |
| 38. Same-name replacement | Device/inode checks narrow the admitted object; check/use race remains. |
| 39. Cleanup status | Cleanup refusal can alter status; no universal signal theorem is claimed. |
| 40. Source preservation | This reviewer made no checkout edits; no full new canary manifest was generated. |
| 41. Incident causation | Unresolved; timing does not identify the PDF script as cause. |
| 42. Negative evidence retention | Four type-coercion observations and incident limits remain recorded. |
| 43. Receipt subject | Blueprint current receipt is stale and must bind the inspected exact PDF/source. |
| 44. Visual scope | This reviewer did not render-inspect pages; no visual pass is inferred. |
| 45. Publication actions | Blueprint gate includes strict action checks; full gate not reached in this review. |
| 46. Reproducibility | Actual new exact two-build PDF evidence remains a parent completion gate. |
| 47. Mutable/historical evidence | Rebind current overlay only; immutable r14 receipt and maps stay fixed. |
| 48. Derived source identity | Manifest regeneration is last and uses two independent output files. |
| 49. Remote publication | No remote or mainline hosted result was observed by this reviewer. |
| 50. Branch retirement | No deletion authorized by this report; fragment dispositions and current retrieval remain required. |

## Exact executed checks

| Command | Actual result |
|---|---|
| `python3 -I -S -B scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4.py` | PASS; 18 nodes, 129 order pairs, 324 zeta entries, 65 nonzero Möbius entries, six source permutations, three compatibility files, Program A partial/open, Programs closed 0/5. |
| `python3 -O -I -S -B scripts/check-sxpid3-mgw-v5-program-a-semantic-bridge-v4-self-test.py` | PASS; two baselines, four alternate-input rejections, 28 record reseals, 12 semantic-source rejections, six raw compatibility drifts, four compatibility reseals, two document drifts, two accepted coordinated-reseal boundary diagnostics. |
| `bash scripts/check-sxpid3-source-marginal-audit-builder-self-test.sh` | PASS; controls=9, hostile_cases=38, required_source_aliases=8, static_guards=5. |
| `bash -n` on both changed builders, both PDF checkers and their shell self-tests | PASS for all six paths. |
| `bash scripts/check-pid-discovery-verification-blueprint-pdf.sh --exact` | FAIL at the typed-equality failure-record hash, before build. |
| `python3 -I -S -B scripts/check-lean-toolchain-freeze.py` | FAIL at the current AGENTS operational binding. |

The shell self-test commands above were invoked in the provided local environment. They are
bounded test observations; they do not claim the stricter clean-external-launch canary protocol
was independently repeated. Remaining gates include normal-host and optimized checker/self-test
replays as applicable, current catalog/summary/transfer-ledger checks, current dependency-pin
repairs and tests, both real PDF exact gates, blueprint hostile suite, staged publication links,
the final source-state manifest and post-commit identity workflow, broader applicable CI, and
exact new branch/mainline hosted evidence.

## Later visual review addendum

After the verifier report, the parent requested an independent read-only visual inspection. The
reviewer read the PDF skill and inspected the existing 300-dpi PNGs at original detail for
physical PDF pages **1, 3, 9, 12, 14, 15, 16, 17, 18, 19, 20, 22**. The render root was
a temporary rendering directory; these machine paths are scratch locators, not portable
publication authority. The current PDF was independently hashed as
`b82c5a0a400ccb129195c3db6e765c7861605f84710226cedd01246967cca7d7`.

The reviewer also inspected the 120-dpi color and grayscale images for physical pages 9 and 22.
No PDF was authored or rebuilt by this reviewer. Other normal-size pages and the remaining seven
high-resolution pages were assigned to the parent, so this addendum is not an all-page review.

**Final bounded visual disposition: pass for the inspected pages.** No clipping, overlap, missing
glyph, broken equation, cut-off table row, caption collision, or figure-label overflow was
established. Headings, page furniture, figure panels and mathematical notation are readable. The
cover title has widely stretched interword spacing on its first line; this is a cosmetic
typography observation, not a required repair or a false scientific status.

A false visual alarm is retained explicitly. Initial original-detail presentations appeared to
make two historical-table gutters on page 9 and two mutation-table gutters on page 22 disappear.
They also appeared to remove the space in `reporting. An` on page 22. The reviewer sent these as
preliminary concerns, then immediately qualified them when the color/grayscale 120-dpi images
showed clear separation. Exact `pdftotext -bbox-layout` word coordinates from the unchanged PDF
resolved the observations:

| Location | Actual end/start coordinate in PDF points | Separation |
|---|---|---|
| Page 9, row 13, `dependency` to next column | 158.731235 to approximately 175.554 | 16.82 pt |
| Page 9, row 14, `exact` to `Use` | 337.195801 to 352.160000 | 14.96 pt |
| Page 22, Keying row, `permutation` to `stable-key` | 322.707249 to 347.139000 | 24.43 pt |
| Page 22, Factor IR row, `vector` to `normalized` | 330.696116 to 347.138453 | 16.44 pt |
| Page 22, list item 3, `reporting.` to `An` | 179.123269 to 183.546681 | 4.42 pt |

The concerns were retracted. They are not layout defects, and the parent was told not to change
the publication on their basis. This retains a useful review failure: one high-resolution tool
presentation can create a false visual impression; confirm suspected touching text with another
render scale and actual PDF positions before changing a reviewed artifact.

The visual council coverage has the following twenty distinct lenses. These are observations by
one advisory reviewer, not twenty independent reviewers or an accessibility audit.

| Visual lens | Bounded result |
|---|---|
| Hierarchy | Primary and subordinate headings have clear weight/size differences. |
| Typography | Narrative, code and mathematical fonts are legible; cosmetic cover spacing retained. |
| Grid | Inspected table and figure columns have clear actual gutters. |
| Spacing/rhythm | No heading/caption/body collision established on inspected pages. |
| Narrative order | Source/status context precedes mathematical and implementation detail in this subset. |
| Motif provenance | Local header was read; external design-source provenance was not re-adjudicated. |
| Motif coherence | Low-contrast paper grain and related panel textures recur coherently. |
| Ornamental restraint | Body text remains readable above decoration. |
| Palette identity | Observed lapis/turquoise/ivory/pomegranate roles agree with the local header. |
| Pattern/data-semantic separation | Panels use textual labels; no quantity is inferred from texture. |
| Color-redundant labels | Diagram stages and statuses remain explicitly named. |
| Grayscale legibility | Checked directly for pages 9 and 22 only; readable. |
| Real-text extraction order | Selected word coordinates are available; complete logical extraction was not audited. |
| Print fidelity | Renders have no observed clipping; physical print was not tested. |
| A4/profile/embedded fonts | No fresh metadata or font audit in this visual addendum; exact PDF gate remains required. |
| Link/action safety | Not visually provable; requires the actual strict PDF/link gate. |
| Deterministic reproduction | Not established by looking at PNGs; parent must run exact rebuild gate. |
| Source/derived-asset separation | Only read existing PNGs/PDF/header; no derived asset was edited. |
| Portable dependencies | Local header inspected; complete producer dependency audit not repeated. |
| Normal-size/high-resolution inspection | Exact 12-page high set and two-page color/grayscale set stated above. |
