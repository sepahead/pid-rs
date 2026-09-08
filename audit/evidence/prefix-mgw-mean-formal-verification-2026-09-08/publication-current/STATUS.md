# Current mean publication evidence

The categorical MGW mean bridge has three locally accepted exports. This record concerns their publication and replay tooling; it adds no theorem, calibration or deployment result. The [main results](../RESULTS.md) retain the formal statements, full proof history and actual kernel replay.

| Evidence | Actual result | Boundary |
|---|---|---|
| [HTTPS PDF production](https-production/ROOT_PDF_REVIEW.json) | Two builds matched the reviewed nine-page PDF. All pages, text, fonts and annotations were inspected. | Repository-main HTTPS is navigation, not immutable provenance. |
| [Public builder](builder/ROOT_REAL_BUILD_REVIEW.json) | Normal and optimized invocations each produced two further byte-identical PDFs. | Same-toolchain relation only; no Linux reproduction. |
| [Builder controls](builder-controls-v2/ACCEPTANCE.json) | 224 causal cases and 532 inert tool starts passed. | Inert controls produce no real PDF or proof. |
| [Materializer controls](materializer-controls/ACCEPTANCE.json) | 192 causal cases passed; exact source/archive members and modes were checked. | The approved exact fixture, not a deliberately rebased mutation, supplied the next stage. |
| [Relocated replay controls](relocated-controls/ACCEPTANCE.json) | 198 adapter cases, 218 instrumented entrypoint invocations and 12 supervisor cases passed. | Synthetic compiler dispatch is not Lean execution. Process observations are bounded, not atomic. |

The PDF is `e6950ccb21747578b20a244d00de9d09de3ca6810006422224ccfee2469f0c0d` (162,538 bytes). Its Markdown remains `b8b1244f3b216c30aa5bd69a4a8c1274555fdaf8544c32b09508a09bb892d21e`. The public builder is `4b8509424a2baa580ef336c79eff2e4c4583dcc51a5efa74aca15806b7518d24`; its profile is `e85c572d7221a5a46c1200e9e0dde12f73d50def5a0b5dd5bbaf5e4bd97fe09f`.

The first builder-control source packet sealed 12 seconds late; its [original stop record](builder-controls-v1-source/STOP_RECORD.json) remains late. A separately registered actual control invocation then [failed after 41 matched rows](builder/ROOT_CONTROL_FAILURE.json): its global 0.2-second private timeout killed the Pandoc version probe before the intended producer. The harness correctly rejected that causal mismatch, and optimized controls were not run. The successor changes only the private producer timeout to two seconds and the inert producer delay to four seconds; version probes retain 300 seconds. The production builder, profile and PDF stay unchanged. The later passing control matrix does not change the earlier lateness or failure.

The relocated adapter review found two deliberately supplied mode-2 inputs and two deliberately altered prior candidate files. The entrypoints rejected those exact cases. The [root disposition](relocated-controls/ACCEPTANCE.json) separates them from unexplained corruption; all other declared artifacts matched. Supervisor cases check actual bounded inert processes, including a separate Runtime child group. They do not establish a sandbox, hard real-time bound or complete escaped-process detection.

The [projection map](RAW_TO_PUBLIC_MAP.json) binds every selected original receipt/producer stream to its public projection. Logical host locators replace machine paths; embedded historical hashes still refer to original bytes. Complete fixture trees, private process tables, caches, dependency snapshots and QA images remain retained but are not redistributed. These omissions do not acquire public replay credit.

The [portable builder controls](portable-builder-controls/ACCEPTANCE.json) passed their separate actual 224-case/532-start relocation matrix after extraction of the exact reduced archive. Final repository source/PDF/link gates and exact-commit hosted evidence remain open at this source freeze. Cross-toolchain mode returns status 2 because no Linux mean-PDF relation has been reviewed. Generic convergence, MGW inverse and prefix-probability standalone publications remain separate work. No ordinary receipt authorizes reopening an old clock.
