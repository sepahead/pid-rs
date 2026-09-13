# Workflow PDF aggregate: temporary-root containment failure

On 13 September 2026, local publication aggregate05 failed at the workflow PDF input check.
The run's temporary directory was beneath the original repository root. The checker forbids
inputs from that root so that the build must use its captured source snapshot. This is an
execution-layout failure. It changes no mathematical result.

## What the retained evidence shows

The diagnostic identifies build A, recorded pass 1, and the generated file
`texmf-cache/luatex-cache/generic/names/luaotfload-names.luc.gz`. It reports that this input bypassed
the source snapshot. The recorder check follows both report builds, convergence checks and the
comparison of their PDFs. “Pass 1” identifies the input set being checked; it does not establish
that compilation stopped during its first pass.

The [workflow checker](../../scripts/check-mathematical-workflow-pdf.sh) rejects each resolved
input beneath the original repository root before it considers the permitted snapshot and build
roots. In this attempt, the entire temporary build tree was inside that prohibited root. The
named font cache was one conflicting input; relocating only that cache would leave the source
snapshot and other private build inputs inside the same prohibited domain.

The child returned status 1. The wrapper's post-run source, selected native-tool and launcher
comparisons reported equality, and no surviving process-group member was observed. Peak sampled
group memory was 6,419,857,408 bytes, below the 6,442,450,944-byte limit. Completion preceded the
original deadline. The evidence does not support a memory-limit failure, cache corruption or a
cache write-permission failure.

The failed workflow's numbered compiler logs and recorder files were removed during cleanup and
were not recovered. The aggregate stdout and stderr were retained. These streams do not recover
the missing file inventory or exact pass count. No reconstructed compiler record is used.

## Repair condition and rejected alternatives

A fresh execution must place the complete temporary build root outside the canonical source
root. It must create that directory exclusively, require mode 0700 and canonical paths, and
reject an existing leaf or overlap with the source root. The existing temporary, TeX and cache
mappings can then share this external directory. Check this placement before native execution.

Keep the source-bypass rule, allowed-input checks, exact PDF comparisons, marker checks, stream
checks and resource limits. Moving only the cache does not fix the whole-tree overlap. Weakening
the input rule would remove the evidence this check is meant to provide. Raising the memory
limit does not address the recorded cause. Reusing the failed attempt would erase the boundary
between separate executions.

This is a source-supported repair condition, not a receipt for a successful follow-up. A fresh
aggregate needs its own complete result, source checks and observed process exit. The previous
standalone workflow success used a source snapshot with a sibling temporary directory. It did
not test aggregate05's containment arrangement. The two bias-paper builds and their controls
retain their own successful results; they do not make this aggregate pass. See the
[bias summary](../formal/lean-prefix-mgw-bias/SUMMARY.md) for the separate scientific scope.

## Retained-record manifest and access boundary

The following SHA-256 values identify exact retained bytes. They do not authenticate execution or
replace an omitted artifact. Original records with machine-specific paths remain in the local
recovery store. This public manifest and account provide a portable record; they are not a public
copy of those raw streams or a standalone replay package. Local locators belong in the ignored
session handoff. No missing compiler log is represented by a substitute hash.

| Retained record | Bytes | SHA-256 |
| --- | ---: | --- |
| Aggregate05 result | 1990 | `86a21eeeb5c16cb36262f6cd9b26dcaadff67450ad85c5d8e3d2db6d763c61d7` |
| Aggregate command stdout | 60284 | `527b111432b678d5560cc9647746931d5a5da79f5159e8c365c760e0b277aa2f` |
| Aggregate command stderr | 4445 | `7656abd390d5e1446a373588bc9532aabe501d08192d2304e353ec8f5e3acd93` |
| Aggregate05 launcher source | 18588 | `6565b80a4099e6f237b758224617e349768237ad05eccc57853174264ec7da75` |
| Workflow checker source | 276031 | `bc84cddae22fc9a79136cd97ce3f64dde2f16e57f676066850850597cd7eb65e` |
| Independent initial diagnosis | 2579 | `f4f711589827199c793033c0ee35eaf1f17f4c7f7815a65980ff88210b0c1ece` |
| Independent source review | 6329 | `94733dc7badd39551dc53182d13e6d56cd878a7a32d48c994a6f2c582b7f43aa` |

The source review corrects an earlier review that checked cache-variable propagation but missed
source/build-root containment. Both reviews are retained. Independent-first critique and root
inspection support this diagnosis; agreement alone proves neither runtime success nor science.
