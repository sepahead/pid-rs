# Historical Markdown link context

The [exact outer aggregate stderr](LINK_FAILURE_20260912.stderr.txt) from a
12 September 2026 local invocation of `/bin/bash scripts/check-formal-pdf-set.sh --exact`
contains publication-link diagnostics: 48 missing-target findings in the predecessor Markdown,
naming 40 distinct files. It is not a separately captured publication-link child stream or a
complete aggregate receipt, and it does not establish results for earlier or later commands.
The earlier relocation preserved the documents but omitted these relative targets.

[LINK_CONTEXT.json](LINK_CONTEXT.json) binds copies of those 40 files at the expected relative
paths. Each copy is byte-identical to an existing public package leaf and matches the unchanged
[historical manifest](PACKAGE_MANIFEST.json). The copied leaves total 2,087,895 bytes. The
predecessor Markdown, its original manifests, the accepted proof inputs and PDF bytes are unchanged.

This supplies the Markdown links and figures. It does not reconstruct every path recorded inside
the historical JSON, the complete 1,207-file old package, or its replay dependencies. The
[historical-root record](HISTORICAL_ROOT.json) still defines how the old manifest is interpreted.
Use the [current reading guide](../../PUBLICATION.md) and [current source correspondence](../../SOURCE_CORRESPONDENCE.md)
for present claims and execution boundaries. Historical acceptances and failures retain their
original scope; these copies provide no new proof, sampling guarantee or hosted result.

The exact pre-correction [source-correspondence text](../link-context-preparation-2026-09-12/SOURCE_CORRESPONDENCE.md.txt)
and [current package inventory](../link-context-preparation-2026-09-12/PACKAGE_MANIFEST.json.txt)
are preserved separately. The current inventory includes the restored context; the old inventory
and historical source-public mappings are not rewritten.
