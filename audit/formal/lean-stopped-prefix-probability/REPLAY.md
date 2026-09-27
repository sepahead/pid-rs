# Exact sources and local verification

Author: Sepehr Mahmoudian · 27 September 2026.

The [source map](SOURCE_MAP.json) identifies the exact 25 project modules used in the accepted local joint run: 18 package files and seven unchanged dependencies selected from [lean-prefix-mgw-gradient](../lean-prefix-mgw-gradient/PUBLICATION.md). It records Lean 4.33.0 source commit `d8b18978322de05a8f3dba51ef03cf5461676c17`, Mathlib commit `db584cd6d46c92f209a44c0f1c829460d327499d` and the existing toolchain source-file pins. These are source identities, not authentication of installed binaries.

## What the retained execution checked

The [local acceptance projection](LOCAL_FORMAL_ACCEPTANCE.json) records root adoption at 21:28:05 UTC on 26 September 2026. The actual run completed 29 commands, 58 stdout/stderr streams and 41 typed records. Those records contain exactly three theorem exports, the F1/F2 and F4 controls, six causal comparisons and the expected forbidden-axiom rejection. Their [actual values](evidence/RECORDS.json) remain separate from the [expected control roster](CONTROL_ROSTER.json).

The run compiled the 25 selected modules and checked the declared `StoppedPrefixProbabilityRoot` with `leanchecker --fresh`. The deliberately forbidden-axiom fixture, `PidStoppedPrefixCausal.AxiomControls`, was compiled to observe rejection and is excluded from that root. The fresh-kernel command returned zero with empty stdout and stderr after 206.891 seconds. This is the recorded proof-checking workload, not estimator runtime or a resource promise for another environment.

The semantic judges compared complete raw/alias/candidate propositions and exact export rosters, preserving universe and axiom checks. All three exports reported universes `u`, `v` and `w` and axioms `Classical.choice`, `Quot.sound` and `propext`. F1/F2's [raw printed types](evidence/EXPORTED_TYPES.json) are target abbreviations; the [separate expanded statements](THEOREM_STATEMENTS.md) retain the corresponding source declarations. A successful compilation, theorem name or abbreviated print alone does not establish that correspondence.

## Public source assembly

To reconstruct the project source tree, select each module into exactly its `module_relative_path` from the source map. Do not mix the old StageA definitions, legacy comparison namespaces and current targets on one module path. Preserve all selected bytes, including historical preparation comments, and compile fresh project objects in the declared dependency order under a separately admitted replay.

The [expected command order](COMMAND_ORDER.json) is an input, not execution evidence. The six causal comparisons include expected false values; truthiness or a record count cannot replace their exact typed values. The [command ledger](evidence/COMMANDS.json) binds the actual command outcomes and selected streams.

The original driver was bound to private preparation/execution roots, specific installed native tools, lookup membership and 139,949 installed files at each observed boundary. It checked 137 input snapshots. The [root acceptance projection](evidence/ROOT_ACCEPTANCE.projection.json) records a 382-file readback and 1,118,194,504 hashed bytes. The [native result](evidence/NATIVE_RESULT.projection.json), [root readback](evidence/ROOT_READBACK_RESULT.projection.json), [outer supervision](evidence/OUTER_RESULT.projection.json) and [projection record](evidence/PROJECTIONS.json) preserve their respective statuses and original-byte commitments. Planning labels and pending-adoption statuses inside earlier immutable records remain historical; the later root acceptance adopts the bounded result.

The [public metadata ledger](evidence/PUBLIC_METADATA_PROJECTIONS.json) records complete private-root replacements and omissions of process, session and terminal handles. Original-native hashes, retained first-projection hashes and current projected hashes identify different byte domains. Locator tokens denote roles; they are not executable commands. Of the 58 main stream files, 56 are exact native-byte copies and two are declared PRE/POST boundary stdout projections. All 41 theorem/control values and accepted source bytes are unchanged.

The pre-admission inventory is separate from the 29 main commands. Sequential boundary observations are not an atomic filesystem snapshot or loader trace. The supervisor's sampled memory/process observations are cooperative controls, not a hostile-host sandbox or a hard operating-system memory cap. Public source/object/input joins do not supply every installed binary or private inventory table, authenticate those binaries, or establish complete off-host raw custody. Publishing the projection grants no new native acceptance.

## Portable and hosted replay remain open

No portable native launcher or hosted theorem replay has been accepted for this public assembly. Existing mean, bias and gradient launchers hard-code other module rosters, schemas, targets and admission rules. Replacing their manifest does not replay this package. A separately reviewed thin relocation adapter, new bounded owner, admitted native environment, actual execution and complete readback would establish a new replay result. Expired registrations do not authorize one.

This gap does not change the exact local formal result. Conversely, the local result does not establish portable replay, scientific priority, an implemented sampler, a stopped-gradient theorem, continuous-PID transfer or a useful application. Paper correspondence, formal validity, finite-precision implementation and application evidence remain distinct.

## Preserved earlier outcomes

The [history](HISTORY.md) and [failed F1/F2 disposition](../../archive/stopped-prefix-f1f2-v3/DISPOSITION.md) retain the compiled candidate whose F1 raw/contract comparison failed; that attempt accepted neither export and reached no fresh-kernel step. The later explicit classical-decision repair keeps the probability meaning and endpoint cases while resolving the exact definitional comparison.

The [historical F4 closure](evidence/historical-f4-v4/DISPOSITION.md) retains its older two StageA target files and its own acceptance. Reusing the unchanged F4 proof under repaired shared targets required the fresh joint check recorded here. An initial combined attempt was refused before admission because its inventory was stale and ran no Lean proof command. None of these earlier outcomes is overwritten by the accepted successor.

The [research archive](../../archive/stopped-prefix-research/DISPOSITION.md) separately retains gradient counterexamples and the corrected latent-transfer argument. They constrain stronger stopping claims without refuting F1, F2 or F4.
