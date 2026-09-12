# PDF parser dependency update

The current PDF dependency is pypdf 6.16.1. The requirements file pins the exact wheel by SHA-256:
`63fec31c4092ae50b6729beedcb469055b60d20c834bde1c402df241f371f644`.

The maintainer's [6.16.1 release](https://github.com/py-pdf/pypdf/releases/tag/6.16.1)
limits iterations in outline retrieval and XForm text extraction. It addresses the published
[outline advisory](https://github.com/py-pdf/pypdf/security/advisories/GHSA-23w6-3w8w-8484)
and [XForm advisory](https://github.com/py-pdf/pypdf/security/advisories/GHSA-763m-79hh-57f2),
and includes the earlier [tree-insertion fix](https://github.com/py-pdf/pypdf/security/advisories/GHSA-jp53-mhqp-8xcg).
These are PDF tooling changes. No Rust estimator, PID definition or Lean proposition changes.

## Historical evidence and current validation

The [2 September custody receipt](post-publication-custody-2026-09-02.json) records the parser
and builder used for that observation. Its exact bytes and pypdf 6.15.0 version field remain
unchanged. The [original builder](post-publication-custody/builder-pypdf-6.15.0.sh.txt) is an inert
preimage with SHA-256 `5c9e29477fef0d45fcf086a694c3baf72cfc687d87ed1735d244271e236d2cfa`.
The custody checker validates that file against the historical receipt. It checks the active
builder with a separate current hash. Neither builder can substitute for the other.

The current parser guards also apply when a checker reads an old PDF fixture. They identify
the new comparison runtime; they do not rewrite that fixture's production record or establish
a new hosted execution. Frozen replay records, rejected attempts and dated parser observations
keep their original identities. Current operational bindings are separate from the preserved
Lean r14 record and the closed KSG lifecycle records.

The original results-guide v2 checker and self-test keep their exact historical bytes. Their
structure dependency is superseded. The current v2 replay adapter selects the preserved v2
structure explicitly and uses the new parser. Rebinding the original checker would obscure
that distinction; a rejected trial of that route is retained in the local development record.

## Verification scope

The full PDF check requires this exact parser version. The standalone results-guide and
SxPID3 source-marginal PDF commands also check the version before parsing figures or building
documents. These checks assume a stable interpreter, package and command path during execution.

Five added custody controls reject corruption or substitution of either builder and reject
rewriting the historical parser version. Existing publication controls remain applicable:
strict object and action checks, portable staged links, warning handling, fixture comparisons,
normal and optimized Python modes, and exact PDF reproduction. Parser compatibility requires
these checks on the changed source and declared dependency; a matching version string alone
is insufficient. A dependency update supplies no new mathematical, statistical or consumer
qualification evidence.
