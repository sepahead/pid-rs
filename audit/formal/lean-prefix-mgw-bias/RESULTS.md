# Original acceptance and retained failures

The root accepted exactly five finite-categorical MGW bias families at **09:47:03.769575 UTC on 8 September 2026**. The [public acceptance projection](evidence/campaign/ACCEPTANCE.json) corresponds to raw SHA-256 `e46380b7a2b38cf4969c1996a5256ae7e6bacc4397458bdec9dec41dcadba698`. This packaging stage performed no proof or replay execution and adds no theorem families.

The original campaign began at 08:50:22.612393 UTC with a fixed 20:50:22.612393 UTC deadline, at most 80 development slots, eight full slots and one concurrent wrapper. It closed early after five development and five full-slot attempts. The selected source was the first chronological full fresh semantic/kernel pass. Its original [freeze](evidence/campaign/FROZEN.json), [selection rule](evidence/campaign/SELECTION_RULE.json), [ledger](evidence/campaign/ATTEMPT_LEDGER.json) and [stop record](evidence/campaign/STOP_RECORD.json) retain that history; no clock is restarted here.

| Attempt | Source role | Recorded result | Compilers / fresh kernels | Bias records | Receipt |
| --- | --- | --- | --- | --- | --- |
| 001-development-0 | Scalar development | `failed` | 1 / 0 | 0 | [record](evidence/runs/001-development-0/RESULT.json) |
| 002-development-0 | Join-envelope development | `failed` | 1 / 0 | 0 | [record](evidence/runs/002-development-0/RESULT.json) |
| 003-development-0 | Moment/fiber development | `failed` | 1 / 0 | 0 | [record](evidence/runs/003-development-0/RESULT.json) |
| 004-development-0 | Final signed-bound development | `failed` | 1 / 0 | 0 | [record](evidence/runs/004-development-0/RESULT.json) |
| 005-development-0 | Complete development source | `development_compile_pass` | 1 / 0 | 0 | [record](evidence/runs/005-development-0/RESULT.json) |
| 006-full-0 | Selected, normal Python | `fresh_semantic_kernel_pass` | 30 / 1 | 5 | [record](evidence/runs/006-full-0/RESULT.json) |
| 007-full-1 | Selected, optimized Python | `fresh_semantic_kernel_pass` | 30 / 1 | 5 | [record](evidence/runs/007-full-1/RESULT.json) |
| 008-full-0 | Cosmetic, normal Python | `fresh_semantic_kernel_pass` | 30 / 1 | 5 | [record](evidence/runs/008-full-0/RESULT.json) |
| 009-full-1 | Cosmetic, optimized Python | `fresh_semantic_kernel_pass` | 30 / 1 | 5 | [record](evidence/runs/009-full-1/RESULT.json) |
| 010-wrong-last-target-0 | Actual wrong-final control | `expected_target_rejection` | 29 / 0 | 4 | [record](evidence/runs/010-wrong-last-target-0/RESULT.json) |

[RUN_INDEX.json](RUN_INDEX.json) records every original and public receipt hash, candidate capture/execution identity, timestamp, child count and original artifact count. The [source map](SOURCE_PUBLIC_MAP.json) binds all command records and streams. Counts describe these specific runs; repeated runs and controls are not independent proofs.

## Selected and negative evidence

Attempts 001–004 are preserved compiler/elaboration/linter failures. They concern finite-sum and instance conversions, an unused tactic and missing nonnegativity premise, zero/fiber/decision elaboration, and the final negation/division syntax mismatch. These failures are not mathematical countermodels. Attempt 005 compiled the complete source for development, with no semantic or fresh-kernel acceptance of its own.

The selected candidate is `c945862f2bb64825ad5b754cd6fcd4f32da02c0377f13074d9192b6568e3fb45`. Attempts 006 and 007 passed the complete fresh graph in normal and optimized Python. The exact cosmetic variant is `ac65476b7a101d344fff4fe0f4a9370ef7438b83e63d3854883e205c5ee33481`; it uses only the frozen comment prefix and newline suffix. Attempts 008 and 009 passed the same five records and fresh kernel. Each positive full run has 298 inventoried artifacts excluding its RESULT record.

Attempt 010 captured the selected original but executed the narrowly altered candidate `cb1d67ad0b21a28ba928b0ec690181c00f1c43a730467d5d6f305c49f1c9f50d`. Its final public `mass_floor_bias` declaration has type `True`. The [actual diagnostic stream](evidence/runs/010-wrong-last-target-0/28-compile-PidPrefixMgwBias-SemanticJudge/stdout.log) preserves the raw/alias type mismatches, the first four accepted semantic records and `DNF_JUDGE_TARGET_TYPE`. It failed at the 29th compiler, ran no kernel and has 288 inventoried artifacts excluding RESULT. This expected rejection grants no proof to the altered source.

Four positive full runs and this negative control support one five-family acceptance. The inherited eleven MGW, six prefix and three mean records remain dependency evidence; they are not additional bias results.

## Earlier operational preparation

The campaign was adopted after eight original normal/optimized control suites, covering entrypoint, source-policy, instrumented-attempt and strict-closure behavior. Their 324 reported cases and the original adoption record are retained through [OPERATIONAL_CONTROL_ACCEPTANCE.json](evidence/campaign/OPERATIONAL_CONTROL_ACCEPTANCE.json). The package includes those eight summary receipts, with raw/public identities in the source map. The full preparation-control artifact corpus is omitted and remains in its original lane. This stage did not execute those controls or independently replay their complete corpus.

## Publication and trust boundaries

All 316 recorded candidate compiler/kernel stream files are represented. Of these, 311 public stream files preserve the original bytes; five diagnostic streams replace only private source-path prefixes and retain separate original/public hashes. Exact original text preimages remain locally preserved outside the public payload. [OMITTED_INPUTS.json](OMITTED_INPUTS.json) enumerates binary/cache omissions; the [correspondence guide](SOURCE_CORRESPONDENCE.md) explains their limits.

The preserved [root adjudication](evidence/reviews/root-proof-adjudication.json), [independent mathematical critique](evidence/reviews/proof-review-initial.md.txt) and [final mathematical review](evidence/reviews/proof-review-final.md.txt) retain their stated scientific scope and independence limits. They do not turn this new package into an executed portable replay or supply human institutional review.

The full exposition still states the definitions, assumptions, derivations, four hand examples and use limits. No variance, confidence coverage, stopping, dependent-row validity, implementation refinement, continuous/hyperbolic transfer, utility, novelty or superiority result is added. Public/mainline adoption, hosted replay, PDF production and rendered inspection are separate obligations.
