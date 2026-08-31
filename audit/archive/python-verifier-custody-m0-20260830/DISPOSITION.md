# Python verifier custody M0 archive disposition

Status: **inert historical process prototype; never current authority**.

This packet preserves the reusable source and design bytes from commit
`e16a6915262e8bf2fac1752ff959d9d3733c7a7d` (tree
`74030de0ec545e29fd35429dfc2c889f676dfc8d`). That commit reviewed its parent
`eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9`. It is not merged as active
functionality because its registry describes that historical parent rather than the
current repository, its checker has no current workflow or Just entry point, and its
execution-custody edges remain deliberately open.

## What is retained

Five exact source artifacts are copied under inert `.txt` names:

- the design record;
- the explanatory document;
- the registry schema;
- the static-inventory checker; and
- its hostile self-test.

The useful process contribution is the separation of eight objects that are easy to
conflate:

1. stored source bytes;
2. a textual or programmatic launch request;
3. the interpreter executable;
4. final arguments, standard input, working directory, environment, and platform;
5. imports and dynamically generated source;
6. child processes and native dependencies;
7. the produced result; and
8. the meaning assigned to that result.

The historical packet's key inequality remains useful:

```text
source found != source loaded != source ran != result correct
```

It also preserves twelve compared design routes, a fifty-lens internal critique,
explicit false-positive and false-negative examples, and the rule that unknown
edges remain blocking rather than being collapsed into one misleading
`verified` flag. These are engineering-process lessons. They are not a new PID
method, estimator, theorem, statistical result, formal proof, security attestation,
or scientific-priority claim.

## What is deliberately omitted

The generated `registry-v1.json` is not copied. Its exact historical identity is
recorded in `INDEX.json`: 5,473,991 bytes, SHA-256
`ce11224f6fb95246a43dd36c24da57501f3854bf2f667c483f99125d751f016a`,
and Git blob `a7a101bff380e64f18fcba2b9cc0bd5b61ee6af9`. It is deterministic
derived output for a parent tree that remains reachable from current Git history.
Copying 5.47 MB of stale inventory into the current source tree would add no unique
reasoning and could be mistaken for current evidence.

The historical census was 1,040 tracked tree entries, 186 Python files, 66
operational roots, 2,110 import statements, 2,295 imported-name edges, 165 selected
dynamic-call spellings, and 1,057 static launch candidates. These counts describe
only the pinned parent and the M0 grammar. They are not process counts.

A read-only drift probe applied the historical grammar to the 2026-08-31 candidate
worktree and found 201 Python files, 73 operational roots, 2,286 import statements,
2,530 imported-name edges, 176 selected dynamic-call spellings, and 1,138 static
launch candidates. This probe is diagnostic only. It demonstrates staleness; it is
not a current registry or release authority. The old standard-library profile also
leaves the now-imported `html` root unresolved. That behavior is fail-closed, but
it confirms that the frozen registry cannot represent the current tree.

## Why the implementation is not activated

- The checker and schema pin the old parent commit and tree.
- The checker inventories the parent, not the commit that contains the checker, so
  its bootstrap remains open.
- No current workflow or Just recipe invokes it.
- Its “official verifier” projection is based on a `check-*` spelling, not an
  authority theorem.
- The root seed omits native launchers and does not implement complete
  shell/YAML/Just/Actions semantics.
- Static import candidates do not determine `sys.path`, import hooks, loaded
  modules, wheels, native libraries, or child processes.
- Git subprocesses have no hard timeout.
- Checker and self-test share the same dynamic Python loading route and do not form
  an independent bootstrap.
- The old method-catalog status `stable` would overstate the absence of an active
  entry point and the open execution edges.

These are scope boundaries, not evidence that the prototype's bounded static
inventory was incorrect on its pinned tree.

## Retained negative results and nonclaims

The historical prototype did not implement complete shell/YAML/Just/Actions
semantics, scan native launchers, resolve dynamic aliases, close its bootstrap,
authenticate Git or Python, or establish execution custody for any launch. Its
hostile suite showed sensitivity to named faults only; it did not prove scanner
correctness or fault-inventory completeness.

Never execute files from this archive or treat embedded commands, counts, paths, or
statuses as current guidance. The archive checker validates exact bytes, Git-blob
correspondence, non-executable modes, closed-world file inventory, and Python syntax.
It grants no mathematical, statistical, estimator, application, formal, security,
authenticity, release, or execution-custody credit.

This directory deliberately has no `README.md`: it is an inert evidence archive,
not a published package, directly consumed command, or browsed-asset directory.
