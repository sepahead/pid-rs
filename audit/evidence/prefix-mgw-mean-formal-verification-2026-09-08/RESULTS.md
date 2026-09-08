# Three mean theorems: exact results and publication status

A short-prefix statistic can suggest information that the population does not contain. In the [worked example](../../formal/lean-prefix-mgw-mean/EXPOSITION.current.md), an independent fair sensor and target have mutual information zero, but the horizon-one mean is `1/4`. Substituting elapsed time for target-matching rank also changes the horizon-two answer. These exact symbolic calculations expose two practical hazards: finite-horizon bias and an incorrect sampling denominator. They are not separately executed fixtures or specialized formal theorems.

The accepted bridge connects a specified row statistic to actual finite-law expectations and proves that these expectations approach the categorical MGW atom mean. The law is a normalized PMF on the full finite source-and-target product, with a fresh anchor and iid complete rows; variables within a row may be dependent. Values use natural logarithms and nats. Zero cells and negative atoms are permitted. Fixed quantization defines a categorical estimand; it does not identify that estimand with continuous PID.

For an unknown population, estimating its law or mean remains a statistical problem. The result gives no finite bias bound, sample-size guarantee, confidence coverage, stopping-rule validity or implementation refinement. Held-out task loss, MI/CMI and appropriately defined ablations may already answer a sensor question. MGW is useful to investigate when its particular redundant/unique/synergistic allocation addresses an additional question. No deployment superiority or scientific-priority claim follows here.

## Actual portable replay

The [local acceptance](portable-replay/ACCEPTANCE.json), original SHA-256 `5746ec542928722ca6a712036b9b313054aca0a294c1c840789c474128c7c7ff`, was recorded at **07:41:05 UTC on 8 September 2026**. It replays the same three targets accepted by the earlier campaign; it adds no theorem count. The [root receipt review](portable-replay/ROOT_REPLAY_REVIEW.json) and [STOP](portable-replay/STOP_RECORD.json) retain the execution boundary.

| Actual attempt | Source and Python mode | Observed result |
|---|---|---|
| [001](portable-replay/attempt-001/RESULT.json) | Selected, normal | Complete exact semantic and fresh-kernel pass. |
| [002](portable-replay/attempt-002/RESULT.json) | Selected, optimized | Same full pass. |
| [003](portable-replay/attempt-003/RESULT.json) | Cosmetic, normal | Same full pass. |
| [004](portable-replay/attempt-004/RESULT.json) | Cosmetic, optimized | Same full pass. |
| [005](portable-replay/attempt-005/RESULT.json) | Selected source with deliberately false final target | First two records preserved; actual final raw/alias target-type rejection. |

The four positive runs produced identical mean3/MGW11/probability6 arrays. Together the five runs used 123 compiler/kernel children and five version probes. Only `Classical.choice`, `Quot.sound` and `propext` occur in the accepted transitive axiom arrays. The wrong-final run is a rejection control, not a two-theorem result. [Complete statements and proof correspondence](../../formal/lean-prefix-mgw-mean/SOURCE_CORRESPONDENCE.md) identify exactly what was checked.

The adapter is unchanged at SHA `121068917f2cdc0e3b3098c63869227be9511d7df5f9c011d3d68f980308220a`; its manifest remains `acc59640c0f135063bd58b8827ffc9d058e3d3a82d0e1ab0f980fad881d4b618`. All 48 bound files, including older status prose, retain their accepted bytes. [Current publication navigation](../../formal/lean-prefix-mgw-mean/PUBLICATION.md) explains that boundary and links the separate current exposition. No historical input was repinned to modernize a sentence.

## Controls and publication evidence

The original [control setup failed](controls/original-copy-root-failure/RESULT.json) before any completed case or driver call: copying the sealed fixture root retained mode `0555`. The [successor diff](controls/copy-root-mode-correction.diff) changes only the newly copied fixture root to `0755`; its [mode parity record](controls/copy-root-mode-parity.json) preserves all frozen inputs. The [corrected suite](controls/adapter-controls-current/RESULT.json) matched 198 scored rows across 218 instrumented entrypoint calls. The separate [supervisor suite](controls/supervisor-controls-current/RESULT.json) matched 12 inert cases. These were adopted in the [controls receipt](portable-replay/CONTROLS_ACCEPTANCE.json), with zero proof credit. Cooperative process observation is not atomic and supplies no hard real-time or escaped-descendant guarantee.

The [current Markdown](../../formal/lean-prefix-mgw-mean/EXPOSITION.current.md), SHA `b8b1244f3b216c30aa5bd69a4a8c1274555fdaf8544c32b09508a09bb892d21e`, has a reviewed [nine-page PDF successor](../../../output/pdf/prefix-mgw-mean.pdf), SHA `e6950ccb21747578b20a244d00de9d09de3ca6810006422224ccfee2469f0c0d`. Six actual local productions matched: two producer builds and four public-builder builds across both Python modes. Root inspected all nine successor pages, searchable text, embedded fonts and annotations. The rendered pages and extracted text match the earlier prototype; the changed action is repository-main HTTPS navigation, not immutable provenance. [The current evidence](publication-current/STATUS.md) distinguishes production, controls and remaining integration obligations.

The [earlier prototype](publication-prototype/attempt-04/prefix-mgw-mean.pdf), SHA `b4382567d21f1f353230daad6fcdfb7538a8ecafaaa509ec93ca8c78ecdae01e`, remains preserved because its relative verification URI fails the unchanged publication-link gate. Its [visual review](publication-prototype/ROOT_FINAL_REVIEW.json) retains the original nine-page, enlarged and grayscale inspection. The [retained-rank SVG](../../formal/lean-prefix-mgw-mean/retained-rank.svg) and its open-font PDF derivative keep distinct identities. None of this supplies hosted reproduction, PDF/UA certification or new mathematical proof.

Earlier publication attempts remain evidence: attempt 01 failed with counter/identifier layout issues; attempt 02 split the example table and retained a font fallback; attempt 03 repaired pagination but still used Helvetica despite font-selection probing. Attempt 04 uses the corrected domains, PDF-relative verification link and explicit font backend. [Publication provenance](../../formal/latex/prefix-mgw-mean/PUBLICATION_PROVENANCE.json) identifies all four attempts and the remaining build obligations.

## Original proof campaign and negative history

The original [acceptance](history/ACCEPTANCE.json), SHA `26789c336a5928a07786bc2e1867f600995c09300a1e9b056083349a2fce3fb2`, was recorded at **05:03:36 UTC on 8 September 2026**. Its selected candidate is `17fc2d8fce5ad0ba28cc8348e9348911c393e6eb00515c8139fbd27b85331b6a`; the cosmetic variant is `4dc776110f0db0a370123c011d8fe05e2a0abcf99a55dd1b76c9ec335ed71409`.

| Attempt | Historical outcome | Interpretation |
|---|---|---|
| [001](history/attempts/001-development-0/RESULT.json)–[007](history/attempts/007-development-0/RESULT.json) | Development compilation failed. | Retained proof elaboration/source failures; no full acceptance. |
| [008](history/attempts/008-development-0/RESULT.json) | Development compilation passed. | Intermediate source development, not full three-target acceptance. |
| [009](history/attempts/009-development-0/RESULT.json)–[013](history/attempts/013-development-0/RESULT.json) | Development compilation failed. | Remaining mean-series/source obligations; earlier failures stay in the record. |
| [014](history/attempts/014-development-0/RESULT.json), [015](history/attempts/015-development-0/RESULT.json), [016](history/attempts/016-development-0/RESULT.json) | Development compilation passed. | Attempt 016 supplied the complete selected source; compilation remained distinct from semantic/kernel acceptance. |
| [017 selected normal](history/attempts/017-full-0/RESULT.json) | Exact semantic/fresh-kernel pass. | 25 compiler/kernel children; original result SHA `5b90925ff33db838e3bd33b2301b8172c77f5168e3532841f266ba51ef8493ea`. |
| [018 selected optimized](history/attempts/018-full-1/RESULT.json) | Same full pass. | Original result SHA `6cf40f442047220a55717d9eb0336ae2c44bed1d70d23e503fee3d3ba5a0b2f5`. |
| [019 cosmetic normal](history/attempts/019-full-0/RESULT.json) | Same full pass. | Original result SHA `93f635f05ec08fb97b4a9d4cf3c1f900b986054f3cfac112ab6b8bde8845811e`. |
| [020 cosmetic optimized](history/attempts/020-full-1/RESULT.json) | Same full pass. | Original result SHA `f30ce9c9d0d6107b97668c4c9bc20f2637256c71e2d8c257e5ce7159d2c46688`. |
| [021 wrong final target](history/attempts/021-wrong-last-target-0/RESULT.json) | Actual last-type rejection. | 23 compiler children; original result SHA `9865791a59342b391a6bd982707ecb0a173dfb4a9bea1108b69834560894c7c0`. |

Each retained attempt includes its result, registration, source variants, command records and full bounded stdout/stderr streams, including empty streams. Twelve v2 development failures, four development passes, four full passes and one negative full-budget attempt used 139 actual compiler/kernel children. These are historical counts, not replenished execution allowance or additional theorem counts.

The [earlier v1 attempt](history/prior-v1/attempts/001-development-0/RESULT.json) failed compilation and its original campaign expired. Its [terminal evidence](history/prior-v1/STOP_RECORD.json), failed source and diagnostic stream remain preserved. Later v2 success cannot complete its old deadline or turn a development failure into a mathematical counterexample. Frozen mathematical targets were not weakened to admit the selected proof. Source development and formal proof acceptance are distinguished from an empirical confirmatory experiment.

All four full positive results contain identical three-mean arrays, the accepted eleven MGW/six probability arrays, and fresh `PrefixMgwMeanCandidateRoot` closure. The same-selected-source wrong-target run reaches both actual final raw/alias type mismatches and the inherited judge's `DNF_JUDGE_TARGET_TYPE` marker. That prefix names the reused implementation; its tested declaration is the final mean theorem. It is not a DNF negative control or a separate two-mean-proof result.

## Projection and remaining obligations

[The original projection map](RAW_TO_PUBLIC_MAP.json) and [current projection map](CURRENT_RAW_TO_PUBLIC_MAP.json) bind original raw bytes to public text projections. Repository/home/temporary locators are logical substitutions; embedded historical hashes still describe original bytes. Current portable results, registrations, candidate variants and every bounded command stdout/stderr stream are included. This source review independently rehashed all 1,194 declared artifacts of the five portable attempts. The prior root review supplies its separate complete input audit. Compiled objects, full external caches and the complete inert-control fixture tree are not redistributed. Original raw records remain preserved.

[Dependency provenance](../../formal/lean-prefix-mgw-mean/DEPENDENCIES.md) distinguishes the mean3 closure from inherited generic8, MGW11, probability6 and public DNF13 families. Standalone publication promises for those other packages remain separate. The current note cites MGW's defining paper and explains the bridge; it is not a reproduction of every imported library proof. The full statements, contracts, selected proof, semantic judge and source graph remain linked and inspectable.

The materializer causal checks, relocated adapter/supervisor controls, normal/optimized builder controls and repeated exact PDF production have completed locally. The current evidence records their scope and retained failures. Public integration still needs the final source/PDF inventory, link and applicable hosted checks at the exact final source projection; portable builder-control relocation also passed its separate actual 224-case/532-start matrix. No reviewed Linux relation for this new mean PDF exists; cross mode must refuse with status 2. Current guide/baseline/catalog links and their derived artifacts need reconciliation; regenerate source state last. The [current replay instructions](../../formal/lean-prefix-mgw-mean/REPLAY.current.md) identify executable paths without reopening old clocks. Quantitative bias bounds, empirical-error bounds, Boolean/executable refinement and application validation are outside this three-mean package; acceptance here does not settle those separate obligations.
