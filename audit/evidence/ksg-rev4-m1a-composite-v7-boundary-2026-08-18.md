# KSG revision-4 M1a composite-v7 bounded operational correction

- Status: **final C7 process-publication boundary; C6 is published; R6 is permanently unissued;
  the terminal C6 roster and predecessor capture are fixed; the frozen exact C7 rows, fresh `r12`,
  current-source manifest, and sealed v7 publication family are bound by the final C7 checker and
  exact C7 tree; R7 remains conditional and unissued**
- Observation date: 18 August 2026
- Repository: `sepahead/pid-rs`

## Disposition

Published C6 is exact unsigned commit
`0c3afa0ab5b264370072a18d24655df35b90574c`, tree
`ad28fd5ec3eed76fca1315b24c2e047fb5e6cff4`, sole parent
`be862b155d710573ec95356fc1cbe9a96a2b83b9`, with message
`Repair KSG M1a composite v6 contract`. Its exact C6 tree, finalized C6-era predecessor Lean replay
`r11`, v6 publication family, v6 gates, v6 schemas, v6 checkers, v6 capture tools, and predecessor
evidence remain immutable.

R6 is permanently unissued. Two bounded defect classes are known and neither observation transfers
qualification credit to C7:

1. The exact C6 local recorder routes every internal command through a 65,536-byte per-stream
   bound, while its required sorted authority inventory includes exact C6 blobs of 69,573 and
   124,520 bytes. Full equality to either blob and acceptance by that internal bound cannot both
   hold. The canonical counterexample is
   `audit/evidence/ksg-rev4-m1a-composite-v6-local-closure-counterexample-v7-2026-08-18.json`
   (SHA-256 `cabcd565f25e11d14c4082532ea7efe1987eb0d700c115a8fbf36937486eede2`,
   9,103 bytes); its closed schema is
   `audit/schemas/ksg-rev4-m1a-composite-local-closure-counterexample-v7.schema.json`
   (SHA-256 `d06f0437cd5eddce35a88be9eccd5653ddc36b29b361ff924c33578d15a4de7b`,
   21,621 bytes). Both are present and exact-byte-bound by the final C7 checker; their modes and
   paths are included in the frozen exact C7 row inventory.
2. Dedicated C6 attempt-1 run `32139920743`, job `95719898016`, failed at its publication step with
   the exact diagnostic `composite publication PDF v6 adjudication: missing command: rg`.
   Repository CI attempt-1 push/main run `32139920717` completed with conclusion `failure` at
   `2026-08-18T14:48:10Z`. Its exact terminal roster contains 45 jobs: 44 success and the sole
   failure job `95719898423`, `Formal LaTeX / PDF inventory and cross-toolchain structure`. That
   job's sole failed step is step 11, `Rebuild papers and check cross-toolchain text, geometry,
   fonts, and workflow renders`; it reached the same diagnostic after seven earlier PDF gates
   passed. The repository and head-repository ID is `1271708111`. Their exact bounded predecessor
   hosted capture is installed at
   `audit/evidence/ksg-rev4-m1a-composite-predecessor-failure-hosted-capture-v7-2026-08-18.json`
   (SHA-256 `e9a1d574cb4127263d8aaec3e291e78836b849f9b402af8a0daa5eb37cc70104`,
   1,819,338 bytes; normalized projection SHA-256
   `bc81849000b3967b9f3a226629e39cfe754fc2cf951294a94fc319a41ac0f9e8`). It contains 36 exact
   response rows, two retrieval repetitions, and zero retry events. CodeQL attempt-1 run
   `32139921184` completed successfully, but that term cannot transfer across the false
   conjunction.

The dedicated and repository-CI missing-`rg` manifestations are two observations of one
dependency-declaration defect. They are not independent evidence or cross-platform replication.

The hosted diagnostic is a dependency-closure failure, not evidence of PDF-content failure. C7
therefore adds the `ripgrep` package to the CI formal-PDF apt block and the dedicated-v7 apt block.
Each hosted lane requires executable `/usr/bin/rg`, requires `command -v rg` to resolve exactly to
`/usr/bin/rg`, and executes `/usr/bin/rg --version` before the dependent gates. The apt package is
not byte-pinned. C7 leaves every v6
PDF, TeX, SVG, rendering receipt, visual receipt, comparator, gate, and hostile suite byte-exact.
The repaired v7 local recorder separately observes `rg` in its reviewed executable roster.

## Exact C6 local contradiction

The immutable v6 recorder's authority inventory is sorted by path:

| Path | Bytes | SHA-256 | Above 65,536 |
|---|---:|---|---|
| `audit/schemas/ksg-rev4-m1a-composite-local-closure-v6.schema.json` | 13,620 | `4ab719785b6f89ce63d1061813a31e17289fa94cf4300aab00946de2c045f3fd` | no |
| `justfile` | 32,358 | `7654a4ea10c71dced82ce492717a55568f91fbe9d09471aa3e306d830907873c` | no |
| `scripts/capture-ksg-m1a-composite-v6-local-closure.py` | 57,021 | `5f16ac70cc8a927efd85ab19770a976f928125ab60c003fdf8959ea9039f748a` | no |
| `scripts/check-ksg-m1a-composite-v6-self-test.py` | 69,573 | `3430e7c0e083fd444de4649d432051a9fa54659d974b6d4384337857d79b7265` | **yes; first** |
| `scripts/check-ksg-m1a-composite-v6.py` | 124,520 | `6708de55bd0ffd938d1a567630b64d2a6d577cccd09b2285abe00ccf31cba494` | **yes** |

The exact source route is `authority_descriptors` to `git_output` to `internal_command` to
`run_bounded`; `internal_command` supplies `MAX_VERSION_STREAM_BYTES = 64 * 1024` for all callers.
The recorder requires the returned bytes to equal each full authority blob. This establishes a
source-and-byte contradiction for L6; it is not a claim about a detailed runtime trace. The present
machine counterexample records no invocation, runtime, exit-status, or stderr observation and must
not be read as or extended with an invented runtime observation.

## V7 repair predicate

The v7 recorder preserves the 65,536-byte bound for version and small metadata probes. It adds a
separate 2,097,152-byte authority-stream bound equal to the authority-file read bound. The new v7
authority wrapper explicitly selects that class only for exact validated
`git show <C7-commit>:<authority>` reads. Inherited generic probes retain the immutable V6
65,536-byte route. The full returned bytes must still equal the stable mode-`0644` worktree file.
The command output remains bounded to 8 MiB per stream, the canonical record to 32 MiB, and
reviewed executables to 256 MiB. Boundary tests require 65,536 acceptance and 65,537 rejection in
the version lane, 65,537 and 2,097,152 acceptance in the authority lane, and 2,097,153 rejection.

The fixed command becomes `just ksg-composite-v7`. Its record is valid only for one exact clean C7
commit, with clean pre/post observations, the fixed minimal environment, `0077` umask, complete
bounded stdout/stderr, named authority bindings, and a reviewed executable roster that includes
`rg`. This remains correlated unsigned operational evidence, not hermetic execution,
authentication, trusted time, first-attempt authority, or independent reproduction.

## Append-only topology

The bound topology is

```text
C5 -- C6 -- C7 -- R7
       \\-- R6 permanently absent
```

C7 is the exact unsigned direct child of C6. The frozen exact C7 row inventory, fresh `r12` replay
cut, current-source manifest, and sealed v7 publication family are bound by the final C7 checker and
exact C7 tree. The path policy stores `tree: null` with state
`derived_from_c7_commit_not_embedded`; the checker derives the actual tree from the C7 commit
instead of creating a tree self-reference. R7 remains conditional and unissued. If and only if
every C7 qualification term is true, R7 is the exact direct child of C7 and changes only the
self-excluding current-source manifest, the durable local L7 record, the successor hosted capture,
and the derived receipt.

The exact R7 delta is fixed independently of the frozen C7 rows:

| Status | Mode | Path |
|---|---|---|
| M | `100644` | `audit/evidence/current-source-state-v1.json` |
| A | `100644` | `audit/evidence/ksg-rev4-m1a-composite-local-closure-v7-2026-08-18.json` |
| A | `100644` | `audit/evidence/ksg-rev4-m1a-composite-receipt-v7-2026-08-18.json` |
| A | `100644` | `audit/evidence/ksg-rev4-m1a-composite-successor-qualification-hosted-capture-v7-2026-08-18.json` |

Define

$$
Q_7 = L_7 \land \mathrm{CI}_7 \land \mathrm{CodeQL}_7 \land D_7.
$$

The three hosted terms require fresh terminal attempt-1 success for the same exact C7 commit.
L7 carries no attempt-number authority. The issuance rule is

$$
\mathrm{issue}(R7) \Longleftrightarrow Q_7.
$$

Any false, absent, nonterminal, retry, wrong-commit, or wrong-attempt term leaves R7 unissued and
requires another append-only successor. R4, R5, and R6 remain absent and may not be reconstructed,
renamed, backdated, or inferred.

## Publication and scientific scope

The full v7 process-publication family is delivered and quiescent: visual receipt, TeX, SVG,
standalone figure PDF, report PDF, rendering receipt, PDF gate, and PDF hostile suite. Its complete
file set is included in the frozen exact C7 row inventory and bound by the final C7 checker and exact
C7 tree. The publication describes both bounded defects and does not alter any v6 publication or
gate.

C7 changes zero PID definitions, zero functionals, zero estimators, zero theorem sources, and zero
numerical results. It updates no method-catalog origin claim. Operational evidence here grants no
mathematical, scientific, estimator, security, privacy, accessibility, renderer-independence,
application, authentication, attestation, authorship, provider-completeness, trusted-time, or
independence credit. No evidence transfers among KSG mutual information, categorical or continuous
shared exclusions, `I_min`, PID2, PID3, quantized or mixed-support routes, uncertainty procedures,
or downstream objectives.
