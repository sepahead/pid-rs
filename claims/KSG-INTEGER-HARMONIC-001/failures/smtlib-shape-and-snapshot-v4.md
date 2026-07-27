# SMT-LIB shape and snapshot failure, revision 4

## Failure

The first revision-4 Z3 checker pinned each raw proof-file digest, but its semantic-shape check was
substring based. After deliberately rebasing that one raw digest, syntactically different files
could preserve the expected substrings while adding commands or changing token boundaries. In
particular, an appended positive assertion, a whitespace-split quantifier spelling, and unsupported
commands exposed that the checker had not parsed the complete SMT-LIB input.

The old route also validated a file and later passed its path to Z3. A replacement between those
operations could make the solver consume bytes other than the validated snapshot. No such race is
claimed to have occurred in ordinary replay; the point is that the custody design did not exclude
it.

The former checker and self-test digests were:

```text
030e5cf060ff5e452390f6138c66083cc68ed22d5e599e5c0ee261500de924a0  checker
a4a401523fbfcad08fc58e29da497c141ab18ce27f62ef987d14a63d960d1e23  self-test
```

Frozen proof sources were not changed. This memo records a checker failure, not a refutation of any
of the four conditional obligations.

## Repair

The replacement checker:

1. reads all four proof files once into immutable byte snapshots before starting a solver;
2. rejects non-ASCII/control bytes and lexes every remaining byte under explicit size limits;
3. parses a bounded S-expression grammar and rejects trailing or unsupported forms;
4. requires an exact ordered profile of commands, declarations, sorts, arities, assertions, and the
   terminal negated obligation for each proof;
5. infers the accepted `Bool`/`Int`/`Real` expression subset and rejects undefined or ill-sorted
   expressions;
6. checks correlated raw-byte and token-stream digests;
7. constructs the positive satisfiability preflight by replacing only the validated in-memory
   terminal negated assertion; and
8. sends both exact snapshots to `z3 -smt2 -in`, accepting only the expected single-word result,
   empty standard error, and successful exit before and after a bounded timeout.

The repaired sources are:

```text
2e0579820c02423e6d15bf81f6ee7470563a121908b4d06e5168b6508f991680  checker
927a21d119686d8e5a03755e8cf48581a2879bb67c835c295fdefcede26ec101  self-test
```

The four proof files retain their earlier raw SHA-256 values. Their correlated token-stream pins
are:

```text
46d504aea109ae875598404a7d680e8dceb93635a4f91ab3d11bd51b08de5292  digamma cancellation
7e655ca85f042c4275042fc8e9368a72aef10b1e0cbde3dce7b87c67769a7f2c  index maps
9f20298f0fb6a630167995b96638f6446a07e4005b9bc1a265a136302a73f284  local bound
e7d9605f13384e1f7d04b0f1b6b4a61848adc70a6ae1925a06eeeddca2475aa1  symmetric range
```

These two digests are correlated views of the same source. They improve accidental/drift
detection and require a deliberate source change to rebase two checker fields; they are not two
mathematical proofs or an authenticity mechanism.

## Separate evidence accounting

Normal and optimized Python replay are byte-identical. The main route obtains four exact `sat`
positive preflights and four exact `unsat` negated obligations. The self-test retains **12/12**
semantic countermodel mutations. A separately labelled checker firewall passes **52/52** controls:

```text
lexer/parser                 16
profile/type                 25
custody/transport/result     11
```

The 52 controls do not enlarge the theorem, obligation, or semantic-mutation count. Conversely,
the 12 semantic countermodels do not establish parser or transport integrity.

## Retained adequacy boundary

A well-typed but wrong digamma statement remains green after a deliberate rebase of both
correlated pins:

```text
raw SHA-256          88e67f4289caf81770c9457d3ac77de4f470fe56d8bf3eb0a8139ac42c23ec52
token-stream SHA-256 f8c8334b0cd73a55072e833463ae6ec43bd0f6042c0f7e888eff01b8f75caa8e
positive preflight   sat
negated obligation  unsat
old semantic mutants still returning sat  12/12
```

This is a retained negative result. The bounded parser can enforce the approved statement's shape
and type, but it cannot decide whether humans intended that statement. Statement selection,
coefficient signs, index maps, and a deliberate dual-pin rebase remain shared human/Git/receipt
cuts. Z3 also emits solver answers rather than proof objects checked by an independent small
kernel.

## Boundary

The repair establishes bounded, fail-closed handling for the four frozen conditional QF_UFLIRA
scripts. It does not prove the analytic digamma premise, harmonic monotonicity, Rust refinement,
neighbor geometry, binary64 correctness, KSG estimator validity, support assumptions, shared
exclusions, PID atoms, calibration, or applications. The executable path, version, and binary hash
are observed provenance only; they are not authenticity or attestation.
