# Revision-3 retained negative controls for SX-CERTIFIED-AVERAGED-PID2-001

These controls extend, rather than replace,
[retained-negative-controls.md](retained-negative-controls.md) and
[retained-negative-controls-v2.md](retained-negative-controls-v2.md).

## V3-NC1: nonsemantic cache state caused a fail-closed false rejection

Actions run `30305288762`, job `90107923447`, used CPython 3.11.15 and failed with:

```text
independent verifier loaded execution changed after module initialization
```

The old route marshalled normalized live code objects before and after verification. Lazy
string-intern cache state could change the marshal byte stream without changing executable code or
critical semantic constants. The verifier rejected before crediting a certificate, so this is a
false rejection in a project-defined integrity measurement, not a false acceptance or a
counterexample to the SxPID mathematics.

The complete retained observation, source hashes, run/job/commit/tree identifiers, retrieved-log
digest, and open rerun status are recorded in
[`audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md`](../../../audit/evidence/certified-sxpid2-cpython311-loaded-execution-incident-20260728.md).

## V3-NC2: cache normalization must not erase mutation sensitivity

`check_loaded_execution_cache_stability` loads two isolated verifier copies with identical probe
code and equal dynamically constructed strings. The cold copy starts with a non-interned string
that its own digest normalization intentionally primes. The separate warm copy starts with an
equal explicitly interned string before its digest is taken. The two normalized digests must be
equal. Isolating the copies prevents a first digest on shared module state from warming the same
object before the second initial-state condition is established.

This control targets the observed cache transition. It does not prove equality across Python
versions, implementations, builds, marshal formats, platforms, or arbitrary interpreter states.

## V3-NC3: a live code replacement must still fail

`check_post_import_execution_mutation` replaces `sha256_hex.__code__` after the verifier copy has
initialized. The integrity check must reject through exactly:

```text
independent verifier loaded execution changed after module initialization
```

The control then restores the original code and requires integrity to pass. This distinguishes the
allowed cache-state normalization from an inspected executable-code mutation. It does not prove
that every process mutation is inspected or detected.

## V3-NC4: removing cache normalization must expose the affected path

On CPython 3.11, `check_cache_normalization_source_mutation` loads an isolated verifier source
mutant with the unique `_stabilize_code_string_cache(function.__code__)` call removed. A live
integrity check must reject through the same loaded-execution error. The lane reports zero on
other Python versions; zero there means “not exercised,” not “mutant survived.”

This is one named source mutation. It does not prove that the normalization traversal is complete
for every code object, constant graph, interpreter state, or Python runtime.

## V3-NC5: every declared semantic constant must affect integrity

`check_post_import_semantic_constant_mutations` first requires the exact reviewed inventory of 51
uppercase semantic/configuration globals. It then mutates each global using a deterministic
type-matched replacement, requires the loaded-execution integrity guard to reject, restores the
original value, and requires recovery. The sweep includes the four active exact-product admission
ceilings omitted by the earlier positional digest inventory.

This is exhaustive over the declared 51-name inventory, not over imported Python objects,
underscored/lowercase module state, the process, or mutate-use-restore races. The typed automatic
inventory prevents another declared uppercase constant from being silently omitted, but it does
not prove that every possible behavior-affecting runtime object is declared that way.

## V3-NC6: schema v2 cannot inherit schema-v3 digest semantics

The loaded-execution digest domain changed from
`pid-certified-sxpid-independent-loaded-execution-v1\0` to
`pid-certified-sxpid-independent-loaded-execution-v3\0`. The independent-verification schema
therefore changed from v2 to v3. Treating a v2 report or decision as revision-3 authority would
violate revision 2's explicit schema and runtime re-adjudication triggers even though the
mathematical functional, producer report, and resource policy are unchanged.

## Boundary

Passing the two cache/code controls, rejecting all 51 semantic-constant mutations, and killing the
affected-runtime source mutant shows sensitivity to the named cache, normalization-removal,
code-replacement, and declared configuration cases. It does not establish:

- absence of unnamed integrity faults;
- correctness of CPython, code-object metadata, `sys.intern`, or `marshal`;
- source-to-bytecode or executable refinement;
- digest portability or semantic equivalence;
- independent authorship, review, custody, or a green public rerun;
- population/statistical validity; or
- `pid-core`, continuous, pointwise, quantized, or higher-source correctness.
