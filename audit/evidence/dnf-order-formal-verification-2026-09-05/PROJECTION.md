# Public evidence projection

This packet preserves the exact accepted proof and contract, the exact adopted judge, the
earlier rejected proof, the decisive failed reporting module, complete nonempty command streams,
and portable projections of the seven full-run receipts. It also records both seventy-five-control
preparation runs and the separate reporting regression. It is a selected evidence packet, not a
complete copy of the operator's workspace or every preparation attempt.

The manifest classifies each file. `exact source bytes` and `exact stream bytes` mean that the
public bytes equal the retained source bytes. The accepted Lean source, contract, original v3
freeze and all fifteen bound v3 files retain their exact identities. The original v2 freeze
is also exact. Its [source map](history/judge-v2/source-map.json) names the public file for each
of its thirteen bound inputs. Unchanged files are shared by reference with v3.

JSON projections keep the original structural fields, commands, times, resource observations,
exit codes, theorem records, and declared artifact hashes. They replace machine directory
prefixes with `{REPOSITORY}`, `{LEAN_TOOLCHAIN}`, `{OPERATOR_HOME}`, or
`{PACKAGE_MANAGER_PREFIX}`. These role tokens are documentary values, not executable paths.
Filesystem `identity` tuples are omitted. Temporary locators, if present, are replaced by
`{TEMPORARY_LOCATOR_OMITTED}`. A record's original artifact hash map is named
`declared_local_artifact_inventory` to distinguish it from publicly retained artifacts.

The raw receipt SHA-256 and byte count bind the retained local original. The public file has
its own SHA-256 and byte count. Omitted directory prefixes and filesystem identities cannot be
reconstructed from this packet. This projection does not supply full original-receipt custody.
Empty stdout and stderr streams are represented by the standard empty-byte digest and recorded
zero byte count; separate empty files are omitted. Nonempty command streams are kept in full,
with the same directory-prefix substitution where needed. There is no diagnostic line selection.

Compiled `.olean` files, executable binaries, full local environment records, and copies of
third-party PDFs are omitted. Their recorded local hashes remain observations, not publicly
retained binary artifacts or source-to-binary authenticity. The
[source retrieval record](source-retrieval.json) retains the primary-source URLs, revisions,
reviewed PDF byte counts, and SHA-256 values. The public replay consumes the repository's exact
existing Lean and package pins and produces fresh local artifacts.

The earlier [exposition](history/exposition-before-acceptance/EXPOSITION.md), symbol map,
source correspondence and SVG remain byte-preserved history. Their old pending status and
local-reference wording describe the earlier stage. The current
[exposition](../../formal/lean-sx-dnf-order/EXPOSITION.md) and
[source table](../../formal/lean-sx-dnf-order/SOURCE_CORRESPONDENCE.md) update acceptance status,
source identity and evidence links. No existing publication PDF is changed by this packet.

Historical judge documents contain the commands and proposed allocations that applied when
they were frozen. They are retained to preserve the freeze. Use the current
[lane guide](../../formal/lean-sx-dnf-order/README.md) for public replay. The public launcher has
its own routing manifest; it stages the historical judge without changing the judge's bytes.
It does not relabel the historical freeze as a new pre-candidate registration.
