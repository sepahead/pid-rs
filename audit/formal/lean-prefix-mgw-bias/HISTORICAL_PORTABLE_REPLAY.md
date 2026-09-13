# Historical local portable replay

This record projects a completed **historical local** replay and control acceptance into the reader package. It is a compact account of retained private evidence, not a raw execution receipt and not a current run. The exact machine-readable record is [HISTORICAL_PORTABLE_REPLAY.json](HISTORICAL_PORTABLE_REPLAY.json).

The historical replay used the 43-input source manifest [replay-proposed-v1.json](replay-proposed-v1.json), SHA-256 `6783dffce953c0e6dd812658af049770b2e63889807acb34f11c75eb4d577b10`. On 2026-09-12, all 43 package-relative files were rehashed in the current assembled package and found byte-identical to the historical portable source layer. This is a current assembly observation. No adapter or proof tool was run to make it.

## Historical result

The local production ran from 2026-09-08 16:40:21.065992 UTC through outer-process completion at 16:58:35.985670 UTC. Its registered deadline was 18:40:21.065992 UTC and was explicitly not a hard real-time guarantee.

| Source and mode | Historical outcome | Private result SHA-256 |
|---|---|---|
| selected, normal | Five exact bias records, then fresh kernel returned zero | `251673d7be66a8cb037793ef561da78f358b6ec6cf2f699bb5fadf5259c09b0d` |
| selected, `-O` | Five exact bias records, then fresh kernel returned zero | `be7c98996b92b60d83e4b13c60407c7f421b1dbc760f99f7e0b1866b9b3d59ee` |
| cosmetic control, normal | Five exact bias records, then fresh kernel returned zero | `026e3b1c975126e26c068797ff2f59702559563408fe081656829d349d821fd9` |
| cosmetic control, `-O` | Five exact bias records, then fresh kernel returned zero | `d6a6fbef668c796880aee4ec6add02fc9f715820d5d9ee21a7ab184f85df6bfa` |
| selected, normal, wrong last target | Four exact bias records, then the last target was rejected | `4ffa5c37c6aa19ea6a99ae5f695145390760e2745bc3cf6d539b0a112a20b11e` |

Every attempt also recorded the exact inherited eleven MGW, six prefix-probability, and three mean target records. The four positives ended with separate recorded `leanchecker --fresh BiasCandidateRoot` commands. The wrong-last mutation changed `mass_floor_bias` to type `True`; the bias semantic judge returned one because it no longer had either frozen last target. Its complete private diagnostic is 2,627 bytes, SHA-256 `bb44cbc34127f012c1924fa37e6cee16e220cd83a3cc6af19961fffb0302b87e`. The negative did not compile the root or run a fresh kernel.

The retained ledger records 158 child commands: 153 compiler or kernel commands and five version probes. The five attempt receipts cover 1,379 artifact records and 572 input records. The production manifest, SHA-256 `d63bd9cb3b49a11f0f4aa8600726cf46039a1d8b393361d002e60bf24dbc93df`, binds 1,537 retained members. These are finite historical receipts. They add zero theorems.

## Historical controls

The controls exercised the actual adapter entry point against synthetic runners and the actual supervisor/runtime against inert bounded child processes. They did not execute Lean and provide no proof credit.

| Control family | Normal | `-O` | Result |
|---|---:|---:|---|
| adapter | 214 records | 214 records | every record matched its expected behavior |
| supervisor/runtime | 24 records | 24 records | every record matched its expected behavior |
| closeout finite checks | 40 cases | 40 cases | 36 expected rejections and four expected acceptances per mode |

The normal and optimized closeout baseline outputs were byte-identical, SHA-256 `8807c0de7dedc795c0e4a466f94390399f3eef8bb63c94b4816692024ea1320f`. The normal and optimized finite-control outputs were also byte-identical, SHA-256 `b3138d051346c7a69b4e09390a33eccbfcaf455514dec4e8fd9deff11e95b012`. Closeout rehashed 63,010 retained artifact entries and 7,936 strict records.

One historical evidence gap remains. Each of the four original control owner receipts says that a terminal state was observed before the deadline and contains no error, but none stores a `returncode` field. A later aggregate record says that all four return codes were zero, and the later closeout calls store their own return codes. Those later records do not reconstruct a per-supervisor return code in the original four receipts. The gap remains explicit and unrepaired.

## Evidence access and negative record

The public package contains no raw private receipt, command tree, process map, compiled object, tool binary, or machine-specific path. The JSON gives opaque locator IDs with exact byte counts, SHA-256 hashes, and roles for the retained evidence. Opening or independently rehashing those objects requires separately authorized access to the private custody set. A digest identifies bytes; it does not authenticate their creator.

The retained negative record includes the wrong-last result and diagnostic, the original control-owner return-code gap, two inspection mistakes recorded during control review (an unmatched-parenthesis command that launched no child and an initially incomplete search scope), expected supervisor failure cases, and five findings from a rejected reviewer assumption about the final in-flight process snapshots. The source-backed post-wait field is the separate terminal `observed_survivors` record. Process samples remain non-atomic observations rather than attestation.

The existing [RUN_INDEX.json](RUN_INDEX.json) and [RESULTS.md](RESULTS.md) describe the earlier ten-run proof campaign and remain unchanged. This later packaging replay does not renumber or replace those runs, change any of the 43 accepted proof inputs, or add a theorem family.

This record establishes no source-to-prebuilt-dependency authenticity, current replay, current native acceptance, hosted acceptance, cross-platform reproduction, exhaustive runtime correctness, scientific novelty, estimator calibration, statistical validity, Rust refinement, or deployment value. The 2026-09-12 source-correspondence observation and preparation of this historical projection ran no Lean, kernel, adapter, control, native, PDF, production, or hosted command.
