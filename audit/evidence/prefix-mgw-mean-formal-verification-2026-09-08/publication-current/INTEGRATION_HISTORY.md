# Mean publication integration history

The [first integration check](integration-first-failure.json) failed on 8 September 2026. The new mean PDF dispatch changed the shared formal-PDF gate, but the certified-SxPID2 checker still held that gate’s previous digest. It rejected the mismatch before later checks ran.

The correction updates only the checker’s current support-gate digest and its containing current Lean-freeze digest. The existing certified theorem, historical receipts, mutation policy and certified PDF calls remain unchanged. The [earlier container-rebind record](../../certified-sxpid2-post-publication-container-rebind-2026-09-02.md) explains this current-versus-historical boundary. The failed invocation remains failed; a later passing check must have its own actual result.

This was an incomplete integration dependency map, not a mathematical counterexample. Reconsider the correction if the shared gate weakens an existing obligation or either replacement changes a protected historical binding.

## Native cross-platform invocation on 8 September

The [second integration attempt](integration-platform-failure.json) remains failed. Fourteen top-level commands passed, including the complete native exact PDF set. The fifteenth command, `bash scripts/check-formal-pdf-set.sh --cross-toolchain`, exited 1 at 12:14:19 UTC. The [complete stream projection](integration-platform-projection.json) preserves both aggregate outputs and diagnostics with separate original-byte hashes.

The results-guide gate rejected a symbolic or noncanonical Pandoc component while capturing its producer inputs. Its profile selector and primary PDF build were not reached. Separately, source review found no accepted native Darwin cross profile: the current route requires the reviewed Ubuntu 24.04/Linux producer, and the legacy Linux profile remains incomplete. Resolving the native Pandoc alias alone would not meet those Linux path, renderer and byte conditions. The earlier exact run reproduced the reviewed mean PDF in two builds; it does not convert the failed cross invocation into success.

The continuation must retain the original 15:06:05.117272 UTC local deadline and all prior failures. It may complete source and post-commit identity under a separately reviewed scope, then obtain fresh hosted checks for that exact committed descendant, including the supported Linux cross aggregate. Passing checks at an earlier commit do not transfer. The mean PDF still has no accepted Linux cross relation: the aggregate checks its explicit status-2 refusal. Hosted mean proof replay and Linux mean-PDF reproduction remain open.
