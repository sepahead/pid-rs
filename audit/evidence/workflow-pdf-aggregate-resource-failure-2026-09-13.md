# Workflow PDF aggregate: sampled memory-limit failure

On 13 September 2026, local publication aggregate06 failed during the workflow PDF build.
Its peak sampled process-group RSS was 6,487,490,560 bytes. This exceeded the declared
6-GiB limit of 6,442,450,944 bytes by 45,039,616 bytes. The result is an execution failure;
it changes no mathematical statement or proof result.

## Trigger and final process observation

The retained peak and the unchanged [supervisor source](../formal/lean-prefix-mgw-mean/replay-support/runtime.py)
establish that the memory-limit branch was reached: that branch immediately follows an
above-limit peak update. The supervisor later observed a remaining process-group row and
replaced its first failure label with `postterminal_group_observed_without_identity_or_signal`.
Both observations matter. The command returned -9, and the outer wrapper returned 1.

RSS here is a sampled sum of process-group resident sizes. It is not unique physical memory,
a hard operating-system cap, or a complete process-tree inventory. Neither the peak nor the
return code identifies the child's exact allocation peak, a memory leak, an operating-system
out-of-memory event, or the signal sender. Later process queries found neither the recorded
process ID nor a member of the recorded group. Those later samples do not erase the earlier
observation or establish continuous absence. No signal was sent to a historical process ID.

The post-run source, selected native-tool and launcher comparisons reported equality.
The two bias-paper producers and both control modes retained successful scoped results.
They do not establish aggregate success. Nine partial workflow files were captured, including
compiler output, a recorder file and an incomplete PDF. They are retained diagnostic bytes;
they are not a completed pass set or an accepted workflow PDF.

## Successor conditions and rejected interpretations

This failure differs from the earlier [temporary-root containment failure](workflow-pdf-aggregate-temp-root-failure-2026-09-13.md).
That earlier run remained below its memory limit. Aggregate06 used an external temporary tree;
its new resource failure does not justify weakening the source-isolation rule.

A fresh attempt may use a declared 8-GiB outer allowance after current host capacity and
concurrent work have been checked. This is a prospective resource decision, not a successful
execution receipt or assurance that the allowance will suffice. Keep the original time and
stream limits, inner producer limits, exact source and PDF predicates, and process checks.
Use a new execution record and temporary directory. Do not change the failed result, reuse its
clock, ignore its final process observation, or escalate automatically after another failure.

The [bias summary](../formal/lean-prefix-mgw-bias/SUMMARY.md) states the separate mathematical
scope. This operational record grants no new theorem, estimator, application or publication
qualification.

## Retained records

The hashes below identify exact retained bytes. Raw records contain machine-specific paths
and remain in local recovery storage; their locators are in the ignored session handoff.
This public account is a bounded projection, not the raw execution package or an off-host
archive. A digest does not authenticate execution or replace access to its preimage.

| Record | Bytes | SHA-256 |
| --- | ---: | --- |
| Aggregate06 result | 2166 | `9e49b614f94516b45b470481f214ec5aac3c983dd7c003a060c3f6c7c1904086` |
| Aggregate06 launcher | 19291 | `3bdf1c141004702538411db28503dab11ccaee9ecff4a5dea50f246553f48b13` |
| Supervisor source | 27277 | `bd8a9f2272a20422863c9902ce2148d2957471bb958d13949fece923cb6a7f5d` |
| Independent resource review | 7294 | `a1983fa1d598c3e85ee6d2371cfae393d6af703e9d7a286524bbacd3e5fa36cf` |
| Aggregate command stdout | 60284 | `0b9b8f73666ec20fd97d7b66a1cf0aaf37f5614e6d64aa96a1aeef8c2db6c0db` |
| Aggregate command stderr | 4070 | `35b20c2e23303b4d16be338fbe96001c28feba7f715d917c6be92da1fd6cbf2e` |
